#!/usr/bin/env python3
"""
PadelMind Court Recorder — Pi Edge Software (C1)

Polls Supabase every 5 seconds for active matches on this Pi's courts.
Starts/stops ffmpeg recording accordingly.
On match end: concatenates segments → uploads raw.mp4 to Cloudflare R2 →
notifies our Cloudflare Worker webhook.

Flask HTTP endpoints (/match/start, /match/stop, /status, /ping) available
for manual control and testing on the local network.
"""

import glob
import logging
import os
import subprocess
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

import boto3
import requests
from flask import Flask, jsonify, request

# ── Config from environment ────────────────────────────────────────────────
SUPABASE_URL  = os.environ['PADEL_SUPABASE_URL']
SUPABASE_KEY  = os.environ['PADEL_SUPABASE_KEY']          # service_role key
COURT_IDS     = [c.strip() for c in os.environ['PADEL_COURT_IDS'].split(',')]
R2_ACCOUNT_ID = os.environ['PADEL_R2_ACCOUNT_ID']
R2_ACCESS_KEY = os.environ['PADEL_R2_ACCESS_KEY']
R2_SECRET_KEY = os.environ['PADEL_R2_SECRET_KEY']
R2_BUCKET     = os.environ.get('PADEL_R2_BUCKET', 'padelmind-videos')
WORKER_URL    = os.environ['PADEL_WORKER_URL']             # Worker base URL (no path)
PI_SECRET     = os.environ.get('PADEL_PI_SECRET', '')      # Worker's PI_SHARED_SECRET
SEGMENTS_BASE = Path(os.environ.get('SEGMENTS_DIR', '/tmp/padelmind'))
POLL_INTERVAL = int(os.environ.get('POLL_INTERVAL', '5'))

# Camera device per court — index into COURT_IDS list
CAMERA_DEVICES = {}
for i, court_id in enumerate(COURT_IDS):
    CAMERA_DEVICES[court_id] = os.environ.get(f'CAMERA_DEVICE_{i}', f'/dev/video{i * 2}')

# ── Logging ────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s  %(levelname)-7s  %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
log = logging.getLogger('padelmind')

# ── Shared state ───────────────────────────────────────────────────────────
# court_id → {match_id, process, segments_dir, started_at, uploading}
state_lock   = threading.Lock()
courts_state = {}

app = Flask(__name__)

# ── Supabase helpers ───────────────────────────────────────────────────────
SB_HEADERS = {
    'apikey':        SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}',
    'Content-Type':  'application/json',
}

def sb_get(table, params):
    r = requests.get(
        f'{SUPABASE_URL}/rest/v1/{table}',
        headers=SB_HEADERS, params=params, timeout=10,
    )
    r.raise_for_status()
    return r.json()


# ── Recording ──────────────────────────────────────────────────────────────
def start_recording(court_id, match_id):
    with state_lock:
        s = courts_state.get(court_id, {})
        # Already recording this exact match → skip
        if s.get('match_id') == match_id and s.get('process') and s['process'].poll() is None:
            return
        # Different match running → terminate it first
        if s.get('process') and s['process'].poll() is None:
            s['process'].terminate()

    segments_dir = SEGMENTS_BASE / match_id
    segments_dir.mkdir(parents=True, exist_ok=True)
    camera = CAMERA_DEVICES.get(court_id, '/dev/video0')

    cmd = [
        'ffmpeg', '-y',
        '-f', 'v4l2',
        '-video_size', '1280x720',
        '-framerate', '30',
        '-i', camera,
        '-c:v', 'libx264',
        '-preset', 'ultrafast',  # minimise CPU on Pi 4
        '-crf', '25',
        '-f', 'segment',
        '-segment_time', '600',  # 10-minute chunks
        '-segment_format', 'mp4',
        '-reset_timestamps', '1',
        str(segments_dir / 'seg_%03d.mp4'),
    ]

    log.info(f'[{match_id[:8]}] START  court={court_id[:8]}  camera={camera}')
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

    with state_lock:
        courts_state[court_id] = {
            'match_id':    match_id,
            'process':     proc,
            'segments_dir': segments_dir,
            'started_at':  datetime.now(timezone.utc).isoformat(),
            'uploading':   False,
        }


def stop_and_upload(court_id):
    with state_lock:
        s = courts_state.get(court_id)
        if not s or s.get('uploading') or not s.get('match_id'):
            return
        match_id     = s['match_id']
        segments_dir = s['segments_dir']
        proc         = s.get('process')
        s['uploading'] = True

    log.info(f'[{match_id[:8]}] STOP   court={court_id[:8]}')
    if proc and proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=15)
        except subprocess.TimeoutExpired:
            proc.kill()

    # Upload in background — poll loop must not block
    threading.Thread(
        target=_upload_worker,
        args=(court_id, match_id, segments_dir),
        daemon=True,
    ).start()


