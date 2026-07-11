# 60-Day Execution Plan
## From Camera-Live to Customer-Ready UI — PadelMind by AutomationXpert

**Document version:** 1.0
**Date:** 2026-07-03
**Author:** Manoj Maheshwari
**Companion:** `TECHNICAL_FEASIBILITY_REPORT.md`, `NSCI_PROPOSAL.md`, `PROJECT_REPORT.md`
**Target:** Model trained + PWA shipped + WhatsApp delivery live by **Day 60**
**Buffer:** Days 61–90 of the NSCI 90-day window used for coach blind audit, edge-case remediation, and commercial-launch dress rehearsal
**Day 91:** Commercial phase begins per NSCI proposal

---

## 0. Reading this document

The 60 days are structured as **9 parallel workstreams**, gated by **6 hard milestones**. Each workstream has an owner, a deliverable, a resource cost, and a "definition of done." Where two workstreams must handshake (e.g., pipeline emits shots → classifier consumes them), the interface contract is stated explicitly.

The plan assumes the NSCI proposal is approved and hardware is installed on Day 0. If installation slips, every downstream date slips by the same amount — data capture is on the critical path.

---

## 1. The signal path — what happens to a match, stage by stage

Every match played on the NSCI courts flows through **13 sequential stages** from photon capture to coaching insight. This is the pipeline the 60-day plan builds and validates.

| # | Stage | Where it runs | Input | Output | Latency budget |
|---|---|---|---|---|---|
| 1 | Photon → sensor | Reolink RLC-823A 4K IP camera, mounted 4–5m high behind back glass | Ambient light off court | H.265 RTSP stream @ 3840×2160, 30fps | Real-time |
| 2 | RTSP relay + segmentation | MediaMTX on Raspberry Pi 5 edge box | RTSP stream | 10-min MP4 chunks on local NVMe | Real-time |
| 3 | Match window detection | Python daemon on Pi 5 (motion + court-occupancy heuristic) | MP4 chunks | Match start/end timestamps + concatenated match MP4 | 1 min post-match |
| 4 | Upload to cloud | Pi 5 → Cloudflare R2 over 4G/5G modem | Match MP4 (~3 GB per 60-min match) | R2 object URL + webhook event | 3–8 min depending on cell signal |
| 5 | Job dispatch | Cloudflare Worker webhook → Upstash Redis queue → RunPod worker wake | R2 event | GPU worker booted, video downloaded | 30 sec |
| 6 | Decode + downsample | RunPod RTX 3090 (ffmpeg + GPU decode) | 4K MP4 | 1080p30 frame tensor | 30 sec |
| 7 | Player tracking | YOLOv8m + ByteTrack (from `padel_analytics` fork) | 1080p frames | Per-frame player bounding boxes + persistent IDs (1–4) | 80 sec |
| 8 | Pose estimation | YOLOv8-pose 13-DOF (from `padel_analytics` fork) | Player crops | 13 joint keypoints × 4 players × N frames | (Bundled with stage 7 above) |
| 9 | Ball tracking | TrackNet + InpaintNet, retrained on padel ball | Full-frame sequence | Ball (x, y) per frame + occlusion gaps filled | 40 sec |
| 10 | Court homography | Precomputed 12-point matrix from install-day calibration | Pixel coords | Top-down metric coords for players + ball | Trivial (<1 sec) |
| 11 | Shot-impact segmentation | Rule-based velocity-change detector on ball trajectory | Ball trajectory | List of shot events (timestamp, executor player ID, ball trajectory features) | 10 sec |
| 12 | **Shot classifier + quality scoring** | Our trained MLP (Stage A class head + Stage B quality head + Stage C deviation-flag head) | Per-shot feature vector (~390-dim) | Shot class (14 options) + quality 1–5 + deviation flags | 5 sec |
| 13 | Delivery composition | Cloudflare Worker + AutomationXpert WA router | Per-shot JSONL + summary JSON | WhatsApp message with skill score, top-3 weak shots, drill recs, highlight clip | 20 sec |

**Match-end to player-WhatsApp target: 10–12 min P95.**

