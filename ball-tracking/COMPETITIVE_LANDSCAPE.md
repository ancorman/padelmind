# Ball tracking in racket sports — landscape & where PadelMind fits

Compiled 2026-07-13 from 4 sourced research passes. Vendor marketing flagged as such.
Visual: https://claude.ai/code/artifact/ff3b56a1-93d7-4507-8a7a-b7cc5a8c2664

## Four camps
1. **Pro officiating** — Hawk-Eye (Sony, ~3.6mm, 6–18 cams, ~$100k/court), Foxtenn (~2500fps + lasers). **No verified Hawk-Eye padel deployment.** Padel tour (unified Premier Padel from 2024) runs **human video review only — no automated line calling.**
2. **Research lineage** — TrackNet (2019, 98.5% F1) → V2 (2020, 31fps, honest 96→85% generalization drop) → V3 (2023, inpainting, 97.5%) → V4 (2024, motion attention). **WASB** (2023, NTT) beats V2 across 5 sports at 7× smaller (1.5M params). **MonoTrack** (2022) = single-cam 3D. Padel-native: **Novillo et al. 2024 (DS_Padel) = TrackNet + homography → 2D court — our exact pipeline**; PadelTracker100 dataset (~100k frames, 2 WPT matches).
3. **Consumer phone apps** — **SwingVision** (category leader: on-device single-phone, 20k subs, ~$4M ARR, $6M Series A, 2023 Apple Design Award; iOS-only, tennis-first, **padel in beta**). Padel-specific: **Padel AI** (closest comparable — scores 6 strokes on Playtomic 1–7 from phone, cloud, Europe-first, **no ball tracking claimed**, $49.99/yr), Padelize, PadelShot.
4. **Club camera + SaaS** — Clutch (125+ clubs, "Clutch Score", €199/mo, player-not-ball), GameCam (250+ clubs, ball+player, €950+€300/mo), **Padelytics → acquired by SportAI 2025** (real ball+player tracking, $1.8M seed + $805k grants), Wingfield (€4M Series A), PlaySight (recording, not tracking).

## Key strategic findings
- **No incumbent to displace in India** — zero India padel-analytics startup surfaced in any search.
- **No automated ball-tracking on the padel tour** — only human video review.
- **The closest phone competitors (Padel AI, Padelize) don't claim real ball tracking** — our clearest differentiator.
- **On-device vs cloud is the moat axis** — Zepp/Babolat/Sony racket sensors all died 2020–21 on cloud-backend shutoffs. Cloud dependency = product-death risk.
- **Glass-wall rebounds unsolved by everyone** — no benchmark models it. Opportunity + risk (don't assume tennis methods transfer).

## Threats (the clock)
- **SwingVision** padel beta (Apple pedigree, on-device).
- **SportAI/Padelytics** (funded, real ball+player tracking, moving down-market).
- **Padel AI** already owns "phone technique score" — a me-too loses; our edge must be ball tracking + rubric depth + India distribution.

## Where PadelMind tracks
Method validated (TrackNet zero-shot 71%, matches Novillo 2024) · real ball tracking (rivals lack) · win-anchored 94-video coach rubric (deeper than a 1–7 number) · India-first + Android + ₹ pricing · on-device path (avoids cloud-death). Wedge = **real on-device ball tracking + win-anchored coach, India first.**

## Corrected / unverified
- **"MatchVision" does not exist** under that name (likely a misremember of **Clutch**).
- **SwingVision Shark Tank** — no source; real accolade is the 2023 Apple Design Award.
- Foxtenn "0mm/100% real", club counts, revenue-uplift = vendor marketing.
- WASB per-sport F1 digits + some GitHub stars from secondary summaries.

## Sources
Hawk-Eye [wiki](https://en.wikipedia.org/wiki/Hawk-Eye) · TrackNet [arxiv](https://arxiv.org/abs/1907.03698) · WASB [arxiv](https://arxiv.org/abs/2311.05237) · MonoTrack [arxiv](https://arxiv.org/abs/2204.01899) · DS_Padel [github](https://github.com/AlvaroNovillo/DS_Padel) · SwingVision [sportico](https://www.sportico.com/business/tech/2023/swingvision-ai-tennis-tracking-series-a-financing-round-1234742401/) · SportAI+Padelytics [sportai](https://sportai.com/news/sportai-and-padelytics-join-forces) · Padel AI [site](https://padelaiapp.com/) · Clutch [site](https://www.clutchapp.io/) · GameCam [site](https://www.gamecam.io/) · Wimbledon ELC [svg](https://www.svgeurope.org/blog/headlines/wimbledon-to-adopt-sony-hawk-eyes-live-electronic-line-calling-for-2025/)
