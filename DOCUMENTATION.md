# Documentation — Open Surf Software

Requirements: [REQUIREMENTS.md](REQUIREMENTS.md). Decisions:
[ARCHITECTURE_DECISIONS.md](ARCHITECTURE_DECISIONS.md). Operator tasks:
[HOW_TO.md](HOW_TO.md).

## Layout

```
opensurf/
  opensurf/
    api.py                 whitelisted Guest API: spots / forecast / cams / best_today
    scoring.py             pure-function scoring engine (no framework deps)
    report.py              optional LLM daily report + confidence (OpenAI-compatible)
    seed.py                after_install: loads data/*.json into DocTypes
    helpers.py             page helpers (arrows, day labels, SVG tide curve)
    ingest/
      __init__.py          refresh_all() — scheduler entry, one spot at a time
      openmeteo.py         marine + weather fetch/normalize
      bmkg.py              perairan (waters) + pelabuhan (port/tides) fetch
      snapshots.py         site/files JSON snapshot store (read/write/latest)
    data/
      bali_spots.json      23 curated Bali spots with condition envelopes
      bali_cams.json       21 known Bali cams, all consent = link-only
    open_surf_software/doctype/
      surf_spot/           registry: geo, break info, BMKG codes, score envelope
      surf_cam/            registry: provider, stream url, consent state
      open_surf_settings/  single: LLM base url / model / api key / enable flag
    www/
      spots/index.html+py  spot list, today's pick, sorted by day score
      spot.html+py         spot detail: report box, day nav, tide curve, hour table
      cams.html+py         cam directory grouped by spot/provider
      opensurf.css         shared styles, linked via head_include per page
    tests/                 scoring + BMKG parsing unit tests (no network)
```

## Data flow

```
hourly cron → ingest.refresh_all()
    per active Surf Spot:
      openmeteo.fetch(spot)   → marine (swell1/2, wind-wave) + weather (wind/gust)
      bmkg.fetch_area(spot)   → human-forecaster waters forecast (P.P.xx)
      bmkg.fetch_port(spot)   → hourly tide metres + waves for nearest port (XPxxx)
      snapshots.write(slug)   → {fetched_at, openmeteo:{hours[]}, bmkg:{area,port}}
      report.refresh_if_stale → LLM report if missing or >6h old
```

Pages and API read only snapshots + DocType fields — a user request never
hits an upstream API (ADR-004). Fetch timestamps are rendered in the page
footer for staleness visibility (N5).

## Scoring

`scoring.score_hour(envelope, hour)` weights five components:

| component    | weight | source fields                        |
|--------------|--------|--------------------------------------|
| swell_dir    | 0.25   | direction vs preferred arc           |
| swell_size   | 0.25   | height vs preferred band             |
| swell_period | 0.15   | period vs preferred band             |
| wind         | 0.20   | direction vs offshore band, speed    |
| tide         | 0.15   | level vs `tide_preference`           |

A component that is absent from the data returns `None` and is re-weighted
away — except `tide_preference == "any"`, which scores 1.0. Missing tide data
is therefore neutral, never a free bonus. `score_day` aggregates daylight
hours into a 0–10 day score plus best-window hours; `best_spot` picks the
daily recommendation across all spots.

## LLM report

`report.generate_for_spot` posts one chat-completion per spot per day (when
fresh): compact scored hours (06:00+), spot character, and the BMKG human
forecast as "second opinion". The model returns JSON
`{report, confidence, confidence_note}` which lands in the snapshot as
`snapshot.report` together with `model` and `generated_at`.

Configuration (any OpenAI-compatible endpoint):

- `Open Surf Settings`: `enable_llm_reports`, `openai_base_url`,
  `openai_model`, `openai_api_key` (password field), or
- site config `opensurf_openai_api_key` / env `OPENSURF_OPENAI_API_KEY`.

Unconfigured or failing → no report box, error logged, ingest unaffected.

## Public surface

- `/spots` — all spots with today's score, "today's pick" banner
- `/spot?spot=<slug>&day=<YYYY-MM-DD>` — hourly table, SVG tide curve,
  report, cams
- `/cams` — cam directory; every cam links out, embeds only with consent
- `GET /api/method/opensurf.api.spots|forecast|best|cams` — Guest-permitted
  JSON; `forecast` takes `spot` (slug), `cams` an optional spot filter

## Tides

BMKG `pelabuhan` files provide ~24h of hourly tide metres from forecast day
1 plus 3-hourly values for days 2–4. `scoring.attach_tides` normalizes them
onto a 0–1 range (between the day's low and high) per hour; the spot page
renders the raw metres as an SVG curve with low/high annotations. Early
local-morning hours can lack tide data (BMKG forecast days start at 00:00
UTC = 08:00 WITA) — those cells render "–" and the tide component drops
out of scoring per the rule above.

## Cam consent states

`link` (default — external link only), `embed_youtube` (operator-consented,
`youtube-nocookie.com` behind click-to-load), `embed_direct` (partner/own
HLS). All 21 seeded cams ship as `link`; nothing external loads without a
user action (N1).

## Attribution

Rendered on every page footer: Open-Meteo CC BY 4.0 notice and
"Sumber: BMKG" + the waters/port names and issue time carried in the
snapshot. Keep it intact — it's the license deal.

## Tests

```
bench --site <site> run-tests --app opensurf
```

15 unit tests: direction/arc scoring, tide preference + missing-data
re-weighting, day aggregation, BMKG compass-name→degrees mapping and row
normalization. No network — provider modules are tested on fixed payloads.
