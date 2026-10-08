# Architecture Decisions — Open Surf Software

## ADR-001: Frappe framework as the whole backend — accepted (2026-10-08)

Context: need a spot/cam registry, scheduled ingest, a small public API and
server-rendered public pages. Owner already runs a Frappe bench and the team
knows the stack.

Decision: single Frappe app `opensurf`. DocTypes own the registries,
`scheduler_events` own ingest jobs, whitelisted methods expose the read API,
Frappe web pages/templates serve the public UI. No separate service.

Consequence: heavier than Flask for this scope, but zero new stack to learn
or operate; Desk gives free admin UI for curating spots/cams.

## ADR-002: Data sources — Open-Meteo primary, BMKG secondary — accepted (2026-10-08)

Context: forecast must be free for a non-commercial product forever.

Decision: Open-Meteo Marine + Weather APIs (keyless, ≤10k calls/day, CC BY
4.0) as the primary swell+wind source; BMKG maritim/inawaves APIs as the
Indonesia-local second source and for tide/warnings where available. Tides
per spot from a global tide atlas (GOT via pyTMD or FES via pyfes) where
BMKG coverage is insufficient. Spot base data from OpenStreetMap
`sport=surfing`, hand-curated.

Alternatives rejected: Stormglass/WorldTides (paid tiers needed),
scraping Surfline/Magicseaweed (ToS + ethics), running own wave models from
WW3 GRIB (compute/storage overkill for v1; revisit if accuracy demands).

Consequence: every forecast response carries source attribution fields;
ingest is isolated behind a small provider module per source so a source
swap never touches scoring.

Amendment (2026-10-08, v1): BMKG `pelabuhan` port forecasts turned out to
carry hourly `tides` in meters, so v1 tides come from BMKG alone — each
`Surf Spot` maps to its nearest port via `bmkg_port_code` (Gilimanuk,
Padangbai, Benoa, Sanur, Nusa Penida, Kusamba...). The tide atlas stays in
the back pocket for regions BMKG doesn't cover.

## ADR-003: Cam model — link-first directory, consent-gated embeds — accepted (2026-10-08)

Context: Surfline's moat is its cam network. We cannot hot-embed other
people's streams, and YouTube embeds conflict with the no-tracking promise.

Decision: `Surf Cam` records a `stream_type` of `link | youtube | hls |
webrtc` plus a `consent` state. Every cam renders as an external link from
day one. `youtube` embeds use `youtube-nocookie.com` behind a click-to-load
facade (nothing contacts Google before a click) and only where the operator
consented. `hls`/`webrtc` = partner feed or own cam via MediaMTX
(RTSP in → HLS/WHEP out), also consent-gated.

Consequence: the cam feature is useful with zero permissions on day one and
upgrades cam-by-cam. Privacy claim survives embedding.

## ADR-004: No accounts, no tracking, forecasts served from cache — accepted (2026-10-08)

Context: core product promise.

Decision: all read surfaces are Guest-permission public; no cookies, no
analytics (at most self-hosted, aggregate-only counter later — undecided).
Forecast reads are served from server-side snapshots (JSON files/cache
written by scheduled ingest), never proxied live to upstream APIs — keeps
upstream volume flat, protects user privacy, and satisfies N5 graceful
degradation.

Consequence: anything needing identity (community reports, alerts) is
explicitly out of v1 and will need a fresh privacy decision.

## ADR-005: LLM-generated report is optional, endpoint-agnostic, staleness-gated — accepted (2026-10-08)

Context: a good forecast page wants 2–4 sentences of human text plus a
forecast-quality read ("do the sources agree"). Writing rules for that
produces robotic copy; an LLM does it well — but must not become a hard
dependency or a tracking channel.

Decision: `opensurf/report.py` calls one OpenAI-compatible chat-completions
endpoint per spot per (max 6h-stale) day. Endpoint, model and key come from
`Open Surf Settings` or site config/env — any compatible provider works
(OpenAI, Z.AI/GLM, self-hosted vLLM...). The model receives only forecast
numbers — no user data exists to send. Output is stored inside the forecast
snapshot (`report` key) with model name and generation time.

Consequence: unconfigured → pages just show no report box; failures log and
never break ingest. Cost stays flat (~1 call per spot per 6h at most). The
"small text" feature degrades to numbers-only gracefully.
