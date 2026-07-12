import { AwsClient } from 'aws4fetch';

export interface Env {
  VIDEOS: R2Bucket;
  OUTPUTS: R2Bucket;
  SUPABASE_URL: string;
  SUPABASE_SERVICE_KEY: string;
  UPSTASH_REDIS_URL: string;
  UPSTASH_REDIS_TOKEN: string;
  PI_SHARED_SECRET: string;
  RUNPOD_SHARED_SECRET: string;
  RUNPOD_API_KEY: string;
  RUNPOD_ENDPOINT_ID: string;
  META_ACCESS_TOKEN: string;
  META_PHONE_NUMBER_ID: string;
  // R2 S3 credentials — for phone-direct presigned uploads (set via wrangler secret)
  R2_ACCOUNT_ID: string;
  R2_ACCESS_KEY_ID: string;
  R2_SECRET_ACCESS_KEY: string;
}

// ─── Supabase helpers ────────────────────────────────────────────────────────

async function sbQuery(env: Env, path: string, options: RequestInit = {}) {
  const res = await fetch(`${env.SUPABASE_URL}/rest/v1${path}`, {
    ...options,
    headers: {
      apikey: env.SUPABASE_SERVICE_KEY,
      Authorization: `Bearer ${env.SUPABASE_SERVICE_KEY}`,
      'Content-Type': 'application/json',
      Prefer: 'return=representation',
      ...(options.headers || {}),
    },
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`Supabase error ${res.status}: ${err}`);
  }
  const text = await res.text();
  return text ? JSON.parse(text) : null;
}

// ─── Upstash Redis helpers ───────────────────────────────────────────────────

async function redisCmd(env: Env, ...args: string[]) {
  const res = await fetch(`${env.UPSTASH_REDIS_URL}/${args.map(encodeURIComponent).join('/')}`, {
    headers: { Authorization: `Bearer ${env.UPSTASH_REDIS_TOKEN}` },
  });
  const data = await res.json() as { result: unknown };
  return data.result;
}

async function enqueueJob(env: Env, matchId: string) {
  await redisCmd(env, 'rpush', 'padelmind:jobs', matchId);
}

async function dequeueJob(env: Env): Promise<string | null> {
  const result = await redisCmd(env, 'lpop', 'padelmind:jobs');
  return result as string | null;
}

// ─── Router ─────────────────────────────────────────────────────────────────

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    const path = url.pathname;
    const method = request.method;

    // POST /api/matches/:id/upload-url — Pi requests pre-signed R2 PUT URL
    const uploadUrlMatch = path.match(/^\/api\/matches\/([^/]+)\/upload-url$/);
    if (method === 'POST' && uploadUrlMatch) {
      return handleUploadUrl(request, env, uploadUrlMatch[1]);
    }

    // POST /api/matches/:id/start — Pi signals recording started
    const startMatch = path.match(/^\/api\/matches\/([^/]+)\/start$/);
    if (method === 'POST' && startMatch) {
      return handleMatchStart(request, env, startMatch[1]);
    }

    // POST /api/matches/:id/end — Pi signals recording stopped
    const endMatch = path.match(/^\/api\/matches\/([^/]+)\/end$/);
    if (method === 'POST' && endMatch) {
      return handleMatchEnd(request, env, endMatch[1]);
    }

    // POST /api/matches/:id/uploaded — video is in R2 (iPad ingest script or Pi); queue processing
    const uploadedMatch = path.match(/^\/api\/matches\/([^/]+)\/uploaded$/);
    if (method === 'POST' && uploadedMatch) {
      return handleUploaded(request, env, uploadedMatch[1]);
    }

    // GET /api/jobs/next — RunPod polls for next job
    if (method === 'GET' && path === '/api/jobs/next') {
      return handleJobNext(request, env);
    }

    // POST /api/matches/:id/callback — RunPod posts outputs when done
    const callbackMatch = path.match(/^\/api\/matches\/([^/]+)\/callback$/);
    if (method === 'POST' && callbackMatch) {
      return handleCallback(request, env, callbackMatch[1]);
    }

    // GET /api/matches/:id — status check
    const statusMatch = path.match(/^\/api\/matches\/([^/]+)$/);
    if (method === 'GET' && statusMatch) {
      return handleMatchStatus(request, env, statusMatch[1]);
    }

    // POST /api/courts/:id/keypoints — admin saves calibration keypoints
    const keypointsMatch = path.match(/^\/api\/courts\/([^/]+)\/keypoints$/);
    if (method === 'POST' && keypointsMatch) {
      return handleSaveKeypoints(request, env, keypointsMatch[1]);
    }

    // GET /health
    if (method === 'GET' && path === '/health') {
      return json({ ok: true, service: 'padelmind-api' });
    }

    // OPTIONS — CORS preflight
    if (method === 'OPTIONS') {
      return cors();
    }

    return json({ error: 'Not found' }, 404);
  },
};

