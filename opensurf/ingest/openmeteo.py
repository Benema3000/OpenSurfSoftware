# Copyright (c) 2026, Open Surf Software contributors
# For license information, please see license.txt

"""Open-Meteo marine + weather ingest (CC BY 4.0, free non-commercial, keyless).

Two calls per spot: the marine endpoint (swell/wind-wave/sea level/SST) and
the standard forecast endpoint (10 m wind). Both are merged into one flat
hourly row list keyed on the spot's local timezone.
"""

from datetime import UTC, datetime

import requests

MARINE_URL = "https://marine-api.open-meteo.com/v1/marine"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
TIMEOUT_SECONDS = 30
FORECAST_DAYS = 8

MARINE_HOURLY = [
	"swell_wave_height",
	"swell_wave_direction",
	"swell_wave_period",
	"secondary_swell_wave_height",
	"secondary_swell_wave_direction",
	"secondary_swell_wave_period",
	"wave_height",
	"wave_direction",
	"wave_period",
	"sea_level_height_msl",
	"sea_surface_temperature",
]
WEATHER_HOURLY = ["wind_speed_10m", "wind_direction_10m", "wind_gusts_10m"]

# Flat hourly keys in the stored rows.
KEY_MAP = {
	"swell_wave_height": "swell_height",
	"swell_wave_direction": "swell_dir",
	"swell_wave_period": "swell_period",
	"secondary_swell_wave_height": "swell2_height",
	"secondary_swell_wave_direction": "swell2_dir",
	"secondary_swell_wave_period": "swell2_period",
	"wave_height": "wave_height",
	"wave_direction": "wave_dir",
	"wave_period": "wave_period",
	"sea_level_height_msl": "sea_level",
	"sea_surface_temperature": "sst",
	"wind_speed_10m": "wind_speed",
	"wind_direction_10m": "wind_dir",
	"wind_gusts_10m": "wind_gust",
}


def _get(url: str, params: dict) -> dict:
	response = requests.get(url, params=params, timeout=TIMEOUT_SECONDS)
	response.raise_for_status()
	return response.json()


def fetch_spot(latitude: float, longitude: float, timezone: str) -> dict:
	"""Fetch and merge marine + weather hourly rows for one coordinate."""
	marine = _get(
		MARINE_URL,
		{
			"latitude": latitude,
			"longitude": longitude,
			"hourly": ",".join(MARINE_HOURLY),
			"timezone": timezone,
			"forecast_days": FORECAST_DAYS,
		},
	)
	weather = _get(
		WEATHER_URL,
		{
			"latitude": latitude,
			"longitude": longitude,
			"hourly": ",".join(WEATHER_HOURLY),
			"wind_speed_unit": "kn",
			"timezone": timezone,
			"forecast_days": FORECAST_DAYS,
		},
	)

	merged: dict[str, dict] = {}
	for source in (marine, weather):
		hourly = source.get("hourly") or {}
		times = hourly.get("time") or []
		for idx, ts in enumerate(times):
			row = merged.setdefault(ts, {"time": ts})
			for remote, local in KEY_MAP.items():
				values = hourly.get(remote)
				if values is not None and idx < len(values):
					row[local] = values[idx]

	return {
		"fetched_at": datetime.now(UTC).isoformat(timespec="seconds"),
		"hours": [merged[ts] for ts in sorted(merged)],
	}
