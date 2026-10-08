# Copyright (c) 2026, Open Surf Software contributors
# For license information, please see license.txt

import frappe

from opensurf import api, helpers

no_cache = 1


def get_context(context) -> None:
	slug = frappe.form_dict.get("spot") or ""
	data = api.forecast(slug)

	days = sorted(data["days"])
	active_day = frappe.form_dict.get("day") or (days[0] if days else None)
	day_data = data["days"].get(active_day) or {"hours": []}
	tide_rows = [r for r in data["tides"] if r["time"].startswith(active_day or "")]

	context.update(
		{
			"title": f"{data['spot']['spot_name']} — Open Surf",
			"spot": data["spot"],
			"days": [
				{"day": d, "label": helpers.day_label(d), "score": data["days"][d]["day_score"]} for d in days
			],
			"active_day": active_day,
			"day_score": day_data.get("day_score"),
			"best_hours": day_data.get("best_hours") or [],
			"hours": day_data.get("hours") or [],
			"report": data.get("report"),
			"cams": data.get("cams") or [],
			"bmkg_area": data.get("bmkg_area"),
			"fetched_at": data.get("fetched_at"),
			"errors": data.get("errors"),
			"tide_svg": helpers.tide_svg(tide_rows),
			"helpers": helpers,
			"show_sidebar": False,
		}
	)