Stages 1–4 are hardware + plumbing. Stages 6–11 are forked OSS with retraining. **Stage 12 is the singular custom asset — the moat.** Stage 13 rides on AutomationXpert infrastructure that already exists.

---

## 2. The 6 milestone gates

The 60 days are governed by six binary gates. Missing any gate triggers the escalation plan in §7.

| Gate | Day | What it proves |
|---|---|---|
| **G1 — First frame captured** | Day 3 | Camera live, RTSP stream reaches cloud, first match MP4 sits in R2 |
| **G2 — First shot detected end-to-end** | Day 14 | Full pipeline stages 1–11 run on a real NSCI match; shot events produced (unclassified yet) |
| **G3 — First 200 labelled clips banked** | Day 21 | Coach + labeller team producing clips at design velocity; taxonomy locked |
| **G4 — Classifier V0 hits 55% top-1** | Day 35 | Proof the classifier approach works; permission to keep iterating |
| **G5 — Classifier V1 hits 70% top-1** | Day 50 | Ship criterion for the moat layer met |
| **G6 — End-to-end demo delivered to player WhatsApp** | Day 60 | Player receives a real match report with skill score, weaknesses, drills, and highlight clip |

---

## 3. The 9 workstreams — what each stream builds and who owns it

Each workstream runs in parallel from Day 0. Handshakes between streams are called out where they occur.

### WS-A — Hardware install + live feed
**Owner:** Hardware lead (contract, ~₹40k/mo for 2 months) + Manoj coordinating with NSCI
**Days 0–5.**

| Task | Days |
|---|---|
| Site walk with NSCI maintenance; identify electrical point; confirm mount positions | Day −2 to 0 |
| Procure 2× Reolink RLC-823A, 2× Pi 5 + NVMe, 1× 4G/5G modem, PoE switch, cabling, IP66 enclosures | Days 0–3 (parallel with site walk) |
| Install day: mount cameras, run Cat6, install Pi 5 + modem in weatherproof enclosure, do 12-point court keypoint clicks per court | Day 3 (single 2-hour morning window) |
| Configure MediaMTX + segmentation daemon on both Pi units; connect to Cloudflare R2 upload | Days 3–5 |
| Install 1× courtside pause button per court + wire to state-machine service | Day 4 |
| Post informational signage at both courts | Day 3 |
| Heartbeat + health monitor live in Grafana | Day 5 |

**Definition of done:** Both courts streaming; first match MP4 auto-uploaded to R2; pause button toggles recording; signage up. **This is G1.**

**Resources:** ₹90k hardware BOM (2 courts × ~₹40k + spares), 1 electrician for 2 hours, 1 install lead.

---

### WS-B — Data capture + labelling ops
**Owner:** Coach (part-time, ₹40k/mo retainer) + 2 labellers (₹15k/mo each)
**Days 0–60.**

The bottleneck for the whole project is labelled clips. This stream must not stall.

| Task | Days |
|---|---|
| Coach authors 15-page taxonomy + rubric document (14 shot classes, quality 1–5 rubric, deviation flag glossary) | Days 0–7 |
| Coach labels 100 "gold-standard" clips — the reference set for training the labellers | Days 7–12 |
| Build Streamlit labelling tool (see WS-C below for engineering) | Days 5–8 (WS-C hands over) |
| Recruit + onboard 2 labellers (existing padel players preferred, part-time OK) | Days 5–10 |
| Labeller ramp: 50 clips each week 2 → 100 each week 3 → 150 each week 4 onwards | Days 10–60 |
| Coach 10% weekly audit of labeller output; inter-rater reliability tracked | Weekly from Day 14 |
| Import supplementary clips from PadelVic public dataset (~150 clips) to bootstrap class balance | Days 10–14 |

**Definition of done Week 3 (G3):** 200 labelled clips in the training corpus with all 14 classes represented and inter-rater kappa ≥ 0.7.

**Definition of done Day 50:** 700 labelled clips, class-balanced, held-out 15% test set frozen.

