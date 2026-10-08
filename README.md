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

## Roadmap sketch

1. `Surf Spot` + `Surf Cam` DocTypes, seed data for ~20 Bali breaks
2. Scheduled ingest: Open-Meteo marine+wind, BMKG maritime forecast
3. Tide prediction for each spot
4. Per-spot hourly surf score (swell direction/size/period vs. spot envelope,
   offshore wind, tide window) → daily best-spot pick
5. Public web pages: spot map, spot forecast, cam directory — no auth
6. Later: community spot reports, own cams at partner locations

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
