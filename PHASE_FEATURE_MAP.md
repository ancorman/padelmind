# PadelMind — Phase Completion & Feature Map Comparison Plan

**Purpose:** one page that says, at any moment: what's DONE, what ships NOW from the current CV learning, what we PROMISE over time — and the coach-powered path to pose intelligence. Marketing copy, app screens, and club pitches should be written off this table and never promise past it.

**Date:** 2026-07-12 · Owner: Manoj + Claude Code
**Siblings:** `CV1_BUILD_LOG.md` (execution log) · `PHASE1_CV_SCOPE.md` (module spec) · `SASANK_SOW_PHASE1.md` (integration contract)

---

## 1. Phase completion status

| Phase | Scope | Status |
|---|---|---|
| **Phase 0 — Rails** | Supabase schema, R2, CF Worker queue, calibration tool, Player PWA | ✅ **DONE** (2026-07-11) |
| **Phase 1 — CV pipeline** | Player tracking → heatmaps + rallies + highlights, WA delivery | 🔨 **IN BUILD** — Step 1 env ✅, bootstrap model training on Colab ⏳, Steps 2–8 pending (4–8 need Sunday NSCI recording + calibration) |
| **Phase 1.5 — Stats layer** (NEW, this doc) | Movement/tactics reports computed from Phase-1 positions JSON — no new CV | 🔜 next after Phase 1 core; ships into WA report + PWA |
| **Phase 2a — Ball intelligence** | Padel-tuned ball tracking (TrackNet-class) | ⬜ promised roadmap |
| **Phase 2b — Pose / coaching** | Skeletons + coach-defined shot & technique intelligence | ⬜ promised roadmap — **coach identified**, workflow §4 |
| **Phase 3** | Live/real-time, multi-camera | ⬜ far roadmap |

---

## 2. Feature map — SHIP NOW vs PROMISE LATER

### Tier S — Ships with Phase 1 core (the pilot wow-moment)
Source: player boxes → ByteTrack → homography → court positions.

| Feature | Delivery surface |
|---|---|
| Per-player court heatmap (4 PNGs) | WA message + PWA |
| Match highlight reel (top rallies, 9:16) | WA message + PWA |
| Rally count + rally timeline | WA text summary + PWA |
| Match duration | WA text summary |

### Tier S+ — Ships with Phase 1.5 "stats layer" — ALL derivable from positions JSON TODAY
No new models. Pure math on data the pipeline already emits. Build effort: days.

| Feature | Player-facing line |
|---|---|
| Distance covered | "You ran 3.2 km" |
| Sprint count + top speed | "14 sprints, fastest 18 km/h" |
| Court coverage % | "You defended 64% of your half" |
| **Net time vs baseline time** | THE padel tactic metric — "only 22% at net" |
| Partner spacing discipline | "avg 3.1 m from partner" |
| Recovery-to-centre habit | "you watch, you don't reset" |
| Rally intensity curve / fade point | "your intensity dropped after min 52" |
| Longest rally + golden-point flags | feeds better highlight picking |
| Multi-match trends (phone = identity) | "net time up 12% this month" |
| WhatsApp share/stats card | player's IG story = free distribution |

### Tier P — PROMISED over time (roadmap language: "coming to your reports")
| Feature | Unlock | Phase |
|---|---|---|
| Real shot counts per rally | ball tracking | 2a |
| Ball speed ("your smash: 87 km/h") | ball tracking | 2a |
| Shot placement maps (where shots LAND) | ball tracking | 2a |
| Winner/error attribution, scorekeeping | ball tracking (+serve inference) | 2a |
| Shot-type breakdown (bandeja/vibora/volley…) | pose + coach labels | 2b |
| Technique feedback per shot type | pose + coach rubric | 2b |
| Split-step/readiness + fatigue posture signals | pose | 2b |
| Score OCR, live analysis, multi-cam | misc | 2/3 |

### Player Score / classification protocol (V2 flagship — decided 2026-07-12)
**Rule: V1.5 metrics are STATS, never a "score."** V1.5 measures activity, not skill (fit beginner would out-score lazy expert). A credible **PadelMind Level** needs 6 pillars:
1. **Stroke quality** — technique vs coach rubric (pose, 2b)
2. **Outcome attribution** — winners/unforced errors (ball, 2a)
3. **Consistency** — rally survival, error variance (2a/2b)
4. **Tactical positioning** — net presence, recovery, pair coordination (partially in V1.5 — only early pillar)
5. **Shot selection** — right shot for the situation (2b+, coach judgment)
6. **Opponent-relative results** — Elo-style anchor from match results + identity (**cheap — start NOW**)

**Start pillar 6 in V1.5:** add match-result capture (club staff via PADEL END, or player-confirmed in PWA) → Elo accumulates silently from day one; every pre-V2 match still feeds the eventual score. Waiting costs history.

**Score validation protocol (the ground-truth loop):** coach blind-rates 20–30 known players (another ~30-min MCQ worksheet); correlate composite vs coach ratings; tune pillar weights until correlation is strong; only then display a number. Two-coach divergence protocol applies — players the coaches disagree on are the key calibration cases. Launch "PadelMind Level" once, credibly, as a V2 headline (retention + matchmaking hook).

