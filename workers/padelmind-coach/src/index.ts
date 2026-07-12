// PadelMind — coach pose-labeling backend.
// Receives a coach's completed labels and stores them in R2 as a dataset
// (coach-labels/<session>.json). Separate from padelmind-api by design.

export interface Env {
  LABELS: R2Bucket;
}

const CORS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
};

function json(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: { 'Content-Type': 'application/json', ...CORS },
  });
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    if (request.method === 'OPTIONS') return new Response(null, { headers: CORS });

    if (request.method === 'GET' && url.pathname === '/health') {
      return json({ ok: true, service: 'padelmind-coach' });
    }

    // POST /submit — save a coach's labels as a dataset file
    if (request.method === 'POST' && url.pathname === '/submit') {
      let body: { coach?: string; clip?: string; labels?: unknown[] };
      try {
        body = await request.json();
      } catch {
        return json({ error: 'Invalid JSON' }, 400);
      }
      if (!Array.isArray(body.labels) || body.labels.length === 0) {
        return json({ error: 'No labels' }, 400);
      }

      const coach = (body.coach || 'anon').replace(/[^a-zA-Z0-9_-]/g, '').slice(0, 40) || 'anon';
      const stamp = new Date().toISOString().replace(/[:.]/g, '-');
      const key = `coach-labels/${coach}_${stamp}.json`;

      const record = {
        coach: body.coach || 'anon',
        clip: body.clip || null,
        submitted_at: new Date().toISOString(),
        count: body.labels.length,
        labels: body.labels,
      };

      await env.LABELS.put(key, JSON.stringify(record, null, 2), {
        httpMetadata: { contentType: 'application/json' },
      });

      return json({ ok: true, saved: key, count: body.labels.length });
    }

    // GET /list — how many datasets collected so far (quick sanity check)
    if (request.method === 'GET' && url.pathname === '/list') {
      const listed = await env.LABELS.list({ prefix: 'coach-labels/' });
      return json({ count: listed.objects.length, keys: listed.objects.map((o) => o.key) });
    }

    return json({ error: 'Not found' }, 404);
  },
};
