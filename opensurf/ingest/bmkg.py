# Copyright (c) 2026, Open Surf Software contributors
# For license information, please see license.txt

"""BMKG maritime forecast ingest (maritim.bmkg.go.id, "Sumber: BMKG").

Two products per spot, both human-forecaster issued and free with attribution:

- ``perairan/<area>.json`` — waters-area forecast: hourly day-1 and 3-hourly
  day 2-4 wave height, wind, weather, currents.
- ``pelabuhan/<port>.json`` — port forecast: same shape plus an hourly
  ``tides`` field in metres, used as the tide curve for nearby spots.

Times arrive as ``YYYY-MM-DD HH:MM UTC`` and are stored converted into the
spot's local timezone, same as the Open-Meteo rows, so sources line up.
"""

from datetime import UTC, datetime
from zoneinfo import ZoneInfo

import requests

BASE_URL = "https://maritim.bmkg.go.id/marine2026-data"
TIMEOUT_SECONDS = 30

# Indonesian 8-point compass names used by BMKG forecasters.
COMPASS_DEG = {
	"utara": 0,
	"timur laut": 45,
	"timur": 90,
	"tenggara": 135,
	"selatan": 180,
	"barat daya": 225,
	"barat": 270,
	"barat laut": 315,
}

DAY_KEYS = ("forecast_day1", "forecast_day2", "forecast_day3", "forecast_day4")


def _get(path: str) -> dict:
	response = requests.get(f"{BASE_URL}/{path}", timeout=TIMEOUT_SECONDS)
	response.raise_for_status()
	return response.json()


def _to_local(ts_utc: str, timezone: str) -> str:
	dt = datetime.strptime(ts_utc, "%Y-%m-%d %H:%M UTC").replace(tzinfo=UTC)
	return dt.astimezone(ZoneInfo(timezone)).strftime("%Y-%m-%d %H:%M")


def _compass_deg(name: str | None) -> int | None:
	return COMPASS_DEG.get((name or "").strip().lower())


def _rows(doc: dict, timezone: str) -> list[dict]:
	rows = []
	for day_key in DAY_KEYS:
		for entry in doc.get(day_key) or []:
			rows.append(
				{
					"time": _to_local(entry["time"], timezone),
					"wave_height": entry.get("wave_height"),
					"wave_cat": entry.get("wave_cat"),
					"wind_from": entry.get("wind_from"),
					"wind_dir": _compass_deg(entry.get("wind_from")),
					"wind_speed": entry.get("wind_speed"),
					"wind_gust": entry.get("wind_gust"),
					"weather": entry.get("weather"),
					"current_speed": entry.get("current_speed"),
					"tide": entry.get("tides"),
				}
			)
	return rows


def fetch_spot(area_code: str | None, port_code: str | None, timezone: str) -> dict:
	"""Fetch area forecast + port tides for one spot. Either code may be empty."""
	out: dict = {"fetched_at": datetime.now(UTC).isoformat(timespec="seconds")}
	if area_code:
		doc = _get(f"perairan/{area_code}.json")
		out["area"] = {
			"code": doc.get("code"),
			"name": doc.get("name"),
			"issued": doc.get("issued"),
			"hours": _rows(doc, timezone),
		}
	if port_code:
		doc = _get(f"pelabuhan/{port_code}.json")
		out["port"] = {
			"code": doc.get("code"),
			"name": doc.get("name"),
			"issued": doc.get("issued"),
			"hours": [r for r in _rows(doc, timezone) if r.get("tide") is not None],
		}
	return out
