# Copyright (c) 2026, Open Surf Software contributors
# For license information, please see license.txt

import unittest

from opensurf.ingest import bmkg

SAMPLE_AREA = {
	"code": "P.P.04",
	"name": "Perairan Selatan P. Bali",
	"forecast_day1": [
		{
			"time": "2026-10-08 00:00 UTC",
			"weather": "Berawan",
			"wind_from": "Tenggara",
			"wind_speed": 6,
			"wind_gust": 10,
			"wave_cat": "Tinggi",
			"wave_height": 3.2,
			"current_to": "Selatan",
			"current_speed": 1.34,
		}
	],
}


class TestCompass(unittest.TestCase):
	def test_names(self):
		self.assertEqual(bmkg._compass_deg("Tenggara"), 135)
		self.assertEqual(bmkg._compass_deg("Barat Laut"), 315)
		self.assertIsNone(bmkg._compass_deg("Variable"))


class TestRows(unittest.TestCase):
	def test_utc_to_local(self):
		rows = bmkg._rows(SAMPLE_AREA, "Asia/Makassar")
		self.assertEqual(len(rows), 1)
		self.assertEqual(rows[0]["time"], "2026-10-08 08:00")  # UTC+8 WITA
		self.assertEqual(rows[0]["wind_dir"], 135)
		self.assertEqual(rows[0]["wave_height"], 3.2)


if __name__ == "__main__":
	unittest.main()
