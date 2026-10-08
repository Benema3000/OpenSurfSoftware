# Copyright (c) 2026, Open Surf Software contributors
# For license information, please see license.txt

"""Guest-facing read API. Everything here is unauthenticated by design —
the product promise is no accounts (ADR-004). All data is served from
server-side snapshots and the spot/cam registries; nothing proxies upstream.
"""

from __future__ import annotations

import frappe

from opensurf import scoring
from opensurf.ingest import snapshots

SPOT_PUBLIC_FIELDS = [
	"spot_name",
	"slug",
	"region",
	"latitude",
	"longitude",
	"break_type",
	"wave_direction",
	"bottom",
	"experience_level",
	"typical_crowd",
	"description",
	"hazards",
	"forecast_timezone",
]

_ENVELOPE_FIELDS = [
	"ideal_swell_dir_min",
	"ideal_swell_dir_max",
	"ideal_swell_height_min",
	"ideal_swell_height_max",
	"ideal_swell_period_min",
	"offshore_wind_dir_min",
	"offshore_wind_dir_max",
	"tide_preference",
]


def _envelope(spot) -> dict:
	return {f: spot.get(f) for f in _ENVELOPE_FIELDS}


def _spot_row(spot) -> dict:
	return {f: spot.get(f) for f in SPOT_PUBLIC_FIELDS} | {"name": spot.name}


def _tide_rows(snapshot: dict | None) -> list[dict]:
	port = ((snapshot or {}).get("bmkg") or {}).get("port") or {}
	return port.get("hours") or []


def _scored_days(spot, snapshot: dict | None) -> dict[str, dict]:
	"""Score every snapshot day against the spot envelope."""
	hours = list(((snapshot or {}).get("openmeteo") or {}).get("hours") or [])
	if not hours:
		return {}
	scoring.attach_tides(hours, _tide_rows(snapshot))
	days: dict[str, list[dict]] = {}
	for hour in hours:
		days.setdefault(hour["time"][:10], []).append(hour)
	return {day: scoring.score_day(day_hours, _envelope(spot)) for day, day_hours in days.items()}


def _spot_or_404(spot: str):
	name = frappe.db.get_value("Surf Spot", {"slug": spot, "is_active": 1}, "name") or (
		spot if frappe.db.exists("Surf Spot", {"spot_name": spot, "is_active": 1}) else None
	)
	if not name:
		frappe.throw("Unknown surf spot", frappe.NotFound)
	return frappe.get_doc("Surf Spot", name)


@frappe.whitelist(allow_guest=True)
def spots() -> list[dict]:
	"""All active spots with today's day score, for the map/list."""
	out = []
	for name in frappe.get_all("Surf Spot", filters={"is_active": 1}, pluck="name"):
		spot = frappe.get_doc("Surf Spot", name)
		snapshot = snapshots.read(spot.slug)
		days = _scored_days(spot, snapshot)
		today = min(days) if days else None
		row = _spot_row(spot)
		row["today"] = days[today]["day_score"] if today else None
		row["fetched_at"] = ((snapshot or {}).get("openmeteo") or {}).get("fetched_at")
		out.append(row)
	return sorted(out, key=lambda r: (r["today"] is None, -(r["today"] or 0), r["spot_name"]))


@frappe.whitelist(allow_guest=True)
def forecast(spot: str) -> dict:
	"""Full per-spot forecast: scored days, tide rows, BMKG area, cams, report."""
	doc = _spot_or_404(spot)
	snapshot = snapshots.read(doc.slug) or {}
	days = _scored_days(doc, snapshot)
	area = (snapshot.get("bmkg") or {}).get("area") or {}
	return {
		"spot": _spot_row(doc),
		"days": days,
		"tides": _tide_rows(snapshot),
		"bmkg_area": {"name": area.get("name"), "issued": area.get("issued")},
		"report": snapshot.get("report"),
		"cams": cams(spot=doc.name),
		"fetched_at": (snapshot.get("openmeteo") or {}).get("fetched_at"),
		"errors": snapshot.get("errors"),
	}


@frappe.whitelist(allow_guest=True)
def cams(spot: str | None = None) -> list[dict]:
	"""Cam directory. Links always; embed data only for consented cams."""
	filters = {"is_active": 1}
	if spot:
		doc = _spot_or_404(spot)
		filters["spot"] = doc.name
	rows = frappe.get_all(
		"Surf Cam",
		filters=filters,
		fields=["cam_name", "spot", "provider", "stream_type", "url", "consent", "embed_url", "youtube_id"],
		order_by="spot, cam_name",
	)
	for row in rows:
		if row["consent"] != "Embed Granted" or row["stream_type"] == "Link":
			row.pop("embed_url", None)
			row.pop("youtube_id", None)
	return rows


@frappe.whitelist(allow_guest=True)
def best() -> dict:
	"""Today's best-scored spot — the headline pick."""
	rows = spots()
	today = [r for r in rows if r.get("today") is not None]
	return {"best": today[0] if today else None, "spots": rows}
