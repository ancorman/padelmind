# Team Brief — The Padel AI Opportunity

## 1. Executive Summary

Padel is India's fastest-growing racket sport. Mumbai alone has **~44 padel venues and ~80–95 courts** live today, on track for **~140 courts by mid-2027**. Hudle's platform data shows **505 active players per court in Mumbai** — nearly double the national average — and weekend availability is chronically over-subscribed.

Despite this heat, **no AI camera / match-analytics product is live at any Mumbai club today**. The three EU incumbents (Matchlytics in Portugal, SportAI/Padelytics in Norway, SPASH in Spain, plus GameCam globally) have zero India installs. That whitespace is real, and it is closing — SportAI's post-acquisition mandate explicitly names "emerging markets," which puts us on a **12–18 month clock** before an incumbent lands here via a distributor.

Our first anchor is **NSCI (Worli, Mumbai)** — proposal live, awaiting reply — with a 90-day training phase followed by a 2-year commercial phase (30% gross revenue share to the club). NSCI is the credential; the money engine is the network — Padel Park's 5-venue chain, Courtside Worli, and the heritage clubs (Bombay Gymkhana, CCI) that follow the NSCI precedent.

This document is what the founding team (Manoj, Aayush, Tanisha) needs to align on before we spend the next 60 days building. A companion document ("Scope Reset — Technical Deltas") follows separately.

---

## 2. The Local Infrastructure

### 2.1 Venue census — Mumbai

Consolidated from Hudle, KheloMore, Padel Park, Courtside, and press coverage. We identified **~38 commercial padel venues** plus **6 heritage / members clubs** that have added padel.

**Commercial venues (top 15 by visibility, 38 total):**

| # | Venue | Area | Notes |
|---|---|---|---|
| 1 | Padel Park — Malabar Hill | Priyadarshini Park | Flagship |
| 2 | Padel Park — Worli | Lala Lajpatrai Marg | Flagship |
| 3 | Padel Park — Cooperage Stadium | Colaba | |
| 4 | Padel Park — Bandra (KC Marg) | Bandra | |
| 5 | Padel Park — Andheri (Celebrations SC) | Lokhandwala | |
| 6 | Courtside Padel Social Club | Atria Mall rooftop, Worli | 3 padel + 1 pickleball, invite-only |
| 7 | SkyPadel @ Sahara Star | Vile Parle | Indoor |
| 8 | Padel Project | Supreme Business Park, Powai | Indoor |
| 9 | Padel 360 | Worli | |
| 10 | Ace Padel Bandra / Ace Padel Andheri | Bandra W / Andheri E | Two sites |
| 11 | 7Padel × Super Sports Park | Mulund | Premium tier |
| 12 | The CourtRoom (R Odeon) | Ghatkopar | Rooftop mall |
| 13 | BandrArcade @ Taj Lands End | Bandra | Rooftop |
| 14 | Serve Society Kohinoor | Dadar W | |
| 15 | Racquet Republic @ Sacred Heart | Khar / Santa Cruz W | |

Plus ~23 more mid- and budget-tier venues across Andheri, Powai, Ghatkopar, Bhandup, Mulund, Goregaon, Borivali, and Navi Mumbai.

**Heritage members clubs that have added padel:**

| Club | Location | Notes |
|---|---|---|
| **NSCI Padel Club** | Worli | **Our Client #0.** 2 courts, members-only. |
| Cricket Club of India (CCI) | Churchgate | Padel live on Hudle |
| Willingdon Sports Club | Maali Khata | Padel bookable |
| Bombay Gymkhana | Fort | Padel court unveiled 2026 |
| Wodehouse Gymkhana | Colaba | Padel live |
| Breach Candy Swimming Bath Trust | Breach Candy | Padel + pickleball, members-only |

### 2.2 Tier stratification