**Resources:** Coach ₹80k over 2 months, 2 labellers ₹60k over 2 months, ₹5k labelling tool infra. Total ~₹145k.

---

### WS-C — CV pipeline fork + hardening
**Owner:** CTO/ML lead (full-time from Day 0) + 1 CV engineer (contract from Day 7, ₹1.2L/mo)
**Days 0–35.**

This stream forks the OSS and turns it into a production pipeline that ingests our NSCI match MP4s and emits per-shot features ready for the classifier.

| Task | Days |
|---|---|
| Fork `Joao-M-Silva/padel_analytics` into private repo `automationxpert/padelmind-pipeline`; strip UI, keep only inference nodes | Days 0–3 |
| Wrap pipeline in a queue-consumer worker that reads R2 events, downloads video, runs stages 6–11, writes shots-JSONL back to R2 + Postgres | Days 3–10 |
| Retrain TrackNet on padel ball (yellow, faster than tennis) using PadelVic + first NSCI captures | Days 7–14 |
| Retrain court keypoint detector for padel court geometry (or use manual 12-point cache for V1 — decision Day 5) | Days 7–10 |
| Build shot-impact segmentation logic — ball velocity direction-change detector with wall-bounce handling specific to padel | Days 10–18 |
| Build Streamlit labelling tool that reads shot events, plays the ±1s clip, exposes 14-class dropdown + quality slider + deviation checkboxes, writes to labels table | Days 5–10 |
| Pipeline observability: Sentry hooks, per-stage timing metrics, failure-mode dashboards | Days 15–20 |
| Harden for reliability: retry on transient failures, dead-letter queue for corrupt matches, graceful "no ball detected" fallback | Days 20–30 |
| Ship-ready pipeline v1.0 tagged | Day 35 |

**Definition of done Day 14 (G2):** Real NSCI match MP4 → pipeline → shots-JSONL in Postgres. Class field null but every other field populated.

**Definition of done Day 35:** Pipeline runs unattended on the queue; P99 crash rate <1%; per-stage latency within budget in §1.

**Resources:** CTO/ML full-time (co-founder equity + ₹1.5L/mo stipend), CV engineer ₹1.2L × 2 mo = ₹2.4L, RunPod compute ~₹15k for training runs.

---

### WS-D — Shot classifier training (the moat)
**Owner:** CTO/ML lead
**Days 15–50.**

Waits for WS-B to produce first 200 clips (G3, Day 21). From then it iterates weekly until G5.

| Task | Days |
|---|---|
| Feature extraction module: given a shot event, compute the 390-dim feature vector (pose sequence + court-relative position + ball trajectory + opponent positions) | Days 15–22 |
| V0 classifier — small MLP, 14-class head only, no quality head — trained on first 200 clips | Days 22–28 |
| V0 accuracy readout on 15% held-out test set; class confusion matrix; identify hardest 3 classes | Day 28 |
| Add quality-regression head; retrain on all 400 clips available by Day 35 | Days 28–35 |
| Add deviation-flag multi-label head; retrain on all 600 clips available by Day 42 | Days 35–42 |
| Iteration loop: analyse errors → request specific labels from coach → retrain — weekly | Days 28–50 |
| If accuracy plateau, escalate: bring in a senior CV contractor for 2-week engagement, try ensemble (MLP + temporal CNN), try MotionBERT adaptation | Days 42–50 if triggered |
| V1 classifier frozen; model artefact registered; served via FastAPI on RunPod | Day 50 |

**Definition of done Day 35 (G4):** V0 hits ≥ 55% top-1 on held-out test set. Below this triggers the escalation plan.

**Definition of done Day 50 (G5):** V1 hits ≥ 70% top-1 and quality MAE ≤ 0.7.

**Resources:** ~₹20k RunPod compute for training runs, ₹1L reserved for senior CV contractor if escalation triggered.

---

### WS-E — Backend + data model
**Owner:** Full-stack engineer (contract from Day 3, ₹1L/mo) reporting to CTO
**Days 3–45.**

