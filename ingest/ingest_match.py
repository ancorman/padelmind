#!/usr/bin/env python3
"""
PadelMind iPad-recording ingest tool (no Pi required).

Takes a match video (AirDropped from the iPad), uploads it to R2, creates the
match records in Supabase, and kicks off CV processing on RunPod via our
Cloudflare Worker. From there the normal pipeline takes over: heatmaps +
highlight reel + rally stats → WhatsApp + PWA.

Usage:
  # New match from a video file:
  python3 ingest_match.py --video match.mp4 --court-id <uuid> \
      --phones +919820027850,+91XXXXXXXXXX

  # Attach the video to a match already created via the PWA Staff page:
  python3 ingest_match.py --video match.mp4 --match-id <uuid>

Config: reads ingest.env next to this script (see ingest.env.example),
overridable by real environment variables.
"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import boto3
import requests

CONFIG_KEYS = [
    'PADEL_SUPABASE_URL', 'PADEL_SUPABASE_KEY',
    'PADEL_R2_ACCOUNT_ID', 'PADEL_R2_ACCESS_KEY', 'PADEL_R2_SECRET_KEY',
    'PADEL_R2_BUCKET', 'PADEL_WORKER_URL', 'PADEL_PI_SECRET',
]


def load_config():
    env_file = Path(__file__).parent / 'ingest.env'
    cfg = {}
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                cfg[k.strip()] = v.strip()
    for k in CONFIG_KEYS:
        if os.environ.get(k):
            cfg[k] = os.environ[k]
    missing = [k for k in CONFIG_KEYS if not cfg.get(k)]
    if missing:
        sys.exit(f'Missing config: {", ".join(missing)} — copy ingest.env.example to ingest.env and fill it in.')
    return cfg


def sb(cfg, method, path, body=None, prefer='return=representation'):
    r = requests.request(
        method, f"{cfg['PADEL_SUPABASE_URL']}/rest/v1{path}",
        headers={
            'apikey': cfg['PADEL_SUPABASE_KEY'],
            'Authorization': f"Bearer {cfg['PADEL_SUPABASE_KEY']}",
            'Content-Type': 'application/json',
            'Prefer': prefer,
        },
        json=body, timeout=30,
    )
    if not r.ok:
        sys.exit(f'Supabase {method} {path} failed {r.status_code}: {r.text}')
    return r.json() if r.text else None


def normalize_phone(raw):
    digits = ''.join(c for c in raw if c.isdigit())
    if raw.strip().startswith('+'):
        return '+' + digits
    if len(digits) == 10:
        return '+91' + digits
    return '+' + digits


def video_duration_sec(path):
    try:
        out = subprocess.run(
            ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', str(path)],
            capture_output=True, text=True, timeout=60,
        )
        return int(float(json.loads(out.stdout)['format']['duration']))
    except Exception:
        return 0


def main():
    ap = argparse.ArgumentParser(description='Ingest an iPad match recording into PadelMind')
    ap.add_argument('--video', required=True, help='Path to the match MP4/MOV')
    ap.add_argument('--court-id', help='padel_courts.id (required unless --match-id)')
    ap.add_argument('--match-id', help='Attach to an existing padel_matches row (e.g. created via PWA Staff page)')
    ap.add_argument('--phones', default='', help='Comma-separated player WhatsApp numbers, slot order P1..P4')
    args = ap.parse_args()

    video = Path(args.video).expanduser()
    if not video.exists():
        sys.exit(f'Video not found: {video}')
    if not args.match_id and not args.court_id:
        sys.exit('Provide --court-id (new match) or --match-id (existing match).')

    cfg = load_config()
    duration = video_duration_sec(video)
    now = datetime.now(timezone.utc)

    # 1 — match row
    if args.match_id:
        match_id = args.match_id
        rows = sb(cfg, 'GET', f'/padel_matches?id=eq.{match_id}&select=id,status')
        if not rows:
            sys.exit(f'Match {match_id} not found.')
        print(f'Using existing match {match_id} (status={rows[0]["status"]})')
    else:
        rows = sb(cfg, 'POST', '/padel_matches', {
            'court_id': args.court_id,
            'started_at': (now - timedelta(seconds=duration or 0)).isoformat(),
            'ended_at': now.isoformat(),
            'status': 'uploaded',
            'duration_sec': duration or None,
        })
        match_id = rows[0]['id']
        print(f'Created match {match_id}')

    # 2 — players
    phones = [normalize_phone(p) for p in args.phones.split(',') if p.strip()]
    for slot, phone in enumerate(phones[:4], start=1):
        existing = sb(cfg, 'GET', f'/padel_players?phone=eq.{phone}&select=id')
        if existing:
            player_id = existing[0]['id']
        else:
            created = sb(cfg, 'POST', '/padel_players', {'phone': phone, 'status': 'pending'})
            player_id = created[0]['id']
        sb(cfg, 'POST', '/padel_match_players', {
            'match_id': match_id, 'player_id': player_id,
            'player_phone': phone, 'player_slot': slot,
        }, prefer='resolution=merge-duplicates,return=representation')
        print(f'  P{slot} → {phone}')

    # 3 — upload to R2 (multipart, handles multi-GB iPad files)
    r2_key = f'videos/{match_id}/match.mp4'
    size_mb = video.stat().st_size / 1e6
    print(f'Uploading {video.name} ({size_mb:.0f} MB) → r2://{cfg["PADEL_R2_BUCKET"]}/{r2_key}')
    s3 = boto3.client(
        's3',
        endpoint_url=f"https://{cfg['PADEL_R2_ACCOUNT_ID']}.r2.cloudflarestorage.com",
        aws_access_key_id=cfg['PADEL_R2_ACCESS_KEY'],
        aws_secret_access_key=cfg['PADEL_R2_SECRET_KEY'],
    )
    done = {'bytes': 0}

    def progress(n):
        done['bytes'] += n
        pct = done['bytes'] / video.stat().st_size * 100
        print(f'\r  {pct:5.1f}%', end='', flush=True)

    t0 = time.time()
    s3.upload_file(str(video), cfg['PADEL_R2_BUCKET'], r2_key,
                   ExtraArgs={'ContentType': 'video/mp4'}, Callback=progress)
    print(f'\r  100.0%  ({time.time() - t0:.0f}s)')

    # 4 — tell the Worker: video is in, queue the job + trigger RunPod
    worker = cfg['PADEL_WORKER_URL'].rstrip('/')
    r = requests.post(f'{worker}/api/matches/{match_id}/uploaded',
                      json={'secret': cfg['PADEL_PI_SECRET'], 'r2_key': r2_key}, timeout=60)
    if not r.ok:
        sys.exit(f'Worker /uploaded failed {r.status_code}: {r.text}')
    print(f'Queued for processing: {r.json()}')
    print(f'\nCheck status:  curl {worker}/api/matches/{match_id}')
    print(f'PWA:           https://padelmind.quitlosing.in/match/{match_id}')


if __name__ == '__main__':
    main()
