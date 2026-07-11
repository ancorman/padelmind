# 60-Day Expanded Execution Plan
## From Camera-Install to Customer-Ready UI — PadelMind by AutomationXpert

**Version:** 2.0 (expanded from `60_DAY_EXECUTION_PLAN.md` v1.0)
**Date:** 2026-07-03
**Author:** Manoj Maheshwari
**Companion documents:** `TECHNICAL_FEASIBILITY_REPORT.md`, `NSCI_PROPOSAL.md`, `TECH_BRIEFING_FOR_SON.md`
**Target outcome by Day 60:** A real match played on NSCI court has, by end of day, produced WhatsApp reports to all 4 players, each able to open a full match report on a mobile phone.

---

## 0. How to read this document

The 60 days are divided into **9 parallel workstreams (A through I)**. Each workstream is a self-contained module of work with its own owner, budget, deliverables, and hand-offs to other workstreams.

For every workstream, this document details:

1. **Objective** — the one sentence that describes why the workstream exists
2. **Owner** — the person accountable for delivering it; their day-cost; who to escalate to if they miss
3. **Scope in / scope out** — a bright line on what belongs to this workstream and what does not
4. **Day-by-day tasks** — concrete work items with dates
5. **Deliverables** — the artefacts that prove the work is done
6. **Handoffs** — the specific outputs this workstream hands to other workstreams, in what format
7. **Risk + contingency** — the top thing that could break this workstream and the plan if it does
8. **Budget** — cash cost of running this workstream for the full 60 days

At the end of each workstream is a **definition of done** — the binary check that gates whether the workstream is closed.

The 60 days are then punctuated by **6 hard milestone gates**: G1 (Day 3), G2 (Day 14), G3 (Day 21), G4 (Day 35), G5 (Day 50), G6 (Day 60). Missing any gate triggers the escalation plan in the last section.

---

## 1. Executive summary of the 60 days

| Metric | Target |
|---|---|
| Duration | 60 calendar days from installation-approved by NSCI committee |
| Courts covered | Both NSCI padel courts |
| Team size (effective FTE) | 5.5 people fully committed for 60 days |
| Team size (headcount) | 10 people with varying commitments |
| Total cash outlay | ₹7.2 lakh base + ₹1 lakh contingency |
| Hardware BOM | ₹1.2 lakh (both courts + spares) |
| End state | Working V1: cameras live, classifier trained, PWA shipped, WhatsApp delivery active |
| What Day 61 onwards is for | Coach blind audit + polish + closed beta with 10 NSCI members before Day 91 commercial launch |

---

## 2. Workstream A — Hardware Install & Live Feed

### 2.1 Objective
Get two NSCI courts filming and streaming to the cloud within 5 days of committee approval, with a player-facing pause switch in place.

### 2.2 Owner
**Hardware install lead** — a Mumbai CCTV integrator on retainer for 60 days.
- Day cost: ₹40,000 flat fee for the 5-day install + ₹5,000/month standby for the remaining ~55 days
- Escalation: Manoj personally handles NSCI-facing communication; hardware lead handles installation and technical support only
- Backup: A second CCTV integrator (SPL Technologies as fallback) pre-lined-up before Day 0 so no single point of failure

### 2.3 Scope in
- Physical camera mounting (2 cameras, one per court)
- Cabling — Cat6 from cameras to edge box
- Weatherproof enclosure for Pi 5 + modem + UPS
- Courtside pause-button installation (1 per court)
- Signage installation
- Initial 12-point court keypoint calibration per court
- Heartbeat monitoring + alerting configured

### 2.4 Scope out
- Model training (WS-D)
- Any pipeline work (WS-C)
- Any interaction with NSCI members or staff — handled by Manoj

### 2.5 Day-by-day tasks

| Day | Task | Responsibility |
|---|---|---|
| −5 to 0 | Order all hardware from Amazon India / Robu.in / Reolink India | Manoj purchases + tracks |
| −2 | Site walk at NSCI with maintenance staff, identify electrical point, confirm mount positions | Manoj + install lead |
| 0 | All hardware received at Manoj's office, tested in bench setup | Install lead |
| 1 | Pi 5 pre-configured — Ubuntu, MediaMTX, uploader daemon, health beacon — before going to court | Install lead |
| 2 | 4G/5G modem provisioned with dedicated SIM, tested on hotspot to R2 upload | Install lead |
| 3 | Install day at NSCI — single 2-hour morning window agreed with committee. Cameras mounted, cables run, edge box installed, first frame captured | Install lead + 1 electrician; Manoj present |
| 3 | 12-point court keypoint clicks for both courts, saved to court-config file | Install lead |
| 3 | Informational signage put up at both courts | Manoj |
| 4 | Courtside pause buttons installed and wired to state-machine service | Install lead |
| 5 | Grafana heartbeat dashboard live, alerts wired to Manoj's WhatsApp | Install lead |

### 2.6 Deliverables
- Both courts streaming RTSP to their respective Pi 5
- First real match MP4 auto-uploaded to Cloudflare R2, timestamped
- Pause button tested (recording pauses within 5 seconds of press, resumes automatically after 2 hours)
- Signage in place at both courts
- Health monitor showing >99% uptime for camera + Pi + modem
- Court keypoint JSON files saved in the config repo

