# PadelMind — Phase 0 Build Plan (Our Side)

**Owner:** Manoj Maheshwari  
**Duration:** 12 weeks (morning + weekend slots, ~15 hrs/week)  
**Goal:** Build the full infrastructure and delivery rails so that when Sasank's CV pipeline is ready, plugging it in is a one-day integration test — not a construction project.

---

## What Phase 0 Is

Phase 0 is everything on our side of the boundary defined in the Sasank SOW. We own:

| # | Component | Type |
|---|---|---|
| P0-A | Supabase schema | Foundation |
| P0-B | Cloudflare R2 bucket + upload webhook | Storage + trigger |
| P0-C | Job queue (CF Worker + Upstash Redis) | Orchestration |
| P0-D | WhatsApp delivery wiring | Delivery |
| P0-E | Club WA command parser | Input interface |
| P0-F | Player PWA | Player-facing |
| P0-G | Court calibration tool | Setup tool |
| P0-H | End-to-end integration test | Validation |

When Phase 0 is complete, we can run a full end-to-end test using **mock CV outputs** (a static heatmap PNG and a short test video). Real CV outputs drop in from Sasank's side without us touching our code again.

---

## Dependency Graph

```
P0-A (Schema)
    ├── P0-B (R2 + webhook)
    │       └── P0-C (Job queue)
    │               └── P0-D (WA delivery)    ← Sasank's RunPod calls our callback here
    ├── P0-E (Club WA parser)                 ← Talks to P0-B to signal Pi start/stop
    ├── P0-F (Player PWA)                     ← Reads from P0-A
    └── P0-G (Court calibration tool)         ← Writes keypoints to P0-A
P0-H (E2E test) requires all of the above
```

**Rule:** P0-A first. Everything else is parallelisable after schema is locked.

---

## P0-A — Supabase Schema

**Time estimate:** 2–3 days  
**Complexity:** Low — familiar stack

### Tables

```sql
-- Clubs registered on PadelMind
CREATE TABLE padel_clubs (
  id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name         text NOT NULL,
  city         text NOT NULL,
  wa_number    text NOT NULL UNIQUE,   -- club's WA number that sends commands
  active       boolean DEFAULT true,
  created_at   timestamptz DEFAULT now()
);

-- Courts within a club
CREATE TABLE padel_courts (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  club_id         uuid REFERENCES padel_clubs(id),
  name            text NOT NULL,         -- "Court 1", "Court 2"
  camera_keypoints jsonb,                -- 12 pixel coords from calibration tool
  active          boolean DEFAULT true,
  created_at      timestamptz DEFAULT now()
);

-- Players (identified by phone number)
CREATE TABLE padel_players (
  id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  phone      text NOT NULL UNIQUE,       -- E.164 format: +91XXXXXXXXXX
  name       text,
  club_id    uuid REFERENCES padel_clubs(id),
  created_at timestamptz DEFAULT now()
);

-- Match records
CREATE TABLE padel_matches (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  court_id       uuid REFERENCES padel_courts(id),
  started_at     timestamptz,
  ended_at       timestamptz,
  status         text DEFAULT 'recording',
  -- status values: recording | uploaded | queued | processing | done | failed
  video_r2_key   text,                   -- R2 object key for raw match video
  duration_sec   integer,
  created_at     timestamptz DEFAULT now()
);

-- Which players played in which match + per-player outputs
CREATE TABLE padel_match_players (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  match_id        uuid REFERENCES padel_matches(id),
  player_id       uuid REFERENCES padel_players(id),
  player_slot     integer,               -- 1–4 (maps to heatmap_p1 … heatmap_p4)
  heatmap_r2_key  text,                  -- populated by Sasank's callback
  wa_delivered    boolean DEFAULT false,
  delivered_at    timestamptz,
  UNIQUE(match_id, player_id)
);

-- Shared match outputs (not per-player)
CREATE TABLE padel_match_outputs (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  match_id         uuid REFERENCES padel_matches(id) UNIQUE,
  highlight_r2_key text,                 -- shared highlight reel
  positions_r2_key text,                 -- positions JSON (for Phase 2)
  rally_count      integer,
  rally_windows    jsonb,                -- array of {start_sec, end_sec, duration}
  zones_summary    jsonb,                -- per-player zone percentages
  created_at       timestamptz DEFAULT now()
);

-- Processing job tracker
CREATE TABLE padel_jobs (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  match_id       uuid REFERENCES padel_matches(id) UNIQUE,
  runpod_job_id  text,
  status         text DEFAULT 'queued',
  queued_at      timestamptz DEFAULT now(),
  started_at     timestamptz,
  completed_at   timestamptz,
  error_message  text
);
```

