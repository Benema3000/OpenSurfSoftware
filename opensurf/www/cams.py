# Copyright (c) 2026, Open Surf Software contributors
# For license information, please see license.txt

import frappe

from opensurf import api

no_cache = 1


def get_context(context) -> None:
	rows = api.cams()
	by_spot: dict[str, list] = {}
	for row in rows:
		by_spot.setdefault(row["spot"], []).append(row)
	context.update(
		{
			"title": "Surf cams — Open Surf",
			"by_spot": sorted(by_spot.items()),
			"show_sidebar": False,
		}
	)
