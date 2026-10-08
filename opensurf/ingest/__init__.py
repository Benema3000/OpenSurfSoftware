# Copyright (c) 2026, Open Surf Software contributors
# For license information, please see license.txt

"""Scheduled forecast ingest for every active Surf Spot.

Each spot's snapshot is written independently: one failing source or spot
never blocks the others, and a failed refresh leaves the previous snapshot
untouched (N5 graceful degradation).
"""

import frappe

from opensurf.ingest import bmkg, openmeteo, snapshots


def _settings() -> dict:
	doc = frappe.get_single("Open Surf Settings")
	return {
		"openmeteo": bool(doc.openmeteo_enabled),
		"bmkg": bool(doc.bmkg_enabled),
	}


def refresh_spot(spot) -> dict:
	snapshot = snapshots.read(spot.slug) or {
		"spot": spot.name,
		"slug": spot.slug,
		"timezone": spot.forecast_timezone,
	}
	snapshot.pop("errors", None)
	errors = {}
	settings = _settings()

	if settings["openmeteo"]:
		try:
			snapshot["openmeteo"] = openmeteo.fetch_spot(
				spot.latitude, spot.longitude, spot.forecast_timezone
			)
		except Exception as exc:  # upstream outage must not kill the refresh
			errors["openmeteo"] = str(exc)
			frappe.log_error(f"opensurf openmeteo failed for {spot.name}: {exc}")

	if settings["bmkg"] and (spot.bmkg_area_code or spot.bmkg_port_code):
		try:
			snapshot["bmkg"] = bmkg.fetch_spot(
				spot.bmkg_area_code, spot.bmkg_port_code, spot.forecast_timezone
			)
		except Exception as exc:
			errors["bmkg"] = str(exc)
			frappe.log_error(f"opensurf bmkg failed for {spot.name}: {exc}")

	if errors:
		snapshot["errors"] = errors

	snapshots.write(spot.slug, snapshot)
	return errors


def refresh_all() -> None:
	"""Hourly scheduler entry point."""
	from opensurf import report

	for name in frappe.get_all("Surf Spot", filters={"is_active": 1}, pluck="name"):
		spot = frappe.get_doc("Surf Spot", name)
		refresh_spot(spot)
		try:
			report.refresh_if_stale(spot)
		except Exception as exc:
			frappe.log_error(f"opensurf report refresh failed for {spot.name}: {exc}")
	frappe.db.commit()
