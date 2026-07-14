"""Tests for extended patterns (Wedge, Channel, Multiple Tops/Bottoms, S/R)."""

import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils import get_max_min
import patterns_extended as pe


def _falling_wedge_data(seed=42):
    np.random.seed(seed)
    n = 150
    x = np.arange(n)
    amplitude = np.linspace(5, 1.5, n)
    center = 100 - x * 0.04
    osc = np.sin(x * 0.4) * amplitude
    dates = pd.date_range("2024-01-01", periods=n, freq="D")
    close = center + osc * 0.3
    return pd.DataFrame(
        {
            "Open": close + np.random.randn(n) * 0.1,
            "High": center + osc + abs(np.random.randn(n) * 0.2),
            "Low": center + osc - abs(np.random.randn(n) * 0.2),
            "Close": close,
            "Volume": np.random.randint(1000000, 5000000, n),
        },
        index=dates,
    )


def _rising_wedge_data(seed=42):
    np.random.seed(seed)
    n = 150
    x = np.arange(n)
    amplitude = np.linspace(5, 1.5, n)
    center = 95 + x * 0.04
    osc = np.sin(x * 0.4) * amplitude
    dates = pd.date_range("2024-01-01", periods=n, freq="D")
    close = center + osc * 0.3
    return pd.DataFrame(
        {
            "Open": close + np.random.randn(n) * 0.1,
            "High": center + osc + abs(np.random.randn(n) * 0.2),
            "Low": center + osc - abs(np.random.randn(n) * 0.2),
            "Close": close,
            "Volume": np.random.randint(1000000, 5000000, n),
        },
        index=dates,
    )


def _channel_up_data(seed=42):
    np.random.seed(seed)
    n = 150
    x = np.arange(n)
    dates = pd.date_range("2024-01-01", periods=n, freq="D")
    base = 95 + x * 0.05
    osc = np.sin(x * 0.4) * 3
    close = base + osc * 0.3
    return pd.DataFrame(
        {
            "Open": close + np.random.randn(n) * 0.1,
            "High": base + osc + abs(np.random.randn(n) * 0.2) + 0.5,
            "Low": base + osc - abs(np.random.randn(n) * 0.2) - 0.5,
            "Close": close,
            "Volume": np.random.randint(1000000, 5000000, n),
        },
        index=dates,
    )


def _channel_down_data(seed=42):
    np.random.seed(seed)
    n = 150
    x = np.arange(n)
    dates = pd.date_range("2024-01-01", periods=n, freq="D")
    base = 105 - x * 0.05
    osc = np.sin(x * 0.4) * 3
    close = base + osc * 0.3
    return pd.DataFrame(
        {
            "Open": close + np.random.randn(n) * 0.1,
            "High": base + osc + abs(np.random.randn(n) * 0.2) + 0.5,
            "Low": base + osc - abs(np.random.randn(n) * 0.2) - 0.5,
            "Close": close,
            "Volume": np.random.randint(1000000, 5000000, n),
        },
        index=dates,
    )


def _multi_bottom_data(seed=1):
    np.random.seed(seed)
    n = 150
    dates = pd.date_range("2024-01-01", periods=n, freq="D")
    close = 100 + np.cumsum(np.random.randn(n) * 0.3)
    for dip_start in [20, 60, 100]:
        for i in range(10):
            idx = dip_start + i
            if idx < n:
                close[idx] = 95 + np.random.randn() * 0.3
    high = close + abs(np.random.randn(n)) * 0.8
    low = np.minimum(close - abs(np.random.randn(n)) * 0.8, 94.5 + np.random.randn(n) * 0.2)
    return pd.DataFrame(
        {
            "Open": close + np.random.randn(n) * 0.2,
            "High": high,
            "Low": low,
            "Close": close,
            "Volume": np.random.randint(1000000, 5000000, n),
        },
        index=dates,
    )