### Row-Level Security
- Club admin reads: filtered by `wa_number` claim in JWT
- Player reads: filtered by `phone` claim in JWT
- Service role (Workers, RunPod callback): full access via service key

### Acceptance test
- All tables exist, foreign keys enforce correctly
- Insert a test match, update status, join across all tables — no errors

---

## P0-B — Cloudflare R2 + Upload Webhook

**Time estimate:** 2 days  
**Complexity:** Low — same as AX patterns

### R2 Buckets

| Bucket | Contents | Access |
|---|---|---|
| `padelmind-videos` | Raw match MP4s (uploaded by Pi) | Private — pre-signed upload URLs only |
| `padelmind-outputs` | Heatmap PNGs + highlight MP4s (written by RunPod) | Public read — direct CDN URLs in WA messages |

### Pre-signed Upload URL Flow
1. Pi daemon calls our CF Worker: `POST /api/matches/{match_id}/upload-url`
2. Worker generates R2 pre-signed PUT URL (1-hour TTL)
3. Pi uses this URL to upload directly to R2 — no credentials on the Pi
4. On upload complete, R2 fires `padelmind-videos-webhook` event to our Worker

### R2 Event Notification
- Configure R2 bucket notification on `object-create` for `padelmind-videos`
- Target: CF Worker `padelmind-job-dispatcher`
- Payload includes: object key, size, match_id (encoded in key prefix)

### R2 Key Naming Convention
```
videos/{match_id}/match.mp4
outputs/{match_id}/heatmap_p1.png
outputs/{match_id}/heatmap_p2.png
outputs/{match_id}/heatmap_p3.png
outputs/{match_id}/heatmap_p4.png
outputs/{match_id}/highlights.mp4
outputs/{match_id}/positions.json
```

### Acceptance test
- Upload a test video via pre-signed URL → R2 event fires → Worker receives notification → match status updates to `uploaded`

---

## P0-C — Job Queue (CF Worker + Upstash Redis)

**Time estimate:** 3 days  
**Complexity:** Medium — first time using Upstash Redis for queue in this context

### Architecture

```
R2 upload-complete event
    → CF Worker: padelmind-job-dispatcher
        → Upstash Redis: RPUSH padelmind:jobs {match_id}
        → Supabase: UPDATE padel_matches SET status='queued'
        → Supabase: INSERT padel_jobs {match_id, status:'queued'}

RunPod GPU worker (Sasank's code, polls or uses webhook)
    → Picks up job from queue (via our API or Upstash direct)
    → Processes match
    → POST /api/matches/{match_id}/callback with outputs payload

CF Worker: padelmind-callback-receiver
    → Validates callback (shared secret)
    → Writes output URLs to padel_match_outputs
    → Updates padel_matches.status = 'done'
    → Triggers WhatsApp delivery (P0-D)
```

