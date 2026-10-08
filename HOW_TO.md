# How To — Open Surf Software

## Install

See [README.md](README.md#installation). `after_install` seeds the Bali
spots and cams from `opensurf/data/` automatically — no fixture step.

## Curate spots and cams

In Desk (admin only; the public site never needs auth):

- `Surf Spot` — set `is_active` to show/hide, adjust the scoring envelope
  fields, or point `bmkg_area_code`/`bmkg_port_code` at a nearer waters
  area or port. Codes come from
  `https://maritim.bmkg.go.id/marine2026-data/meta/area_province.json` and
  the port meta file next to it.
- `Surf Cam` — everything renders as an external link. Only flip `consent`
  to `embed_youtube`/`embed_direct` after the operator agreed in writing.
- `Open Surf Settings` — LLM config lives here (see below).

## Forecast refresh

Runs hourly via `scheduler_events` → `opensurf.ingest.refresh_all`. To
force it:

```bash
bench --site <site> execute opensurf.ingest.refresh_all
```

Snapshots are JSON under the site `files` dir; inspect one with
`opensurf.ingest.snapshots.read("<slug>")` from `bench console`.

## Enable the LLM report

1. Desk → `Open Surf Settings`: tick `enable_llm_reports`, set
   `openai_base_url` (e.g. `https://api.openai.com/v1` — any
   OpenAI-compatible endpoint works) and `openai_model`.
2. Key priority: env `OPENSURF_OPENAI_API_KEY` → site config key
   `opensurf_openai_api_key` → the `openai_api_key` password field.
3. Reports regenerate when missing or older than 6h, inside the same
   hourly job. To regenerate everything now:

```python
from opensurf import report
for n in frappe.get_all("Surf Spot", filters={"is_active": 1}, pluck="name"):
    report.refresh_if_stale(frappe.get_doc("Surf Spot", n))
```

Failures land in Error Log as `opensurf report failed for <spot>` and never
break ingest.

## Tests and lint

```bash
bench --site <site> run-tests --app opensurf
pre-commit run --all-files   # inside apps/opensurf
```