| Tier | Rate/hr | Venues | Fit for paid AI product |
|---|---|---|---|
| **Budget** | ₹400–1,000 | Urban Sports network, TSG, PickPad, Radio Club, Padelverse | Low — hardware-included freemium at best |
| **Mid** | ₹1,500–1,800 | Ace Padel, Serve Society, Padel 360, BandrArcade | Good — main paid segment |
| **Premium** | ₹2,500–3,000+ | Padel Project Powai, 7Padel × Super, Courtside Worli | High — brand-conscious, low price sensitivity |

Heritage members clubs (NSCI, CCI, Willingdon, Bombay Gymkhana) run ₹10–₹400 subsidised member rates but hold the highest-value roster in the city.

---

## 3. Current Statistics

### 3.1 Growth signal

- **India padel market**: USD 25–30M today → USD 250–300M projected by 2036 (Hudle Report / MediaBrief).
- **Player base**: 100× growth in 3 years → ~1 lakh active players.
- **National courts**: 48 new venues opened Jan–Apr 2026 — annualised ~70% court growth.
- **Investor money**: JSW Sports invested in Padel Park (Aug 2024). A federation-analytics startup raised ₹28 Cr Pre-Series A May 2024 (Centre Court Capital + PeerCapital).

### 3.2 Absorption / demand pressure

| Metric | Mumbai | Delhi NCR | India avg |
|---|---|---|---|
| **Active players / court** | **505** | 636 | 305 |
| Avg session length | 1.75 hrs | 1.75 hrs | 1.75 hrs (longest of any Hudle sport) |
| 12-month retention | 55% | 55% | 55% |
| Games per user / year | 9.2 | 9.2 | +73% YoY |

Press language across coverage: *"jam-packed like sardines every weekend"*, *"book 5–7 days in advance"*, *"waitlists are the new normal for weekend nights."*

### 3.3 Padel Park financial anchor (only Indian padel P&L in the public domain)

From Inc42 disclosure — Padel Park FY24:

| Line | Value |
|---|---|
| **Revenue** | ₹2.5 Cr |
| EBITDA | Positive |
| MoM revenue growth | 20% |
| Court bookings share | 60% |
| Events & tournaments share | **30%** |
| Training / coaching share | 10% |
| Monthly footfall per court | ~500 users |
| Booking lead time | 2–3 weeks in advance (fully booked) |
| Coach training pack | ₹8,000–9,000/month/player |

**Reads**: revenue per court ≈ **₹2 lakh/month** at Padel Park. Events + coaching alone = 40% of revenue — this is the layer we can attack with an AI product without disturbing the club's court-rental base.

---

## 4. The Opportunity

### 4.1 GameCam as the benchmark

GameCam (EU, 250+ clubs claimed) pitches a **€900–1,200/court/month** revenue uplift to clubs via analytics subscriptions + AI-court booking premiums. Translated at PPP-adjusted India pricing, that same envelope collapses to **₹65–100K/court/month gross** with a different mix — India can approach the number, but the levers invert: highlights + coaching + tournaments carry more weight; court-booking premium carries less.

### 4.2 What makes India uniquely attractive vs the EU

1. **Zero incumbent to displace.** No GameCam, no Matchlytics, no PlaySight, no SPASH live in Mumbai. Whiteboard, not a war.
2. **Hopper culture is the norm.** Hudle's whole model is cross-venue booking; players don't stay loyal to one club. This *forces* a player-following network as the product shape — exactly what a new entrant should build, but a legacy club-side product can't.
3. **Demographic density**: padel in Mumbai skews ₹12K+/mo discretionary sport spend, 25–45, urban, HNI-adjacent. One brand deal with Head / Bullpadel / Wilson / Red Bull / HSBC pays for a year of ops.
4. **Coaching underserved**: no Indian padel-coach-discovery layer exists. Padel Park's academy is the closest, but it's their own coaches, their own venues.
5. **NSCI as credential**: once "as used at NSCI" is on the pitch deck, Bombay Gymkhana, CCI, and Willingdon close on governance-envy alone.