### 2.7 Handoffs
- **To WS-C:** Match MP4 in R2 at path `matches/{court_id}/{yyyy-mm-dd}/{match_id}.mp4` + webhook payload with `{match_id, court_id, start_ts, end_ts, duration_s, size_bytes}`
- **To WS-E:** Court keypoint JSON with 12 (x, y) pairs per court
- **To WS-E (audit):** Every pause-button press posts to `POST /audit/pause` — logged forever, per NSCI proposal transparency commitment

### 2.8 Risk + contingency

**Top risk:** Camera mounting height or angle proves suboptimal after first day of test matches (e.g., ball too small, blind spots at back walls). **Contingency:** Site walk done at 4pm on a match day so we see actual play conditions before committing to mount positions. Second visit budgeted at Day 10 for adjustment. Spare camera on hand.

**Second risk:** Modem cellular signal weak inside NSCI service niche. **Contingency:** External antenna kit ordered in advance (₹3,000); mount to modem enclosure exterior if internal signal is under −85 dBm.

### 2.9 Budget

| Item | Cost |
|---|---|
| Hardware BOM (both courts + 1 spare of each) | ₹1,20,000 |
| Install lead retainer (5 days + 55 days standby) | ₹68,000 |
| Contingency (antenna, extra cabling, unforeseen) | ₹15,000 |
| **Total WS-A** | **₹2,03,000** |

### 2.10 Definition of done (G1, Day 3)
Both courts streaming; first match MP4 auto-uploaded to R2; pause button toggles recording; signage up.

---

## 3. Workstream B — Data Capture & Labelling Operations

### 3.1 Objective
Produce 700 coach-labelled shot clips by Day 50 — the training corpus for the shot classifier (Stage 12 of the signal path). This workstream is on the critical path for the whole venture.

### 3.2 Owner
**Padel Coach (part-time retainer)** for the taxonomy and audit; **2 labellers (part-time)** for bulk labelling.
- Coach day cost: ₹40,000/month × 2 months = ₹80,000
- Labeller day cost: ₹15,000/month × 2 people × 1.7 months = ₹51,000
- Escalation: Manoj to interview + line up a #2 coach on ₹10k/mo retainer before Day 15 so switching costs are days, not weeks
- Coach criteria: Level-B PBI-certified coach with ≥5 years of coaching experience, based in Mumbai for weekly in-person sessions

### 3.3 Scope in
- Authorship of the taxonomy + rubric document (14 shot classes, 1–5 quality rubric, deviation-flag glossary)
- Labelling of 100 "gold-standard" reference clips
- Training and ongoing management of the 2 labellers
- Weekly 10% audit of labeller output; inter-rater reliability tracked
- Blind audit of the trained classifier on 20 matches (Day 45–55)

### 3.4 Scope out
- Any code writing (WS-C builds the labelling tool)
- Any modelling decisions (WS-D)
- Direct member interaction beyond passive observation of play

### 3.5 Day-by-day tasks

| Days | Task | Responsibility |
|---|---|---|
| 0–7 | Coach authors 15-page taxonomy + rubric document | Coach |
| 5–8 | Manoj interviews 3 labeller candidates from padel WhatsApp groups + NSCI community | Manoj + Coach |
| 7–12 | Coach labels 100 gold-standard reference clips using Streamlit tool built by WS-C | Coach |
| 10–14 | Onboard 2 labellers, train them on the gold-standard set | Coach |
| 10–14 | Import ~150 supplementary clips from PadelVic public dataset for class balance | Full-stack engineer (WS-E) |
| 14–21 | Labellers ramp: 50 clips each in week 3 → 100 each in week 4 → 150 each week 5 onwards | Labellers |
| Weekly | Coach 10% audit of labeller output, feedback loop, inter-rater kappa tracking | Coach |
| 45–55 | Coach blind audit: score 20 recent matches independently, compare with model output | Coach |

### 3.6 Deliverables
- Taxonomy + rubric document (15 pages, PDF)
- Gold-standard clip set: 100 clips with coach labels
- Ongoing labelled dataset in `labels` table on Supabase — 200 clips by Day 21, 400 by Day 35, 600 by Day 42, 700+ by Day 50
- Inter-rater kappa scores tracked weekly (target ≥ 0.7)
- Blind audit report: coach vs. model agreement on per-player skill summary and top-3 weaknesses (target ≥ 80% directional agreement)

### 3.7 Handoffs
- **To WS-D:** Labelled clips as JSONL rows: `{shot_id, class, quality, deviations[]}` linked to the shot feature vector in `shots` table
- **To WS-I:** Blind audit results file for launch-readiness memo

### 3.8 Risk + contingency

**Top risk:** Coach retention becomes unreliable (competing engagements, health issues, disagreements). **Contingency:** #2 coach on retainer from Day 15, briefed on the taxonomy so hand-off is 3 days not 3 weeks.

