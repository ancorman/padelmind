# PadelMind — Post-Match Report UI Scope

**Date:** 2026-07-12 · Owner: Manoj + Claude Code
**Siblings:** `PHASE_FEATURE_MAP.md` (feature tiers — the LAW for what renders) · `SASANK_SOW_PHASE1.md` §1 (WA delivery moment) · `pwa/` (live Player PWA, padelmind-pwa.pages.dev)
**Scope rule (from PHASE_FEATURE_MAP §2):** Tier S + S+ render as LIVE. Tier P appears ONLY inside the "Coming soon" strip, no dates. Nothing on any surface may promise past the feature map.

---

## 0. Existing PWA visual language (design within this — observed, not invented)

| Aspect | What the codebase actually does |
|---|---|
| Framework | React 18 + Vite, plain `.jsx`, deployed to Cloudflare Pages |
| Routing | **No router.** State-machine nav in `App.jsx`: `appState` (loading/unauth/register/pending/app) → `tab` (matches/book/staff) → `matchCtx` object opens `Match.jsx` as a pushed detail view |
| Styling | Tailwind is installed but **unused in practice**. Real convention: inline `style={{}}` objects + a small global class set in `src/index.css` (`.card`, `.badge`, `.btn-primary`, `.btn-ghost`) driven by CSS variables |
| Theme tokens | `--bg #0F172A` (slate-900) · `--bg-elev #1E293B` · `--border #334155` · `--amber #3D6FD6` (**actually blue** — the accent; keep the variable name, it's everywhere) · `--green #34D399` · `--text #F1F5F9` · `--muted #94A3B8` · `--danger #F87171` · orange `#FB923C` exists in `.badge-processing` |
| Type | System font stack. Headings 15–20px weight 700–800 negative letterspacing; section labels 11–12px UPPERCASE muted with 0.5–0.8px letterspacing; stat values 16–22px weight 700–800 |
| Patterns | `.card` = 16px-radius elevated panel; sticky header with back arrow; bottom nav 3 tabs; local single-file helper components (`StatBlock`, `SectionLabel`, `Stat`, `NavTab`); emoji as icons; `—` for missing values; every media block has an explicit empty/error state |
| Data | Supabase anon client (`src/supabase.js`) + `PUB_R2` public R2 base URL const. Media = `PUB_R2 + r2_key` |
| Auth | Email magic link (`signInWithOtp`), 3s session polling on the sent screen |
| Existing report | `src/pages/Match.jsx` **is already the V1 proto-report**: 3-stat strip (Rallies/Duration/Avg Rally), own heatmap image, highlight `<video>`, calibration/processing empty states baked in |

**Design consequence for the heatmap PNGs (800×1600, dark bg, fire colormap):** they sit natively on `--bg-elev` cards. The fire oranges/yellows are the hottest color on the screen — let them own "movement/intensity" visually. Use orange `#FB923C` as the accent for intensity elements (sparkline, fade-point marker, sprint tile) so the UI echoes the heatmap; keep `--amber` blue for navigation/CTAs as today. Do not put competing saturated colors adjacent to the heatmap.

---

## 1. Surfaces overview

Two surfaces, one report. **WA is the hook, PWA is the depth.**

| | (a) WhatsApp message set | (b) PWA match report page |
|---|---|---|
| Constraint | text + 1 image + 1 video + 1 link (3 messages, per SOW §1) | full scrollable page, authenticated |
| Arrives | ~12 min post-match, zero user action | on tapping the WA link |
| Job | deliver the wow-moment + 3–4 punchiest numbers + create the itch to tap | ALL 14 metrics, 4-player heatmaps, trends, share card, roadmap teaser |
| Identity | phone number (no login during match) | magic-link session; deep link lands on this match |

Why the split: WhatsApp is where the player already is — it must carry the emotional payload (your heatmap, your highlight, "you ran 3.4 km") in a glance, but it cannot carry 14 metrics without becoming spam. The PWA is where identity, history, and trends live — and it's the only surface that can render the intensity curve, 4-player comparison, and the IG share card. Every WA message therefore ends in the same single deep link. One link, one destination (per one-canonical-link rule).

---

## 2. WA message spec

Three messages, sent in order to each of the 4 players individually (personalized heatmap + personalized numbers).

**Message 1 — text summary (V1.5 template, 11 lines):**

```
🎾 Match Report — {court_name}, {DD Mon}

⏱ {duration_min} min · {rally_count} rallies
🏃 You ran {distance_km} km — {sprint_count} sprints, top speed {top_speed} km/h
🎯 Net time {net_pct}% · baseline {baseline_pct}%
🔥 Longest rally: {longest_rally_s} sec — it's in your highlights
📉 Intensity dipped after min {fade_min}

Aapka full report — heatmap, trends, share card:
👉 https://padelmind-pwa.pages.dev/?m={match_id}

Heatmap aur highlight reel next 2 messages mein 👇
```

**V1 fallback of Message 1** (only Tier S data exists — drop the 3 stat lines):

```
🎾 Match Report — {court_name}, {DD Mon}

⏱ {duration_min} min · {rally_count} rallies
🔥 Aapke top rallies ka highlight reel ready hai

Full report + heatmap:
👉 https://padelmind-pwa.pages.dev/?m={match_id}

Heatmap aur highlight reel next 2 messages mein 👇
```

**Message 2 — image:** the player's OWN heatmap PNG (`heatmap_r2_key`, <300KB). Caption: `Aapka court heatmap — jahan aap sabse zyada khele 🔥`

**Message 3 — video:** shared `highlights.mp4` (<15MB). Caption: `Top {n} rallies — 60 sec highlight reel 🎬`

**Deep link:** `https://padelmind-pwa.pages.dev/?m={match_id}` — see §3.0. Same link in all contexts; no variant links.

Rules: plain English + natural Hinglish, no jargon (never "homography", "coverage index", "positional"). Numbers pre-rounded (1 decimal km, integer %, integer km/h). If a stat is null, its line is omitted — never `—` in WhatsApp.

---

## 3. PWA match report screen — section-by-section wireframe

Mobile-first, 390px mental model. This page = `src/pages/Match.jsx` grown up (extend in place; the list→detail wiring in `Matches.jsx`/`App.jsx` already works).

### 3.0 Deep link (new, V1)

No router exists — add query-param handling in `App.jsx`: on load read `?m=<match_id>`; after `resolvePlayer()` lands in `app` state, fetch that match's ctx and `setMatchCtx(...)`, then strip the param via `history.replaceState`. Unauthenticated → normal magic-link flow, param survives in `localStorage` until session lands (redirect target is `window.location.origin` — persist the param before it's lost). Match not found / not this player's → silently fall through to the list.

