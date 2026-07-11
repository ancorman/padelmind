# Technical Feasibility Report
## AI-Powered Padel Coaching Platform — India to Asia

**Document version:** 1.0
**Date:** 2026-07-01
**Authors:** Manoj Maheshwari (CEO), Claude (technical drafting)
**Reviewers (pending):** [Coach name], [CTO/ML co-founder], [Apple AI advisor — son]
**Document classification:** Internal + investor diligence ready
**Companion documents:** `PADEL_AI_VENTURE_PLAN.md` (strategy), `PROJECT_REPORT.md` (execution), `COMMERCIAL_REPORT.md` (commercial)

---

## Table of Contents

1. Executive Summary
2. System Overview
3. End-to-End Architecture
4. Computer Vision Pipeline — Layer-by-Layer Feasibility
5. The Shot Classification Layer (Proprietary IP)
6. Hardware Specification (Per Court)
7. Cloud & Backend Infrastructure
8. Data, Privacy & Security
9. Multi-Sport Extensibility — Badminton & Tennis Roadmap
10. Technical Risk Register
11. Build vs Buy vs Fork Decision Matrix
12. Performance Targets & Acceptance Criteria
13. Edge Inference — Year 2/3 Architecture
14. Feasibility Verdict

---

## 1. Executive Summary

This report assesses whether an end-to-end AI padel coaching platform — capturing match footage from a single fixed IP camera per court, processing it through a computer vision pipeline, scoring player technique against an expert-coach-designed rubric, and delivering personalised improvement feedback to the player via WhatsApp within 10 minutes of match end — is **technically feasible to build, ship, and operate at scale by an Indian startup in 2026**.

**Verdict: Strongly feasible.** Every layer of the proposed stack has a working open-source reference. The one piece that does not exist in open source — the **shot-quality classifier scored against expert coaching rubric** — is the proprietary IP that constitutes the company's defensible moat. It is a supervised classification problem on pre-extracted features (pose keypoints + ball trajectory), tractable with standard small-model techniques, requiring an estimated 500–1,000 expert-labelled video clips for V1.

**Key technical findings:**
- Player tracking, ball tracking, court keypoint detection, and pose estimation are solved problems with mature OSS implementations
- A direct fork of `Joao-M-Silva/padel_analytics` accelerates the pipeline build by an estimated 8–12 weeks
- Hardware bill of materials is ~₹35,000 per court using off-the-shelf components (Reolink 4K IP camera + Raspberry Pi 5 edge buffer + PoE switch)
- Cloud unit economics are ~₹540 per court per month at 120 matches/court, supporting 89% gross margin at ₹5,000 ASP
- The architecture extends naturally to **badminton and tennis** with primarily the classifier head needing retraining (court keypoints and shot taxonomies change; the underlying tracking + pose stack is identical)
- Edge inference migration (Year 2/3) is feasible on either NVIDIA Jetson Orin Nano or Apple Mac mini M4 with Neural Engine — both paths are credible

**The single highest technical risk** is shot classifier accuracy plateauing below the 70% top-1 target. Mitigation is multi-coach labelling, dataset expansion, and ensemble modelling with predictable escalation to senior ML specialist contractor if stuck beyond Week 8.

**Recommendation:** Proceed to V1 build per the 12-week plan in `PROJECT_REPORT.md`.

---

## 2. System Overview

The platform turns every padel match played at a partner club into a structured, scored, and actionable coaching artefact delivered to the player on their phone — without requiring the player or club to take any action beyond starting and stopping play.

**The core insight:** Coaches charge ₹1,500–₹3,000/hour to provide expert technique feedback. We encode that expert judgment into a software system that runs at near-zero marginal cost per match, available to every player at every match without scheduling friction.

**The product is not the camera. The product is the coaching feedback.**

### 2.1 Functional capabilities V1

| Capability | Description |
|---|---|
| Automatic match capture | Single fixed camera per court records every match. No player or club action required beyond initial install |
| Player identification | Each match's 4 players identified via tap-in (QR + WhatsApp number) on first match; persistent identity thereafter |
| Court geometry | 12-point homography calibration done once at install; persists for life of installation |
| Shot detection | Every shot played in a match is detected with timestamp, type, executor, and ball trajectory |
| Shot quality scoring | Each shot scored 1–5 against expert rubric on form-quality dimensions (e.g., arm angle, hip rotation, balance, footwork) |
| Per-player skill score | Aggregate "Skill Score" updated after every match (ELO-style) reflecting class composition and quality distribution |
| Improvement feedback | Top 3 weakest shot types identified per match with named drill recommendations |
| Highlight clips | Best 3 rallies auto-extracted as 6-second MP4s, shareable to WhatsApp/Instagram |
| Club dashboard | Court utilisation, recording index, active player counts, engagement metrics |

### 2.2 Out of scope V1

- Live in-match insights (Year 2)
- Multi-camera 3D ball depth (Year 3, Series B feature)
- Line calling / officiating (deliberately out — high failure cost)
- Native iOS/Android apps (PWA is sufficient)
- Tournament management / draw generation (Year 2)
- Booking integration (handled via Hudle partnership)

---

## 3. End-to-End Architecture

