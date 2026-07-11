# Padel AI Coach — Technical Review Request

**To:** [Son's name]
**From:** Papa (Manoj)
**Date:** 2026-07-01
**Reading time:** 20 min for the brief + 30 min for the technical depth (if you have it). Honest answers to the questions at the end are the prize.

---

## Why this document exists

You introduced me to Clutch. You play 3x a week. You're on their app. You work at Apple in AI. There is **no one whose technical and product opinion would change my decisions more** on this venture.

I am committing to building an India-first AI padel coaching platform — a Clutch-equivalent but defensible by geography and language, with an expert coach co-founder designing the technique rubric. I have done about 4 hours of due diligence research with Claude. This document is the **distilled output of that research**. I'd like you to:

1. **Read the technical plan below**
2. **Tell me where I'm wrong, where Apple-stack thinking changes the answer, and where the moat thesis breaks**
3. **Not commit any time** — just give direction. I want your brain, not your weekends. Time investment only if we hit commercial traction (paying clubs).

If you accept this lightweight advisory role, the equity ask would be **0.5–1% over 2-year vest as a formal advisor** — designed so you have a real upside if this works, no obligation if it doesn't, and zero conflict with Apple.

---

## Part 1: The product (what we'd build)

A single IP camera per padel court records every match. Cloud AI runs computer vision: player tracking, ball trajectory, pose estimation, court keypoints, and most importantly — **shot classification scored against an expert padel coach's rubric**. Players get a WhatsApp message 10 min after every match: "Your bandeja: 3.2/5, your hip rotation is 18° below ideal. Drill — shadow swing with hip cue, 5 min/day."

**The MVP scope:**
- 1 camera per court (Reolink RLC-823A 4K, PoE, ~₹12k)
- Edge buffer (Pi 5 8GB + 1TB NVMe) for offline reliability
- RTSP stream → cloud GPU (RunPod RTX 3090) → analysis
- Player PWA delivered via WhatsApp link
- Club dashboard for court owners

**The product roadmap:**
- V1 (Month 3): Movement + shot histogram + skill score
- V2 (Month 6): Shot quality scoring + drill recommendations + clips
- V3 (Month 12): Cross-club player identity ("Skill Score") + matchmaking
- V4 (Year 2): Edge inference (this is where I want your Apple Neural Engine view)

---

## Part 2: The technical stack we propose

### 2.1 OSS we'd fork as the base

| Component | OSS pick | Why |
|---|---|---|
| Full pipeline scaffold | [Joao-M-Silva/padel_analytics](https://github.com/Joao-M-Silva/padel_analytics) | Player tracking + pose + ball + court keypoints already wired. Author actively seeking collaborators. |
| Ball tracking | [yastrebksv/TrackNet](https://github.com/yastrebksv/TrackNet) | Cleanest TrackNet implementation. Padel-retrain candidate. |
| Court keypoints | [yastrebksv/TennisCourtDetector](https://github.com/yastrebksv/TennisCourtDetector) | Retrain on padel court keypoints. |
| Reference pipeline | [ArtLabss/tennis-tracking](https://github.com/ArtLabss/tennis-tracking) | Tennis HawkEye OSS — most complete reference. |
| Training datasets | [UPC-ViRVIG/PadelVic](https://github.com/UPC-ViRVIG/PadelVic) | Padel-labeled video datasets. |

### 2.2 Live architecture (proposed)

```
┌─────────────────────────────────────────┐
│ Court — physical install                 │
│  Reolink RLC-823A (4K, PoE, ultra-wide) │
│  ↓ RTSP H.265                            │
│  Pi 5 + 1TB NVMe (edge buffer)           │
│  - Records to disk during WiFi drops     │
│  - Match-end trigger uploads MP4 to R2   │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│ Cloud: Cloudflare R2 (object storage)    │
└──────────────┬──────────────────────────┘
               │ webhook trigger
               ▼
┌─────────────────────────────────────────┐
│ RunPod GPU worker (RTX 3090)             │
│  1. YOLOv8m player detection             │
│  2. YOLOv8-pose 13-DOF keypoints         │
│  3. TrackNet ball trajectory             │
│  4. Court homography (12-pt cached)      │
│  5. SHOT CLASSIFIER ← our trained model  │
│  6. Skill scoring engine ← our rubric    │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│ Supabase (Postgres + Auth)               │
│  Player identity, match records,         │
│  scores, drill recommendations           │
└──────────────┬──────────────────────────┘
               │
       ┌───────┴────────────┐
       ▼                    ▼
┌──────────────┐    ┌──────────────────┐
│ Player PWA   │    │ Club dashboard   │
│ (Cloudflare  │    │ (same React app, │
│ Pages, React)│    │  role-gated)     │
└──────────────┘    └──────────────────┘
       │
       ▼
WhatsApp delivery (we have this — AutomationXpert router)
```

### 2.3 The hard ML problem (where you can save us months)

**The classifier is the moat.** Pipeline diagram shows step 5 ("shot classifier"). This is the one piece **not solved in OSS**. We have to train it.

Plan:
- **Input:** Per-frame pose-keypoint sequence (~30 frames at 30fps = 1 sec around ball impact) + court-relative position + ball trajectory feature
- **Output:** Shot class (bandeja, vibora, smash, volley, bajada, chiquita, x3, serve, return, lob, drive) + **quality score 1–5** + **specific deviations from ideal form**
- **Training data:** Coach designs rubric (10-15 page IP doc) + labels 100 gold-standard clips + 2 trained labellers do bulk labelling (target 500–700 clips for V1)
- **Architecture (placeholder):** Small MLP or temporal CNN on pose-keypoint features → multi-head (class + quality + deviation flags)
- **Target accuracy V1:** 70% top-1 class accuracy

**The big technical question I want your view on:** Is this approach right? Or should we be looking at:
- (a) Temporal transformer over keypoints?
- (b) Fine-tune a pretrained pose-classifier (e.g., MotionBERT)?
- (c) Multi-modal (pose + ball trajectory features cross-attention)?
- (d) Self-supervised pretraining on unlabeled padel video first, then small labeled fine-tune?

### 2.4 Hardware bill of materials (per court)

| Item | Spec | INR |
|---|---|---|
| Camera | Reolink RLC-823A 16x or Hikvision DS-2CD2T87G2 | 12,000–22,000 |
| Edge buffer | Pi 5 8GB + 1TB NVMe + case + cooling | 15,000 |
| PoE switch | TP-Link TL-SG1005P | 3,000 |
| Cabling + mount + IP66 box | Local | 2,000 |
| **Per-court total** | | **~₹32,000–42,000** |

### 2.5 Cloud cost per court per month (at 120 matches/court/month)

| Item | INR |
|---|---|
| RunPod GPU inference (~3 min/match × ₹2.5/min) | 360 |
| R2 storage + egress | 150 |
| Supabase free/pro tier | 30 |
| WhatsApp delivery (own infra) | 30 |
| **Total COGS / court / mo** | **~₹540** |

At ₹5,000/court/mo ASP → **~89% gross margin.**

---

## Part 3: Edge inference (V2/V3) — the Apple-stack question

**This is where you have a 10x view I don't.**

Year-2 plan currently has us migrating from "cloud-only inference" to "edge inference on a small device per court" — primary motivations:
1. Cost: cloud inference at scale (1,000+ clubs) gets expensive
2. Latency: live in-match insights need <1 sec round trip
3. Bandwidth: 4K RTSP to cloud at scale = ISP grief at clubs

Default plan picks **NVIDIA Jetson Orin Nano (₹40k) or Jetson Orin NX 16GB (₹70k)** as the edge device. That's the safe path.

**The Apple-stack alternative I want your view on:**
- Mac mini M4 (₹60–70k) as the edge box per court, running CoreML-compiled models on Neural Engine
- Pros: cheaper than Orin NX, Apple Neural Engine is genuinely top-tier for vision workloads, you'd know how to optimize this in your sleep
- Cons: macOS is not a server OS most people use for production deploys; software ecosystem (RTSP capture, ffmpeg, headless service management) is slightly more awkward
- **Reality check question:** Have you seen anyone do production CV pipelines on Mac mini in a multi-site deploy? Or is this a thought experiment? If real, can you point me at any case studies?

There's a Mac Pro M2 Ultra angle for a regional inference node serving 10–20 clubs from a colocated rack. Same question.

---

## Part 4: Competitive landscape (what we found)

You know Clutch. There are 7–8 European competitors (Clutch, Wingfield, Padelytics, Eyes-On, GAMETRAQ, SPASH, PlaySight). The interesting find this week:

**Epic Padel ($10M seed Sept 2025)** — US-based rollup that OWNS Clutch AI + Padel India (chain of courts) + Red Padel (the world rating) + multiple US club chains. They're launching **Zero.40 in 2026** — "club operating system" combining all of this. Clutch India is their Bangalore arm — Curved Consistency Technologies Pvt Ltd, co-founded by **Sharath Kumar** (ex-Ninjacart, ex-BharatPe).

**China that I missed in the first pass:**
- 小球圈 (Xiaoqiuquan) — ex-ByteDance + ex-DJI founders, AI coach for tennis/badminton/table-tennis/pickleball, already top-50 on Chinese sports app charts, ~30% MoM user growth. **They will add padel within 12 months.**
- Lumistar (Shenzhen) — AI tennis training systems (TERO launched Mar 2026)
- SenseTime — already runs basketball AI analytics for Chinese pro teams
- Hikvision/Dahua — they manufacture the cameras we'd buy; could vertically integrate

**Our moat thesis** (please critique honestly):
- ❌ Tech moat — we agree there isn't one; it's commodity ML
- ✅ India geopolitical wall vs Chinese SaaS (TikTok/PUBG-style)
- ✅ Federation distribution lock (Asian Games 2026 catalysed national federations forming NOW)
- ✅ Padel coach co-founder = proprietary rubric dataset
- ✅ WhatsApp-native distribution + Hindi/Arabic UX depth

**The biggest risk** I see: if Sharath Kumar's team (Epic Padel-funded) moves fast in Mumbai/Bangalore before we get 25 clubs locked, the geographic moat thesis erodes. That's a 6-month race, not a 24-month one.

---

## Part 5: Honest open questions for you

You can answer these inline below each one, save the file, and send back. Or schedule 30 min and we talk.

### Q1. Clutch as a user
Have you used Clutch enough to tell me **what is genuinely good** about the product and **what is weak**? What would make you switch to a different product if it appeared in your club? What do you wish it did that it doesn't?

**Your answer:**


### Q2. The classifier approach
Of the four options I listed in §2.3 (MLP, MotionBERT, multi-modal cross-attention, self-supervised pretraining), which would you bet on for V1? Why? What would you change about the framing of the problem?

**Your answer:**


### Q3. Edge inference path
Is Mac mini M4 + CoreML a real production CV deploy path in 2026? Or do we go safely with Jetson Orin? If you'd pick Apple stack, what's the architecture you'd build?

**Your answer:**


### Q4. Apple internal angles
Without revealing anything confidential — are there public Apple frameworks (Vision, ARKit body pose, CoreML model zoo) that we should be paying attention to? Anything from VisionPro Body Pose APIs that would shortcut our pose-keypoint work?

**Your answer:**


### Q5. The moat
Honest critique: does the geopolitical + federation + coach + WhatsApp moat actually hold up under pressure, or am I rationalizing? What would you ADD to the moat thesis if you were investing?

**Your answer:**


### Q6. The build vs partner question
There's a real option: **don't compete with Clutch — try to become their India partner instead.** Sharath Kumar is in Bangalore, the company is Indian-incorporated, they likely need install/ops help in Mumbai/Delhi. If we did this, my AX distribution muscle goes into THEIR product, we get revenue share, no fundraise pressure. Less glory, less risk. **What's your take?**

**Your answer:**


### Q7. Your honest "should I do this" view
You're the closest person to me who plays this sport AND understands the tech. **Should I do this venture?** Or is it a distraction from AutomationXpert and I should send the LinkedIn DM to Sharath to find partnership / advisor / nothing? No need to be polite.

**Your answer:**


### Q8. Anything I missed
What would you have asked that I didn't?

**Your answer:**


### Q9. The advisory role
If yes — 0.5–1% advisor equity over 2-yr vest, no time commitment, monthly 30-min sync, you respond when asked specific questions (like in this doc). Acceptable structure? Want to change anything?

**Your answer:**


---

## Part 6: Reference reading (only if you want depth)

- **Strategy:** `~/Documents/padel-clone/PADEL_AI_VENTURE_PLAN.md` — full venture plan v0.2
- **Execution:** `~/Documents/padel-clone/PROJECT_REPORT.md` — operational plan with 30-day punch list
- **Technical feasibility:** `~/Documents/padel-clone/TECHNICAL_FEASIBILITY_REPORT.md` — formal feasibility report
- **OSS we'd fork:** https://github.com/Joao-M-Silva/padel_analytics (the base) + https://github.com/yastrebksv/TrackNet (ball)

---

**Thank you for reading this far.** Even a 20-min skim and 4-line response on the moat (§Q5) and "should I do this" (§Q7) would be incredibly useful. No pressure, no obligation — just your brain. Love, Papa.