### 3.1 Full-page wireframe

```
┌──────────────────────────────────────┐
│ ←  Match Report                      │ 3.2 HEADER (sticky)
│    Court 2 · NSCI Mumbai             │
│    Sat 12 Jul · 7:31–8:58 pm · 87min │
├──────────────────────────────────────┤
│  YOUR HEATMAP                        │ 3.3 HERO — heatmap
│ ┌──────────────────────────────────┐ │
│ │ [You] [Rahul] [Amit] [Priya]     │ │  ← 4 player tabs
│ │ ┌──────────────────────────────┐ │ │
│ │ │                              │ │ │
│ │ │    800×1600 fire-colormap    │ │ │
│ │ │    heatmap PNG, full width   │ │ │
│ │ │    (aspect 1:2, dark bg      │ │ │
│ │ │     merges with card)        │ │ │
│ │ │                              │ │ │
│ │ └──────────────────────────────┘ │ │
│ └──────────────────────────────────┘ │
├──────────────────────────────────────┤
│  HIGHLIGHT REEL                      │ 3.4 highlight player
│ ┌──────────────────────────────────┐ │
│ │        ▶  9:16 video             │ │
│ │        (max-height 60vh)         │ │
│ └──────────────────────────────────┘ │
├──────────────────────────────────────┤
│  RALLY TIMELINE                      │ 3.5 rally strip
│ ┌──────────────────────────────────┐ │
│ │ ▂▂█▂▂▂██▂▂▂▂█▂▂██▂▂▂▂▂█▂▂▂▂▂█▂  │ │  ← bars on 0→87min axis
│ │ 24 rallies · avg 18s             │ │
│ └──────────────────────────────────┘ │
├──────────────────────────────────────┤
│  MOVEMENT                            │ 3.6 stat tile grid
│ ┌─────────┐ ┌─────────┐ ┌─────────┐ │  (2- or 3-up .card tiles)
│ │ 3.4 km  │ │ 14      │ │ 64%     │ │
│ │ DISTANCE│ │ SPRINTS │ │ COVERAGE│ │
│ │         │ │ top 18  │ │ of your │ │
│ │         │ │ km/h    │ │ half    │ │
│ └─────────┘ └─────────┘ └─────────┘ │
│  TACTICS                             │
│ ┌─────────┐ ┌─────────┐ ┌─────────┐ │
│ │ 22%     │ │ 3.1 m   │ │ 41%     │ │
│ │ NET TIME│ │ PARTNER │ │ RESETS  │ │
│ │ 78% base│ │ SPACING │ │TO CENTRE│ │
│ └─────────┘ └─────────┘ └─────────┘ │
├──────────────────────────────────────┤
│  INTENSITY                           │ 3.7 sparkline
│ ┌──────────────────────────────────┐ │
│ │     ╱╲    ╱╲╱╲                   │ │
│ │ ╱╲╱    ╲╱      ╲___  ← fade      │ │  orange #FB923C line,
│ │ 0        45    ⚠52         87min │ │  fade-point marker
│ │ Intensity dropped after min 52   │ │
│ └──────────────────────────────────┘ │
├──────────────────────────────────────┤
│ ┌──────────────────────────────────┐ │ 3.8 longest rally callout
│ │ 🔥 LONGEST RALLY — 41 sec        │ │
│ │ Rally #17, minute 52 · golden pt │ │
│ │ [▶ Watch it]  (seeks highlight)  │ │
│ └──────────────────────────────────┘ │
├──────────────────────────────────────┤
│  VS YOUR LAST MATCH                  │ 3.9 trends
│ ┌──────────────────────────────────┐ │
│ │ Net time    22% ▲ +4pts   (green)│ │
│ │ Distance   3.4km ▼ −0.3km (muted)│ │
│ │ Top speed  18kmh ▲ +1     (green)│ │
│ │ Sprints      14  ─  same         │ │
│ └──────────────────────────────────┘ │
├──────────────────────────────────────┤
│ ┌──────────────────────────────────┐ │ 3.10 share CTA
│ │   📤 Share your match card       │ │  .btn-primary full-width
│ └──────────────────────────────────┘ │
├──────────────────────────────────────┤
│  COMING TO YOUR REPORTS              │ 3.11 Tier P teaser
│ ┌──────────────────────────────────┐ │
│ │ 🎾 Smash speed  🏸 Shot types    │ │  muted chips, no dates,
│ │ 🎯 Shot placement 📊 Win/error   │ │  not tappable
│ └──────────────────────────────────┘ │
│                                      │
│ [existing bottom nav]                │
└──────────────────────────────────────┘
```