### 3.1 Architecture diagram

```
LAYER 1 — COURT (per installation)
┌─────────────────────────────────────────────────────────────┐
│ Reolink RLC-823A IP camera (4K, PoE, IP66, ultra-wide)     │
│ Mounted behind back glass, ~5m high, ~15° downtilt          │
│ RTSP H.265 stream over PoE Cat6                             │
│             │                                                │
│             ▼                                                │
│ Raspberry Pi 5 8GB + 1TB NVMe (edge buffer)                 │
│  - MediaMTX relay (RTSP → segmented MP4 chunks)            │
│  - Local 7-day rolling buffer (offline-tolerant)            │
│  - Match-end trigger uploads to R2                          │
│  - Health metrics push every 60s                            │
└──────────────────────────┬──────────────────────────────────┘
                           │ TLS upload
                           ▼
LAYER 2 — INGEST & STORAGE
┌─────────────────────────────────────────────────────────────┐
│ Cloudflare R2 — match MP4 storage                           │
│ Cloudflare Workers — upload webhook + auth                  │
│ Cloudflare KV — install registry, court metadata            │
└──────────────────────────┬──────────────────────────────────┘
                           │ event trigger
                           ▼
LAYER 3 — INFERENCE
┌─────────────────────────────────────────────────────────────┐
│ RunPod RTX 3090 GPU worker (autoscaled, on-demand)         │
│  Pipeline (sequential per match):                           │
│   1. Video decode + downsample to 1080p30 for inference     │
│   2. Player tracking (YOLOv8m + ByteTrack)                  │
│   3. Pose keypoints (YOLOv8-pose 13-DOF)                    │
│   4. Ball tracking (TrackNet + InpaintNet)                  │
│   5. Court keypoint loading (from install cache)            │
│   6. Homographic projection (2D top-down map)               │
│   7. Shot-impact frame detection (ball trajectory analysis) │
│   8. SHOT CLASSIFIER (our trained model) ← PROPRIETARY       │
│   9. Skill scoring engine (rubric-driven)                    │
│  10. Highlight clip extraction (rally detector)              │
│  11. Output structuring (per-shot JSONL + summary JSON)     │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
LAYER 4 — APPLICATION DATA
┌─────────────────────────────────────────────────────────────┐
│ Supabase (managed Postgres + Auth + Storage + Realtime)    │
│  - players (identity, persistent across clubs)              │
│  - clubs (tenant, court count, subscription state)          │
│  - matches (court, timestamp, 4 player FKs, outcome)        │
│  - shots (match FK, player FK, class, quality, frame)       │
│  - skill_scores (player FK, time-series ELO snapshot)       │
│  - drills (recommendation engine output)                    │
│  - highlights (extracted clip URLs + ranking)               │
└──────────────────────────┬──────────────────────────────────┘
                           │
       ┌───────────────────┼────────────────────┐
       ▼                   ▼                    ▼
LAYER 5 — DELIVERY
┌──────────────┐  ┌─────────────────┐  ┌─────────────────────┐
│ Player PWA   │  │ Club Dashboard  │  │ WhatsApp Delivery   │
│ React + Vite │  │ Same React app  │  │ AutomationXpert     │
│ Cloudflare   │  │ Role-gated      │  │ router (own infra)  │
│ Pages        │  │ Recharts viz    │  │ Cost ~₹0.03/msg     │
└──────────────┘  └─────────────────┘  └─────────────────────┘
```

### 3.2 Why this architecture

| Choice | Rationale |
|---|---|
| Single camera, fixed mount | 1 camera covers the whole 20×10m court with an ultra-wide lens; reduces install cost; aligns with `padel_analytics`'s tested fixed-camera assumption |
| Cloud inference (not edge) for V1 | Lower hardware cost per court; centralised model updates; we can train smarter models without touching court hardware |
| Cloudflare R2 over AWS S3 | Zero egress fees; saves ~60% on bandwidth at scale; better fit for video |
| Supabase over self-hosted Postgres | Battle-tested in our existing AX platform; reduces ops burden; built-in Auth + Realtime |
| PWA over native | 8 weeks faster to ship; ~95% feature parity for our use case; instant deploy iteration |
| WhatsApp delivery | India has 600M+ WhatsApp MAU; existing AX router infrastructure; near-zero CAC for player engagement |
| Edge buffer (Pi 5) | Survives WiFi outages; segments long matches into uploadable chunks; cheap insurance against connectivity issues |

### 3.3 Failure modes and graceful degradation

| Failure | Impact | Degradation behaviour |
|---|---|---|
| Internet drops mid-match | None visible | Edge buffer continues recording; uploads when link restored; analysis delayed not lost |
| GPU worker queue saturated | Delay in feedback delivery | Match queued; player gets WhatsApp "your match is processing, results in 30 min"; SLA = best-effort |
| Ball tracking fails on particular match (e.g., dim lighting) | Reduced quality scores | Fall back to "movement-only" report; flag to client team; coach reviews edge cases |
| Camera offline | New matches not captured | Watchdog detects within 60s, alerts club + ops team; SLA = restore within 24h |
| Classifier confidence below threshold | "Inconclusive" shot label | Soft fail — show shot detected but no class label; do not pollute training data |

