# Copyright (c) 2026, Open Surf Software contributors
# For license information, please see license.txt

import re

import frappe
from frappe.model.document import Document

_SLUG_UNSAFE = re.compile(r"[^a-z0-9]+")


def slugify(value: str) -> str:
	return _SLUG_UNSAFE.sub("-", value.strip().lower()).strip("-")


class SurfSpot(Document):
	def validate(self) -> None:
		self.slug = slugify(self.spot_name)