### 3.2 Header — match meta

- **Data:** `padel_matches.started_at/ended_at/duration_sec` + `padel_courts.name` + `padel_clubs.name,city` (already in the `Matches.jsx` select; pass through `matchCtx`).
- **Empty:** date always exists; missing court → hide line 2. `duration_sec` null → omit.
- **Phasing:** V1 (upgrade of the existing "Match Detail / Player N" header).

### 3.3 Hero — heatmap with 4-player tabs

- **Data:** all 4 `padel_match_players` rows for this match — `player_slot`, `heatmap_r2_key`, joined `padel_players.name` (first name only). New query on page mount (current ctx carries only own key). "You" tab first, then slots in order. Image = `PUB_R2 + key`.
- **RLS dependency (flag):** players must be able to SELECT co-players' `heatmap_r2_key` + first name for matches they played in — verify/extend the `004_email_auth_rls.sql` policy before build.
- **Empty:** no calibration → all keys null → keep existing "Heatmap will appear after court calibration" card, no tabs. Some slots missing → render only tabs that have keys. Image error → existing "Heatmap unavailable" card.
- **Phasing:** V1. (Tier S ships 4 PNGs; tabs are pure UI on existing data.)

### 3.4 Highlight player

- **Data:** `padel_match_outputs.highlight_r2_key` (shared per match, already wired).
- **Empty:** existing "Highlight reel processing" card. Video error → "Video unavailable".
- **Phasing:** V1 — already built. V1.5 adds a `ref` so §3.8 can seek it.

