"""
Extended chart patterns built on stock-pattern's pivot framework.

Adds 4 pattern families missing from stock-pattern:
  - Wedge (Rising/Falling)
  - Channel (Up/Down)
  - Multiple Tops & Bottoms
  - Horizontal Support & Resistance
"""

import logging
from typing import Optional

import numpy as np
import pandas as pd

from utils import (
    generate_trend_line,
    get_next_index,
    Point,
)

logger = logging.getLogger(__name__)


def _separate_pivot_types(pivots: pd.DataFrame, df: pd.DataFrame):
    """Separate pivot DataFrame into highs and lows based on price comparison."""
    high_dates = []
    low_dates = []

    for dt in pivots.index.unique():
        p_val = pivots.at[dt, "P"]
        h_val = df.at[dt, "High"]
        l_val = df.at[dt, "Low"]

        if isinstance(p_val, pd.Series):
            for single_p in p_val:
                if abs(single_p - h_val) < abs(single_p - l_val):
                    high_dates.append(dt)
                else:
                    low_dates.append(dt)
            continue

        if abs(p_val - h_val) < abs(p_val - l_val):
            high_dates.append(dt)
        else:
            low_dates.append(dt)

    high_dates.sort()
    low_dates.sort()
    return high_dates, low_dates


def _check_tl_breach(
    df: pd.DataFrame, upper_tl, lower_tl
) -> bool:
    """Return True if close has breached either trendline."""
    pos = df.reset_index().index
    upper_slope = upper_tl.slope * pos + upper_tl.y_int
    lower_slope = lower_tl.slope * pos + lower_tl.y_int
    return bool((df.Close > upper_slope).any() or (df.Close < lower_slope).any())


def find_bullish_wedge(
    sym: str, df: pd.DataFrame, pivots: pd.DataFrame, config
) -> Optional[dict]:
    """
    Falling Wedge (Bullish).

    Both highs and lows slope DOWN, with the upper (high) trendline
    steeper than the lower (low) trendline → convergence.
    Typically a bullish reversal pattern after a downtrend.
    """
    if len(df) < 40 or len(pivots) < 8:
        return

    high_dates, low_dates = _separate_pivot_types(pivots, df)
    if len(high_dates) < 3 or len(low_dates) < 3:
        return

    h1, h2 = high_dates[-1], high_dates[-2]
    l1, l2 = low_dates[-1], low_dates[-2]

    upper_tl = generate_trend_line(df["High"], h2, h1)
    lower_tl = generate_trend_line(df["Low"], l2, l1)

    mid_idx = df.index.get_loc(h2) + (df.index.get_loc(l1) - df.index.get_loc(h2)) // 2

    if upper_tl.slope >= 0 or lower_tl.slope >= 0:
        return

    slope_of_gap = upper_tl.slope - lower_tl.slope
    if slope_of_gap >= 0:
        return

    gap_start = upper_tl.slope * df.index.get_loc(h2) + upper_tl.y_int - (
        lower_tl.slope * df.index.get_loc(h2) + lower_tl.y_int
    )
    gap_end = upper_tl.slope * df.index.get_loc(l1) + upper_tl.y_int - (
        lower_tl.slope * df.index.get_loc(l1) + lower_tl.y_int
    )
    if gap_start <= 0 or gap_end <= 0:
        return

    if _check_tl_breach(df, upper_tl, lower_tl):
        return

    last_idx = df.index[-1]
    last_close = df.at[last_idx, "Close"]
    if isinstance(last_close, pd.Series):
        last_close = last_close.iloc[-1]
    upper_at_last = upper_tl.slope * df.index.get_loc(last_idx) + upper_tl.y_int
    lower_at_last = lower_tl.slope * df.index.get_loc(last_idx) + lower_tl.y_int

    if last_close > upper_at_last or last_close < lower_at_last:
        return

    logger.debug(f"{sym} - WEDGU (Falling Wedge)")

    return dict(
        sym=sym,
        pattern="WEDGU",
        alt_name="Falling Wedge",
        start=h2,
        end=last_idx,
        df_start=df.index[0],
        df_end=df.index[-1],
        points=dict(
            A=(h2, df.at[h2, "High"]),
            B=(l2, df.at[l2, "Low"]),
            C=(h1, df.at[h1, "High"]),
            D=(l1, df.at[l1, "Low"]),
        ),
        extra_points=dict(
            upper_start=upper_tl.line.start,
            upper_end=upper_tl.line.end,
            lower_start=lower_tl.line.start,
            lower_end=lower_tl.line.end,
        ),
    )


