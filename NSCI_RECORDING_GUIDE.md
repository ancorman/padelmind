# NSCI Court Recording + Calibration Field Guide
**For:** Sunday 2026-07-12 — evening floodlight match (+ optional daytime bonus clip)
**Feeds:** CV pipeline test (Steps 2–8), calibration keypoints (M5), fine-tune dataset (Roboflow round 2)

---

## The one rule that matters

> **The camera must not move — at all — from the calibration moment to the last second of the match.**
> Calibration maps THIS camera at THIS exact position to court metres. A 2 cm nudge invalidates everything.
> If the camera gets bumped mid-match: don't panic, don't re-aim mid-match — note the time; footage before the bump is still fully usable.

And the corollary: **you need ONE wide still from the recording camera's final position — not photos of every court zone.** Training frames come from the video automatically.

---

## Kit checklist (before leaving home)

- [ ] Phone/camera with **≥25 GB free** (4K30 ≈ 15 GB for 90 min; 1080p30 ≈ 5.5 GB)
- [ ] Tripod / clamp mount / stable railing spot — anything that locks the phone dead still
- [ ] Power bank + cable (90 min continuous 4K recording drains hard)
- [ ] 60 seconds of patience before the match for the setup ritual below

**Resolution call: shoot 4K30 if storage allows, else 1080p30.** 4K gives the far court more pixels (that's our weakest zone); the pipeline downsamples anyway, so nothing is wasted.

---

## Camera position (get as close to production spec as the venue allows)

Target the SOW Plan-A geometry:
1. **Behind one back glass wall**, centred on the court's width
2. **As high as you can get it** — production is 4–5 m; a first-floor gallery/railing/high clamp beats head height. Height is what separates the four players visually and keeps far players from hiding behind near players.
3. Frame check, in priority order (sacrifice top-of-frame headroom first if forced):
   - [ ] All 4 court corners visible
   - [ ] **Far corners + far service line clearly in frame** (homography dies without the far anchors)
   - [ ] Near baseline fully inside the frame (not clipped at the bottom edge)
   - [ ] Net posts both visible
4. **Landscape orientation.** Lock rotation.
5. iPhone: **AE/AF LOCK** — long-press on mid-court until "AE/AF LOCK" shows, so floodlight exposure doesn't pump when players cluster. Turn OFF HDR video if easy to find. Action mode OFF (it crops).

---

## The 4-step recording ritual

### 1 — Lock the camera, then hands off
Mount, frame, AE/AF-lock. From this moment the phone is untouchable.

### 2 — Empty-court clip (30 s) ← the calibration gold
Before players walk on (or between points at worst), record **30 seconds of the empty court** in good floodlight. This clip is where the calibration still gets extracted from — clean lines, zero occlusion. This is the single most important 30 seconds of the evening.

### 3 — Record the match (one continuous take)
- One recording, start to finish. Don't stop/start between games (each cut risks a nudge).
- Note **match start time and end time** (rough is fine; helps us trim).
- Nobody stands directly in front of the lens between camera and glass.

### 4 — Post-match still (drift insurance)
Before touching the mount, record 10 more seconds (or snap one photo *from the recording position*). If lines in the pre- and post-clips overlay perfectly, we KNOW the camera never moved. Then pack up.

---

## Optional daytime bonus (only if convenient — courts full is FINE)

Purpose: **lighting diversity for the model fine-tune** (floodlight vs daylight look very different to a detector). Not needed for calibration.

- 5–10 minutes of any running daytime match, from roughly the same vantage style (high, behind glass)
- Same rules-lite: landscape, stable (railing is fine), don't need the empty court, don't need perfection
- Any court works — it's texture for the model, not geometry
- Courtesy note: it's your club and the footage is internal training data, but a quick word to the players on court never hurts

---

## What happens after (my side, Mac)

| Step | Effort | When |
|---|---|---|
| Extract calibration still from empty-court clip | minutes | tonight/tomorrow |
| Click 12 keypoints in the P0-G calibration tool → Supabase | **10–15 min, one-time** | same sitting |
| Run pipeline Steps 2–6 on the match footage | the real build | next session |
| Auto-sample ~800 frames + auto-label with bootstrap model → Roboflow fine-tune round | background | after pipeline runs |

Re-calibration is only ever needed if the camera position changes. For the pilot install (fixed Reolink on a wall mount), it's once per court, ever — until someone bumps the mount.

---

## TL;DR card (screenshot this)

```
□ 25 GB free, power bank, tripod/clamp
□ High + centred behind back glass, landscape, AE/AF lock
□ All 4 corners in frame (far corners = non-negotiable)
□ 30 s EMPTY COURT clip first  ← the gold
□ One continuous match take, note start/end
□ 10 s post-match clip (drift check)
□ Camera NEVER moves in between
□ Bonus: 5–10 min daytime clip, any court, for model variety
```