---

## 4. Computer Vision Pipeline — Layer-by-Layer Feasibility

For each layer below, "feasibility" = "we can ship V1 quality without inventing new ML."

### 4.1 Player tracking

- **Method:** YOLOv8m detector + ByteTrack association
- **Reference OSS:** Already integrated in `padel_analytics`
- **Court polygon filter:** Reject detections outside the homographed court polygon to exclude spectators, coaches, ball boys
- **Persistent ID over a match:** ByteTrack handles occlusion; for the 4-player padel case this is more reliable than tennis (smaller court, players don't leave frame)
- **Feasibility:** **Mature. V1 ready.**

### 4.2 Pose estimation (player skeleton keypoints)

- **Method:** YOLOv8-pose (13 keypoints) or HRNet (17 keypoints, higher accuracy at 3× compute)
- **Reference OSS:** Custom-trained YOLOv8-pose model already in `padel_analytics` (with public weights via Google Drive link in the upstream repo)
- **Coverage:** Wrists, elbows, shoulders, hips, knees, ankles. Sufficient for racket-arm angle, hip rotation, balance assessment
- **Feasibility:** **Mature. V1 ready.**

### 4.3 Ball tracking

- **Method:** TrackNet (multi-frame heatmap prediction for small fast objects) + InpaintNet to fill gaps when ball is occluded
- **Reference OSS:** `yastrebksv/TrackNet` (cleanest reference); ball-tracking node in `padel_analytics`
- **Padel-specific concern:** Yellow padel ball vs orange tennis ball — retrain on padel dataset (PadelVic provides labelled clips)
- **Frame rate dependency:** At 30 fps with 100 km/h ball, ball moves ~92 cm/frame; 60 fps preferred where camera supports it
- **Feasibility:** **Mature, needs padel retraining. Estimated 1 week of fine-tuning.**

### 4.4 Court keypoint detection / homography

- **Method:** Either (a) one-time manual click of 12 court keypoints at install, cached as JSON; or (b) automatic detection via a trained CNN heatmap regressor
- **For V1:** Option (a) — the install team clicks 12 points once, saved forever. Reliable, zero failure mode.
- **For V2:** Option (b) — retrain `yastrebksv/TennisCourtDetector` for padel courts; enables zero-install homography for mobile-camera scenarios
- **Feasibility:** **Trivially mature for V1.**

### 4.5 2D court projection

- **Method:** Standard perspective transform using the 12-point homography matrix
- **Output:** Top-down (x, y) coordinates in court metres for every player and ball, every frame
- **Use:** Heatmaps, court coverage %, partner-spacing analytics, distance run per player
- **Feasibility:** **Trivially mature. Implemented in `padel_analytics`.**

### 4.6 Shot impact / rally segmentation

- **Method:** Ball trajectory analysis — detect sharp velocity direction changes (= impact events) to segment continuous rallies and assign each shot to the nearest player
- **Reference:** Common pattern in tennis CV literature; needs adaptation to padel's wall-bounce dynamics
- **Feasibility:** **Standard. V1 implementable in ~2 weeks.**

### 4.7 Shot classification (THE PROPRIETARY LAYER)

**This is treated as its own section below.** See §5.

### 4.8 Highlight extraction

- **Method:** Rule-based — rank rallies by (length × ball-impact density × player movement intensity) → cut top 3 as 6-second clips with ffmpeg
- **Feasibility:** **Trivial. ~3 days of work.**

---

## 5. The Shot Classification Layer (Proprietary IP)

This is **the singularly unique technical work** of this venture. All other layers are reproducible from OSS. This layer is what we build, train, and own.

### 5.1 Problem formulation

**Input per shot:**
- Pose keypoint sequence: 13 joints × (x, y, confidence) × N frames (~30 frames centred on impact = 1 sec at 30 fps)
- Court-relative player position at impact (top-down x, y in metres)
- Ball trajectory feature vector: incoming velocity, angle, and bounce state at impact
- Opponent positions at impact (4 (x, y) coords)
- Score context: rally-length-so-far, point-importance (deuce, set point, etc.)

**Output per shot:**
- Shot class: one-of `{bandeja, vibora, smash, volley_forehand, volley_backhand, bajada, chiquita, x3, serve, return, lob, drive_forehand, drive_backhand, defensive_lob}` (~14 classes for padel V1)
- Quality score: 1–5 stars (the moat)
- Deviation flags: list of named flaws — `{arm_angle_low, hips_underrotated, balance_lost, ball_too_high_at_impact, non_racket_arm_dropped}`, etc.
- Tactical quality: 1–5 (was this the right shot choice given the situation?)

### 5.2 Why this is tractable

- It is **supervised classification on pre-extracted features**, not raw video understanding. The hardest part of CV (extracting pose from pixels) is done upstream.
- The feature space is small (~390-dim per shot), which means small models suffice and overfitting risk is manageable
- The shot class taxonomy is finite (~14 classes), labels are physically observable, and a trained coach can label a clip in <10 seconds
- Quality scoring is the same model with an additional regression head trained from coach-provided 1–5 labels

### 5.3 Proposed architecture (V1)

**Stage A — Class head:** Multi-layer perceptron over flattened pose sequence + positional + ball features → softmax over 14 shot classes.

**Stage B — Quality head:** Separate small MLP (sharing the early embedding layer) → regression to 1–5 quality score.

**Stage C — Deviation flags:** Sigmoid-activated multi-label head — one per named deviation.

**Inference order:** Class → quality → deviations. Quality and deviations are conditioned on predicted class.

**Why MLPs and not transformers for V1:** Compute-cheap, fast iteration, suitable for our dataset size. We re-evaluate after 1,000 labelled clips whether a temporal transformer (e.g., adapted MotionBERT) wins on held-out accuracy.

### 5.4 Data pipeline

| Stage | Effort | Owner |
|---|---|---|
| Coach designs taxonomy + rubric document (15 pages) | 10–15 hrs coach time | Coach |
| Coach labels 100 "gold standard" clips | 10 hrs coach time | Coach |
| 2 trained labellers do bulk labelling at ₹15k/mo each | 500 clips in 4 weeks | Labellers |
| Coach audits 10% sample weekly | 2 hrs/week | Coach |
| Build Streamlit labelling tool | 3 days | Engineer |
| Acquire supplementary clips from PadelVic dataset + own recordings | Ongoing | Engineer |

**Target dataset for V1:** 700 labelled clips covering all 14 classes with class balance.

### 5.5 Training protocol

- 70/15/15 train/val/test split, stratified by shot class
- Mixed loss: cross-entropy (class) + MSE (quality) + binary cross-entropy (deviations)
- Augmentation: temporal jitter, horizontal flip with player-side adjustment, pose-keypoint Gaussian noise
- Optimiser: AdamW with cosine schedule
- Early stopping on val accuracy
- Training run: ~2 hours on RTX 3090 per iteration

### 5.6 Acceptance criteria (V1)

- **Class accuracy:** ≥ 70% top-1, ≥ 92% top-2 on held-out test set
- **Quality MAE:** ≤ 0.7 on 1–5 scale (i.e., coach and model agree within ~0.7 stars on average)
- **Coach blind audit:** On 20 random matches, coach agrees with model's per-player skill summary "directionally" in ≥ 16 cases

### 5.7 Risk mitigations

- **Plateau below 70%:** Multi-coach labelling (add 2nd coach to get inter-rater agreement labels), expand dataset to 1,500 clips, ensemble of MLP + temporal CNN
- **Coach disagrees with model output:** Add human-in-the-loop relabel UI; weekly retraining cron on new corrections
- **Skill-level confusion (bandeja vs vibora pose looks similar):** Use ball trajectory feature as discriminator (vibora is faster), retrain with class-balanced sampling

---

## 6. Hardware Specification (Per Court)

### 6.1 Bill of materials

| Component | Specification | Supplier | INR | Lead time |
|---|---|---|---|---|
| Primary camera | Reolink RLC-823A 16x — 4K, PoE, IP66, IR, weather-resistant, 16× optical zoom for flexible mounting | Amazon India / Reolink India | 12,000 | 5–7 days |
| Premium alternative | Hikvision DS-2CD2T87G2-LU — 4K ColorVu (low-light excellence), PoE, IP67 | Authorised Hikvision dealer | 18,000 | 7–10 days |
| Edge compute | Raspberry Pi 5 8GB + 1TB NVMe HAT + active cooling case | Robu.in / SB Components India | 15,000 | 2–3 days |
| Network switch | TP-Link TL-SG1005P — 5-port PoE+ Gigabit | Amazon India | 3,000 | 2 days |
| Cabling | Cat6 outdoor-rated 25m + RJ45 connectors | Local | 1,500 | Same day |
| Mount + enclosure | Wall-mount bracket + IP66 weatherproof box for Pi | Local CCTV supplier | 1,500 | 2 days |
| Power adapter (Pi) | Official 27W USB-C | Local | 500 | Same day |
| **TOTAL PER COURT** | | | **₹33,500 standard / ₹39,500 premium** | **~1 week** |

### 6.2 Installation specification

- Camera mounted 4–5m above ground level, centred on court midline, behind the back glass, with 15–20° downtilt
- Maximum visible elements: full 20×10m court surface + back wall behind both player teams
- Network: PoE Cat6 from camera to PoE switch; CAT6 from switch to Pi; Pi connected to club WiFi for backhaul (or direct LAN where available)
- Power: single 230V outlet feeds the PoE switch; Pi runs off USB-C from switch's auxiliary or its own adapter
- Footprint: total mount and edge-box install completes in 90 minutes by 1 electrician + 1 operator

### 6.3 Operating conditions tolerance

- Temperature: 0–55 °C (camera and Pi both rated)
- Humidity: 0–95% non-condensing
- Ingress protection: camera IP66, Pi enclosure IP66
- Power resilience: 7-day local SSD buffer survives WAN outages; UPS recommended at club but not required

### 6.4 Maintenance & support

- Remote health beacon every 60s (camera + Pi)
- Auto-restart on Pi-side process failure
- Field-replaceable unit: cameras kept as spares (1 per 10 clubs); Pi kept as spare (1 per 20 clubs)
- Field service SLA: 24h replacement in install city; 48h elsewhere

---

## 7. Cloud & Backend Infrastructure

### 7.1 Stack choices

| Layer | Service | Why |
|---|---|---|
| Object storage | Cloudflare R2 | Zero egress fees; saves 60% vs AWS S3 at our scale |
| Compute (inference) | RunPod RTX 3090 / RTX 4090 | Pay-per-second; auto-scale; ~₹2.5/min |
| Database + Auth | Supabase (managed Postgres) | Battle-tested in our AX platform; built-in row-level security and Realtime |
| Web hosting | Cloudflare Pages | Global edge CDN; free tier ample; instant deploy |
| Edge compute (serverless) | Cloudflare Workers | Webhook handlers, upload auth, lightweight transforms |
| Messaging | AutomationXpert WhatsApp router | Own infra; near-zero marginal cost; bypasses Twilio premium |
| Observability | Sentry + PostHog | Standard for our team |
| Job queue | Upstash Redis + simple worker | Lightweight; scales sufficiently for V1 |

### 7.2 Inference cost model

At a single match (60 minutes of 1080p30 video):

| Stage | GPU time |
|---|---|
| Decode + downsample | 30s |
| Player + pose tracking (combined) | 80s |
| Ball tracking | 40s |
| Shot impact detection | 10s |
| Classification + scoring | 5s |
| Highlight extraction | 5s |
| Total | **~170s = ~2.8 minutes** |

At RunPod RTX 3090 rate of ~₹2.5/min → **~₹7 GPU cost per match.**

At 120 matches/court/month → **₹840/court/month GPU cost.**

At 1,000 matches/club/month for a large 4-court club → ₹7,000/month GPU cost; with reserved-instance discount, drops to ₹4,200/month.

### 7.3 Scaling forecast

| Scale | Monthly inference volume | GPU spend | Optimisation lever |
|---|---|---|---|
| 5 clubs, 600 matches/mo | 28 hrs GPU time | ~₹4k | On-demand |
| 25 clubs, 3,000 matches/mo | 140 hrs | ~₹21k | On-demand with batching |
| 200 clubs, 24,000 matches/mo | 1,120 hrs | ~₹170k | Reserved instances |
| 1,000 clubs, 120,000 matches/mo | 5,600 hrs | ~₹500k | Edge inference shift (Year 3) |

### 7.4 Storage cost model

Per match: 60-min 4K H.265 ≈ 3 GB raw; processed analytics ≈ 5 MB.

| Tier | Retention | Volume at 25 clubs | Cost |
|---|---|---|---|
| Hot (R2) | 30 days | 9 TB | ₹3,200/mo |
| Cold (R2 + Glacier-class) | 1 year | 30 TB | ₹4,800/mo |
| Analytics (Supabase) | Forever | <100 GB | Included in Pro plan |

### 7.5 Capacity ceilings

| Component | V1 ceiling | Hard limit | Next step |
|---|---|---|---|
| Single RunPod worker | 100 matches/day | 250 matches/day with batching | Parallel workers (auto-scale) |
| Supabase Pro plan | 8 GB database, 250 GB storage | Sufficient for ~10,000 players | Migrate to Team plan |
| Cloudflare Workers | 100k requests/day free | 10M/day paid | Not a bottleneck for V1 |
| R2 storage | Unlimited; cost-bounded | — | Cold-tier migration after 30 days |

---

## 8. Data, Privacy & Security

### 8.1 What data we hold

| Category | Examples | Sensitivity | Retention |
|---|---|---|---|
| Player identity | Name, WhatsApp number, club, photo (for tap-in) | Medium | While account active + 90 days |
| Match video | Raw recordings | Medium (faces visible) | 30 days hot, 1 year cold, then deletion unless flagged |
| Per-shot analytics | Class, quality, position | Low | Forever (anonymised post-deletion) |
| Skill scores | Time-series ratings | Low | Forever |
| Club operational | Court usage, billing | Medium | Forever |

### 8.2 Compliance posture

- **DPDPA (India Digital Personal Data Protection Act 2023):** Data fiduciary obligations — consent at signup, purpose limitation, ability to request deletion, breach notification within 72h. We design as data fiduciary from day 1.
- **GDPR (for EU pilot if applicable in Year 3):** SAR (subject access requests) and right to erasure tooling built into Supabase admin panel
- **Children's data:** No platform access for under-13s; under-18s require parental consent token
- **PCI-DSS:** Not in scope — Stripe / Razorpay handle all card data; we never touch it

### 8.3 Security controls

- All RTSP streams encrypted via VPN tunnel from court to ingest (Tailscale Lite or equivalent)
- Cloudflare R2 with signed URL access only — no public buckets
- Supabase RLS enforced on every table — players see only their data, clubs only their courts
- Secrets in Cloudflare KV (not in code)
- Quarterly third-party penetration test (Year 2 onwards)
- Encrypted laptop policy, MFA mandatory for all internal team

### 8.4 What we explicitly DO NOT collect

- Audio from court microphones (no microphone on cameras)
- Continuous outside-of-match footage (camera recording is match-windowed)
- Biometric face data for identification (we use tap-in QR + WhatsApp number, not face recognition)

This conservative posture is positioned as a **trust differentiator** vs. competitors that may default to face recognition.

---

## 9. Multi-Sport Extensibility — Badminton & Tennis Roadmap

The architecture is **sport-agnostic at every layer except (a) court keypoints, (b) shot taxonomy, and (c) the trained classifier model**. Adding a new racket sport is a multiplexed deployment of the existing platform, not a rebuild.

### 9.1 What stays the same across all racket sports

| Layer | Reuse |
|---|---|
| Camera hardware | Identical |
| Edge buffer + ingest | Identical |
| Cloudflare R2 + Supabase backend | Identical (per-sport tenant flag) |
| Player tracking | Identical (same YOLOv8m) |
| Pose estimation | Identical (same YOLOv8-pose) |
| Ball tracking (TrackNet) | Re-fine-tune for ball appearance — 1 week |
| 2D court projection logic | Identical algorithm |
| Player PWA + club dashboard | Identical with sport-specific theming |
| WhatsApp delivery | Identical |
| Skill scoring engine | Identical (rubric-driven; rubric content changes) |

### 9.2 What changes per sport

| Sport | Court dimensions | Net height | Ball | Shot taxonomy size |
|---|---|---|---|---|
| Padel (base) | 20m × 10m | 0.88m centre | Yellow padel ball (faster) | ~14 classes |
| Tennis | 23.77m × 10.97m | 0.914m centre | Yellow tennis ball | ~20 classes (FH/BH × topspin/slice × volley × overhead × serve × return × lob × drop, etc.) |
| Badminton | 13.4m × 6.1m | 1.55m centre | Shuttlecock (very different aerodynamics) | ~16 classes (clear, drop, smash, drive, net shot, lift, push, etc.) |
| Pickleball | 13.4m × 6.1m (same as badminton) | 0.86m centre | Wiffle-ball-like | ~12 classes |

### 9.3 Per-sport effort estimate

| Task | Padel (V1, baseline) | Tennis add | Badminton add |
|---|---|---|---|
| Court keypoint retraining | 1 week | 1 week | 2 weeks (more keypoints) |
| Ball/shuttle tracker retraining | 1 week (yellow ball, retrain TrackNet) | 0 (same as padel) | 4 weeks (shuttlecock is much harder — non-rigid, very different trajectory dynamics, lower visibility) |
| Coach + rubric design | 4 weeks | 4 weeks (different coach) | 4 weeks (different coach) |
| Classifier training | 8 weeks (1,000 clips) | 6 weeks (4,000+ public tennis clips available) | 8 weeks (limited public datasets) |
| PWA/dashboard theming | 2 weeks | 1 week (re-use Padel) | 1 week |
| Total to launch | 12 weeks | 8 weeks | 12 weeks (shuttle is the long pole) |

### 9.4 Strategic sequencing

**Year 1:** Padel only. Don't dilute focus.

**Year 2 Q3–Q4:** Tennis as second sport.
- Why tennis next: shares ball physics with padel (TrackNet transfers); largest pool of analytics-curious players; India has 800+ tennis academies; Bhupathi network gives instant credibility
- Coach to hire: ex-AITA / Davis Cup coach
- Expected revenue lift: +40% to total ARR within 6 months of launch

**Year 3 Q1–Q2:** Badminton as third sport.
- Why third (not second): shuttlecock tracking is hard; data is sparse; but **India is the world's #1 badminton market by participation** — domestic TAM exceeds tennis + padel combined
- Coach to hire: ex-PV Sindhu camp / SAI-level
- Investment thesis lift: "Tri-racket-sport platform" frames Series A as a **₹500 Cr opportunity, not ₹50 Cr**

**Year 3 Q3+:** Pickleball.
- Why fourth: explosive global growth (USA leads), shares court dimensions with badminton (re-use court keypoint detector), small classifier delta from badminton
- Particularly relevant for UAE / Saudi expansion (pickleball is gaining traction in MENA)

### 9.5 Multi-sport positioning value

A single platform across padel + tennis + badminton + pickleball:
- **For clubs:** One vendor, one camera, one dashboard regardless of court mix — radical operational simplification
- **For players:** One identity, one skill score domain, one PWA — players who play multiple sports never have to switch
- **For investors:** A 4-sport addressable market in India + Asia + ME = ~25,000 courts addressable (vs. ~5,000 for padel alone)
- **Defensibility:** Each additional sport widens our moat — no competitor today serves all four

---

## 10. Technical Risk Register

| # | Risk | Likelihood | Severity | Owner | Mitigation |
|---|---|---|---|---|---|
| T1 | Shot classifier accuracy plateaus below 70% | Medium | High | CTO | Multi-coach labels; dataset expansion to 1,500; ensemble model; senior CV contractor escalation if stuck >Week 8 |
| T2 | Ball tracking unreliable in dim indoor club lighting | Medium | Medium | Hardware lead | Upgrade to Hikvision ColorVu camera (₹6k delta); recommend club to add 2× 50W LED panels at ₹4k each |
| T3 | RTSP stream drops frames intermittently | Medium | Low | Engineer | Edge buffer + ffmpeg watchdog; auto-restart on stream-frame-gap detection |
| T4 | `padel_analytics` upstream goes inactive | Low | Medium | CTO | Fork early (within Month 1); do not depend on upstream; build CI to validate against latest |
| T5 | YOLOv8 license changes affect commercial use | Low | High | CTO | Track AGPL → enterprise license change; budget for Ultralytics enterprise licence (~$1k/yr) if needed; OR swap to YOLOv7 / RTMPose (MIT-licensed) |
| T6 | Single court keypoint click drifts over time | Low | Low | Ops | Quarterly recalibration cron; auto-detect via court-keypoint CNN as fallback |
| T7 | Player misidentification (4 players, similar clothing) | Medium | Medium | CTO | Combine tracking + WhatsApp tap-in + jersey-colour-cluster fallback |
| T8 | Edge Pi 5 hardware reliability in monsoon | Medium | Low | Hardware lead | IP66 enclosure; humidity monitor; cooling fan; 1 spare unit per 20 clubs |
| T9 | Cloud GPU cost spikes during demand surges | Low | Low | Engineer | Reserved RunPod capacity at Series A; auto-scaling cap; queue prioritisation |
| T10 | Padel-specific datasets remain small / proprietary | High | Low | CTO | Build our own labelled dataset; treat as competitive moat; do not depend on public datasets long-term |
| T11 | Apple Vision / CoreML stack chosen for edge V2 but pipeline migration takes longer than estimated | Medium | Medium | CTO / Apple advisor | Prototype on single court; staged rollout; preserve Jetson Orin Nano fallback path |

---

## 11. Build vs Buy vs Fork Decision Matrix

| Component | Build | Buy | **Fork OSS** | Rationale |
|---|---|---|---|---|
| Player tracking | | | ✅ `padel_analytics` | Mature OSS |
| Pose estimation | | | ✅ `padel_analytics` | Mature OSS |
| Ball tracking | | | ✅ `TrackNet` | Mature OSS, retrain for padel |
| Court keypoint detection | | | ✅ `TennisCourtDetector` | Retrain for padel |
| Pipeline orchestration | ✅ | | | Custom; needs streaming refactor |
| Shot classifier | ✅ | | | **Proprietary moat** |
| Skill scoring engine | ✅ | | | **Proprietary moat (encodes coach's rubric)** |
| Player identity | | | ✅ Supabase Auth | Standard |
| PWA frontend | ✅ | | | Standard React; no shortcuts needed |
| WhatsApp delivery | | | ✅ AX router (own) | Already built for AX |
| Video storage | | ✅ Cloudflare R2 | | Buy infra |
| GPU inference | | ✅ RunPod | | Buy capacity |
| Database | | ✅ Supabase Pro | | Buy managed |
| Highlight clipping | ✅ | | | ~3 days work; not worth buying |

**Net:** Build ~30% (the proprietary parts), Buy ~30% (managed infra), Fork ~40% (mature OSS).

This balance is the right shape for a 12-week V1 — minimum custom work focused on the proprietary moat layers.

---

## 12. Performance Targets & Acceptance Criteria

### 12.1 V1 Ship Criteria

| Metric | Target | Method |
|---|---|---|
| Match-end to first-WhatsApp-message latency | < 12 minutes (P95) | Production telemetry |
| Pipeline crash rate | < 1% of matches processed | Sentry + custom monitor |
| Shot classifier top-1 accuracy | ≥ 70% on held-out test | Coach-labelled test set |
| Shot quality MAE | ≤ 0.7 on 1–5 scale | Coach-labelled test set |
| Coach blind audit agreement | ≥ 80% directional agreement | Random 20-match sample |
| Highlight clip relevance | ≥ 75% relevance rate (coach judged) | Random 50-clip sample |
| Camera uptime | ≥ 99% (excluding power outages) | Heartbeat monitor |
| Player feedback satisfaction (NPS) | ≥ +20 | In-app survey post-3rd match |

### 12.2 Scale Criteria (Month 12)

| Metric | Target |
|---|---|
| Clubs live | 25 |
| Matches processed / month | 3,000 |
| Pipeline cost per match | ≤ ₹10 |
| Active analysed players (WAAP) | ≥ 1,500 / week |
| Player retention (D30) | ≥ 60% |
| Club churn (annualised) | ≤ 10% |
| Classifier accuracy on new club | ≥ 65% top-1 (transfer test) |

---

## 13. Edge Inference — Year 2/3 Architecture

Year 1 architecture runs all inference in the cloud. This is the right choice for V1 (centralised iteration, model upgrades hit every court instantly, no field hardware update headaches). It becomes the wrong choice at scale because GPU cost grows linearly with court count.

### 13.1 The migration trigger

Migrate to edge inference when **GPU cost > ₹3 lakh/month** (roughly 200 active clubs). Below that, cloud is cheaper than the engineering + ops cost of an edge fleet.

### 13.2 Two credible edge paths

**Path A — NVIDIA Jetson Orin Nano (₹40k) or Orin NX 16GB (₹70k)** *(safe path)*
- Mature CUDA stack
- TensorRT-optimised inference of YOLOv8 + custom classifier at 30 fps
- 8 GB unified memory (Nano) tight; 16 GB (NX) comfortable
- Linux-based; familiar ops
- Software ecosystem entirely server-friendly

**Path B — Mac mini M4 (₹60–70k) with CoreML on Apple Neural Engine** *(higher-upside path)*
- M4's Neural Engine is genuinely top-tier for vision workloads
- Lower power than Orin NX (relevant for venue installs)
- CoreML model conversion is mature; the labour is in pipeline plumbing on macOS
- **Risk:** macOS is not a typical production-server OS; long-running headless services need careful management; community references for this kind of multi-site deployment are thin

**Recommendation:** **Prototype Path B on 2 courts in parallel with Path A on 8 courts during the migration window.** Pick the winner based on Q1 of that year's reliability + cost data. The Apple advisor (Manoj's son, pending) is the right person to run the Path B feasibility prototype.

### 13.3 Edge architecture

```
[Camera] → [Mac mini M4 or Jetson Orin NX]
              │
              ├─ CoreML / TensorRT inference (all 9 stages)
              ├─ Local result cache (Supabase Edge)
              ├─ Result sync to cloud Supabase (delta only)
              └─ Player WhatsApp delivery via cloud
```

### 13.4 Cost crossover (illustrative)

At 200 clubs, 24,000 matches/month:
- Cloud-only: ~₹1.7 lakh/mo GPU spend
- Edge-only (Mac mini M4 × 200 amortised over 36 mo): ~₹35,000/mo + ~₹15k support → **₹50k/mo, 70% cheaper**

ROI on edge fleet pays back in ~9 months.

---

## 14. Feasibility Verdict

**Strongly feasible.** The proposed system can be built in 12 weeks for a V1 ship by a 3-person founding team (CEO + CTO/ML + Coach) augmented by two ₹15k/month labellers, using off-the-shelf cameras (~₹35k per court), managed cloud infrastructure (~₹540 COGS per court per month), and a directed fork of `Joao-M-Silva/padel_analytics` and `yastrebksv/TrackNet`.

**The single non-commodity technical asset** is the shot-quality classifier, trained on coach-designed rubric labels — a supervised classification problem on pre-extracted pose-keypoint features that is technically tractable and proprietary by virtue of the labelling work, not the model architecture. This is the defensible moat.

**Year 2 extensibility to tennis and badminton** is architecturally straightforward — same hardware, same backend, retrain ball tracker and classifier per sport, add per-sport rubric authored by a sport-specialist coach. Tri-sport coverage achievable within 24 months.

**Edge inference migration** is feasible on either NVIDIA Jetson Orin or Apple Mac mini M4 + CoreML when fleet exceeds 200 active clubs.

**No layer of the proposed stack requires invented science.** The risk is execution speed and labelling-data quality, not technical impossibility.

**Recommended next steps:**
1. Lock CTO/ML co-founder (target João Silva, fallback senior Bangalore CV hire)
2. Lock padel coach co-founder
3. Install pilot court hardware at base club (~₹35k)
4. Begin coach rubric authorship and parallel labelling pipeline
5. Re-review this report on **2026-10-01** against actual classifier accuracy on first 500 labelled clips

---

## Appendix A — Open Source Repositories Referenced

| Repo | Role | Stars | License |
|---|---|---|---|
| github.com/Joao-M-Silva/padel_analytics | Primary pipeline fork | ~150 | MIT |
| github.com/yastrebksv/TrackNet | Ball tracking | ~300 | MIT |
| github.com/yastrebksv/TennisCourtDetector | Court keypoint reference | ~250 | MIT |
| github.com/ArtLabss/tennis-tracking | Reference pipeline | ~700 | GPL-3.0 (avoid direct fork — reference only) |
| github.com/UPC-ViRVIG/PadelVic | Labelled padel dataset | ~50 | Apache-2.0 |
| github.com/andresgilvicente/padel-ai-system | Serve validation reference | ~60 | MIT |
| github.com/ultralytics/ultralytics | YOLOv8 base | ~30k | AGPL-3.0 (commercial licence required) |
| github.com/bluenviron/mediamtx | RTSP relay / edge ingest | ~10k | MIT |

## Appendix B — Hardware Vendor Contacts (India)

| Vendor | Product | Contact path |
|---|---|---|
| Reolink India distributor | RLC-823A | Amazon India enterprise account; bulk-buy discount available at 25+ units |
| Hikvision India | DS-2CD2T87G2 series | Authorised dealer at Lamington Road (Mumbai) or SP Road (Bangalore) |
| Robu.in | Raspberry Pi 5 + accessories | Direct API ordering; ~3 day Bangalore delivery |
| SB Components India | Pi-class hardware | Alternative supplier |

## Appendix C — Compliance Reference

- Indian Digital Personal Data Protection Act 2023 (DPDPA) — full text: https://www.meity.gov.in/data-protection
- Data fiduciary registration: required when scale crosses prescribed thresholds (not yet binding for early-stage)

---

**End of Technical Feasibility Report v1.0**

*This document is companion to PADEL_AI_VENTURE_PLAN.md (strategy) and PROJECT_REPORT.md (execution). For commercial framing, see COMMERCIAL_REPORT.md.*
