# Copyright (c) 2026, Open Surf Software contributors
# For license information, please see license.txt

import unittest
from typing import ClassVar

from opensurf import scoring


class TestArc(unittest.TestCase):
	def test_simple_range(self):
		self.assertEqual(scoring._arc_dist(210, 190, 240), 0)
		self.assertAlmostEqual(scoring._arc_dist(250, 190, 240), 10)
		self.assertAlmostEqual(scoring._arc_dist(170, 190, 240), 20)

	def test_wrap_around_range(self):
		# Lembongan offshore band 320-40 wraps through north.
		self.assertEqual(scoring._arc_dist(0, 320, 40), 0)
		self.assertEqual(scoring._arc_dist(350, 320, 40), 0)
		self.assertAlmostEqual(scoring._arc_dist(50, 320, 40), 10)
		self.assertAlmostEqual(scoring._arc_dist(180, 320, 40), 140)


class TestWindScore(unittest.TestCase):
	def test_offshore_light(self):
		# Bukit band 80-160, SE trade 135°, 8 kn → full marks.
		self.assertEqual(scoring._wind_score(135, 80, 160, 8, 12), 1.0)

	def test_onshore(self):
		# Wind from 300° at Uluwatu is onshore → low score.
		score = scoring._wind_score(300, 80, 160, 10, 14)
		self.assertLess(score, 0.3)

	def test_strong_offshore_penalty(self):
		# Offshore but howling (gust 30 kn) — direction credit stays, strength drops.
		score = scoring._wind_score(135, 80, 160, 25, 30)
		self.assertAlmostEqual(score, 0.3)

	def test_cross_shore(self):
		# South wind (180) is cross-shore for the 80-160 band, not in onshore arc.
		score = scoring._wind_score(180, 80, 160, 8, 10)
		self.assertAlmostEqual(score, 0.55)


class TestTideScore(unittest.TestCase):
	def test_band(self):
		self.assertEqual(scoring._tide_score("Mid to High", 0.6, 0.1), 1.0)
		self.assertLess(scoring._tide_score("Mid to High", 0.1, -0.1), 0.5)

	def test_incoming(self):
		self.assertEqual(scoring._tide_score("Incoming", 0.5, 0.2), 1.0)
		self.assertEqual(scoring._tide_score("Incoming", 0.5, -0.2), 0.35)

	def test_any(self):
		self.assertEqual(scoring._tide_score("Any", 0.1, -0.5), 1.0)


class TestScoreHour(unittest.TestCase):
	ULUWATU: ClassVar[dict] = {
		"ideal_swell_dir_min": 190,
		"ideal_swell_dir_max": 240,
		"ideal_swell_height_min": 1.0,
		"ideal_swell_height_max": 3.0,
		"ideal_swell_period_min": 12,
		"offshore_wind_dir_min": 80,
		"offshore_wind_dir_max": 160,
		"tide_preference": "Mid to High",
	}

	def test_pumping_day(self):
		hour = {
			"swell_height": 2.0,
			"swell_dir": 215,
			"swell_period": 15,
			"wind_dir": 120,
			"wind_speed": 7,
			"wind_gust": 10,
			"tide_level": 0.7,
			"tide_trend": 0.1,
		}
		self.assertEqual(scoring.score_hour(self.ULUWATU, hour)["score"], 10.0)

	def test_flat_onshore(self):
		hour = {
			"swell_height": 0.2,
			"swell_dir": 60,
			"swell_period": 6,
			"wind_dir": 300,
			"wind_speed": 18,
			"wind_gust": 26,
			"tide_level": 0.1,
			"tide_trend": -0.1,
		}
		self.assertLess(scoring.score_hour(self.ULUWATU, hour)["score"], 3)

	def test_missing_components_reweight(self):
		# No tide data → tide drops out of the weights instead of scoring 0 or free 1.
		hour = {"swell_height": 2.0, "swell_dir": 215, "swell_period": 15, "wind_dir": 120, "wind_speed": 5}
		result = scoring.score_hour(self.ULUWATU, hour)
		self.assertIsNotNone(result["score"])
		self.assertIsNone(result["parts"]["tide"])


class TestAttachTides(unittest.TestCase):
	def test_normalizes_per_day(self):
		hours = [{"time": "2026-10-08T06:00"}, {"time": "2026-10-08T12:00"}]
		tides = [
			{"time": "2026-10-08 06:00", "tide": -1.0},
			{"time": "2026-10-08 12:00", "tide": 1.0},
		]
		scoring.attach_tides(hours, tides)
		self.assertEqual(hours[0]["tide_level"], 0.0)
		self.assertEqual(hours[1]["tide_level"], 1.0)
		self.assertGreater(hours[1]["tide_trend"], 0)


if __name__ == "__main__":
	unittest.main()