### Worker Endpoints

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/matches/{id}/upload-url` | Generate R2 pre-signed PUT URL for Pi |
| POST | `/api/matches/{id}/start` | Pi signals recording started |
| POST | `/api/matches/{id}/end` | Pi signals recording stopped |
| GET  | `/api/jobs/next` | RunPod polls for next job (returns match_id + R2 video URL + keypoints) |
| POST | `/api/matches/{id}/callback` | Sasank's RunPod posts outputs when done |
| GET  | `/api/matches/{id}` | Status check |

### Job Dispatch to RunPod
Two options — pick based on Sasank's preference:
1. **Polling (simpler):** RunPod worker polls `GET /api/jobs/next` every 30s. Returns null if queue empty, job payload if available.
2. **Webhook push (faster):** When job is queued, Worker POSTs to a RunPod serverless endpoint URL stored per-job. Sasank provides the endpoint.

We implement polling first (zero dependency on Sasank). Add push later if latency matters.

### Callback Payload (what Sasank POSTs to us)
```json
{
  "match_id": "uuid",
  "secret": "shared-secret-from-env",
  "rally_count": 12,
  "duration_sec": 5400,
  "rally_windows": [
    {"start_sec": 120, "end_sec": 145, "duration": 25},
    ...
  ],
  "zones": {
    "player_1": {"back_left": 0.42, "back_right": 0.31, "front_left": 0.15, "front_right": 0.12},
    ...
  },
  "outputs": {
    "heatmap_p1": "outputs/{match_id}/heatmap_p1.png",
    "heatmap_p2": "outputs/{match_id}/heatmap_p2.png",
    "heatmap_p3": "outputs/{match_id}/heatmap_p3.png",
    "heatmap_p4": "outputs/{match_id}/heatmap_p4.png",
    "highlight": "outputs/{match_id}/highlights.mp4",
    "positions": "outputs/{match_id}/positions.json"
  }
}
```

### Acceptance test
- Mock job: insert match_id directly into Upstash queue → Worker picks it up → POSTing a fake callback payload triggers delivery flow

---

## P0-D — WhatsApp Delivery

**Time estimate:** 2–3 hours (existing AX infra)  
**Complexity:** Very low — wire-up only

### What gets sent to each player after match

**Message 1 — Text summary**
```
Your PadelMind match report is ready 🎾

Match: 90 min | 14 rallies
Court coverage: Back-left 42%, Back-right 31%, Net 27%

