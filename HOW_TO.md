# How To — Open Surf Software

No operator workflows exist yet — the app is a scaffold.

- Install: see [README.md](README.md#installation).
- Curate spots/cams (once the DocTypes land): via Frappe Desk, `Surf Spot` /
  `Surf Cam` — Desk access is admin-only; the public side never needs auth.
- Force a forecast refresh (planned): `bench --site <site> execute
  opensurf.ingest.refresh_all`
