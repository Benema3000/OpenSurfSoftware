# Copyright (c) 2026, Open Surf Software contributors
# For license information, please see license.txt

"""Idempotent seed of the Bali spot registry and cam directory.

Data lives in ``opensurf/data/bali_*.json`` — the repo is the source of truth;
``run()`` upserts so re-running pulls in corrections without duplicating rows.
"""

import json
from pathlib import Path

import frappe

DATA_DIR = Path(__file__).resolve().parent / "data"


def _load(name: str) -> list[dict]:
	return json.loads((DATA_DIR / name).read_text())


def _upsert(doctype: str, key_field: str, rows: list[dict]) -> tuple[int, int]:
	created = updated = 0
	for row in rows:
		key = row[key_field]
		if frappe.db.exists(doctype, key):
			doc = frappe.get_doc(doctype, key)
			changed = False
			for field, value in row.items():
				if doc.get(field) != value:
					doc.set(field, value)
					changed = True
			if changed:
				doc.save(ignore_permissions=True)
				updated += 1
		else:
			doc = frappe.new_doc(doctype)
			doc.update(row)
			doc.insert(ignore_permissions=True)
			created += 1
	return created, updated


def run() -> dict[str, tuple[int, int]]:
	"""Seed spots first (cams link to them), then cams. Safe to re-run."""
	spots = _upsert("Surf Spot", "spot_name", _load("bali_spots.json"))
	cams = _upsert("Surf Cam", "cam_name", _load("bali_cams.json"))
	frappe.db.commit()
	result = {"surf_spot": spots, "surf_cam": cams}
	print(f"opensurf seed: {result}")
	return result
