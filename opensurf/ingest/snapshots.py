# Copyright (c) 2026, Open Surf Software contributors
# For license information, please see license.txt

"""Per-spot forecast snapshots on disk.

Raw upstream responses are normalized into one JSON document per spot under
``sites/<site>/private/files/opensurf/<slug>.json``. Reads are served from
these files only — user requests never hit upstream APIs (ADR-004), and a
failed refresh leaves the last good snapshot in place (N5).
"""

import json
from pathlib import Path

import frappe

SNAPSHOT_DIR = "opensurf"


def _dir() -> Path:
	path = Path(frappe.get_site_path("private", "files", SNAPSHOT_DIR))
	path.mkdir(parents=True, exist_ok=True)
	return path


def _path(slug: str) -> Path:
	return _dir() / f"{slug}.json"


def write(slug: str, payload: dict) -> None:
	_path(slug).write_text(json.dumps(payload, indent=1, default=str))


def read(slug: str) -> dict | None:
	path = _path(slug)
	if not path.exists():
		return None
	try:
		return json.loads(path.read_text())
	except (json.JSONDecodeError, OSError):
		return None
