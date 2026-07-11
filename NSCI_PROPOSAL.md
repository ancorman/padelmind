# An AI Vision-Based Player Grading and Improvement System for the NSCI Padel Courts
## A Proposal to the NSCI Padel Committee — 90-Day Training Phase at No Cost, Followed by a 2-Year Commercial Phase with a 30% Revenue Share to NSCI

**To:** The Padel Committee, National Sports Club of India, Worli, Mumbai
**From:** Anchor Fastener Mfg Corporation
&nbsp;&nbsp;&nbsp;&nbsp;318/319, Tardeo Aircon Market, Tardeo, Mumbai, Maharashtra – 400034, India
&nbsp;&nbsp;&nbsp;&nbsp;GSTIN 27ACAPM7018E1ZV
&nbsp;&nbsp;&nbsp;&nbsp;For its product line **PadelMind by AutomationXpert**
&nbsp;&nbsp;&nbsp;&nbsp;Represented by Manoj Maheshwari, Director (and Member, NSCI)
**Date:** 2026-07-02
**Reading time:** 5 minutes

---

## The proposal in one paragraph

Anchor Fastener Mfg Corporation, through its product line **PadelMind by AutomationXpert**, would like the committee's permission to install — entirely at our own cost — video capture equipment on **both NSCI padel courts** for a **90-day data-capture and model-training period**, followed by a **2-year commercial phase** during which members can pay to use the system and the club earns a **30% share of all revenue** from NSCI members. During the 90-day training phase, **no service is being offered to members** — players simply play as usual; no member action is required and no member deliverable is provided.

**No audio is captured. No footage is shared with any third party. No feed is made available to any player, staff member, or outside person during the trial.** The data captured during the training phase is used solely internally, for the purpose of training the software.

The only ask on the club is one covered, weather-protected electrical point near the courts to house the internet modem. Everything else — cameras, cabling, modem, cellular data, cloud processing, support, and all operating expenses of the commercial phase — is fully borne by us.

Both the training phase and the commercial framework are being placed before the committee together in this single proposal, so the club has full clarity today on the entire arrangement — training terms, commercial terms, tenure, and revenue share.

---

## Why we are bringing this to NSCI first

I am a member and an active padel player at the club. Professionally I run **Anchor Fastener Mfg Corporation** (Mumbai, GSTIN 27ACAPM7018E1ZV) and, under its umbrella, **AutomationXpert** — an established SaaS platform serving Indian small businesses. **PadelMind by AutomationXpert** is a new product line we are building under the same corporate roof, focused on AI-assisted racket-sports coaching.

The honest ask is this: NSCI has two well-utilised padel courts, an engaged member base, and the atmosphere to run a real-world observation and training period without disruption. If the committee grants permission, we can develop, refine, and validate the software on Indian match play — and if it works, NSCI will have been the club where a genuinely Indian sports-technology capability was built.

During the 90-day training phase there is no cost to the club and no obligation of any kind. From Day 91, the club begins earning a 30% share of gross revenue from NSCI members using the system, on the framework detailed later in this document.

---

## Trial terms — 90 days

| Item | Detail |
|---|---|
| **Duration** | 90 days from the date of installation |
| **Courts covered** | Both padel courts |
| **Purpose** | Data capture and model training only. No service is offered to members during this phase. |
| **Cost to NSCI** | Zero. No installation charge, no fee, no consumable cost. |
| **Impact on members** | None. Members play as usual. Nothing to sign up for, nothing to opt into, no action required. |
| **Audio** | Not captured. Video only. |
| **Data usage** | Solely internal, for training the software. Not shared with any third party. Not made available to members or club staff during the trial. |
| **Commitment during training phase** | None. The committee may terminate the training phase at any point with 7 days' written notice. |
| **Removal on early termination** | If the training phase is terminated during the 90 days, all equipment removed at our cost within 7 days of notice, with no residual obligation on the club. |
| **After Day 90** | Automatic transition to the 2-year commercial phase on the terms set out in the "What happens after Day 90" section below. |
| **Transparency** | A small informational notice will be posted at the courts explaining that AI research video capture is in progress for internal software-training purposes only. |
| **Per-session opt-out** | Any member who prefers not to be recorded can pause recording on that court instantly — either by pressing a clearly labelled courtside pause switch, or by asking club staff (see next section). |

