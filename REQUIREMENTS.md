# Requirements — Open Surf Software

Numbered, traceable requirements. IDs stay stable; status in brackets.
Source: product research 2026-10-08 (`/workspace/surf-forecast-research-2026-10-08.md`)
plus owner decisions the same day (open source, free forever, link-first cams).

## Functional

- [F1] Maintain a registry of surf spots: name, geo position, region, break
  type, wave direction, bottom, experience level, hazards, crowd notes.
- [F2] Per spot, store the ideal-condition envelope used for scoring:
  preferred swell direction/size/period range, offshore wind directions,
  preferred tide window (e.g. mid-high, incoming).
- [F3] Scheduled ingest of marine forecast (swell/wind-wave height, direction,
  period; primary+secondary swell) and surface wind forecast per spot from
  Open-Meteo, cached server-side.
- [F4] Scheduled ingest of BMKG maritime forecast for the relevant Indonesian
  water areas (wave height, wind, tide, warnings) as a second opinion/source.
- [F5] Tide height prediction per spot (harmonic constituents via a global
  tide atlas, or BMKG tide field) — no per-station gauge dependency.
- [F6] Compute a per-spot hourly surf score from F2–F5 plus a daily
  best-spot recommendation.
- [F7] Maintain a cam registry: spot link, provider, stream type
  (link / youtube / hls / webrtc), URL, consent status, health.
  Every cam is always at least an external link; embeds require recorded
  operator consent.
- [F8] Public, unauthenticated read API: spot list, per-spot forecast series
  + score + tide curve, cam list.
- [F9] Public web UI: spot map, per-spot forecast page (charts + score +
  tide), cam directory page. Map via OpenStreetMap tiles.

## Non-functional

- [N1] No personal data collection: no analytics, no tracking, no cookies,
  no accounts required for viewing. Third-party content loads only on
  explicit user action (click-to-load facade; `youtube-nocookie.com`).
- [N2] Free forever, no commercial use of the service → only non-commercial
  data sources qualify. Attribution per source terms (Open-Meteo CC BY 4.0,
  "Sumber: BMKG").
- [N3] Upstream API volume stays small: fetch once per unique spot
  coordinate per interval, cache, never proxy user traffic to upstream APIs.
- [N4] AGPL-3.0 licensed; all dependencies compatible.
- [N5] Graceful degradation: if an upstream source fails, the app keeps
  serving the last good forecast, marked with its fetch time.

## Scope

- v1 geography: Bali (Bukit peninsula, west/east coasts, Nusa islands).
  The model is region-agnostic; Bali is curation scope, not a code limit.
- Out of scope for v1: user accounts, community reports, own camera
  hardware, mobile apps, monetisation of any kind.
