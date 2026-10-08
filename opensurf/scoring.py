# Copyright (c) 2026, Open Surf Software contributors
# For license information, please see license.txt

"""Per-spot surf scoring — the layer that turns a wave forecast into a surf
forecast.

Every spot declares an ideal envelope (swell direction/height/period bands,
offshore wind band, tide preference). ``score_hour`` grades one forecast hour
against that envelope; ``score_day`` collapses a day's hours into a day score
and a best-window pick. Pure functions over plain dicts — no database, no
network — so the whole engine is unit-testable without a site.
"""

from __future__ import annotations

DAYLIGHT_HOURS = range(6, 19)  # 06:00-18:00 local — surfable window in Bali

WEIGHTS = {
	"swell_dir": 0.25,
	"swell_size": 0.25,
	"swell_period": 0.15,
	"wind": 0.20,
	"tide": 0.15,
}

# How far outside the ideal direction band a component still scores >0, in degrees.
DIR_GRACE_DEG = 45
# Wind speed (kn) above which even offshore wind stops being a plus.
WIND_OK_KN = 15
WIND_BAD_KN = 24

TIDE_BANDS = {
	"low": (0.0, 0.35),
	"mid": (0.35, 0.7),
	"high": (0.7, 1.01),
	"low to mid": (0.0, 0.55),
	"mid to high": (0.45, 1.01),
}


def _norm_deg(deg: float | None) -> float | None:
	return None if deg is None else deg % 360


def _arc_dist(deg: float, lo: float, hi: float) -> float:
	"""Shortest arc distance in degrees from ``deg`` to the ``lo``-``hi`` band.

	The band may wrap north (lo > hi, e.g. 320-40). Returns 0 when inside.
	"""
	deg, lo, hi = deg % 360, lo % 360, hi % 360
	if lo <= hi:
		if lo <= deg <= hi:
			return 0.0
		return min((deg - hi) % 360, (lo - deg) % 360)
	if deg >= lo or deg <= hi:
		return 0.0
	return min((deg - hi) % 360, (lo - deg) % 360)


def _arc_score(deg: float | None, lo: float | None, hi: float | None) -> float | None:
	if deg is None or lo is None or hi is None:
		return None
	dist = _arc_dist(deg, lo, hi)
	return max(0.0, 1.0 - dist / DIR_GRACE_DEG)


def _size_score(height: float | None, lo: float | None, hi: float | None) -> float | None:
	if height is None:
		return None
	if lo is None or hi is None:
		return 1.0
	if lo <= height <= hi:
		return 1.0
	if height < lo:
		return max(0.0, height / lo) if lo else 0.0
	return max(0.0, 1.0 - (height - hi) / hi)


def _period_score(period: float | None, period_min: float | None) -> float | None:
	if period is None:
		return None
	if not period_min:
		return 1.0
	return min(1.0, period / period_min)


def _wind_score(
	wind_dir: float | None,
	lo: float | None,
	hi: float | None,
	speed_kn: float | None,
	gust_kn: float | None,
) -> float | None:
	if wind_dir is None:
		return None
	dist = _arc_dist(wind_dir, lo or 0, hi or 0) if lo is not None and hi is not None else None
	# Offshore band scores 1.0, decaying to cross-shore at the grace edge;
	# directly onshore (the arc opposite the offshore band) scores lowest.
	if dist is None:
		direction = 0.7
	elif lo is None or hi is None:
		direction = 0.7
	elif dist == 0:
		direction = 1.0
	else:
		mid = ((lo + hi) / 2) % 360 if lo <= hi else ((lo + hi + 360) / 2) % 360
		onshore_arc = _arc_dist(wind_dir, (mid + 180 - 45) % 360, (mid + 180 + 45) % 360)
		if onshore_arc == 0:
			direction = 0.15
		else:
			direction = 0.55

	speed = max(speed_kn or 0.0, gust_kn or 0.0)
	if speed <= WIND_OK_KN:
		strength = 1.0
	elif speed >= WIND_BAD_KN:
		strength = 0.3
	else:
		strength = 1.0 - 0.7 * (speed - WIND_OK_KN) / (WIND_BAD_KN - WIND_OK_KN)
	return direction * strength


