# Copyright (c) 2026, Open Surf Software contributors
# For license information, please see license.txt

"""Presentation helpers shared by the www pages: direction arrows, day
labels, and inline-SVG chart builders. Everything renders server-side —
no chart library, no third-party assets."""

from __future__ import annotations

from datetime import date, datetime, timedelta

_ARROWS = "↑↗→↘↓↙←↖"


def deg_arrow(deg: float | None) -> str:
	"""Arrow pointing where the swell/wind travels TO (deg is the FROM direction)."""
	if deg is None:
		return "-"
	return _ARROWS[round(((deg + 180) % 360) / 45) % 8]


def deg_compass(deg: float | None) -> str:
	if deg is None:
		return "-"
	names = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
	return names[round((deg % 360) / 45) % 8]


def day_label(day: str) -> str:
	d = date.fromisoformat(day)
	if d == date.today():
		return "Today"
	if d == date.today() + timedelta(days=1):
		return "Tomorrow"
	return d.strftime("%a %-d %b")


def score_class(score: float | None) -> str:
	if score is None:
		return "score-none"
	if score >= 7:
		return "score-good"
	if score >= 4:
		return "score-ok"
	return "score-poor"


def tide_svg(rows: list[dict], width: int = 640, height: int = 90) -> str:
	"""Inline SVG sparkline of one day's tide readings ({time, tide})."""
	points = [(r["time"], float(r["tide"])) for r in rows if r.get("tide") is not None]
	if len(points) < 2:
		return ""
	lo, hi = min(v for _, v in points), max(v for _, v in points)
	span = (hi - lo) or 1.0
	n = len(points)
	coords = " ".join(
		f"{i * width / (n - 1):.1f},{(height - 8 - (v - lo) / span * (height - 20)):.1f}"
		for i, (_, v) in enumerate(points)
	)
	return (
		f'<svg class="tide-svg" viewBox="0 0 {width} {height}" '
		f'role="img" aria-label="Tide curve">'
		f'<polyline points="{coords}" fill="none" stroke="#2b7cd3" stroke-width="2"/>'
		f'<text x="2" y="{height - 4}" font-size="9" fill="#888">low {lo:.1f} m</text>'
		f'<text x="{width - 70}" y="10" font-size="9" fill="#888">high {hi:.1f} m</text>'
		f"</svg>"
	)


def parse_hour(ts: str) -> datetime:
	return datetime.strptime(ts.replace("T", " "), "%Y-%m-%d %H:%M")