Tap to see your full heatmap history:
https://app.padelmind.in/match/{match_id}
```

**Message 2 — Heatmap image**
- `padelmind-outputs.r2.dev/outputs/{match_id}/heatmap_p{slot}.png`
- Caption: "Your court heatmap — {player_name}"

**Message 3 — Highlight reel video**
- `padelmind-outputs.r2.dev/outputs/{match_id}/highlights.mp4`
- Caption: "Top rallies from today's match"

### Implementation
- Add `padelmind_deliver_match` function to AX router (or standalone CF Worker)
- Uses existing Meta Cloud API credentials (same WABA as AX)
- Sends to `padel_match_players.phone` for each of the 4 players
- Updates `padel_match_players.wa_delivered = true` on 200 response
- Retry logic: 3 attempts, 60s apart, on non-200

### WA Message Templates needed (Meta approval, ~24h)
Register these templates in Meta Business Manager before we build:
1. `padelmind_match_summary` — text, 3 variables: match duration, rally count, PWA link
2. `padelmind_heatmap` — image header, 1 variable: player name
3. `padelmind_highlight` — video header, no variables

**Submit templates in Week 1** — approval takes 24–48h and blocks testing.

### Acceptance test
- Trigger delivery with a real heatmap PNG + short test MP4 → all 4 player numbers receive 3 messages each

---

## P0-E — Club WA Command Parser

**Time estimate:** 2–3 days  
**Complexity:** Low — familiar AX router pattern

### Commands

```
PADEL START court1 +919820012345 +919820012346 +919820012347 +919820012348
PADEL END court1
PADEL STATUS court1
```

### PADEL START flow
1. Parse court name + 4 phone numbers from message
2. Look up court by name + club (identified by incoming WA number)
3. Auto-register any unknown phone numbers as new padel_players
4. Create `padel_matches` row with status `recording`
5. Reply to club: "Match started on Court 1. Players notified."
6. Send to each player: "Your match has started. You'll receive your highlights within 15 minutes of finishing."
7. Signal Pi daemon: POST `{pi_webhook_url}/start` with match_id

### PADEL END flow
1. Parse court name
2. Find active match for court
3. Update match status to `ending`
4. Signal Pi daemon: POST `{pi_webhook_url}/end` with match_id
5. Reply to club: "Match ended. Processing starts when video upload completes (~2 min)."

### PADEL STATUS flow
1. Look up latest match for court
2. Reply with current status + elapsed time

### Pi signal
- Pi webhook URL is stored in `padel_courts.pi_webhook_url` (set during Pi setup)
- Shared secret in `padel_courts.pi_secret`
- Pi acknowledges with HTTP 200

### Acceptance test
- Send `PADEL START court1 +91...×4` from club's WA → match created → player WAs receive start notification → Pi receives start signal

---

## P0-F — Player PWA

**Time estimate:** 8–10 days  
**Complexity:** Medium — largest piece in Phase 0

### Stack
- React + Vite + TailwindCSS
- Deployed on Cloudflare Pages
- Auth: Supabase phone OTP (no password, no app store)
- Domain: `app.padelmind.in` (or `play.padelmind.in`)

### Pages

**/ (Landing + OTP login)**
- Phone number input → OTP via Supabase Auth
- No email, no password, no social login
- First-time users land here from their WA match link

**/ home (Match history)**
- List of past matches sorted by date
- Each row: date, duration, court, rally count
- Tapping opens match detail

**/ match/{match_id} (Match detail)**
- Heatmap image (player's own)
- Highlight video player (shared reel)
- Stats: duration, rally count, zone percentages as a bar chart
- Share button: copies stats card image to clipboard

**/ profile**
- Player name (editable)
- Total matches, total rally count

### Design principles
- Mobile-first, thumb-friendly
- Court-green + amber (matches PDF brand: #1B4D3E + #D97706)
- Opens from WA in browser — must work without being "installed"
- No bottom nav on first load (player hasn't logged in yet)

### PWA features
- `manifest.json` for add-to-homescreen
- Service worker for offline caching of match data
- NOT required for MVP — add after first pilot club

### Acceptance test
- Player receives WA link → opens in browser → OTP login → sees their match → heatmap loads → highlight plays

---

## P0-G — Court Calibration Tool

**Time estimate:** 1–2 days  
**Complexity:** Low — simple browser tool

### Purpose
Run once per court at camera install time. The installer uploads a still frame from the camera and clicks 12 court keypoints. The pixel coordinates are saved to Supabase. All RunPod jobs thereafter receive these coordinates in the job payload — no re-clicking required.

### Interface
- URL: `admin.padelmind.in/calibrate/{court_id}`
- Gated by admin passphrase (simple, not per-user auth)
- Step 1: Upload still frame from camera → renders in browser
- Step 2: Court overlay guide shows where to click (12 numbered points labelled on a reference diagram)
- Step 3: Click each of the 12 keypoints on the uploaded image
- Step 4: Preview: court wireframe overlaid on image showing the homography result
- Step 5: Save → writes `padel_courts.camera_keypoints` to Supabase

### 12 keypoints (standard padel court)
Following the padel_analytics convention:
- 4 corners of the outer court boundary
- 4 inner service box corners
- 2 net posts (base)
- 2 midpoints of the net line

### Acceptance test
- Upload a test image → click 12 points → save → Supabase shows keypoints JSON → verify homography output looks correct (court wireframe aligns with image)

---

## P0-H — End-to-End Integration Test

**Time estimate:** 2–3 days (build test harness + run it)  
**Complexity:** Medium — first full-system validation

### What we're testing
With ALL of our side (P0-A through G) built, we run a full flow using **mock CV outputs** to confirm the entire pipe works before Sasank hands us anything.

### Mock test flow

```
1. Club WA sends: PADEL START court1 +91×4
   → match created, players notified, Pi signalled

2. Mock Pi upload: PUT a test video to R2 via pre-signed URL
   → R2 event fires → job enqueued → match status = queued

3. Mock RunPod poll: GET /api/jobs/next
   → returns match_id + R2 video URL + keypoints

4. Mock RunPod callback: POST /api/matches/{id}/callback
   with real heatmap PNGs + test highlight video in correct R2 paths

5. Verify:
   → WhatsApp delivers 3 messages to all 4 test player numbers
   → Player PWA shows the match with correct heatmap + video
   → All DB tables have correct status
