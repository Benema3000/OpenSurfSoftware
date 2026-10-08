# Copyright (c) 2026, Open Surf Software contributors
# For license information, please see license.txt

"""LLM-written daily surf report + forecast-confidence note.

One OpenAI-compatible chat-completions call per spot per day produces the
two things a model is genuinely good at here: a short human-readable report
("small text") and a forecast-quality read ("confidence") that compares the
Open-Meteo and BMKG sources and flags disagreement or marginal setups.

The endpoint is configured in Open Surf Settings (base URL + model + key),
or via site config ``opensurf_openai_api_key`` / env
``OPENSURF_OPENAI_API_KEY``. When unconfigured the app simply shows no
report — never an error page.
"""

from __future__ import annotations

import copy
import json
import os
from datetime import UTC, datetime
from zoneinfo import ZoneInfo

import frappe
import requests

from opensurf import api, scoring
from opensurf.ingest import snapshots

REQUEST_TIMEOUT_SECONDS = 60
REPORT_MAX_AGE_HOURS = 6

PROMPT = """You write the daily surf report for {spot}, {region}, Bali.
Tone: like a good local friend briefing another surfer. Plain language, no
hype, no emoji, 2-4 sentences. Mention swell size/period/direction trend, wind,
tide, and which hours look best. If it looks flat or blown out, say so plainly.

Spot character: {character}
Today's scored hours (local time, score 0-10): {hours}
BMKG human forecast for the area (second opinion): {bmkg}

Also judge forecast quality: do the two sources roughly agree, and is the
setup clean (steady swell/wind) or marginal? Pick confidence "high",
"medium" or "low" with a few-word reason.

Answer as JSON only: {{"report": "...", "confidence": "high|medium|low", "confidence_note": "..."}}"""


def _api_key(settings) -> str | None:
	return (
		os.environ.get("OPENSURF_OPENAI_API_KEY")
		or frappe.conf.get("opensurf_openai_api_key")
		or (settings.get_password("openai_api_key") if settings else None)
	)


def _configured() -> tuple[bool, object | None, str | None]:
	try:
		settings = frappe.get_single("Open Surf Settings")
	except Exception:
		return False, None, None
	key = _api_key(settings)
	return bool(settings.enable_llm_reports and key), settings, key


def _chat(settings, key: str, prompt: str) -> dict:
	url = f"{settings.openai_base_url.rstrip('/')}/chat/completions"
	response = requests.post(
		url,
		headers={"Authorization": f"Bearer {key}"},
		json={
			"model": settings.openai_model,
			"messages": [{"role": "user", "content": prompt}],
			"response_format": {"type": "json_object"},
		},
		timeout=REQUEST_TIMEOUT_SECONDS,
	)
	response.raise_for_status()
	return json.loads(response.json()["choices"][0]["message"]["content"])


def _compact_hours(scored_hours: list[dict], day: str) -> list[dict]:
	return [
		{
			"time": h["time"][11:16],
			"score": h.get("score"),
			"swell_m": h.get("swell_height"),
			"swell_s": h.get("swell_period"),
			"swell_deg": h.get("swell_dir"),
			"wind_kn": h.get("wind_speed"),
			"wind_deg": h.get("wind_dir"),
			"tide": h.get("tide_level"),
		}
		for h in scored_hours
		if h.get("time", "").startswith(day) and 6 <= int(h["time"][11:13])
	]


def generate_for_spot(spot, scored_day: dict, day: str) -> dict | None:
	"""Generate (and snapshot-store) one day's report for a spot."""
	enabled, settings, key = _configured()
	if not enabled:
		return None

	bmkg_note = "unavailable"
	snapshot = snapshots.read(spot.slug) or {}
	area = (snapshot.get("bmkg") or {}).get("area")
	if area:
		today = [r for r in area.get("hours", []) if r["time"].startswith(day)]
		if today:
			heights = [r["wave_height"] for r in today if r.get("wave_height") is not None]
			winds = {r["wind_from"] for r in today if r.get("wind_from")}
			bmkg_note = (
				f"waves {min(heights)}-{max(heights)} m, wind from {', '.join(sorted(winds))}"
				if heights
				else "no wave heights today"
			)

	character = ", ".join(
		str(v)
		for v in (
			spot.wave_direction,
			f"{spot.break_type} over {spot.bottom}" if spot.bottom else spot.break_type,
			f"for {spot.experience_level}" if spot.experience_level else "",
		)
		if v
	)
	prompt = PROMPT.format(
		spot=spot.spot_name,
		region=spot.region,
		character=character,
		hours=json.dumps(_compact_hours(scored_day["hours"], day)),
		bmkg=bmkg_note,
	)
	try:
		answer = _chat(settings, key, prompt)
	except Exception as exc:
		frappe.log_error(f"opensurf report failed for {spot.name}: {exc}")
		return None

	report = {
		"date": day,
		"generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
		"model": settings.openai_model,
		"text": answer.get("report"),
		"confidence": answer.get("confidence"),
		"confidence_note": answer.get("confidence_note"),
	}
	snapshot["report"] = report
	snapshots.write(spot.slug, snapshot)
	return report


def refresh_if_stale(spot) -> dict | None:
	"""Regenerate today's report when missing or older than
	REPORT_MAX_AGE_HOURS. Called after ingest so the report reflects the
	fresh forecast."""
	enabled, _settings, _key = _configured()
	if not enabled:
		return None

	snapshot = snapshots.read(spot.slug) or {}
	hours = ((snapshot.get("openmeteo") or {}).get("hours")) or []
	if not hours:
		return None

	today = datetime.now(ZoneInfo(spot.forecast_timezone)).strftime("%Y-%m-%d")
	existing = snapshot.get("report") or {}
	if existing.get("date") == today:
		age = (datetime.now(UTC) - datetime.fromisoformat(existing["generated_at"])).total_seconds() / 3600
		if age < REPORT_MAX_AGE_HOURS:
			return None

	day_hours = [h for h in hours if h["time"].startswith(today)]
	if not day_hours:
		return None

	scored = copy.deepcopy(day_hours)
	scoring.attach_tides(scored, ((snapshot.get("bmkg") or {}).get("port") or {}).get("hours") or [])
	envelope = {f: spot.get(f) for f in api._ENVELOPE_FIELDS}
	return generate_for_spot(spot, scoring.score_day(scored, envelope), today)