### Club-side features (no CV; sell-side sweeteners — build only against a paying-club ask)
Match-of-the-week reel for club IG · court-utilization analytics · weekly player leaderboards · intensity-based matchmaking.

**Rule: app + pitch may show Tier S and S+ as LIVE, Tier P only under "coming soon" with no dates promised to players. Club contract dates only after 2a/2b are scoped-for-real.**

---

## 3. App integration of Tier S+ (straight-away plan)

> **UI scope done 2026-07-12:** full screen-by-screen design in `UI_MATCH_REPORT_SCOPE.md` (WA template, PWA wireframe w/ data sources + empty states, share card, component plan). Estimates: **V1 UI ≈ 16 h, V1.5 UI ≈ 29.5 h.** Dependencies flagged there: RLS co-player heatmap read, R2 CORS for share card, deep-link survival through magic-link auth, `stats` jsonb + trends view.

1. **Compute in the RunPod worker** — extend the pipeline after position logging with a `stats.py` module (pure numpy on position_log). Outputs one `stats.json` per match to R2 alongside heatmaps.
2. **Callback carries stats** — add `stats` block to the existing Worker callback payload (schema already has a `stats` stub in SOW §4.2 — we fatten it).
3. **WA message upgrade** — text summary grows from 3 lines to a match report (duration, rallies, km run, sprints, net-time %, longest rally).
4. **PWA match page** — render stats.json as stat tiles + intensity sparkline; share-card generator (PNG) for IG stories.
5. **Trends** — nightly rollup per player phone across matches (Supabase view) → "vs your last match" deltas.

---

## 4. Coach workflow — pose/skeleton validation (Phase 2b prep)

**Principle: the coach never draws, never annotates skeletons — models extract joints automatically. The coach supplies padel JUDGMENT via single-tap MCQs on a scrolling worksheet.** Worksheet = same vanilla HTML+canvas pattern as the calibration tool; phone-friendly.

| Job | Format | Coach effort |
|---|---|---|
| **J1 Shot vocabulary labeling** | Scrolling sheet of 2–4 s clips (skeleton overlaid), one tap: Forehand/Backhand/Volley/Bandeja/Vibora/Smash/Lob/Serve/**Unclear** | ~6–8 s/clip → 1,000 clips ≈ 2 h; target 2,000–3,000 total = **4–6 h across 2–3 weeks** |
| **J2 Technique rubric** | Structured interview per shot type: 3–5 checkpoints separating correct/wrong (elbow height, contact point, knee bend…) → we convert to joint-angle rules | **2–3 h once** |
| **J3 Ongoing validation** | Sheet shows model verdict + skeleton; coach taps Agree/Disagree(+MCQ reason) | **~30 min/week** during Phase 2b |

**Total coach ask: ~8–12 hours, all phone-tap work, zero technical skill.**

Design rules (dataset-quality critical):
- Clips, never stills — shot identity lives in motion.
- Skeleton overlay always visible — he's validating what the machine sees.
- Always an "Unclear / bad angle" escape — forced answers on garbage poison training data.
- All labeling on **our NSCI-camera footage** (post-Sunday) so labels match our deployment domain.
- Frame/clip selection is OURS (auto-cut around motion peaks near players) — coach never hunts through footage.

Verdict: **yes — with frame selection done by us and an MCQ scrolling worksheet, the coach can fully deliver the pose-validation dependency.** His labels + rubric are exactly the two inputs Phase 2b is blocked on per the SOW.

### Two-coach protocol (decided 2026-07-12 — Manoj's call, refined)
Dual labeling with adjudication — divergence is signal (ambiguous clips + vocabulary mismatch), but full duplication is wasteful. Protocol:
1. **Calibration round** — both coaches label the SAME 100 clips → measures agreement, surfaces vocabulary mismatch early.
2. **Reconcile session** — 30-min call on divergent clips only → single agreed taxonomy.
3. **Volume split** — remaining clips split between coaches with a **hidden 20–25% overlap** (neither knows which) → continuous agreement monitoring at ~1.25x effort instead of 2x.
4. **Adjudication** — overlap divergences re-voted with an explicit "genuinely ambiguous" option; still-split clips are EXCLUDED from training (never side-picked).
Effort: ~7–8 h per coach (vs 12 h naive duplication). Early exit: if calibration agreement ≥95%, drop to one coach + spot checks.
**J2 rubric exception:** technique philosophy can legitimately differ between coaches — run the rubric interview JOINTLY and force one agreed rubric (or name a head coach with tie-break authority). Two conflicting definitions of "correct" trains neither.

---

## 5. Immediate next actions (unchanged discipline: one step at a time)

1. Finish bootstrap training (Colab, running now) → R5 benchmark.
2. Steps 2–3 of CV1 (detect + track on test video).
3. Sunday: record + calibrate NSCI Court 2 → Steps 4–8.
4. Then Phase 1.5 `stats.py` (this doc §3).
5. Coach: send J2 interview invite only after Phase 1 pilot is live (don't spend his goodwill early).