```

### Test materials
- 4 test WA numbers (Manoj's own + 3 others)
- 1 static heatmap PNG (hand-drawn or matplotlib mock)
- 1 short video clip (<15MB, any padel footage)
- 1 test court with calibration keypoints stored

### Acceptance: DONE when
All 4 test phones receive the 3 WA messages, and all 4 can open the PWA and view the match. Zero manual steps after `PADEL END`.

---

## Week-by-Week Timeline

| Week | Focus | Deliverable |
|---|---|---|
| 1 | P0-A schema + Supabase project setup | All tables created, RLS in place, local dev working |
| 1 | Submit WA message templates to Meta | Template approval in queue (unblocks Week 5) |
| 2 | P0-B R2 buckets + pre-signed URL Worker | Pi can upload; R2 event fires correctly |
| 3 | P0-C Job queue — Upstash + Worker endpoints | Job enqueues on upload; `/api/jobs/next` returns payload |
| 3 | P0-G Court calibration tool | Keypoints saved to Supabase from browser |
| 4 | P0-E Club WA command parser | PADEL START/END parsed; match created; Pi signalled |
| 5 | P0-D WhatsApp delivery (templates approved by now) | 3 messages fire on callback receipt |
| 6–8 | P0-F Player PWA | OTP login, match history, heatmap, highlight player |
| 9 | P0-C callback + P0-D integration | Callback → delivery fully wired |
| 10 | P0-H end-to-end test | Full mock flow passes on real WA numbers |
| 11 | Buffer + fixes from E2E test | Edge cases, error handling, retries |
| 12 | Pilot club onboarding prep | Court calibrated, club WA registered, players pre-loaded |

---

## Integration Contracts with Sasank

These are the **exact API shapes** Sasank's code will call. We build our side; he calls these endpoints. No negotiation needed mid-build.

### What Sasank calls on our side

**GET `/api/jobs/next`** (Pi polls for new upload URLs; RunPod polls for jobs)
```json
Response 200:
{
  "match_id": "uuid",
  "video_url": "https://r2-presigned-url-for-download",
  "keypoints": [[x1,y1], [x2,y2], ...],  // 12 points
  "player_slots": {
    "1": "+919820012345",
    "2": "+919820012346",
    "3": "+919820012347",
    "4": "+919820012348"
  }
}

Response 204: No jobs in queue
```

**POST `/api/matches/{match_id}/upload-url`** (Pi requests pre-signed URL before upload)
```json
Request: { "secret": "pi-shared-secret" }
Response: { "upload_url": "https://r2-presigned-put-url", "expires_in": 3600 }
```

**POST `/api/matches/{match_id}/callback`** (RunPod posts when processing complete)
```json
Request:
{
  "secret": "runpod-shared-secret",
  "rally_count": 14,
  "duration_sec": 5400,
  "rally_windows": [...],
  "zones": { "player_1": {...}, "player_2": {...}, "player_3": {...}, "player_4": {...} },
  "outputs": {
    "heatmap_p1": "outputs/{match_id}/heatmap_p1.png",
    "heatmap_p2": "outputs/{match_id}/heatmap_p2.png",
    "heatmap_p3": "outputs/{match_id}/heatmap_p3.png",
    "heatmap_p4": "outputs/{match_id}/heatmap_p4.png",
    "highlight": "outputs/{match_id}/highlights.mp4",
    "positions": "outputs/{match_id}/positions.json"
  }
}
Response: { "ok": true }
```

---

## What Is NOT in Phase 0

| Item | When |
|---|---|
| Shot classifier | Phase 2 (needs coach + ML specialist) |
| Pose estimation | Phase 2 |
| Ball tracking | Phase 2 |
| Dual-camera merge | Phase 2 |
| Club admin dashboard (web) | After first paying club |
| Skill scores / drill recommendations | Phase 2 |
| India cloud GPU (AWS Mumbai) | Phase 2 (scale trigger: 25+ courts) |
| iOS / Android native app | After Series A (PWA handles Phase 1) |

---

## Build Environment

| Tool | We use |
|---|---|
| Database | Supabase (same project as AX or new sibling project) |
| Storage | Cloudflare R2 |
| Serverless | Cloudflare Workers (TypeScript) |
| Frontend | React + Vite + Tailwind, deployed on Cloudflare Pages |
| Queue | Upstash Redis (Serverless) |
| WA delivery | AX Meta Cloud API (existing WABA) |
| Local dev | `wrangler dev` for Workers, Vite dev server for PWA |
| Deploy | `wrangler publish` + Cloudflare Pages Git integration |

---

*Phase 0 Build Plan — PadelMind by AutomationXpert*  
*Author: Manoj Maheshwari · 2026-07-10*  
*Companion: SASANK_SOW_PHASE1.md (contractor scope) · SON_PHASE_PLAN_REVIEW.md (tech review)*