### 3.5 Rally timeline

- **Data:** `padel_match_outputs.rally_windows` jsonb `[{start_sec, end_sec, duration}]` (column exists TODAY) + `rally_count` + `duration_sec` for the axis. Bars = rally windows positioned on a 0→duration horizontal track (plain flex/absolute divs, no chart lib); bar height ∝ duration. Top-5 (highlight-reel rallies) tinted `#FB923C`, rest `--border`-ish.
- **Empty:** `rally_windows` null/empty → fall back to the plain "24 rallies" stat in the header strip; hide the track.
- **Phasing:** V1 (Tier S = "rally count + rally timeline").

### 3.6 Stat tile grid — Movement / Tactics

- **Data:** NEW `stats.json` from the Phase-1.5 `stats.py` worker module (PHASE_FEATURE_MAP §3). Proposed persistence: `padel_match_outputs.stats jsonb` (schema delta — this doc flags it, worker/Worker own it). Per-player block keyed by slot:
  - Movement: `distance_m`, `sprint_count`, `top_speed_kmh`, `coverage_pct`
  - Tactics: `net_time_pct`, `baseline_time_pct`, `avg_partner_dist_m`, `recovery_to_centre_pct`
- Tiles are mini `.card`s in a CSS-grid 3-up; value 22px/800 (`--text`; orange for sprint/intensity tiles), label 11px UPPERCASE muted, optional 10px sub-line ("top 18 km/h", "78% baseline"). Group headers use existing `SectionLabel` style.
- **Empty:** `stats` null (all V1 matches) → **entire grid absent**, plus one muted line: "More stats coming to your reports soon." (generic, no dates, no Tier-S+ enumeration — don't tease specifics before V1.5 ships).  Individual null field → that tile shows `—`.
- **Phasing:** V1.5.

### 3.7 Intensity sparkline

- **Data:** `stats.intensity_curve` `[{min, v}]` (per-match avg movement velocity per minute, 0–1 normalized) + `stats.fade_point_min` (nullable). Inline SVG polyline, orange `#FB923C`, 2px, faint area fill; fade point = dashed vertical + ⚠ marker + one plain sentence below.
- **Empty:** curve absent → hide section. Curve present but no fade → line only, sentence omitted (a no-fade match is a good match — don't invent commentary).
- **Phasing:** V1.5 (Tier S+ "rally intensity curve / fade point").

### 3.8 Longest rally callout

- **Data:** `stats.longest_rally {duration_s, start_s, rally_index, is_golden}` (derivable from `rally_windows` alone as fallback: max-duration window). "Watch it" maps `rally_index` → offset inside `highlights.mp4` via `stats.highlight_clip_map` `[{rally_index, offset_s}]` from the clipper; seeks the §3.4 `<video>` and scrolls to it.
- **Empty:** no `rally_windows` → hide. No `clip_map` or rally not in top-5 → render callout without the Watch button. `is_golden` absent → omit the golden-point chip.
- **Phasing:** callout-lite (duration only, from `rally_windows`) could ship V1 free; full version (golden flag + Watch seek) is V1.5. Scope it as V1.5, don't gold-plate V1.
- Visual: `.card` with `1px solid #FB923C`-tinted border — the one "hot" card on the page.

### 3.9 Trends — "vs your last match"

- **Data:** NEW Supabase view `padel_player_match_stats` (player_id, match_id, started_at, flattened stat columns) per PHASE_FEATURE_MAP §3.5; PWA fetches this player's 2 most recent rows and diffs client-side. Rows: net time, distance, top speed, sprints, coverage (5 max). Delta chip: ▲ `--green` / ▼ `--muted` / ─ same. **Direction-aware:** ▲ is green only when up is good (all 5 chosen rows: up = good; distance is framed as work-rate so up = green too — keep it consistent, never red: a report should never scold).
- **Empty:** <2 matches with stats → "Play one more match to unlock trends 📈" muted card. Multi-match sparkline-per-stat ("net time up 12% this month") = later V1.5 iteration, same section, don't build now.
- **Phasing:** V1.5.

### 3.10 Share-card CTA → §4

- **Data:** own heatmap PNG + 4–5 stats (§4). Client-side `<canvas>` 1080×1920 → `toBlob` → Web Share API (`navigator.share({files})`); fallback = download + "Add to your story".
- **CORS dependency (flag):** drawing the R2-hosted heatmap into canvas needs `crossOrigin="anonymous"` + R2 CORS allow-origin for the Pages domain, else the canvas taints. Verify on `padelmind-dev` bucket before build.
- **Empty:** stats or heatmap missing → button hidden (V1 has no share card; Tier S+ item).
- **Phasing:** V1.5.

### 3.11 "Coming soon" strip — Tier P teaser

- **Data:** hard-coded array, copy straight from PHASE_FEATURE_MAP Tier P: `Smash & shot speed`, `Shot types (bandeja, vibora…)`, `Shot placement maps`, `Winners & errors`. Muted chips (badge style, `--muted` on `--bg-elev`), not tappable, header "COMING TO YOUR REPORTS". **No dates, ever** (feature-map rule).
- **Empty:** n/a — always renders.
- **Phasing:** V1 (cheap, sets roadmap expectation from day one).

### V1 page (only Tier S data) renders as:
Header → heatmap hero with tabs → highlight player → rally timeline → "More stats coming soon" line → coming-soon strip. Complete-feeling page, no dead tiles, no locked-content nagging.

---

## 4. Share card spec — 1080×1920 IG-story PNG

Client-side canvas render (no server). Background `#0F172A`. The heatmap IS the design.

```
┌────────────────────────────────┐ 1080×1920
│  PADELMIND        NSCI · 12 Jul│  y0–140: wordmark 44px 800 white,
│                                │          right: club+date, muted
│   ┌────────────────────────┐   │
│   │                        │   │  y160–1210: own heatmap PNG
│   │    heatmap 800×1600    │   │  scaled to 840×1050 h-crop
│   │    scaled ~840 wide    │   │  (top ⅔ of court view), 24px
│   │    fire colormap       │   │  rounded corners, 1px #334155
│   │                        │   │  border. Dark PNG bg merges
│   │                        │   │  into card bg.
│   └────────────────────────┘   │
│                                │
│   3.4 km        18 km/h       │  y1270–1450: 2×2 metric grid
│   DISTANCE      TOP SPEED     │  values 72px 800 white,
│                                │  labels 26px uppercase #94A3B8
│   22%           41 sec        │
│   NET TIME      LONGEST RALLY │
│                                │
│   ── 24 rallies · 87 min ──   │  y1520: strip line, 30px muted
│                                │
│      Get your match report     │  y1650: CTA 30px #3D6FD6
│      padelmind-pwa.pages.dev  │  y1700: URL 26px muted
│  🎾 PadelMind — AI match report│  y1840: footer lockup 24px
└────────────────────────────────┘
```

- **The 4 card metrics + strip:** Distance, Top speed, Net time %, Longest rally (the 4 most braggable / most conversation-starting) + rallies·duration as a subline. Not coverage/spacing/recovery — too explain-y for a story.
- **Branding:** PadelMind wordmark top-left (text, 800 weight, matches PWA header), club name top-right (flatters the club → clubs reshare), URL + tagline bottom. No player name by default (privacy on public stories) — first name optional later.
- Null metric → swap in next-best from priority list [distance, top_speed, net_pct, longest_rally, sprints, coverage]; card always shows exactly 4.
- Safe margins 90px all sides (IG story UI overlays).

---

## 5. Component / build plan

Conventions observed and followed: page components default-exported from `src/pages/*.jsx`; small helpers as non-exported function components in the same file (like `StatBlock`, `SectionLabel` today); inline styles + CSS vars; no new deps (no chart lib — SVG/divs; no router — query param).

All report UI lives in `src/pages/Match.jsx` + helpers; only deep-linking touches `App.jsx`.

### V1 UI (Tier S data only)

| Component (file) | What | Est |
|---|---|---|
| `App.jsx` — deep-link handling | `?m=` parse, persist through magic-link, auto-open `matchCtx`, replaceState | 3 h |
| `Match.jsx` — header upgrade | court · club · date · time-range meta (pass-through ctx fields) | 1.5 h |
| `HeatmapTabs` (in Match.jsx) | fetch 4 `padel_match_players` rows, tab strip, swap image, per-tab empty states | 4 h |
| `RallyTimeline` (in Match.jsx) | bars from `rally_windows` on duration axis, top-5 tint, count subline | 3 h |
| `ComingSoonStrip` (in Match.jsx) | static Tier P chips | 1 h |
| "More stats coming soon" placeholder line | one muted line where the grid will be | 0.5 h |
| RLS policy check/patch for co-player heatmap keys | migration review | 1 h |
| Device QA pass (iOS Safari + Android Chrome, WA in-app browser) | 5 flows incl. deep link cold-start | 2 h |
| **V1 UI total** | | **16 h (~2 days)** |

### V1.5 UI (needs `stats.json` + trends view from Phase-1.5 backend)

| Component (file) | What | Est |
|---|---|---|
| stats fetch (in Match.jsx) | read `padel_match_outputs.stats` (or `stats_r2_key` fetch), null-safe accessor | 2 h |
| `StatTileGrid` + `StatTile` (in Match.jsx) | 6 tiles, Movement/Tactics groups, sub-lines, `—` nulls | 4 h |
| `IntensitySparkline` (in Match.jsx) | SVG polyline + area + fade marker + sentence | 4 h |
| `LongestRallyCallout` (in Match.jsx) | hot-border card, golden chip, Watch→seek video ref | 2.5 h |
| `TrendsSection` (in Match.jsx) | query `padel_player_match_stats` view, 5 delta rows, unlock empty state | 4 h |
| `ShareCard` (new `src/pages/shareCard.js` — pure canvas module) | 1080×1920 draw: heatmap img + 4 metrics + branding; CORS-safe load | 6 h |
| Share CTA + Web Share / download fallback (in Match.jsx) | button, blob, `navigator.share`, fallback sheet | 2 h |
| WA Message-1 template upgrade (Worker side, copy in this doc §2) | wire stats into existing delivery — counted here for completeness | 2 h |
| Device QA pass incl. share-to-IG on real phone | | 3 h |
| **V1.5 UI total** | | **29.5 h (~4 days)** |

**Out of UI scope (dependencies, owned elsewhere):** `stats.py` in the RunPod worker + fattened callback (PHASE_FEATURE_MAP §3.1–3.2) · `padel_match_outputs.stats` column migration · `padel_player_match_stats` view/rollup · R2 CORS config · WA router `padel-match-report` message type (exists per SOW §3.1).

---

## 6. Metric count summary

**V1 = 4 items · V1.5 adds 10 · total 14 on screen.**

| # | Tier | Item | Tile / section label | Unit shown |
|---|---|---|---|---|
| 1 | S | Per-player heatmap (×4) | YOUR HEATMAP (+ 3 name tabs) | image |
| 2 | S | Highlight reel | HIGHLIGHT REEL | 60–90 s video |
| 3 | S | Rally count + timeline | RALLY TIMELINE | count + bars |
| 4 | S | Match duration | header meta + timeline axis | min |
| 5 | S+ | Distance covered | DISTANCE | km (1 dp) |
| 6 | S+ | Sprint count + top speed | SPRINTS (sub: top speed) | count · km/h |
| 7 | S+ | Court coverage % | COVERAGE (sub: "of your half") | % |
| 8 | S+ | Net vs baseline time | NET TIME (sub: baseline %) | % / % |
| 9 | S+ | Partner spacing | PARTNER SPACING | m (1 dp) |
| 10 | S+ | Recovery-to-centre habit | RESETS TO CENTRE | % |
| 11 | S+ | Intensity curve + fade point | INTENSITY | sparkline + min |
| 12 | S+ | Longest rally + golden points | 🔥 LONGEST RALLY | sec + chip |
| 13 | S+ | Multi-match trends | VS YOUR LAST MATCH | Δ chips |
| 14 | S+ | IG share card | Share your match card | 1080×1920 PNG |

Tier P renders only as the non-tappable "COMING TO YOUR REPORTS" strip — 4 chips, zero dates.

---
*Prepared 2026-07-12 · PadelMind by AutomationXpert · UI scope only — no code modified.*