### 4.3 The one non-obvious insight

> **Players hop. The club doesn't own the player — the peer group does.**
> A camera at a single venue tracks half a player's games. A network of 8–10 venues tracks nearly all of them. The product only becomes valuable at the network level. Which is exactly why an EU incumbent selling club-by-club into India is slower than a local team building the network first.

---

## 5. Economics Playbook

### 5.1 Player affordability today

Court-time cost per player per session (rate ÷ 4 players × 1.75 hrs):

| Tier | Court/hr | Per-player/session |
|---|---|---|
| Budget | ₹600–1,000 | ₹260–440 |
| Mid | ₹1,500–1,800 | ₹655–790 |
| Premium | ₹2,500–3,000 | ₹1,095–1,315 |

A committed player also spends ₹5–10K/mo on coaching + racquets + apparel.

### 5.2 Frequency segmentation

Only the **Engaged + Serious + Obsessed** segments (roughly the top 15–25% of a club's roster) will pay for analytics.

| Segment | Sessions / wk | Court spend / mo (premium) | Notes |
|---|---|---|---|
| Curious | 0.5 | ₹2,000–2,600 | Try-once corporates, tourists |
| Casual regular | 1 | ₹4,400–5,200 | Weekend social players |
| **Engaged** | **2** | **₹8,800–13,000** | Core target — improvers, tournament-curious |
| **Serious** | **3–4** | **₹13,000–20,000+** | Ex-tennis converts, ranking-conscious |
| **Obsessed** | **5+** | **₹22,000+** | Coach candidates, brand ambassadors |

### 5.3 Subscription tier structure (proposed)

Rule of thumb: 8–12% of primary-activity spend goes to enrichment. Cross-checked against Cult Sport (₹499–999), Cult Pass (₹1,499–2,499), Trackman/Arccos India (₹1,500–2,500), and the international padel benchmark (GameCam player app ~₹950–1,400).

| Tier | Price / mo | Includes | Target |
|---|---|---|---|
| **Free** | ₹0 | 1 highlight/mo, basic score | Curious/Casual — conversion funnel |
| **Pro** | ₹499 | Unlimited highlights, heatmap, shot mix, spider chart | Engaged — bulk of paid base |
| **Pro+** | ₹999 | Everything + city ranking + opponent scout + coach-shareable link | Serious |
| **Elite / Coached** | ₹2,499 | Personal coach seat, drill prescriptions, monthly review call | Obsessed + parent-of-junior |

Blended target ARPU: **~₹650/mo/paying player.** À-la-carte per-match unlock at ₹149 as the entry ramp.

### 5.4 Revenue mix at maturity (Y2–3, ~40-court network)

| Stream | Share | Notes |
|---|---|---|
| Player subscriptions | 30% | Recurring, high margin |
| Per-match unlocks | 10% | Casual funnel |
| **Booking take rate** | 20% | 5–7% commission on network bookings |
| **Tournament / ladder fees** | 15% | Padel Park proves 30% for court-only players — we're leaner |
| **Coach discovery** | 10% | 15% take × ₹8–9K/mo × ~2,000 coached players |
| **Brand sponsorship** | 15% | Optionality kicker — one deal / quarter / brand |

Blended ARPU per active paying player pushes to **₹1,100–1,300/mo** when marketplace layers activate — nearly 2× subscription-only.

### 5.5 Unit economics — Year 1 Mumbai (indicative)

| Line | Estimate |
|---|---|
| Venues live end-of-Y1 | 8–9 |
| Courts live | 16–18 |
| Player pool (deduped for hopping) | ~5,500 unique |
| Paid conversion | 15% |
| Paying subs | ~825 |
| Blended ARPU | ₹650 |
| Subscription revenue / yr | ~₹65 L |
| Per-match unlocks | +40% of sub revenue |
| **Gross topline (subs + unlocks)** | **₹90 L – 1 Cr** |
| Less 30% club rev-share (NSCI + peers) | ~₹27–30 L |
| Less hardware amortisation (18 courts × ₹1.2L rig ÷ 24 mo) | ~₹13 L |
| Less cloud + team | ~₹35–45 L |
| **Net Y1** | **~break-even to small loss** |

Year 2 (Delhi NCR replication + coaching upsell + first sponsorship deal) is where the model flips to material profit.

---

## 6. Competitive Landscape

**Confirmed as of 2026-07-04:**

| Player | HQ | Product | India presence | Threat level |
|---|---|---|---|---|
| **Matchlytics** (matchlytics.ai) — João Silva | Portugal | Single 180° wide-angle MatchCam + AI + TieSports booking. 7 clubs live. Early. | None | **Direct** — same architecture, different geography |
| **SportAI + Padelytics** (sportai.com) | Norway (acquired 2026) | API + CV infrastructure. Integrations: MATCHi, Save My Play, Rackety. Stated focus: "EU, NA, emerging markets" | None yet | **High** — best-funded, stated intent |
| **SPASH Match Analyzer** (spash.com) | Spain | ~20 stats within minutes of match end, no sensors | None | Medium |
| **GameCam / GAMETRAQ** (gamecam.io) | EU | Ceiling-mounted 4K/90fps, on-device 12 TOPS AI. 250+ clubs. €900–1,200/court/mo revenue claim | None | Low near-term (hardware complexity), watch |
| **Padex** (github.com/rondo-labs/Padex) | Madrid (solo dev) | OSS pipeline — only production-shaped padel CV outside João's. 16★, 61 commits solo. MIT-licensed. | Fork target | Not a competitor — **a partner** |
| **Padelize, Padelplay** | EU | Sensor + app | None | Low |

**Strategic reads:**

- **The window before an EU incumbent enters India is 12–18 months.** SportAI's post-acquisition mandate explicitly names emerging markets. India will not stay whitespace forever.
- **João Silva (Matchlytics) is now a direct competitor**, not a potential collaborator. The Jul 3 outreach is dead — no follow-up. We do not reveal our India plan to any Matchlytics channel.
- **Padex (Dreaner) is the safest OSS foundation** — MIT-licensed, purpose-built for padel, solo dev likely responsive to a paid pilot.
- **JSW Sports has money in Padel Park.** Two possibilities: they become our best distribution partner (5 → 200 sites), or they build the AI layer in-house. Which one depends on who calls whom first, and how ready our proof is when the call happens.

---

## 7. Tie-Up Prospects

### 7.1 Distribution & venue partners (India)

| Partner | Path | Signal | First ask |
|---|---|---|---|
| **NSCI (Worli)** | Client #0 — proposal live | Awaiting reply. 90-day free training + 2-yr commercial, 30% gross share. | Follow up 2026-07-08 if no reply. Credential secured on signing. |
| **Padel Park network** | JSW-backed. 5 Mumbai sites + national franchise pipeline of 200 courts | Owner runs Indian Padel Academy → coaching-tool angle | Approach post-NSCI-live: "we've built what your JSW deck probably promised, want to integrate before someone asks you to build it." |
| **Courtside Padel Social Club (Worli)** | Invite-only lifestyle brand | Wellness-brand DNA, has an app | Positioning: member-only Insta-clip feature reinforcing exclusivity |
| **Bombay Gymkhana** | Heritage members club, unveiled padel 2026 | Committee-buy governance identical to NSCI | Post-NSCI, sell prestige: "the AI system NSCI is running" |
| **CCI (Cricket Club of India)** | Padel live | Members-only, ₹200+ subsidised | Same governance pitch as Bombay Gym |
| **Willingdon Sports Club** | Padel bookable | Same archetype | Follow-on after Bombay Gym/CCI |
| **Ace Padel Bandra + Andheri** | 2 mid-tier commercial sites | Bandra + Andheri E footprint | Mid-tier pilot after network alpha |
| **7Padel × Super Sports Park (Mulund)** | Premium tier | ₹3,000/hr — willing to pay for premium | Sell hardware-free installation in exchange for revenue share |

### 7.2 Platform integrations (India)

| Partner | Value | Ask |
|---|---|---|
| **Hudle** | India's dominant sports-booking platform (Mumbai + Delhi + 18 cities) — the discovery/booking layer everyone hops through | Deep-link booking integration + Hudle-account SSO for PadelMind ID |
| **KheloMore** | Secondary booking aggregator | Same integration pattern; lower priority |
| **JSW Sports** | Capital + Padel Park distribution | Board observer seat in exchange for 5-site distribution commit? |

### 7.3 White-label / licensing paths (fallback)

If we choose not to build our own CV stack, the three real licensing options:

| Principal | What we get | What we give | Fit |
|---|---|---|---|
| **SportAI (post-Padelytics)** | Best-funded, most complete stack, ambitious | 25–40% rev-share, brand co-existence, India country-manager style deal | Best strategic fit — they've said "emerging markets"; we're the emerging market they haven't landed in yet |
| **SPASH** | Working product, Spanish team, quiet | Similar rev-share | Backup |
| **Matchlytics** | João's stack, closest to our thesis | Awkward — competitor + no India intent visible | Skip. Do not approach. |

### 7.4 Brand / sponsor prospects (Y1–Y2)

| Sponsor | Fit | Product | Approach |
|---|---|---|---|
| Head, Bullpadel, Wilson | Padel-native brands | Racquet + gear affiliate | Post-network-alpha |
| Red Bull | Aspirational sports lifestyle | Tournament title sponsor | Post-city-ranking-launch |
| HSBC / Standard Chartered | Padel demographic matches private-banking segment | Membership tier co-brand | Post-heritage-club signings |
| Local sportswear (Boat, Bewakoof, Bombay Shirt Co.) | Match-day apparel | Court-side overlays | Y2 city-ranking sponsor |

---

## 8. Technical Partner Shortlist

Sourced from GitHub commit graph (stargazers + forkers of Joao-M-Silva/padel_analytics and adjacent racket-sport CV repos), academic authors, and India-diaspora CV engineers. LinkedIn login-wall made direct search low-yield; GitHub was denser signal.

### 8.1 Priority list — reach out this week

| # | Candidate | Role / signal | Ask | Contact channel |
|---|---|---|---|---|
| 1 | **"Dreaner" / Rondo Labs** — author of Padex | Only production-shaped padel-CV OSS besides João's. Solo builder, Madrid, founder DNA. MIT-licensed. | Paid pilot on NSCI courts + equity if it works | github.com/rondo-labs/Padex → GitHub profile → email |
| 2 | **Amey Narwadkar** | Heidelberg Masters (India diaspora). Author of Tennis-Analysis-System (88★). Graduating soon. Tennis-CV is 80% padel-portable. | 8-week paid port from tennis to padel + founding-CV-engineer offer post-Masters, Mumbai relocation | github.com/ameynarwadkar |
| 3 | **Michele Vitale** | Whitehall AI Reply consultant (Rome). Author of ball_tracking_padel — cleanest padel ball tracker on GitHub. | 4 hrs/mo advisor retainer + small equity slice. Doesn't leave day job. | github.com/michele98 |
| 4 | **Anil John** | Indian, starred `Joao-M-Silva/padel_analytics` — one of only ~5 Indians to do so. Almost certainly a padel player. | 30-min coffee. Softest ask, highest hit rate. | github.com/anilujohn |

### 8.2 Second wave — India-based padel-CV stargazers (rare signal)

| Candidate | Signal | Approach |
|---|---|---|
| **Gaurav (Gaurav23V)** — gaurav23v.app | India, full-stack + ML, 86 repos. Padel_analytics starrer. | Coffee ask + build-partner pitch |
| **Subham Agrawal (Neurabit)** — neurabitsolution.com | Runs a CV consultancy in India. Padel_analytics starrer. | Paid POC / delivery partner scope |
| **Akash "sky-akash"** | India, 41 repos, padel_analytics starrer | Coffee + early-hire pitch |

### 8.3 Bench — keep warm

- **Muhammad Moin Faisal** (Lahore) — 929 GitHub followers, tennis_analysis, prolific CV tutorials.
- **Harsh Tomar** (@HarshTomar1234, India) — Tennis-Vision 38★, 71 repos across CV/GenAI/MLOps.
- **Nikhil Devanathan (@nikhil-dev)** — `hawkeye` cricket + tennis ball tracking (54★). India-relevant crossover.
- **Fernando Navales Merino** (Granada) — university, padel research hub, potential PhD sourcing channel.
- **Kishore Patlolla (@kvnptl)** — India-born, Germany robotics/CV. Not padel-native but production muscle.
- **TrackNet lineage authors** (Chang-Chia-Chi, alenzenx, yastrebksv, mareksubocz) — racket-sport ball tracking. Twitter DM sweep for Y2 hires.

### 8.4 Outreach playbook

Each candidate gets a different tone — no template:

- **Dreaner / Padex**: *"Padex is the only production-shaped padel CV pipeline outside of João's. We've locked NSCI Mumbai as our first venue with a 40-court roadmap. Ready to run a paid pilot. Can we cut you a check to deploy Padex on our first two courts, and talk equity if it works?"*
- **Amey**: *"Your YOLO + court-line + ball-speed stack is 80% of what padel needs. NSCI Mumbai is our anchor, 40-court roadmap. Open to an 8-week paid port from tennis to padel, with a founding CV engineer offer in Mumbai after your Masters?"*
- **Michele**: *"Your `ball_tracking_padel` is the cleanest padel ball tracker on GitHub. Not asking you to leave Reply — asking for 4 hrs/month at an advisor rate plus a small equity slice, and access to your dataset annotations under a mutual licence. Interested?"*
- **Anil John**: *"There are five Indians who starred `Joao-M-Silva/padel_analytics`. You're one. I'm another. Coffee or Zoom this week?"*

---

## 9. What This Document Doesn't Cover

A companion document — **Scope Reset: Technical Deltas & Commercial Launch Timeline** — is being prepared separately. It addresses:

- Hardware architecture changes (single 180° wide-angle vs multi-camera ceiling rig)
- CV pipeline decision (Padex fork vs licensed stack vs build-from-scratch)
- Product must-haves that shifted from Y2 to Day-1 (cross-venue player ID, Hudle integration, rally detection, gesture-tag highlights)
- Revised commercial-launch milestone: Day 91 NSCI (proof) → Day 180 network commercial launch
- The three strategic paths (build our own · license & wrap · become the master franchisee) with honest tradeoffs and cost envelopes

Read this brief first for alignment on *why* and *where*. Read the Scope Reset next for alignment on *how* and *when*.

---

## 10. Immediate Actions (this week)

| # | Action | Owner | Deadline |
|---|---|---|---|
| 1 | Follow up NSCI committee if no reply | Manoj | 2026-07-08 |
| 2 | Email Dreaner (Padex) — paid pilot pitch | Manoj + Aayush | 2026-07-06 |
| 3 | Email Amey Narwadkar — founding CV engineer offer | Manoj | 2026-07-06 |
| 4 | Email Michele Vitale — advisor retainer | Manoj | 2026-07-06 |
| 5 | Email Anil John + 3 other Indian padel_analytics stargazers — soft coffee ask | Manoj / Tanisha | 2026-07-07 |
| 6 | Do NOT contact João Silva — competitor, not collaborator | — | Ongoing |
| 7 | Team review of Scope Reset companion doc | All three | 2026-07-05 |
| 8 | Decision meeting: Path A (build) vs B (license) vs C (franchise) | All three | 2026-07-10 |