**Second risk:** Labeller velocity below plan (real people are slow at first). **Contingency:** ₹10k buffer to add a third labeller from Day 30 onwards if week-4 velocity is below 100 clips/labeller.

**Third risk:** Class imbalance — some shot types (e.g., bandeja) rare in casual play. **Contingency:** Supplement with PadelVic public dataset; targeted coach-recorded demo clips for rare classes.

### 3.9 Budget

| Item | Cost |
|---|---|
| Coach retainer (2 months) | ₹80,000 |
| 2 labellers (part-time, 1.7 months) | ₹51,000 |
| Backup coach retainer (Days 15–60) | ₹15,000 |
| Third labeller contingency | ₹10,000 |
| **Total WS-B** | **₹1,56,000** |

### 3.10 Definition of done
- Day 21 (G3): 200 clips labelled, taxonomy locked, all 14 classes represented, inter-rater kappa ≥ 0.7
- Day 50 (G5): 700+ clips banked, held-out 15% test set frozen

---

## 4. Workstream C — CV Pipeline Fork & Hardening

### 4.1 Objective
Turn João's open-source `padel_analytics` codebase into a production pipeline that ingests NSCI match MP4s and emits per-shot feature vectors ready for classification — running unattended in the cloud with observability and reliability.

### 4.2 Owner
**CTO / ML Lead (co-founder, full-time from Day 0)** with support from a **CV engineer (contract, ₹1.2 lakh/month, Days 7–35)**.
- Ideal profile: João Silva himself as consultant + a Bangalore-based CV engineer as the executing hand. Fallback: senior CV engineer with ByteTrack / YOLO / TrackNet familiarity.
- Escalation: Manoj to Manoj's son (Apple AI advisor) for architecture judgement calls if CTO stalls.

### 4.3 Scope in
- Private fork of `Joao-M-Silva/padel_analytics` → `automationxpert/padelmind-pipeline`
- Retrain of TrackNet for padel ball (yellow, faster than tennis)
- Adaptation of court keypoint logic for padel court geometry
- Shot-impact segmentation algorithm (velocity direction-change detector with padel wall-bounce handling)
- Queue-consumer wrapper: reads R2 events, downloads video, runs stages 6–11, emits shots-JSONL
- **Decision on Ultralytics licensing** (Day 5–7) — see `TECH_BRIEFING_FOR_SON.md` §2 for the framing
- Streamlit labelling tool for WS-B
- Observability: Sentry hooks, per-stage timing metrics, failure-mode dashboards
- Reliability hardening: retry logic, dead-letter queue, graceful "no ball detected" fallback

### 4.4 Scope out
- Shot classifier itself (WS-D)
- Application data model (WS-E)
- Any UI (WS-F, WS-G)

### 4.5 Day-by-day tasks

| Days | Task |
|---|---|
| 0–3 | Fork `padel_analytics` → private repo, strip UI, keep inference nodes |
| 3–10 | Wrap pipeline in queue-consumer worker: reads R2 events → downloads video → runs stages 6–11 → writes shots-JSONL to Postgres |
| 5–7 | **Ultralytics licensing decision:** benchmark RTMPose baseline against YOLOv8 on 50 test clips; decide swap or pay |
| 5–10 | Build Streamlit labelling tool → hand over to WS-B |
| 7–14 | Retrain TrackNet on padel ball using PadelVic + first NSCI captures |
| 7–10 | Adapt court keypoint code for padel court; validate against install-day 12-point clicks |
| 10–18 | Build shot-impact segmentation with padel-specific wall-bounce handling |
| 15–20 | Pipeline observability: Sentry, per-stage timing, dashboards |
| 20–30 | Reliability hardening: retries, DLQ, fallbacks |
| 30–35 | Ship-ready pipeline v1.0 tagged; passes 100-match soak test with <1% crash rate |

### 4.6 Deliverables
- Private repo `automationxpert/padelmind-pipeline` at commit `v1.0.0` by Day 35
- Documented feature-vector schema for downstream classifier (390-dim: pose seq + court xy + ball trajectory + opponents + score context)
- Streamlit labelling tool at `label.padelmind.internal` (staging) by Day 10
- Sentry + Grafana dashboards showing per-stage latency and error rates
- Ultralytics-vs-Apache decision memo by Day 7

### 4.7 Handoffs
- **From WS-A:** Match MP4 with webhook payload (as documented above)
- **To WS-B:** Streamlit labelling tool ready for coach use by Day 10
- **To WS-D:** Feature vector JSONL per shot in schema locked on Day 15
- **To WS-E:** Pipeline writes results to Postgres tables `matches`, `shots` (schema owned by WS-E)

### 4.8 Risk + contingency

**Top risk:** Ball tracking unreliable in NSCI's specific lighting conditions (LEDs vs natural light varies through the day). **Contingency:** Camera upgrade to Hikvision ColorVu (₹6k delta) budgeted; recommend NSCI add 2× 50W LED panels if needed.

**Second risk:** Ultralytics licensing decision goes wrong direction — RTMPose accuracy is materially worse than YOLOv8. **Contingency:** ₹2 lakh reserve for Ultralytics Enterprise Licence in Year-1 budget.

