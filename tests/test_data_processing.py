import unittest

import pandas as pd

from rtd_analyzer.data_processing import (
    compute_transition_zones,
    normalize_dimensionless,
    prepare_experiment_window,
)


class DataProcessingTests(unittest.TestCase):
    def test_prepare_experiment_window_builds_time_axis(self) -> None:
        df = pd.DataFrame(
            {
                "Nr": [1, 2, 3, 4],
                "Wylew 1": [10.0, 11.0, 12.0, 13.0],
                "Wylew 2": [20.0, 21.0, 22.0, 23.0],
            }
        )
        out = prepare_experiment_window(df, discard_rows=1, start_offset=1, sample_interval_s=0.3)
        self.assertEqual(len(out), 2)
        self.assertAlmostEqual(out["czas_s"].iloc[0], 0.0)
        self.assertAlmostEqual(out["czas_s"].iloc[1], 0.3)

    def test_normalize_dimensionless_for_max_mode(self) -> None:
        df = pd.DataFrame(
            {
                "czas_s": [0.0, 0.3, 0.6],
                "Wylew 1": [10.0, 15.0, 20.0],
            }
        )
        out = normalize_dimensionless(df, ["Wylew 1"], "max")
        self.assertAlmostEqual(out["Wylew 1"].iloc[0], 0.0)
        self.assertAlmostEqual(out["Wylew 1"].iloc[-1], 1.0)

    def test_transition_zone_detects_delta_time(self) -> None:
        df = pd.DataFrame(
            {
                "czas_s": [0.0, 1.0, 2.0, 3.0],
                "Wylew 1": [0.0, 0.3, 0.7, 1.0],
            }
        )
        results = compute_transition_zones(df, ["Wylew 1"])
        self.assertEqual(results[0].status, "OK")
        self.assertIsNotNone(results[0].delta_t)
        self.assertAlmostEqual(results[0].delta_t, 1.6666666666666667, places=6)


if __name__ == "__main__":
    unittest.main()

