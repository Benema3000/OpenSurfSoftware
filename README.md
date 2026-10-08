# Open Surf Software (OSS)

*Yes — OSS is also the pun. Open source software for open surfing.*

Free, privacy-respecting surf forecasts and surf cams. **Bali first.**
No tracking, no accounts, no ads, no paywall — forever.

An open alternative to surfline.com, built on the
[Frappe framework](https://frappe.io/framework).

## Status

Early scaffold. Nothing to see yet — the roadmap below is the plan, not the
product. Research notes that seeded this project live in
[REQUIREMENTS.md](REQUIREMENTS.md) and
[ARCHITECTURE_DECISIONS.md](ARCHITECTURE_DECISIONS.md).

## Principles

- **Free forever, open source (AGPL-3.0).** No commercial tier, ever.
- **No data collection.** No analytics, no cookies, no login needed to view
  anything. Third-party embeds (e.g. YouTube cams) load only after an explicit
  click, via `youtube-nocookie.com`.
- **Honest attribution.** Forecast data is public-model data — we show its
  sources, not pretend we own them.

## Where the data comes from

| Data | Source | Terms |
|---|---|---|
| Waves, swell, wind | [Open-Meteo](https://open-meteo.com) Marine + Weather APIs (NOAA WaveWatch III, ECMWF, Copernicus models) | Free non-commercial, no key, CC BY 4.0 attribution |
| Indonesian maritime forecast, tides, warnings | [BMKG](https://maritim.bmkg.go.id) (Indonesian met service) | Free, "Sumber: BMKG" attribution, official API only |
| Tide prediction | Global tide atlases (NASA GOT / FES) via `pyTMD`/`pyfes` | Free for non-commercial |
| Surf spots | OpenStreetMap `sport=surfing` + community curation | ODbL |
| Surf cams | Operator links/embeds with consent; own cams via MediaMTX where possible | Per-cam consent tracked in the cam registry |

## Cams

The cam registry is a **link-first directory**: every known cam gets a link,
no permission needed. Embeds (YouTube `nocookie` or direct HLS/WebRTC feeds
via MediaMTX) only switch on with the cam operator's consent, which the
registry records per cam.

## Status

v1 works end to end: 23 seeded Bali spots + 21 cams, hourly Open-Meteo +
BMKG ingest into snapshots, BMKG port tides, per-hour/per-day surf scores
with a daily best-spot pick, optional LLM-written report + confidence per
spot (any OpenAI-compatible endpoint, off by default), and public pages —
`/spots`, `/spot?spot=…`, `/cams` — plus a Guest JSON API
(`opensurf.api.spots|forecast|best|cams`). No auth, no tracking, no cookies.

## Roadmap sketch

- Cam operator outreach → flip consenting cams from `link` to
  `embed_youtube`/`embed_direct`
- Community spot reports (needs a fresh privacy decision — see ADR-004)
- Own/partner cams via MediaMTX (RTSP in → HLS/WHEP out)
- Forecast calibration against cam observations; GEBCO bathymetry for
  swell→breaking-height correction

## Installation

Developed on Frappe 16. With [bench](https://github.com/frappe/bench):

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app https://github.com/Benema3000/OpenSurfSoftware --branch main
bench --site your.site install-app opensurf
```

## Contributing

Too early for PRs to be useful, but issues are open if you surf Bali and want
to shape this. Standard Frappe conventions; `pre-commit` (ruff, eslint,
prettier, pyupgrade) is configured.

## License

AGPL-3.0 — see [license.txt](license.txt). Forks stay free, that's the point.