### 4.9 Budget

| Item | Cost |
|---|---|
| CV engineer contract (1 month) | ₹1,20,000 |
| RunPod training compute for retrains | ₹15,000 |
| Camera upgrade contingency (Hikvision if lighting fails) | ₹12,000 |
| Sentry + Grafana + CI (Cloudflare) | ₹5,000 |
| Ultralytics Enterprise Licence — if the swap doesn't work | ₹2,00,000 (contingent, not base case) |
| **Total WS-C (base case)** | **₹1,52,000** |
| **Total WS-C (worst case if licensing goes wrong)** | **₹3,52,000** |

### 4.10 Definition of done
- Day 14 (G2): Real NSCI match MP4 → pipeline → shots-JSONL in Postgres, all fields populated except `class`
- Day 35: Pipeline runs unattended on queue; P99 crash rate <1%; per-stage latency within budget

---

## 5. Workstream D — Shot Classifier Training (The Moat)

### 5.1 Objective
Train the proprietary shot classifier (Stage 12 of the signal path) to ≥70% top-1 accuracy on held-out test set by Day 50 — the acceptance criterion for the moat layer.

### 5.2 Owner
**CTO / ML Lead** (full-time, this is the single most important workstream for the CTO)
- Escalation: Senior CV contractor budget of ₹1 lakh reserved for 2-week engagement if Day-35 accuracy is below 55% (G4 fail)

### 5.3 Scope in
- Feature extraction module (turns each shot event into a 390-dim vector)
- V0 classifier (14-class head only, small MLP)
- Quality regression head (1–5 stars)
- Deviation-flag multi-label head
- Iteration loop: analyse errors → request specific labels from coach → retrain
- Ensemble modelling if plateau (MLP + temporal CNN, or MotionBERT adaptation)
- Serving the classifier via FastAPI on RunPod

### 5.4 Scope out
- Labelling itself (WS-B)
- Pipeline plumbing (WS-C)
- Skill-score aggregation across matches (WS-E)

### 5.5 Day-by-day tasks

| Days | Task |
|---|---|
| 15–22 | Feature extraction module: shot event → 390-dim vector |
| 22–28 | V0 classifier — 14-class MLP, trained on first 200 clips |
| 28 | V0 readout: accuracy on 15% held-out; confusion matrix; identify hardest 3 classes |
| 28–35 | Add quality-regression head; retrain on 400 clips |
| 35–42 | Add deviation-flag multi-label head; retrain on 600 clips |
| 28–50 | Weekly iteration: analyse errors → coach requests → retrain |
| 42–50 | If G4 pass but plateau visible, ensemble MLP + temporal CNN |
| 50 | V1 classifier frozen; served via FastAPI on RunPod |

### 5.6 Deliverables
- Trained classifier artefact registered in a model registry (weights + metadata + training run log)
- FastAPI service serving `POST /infer/shot` at `<runpod-endpoint>/infer/shot`
- Test-set metrics report: top-1 accuracy, top-2 accuracy, quality MAE, per-class F1

### 5.7 Handoffs
- **From WS-C:** Feature vector schema (locked Day 15)
- **From WS-B:** Labelled clips as they arrive
- **To WS-E:** Classifier inference endpoint URL + API contract
- **To WS-I:** Test-set metrics report for launch-readiness memo

### 5.8 Risk + contingency