| Task | Days |
|---|---|
| Supabase project provisioned; schemas per §7 of feasibility report (players, clubs, courts, matches, shots, skill_scores, drills, highlights, labels, audit_events) | Days 3–7 |
| RLS policies: players see only their matches; club admins see their courts only | Days 7–10 |
| Cloudflare Workers: upload webhook, auth token issuance, signed URL generator for R2 | Days 5–14 |
| Player identity + tap-in flow: QR code at courtside → scan → WhatsApp number → linked to match | Days 14–24 |
| Skill-score engine: ELO-style updater triggered post-match; time-series snapshot in `skill_scores` | Days 24–32 |
| Drill recommender: rule-based Day 1 (`weak_class` → mapped drill from coach-authored catalogue); ML-based later | Days 32–38 |
| Audit-log service for pause-button events + WhatsApp opt-out requests (per NSCI proposal transparency commitment) | Days 24–28 |
| API surface for PWA + club dashboard: REST + Realtime channels | Days 20–45 |

**Definition of done Day 45:** All PWA-consumable endpoints stable; RLS verified with 4 test tenants; audit log queryable by pause-button event.

**Resources:** Full-stack engineer ₹1L × 2 mo = ₹2L, Supabase Pro ₹2k/mo, Cloudflare paid ₹500/mo.

---

### WS-F — Player PWA (customer-facing UI)
**Owner:** Frontend engineer (contract from Day 15, ₹1L/mo)
**Days 15–58.**

| Task | Days |
|---|---|
| React + Vite scaffold on Cloudflare Pages; PadelMind design system (colour, type, iconography) | Days 15–20 |
| Auth flow: WhatsApp OTP via AutomationXpert router; token stored in Supabase Auth | Days 18–24 |
| Home screen: current skill score, last match summary card, next-match teaser | Days 20–28 |
| Match detail: 4-player scoreboard, per-shot breakdown, quality distribution chart, top-3 weaknesses, drill cards | Days 24–36 |
| Highlight clips player: 3 auto-extracted 6-sec MP4s, share-to-WhatsApp button, share-to-Instagram button | Days 30–40 |
| Skill trajectory chart: player ELO over time (Recharts) | Days 32–38 |
| Post-match survey (NPS + free-text) shown on 3rd match onwards | Days 40–46 |
| Opt-out UI: player self-service to pause their own future recordings even without touching the courtside button | Days 40–46 |
| PWA install prompt + offline stub | Days 46–52 |
| Cross-device QA: iOS Safari, Android Chrome, small-screen edge cases | Days 52–58 |

**Definition of done Day 58:** Player can go from a WhatsApp deep-link to a complete match report on iPhone or Android in under 4 seconds cold-load.

**Resources:** Frontend engineer ₹1L × 1.5 mo = ₹1.5L, design tokens/assets ₹20k.

---

### WS-G — Club dashboard
**Owner:** Frontend engineer (shared with WS-F, second half of their allocation)
**Days 35–58.**

| Task | Days |
|---|---|
| Same React app, role-gated `/club/*` routes | Days 35–40 |
| Court occupancy view (live from `matches` table) | Days 38–44 |
| Active players by day/week (chart) | Days 42–48 |
| Revenue-share ledger view (once commercial launched — placeholder table for now, showing gross member revenue and 30% NSCI share) | Days 44–50 |
| Pause-log viewer (per the NSCI proposal audit commitment) — filterable by court and date | Days 46–52 |
| Monthly report export as PDF for committee | Days 52–58 |

**Definition of done Day 58:** NSCI committee can log in and see live utilisation + a mock month-1 revenue-share statement.

**Resources:** shared with WS-F.

---

### WS-H — WhatsApp delivery layer
**Owner:** AutomationXpert engineering (existing team, one dev part-time for this project)
**Days 30–55.**

Rides on existing AX WA router infrastructure — no new stack.

| Task | Days |
|---|---|
| Design 3 WA message templates: `match_ready_intro` (link to PWA), `weakness_summary`, `drill_of_the_week` — get Meta approval | Days 30–40 |
| Wire post-match trigger from Supabase → AX router → WA delivery to each of the 4 players | Days 40–48 |
| Delivery telemetry: sent, delivered, read; feed back into Supabase | Days 45–50 |
| Opt-out mechanism: STOP keyword handled by AX router; propagates to Supabase and pauses future messages for that number | Days 48–52 |
| Load test: 20 concurrent match completions → 80 WhatsApp messages in <2 min | Day 55 |

