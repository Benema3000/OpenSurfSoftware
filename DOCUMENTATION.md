# Documentation — Open Surf Software

Early scaffold — this page records the planned shape; sections fill in as the
code lands. Requirements: [REQUIREMENTS.md](REQUIREMENTS.md). Decisions:
[ARCHITECTURE_DECISIONS.md](ARCHITECTURE_DECISIONS.md).

## Layout

```
opensurf/
  opensurf/            app module
    open_surf_software/  module dir (DocTypes live here)
    hooks.py           scheduler_events for ingest jobs go here
    templates/pages/   public web pages
  .github/workflows/   ci.yml (unittest), linter.yml (semgrep + pip-audit)
```

## Planned pieces

- **DocTypes**: `Surf Spot` (geo + condition envelope, F1/F2),
  `Surf Cam` (stream_type + consent, F7), `Cam Provider`.
- **Ingest** (`opensurf/ingest/`): one provider module per source
  (`openmeteo.py`, `bmkg.py`, `tides.py`) writing JSON snapshots per spot —
  file cache, never live-proxying user requests (ADR-004).
- **Scoring** (`opensurf/scoring.py`): hourly score per spot vs its
  condition envelope; daily best-spot pick. Pure functions over forecast
  dicts — testable without a site.
- **API**: whitelisted read methods (`api.spots`, `api.forecast`,
  `api.cams`) — Guest-permitted, cached.
- **Web**: `templates/pages/` spot map (Leaflet + OSM), spot forecast page,
  cam directory.

## Tests

`bench --site <site> run-tests --app opensurf`. Scoring and provider parsing
get unit tests; ingest gets fixture-replay tests (no network).