def find_bearish_wedge(
    sym: str, df: pd.DataFrame, pivots: pd.DataFrame, config
) -> Optional[dict]:
    """
    Rising Wedge (Bearish).

    Both highs and lows slope UP, with the upper (high) trendline
    flatter than the lower (low) trendline → convergence.
    Typically a bearish reversal pattern after an uptrend.
    """
    if len(df) < 40 or len(pivots) < 8:
        return

    high_dates, low_dates = _separate_pivot_types(pivots, df)
    if len(high_dates) < 3 or len(low_dates) < 3:
        return

    h1, h2 = high_dates[-1], high_dates[-2]
    l1, l2 = low_dates[-1], low_dates[-2]

    upper_tl = generate_trend_line(df["High"], h2, h1)
    lower_tl = generate_trend_line(df["Low"], l2, l1)

    if upper_tl.slope <= 0 or lower_tl.slope <= 0:
        return

    slope_of_gap = upper_tl.slope - lower_tl.slope
    if slope_of_gap >= 0:
        return

    gap_start = upper_tl.slope * df.index.get_loc(h2) + upper_tl.y_int - (
        lower_tl.slope * df.index.get_loc(h2) + lower_tl.y_int
    )
    gap_end = upper_tl.slope * df.index.get_loc(l1) + upper_tl.y_int - (
        lower_tl.slope * df.index.get_loc(l1) + lower_tl.y_int
    )
    if gap_start <= 0 or gap_end <= 0:
        return

    if _check_tl_breach(df, upper_tl, lower_tl):
        return

    last_idx = df.index[-1]
    last_close = df.at[last_idx, "Close"]
    if isinstance(last_close, pd.Series):
        last_close = last_close.iloc[-1]
    upper_at_last = upper_tl.slope * df.index.get_loc(last_idx) + upper_tl.y_int
    lower_at_last = lower_tl.slope * df.index.get_loc(last_idx) + lower_tl.y_int

    if last_close > upper_at_last or last_close < lower_at_last:
        return

    logger.debug(f"{sym} - WEDGD (Rising Wedge)")

    return dict(
        sym=sym,
        pattern="WEDGD",
        alt_name="Rising Wedge",
        start=h2,
        end=last_idx,
        df_start=df.index[0],
        df_end=df.index[-1],
        points=dict(
            A=(h2, df.at[h2, "High"]),
            B=(l2, df.at[l2, "Low"]),
            C=(h1, df.at[h1, "High"]),
            D=(l1, df.at[l1, "Low"]),
        ),
        extra_points=dict(
            upper_start=upper_tl.line.start,
            upper_end=upper_tl.line.end,
            lower_start=lower_tl.line.start,
            lower_end=lower_tl.line.end,
        ),
    )


def find_bullish_channel(
    sym: str, df: pd.DataFrame, pivots: pd.DataFrame, config
) -> Optional[dict]:
    """
    Channel Up (Bullish).

    Two parallel upward-sloping trendlines. Upper through pivot highs,
    lower through pivot lows. Price oscillates within the channel.
    """
    if len(df) < 40 or len(pivots) < 8:
        return

    high_dates, low_dates = _separate_pivot_types(pivots, df)
    if len(high_dates) < 3 or len(low_dates) < 3:
        return

    h1, h2 = high_dates[-1], high_dates[-2]
    l1, l2 = low_dates[-1], low_dates[-2]

    upper_tl = generate_trend_line(df["High"], h2, h1)
    lower_tl = generate_trend_line(df["Low"], l2, l1)

    if upper_tl.slope <= 0 or lower_tl.slope <= 0:
        return

    gap_slope = abs(upper_tl.slope - lower_tl.slope)
    avg_slope = (abs(upper_tl.slope) + abs(lower_tl.slope)) / 2
    if avg_slope > 0 and gap_slope / avg_slope > 0.3:
        return

    if _check_tl_breach(df, upper_tl, lower_tl):
        return

    last_idx = df.index[-1]
    last_close = df.at[last_idx, "Close"]
    if isinstance(last_close, pd.Series):
        last_close = last_close.iloc[-1]
    upper_at_last = upper_tl.slope * df.index.get_loc(last_idx) + upper_tl.y_int
    lower_at_last = lower_tl.slope * df.index.get_loc(last_idx) + lower_tl.y_int

    if last_close > upper_at_last or last_close < lower_at_last:
        return

    logger.debug(f"{sym} - CHNLU (Channel Up)")

    return dict(
        sym=sym,
        pattern="CHNLU",
        alt_name="Channel Up",
        start=h2,
        end=last_idx,
        df_start=df.index[0],
        df_end=df.index[-1],
        points=dict(
            A=(h2, df.at[h2, "High"]),
            B=(l2, df.at[l2, "Low"]),
            C=(h1, df.at[h1, "High"]),
            D=(l1, df.at[l1, "Low"]),
        ),
        extra_points=dict(
            upper_start=upper_tl.line.start,
            upper_end=upper_tl.line.end,
            lower_start=lower_tl.line.start,
            lower_end=lower_tl.line.end,
        ),
    )