**Definition of done Day 55:** Every processed match produces 4 WA messages with 95% delivery in <2 min post-inference.

**Resources:** AX dev part-time (internal cost), ~₹1k Meta template testing.

---

### WS-I — QA, coach blind audit, launch readiness
**Owner:** Manoj (with Coach + CTO)
**Days 40–60.**

| Task | Days |
|---|---|
| Assemble 20-match blind audit set: coach scores each match's per-player skill summary and top-3 weaknesses independently, then compared with model output — target ≥ 80% directional agreement | Days 45–55 |
| Highlight clip relevance audit: 50 clips × coach thumb-up/thumb-down — target ≥ 75% relevance | Days 50–55 |
| End-to-end system test: fake match played on court by staff → within 15 min all 4 players receive WA report and can open PWA | Day 55 |
| Day 75 launch-readiness memo to NSCI committee (per NSCI proposal § "Launch readiness") — model quality, delivery latency, pause-log stats, member-facing UX walkthrough, final pricing sheet | Day 60 → memo dated Day 75 for delivery |
| Prepare NSCI monthly remittance format + AX billing pipeline for Day 91 commercial launch | Days 55–60 |
| Playbook for onboarding NSCI members onto commercial phase (comms, pricing, ID linking, first-time UX) | Days 55–60 |

**Definition of done Day 60 (G6):** A real match played on NSCI court that morning has, by end of day, produced WA messages to 4 players and each has been able to open a full match report on the PWA. This is the go/no-go moment for the venture.

**Resources:** Coach audit time ₹10k, staff test-match sessions ~₹5k.

---

## 4. Weekly Gantt

```
Week    W1    W2    W3    W4    W5    W6    W7    W8    W9
Day     0-7  8-14  15-21 22-28 29-35 36-42 43-49 50-56 57-60
────────────────────────────────────────────────────────────
WS-A  ████░  ─     ─     ─     ─     ─     ─     ─     ─
WS-B  ██████ ██████ ██████ ██████ ██████ ██████ ██████ ██████ ██
WS-C  ██████ ██████ ██████ ██████ ██████ ─     ─     ─     ─
WS-D  ─     ─     ░████ ██████ ██████ ██████ ██████ ████░ ─
WS-E  ░████ ██████ ██████ ██████ ██████ ██████ ██████ ░─    ─
WS-F  ─     ─     ██████ ██████ ██████ ██████ ██████ ██████ ██
WS-G  ─     ─     ─     ─     ░████ ██████ ██████ ██████ ██
WS-H  ─     ─     ─     ─     ██████ ██████ ██████ ██████ ─
WS-I  ─     ─     ─     ─     ─     ░████ ██████ ██████ ██

Gates: G1=D3    G2=D14    G3=D21    G4=D35    G5=D50    G6=D60
```

---

## 5. Resources — the full roster

### 5.1 People (10-person effective team, 5.5 FTE-equivalent for 60 days)

| Role | Commitment | Duration | Cost | Sourcing |
|---|---|---|---|---|
| CEO / product owner | Full-time | 60 days | Founder | Manoj |
| CTO / ML lead | Full-time | 60 days | Co-founder equity + ₹1.5L/mo stipend | Target João Silva (upstream author); fallback Bangalore senior CV hire |
| Coach (padel technical) | Part-time (~15 hrs/wk) | 60 days | ₹40k/mo × 2 = ₹80k, retainer | Hire from NSCI-adjacent Mumbai padel coach circuit |
| CV engineer | Full-time contract | Days 7–35 | ₹1.2L × 1 mo = ₹1.2L | Toptal / TopHire India |
| Full-stack engineer | Full-time contract | Days 3–45 | ₹1L/mo × 1.5 = ₹1.5L | AutomationXpert bench (existing) |
| Frontend engineer | Full-time contract | Days 15–58 | ₹1L/mo × 1.5 = ₹1.5L | AutomationXpert bench (existing) |
| AX dev (WA integration) | 20% allocation | Days 30–55 | Internal (no new spend) | Existing AX team |
| Labeller × 2 | Part-time | Days 10–60 | ₹15k/mo × 2 × 1.7 = ₹51k | Recruit from NSCI + regional padel WhatsApp groups |
| Hardware install lead | 5 days | Days 0–5 | ₹40k | CCTV integrator in Mumbai (SPL Technologies or equivalent) |
| Senior CV contractor (contingent) | 2 weeks | Days 42–50 if triggered | ₹1L reserve | Fractal / Ideas2IT / Toptal roster |