// ─── Handlers ────────────────────────────────────────────────────────────────

// Phone-direct upload: return a real presigned R2 PUT URL so the phone uploads
// the (multi-GB) match file straight to storage — no Mac, no creds on the client.
async function handleUploadUrl(request: Request, env: Env, matchId: string): Promise<Response> {
  // Gate: the match must exist (created by the logged-in player in the app).
  const matches = await sbQuery(env, `/padel_matches?id=eq.${matchId}&select=id`);
  if (!matches?.length) return json({ error: 'Match not found' }, 404);
  if (!env.R2_ACCESS_KEY_ID) return json({ error: 'R2 credentials not configured on Worker' }, 500);

  const key = `videos/${matchId}/match.mp4`;
  const endpoint = `https://${env.R2_ACCOUNT_ID}.r2.cloudflarestorage.com/padelmind-videos/${key}`;

  const r2 = new AwsClient({
    accessKeyId: env.R2_ACCESS_KEY_ID,
    secretAccessKey: env.R2_SECRET_ACCESS_KEY,
    service: 's3',
    region: 'auto',
  });
  // Presign a PUT valid for 2 hours (a long match upload over club WiFi)
  const signed = await r2.sign(
    new Request(`${endpoint}?X-Amz-Expires=7200`, { method: 'PUT' }),
    { aws: { signQuery: true } }
  );

  return json({ upload_url: signed.url, key, match_id: matchId });
}

async function handleMatchStart(request: Request, env: Env, matchId: string): Promise<Response> {
  const body = await request.json() as { secret: string };
  if (body.secret !== env.PI_SHARED_SECRET) return json({ error: 'Unauthorized' }, 401);

  await sbQuery(env, `/padel_matches?id=eq.${matchId}`, {
    method: 'PATCH',
    body: JSON.stringify({ started_at: new Date().toISOString(), status: 'recording' }),
  });

  return json({ ok: true });
}

async function handleMatchEnd(request: Request, env: Env, matchId: string): Promise<Response> {
  const body = await request.json() as { secret: string };
  if (body.secret !== env.PI_SHARED_SECRET) return json({ error: 'Unauthorized' }, 401);

  await sbQuery(env, `/padel_matches?id=eq.${matchId}`, {
    method: 'PATCH',
    body: JSON.stringify({ ended_at: new Date().toISOString(), status: 'uploaded' }),
  });

  // Enqueue job for RunPod
  await enqueueJob(env, matchId);

  await sbQuery(env, '/padel_jobs', {
    method: 'POST',
    body: JSON.stringify({ match_id: matchId, status: 'queued' }),
  });

  await sbQuery(env, `/padel_matches?id=eq.${matchId}`, {
    method: 'PATCH',
    body: JSON.stringify({ status: 'queued' }),
  });

  // Trigger RunPod serverless endpoint directly
  await triggerRunPod(env, matchId);

  return json({ ok: true });
}

// Called AFTER the video is confirmed in R2 — the only place a job should be enqueued.
// Sources: ingest/ingest_match.py (iPad recording) or the Pi recorder's upload worker.
async function handleUploaded(request: Request, env: Env, matchId: string): Promise<Response> {
  const body = await request.json() as { secret?: string; r2_key?: string };
  // Auth: the Mac/Pi path presents the PI secret. The app path presents no secret
  // and is gated instead by the video actually being present in R2 (checked below)
  // — you can only trigger processing for a match whose file already uploaded.
  if (body.secret && body.secret !== env.PI_SHARED_SECRET) return json({ error: 'Unauthorized' }, 401);

  const videoKey = body.r2_key || `videos/${matchId}/match.mp4`;

  // Verify the object actually exists in R2 before queueing (this IS the app-path gate)
  const head = await env.VIDEOS.head(videoKey);
  if (!head) return json({ error: `Video not found in R2: ${videoKey}` }, 400);

  await sbQuery(env, `/padel_matches?id=eq.${matchId}`, {
    method: 'PATCH',
    body: JSON.stringify({ status: 'queued', video_r2_key: videoKey }),
  });

  await enqueueJob(env, matchId);

  await sbQuery(env, '/padel_jobs', {
    method: 'POST',
    body: JSON.stringify({ match_id: matchId, status: 'queued' }),
    headers: { Prefer: 'resolution=merge-duplicates' },
  });

  await triggerRunPod(env, matchId);

  return json({ ok: true, match_id: matchId, video_r2_key: videoKey });
}