---

## What NSCI needs to provide

**One thing — one electrical point.**

The club needs to provide:

- **One 230V / 15A power outlet** at a location of the club's choosing, near or overlooking the padel courts
- The location must be **covered from rain** (under a canopy, inside a service niche, or in an existing covered structure)
- The location must be **reasonably protected from casual tampering** — ideally locked, or in a staff-access-only area, or inside a weatherproof service cabinet the club allows us to mount
- **No club internet is required.** We will bring our own dedicated internet connection (4G/5G cellular modem with our own SIM and paid data plan) at our own cost. The modem lives at this power point.

That is the total ask on the club. No court downtime for installation beyond a 2-hour window on a mutually agreed morning. No staff involvement thereafter. No maintenance obligation.

---

## Member privacy — how a player can opt out of being recorded

We recognise that even though no service is being offered to members and no footage leaves our system, some players may simply prefer not to be recorded on a given day. Two mechanisms will be in place from Day 1 to give every player direct, no-friction control.

**1. A courtside pause switch — one per court.**
A small, clearly labelled push-button (a commodity IP-connected smart switch, ~10 cm across, weather-protected, LED-lit) will be installed at a visible location on each padel court, next to the score area. The convention is:

- **Green LED** = recording is active
- **Red LED** = recording is paused

Pressing the button pauses recording on that court immediately for the next **2 hours** (adjustable). The LED turns red for the whole pause window. Recording auto-resumes after the 2 hours, unless the button is pressed again. Any member arriving on court can look at the LED before they start playing to know the current state, and press the button if they prefer.

**2. A request to club staff (backup channel).**
A member who prefers can simply tell the club staff that they do not wish to be recorded. Staff send a one-line WhatsApp message to a dedicated number monitored by our team, and we pause the relevant court from our end within seconds.

**3. Courtside signage.**
A small, discreet notice at each court will state — in one line — that AI research video capture is in progress, that no audio is captured, that footage is not shared, and how to pause recording (button or ask staff). This ensures every player, including first-time visitors, sees the mechanism before playing.

**Hardware and software:**

| Component | Detail |
|---|---|
| Pause switch | One commodity Zigbee / IP smart button per court (approx. ₹1,500 each), wall-mounted, LED-lit, weather-protected. Supplied and paid for by us. |
| Management software | Small state-machine service running on our edge computer. Reads button presses and WhatsApp pause requests; toggles the corresponding camera's recording state; auto-resumes on timer expiry. All state changes logged with timestamp for audit. |
| Audit trail | On request from the committee at any point during the trial, we can produce a log showing exactly when each court was paused, by which channel (button or staff), and for how long. This lets the committee independently verify that opt-outs are being honoured. |
| Operational burden on the club | None. We install, monitor, respond, and audit. Club staff only need to send a one-line WhatsApp when a member asks — no training, no app, no login. |

This mechanism is designed to be **understandable by any member in five seconds** (look at the LED, press if you want to pause), **auditable by the committee at any time**, and **operationally silent for the club**.

---

## What we install — fully at our cost

| Component | Purpose | Location |
|---|---|---|
| 4K weather-resistant IP cameras (one or two per court, to be finalised at site walk) | Recording rallies during match play | Mounted on existing back-wall or overhead structure, at appropriate height, discreet |
| 1× courtside pause switch per court | Player-facing opt-out mechanism (see previous section) | Wall-mounted at the score area, LED-lit, weather-protected |
| Cabling (Cat6, outdoor-grade) | Camera → central network point | Run along existing cable trays; concealed |
| 1× Edge-buffer computer | Buffers matches locally, uploads to cloud securely, runs pause-switch state machine | Inside a small weatherproof enclosure at the power point |
| 1× 4G/5G cellular modem + SIM | Dedicated internet for the system — does not touch any club network | Same enclosure as the edge computer |
| 1× UPS / battery backup | Prevents data loss during brief power outages | Same enclosure |

**Installation:** A single 2-hour window on a morning of the club's choosing. One licensed electrician plus our install lead. Zero disruption to normal club or member activity outside that window.

