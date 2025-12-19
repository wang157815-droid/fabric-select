import unittest

from src.scoring import check_must, pick_best, score_candidate


class TestScoring(unittest.TestCase):
    def test_check_must(self):
        rules = {
            "must": [
                {"field": "water_repellency", "op": "gte", "value": 4, "reason": "拒水>=4"},
                {"field": "compliance.pfas_free", "op": "eq", "value": True, "reason": "PFAS-free"},
            ]
        }
        ok_cand = {"water_repellency": 4, "compliance": {"pfas_free": True}}
        bad_cand = {"water_repellency": 3, "compliance": {"pfas_free": True}}

        ok, fails = check_must(ok_cand, rules)
        self.assertTrue(ok)
        self.assertEqual(fails, [])

        ok2, fails2 = check_must(bad_cand, rules)
        self.assertFalse(ok2)
        self.assertIn("拒水>=4", fails2)

    def test_score_candidate_order(self):
        rules = {
            "must": [{"field": "ok", "op": "eq", "value": True, "reason": "ok"}],
            "prefer": [
                {"field": "perf", "weight": 0.7, "direction": "high", "normalization": {"type": "ordinal", "levels": [1, 2, 3, 4, 5]}},
                {"field": "cost_level", "weight": 0.3, "direction": "low", "normalization": {"type": "ordinal", "levels": [1, 2, 3, 4, 5]}},
            ],
        }
        a = {"ok": True, "perf": 5, "cost_level": 3}
        b = {"ok": True, "perf": 3, "cost_level": 1}
        self.assertGreater(score_candidate(a, rules), score_candidate(b, rules))

    def test_pick_best_must_eliminate(self):
        rules = {
            "must": [{"field": "x", "op": "gte", "value": 1, "reason": "x>=1"}],
            "prefer": [
                {"field": "x", "weight": 1.0, "direction": "high", "normalization": {"type": "minmax", "min": 0, "max": 10}},
            ],
            "tie_breakers": [{"field": "id", "direction": "low"}],
        }
        candidates = {
            "A": {"id": "a", "x": 5},
            "B": {"id": "b", "x": 6},
            "C": {"id": "c", "x": 0},  # must-fail
            "D": {"id": "d", "x": 4},
        }
        best, scores = pick_best(candidates, rules)
        self.assertEqual(best, "B")
        self.assertEqual(scores["C"], float("-inf"))


if __name__ == "__main__":
    unittest.main()