async function handleJobNext(request: Request, env: Env): Promise<Response> {
  const matchId = await dequeueJob(env);
  if (!matchId) return new Response(null, { status: 204 });

  // Fetch match + court keypoints + player slots
  const matches = await sbQuery(env,
    `/padel_matches?id=eq.${matchId}&select=*,padel_courts(camera_keypoints),padel_match_players(player_slot,player_phone,padel_players(phone))`
  );
  if (!matches?.length) return json({ error: 'Match not found' }, 404);

  const match = matches[0];
  const videoKey = match.video_r2_key || `videos/${matchId}/match.mp4`;

  // Build player slots map — player_phone covers opt-in players with no padel_players row
  const playerSlots: Record<string, string> = {};
  for (const mp of match.padel_match_players || []) {
    playerSlots[String(mp.player_slot)] = mp.padel_players?.phone || mp.player_phone || '';
  }

  // Mark job as dispatched
  await sbQuery(env, `/padel_jobs?match_id=eq.${matchId}`, {
    method: 'PATCH',
    body: JSON.stringify({ status: 'dispatched', started_at: new Date().toISOString() }),
  });
  await sbQuery(env, `/padel_matches?id=eq.${matchId}`, {
    method: 'PATCH',
    body: JSON.stringify({ status: 'processing' }),
  });

  return json({
    match_id: matchId,
    video_r2_key: videoKey,
    keypoints: match.padel_courts?.camera_keypoints || [],
    player_slots: playerSlots,
  });
}

async function handleCallback(request: Request, env: Env, matchId: string): Promise<Response> {
  const body = await request.json() as {
    secret: string;
    rally_count: number;
    duration_sec: number;
    rally_windows: unknown[];
    zones: Record<string, unknown>;
    outputs: {
      heatmap_p1: string; heatmap_p2: string;
      heatmap_p3: string; heatmap_p4: string;
      highlight: string; positions: string;
    };
  };

  if (body.secret !== env.RUNPOD_SHARED_SECRET) return json({ error: 'Unauthorized' }, 401);

  // Write outputs to DB
  await sbQuery(env, '/padel_match_outputs', {
    method: 'POST',
    body: JSON.stringify({
      match_id: matchId,
      highlight_r2_key: body.outputs.highlight,
      positions_r2_key: body.outputs.positions,
      rally_count: body.rally_count,
      rally_windows: body.rally_windows,
      zones_summary: body.zones,
    }),
    headers: { Prefer: 'resolution=merge-duplicates' },
  });

  // Update per-player heatmap keys
  for (let slot = 1; slot <= 4; slot++) {
    const key = body.outputs[`heatmap_p${slot}` as keyof typeof body.outputs];
    if (key) {
      await sbQuery(env, `/padel_match_players?match_id=eq.${matchId}&player_slot=eq.${slot}`, {
        method: 'PATCH',
        body: JSON.stringify({ heatmap_r2_key: key }),
      });
    }
  }

  // Update match + job status
  await sbQuery(env, `/padel_matches?id=eq.${matchId}`, {
    method: 'PATCH',
    body: JSON.stringify({ status: 'done', duration_sec: body.duration_sec }),
  });
  await sbQuery(env, `/padel_jobs?match_id=eq.${matchId}`, {
    method: 'PATCH',
    body: JSON.stringify({ status: 'done', completed_at: new Date().toISOString() }),
  });

  // Trigger WhatsApp delivery (fire and forget)
  const ctx = { waitUntil: (p: Promise<unknown>) => p };
  ctx.waitUntil(deliverWhatsApp(env, matchId, body.outputs, body.rally_count, body.duration_sec));

  return json({ ok: true });
}

async function handleMatchStatus(request: Request, env: Env, matchId: string): Promise<Response> {
  const matches = await sbQuery(env, `/padel_matches?id=eq.${matchId}&select=id,status,started_at,ended_at,duration_sec`);
  if (!matches?.length) return json({ error: 'Not found' }, 404);
  return json(matches[0]);
}