def find_bearish_channel(
    sym: str, df: pd.DataFrame, pivots: pd.DataFrame, config
) -> Optional[dict]:
    """
    Channel Down (Bearish).

    Two parallel downward-sloping trendlines. Upper through pivot highs,
    lower through pivot lows. Price oscillates within the channel.
    """
    if len(df) < 40 or len(pivots) < 8:
        return

    high_dates, low_dates = _separate_pivot_types(pivots, df)
    if len(high_dates) < 3 or len(low_dates) < 3:
        return

    h1, h2 = high_dates[-1], high_dates[-2]
    l1, l2 = low_dates[-1], low_dates[-2]

    upper_tl = generate_trend_line(df["High"], h2, h1)
    lower_tl = generate_trend_line(df["Low"], l2, l1)

    if upper_tl.slope >= 0 or lower_tl.slope >= 0:
        return

    gap_slope = abs(upper_tl.slope - lower_tl.slope)
    avg_slope = (abs(upper_tl.slope) + abs(lower_tl.slope)) / 2
    if avg_slope > 0 and gap_slope / avg_slope > 0.3:
        return

    if _check_tl_breach(df, upper_tl, lower_tl):
        return

    last_idx = df.index[-1]
    last_close = df.at[last_idx, "Close"]
    if isinstance(last_close, pd.Series):
        last_close = last_close.iloc[-1]
    upper_at_last = upper_tl.slope * df.index.get_loc(last_idx) + upper_tl.y_int
    lower_at_last = lower_tl.slope * df.index.get_loc(last_idx) + lower_tl.y_int

    if last_close > upper_at_last or last_close < lower_at_last:
        return

    logger.debug(f"{sym} - CHNLD (Channel Down)")

    return dict(
        sym=sym,
        pattern="CHNLD",
        alt_name="Channel Down",
        start=h2,
        end=last_idx,
        df_start=df.index[0],
        df_end=df.index[-1],
        points=dict(
            A=(h2, df.at[h2, "High"]),
            B=(l2, df.at[l2, "Low"]),
            C=(h1, df.at[h1, "High"]),
            D=(l1, df.at[l1, "Low"]),
        ),
        extra_points=dict(
            upper_start=upper_tl.line.start,
            upper_end=upper_tl.line.end,
            lower_start=lower_tl.line.start,
            lower_end=lower_tl.line.end,
        ),
    )


def find_multiple_top(
    sym: str, df: pd.DataFrame, pivots: pd.DataFrame, config
) -> Optional[dict]:
    """
    Multiple Top (Bearish).

    Three or more pivot highs at approximately the same price level,
    indicating strong resistance. Price has failed to break above
    this level multiple times.
    """
    if len(df) < 40 or len(pivots) < 8:
        return

    high_dates, _ = _separate_pivot_types(pivots, df)
    if len(high_dates) < 3:
        return

    last_3 = [df.at[dt, "High"] for dt in high_dates[-3:]]
    last_3 = [v.iloc[0] if isinstance(v, pd.Series) else v for v in last_3]

    price_range = max(last_3) - min(last_3)
    avg_price = sum(last_3) / len(last_3)
    range_pct = price_range / avg_price if avg_price > 0 else 0

    if range_pct > 0.05:
        return

    last_idx = df.index[-1]
    last_close = df.at[last_idx, "Close"]
    if isinstance(last_close, pd.Series):
        last_close = last_close.iloc[-1]

    resistance_level = max(last_3)
    if last_close > resistance_level:
        return

    level_dates = high_dates[-3:]
    level_prices = last_3

    logger.debug(f"{sym} - MLTP (Multiple Top)")

    return dict(
        sym=sym,
        pattern="MLTP",
        alt_name="Multiple Top",
        start=level_dates[0],
        end=last_idx,
        df_start=df.index[0],
        df_end=df.index[-1],
        points={
            f"Top{i+1}": (dt, df.at[dt, "High"])
            for i, dt in enumerate(level_dates)
        },
        extra_points=dict(
            level_start=(level_dates[0], resistance_level),
            level_end=(last_idx, resistance_level),
        ),
    )


