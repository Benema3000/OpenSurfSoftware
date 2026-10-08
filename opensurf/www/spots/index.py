# Copyright (c) 2026, Open Surf Software contributors
# For license information, please see license.txt

import frappe

from opensurf import api

no_cache = 1


def get_context(context) -> None:
	data = api.best()
	context.update(
		{
			"title": "Open Surf — Bali",
			"spots": data["spots"],
			"best": data["best"],
			"show_sidebar": False,
		}
	)