async function triggerRunPod(env: Env, matchId: string) {
  if (!env.RUNPOD_ENDPOINT_ID || !env.RUNPOD_API_KEY) return;

  // Fetch match + keypoints + player slots to pass directly to RunPod
  const matches = await sbQuery(env,
    `/padel_matches?id=eq.${matchId}&select=*,padel_courts(camera_keypoints),padel_match_players(player_slot,player_phone,padel_players(phone))`
  );
  if (!matches?.length) return;

  const match = matches[0];
  const playerSlots: Record<string, string> = {};
  for (const mp of match.padel_match_players || []) {
    playerSlots[String(mp.player_slot)] = mp.padel_players?.phone || mp.player_phone || '';
  }

  await fetch(`https://api.runpod.io/v2/${env.RUNPOD_ENDPOINT_ID}/run`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${env.RUNPOD_API_KEY}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      input: {
        match_id: matchId,
        video_r2_key: match.video_r2_key || `videos/${matchId}/match.mp4`,
        keypoints: match.padel_courts?.camera_keypoints || null,
        player_slots: playerSlots,
      },
    }),
  });
}

async function handleSaveKeypoints(request: Request, env: Env, courtId: string): Promise<Response> {
  const body = await request.json() as { secret: string; keypoints: unknown };
  if (body.secret !== env.PI_SHARED_SECRET) return json({ error: 'Unauthorized' }, 401);

  await sbQuery(env, `/padel_courts?id=eq.${courtId}`, {
    method: 'PATCH',
    body: JSON.stringify({ camera_keypoints: body.keypoints }),
  });

  return json({ ok: true, court_id: courtId });
}

// ─── WhatsApp Delivery ───────────────────────────────────────────────────────

const PUB_BASE = 'https://pub-04c202b65f234888bf415f2ec899d7f8.r2.dev';

async function deliverWhatsApp(
  env: Env,
  matchId: string,
  outputs: { heatmap_p1: string; heatmap_p2: string; heatmap_p3: string; heatmap_p4: string; highlight: string },
  rallyCount: number,
  durationSec: number,
) {
  const players = await sbQuery(env,
    `/padel_match_players?match_id=eq.${matchId}&select=player_slot,player_phone,padel_players(phone,name)`
  );
  if (!players?.length) return;

  const durationMin = Math.round(durationSec / 60);
  const pwaDomain = 'https://padelmind.quitlosing.in';

  for (const mp of players) {
    const phone = mp.padel_players?.phone || mp.player_phone;
    const name = mp.padel_players?.name || 'Player';
    const slot = mp.player_slot;
    if (!phone) continue;

    const heatmapKey = outputs[`heatmap_p${slot}` as keyof typeof outputs];
    const heatmapUrl = `${PUB_BASE}/${heatmapKey}`;
    const highlightUrl = `${PUB_BASE}/${outputs.highlight}`;
    const pwaUrl = `${pwaDomain}/match/${matchId}`;

    const summary = `Your PadelMind match report is ready 🎾\n\nMatch: ${durationMin} min | ${rallyCount} rallies\n\nFull history: ${pwaUrl}`;

    await sendWAText(env, phone, summary);
    await sendWAImage(env, phone, heatmapUrl, `Your court heatmap — ${name}`);
    await sendWAVideo(env, phone, highlightUrl, 'Top rallies from today\'s match');

    // Mark delivered
    await sbQuery(env, `/padel_match_players?match_id=eq.${matchId}&player_slot=eq.${slot}`, {
      method: 'PATCH',
      body: JSON.stringify({ wa_delivered: true, delivered_at: new Date().toISOString() }),
    });
  }
}

async function metaPost(env: Env, body: unknown) {
  const res = await fetch(
    `https://graph.facebook.com/v19.0/${env.META_PHONE_NUMBER_ID}/messages`,
    {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${env.META_ACCESS_TOKEN}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    }
  );
  if (!res.ok) {
    const err = await res.text();
    console.error(`[WA] Meta API error ${res.status}: ${err}`);
  }
}

async function sendWAText(env: Env, phone: string, text: string) {
  await metaPost(env, {
    messaging_product: 'whatsapp',
    to: phone,
    type: 'text',
    text: { body: text },
  });
}

async function sendWAImage(env: Env, phone: string, url: string, caption: string) {
  await metaPost(env, {
    messaging_product: 'whatsapp',
    to: phone,
    type: 'image',
    image: { link: url, caption },
  });
}

async function sendWAVideo(env: Env, phone: string, url: string, caption: string) {
  await metaPost(env, {
    messaging_product: 'whatsapp',
    to: phone,
    type: 'video',
    video: { link: url, caption },
  });
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

function json(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    },
  });
}

function cors(): Response {
  return new Response(null, {
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    },
  });
}