def find_multiple_bottom(
    sym: str, df: pd.DataFrame, pivots: pd.DataFrame, config
) -> Optional[dict]:
    """
    Multiple Bottom (Bullish).

    Three or more pivot lows at approximately the same price level,
    indicating strong support. Price has failed to break below
    this level multiple times.
    """
    if len(df) < 40 or len(pivots) < 8:
        return

    _, low_dates = _separate_pivot_types(pivots, df)
    if len(low_dates) < 3:
        return

    last_3 = [df.at[dt, "Low"] for dt in low_dates[-3:]]
    last_3 = [v.iloc[0] if isinstance(v, pd.Series) else v for v in last_3]

    price_range = max(last_3) - min(last_3)
    avg_price = sum(last_3) / len(last_3)
    range_pct = price_range / avg_price if avg_price > 0 else 0

    if range_pct > 0.05:
        return

    last_idx = df.index[-1]
    last_close = df.at[last_idx, "Close"]
    if isinstance(last_close, pd.Series):
        last_close = last_close.iloc[-1]

    support_level = min(last_3)
    if last_close < support_level:
        return

    level_dates = low_dates[-3:]
    logger.debug(f"{sym} - MLTB (Multiple Bottom)")

    return dict(
        sym=sym,
        pattern="MLTB",
        alt_name="Multiple Bottom",
        start=level_dates[0],
        end=last_idx,
        df_start=df.index[0],
        df_end=df.index[-1],
        points={
            f"Bot{i+1}": (dt, df.at[dt, "Low"])
            for i, dt in enumerate(level_dates)
        },
        extra_points=dict(
            level_start=(level_dates[0], support_level),
            level_end=(last_idx, support_level),
        ),
    )


class Level:
    __slots__ = ("price", "count", "dates")

    def __init__(self, price, count, dates):
        self.price = price
        self.count = count
        self.dates = dates


def find_support_resistance(
    sym: str, df: pd.DataFrame, pivots: pd.DataFrame, config
) -> Optional[dict]:
    """
    Horizontal Support & Resistance Levels.

    Clusters pivots at similar price levels to identify
    meaningful S/R zones. Returns the strongest level found.
    """
    if len(df) < 40 or len(pivots) < 6:
        return

    prices = pivots["P"].values
    dates = pivots.index.values

    MAX_LEVELS = min(3, len(prices) // 3)
    if MAX_LEVELS < 1:
        return

    price_range = df["High"].max() - df["Low"].min()
    cluster_threshold = price_range * 0.05

    levels = []
    used = set()

    for i in range(len(prices)):
        if i in used:
            continue
        cluster_prices = [prices[i]]
        cluster_dates = [dates[i]]
        for j in range(i + 1, len(prices)):
            if j in used:
                continue
            if abs(prices[i] - prices[j]) < cluster_threshold:
                cluster_prices.append(prices[j])
                cluster_dates.append(dates[j])
                used.add(j)
        used.add(i)
        if len(cluster_prices) >= 3:
            levels.append(
                Level(
                    price=sum(cluster_prices) / len(cluster_prices),
                    count=len(cluster_prices),
                    dates=[pd.Timestamp(d) for d in cluster_dates],
                )
            )

    if not levels:
        return

    levels.sort(key=lambda lev: lev.count, reverse=True)
    best = levels[0]

    last_idx = df.index[-1]
    last_close = df.at[last_idx, "Close"]
    if isinstance(last_close, pd.Series):
        last_close = last_close.iloc[-1]

    is_support = best.price < last_close
    pattern_name = "Support" if is_support else "Resistance"
    pattern_key = "SUPR"

    level_dates_sorted = sorted(best.dates)
    points = {}
    max_labels = min(len(level_dates_sorted), 5)
    for i in range(max_labels):
        dt = level_dates_sorted[i]
        tag = f"S{i+1}" if is_support else f"R{i+1}"
        p_val = df.at[dt, "Low"] if is_support else df.at[dt, "High"]
        if isinstance(p_val, pd.Series):
            p_val = p_val.iloc[0]
        points[tag] = (dt, p_val)

    logger.debug(f"{sym} - {pattern_key} ({pattern_name} at {best.price:.2f}, {best.count} touches)")

    return dict(
        sym=sym,
        pattern=pattern_key,
        alt_name=pattern_name,
        start=level_dates_sorted[0],
        end=last_idx,
        df_start=df.index[0],
        df_end=df.index[-1],
        points=points,
        extra_points=dict(
            level_start=(level_dates_sorted[0], best.price),
            level_end=(last_idx, best.price),
        ),
    )