**People subtotal:** ~₹6.3L (₹0.6L contingent).

### 5.2 Hardware — one-time

| Item | Qty | Unit | Total |
|---|---|---|---|
| Reolink RLC-823A 4K PoE camera | 2 (+ 1 spare) | ₹12k | ₹36k |
| Raspberry Pi 5 8GB + 1TB NVMe HAT + case | 2 (+ 1 spare) | ₹15k | ₹45k |
| TP-Link 5-port PoE+ switch | 1 | ₹3k | ₹3k |
| 4G/5G modem + prepaid SIM (dedicated) | 1 | ₹8k modem + ₹1k/mo data | ₹10k for 60 days |
| Cat6 outdoor cable + connectors | 40m | | ₹2.5k |
| IP66 weatherproof enclosure | 1 | ₹3k | ₹3k |
| Wall mounts + brackets | 2 | ₹750 | ₹1.5k |
| UPS (for edge box) | 1 | ₹6k | ₹6k |
| Courtside pause button (Zigbee, LED, weather-protected) | 2 | ₹1.5k | ₹3k |
| Courtside signage (printed + weather-proofed) | 2 | ₹1.5k | ₹3k |
| Contingency for cable trays, drilling, sundries | | | ₹5k |

**Hardware subtotal:** ~₹1.2L (both courts, plus spares).

### 5.3 Cloud + SaaS — 60 days

| Service | Purpose | 60-day cost |
|---|---|---|
| Cloudflare R2 | Match video storage | ₹1k |
| Cloudflare Workers + Pages | Webhooks, PWA hosting | ₹1k |
| Supabase Pro | DB, Auth, Realtime | ₹4k |
| RunPod RTX 3090 (on-demand + training) | Inference + classifier training | ₹15k (training) + ₹5k (inference during trial) |
| Upstash Redis | Job queue | ₹1k |
| Sentry + PostHog | Observability | ₹2k |
| Streamlit Cloud (labelling tool) | Free tier | ₹0 |
| Grafana Cloud (heartbeat) | Free tier | ₹0 |
| GitHub Team | Private repos, CI | ₹2k |
| Miscellaneous (domains, transactional email, WA template fees) | | ₹3k |

**Cloud subtotal:** ~₹34k for 60 days.

### 5.4 Total 60-day cash outlay

| Bucket | Amount |
|---|---|
| People (fixed) | ₹5.7L |
| People (contingency) | ₹1L (spent only if classifier plateaus) |
| Hardware | ₹1.2L |
| Cloud + SaaS | ₹0.34L |
| **Total, no contingency** | **~₹7.2L** |
| **Total, worst case (classifier escalation triggers)** | **~₹8.2L** |

This is the cash cost to reach a working V1 with a paying-launch-ready platform on the NSCI courts by Day 60.

---

## 6. Handshake contracts between workstreams

Where two streams meet, the format of the artefact passing between them is fixed on Day 0. Changing these contracts mid-flight is the #1 source of delay.

