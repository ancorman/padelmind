# Padel AI Coach — Project Report (Execution Document)

**Companion to:** `PADEL_AI_VENTURE_PLAN.md` (strategy)
**This document:** what we DO, WHEN, with WHOM, for HOW MUCH
**Status:** v0.1 draft — pre-Gate 0
**Authored:** 2026-07-01
**Reading time:** 15 min (executive summary 2 min)

---

## A. Executive Summary (the 1-page for backers)

**The opportunity:** Padel is the world's fastest-growing sport (+1,026% search interest since 2004). India has 500 courts today (up from ~90 in 2023), projected to hit 5,000+ by 2036. Padel entered the 2026 Asian Games — a once-per-sport-lifecycle catalyst. No India-headquartered AI coaching platform exists. Window: 12–18 months.

**The product:** An AI coach (not a camera) that records padel matches via a single IP camera per court, runs computer vision on every shot, scores technique against an expert-coach-designed rubric, and delivers actionable improvement feedback to the player on WhatsApp within 10 minutes of match end.

**The team:**
- **Manoj Maheshwari** (CEO) — SMB SaaS operator (AutomationXpert), WhatsApp distribution expert
- **Padel Coach (CCO)** — domain authority + rubric IP (named TBD)
- **CTO / ML Co-founder** — primary target João Silva (`padel_analytics` author, EU); fallback Bangalore CV hire
- **Technical advisor**: Apple AI engineer (Manoj's son — pending discussion)

**The ask (pre-seed):** ₹2.5 Cr / $300k for 18 months runway → 25 paying clubs in 3 Indian cities, full V1 product, founding team complete, Series A-ready.

**Beachhead:** Mumbai → Pune → Bangalore. **Then:** UAE (Year 1.5), KSA + SE Asia (Year 3). **Anti-China by geography** — India + Middle East procurement-policy moat.

**Unit economics:** ₹540 COGS/court/month, ₹5,000 ASP → 89% gross margin. Same shape as Clutch.

**The moat:** Coach-designed proprietary rubric + WhatsApp-native distribution + federation-level lock-in. Not tech. Tech is commodity.

**Why now, why us:**
- Asian Games 2026 timing window
- Manoj's AX platform = built-in distribution muscle no global competitor has in India
- India has the ML talent at 1/5th Western cost
- Bank-rollable by existing angel network; no VC dependency at pre-seed

---

## B. Project Charter

### B.1 Mission
Make world-class padel coaching accessible to every Indian player via AI feedback in their pocket.

### B.2 Scope (in-scope for V1, 12 weeks)
1. Single-court hardware install + RTSP ingestion pipeline
2. Cloud video processing (player tracking, ball tracking, pose extraction, shot classification)
3. Coach-designed rubric document (IP asset)
4. Player-facing PWA (mobile-first) with skill score + shot feedback + highlight clips
5. Club dashboard (basic — court usage + recording index)
6. WhatsApp delivery of post-match insights

### B.3 Out of scope (explicitly NOT in V1)
- Native Android/iOS apps (PWA enough)
- Multi-camera 3D ball tracking
- Line-calling / officiating
- Live-streaming integration
- Gesture-trigger ("save the last point" hand wave)
- Sponsorship overlay tools
- Tournament management
- Booking integration (Hudle partnership instead)

### B.4 Success criteria (V1 ship)
- 5 pilot clubs live with hardware
- 500 matches analysed and delivered to players
- Shot classifier ≥70% top-1 accuracy
- ≥6 of 10 tester players say "I'd pay ₹300/month for this"
- Coach approves output quality on random 20-match sample

---

## C. 30-Day Punch List (Days 1–30 — start now)

### Week 1 (Days 1–7)
| Day | Task | Owner | Output |
|---|---|---|---|
| 1 | Send LinkedIn DM to Sharath Kumar (Clutch India) | Manoj | Reply OR confirmed ignore |
| 1 | Send João Silva collaboration email | Manoj (Claude drafts) | Reply OR confirmed ignore |
| 2 | Coach onboarding call — scope + comp terms | Manoj | Verbal yes/no |
| 3 | Shortlist 5 clubs in Mumbai/Pune/Bangalore for pilot pitch | Manoj | Names + contacts |
| 4 | Open conversation with son (Apple AI engineer) on advisory role | Manoj | Yes/no/maybe + comfort level |
| 5 | Register `padelmind.in` / `courtiq.ai` / `padelguru.in` (pick one) | Manoj | Domain secured |
| 6 | LLP vs Pvt Ltd decision + CA engaged for incorporation | Manoj | Entity decided |
| 7 | Week 1 review — Gate 0 status | Manoj + Claude | Pass/fail decision |

**GATE 0 (end of Week 1):** Coach committed in writing + 1 pilot club access confirmed. **Fail → pause venture, revisit in 60 days.**

### Week 2 (Days 8–14)
| Day | Task | Owner | Output |
|---|---|---|---|
| 8 | Coach delivers shot taxonomy v1 | Coach | List of 8–12 shots |
| 9 | Hardware bill of materials confirmed — Reolink quoted | Manoj | INR quote in hand |
| 10 | Pilot club informal MOU signed | Manoj + Club | 1-page MOU |
| 11 | Pre-seed deck v0.1 | Manoj + Claude | 15-slide PDF |
| 12 | Coach delivers scoring rubric v1 (1–5 stars per shot) | Coach | Rubric doc |
| 13 | Order pilot hardware (camera + Pi + switch + cabling) | Manoj | Tracking number |
| 14 | First 3 angel conversations opened | Manoj | Meetings scheduled |

### Week 3 (Days 15–21)
| Day | Task | Owner | Output |
|---|---|---|---|
| 15 | Hardware arrives; camera install begins | Manoj + electrician | Camera mounted |
| 16 | 12 court keypoints clicked + cached | Manoj + Claude | JSON saved |
| 17 | First RTSP test recording — 1 hr stream to R2 | Manoj | MP4 in cloud |
| 18 | `padel_analytics` fork — local clone + smoke test | Manoj + Claude | Pipeline runs on test video |
| 19 | First real match recorded | Manoj | 1-hr 4K MP4 |
| 20 | Process first match through full pipeline | Claude + Manoj | data.csv + visualizations |
| 21 | Coach reviews raw output, flags errors | Coach | Feedback list |

### Week 4 (Days 22–30)
| Day | Task | Owner | Output |
|---|---|---|---|
| 22 | Coach labels 100 gold-standard clips | Coach | 100 labels in CSV |
| 23 | Hire 2 labellers (₹15k/mo each) — Indeed/Naukri post | Manoj | 2 hires onboarded |
| 24 | Streamlit labelling tool built | Manoj + Claude | Tool URL |
| 25 | Bulk labelling begins (target 500 clips by Day 50) | Labellers | 50 clips/day pace |
| 26 | Pre-seed pitches to 3 angels (1st round of NO/YES) | Manoj | Term sheet conversations |
| 27 | ML co-founder decision — João Silva accepted OR fallback hire begins | Manoj | Decision logged |
| 28 | First skill-score V0 (rule-based, no ML yet) | Claude + Manoj | Demo for player |
| 29 | First player gets WhatsApp delivery of match report | Manoj | Screenshot |
| 30 | Month 1 review — go/no-go for Month 2 | Manoj + Claude | Decision logged |

**Month 1 spend target:** ≤ ₹60,000 (hardware + first labeller payroll + domain + CA fees)

---

## D. 90-Day Milestones (end of Month 3)

| Milestone | Target | Owner |
|---|---|---|
| Pilot court live & stable | 200+ matches processed | Manoj |
| Shot classifier V1 trained | ≥60% top-1 accuracy | ML lead |
| 500 clips labelled | 100% complete | Coach + labellers |
| 2nd & 3rd club onboarded (free pilot) | 2 additional courts live | Manoj |
| 25 players actively using WhatsApp PWA | weekly active = 25 | Manoj |
| Pre-seed term sheet from 1 angel/syndicate | ₹2 Cr+ committed | Manoj |
| Coach equity formalised | Signed shareholder agreement | Manoj + CA |
| ML co-founder onboarded OR senior CV hire | Equity/contract done | Manoj |

---

## E. 6-Month Deliverables (Year 1 Q2)

| Deliverable | Target |
|---|---|
| Paying clubs in India | 10 |
| Active analysed players | 1,500 |
| Shot classifier accuracy | ≥70% |
| MRR | ₹3 lakh |
| Founding team headcount | 5 (CEO, CCO coach, CTO/ML, 1 engineer, 1 BD) |
| Pre-seed closed | ₹2.5 Cr |
| Hudle partnership conversation | In motion or signed |
| First UAE feasibility visit | Completed |

---

## F. Budget Plan (₹ in lakhs)

### F.1 Month 1–3 (founder-funded bootstrap)

| Line item | INR |
|---|---|
| Pilot hardware (camera + Pi + cabling) | 0.35 |
| Domain + entity incorporation + CA | 0.30 |
| 2 labellers × 2 months | 0.60 |
| Coach engagement (Phase 1 rubric work) | 0.80 |
| Cloud (RunPod, R2, Supabase) | 0.30 |
| Travel (3 cities pilot pitches) | 0.50 |
| Miscellaneous (legal, design, tools) | 0.50 |
| **Total Month 1–3** | **3.35** |

### F.2 Month 4–6 (pre-seed deployed)

| Line item | INR |
|---|---|
| Founding salaries (Manoj + CTO + coach part-time + 1 engineer) | 18 |
| Hardware for 10 clubs | 3.5 |
| Cloud + infra | 1.0 |
| Sales/BD travel + events | 2.0 |
| Labelling ops (2 → 4 labellers) | 1.8 |
| Legal, accounting, admin | 1.5 |
| Buffer | 2.0 |
| **Total Month 4–6** | **29.8** |

### F.3 Month 7–18 (full pre-seed runway)

| Line item | INR/mo | 12-month total |
|---|---|---|
| Salaries (8-headcount avg) | 8 | 96 |
| Hardware for 25 clubs | — | 10.5 |
| Cloud + infra at scale | 1.5 | 18 |
| Sales / BD / events | 2 | 24 |
| Marketing (WhatsApp funnel, content) | 1.5 | 18 |
| Legal, finance, admin | 1 | 12 |
| Office (Bangalore base — small) | 1.5 | 18 |
| **Total Month 7–18** | | **~196** |

**Total 18-month spend: ~₹230 lakhs = ₹2.3 Cr.** Add 10% contingency = **₹2.5 Cr pre-seed ask.**

---

## G. Resource Plan

### G.1 Founding team — who & when

| Role | When | Source | Comp |
|---|---|---|---|
| **CEO / Product / Capital — Manoj** | Day 0 | — | Founder equity 40–50%, salary deferred to month 6 |
| **CCO / Coach** | Day 1–7 | Network | 8–15% equity + ₹50–80k/mo from month 4 |
| **CTO / ML co-founder** | Day 1–60 | João Silva first; Bangalore fallback | 20–30% equity + ₹1.2–1.8 lakh/mo from month 4 |
| **Founding Engineer (full-stack)** | Month 4 | Bangalore hiring | 1–2% ESOP + ₹12–18 LPA |
| **Founding BD/Sales** | Month 7 | Sports-tech background | 0.5–1% ESOP + ₹10–15 LPA + commission |

### G.2 Operating team — month 7+

| Role | Headcount | Notes |
|---|---|---|
| ML engineers | 2 | Classifier improvements + new features |
| Hardware install lead | 1 | Manages partner network |
| Customer success | 1 | Coach training + club support |
| Content / community | 1 | WhatsApp funnel + social |
| Labellers | 3–4 | ₹15k each, college students |

### G.3 Advisors target list (offer 0.25–0.5% each, 2-yr vest)

- 1× Mahesh Bhupathi (Hudle investor, racket-sports India authority)
- 1× WPT player or top-Indian padel pro
- 1× CV/ML academic (UPC-ViRVIG, IIT prof)
- 1× club operator / franchise economics expert
- 1× Indian sports-tech founder (Hudle, Playo, KheloMore CEO — if approachable)

---

## H. Technical Talent — India bench (answer to your question)

The bench in India is **deep, accessible, and ~5x cheaper than EU/US**. Hard numbers:

### H.1 India ML / CV talent supply

| Tier | What you get | INR salary | Where to source |
|---|---|---|---|
| **Senior CV/ML engineer** (4–7 yrs, pose/tracking) | Can refactor `padel_analytics`, train classifier, ship to prod | ₹35–60 LPA full-time, ₹2.5–4 LPA/mo contract | LinkedIn, Cutshort, Wellfound (formerly AngelList Talent), CV Slack communities |
| **Mid-level ML engineer** (2–4 yrs) | Train + tune classifier, integrate inference | ₹15–28 LPA | Same + IIT/IIIT/IISc placement networks |
| **CV specialist (5+ yrs)** w/ sports background | If we want pure thoroughbred | ₹50–90 LPA | Niche — try Sports Mechanics, Hawk-Eye India alumni |
| **Junior ML / fresh grad** | Bulk model-training labour, data pipelines | ₹6–12 LPA | IIT/NIT placements direct |

**Bangalore = the deepest CV pool in India.** Hyderabad and Pune are #2. NCR (Delhi) is fintech-heavy, less CV.

### H.2 Hiring channels — ranked

1. **LinkedIn paid + Wellfound** — fastest yield for senior roles
2. **IIT/IISc placement cells** — best for fresh grads, free
3. **Cutshort / Hirect** — Indian-specific platforms with CV filters
4. **Twitter/X CV community** (`#cv` `#opencv` hashtags) — for senior thoroughbreds
5. **GitHub padel/tennis CV repo contributors** — direct outreach to ArtLabss, padel_analytics, TennisCourtDetector forkers (proven interest in the problem)

### H.3 Cost comparison vs other markets

| Market | Senior CV engineer/mo (INR equivalent) | Multiplier |
|---|---|---|
| Bangalore | ₹3.5 lakh | 1.0x |
| EU (Berlin, Madrid) | ₹15–22 lakh | 4–6x |
| US (SF, NY) | ₹35–60 lakh | 10–17x |
| Shenzhen / Beijing | ₹6–10 lakh | 2–3x |

**Capital efficiency moat:** Same ML quality at 1/4 of EU price, 1/10 of US. This is real and matters for Series A multiples.

### H.4 Verdict on "are we covered on technical?"

**Yes — provided we hire correctly.** Three rules:
1. **Don't compromise on the lead CV/ML hire** (founding role). Pay for excellence here — every junior follows.
2. **Lean on the open-source maintainer network first** (João, ArtLabss, yastrebksv, UPC-ViRVIG) — they have the specific domain experience that takes a generic CV hire 6 months to build
3. **Build remote-first; don't insist on Bangalore-office.** Best CV folks in India are remote-mode already.

---

## I. Procurement & Vendor List (have these phone numbers handy)

### I.1 Hardware

| Item | Vendor | Lead time | INR |
|---|---|---|---|
| Reolink RLC-823A 16x | Amazon India / Reolink India distributor | 5–7 days | 12,000 |
| Hikvision DS-2CD2T87G2-LU (alt premium) | Authorised Hikvision dealer (Lamington Road Mumbai / SP Road Bangalore) | 7–10 days | 15,000–22,000 |
| Raspberry Pi 5 8GB | Robu.in / SB Components India | 2–3 days | 8,500 |
| 1TB NVMe SSD | Crucial / Samsung via Amazon | 2 days | 5,500 |
| PoE switch TP-Link TL-SG1005P | Amazon | 2 days | 3,000 |
| Cat6 cable + connectors | Local | Same day | 1,500 |
| Camera mount bracket + IP66 box | Local CCTV shop | 2 days | 1,500 |

### I.2 Cloud + SaaS

| Service | Vendor | Plan | INR/mo |
|---|---|---|---|
| GPU inference | RunPod (RTX 3090) | Pay-per-second | ~50,000 at 5-club scale |
| Object storage | Cloudflare R2 | Pay-per-use | 5,000 at 5-club scale |
| Database + Auth + Realtime | Supabase | Pro plan | 2,500 |
| PWA hosting | Cloudflare Pages | Free | 0 |
| WhatsApp delivery | AX router (own infra) | Internal | 0 |
| Domain | GoDaddy India / Namecheap | Annual | 1,200/yr |
| Monitoring | Sentry + PostHog | Free tier | 0 initially |

### I.3 Professional services

| Service | Vendor type | Estimated cost |
|---|---|---|
| Company incorporation (Pvt Ltd) | CA firm in Bangalore | ₹25,000 one-time |
| Trademark filing (brand name) | IP lawyer | ₹15,000 + ₹4,500 govt fees |
| Founder equity / vesting agreements | Startup lawyer | ₹50,000–80,000 one-time |
| Coach engagement letter + IP assignment | Same | Included above |

---

## J. Risk Register (with owner + mitigation)

| # | Risk | Likelihood | Severity | Owner | Mitigation |
|---|---|---|---|---|---|
| R1 | Shot classifier accuracy plateaus | Med | High | CTO | Multi-coach labels + dataset expansion + ensemble; contractor escalation if stuck >Week 8 |
| R2 | Hudle builds analytics OR signs Clutch | Med | V.High | CEO | Partnership conversation before Month 3; offer revenue share |
| R3 | Chinese competitor enters India | Low (geopolitics) | High | CEO | Monitor watch list; lean federation lock-in |
| R4 | Coach overcommits, under-delivers | Med | High | CEO | Milestone-based payment, not pure equity |
| R5 | Manoj overstretched (AX is day-job) | High | High | CEO | Founding engineer hired by Month 6 to take ops load; honest hour-budgeting |
| R6 | Hardware reliability fails in monsoon/heat | Med | Med | Hardware ops lead | IP66 cameras only; thermal testing; spare-on-shelf for every club |
| R7 | Pre-seed doesn't close by Month 6 | Med | High | CEO | Bridge of ₹50L from 3–5 angels lined up early; SAFE structure |
| R8 | Players don't share/talk about feedback | Med | Med | Product | WhatsApp-shareable screenshots from V1; influencer seeding |
| R9 | Hardware ops can't scale beyond 10 clubs | Med | Med | Hardware lead | Train partner network from Month 9 |
| R10 | Sharath Kumar / Epic Padel aggressive lock | Med | High | CEO | LinkedIn DM this week; gauge competition vs partnership intent |

---

## K. Governance & Review Cadence

### K.1 Weekly
- **Monday 9am:** Founders sync (30 min). Review previous week's milestones. Lock current week priorities.
- **Friday 6pm:** Metrics review — clubs live, matches analysed, classifier accuracy, MRR, runway months.

### K.2 Monthly
- **First Monday:** Board / advisor monthly update (1-page).
- **Mid-month:** China watch list review (per Section 4.6 of venture plan).
- **End of month:** Budget burn vs plan. Re-forecast if >10% off.

### K.3 Decision gates
Use the 7-gate model from venture plan §13. **Gate failures = automatic Friday emergency review, not next-Monday.**

---

## L. Backer Pitch — Talking Points (use these in conversations)

### L.1 The hook (45 seconds)
"Padel is the world's fastest-growing sport — search interest up 1,000% since 2020. India just hit 500 courts, projected 5,000+ by 2036, growing 70% a year. Padel enters the Asian Games in 2026. No India-headquartered AI coaching platform exists. We're building it — coach-led, WhatsApp-native, defensible by geography against Chinese tech. Pre-seed of ₹2.5 Cr for 18 months runway, target 25 paying clubs and Series A-ready by month 18."

### L.2 The differentiation (when they ask "why won't Clutch / China kill you?")
"Three moats Chinese tech can't easily replicate in India: (1) procurement-policy wall — Indian clubs face geopolitical risk choosing Chinese SaaS, same reason TikTok is banned. (2) A WPT-trained padel coach as co-founder, designing the technique-scoring rubric — that's the data moat, not the code. (3) WhatsApp-native distribution at SMB-club scale — I run AutomationXpert which has shipped this exact muscle into 250+ Indian businesses. Clutch sells direct in Europe; their India arm is one team in Bangalore. We can move faster on home turf."

### L.3 The capital efficiency (when they ask burn rate)
"₹230 lakh over 18 months. We're founder-funded for the first 3 months to hit 5 clubs and a working classifier. Then ₹2.5 Cr pre-seed gets us to 25 clubs, ₹50L MRR, founding team complete. India ML talent is 1/4 of European cost — our gross margin profile (89%) is identical to Clutch's, but our CAC is half theirs because of WhatsApp distribution. Series A target ₹15–20 Cr at Month 18 for India scale + UAE entry."

### L.4 The exit story (when they ask outcome)
"Three credible paths: (a) Acquisition by Epic Padel or a global rollup — they already raised $10M to consolidate. We're the India play they'd buy. (b) Strategic acquirer in Indian sports — Hudle, Playo, KheloMore, or a corporate (Bajaj Sports, Decathlon India) — buying for the AI capability. (c) Continued growth path through Series A/B if Asia thesis plays out — $50–100M Series B in 4 years is achievable at the right multiples on padel growth."

---

## M. Open Decisions (must close before raising)

| # | Decision | Status |
|---|---|---|
| D1 | Brand name + domain | Open |
| D2 | LLP vs Pvt Ltd entity | Open |
| D3 | Coach identity + signed terms | Open |
| D4 | CTO/ML co-founder — João or Bangalore hire | Open |
| D5 | Pilot club identity (Mumbai/Pune/Bangalore) | Open |
| D6 | Manoj's son advisory/role decision | Open |
| D7 | Pan-Asia vs Anti-China geographic strategy (per plan §4.5) | Open |
| D8 | Hudle partnership approach — competitive or collaborative? | Open |
| D9 | First angel commit (₹50L bridge) | Open |
| D10 | Working hour commitment (Manoj's weekly floor) | Open |

---

## N. Change Log

| Date | Author | Change |
|---|---|---|
| 2026-07-01 | Manoj + Claude | v0.1 — initial execution-ready Project Report |

---

*Companion to PADEL_AI_VENTURE_PLAN.md (strategy). This document is execution-focused — what we do, when, with whom, for how much. Update here for any operational state change. Memory pointer in `MEMORY.md`.*