**Ongoing maintenance:** We retain sole responsibility for hardware upkeep, software updates, system uptime, and any breakage. **Zero maintenance burden on the club.**

**Ownership and liability:** All equipment installed remains the property of Anchor Fastener Mfg Corporation. Any damage to club property caused during installation is our liability.

---

## What happens after Day 90 — commercial framework

At the end of the 90-day training phase, PadelMind moves into commercial operation on the two NSCI padel courts, on the framework set out below. This framework is being agreed **upfront, as part of this proposal**, so the committee has full clarity today and no separate commercial negotiation is required later.

**Pricing to members.** Members will be offered two options: (a) a **per-session usage fee** for occasional users, or (b) a **monthly subscription** for members who want continuous access. The exact price points will be shared with the committee ahead of commercial launch and positioned to be attractive to members.

**Revenue share with the club — 70:30, in the club's favour on effort.** All revenue collected from NSCI members using PadelMind will be shared with the club on a **70:30 ratio — 30% to NSCI, 70% to us**. The 30% share is calculated on **gross revenue** from NSCI members (i.e. top-line, not net of our expenses) and is remitted to the club **monthly**, together with a clear statement of member usage and amounts collected.

**All expenses borne by us.** Every operating cost of the commercial phase — hardware, cellular data, cloud, software, support, upgrades, replacements, member onboarding, billing infrastructure — continues to be borne entirely by us as the proposer. The club's 30% share is on top-line revenue, with **no cost deductions of any kind**.

**Tenure — 2-year lock-in.** The commercial arrangement runs for a fixed period of **2 years from the date of first commercial launch**. This protects both sides: the club receives a guaranteed 2-year revenue stream from an asset it invests nothing in, and we get the operating window we need to recover our investment in the training phase and grow member adoption. At the end of the 2-year lock-in, the arrangement will be reviewed and renewed on mutually agreed terms.

**Launch readiness.** At **Day 75** — with 15 days still remaining in the training phase — we will confirm to the committee that the software is ready for commercial launch on Day 91, and share the final member pricing sheet and communication plan for member roll-out. This is a **readiness confirmation, not a fresh commercial negotiation** — the terms above are being agreed today.

---

## Longer horizon — extending to tennis and badminton

If the padel phase proves the system out, the same approach extends naturally to **tennis and badminton**. NSCI is one of very few clubs in India that has active courts in all three of these racket sports under one roof, which makes it a genuinely unique candidate for a multi-sport rollout.

If the committee wished to extend the arrangement after the padel phase, NSCI would become **the first club in India with AI-assisted match analysis across padel, tennis, and badminton** — a distinction that would sit meaningfully alongside NSCI's existing standing as one of Mumbai's premier sports institutions.

We are not seeking a decision on this today. It is stated only so the committee is aware of the natural product horizon: what begins at the two padel courts can, if it earns the right to, become a club-wide capability for racket sports.

---

## A further value-add we would like to offer NSCI in the longer term

Independently of the match-analysis system, we would like to also offer NSCI — at **no cost, hosted and maintained free of charge** — an **in-house online court-bookings system** for the padel courts. This can be extended to other sports facilities at the club if the committee wishes. Members book courts on their phone; the club sees a live occupancy view; reminders and no-shows are handled automatically.

This is offered as a good-faith complement to the primary proposal. It is not a condition, not tied to the commercial phase, and not billable to the club. It reflects our long-term intent to serve NSCI as a technology partner beyond a single product.

We do not need a decision on this today; it is mentioned so the committee is aware of the broader intent. We can present it separately whenever the committee wishes.

---

## Why this is zero-risk for the club

**Equipment failure or issue** — All hardware is our property and our sole responsibility. Any breakage, outage, or replacement is on us, at no cost or inconvenience to the club.

**Member privacy** — No audio is captured. No facial recognition is used. No footage is shared with any third party or shown to any player during the training phase. Data is stored on Indian-jurisdiction cloud and used only for internal software training. **Any player who prefers not to be recorded can pause recording on that court in one press of a courtside switch (or by asking staff), for the next 2 hours — see the "Member privacy" section above for the mechanism.**