| From → To | Contract |
|---|---|
| WS-A → WS-C | Match MP4 in R2 at path `matches/{court_id}/{yyyy-mm-dd}/{match_id}.mp4` + webhook payload `{match_id, court_id, start_ts, end_ts, duration_s, size_bytes}` |
| WS-C → WS-D | Per-shot feature vector as JSONL row: `{match_id, shot_idx, player_id, ts_ms, pose_seq (13×30×3), court_xy, ball_traj, opponents, score_ctx}` |
| WS-C → WS-B (labelling) | Streamlit UI plays MP4 clip [ts−1s, ts+1s]; labeller emits `{shot_idx, class, quality, deviations[]}` |
| WS-D → WS-E | Classifier serves at `POST /infer/shot` → `{class, class_conf, quality, quality_conf, deviations[]}` |
| WS-E → WS-F | REST `GET /matches/:id/report` returns the full report JSON schema locked on Day 20 |
| WS-E → WS-H | Post-match trigger: Supabase Realtime channel `match_complete` → AX router consumer |
| WS-A → WS-E (audit) | Every pause-button press posts to `POST /audit/pause` — logged forever |

---

## 7. Kill criteria + escalation

Two hard stops. Both must be checked at Day 35.

### 7.1 If G4 fails (classifier below 55% on Day 35)

**Escalation ladder:**
1. Ship senior CV contractor within 48 hours (₹1L reserve).
2. Expand labelling target from 700 → 1,500 clips; add a second coach for inter-rater labels.
3. Add temporal CNN or MotionBERT ensemble head.
4. If Day 45 still below 65% → propose to NSCI committee to extend training phase from 90 to 120 days; retain original commercial terms.

### 7.2 If hardware install slips past Day 7

**Escalation:** Move to a single-court install (whichever court is available first). Second court joins later. Data-capture volume halves — G3 date slips by 5 days but classifier still viable on 700 clips at revised pace.

### 7.3 If coach retention becomes unreliable

**Fallback:** AutomationXpert has a small network of Mumbai racket-sport coaches from earlier product research. Pre-line up a #2 coach on ₹10k/mo retainer before Day 15, so switching costs are 3 days not 3 weeks.

---

## 8. What is out of scope for these 60 days

Named explicitly, so it doesn't creep in.

- Native iOS / Android apps — PWA only.
- Live in-match insights — post-match only.
- Multi-camera / 3D ball depth — single camera per court only.
- Line-calling / officiating — deliberately never in scope.
- Player identity via face recognition — tap-in only.
- Tournament / draw generation.
- Booking integration.
- Multi-sport extension (tennis, badminton, pickleball) — architecturally ready but not shipped.

---

## 9. Day 60 → Day 90 → Day 91 handover

Days 60–90 are not idle. The 30-day window between end-of-build and start-of-commercial is where the platform earns its right to launch.

| Day | Activity |
|---|---|
| Days 60–75 | Coach blind audit on 20 matches; iterate classifier one more time on any systemic errors surfaced; fix top-5 PWA UX papercuts from staff test users |
| Day 75 | Launch-readiness memo to NSCI committee — model quality, delivery latency, member-facing UX walkthrough, pause-log audit, final member pricing sheet |
| Days 75–85 | Onboard the first 10 NSCI members as beta commercial users (still free — friends-of-committee style, one week head start) |
| Days 85–90 | Fix any beta feedback; freeze v1.0 |
| Day 91 | Public commercial launch to NSCI members. First WhatsApp broadcast goes out. Monthly clock for the 30% revenue remittance starts |

---

## 10. What Manoj needs to lock this week

Everything else runs off these five decisions.

1. **CTO/ML co-founder outreach.** João Silva email + fallback pipeline — decision by Day 5.
2. **Coach hire.** 3 candidate interviews by Day 3; retainer signed by Day 7.
3. **Hardware order.** Cameras + Pi 5 + accessories ordered Day 0 to allow install on Day 3.
4. **NSCI approval.** The 2026-07-02 proposal must be minuted by the committee before Day 0. If approval slips, all dates slip 1:1.
5. **Budget release.** ₹7.2L cash committed from Anchor Fastener treasury with ₹1L classifier contingency ring-fenced.

---

**End of 60-Day Execution Plan v1.0**

*This document is companion to `TECHNICAL_FEASIBILITY_REPORT.md` and `NSCI_PROPOSAL.md`. It converts the feasibility architecture into a dated, resourced, owner-labelled execution schedule.*