def _upload_worker(court_id, match_id, segments_dir):
    try:
        segments = sorted(segments_dir.glob('seg_*.mp4'))
        if not segments:
            log.warning(f'[{match_id[:8]}] No segments found — nothing to upload')
            return

        # Concatenate all segments into one file
        output_path = segments_dir / 'raw.mp4'
        concat_file = segments_dir / 'concat.txt'
        concat_file.write_text('\n'.join(f"file '{s}'" for s in segments))

        log.info(f'[{match_id[:8]}] Concat {len(segments)} segments → raw.mp4')
        subprocess.run(
            ['ffmpeg', '-y', '-f', 'concat', '-safe', '0',
             '-i', str(concat_file), '-c', 'copy', str(output_path)],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )

        # Upload to Cloudflare R2
        r2_key = f'matches/{match_id}/raw.mp4'
        log.info(f'[{match_id[:8]}] Uploading → R2 {r2_key}')
        s3 = boto3.client(
            's3',
            endpoint_url=f'https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com',
            aws_access_key_id=R2_ACCESS_KEY,
            aws_secret_access_key=R2_SECRET_KEY,
            region_name='auto',
        )
        s3.upload_file(
            str(output_path), R2_BUCKET, r2_key,
            ExtraArgs={'ContentType': 'video/mp4'},
        )
        log.info(f'[{match_id[:8]}] Upload complete')

        # Notify Cloudflare Worker → queues job + triggers RunPod dispatch
        notify_url = f"{WORKER_URL.rstrip('/')}/api/matches/{match_id}/uploaded"
        payload = {'secret': PI_SECRET, 'r2_key': r2_key}
        for attempt in range(3):
            try:
                r = requests.post(notify_url, json=payload, timeout=30)
                r.raise_for_status()
                log.info(f'[{match_id[:8]}] Worker notified  status={r.status_code}')
                break
            except Exception as e:
                log.warning(f'[{match_id[:8]}] Worker notify attempt {attempt + 1} failed: {e}')
                time.sleep(5 * (attempt + 1))

        # Clean up temp files
        for f in segments_dir.glob('*'):
            f.unlink(missing_ok=True)
        segments_dir.rmdir()

    except Exception as e:
        log.error(f'[{match_id[:8]}] Upload pipeline failed: {e}')
    finally:
        with state_lock:
            courts_state.pop(court_id, None)


# ── Poll loop ──────────────────────────────────────────────────────────────
def poll_loop():
    log.info(f'Poll loop started  courts={[c[:8] for c in COURT_IDS]}  interval={POLL_INTERVAL}s')
    while True:
        try:
            for court_id in COURT_IDS:
                matches = sb_get('padel_matches', {
                    'court_id': f'eq.{court_id}',
                    'status':   'eq.recording',
                    'order':    'started_at.desc',
                    'limit':    '1',
                    'select':   'id,started_at',
                })

                with state_lock:
                    s = courts_state.get(court_id, {})
                    is_recording = (
                        s.get('process') and
                        s['process'].poll() is None and
                        not s.get('uploading')
                    )
                    current_match_id = s.get('match_id')

                if matches:
                    db_match_id = matches[0]['id']
                    if not is_recording or current_match_id != db_match_id:
                        start_recording(court_id, db_match_id)
                else:
                    if is_recording:
                        stop_and_upload(court_id)

        except Exception as e:
            log.error(f'Poll error: {e}')

        time.sleep(POLL_INTERVAL)


# ── Flask HTTP endpoints ───────────────────────────────────────────────────
@app.route('/match/start', methods=['POST'])
def api_start():
    data = request.json or {}
    court_id = data.get('court_id')
    match_id = data.get('match_id')
    if not court_id or not match_id:
        return jsonify({'error': 'court_id and match_id required'}), 400
    start_recording(court_id, match_id)
    return jsonify({'ok': True, 'match_id': match_id})


@app.route('/match/stop', methods=['POST'])
def api_stop():
    data = request.json or {}
    court_id = data.get('court_id')
    if not court_id:
        return jsonify({'error': 'court_id required'}), 400
    stop_and_upload(court_id)
    return jsonify({'ok': True})


@app.route('/status')
def api_status():
    with state_lock:
        return jsonify({
            court_id: {
                'recording':  bool(s.get('process') and s['process'].poll() is None),
                'uploading':  s.get('uploading', False),
                'match_id':   s.get('match_id'),
                'started_at': s.get('started_at'),
            }
            for court_id, s in courts_state.items()
        })


@app.route('/ping')
def api_ping():
    return jsonify({'ok': True, 'ts': datetime.now(timezone.utc).isoformat()})


# ── Entry point ────────────────────────────────────────────────────────────
if __name__ == '__main__':
    SEGMENTS_BASE.mkdir(parents=True, exist_ok=True)
    threading.Thread(target=poll_loop, daemon=True).start()
    log.info('PadelMind Recorder started on :5000')
    app.run(host='0.0.0.0', port=5000, debug=False)