class TestWedgePatterns(unittest.TestCase):
    def test_falling_wedge(self):
        df = _falling_wedge_data()
        pivots = get_max_min(df)
        result = pe.find_bullish_wedge("TEST", df, pivots, {})
        self.assertIsNotNone(result)
        self.assertEqual(result["pattern"], "WEDGU")
        self.assertIn("points", result)
        self.assertIn("extra_points", result)

    def test_rising_wedge(self):
        df = _rising_wedge_data()
        pivots = get_max_min(df)
        result = pe.find_bearish_wedge("TEST", df, pivots, {})
        self.assertIsNotNone(result)
        self.assertEqual(result["pattern"], "WEDGD")
        self.assertIn("points", result)
        self.assertIn("extra_points", result)

    def test_not_enough_data(self):
        df = _falling_wedge_data().iloc[:20]
        pivots = get_max_min(df)
        result = pe.find_bullish_wedge("TEST", df, pivots, {})
        self.assertIsNone(result)


class TestChannelPatterns(unittest.TestCase):
    def test_channel_up(self):
        df = _channel_up_data()
        pivots = get_max_min(df)
        result = pe.find_bullish_channel("TEST", df, pivots, {})
        self.assertIsNotNone(result)
        self.assertEqual(result["pattern"], "CHNLU")

    def test_channel_down(self):
        df = _channel_down_data()
        pivots = get_max_min(df)
        result = pe.find_bearish_channel("TEST", df, pivots, {})
        self.assertIsNotNone(result)
        self.assertEqual(result["pattern"], "CHNLD")


class TestMultipleTopsBottoms(unittest.TestCase):
    def test_multiple_bottom(self):
        df = _multi_bottom_data()
        pivots = get_max_min(df)
        result = pe.find_multiple_bottom("TEST", df, pivots, {})
        self.assertIsNotNone(result)
        self.assertEqual(result["pattern"], "MLTB")

    def test_multiple_top_few_pivots(self):
        np.random.seed(42)
        n = 40
        dates = pd.date_range("2024-01-01", periods=n, freq="D")
        close = 100 + np.arange(n) * 0.05 + np.random.randn(n) * 1.0
        df = pd.DataFrame(
            {
                "Open": close + np.random.randn(n) * 0.2,
                "High": close + abs(np.random.randn(n * 1) * 0.3).reshape(n) + 0.2,
                "Low": close - abs(np.random.randn(n * 1) * 0.3).reshape(n) - 0.2,
                "Close": close,
                "Volume": np.random.randint(1000000, 5000000, n),
            },
            index=dates,
        )
        pivots = get_max_min(df)
        result = pe.find_multiple_top("TEST", df, pivots, {})
        self.assertIsNone(result)


class TestSupportResistance(unittest.TestCase):
    def test_support_resistance_detects(self):
        df = _multi_bottom_data()
        pivots = get_max_min(df)
        result = pe.find_support_resistance("TEST", df, pivots, {})
        self.assertIsNotNone(result)
        self.assertEqual(result["pattern"], "SUPR")
        self.assertIn("alt_name", result)
        self.assertIn("points", result)
        self.assertIn("extra_points", result)

    def test_sr_not_enough_pivots(self):
        np.random.seed(42)
        n = 30
        dates = pd.date_range("2024-01-01", periods=n, freq="D")
        df = pd.DataFrame(
            {
                "Open": np.random.randn(n) + 100,
                "High": np.random.randn(n) + 101,
                "Low": np.random.randn(n) + 99,
                "Close": np.random.randn(n) + 100,
                "Volume": np.random.randint(1000000, 5000000, n),
            },
            index=dates,
        )
        pivots = get_max_min(df)
        result = pe.find_support_resistance("TEST", df, pivots, {})
        self.assertIsNone(result)


class TestSeparatePivots(unittest.TestCase):
    def test_separate_types(self):
        np.random.seed(1)
        n = 100
        dates = pd.date_range("2024-01-01", periods=n, freq="D")
        close = 100 + np.cumsum(np.random.randn(n) * 0.3)
        df = pd.DataFrame(
            {
                "Open": close + np.random.randn(n) * 0.1,
                "High": close + abs(np.random.randn(n)) * 0.5,
                "Low": close - abs(np.random.randn(n)) * 0.5,
                "Close": close,
                "Volume": np.random.randint(1000000, 5000000, n),
            },
            index=dates,
        )
        pivots = get_max_min(df)
        highs, lows = pe._separate_pivot_types(pivots, df)
        self.assertGreater(len(highs), 0)
        self.assertGreater(len(lows), 0)
        self.assertEqual(len(highs) + len(lows), len(pivots.index.unique()))


if __name__ == "__main__":
    unittest.main()