**Financial exposure** — Zero. The club invests nothing, pays nothing, and takes no operating risk. From Day 91 the club begins receiving a 30% share of gross revenue from NSCI members using the system, remitted monthly.

**Termination of the training phase** — If, during the 90-day training phase, the committee decides not to proceed at all, the trial may be terminated with 7 days' written notice; equipment is then removed at our cost within 7 days and the club owes nothing.

**No exposure on player-facing services during training** — Because no service is being offered to members during the 90-day training phase, there is no player grievance surface for the club to worry about in that period.

---

## What I ask the committee to approve

A single decision, expressible in one paragraph the committee can minute:

> *The Padel Committee approves a 90-day data-capture and model-training period on both padel courts, followed by a 2-year commercial phase from the date of first commercial launch, proposed by Anchor Fastener Mfg Corporation (through its product line PadelMind by AutomationXpert), represented by Member Manoj Maheshwari, at no cost or obligation to the club. During the training phase, video will be captured for the sole purpose of internal software training; no audio will be captured; no service will be offered to members. A discreet informational notice will be posted at each court explaining the recording and the opt-out mechanism. Members may pause recording on any court at any time either by pressing a clearly labelled courtside switch (auto-resumes after two hours) or by asking club staff. An audit log of pause events will be made available to the committee on request. The club will provide one covered, protected electrical point; internet connectivity will be arranged and paid for by the applicant. All equipment, installation, maintenance, connectivity, and all operating expenses of the commercial phase are the responsibility of the applicant. From the date of first commercial launch, 30% of the gross revenue collected from NSCI members using the system will be remitted to the club monthly for a fixed period of 2 years. The training phase may be terminated by the committee at any point with 7 days' written notice.*

---

## Timeline

| Milestone | Timing |
|---|---|
| Committee review and approval-in-principle | This meeting |
| Site walk with club maintenance to identify electrical point | Within 3 days of approval |
| Courtside informational notice posted | On installation day |
| Installation (2-hour window, morning) | Within 10 days of approval |
| Data capture and model training runs | Days 1–90 |
| Day 75 — launch-readiness confirmation to committee, final member pricing shared | To committee |
| Day 91 — commercial launch to NSCI members | — |
| Monthly remittance to club of 30% of gross revenue | From month 1 of commercial phase |
| End of 2-year lock-in — review and renewal on mutually agreed terms | Month 24 of commercial phase |

---

## About the applicant

**Anchor Fastener Mfg Corporation** is a Mumbai-based Indian company (GSTIN 27ACAPM7018E1ZV) with a registered office at 318/319, Tardeo Aircon Market, Tardeo, Mumbai – 400034. In addition to its manufacturing business, the company operates **AutomationXpert**, a WhatsApp-native SaaS platform serving Indian small businesses with live paying customers today.

**PadelMind by AutomationXpert** is a new product line under the same corporate roof, focused on AI-assisted racket-sports coaching. It is being built with an explicit India-first intent — Indian-owned, Indian-operated, developed on Indian match play, priced for Indian players.

I am Manoj Maheshwari, Director of Anchor Fastener Mfg Corporation and a member of NSCI. I play padel at the club regularly and would rather NSCI be the club where this product is developed and refined than any other.

---

## How to reach me

| Channel | Contact |
|---|---|
| WhatsApp (preferred) | +91 98200 27850 |
| Email | manoj@quitlosing.in |
| In person | On the padel courts most weekends |

I am happy to attend a committee meeting to walk through this in person and answer any questions.

---

## Attachments available on request

- Draft memorandum of understanding covering the 90-day training phase and the 2-year commercial phase, including the 70:30 revenue-share mechanics and monthly remittance format

---

**Thank you for the committee's time and consideration. We would be honoured to have NSCI as the club where PadelMind is developed and refined.**

*— Manoj Maheshwari*
*Director, Anchor Fastener Mfg Corporation*
*For PadelMind by AutomationXpert*
*Member, NSCI*

**Anchor Fastener Mfg Corporation**
318/319, Tardeo Aircon Market, Tardeo, Mumbai, Maharashtra – 400034, India
GSTIN 27ACAPM7018E1ZV

---

*Working draft dated 2026-07-02. Please confirm receipt and preferred meeting slot to discuss.*