def _tide_score(preference: str | None, level: float | None, trend: float | None) -> float:
	"""Score the tide: band match on normalized level plus trend for
	Incoming/Outgoing prefs. ``level`` is 0..1 across the day's range."""
	pref = (preference or "any").strip().lower()
	if level is None:
		# No tide data: only 'Any' spots are tide-proof; other prefs leave the
		# component out of the weights rather than getting free credit.
		return 1.0 if pref == "any" else None
	if pref == "any":
		return 1.0
	if pref == "incoming":
		return 1.0 if (trend or 0) > 0 else 0.35
	if pref == "outgoing":
		return 1.0 if (trend or 0) < 0 else 0.35
	band = TIDE_BANDS.get(pref)
	if not band:
		return 1.0
	lo, hi = band
	if lo <= level <= hi:
		return 1.0
	outside = lo - level if level < lo else level - hi
	return max(0.0, 1.0 - outside / 0.35)


def score_hour(envelope: dict, hour: dict) -> dict:
	"""Grade one forecast hour against the spot envelope → 0-10 + breakdown."""
	parts = {
		"swell_dir": _arc_score(
			hour.get("swell_dir"),
			envelope.get("ideal_swell_dir_min"),
			envelope.get("ideal_swell_dir_max"),
		),
		"swell_size": _size_score(
			hour.get("swell_height"),
			envelope.get("ideal_swell_height_min"),
			envelope.get("ideal_swell_height_max"),
		),
		"swell_period": _period_score(hour.get("swell_period"), envelope.get("ideal_swell_period_min")),
		"wind": _wind_score(
			hour.get("wind_dir"),
			envelope.get("offshore_wind_dir_min"),
			envelope.get("offshore_wind_dir_max"),
			hour.get("wind_speed"),
			hour.get("wind_gust"),
		),
		"tide": _tide_score(envelope.get("tide_preference"), hour.get("tide_level"), hour.get("tide_trend")),
	}
	present = {k: v for k, v in parts.items() if v is not None}
	if not present:
		return {"score": None, "parts": parts}
	weight_total = sum(WEIGHTS[k] for k in present)
	score = sum(parts[k] * WEIGHTS[k] for k in present) / weight_total
	return {"score": round(score * 10, 1), "parts": parts}


def attach_tides(hours: list[dict], tide_rows: list[dict]) -> None:
	"""Merge tide level+trend into forecast hours in place.

	``tide_rows`` are {time, tide} entries (spot-local time, metres). Each hour
	gets ``tide_level`` normalized 0..1 against the day's min/max and
	``tide_trend`` as the change vs the previous reading.
	"""
	by_day: dict[str, list[tuple[str, float]]] = {}
	for row in tide_rows:
		if row.get("tide") is not None:
			by_day.setdefault(row["time"][:10], []).append((row["time"], float(row["tide"])))

	lookup: dict[str, tuple[float, float]] = {}
	for _day, rows in by_day.items():
		rows.sort()
		lo = min(v for _, v in rows)
		hi = max(v for _, v in rows)
		span = hi - lo or 1.0
		for i, (ts, value) in enumerate(rows):
			level = (value - lo) / span
			trend = value - rows[i - 1][1] if i else 0.0
			lookup[ts] = (level, trend)

	for hour in hours:
		ts = (hour.get("time") or "").replace("T", " ")
		if ts in lookup:
			hour["tide_level"], hour["tide_trend"] = lookup[ts]


def score_day(hours: list[dict], envelope: dict) -> dict:
	"""Score every hour, then roll daylight hours into a day verdict."""
	scored = []
	for hour in hours:
		result = score_hour(envelope, hour)
		scored.append({**hour, **result})

	daylight = [
		h
		for h in scored
		if h.get("score") is not None and int((h.get("time") or "  ")[11:13] or 0) in DAYLIGHT_HOURS
	]
	best = sorted(daylight, key=lambda h: h["score"], reverse=True)
	day_score = round(sum(h["score"] for h in best[:4]) / 4, 1) if best else None
	return {
		"day_score": day_score,
		"best_hours": best[:3],
		"hours": scored,
	}