**Top risk (T1 from the risk register):** Classifier accuracy plateaus below 70%. **Contingency ladder:**
1. Multi-coach labels (add coach #2 for inter-rater labels)
2. Dataset expansion to 1,500 clips
3. Senior CV contractor engagement (₹1L reserve, 2 weeks)
4. Ensemble of MLP + temporal CNN
5. If Day 50 still below 65%, propose NSCI extension of training phase to 120 days

**Second risk:** Class-pair confusion (bandeja vs vibora — similar pose, different ball speed). **Contingency:** Use ball trajectory feature more heavily as discriminator; retrain with class-balanced sampling.

### 5.9 Budget

| Item | Cost |
|---|---|
| RunPod compute for training iterations | ₹20,000 |
| Senior CV contractor if escalation triggered | ₹1,00,000 (contingent) |
| **Total WS-D (base case)** | **₹20,000** |
| **Total WS-D (worst case)** | **₹1,20,000** |

### 5.10 Definition of done
- Day 35 (G4): V0 ≥ 55% top-1 on held-out test
- Day 50 (G5): V1 ≥ 70% top-1 and quality MAE ≤ 0.7

---

## 6. Workstream E — Backend & Data Model

### 6.1 Objective
Build the Supabase-backed data model, API surface, and player-identity flows that the PWA, dashboard, and WhatsApp delivery all consume.

### 6.2 Owner
**Full-stack engineer (contract, ₹1 lakh/month, Days 3–45)** — pulled from the AutomationXpert bench so onboarding is zero.
- Escalation: CTO if any schema-level decisions are needed.

### 6.3 Scope in
- Supabase schema: `players`, `clubs`, `courts`, `matches`, `shots`, `skill_scores`, `drills`, `highlights`, `labels`, `audit_events`
- Row-level security policies (players see only their matches; clubs see only their courts)
- Cloudflare Workers: upload webhook, auth token issuance, signed URL generator
- Player identity + tap-in flow (QR code at courtside → WhatsApp OTP → linked to match)
- Skill-score engine (ELO-style updater triggered post-match)
- Drill recommender (rule-based V1: `weak_class` → mapped drill from coach catalogue)
- Audit-log service for pause events + WhatsApp opt-outs
- REST + Realtime channels for PWA and dashboard

### 6.4 Scope out
- Frontend UI (WS-F, WS-G)
- ML model itself (WS-D)
- WhatsApp router integration (WS-H)

### 6.5 Day-by-day tasks

| Days | Task |
|---|---|
| 3–7 | Supabase project provisioned; all tables + RLS policies committed |
| 5–14 | Cloudflare Workers: upload webhook, auth, signed URLs |
| 7–10 | RLS test suite: 4 test tenants, verify data isolation |
| 14–24 | Player identity + tap-in flow |
| 20–45 | REST + Realtime API surface for PWA and dashboard |
| 24–28 | Audit-log service (pause-button events + opt-outs) |
| 24–32 | Skill-score ELO engine |
| 32–38 | Drill recommender V1 |

### 6.6 Deliverables
- Supabase project `padelmind-prod` and `padelmind-staging` with full schema
- 4 Cloudflare Workers deployed
- API documentation at `docs.padelmind.internal`
- Postman collection covering every endpoint

### 6.7 Handoffs
- **To WS-F, WS-G:** REST endpoints + Realtime channels
- **To WS-H:** Realtime `match_complete` channel for post-match trigger

### 6.8 Risk + contingency

**Top risk:** RLS policy bugs leak one player's data to another. **Contingency:** Automated test suite covering every table + every role combination; run in CI on every schema change.

**Second risk:** Supabase Pro plan tier limits hit during load test. **Contingency:** Prepared migration path to Team plan (~₹9k/mo delta).

### 6.9 Budget

| Item | Cost |
|---|---|
| Full-stack engineer (1.5 months) | ₹1,50,000 |
| Supabase Pro (2 months) | ₹4,000 |
| Cloudflare Workers + Pages (paid tier) | ₹1,000 |
| **Total WS-E** | **₹1,55,000** |

### 6.10 Definition of done
Day 45: all PWA-consumable endpoints stable; RLS verified with 4 test tenants; audit log queryable by pause-button event.

---

## 7. Workstream F — Player PWA (Customer-Facing UI)

### 7.1 Objective
Ship a mobile-first Progressive Web App that a player can open from a WhatsApp deep-link and reach their complete match report in under 4 seconds cold-load.

### 7.2 Owner
**Frontend engineer (contract, ₹1 lakh/month, Days 15–58)** — pulled from AutomationXpert bench.
- Design: Manoj drives brand + tone; engineer executes on component library (shadcn/ui + Tailwind)

### 7.3 Scope in
- React + Vite scaffold on Cloudflare Pages
- PadelMind design system (colour, type, iconography)
- Auth flow: WhatsApp OTP via AX router
- Home screen: current skill score, last match summary, next-match teaser
- Match detail: 4-player scoreboard, per-shot breakdown, quality distribution chart, top-3 weaknesses, drill cards
- Highlight clips player (3 auto-extracted 6-sec MP4s, share buttons)
- Skill trajectory chart (ELO over time, Recharts)
- Post-match survey (NPS + free-text) from match 3 onwards
- Player-side opt-out UI
- PWA install prompt + offline stub
- Cross-device QA

### 7.4 Scope out
- Club dashboard (WS-G)
- Any backend logic (WS-E)
- Any WhatsApp mechanics (WS-H)

### 7.5 Day-by-day tasks

| Days | Task |
|---|---|
| 15–20 | React + Vite scaffold, design tokens, PadelMind theme |
| 18–24 | Auth flow (WhatsApp OTP → Supabase session) |
| 20–28 | Home screen with live skill score |
| 24–36 | Match detail page with all breakdowns |
| 30–40 | Highlight clips player + share buttons |
| 32–38 | Skill trajectory chart |
| 40–46 | Post-match survey + player opt-out UI |
| 46–52 | PWA install prompt + offline stub |
| 52–58 | Cross-device QA — iOS Safari, Android Chrome, edge cases |

### 7.6 Deliverables
- PWA live at `play.padelmind.in` (or equivalent short domain)
- Lighthouse audit: >90 on Performance, Accessibility, Best Practices, SEO
- Cross-device screenshots archive
- WhatsApp share flow producing rich preview cards

### 7.7 Handoffs
- **From WS-E:** REST endpoints stabilised by Day 40 so no schema churn during last 2 weeks
- **To WS-H:** Deep-link URLs that the WA router messages will point to

### 7.8 Risk + contingency

**Top risk:** Cold-load time on 3G / weak-signal conditions at NSCI exceeds 4 seconds. **Contingency:** Aggressive code-splitting; skeleton screens; server-side render summary page.

**Second risk:** iOS PWA install experience is famously worse than Android. **Contingency:** Ship native App Store version in Year 2; PWA is sufficient for V1.

### 7.9 Budget

| Item | Cost |
|---|---|
| Frontend engineer (1.5 months) | ₹1,50,000 |
| Design assets + icons | ₹20,000 |
| Cloudflare Pages (free tier ample) | ₹0 |
| **Total WS-F** | **₹1,70,000** |

### 7.10 Definition of done
Day 58: player goes from WhatsApp deep-link to complete match report on iPhone or Android in under 4 seconds cold-load.

---

## 8. Workstream G — Club Dashboard

### 8.1 Objective
Give the NSCI committee a live dashboard of court utilisation, active players, pause-log audit, and a preview of the monthly revenue-share statement.

### 8.2 Owner
**Frontend engineer** (shared with WS-F, second half of allocation)

### 8.3 Scope in
- Role-gated `/club/*` routes in the same React app
- Court occupancy view (live from `matches` table)
- Active players by day/week charts
- Revenue-share ledger view (with mock data pre-launch, real from Day 91)
- Pause-log viewer (per NSCI audit commitment) — filterable by court and date
- Monthly report export as PDF for committee

### 8.4 Scope out
- Anything player-facing (WS-F)

### 8.5 Day-by-day tasks

| Days | Task |
|---|---|
| 35–40 | Role-gated routing, club admin login |
| 38–44 | Court occupancy dashboard |
| 42–48 | Active players charts |
| 44–50 | Revenue-share ledger (mock data) |
| 46–52 | Pause-log viewer |
| 52–58 | PDF export |

### 8.6 Deliverables
- Dashboard live at `club.padelmind.in/nsci`
- NSCI committee login credentials distributed (via secure channel)
- One printed mock monthly report ready for committee review meeting

### 8.7 Handoffs
- **From WS-A:** Pause-event stream (via WS-E)
- **From WS-E:** All API endpoints

### 8.8 Risk + contingency
Low risk — this is a read-only dashboard on data we control.

### 8.9 Budget
Shared with WS-F.

### 8.10 Definition of done
Day 58: NSCI committee can log in and see live utilisation + a mock month-1 revenue-share statement.

---

## 9. Workstream H — WhatsApp Delivery Layer

### 9.1 Objective
Ensure every processed match produces WhatsApp messages to all 4 players within 2 minutes of inference completion, with 95% delivery rate.

### 9.2 Owner
**AutomationXpert engineer (20% allocation, part-time from Day 30)** — internal cost, no new hire needed.
- Escalation: AX Head of Engineering for any router-level changes.

### 9.3 Scope in
- Design 3 WA message templates: `match_ready_intro`, `weakness_summary`, `drill_of_the_week`
- Meta template approval for all 3
- Post-match trigger from Supabase Realtime → AX router
- Delivery telemetry (sent, delivered, read) fed back into Supabase
- STOP-keyword opt-out mechanism
- Load test (20 concurrent match completions → 80 messages in <2 min)

### 9.4 Scope out
- Any UI (WS-F, WS-G)
- Any classifier work (WS-D)
- Any new AX platform features — reusing existing infrastructure

### 9.5 Day-by-day tasks

| Days | Task |
|---|---|
| 30–40 | Design 3 templates + submit for Meta approval |
| 40–48 | Wire post-match Supabase Realtime trigger → AX router |
| 45–50 | Delivery telemetry feedback loop |
| 48–52 | STOP-keyword propagation to Supabase |
| 55 | Load test |

### 9.6 Deliverables
- 3 Meta-approved templates deployed on AX WABA
- End-to-end trigger latency dashboard
- Load test report

### 9.7 Handoffs
- **From WS-E:** Match-complete event on Realtime channel
- **To WS-F:** Deep-link URL shape confirmed for message body

### 9.8 Risk + contingency

**Top risk:** Meta template approval takes >2 weeks (variable). **Contingency:** Submit templates on Day 30 to give 3-week buffer before Day 60. If rejected, iterate content and resubmit; standard patterns like "match_ready_intro" pass approval reliably.

**Second risk:** Delivery latency spikes when many matches complete simultaneously. **Contingency:** AX router already load-tested to 100 msg/sec; well beyond our expected concurrency.

### 9.9 Budget

| Item | Cost |
|---|---|
| AX engineer time (internal) | ₹0 (no new spend) |
| Meta template testing costs | ₹1,000 |
| **Total WS-H** | **₹1,000** |

### 9.10 Definition of done
Day 55: every processed match produces 4 WA messages with 95% delivery in <2 min post-inference.

---

## 10. Workstream I — QA, Coach Blind Audit & Launch Readiness

### 10.1 Objective
Prove the end-to-end system works to acceptance criteria and deliver the launch-readiness memo to the NSCI committee.

### 10.2 Owner
**Manoj** (with Coach + CTO)

### 10.3 Scope in
- 20-match blind audit: coach vs. model on skill summary and top-3 weaknesses
- Highlight clip relevance audit (50 clips)
- End-to-end system test (fake match by staff → all 4 players receive report)
- Day-75 launch-readiness memo to NSCI committee (delivered Day 60, dated Day 75)
- Monthly remittance format for NSCI + AX billing pipeline setup
- Member onboarding playbook for the Day-91 commercial launch

### 10.4 Scope out
- Building anything (that's WS-A through WS-H)

### 10.5 Day-by-day tasks

| Days | Task |
|---|---|
| 45–55 | Coach blind audit on 20 matches, agreement scored |
| 50–55 | Highlight clip relevance audit (50 clips) |
| 55 | End-to-end system test with staff-played match |
| 55–60 | NSCI remittance format + AX billing pipeline preparation |
| 55–60 | Member onboarding playbook (comms, pricing, ID linking, first-time UX) |
| 60 | Launch-readiness memo drafted for delivery on Day 75 |

### 10.6 Deliverables
- Blind audit report
- Highlight clip audit report
- End-to-end test video
- Day-75 launch-readiness memo (approved by CTO + Coach + Manoj)
- Member onboarding playbook

### 10.7 Handoffs
- **From all workstreams:** Their deliverables feed into the memo

### 10.8 Risk + contingency

**Top risk:** Coach audit reveals classifier systematically wrong on a specific class (e.g., bandeja). **Contingency:** One more classifier iteration budgeted in Days 60–75 buffer window.

### 10.9 Budget

| Item | Cost |
|---|---|
| Coach audit time (10 hours) | ₹10,000 |
| Staff test-match sessions | ₹5,000 |
| **Total WS-I** | **₹15,000** |

### 10.10 Definition of done (G6, Day 60)
A real match played on NSCI court that morning has, by end of day, produced WhatsApp messages to 4 players and each has been able to open a full match report on the PWA.

---

## 11. Milestone gates with responsibility split

| Gate | Day | Owner accountable | Deliverable that proves it |
|---|---|---|---|
| **G1** — First frame captured | Day 3 | WS-A owner (Install lead) | First MP4 in R2 with valid webhook payload |
| **G2** — First shot detected end-to-end | Day 14 | WS-C owner (CTO/ML Lead) | Postgres query returns shots rows for a real NSCI match |
| **G3** — 200 clips labelled | Day 21 | WS-B owner (Coach) | Labels table in Postgres shows 200 valid rows |
| **G4** — Classifier V0 ≥ 55% top-1 | Day 35 | WS-D owner (CTO/ML Lead) | Test-set metrics report signed by CTO |
| **G5** — Classifier V1 ≥ 70% top-1 | Day 50 | WS-D owner (CTO/ML Lead) | Test-set metrics report + model registered |
| **G6** — End-to-end demo to player WA | Day 60 | Manoj | Screenshot of received WA message + PWA screenshot + coach sign-off |

Missing any gate triggers Section 12 escalation.

---

## 12. Escalation plan (what to do if a gate is missed)

### 12.1 G1 miss (Day 3, install)
Move to single-court install. Second court comes online Day 5–7. Data-capture volume halves; G3 date slips by ~5 days but classifier still viable on 700 clips at revised pace.

### 12.2 G2 miss (Day 14, pipeline end-to-end)
Bring the CV engineer contract forward and extend by 2 weeks. Manoj personally reviews CTO's blockers within 24 hours; if fundamental, engage a senior CV contractor for 2-week emergency engagement (₹1L pulled from contingency).

### 12.3 G3 miss (Day 21, labels)
Add third labeller. Coach shifts more time to labelling (from 15 hrs/week to 25 hrs/week). Manoj personally labels 20 clips/week to backfill.

### 12.4 G4 miss (Day 35, classifier V0)
1. Ship senior CV contractor within 48 hours (₹1L reserve).
2. Expand labelling target from 700 → 1,500 clips; add second coach for inter-rater labels.
3. Add temporal CNN or MotionBERT ensemble head.
4. If Day 45 still below 65% → propose to NSCI committee to extend training phase from 90 to 120 days; retain original commercial terms.

### 12.5 G5 miss (Day 50, classifier V1)
Extend Day 60 target to Day 75. Use the Day 61–75 window that was reserved for coach blind audit for further classifier iteration. Coach audit compressed into Days 75–90.

### 12.6 G6 miss (Day 60, end-to-end)
Diagnose which specific stage failed (delivery? PWA? classifier? pipeline?) and remediate within a 2-week extension. Day 91 commercial launch date is the immovable deadline; work back from there.

---

## 13. Handshake contracts between workstreams (frozen on Day 0)

Changing these mid-flight is the #1 source of delay. All contracts locked before Day 3.

| From → To | Contract |
|---|---|
| WS-A → WS-C | Match MP4 in R2 at `matches/{court_id}/{yyyy-mm-dd}/{match_id}.mp4` + webhook `{match_id, court_id, start_ts, end_ts, duration_s, size_bytes}` |
| WS-C → WS-D | Per-shot feature vector JSONL: `{match_id, shot_idx, player_id, ts_ms, pose_seq[13×30×3], court_xy, ball_traj, opponents[4], score_ctx}` |
| WS-C → WS-B | Streamlit UI plays MP4 clip [ts−1s, ts+1s]; labeller emits `{shot_idx, class, quality, deviations[]}` |
| WS-D → WS-E | Classifier serves `POST /infer/shot` → `{class, class_conf, quality, quality_conf, deviations[]}` |
| WS-E → WS-F | REST `GET /matches/:id/report` returns full report JSON — schema locked Day 20 |
| WS-E → WS-H | Post-match: Supabase Realtime channel `match_complete` → AX router consumer |
| WS-A → WS-E | Pause-button press posts `POST /audit/pause` — logged forever |

---

## 14. Full budget consolidation

| Workstream | Base case | Worst case (contingencies) |
|---|---|---|
| WS-A — Hardware Install | ₹2,03,000 | ₹2,03,000 |
| WS-B — Labelling Ops | ₹1,56,000 | ₹1,66,000 |
| WS-C — CV Pipeline | ₹1,52,000 | ₹3,52,000 |
| WS-D — Classifier | ₹20,000 | ₹1,20,000 |
| WS-E — Backend | ₹1,55,000 | ₹1,64,000 |
| WS-F — Player PWA | ₹1,70,000 | ₹1,70,000 |
| WS-G — Club Dashboard | (shared) | (shared) |
| WS-H — WhatsApp Delivery | ₹1,000 | ₹1,000 |
| WS-I — QA & Launch | ₹15,000 | ₹15,000 |
| **Subtotal** | **₹8,72,000** | **₹11,91,000** |
| Reserve buffer (10%) | ₹87,000 | — |
| **Grand total** | **~₹9,60,000** | **~₹12,00,000** |

*Note: v1 of the plan estimated ₹7.2L base; this expanded v2 with full per-workstream detail arrives at ₹9.6L base. The delta is (a) hardware install lead standby retainer, (b) backup coach retainer, (c) camera upgrade contingency, (d) reserve buffer. All numbers now explicit.*

---

## 15. Team roster (10 people, ~5.5 FTE for 60 days)

| Role | Commitment | Duration | Cost | Sourcing |
|---|---|---|---|---|
| CEO / product owner | Full-time | 60 days | Founder | Manoj |
| CTO / ML lead | Full-time | 60 days | Co-founder equity + ₹1.5L/mo stipend | Target João Silva (consultant/co-founder); fallback Bangalore senior CV hire |
| Padel Coach | Part-time (~15 hrs/wk) | 60 days | ₹80k | Mumbai coach circuit |
| CV engineer | Full-time contract | Days 7–35 | ₹1.2L | Toptal / TopHire India |
| Full-stack engineer | Full-time contract | Days 3–45 | ₹1.5L | AX bench |
| Frontend engineer | Full-time contract | Days 15–58 | ₹1.5L | AX bench |
| AX dev (WA) | 20% allocation | Days 30–55 | Internal | Existing AX team |
| Labellers × 2 | Part-time | Days 10–60 | ₹51k | NSCI + padel WA groups |
| Backup coach | Retainer standby | Days 15–60 | ₹15k | Interviewed pre-Day 15 |
| Hardware install lead | 5 days + standby | Days 0–5 + 60 | ₹68k | Mumbai CCTV integrator |
| Senior CV contractor | Contingent | Days 42–50 if triggered | ₹1L reserve | Fractal / Ideas2IT / Toptal |

---

## 16. What Manoj must lock this week

Everything else runs off these decisions.

1. **CTO/ML co-founder outreach** — João Silva Meet call + fallback pipeline. Decision by Day 5.
2. **Coach hire** — 3 candidate interviews by Day 3; retainer signed by Day 7. Backup coach identified by Day 10.
3. **Hardware order** — cameras + Pi 5 + accessories ordered Day 0 to allow install Day 3.
4. **NSCI approval** — 2026-07-02 proposal must be minuted before Day 0. If slips, all dates slip 1:1.
5. **Budget release** — ₹9.6L cash committed with ₹2L classifier/licensing contingency ring-fenced.
6. **Ultralytics licensing decision** — resolved by Day 7 based on son's technical opinion (see `TECH_BRIEFING_FOR_SON.md`) + WS-C benchmark result.

---

## 17. What Days 61–90 are for (bridge to commercial launch)

The 60-day plan ends with the platform working. Days 61–90 are the bridge to public commercial launch on Day 91 per the NSCI proposal.

| Days | Activity |
|---|---|
| 60–75 | Coach blind audit on 20 matches; classifier iteration on any systemic errors; fix top-5 PWA UX papercuts |
| 75 | Launch-readiness memo delivered to NSCI committee — model quality, delivery latency, pause-log audit, member UX walkthrough, final pricing sheet |
| 75–85 | Onboard first 10 NSCI members onto commercial pipes (still free — friends-of-committee style) |
| 85–90 | Fix beta feedback; freeze v1.0 |
| 91 | Public commercial launch. First WhatsApp broadcast to NSCI members. Monthly 30% revenue-remittance clock starts |

---

**End of 60-Day Expanded Execution Plan v2.0**

*Companion to `TECHNICAL_FEASIBILITY_REPORT.md`, `NSCI_PROPOSAL.md`, and `TECH_BRIEFING_FOR_SON.md`. This document is the operational source of truth once approved.*
