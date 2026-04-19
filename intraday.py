from __future__ import annotations

from typing import Dict, List

import numpy as np
import pandas as pd


FACTOR_METADATA: List[Dict[str, str]] = [
    {"name": "ret_1m", "group": "price_return", "description": "1-minute return"},
    {"name": "ret_3m", "group": "price_return", "description": "3-minute return"},
    {"name": "ret_5m", "group": "price_return", "description": "5-minute return"},
    {"name": "ret_10m", "group": "price_return", "description": "10-minute return"},
    {"name": "ret_15m", "group": "price_return", "description": "15-minute return"},
    {"name": "ret_30m", "group": "price_return", "description": "30-minute return"},
    {"name": "ret_60m", "group": "price_return", "description": "60-minute return"},
    {"name": "mom_5m", "group": "momentum", "description": "5-minute momentum"},
    {"name": "mom_15m", "group": "momentum", "description": "15-minute momentum"},
    {"name": "mom_30m", "group": "momentum", "description": "30-minute momentum"},
    {"name": "rev_3m", "group": "reversal", "description": "3-minute reversal"},
    {"name": "rev_5m", "group": "reversal", "description": "5-minute reversal"},
    {"name": "acc_mom_5_15", "group": "momentum", "description": "Acceleration of momentum"},
    {"name": "ema_gap_5_20", "group": "trend", "description": "EMA(5) vs EMA(20) gap"},
    {"name": "ema_gap_10_30", "group": "trend", "description": "EMA(10) vs EMA(30) gap"},
    {"name": "ma_slope_10", "group": "trend", "description": "Slope proxy of MA(10)"},
    {"name": "ma_slope_30", "group": "trend", "description": "Slope proxy of MA(30)"},
    {"name": "price_z20", "group": "trend", "description": "Price z-score, 20 bars"},
    {"name": "price_z60", "group": "trend", "description": "Price z-score, 60 bars"},
    {"name": "boll_pos_20", "group": "trend", "description": "Bollinger position (20)"},
    {"name": "vol_5m", "group": "volatility", "description": "5-minute realized volatility"},
    {"name": "vol_15m", "group": "volatility", "description": "15-minute realized volatility"},
    {"name": "vol_20m", "group": "volatility", "description": "20-minute realized volatility"},
    {"name": "vol_30m", "group": "volatility", "description": "30-minute realized volatility"},
    {"name": "vol_60m", "group": "volatility", "description": "60-minute realized volatility"},
    {"name": "vol_of_vol_30", "group": "volatility", "description": "Volatility of volatility"},
    {"name": "downside_vol_20", "group": "volatility", "description": "Downside volatility"},
    {"name": "upside_vol_20", "group": "volatility", "description": "Upside volatility"},
    {"name": "up_down_vol_ratio_20", "group": "volatility", "description": "Upside/downside vol ratio"},
    {"name": "ret_skew_30", "group": "volatility", "description": "Rolling skewness of returns"},
    {"name": "ret_kurt_30", "group": "volatility", "description": "Rolling kurtosis of returns"},
    {"name": "range_proxy_15", "group": "volatility", "description": "Rolling close range proxy"},
    {"name": "vol_regime_20_60", "group": "volatility", "description": "Volatility regime ratio"},
    {"name": "volume_z20", "group": "volume", "description": "Volume z-score, 20 bars"},
    {"name": "volume_z60", "group": "volume", "description": "Volume z-score, 60 bars"},
    {"name": "volume_ma_ratio_5_20", "group": "volume", "description": "Volume MA ratio"},
    {"name": "volume_chg_1", "group": "volume", "description": "Volume change, 1 bar"},
    {"name": "volume_chg_5", "group": "volume", "description": "Volume change, 5 bars"},
    {"name": "turnover_z20", "group": "turnover", "description": "Turnover z-score, 20 bars"},
    {"name": "turnover_z60", "group": "turnover", "description": "Turnover z-score, 60 bars"},
    {"name": "turnover_ma_ratio_5_20", "group": "turnover", "description": "Turnover MA ratio"},
    {"name": "illiq_1m", "group": "liquidity", "description": "One-bar illiquidity proxy"},
    {"name": "amihud_20", "group": "liquidity", "description": "Amihud proxy, 20 bars"},
    {"name": "pv_corr_20", "group": "liquidity", "description": "Price-volume correlation"},
    {"name": "signed_volume_z20", "group": "liquidity", "description": "Signed volume z-score"},
    {"name": "oi_delta", "group": "open_interest", "description": "Open interest difference"},
    {"name": "oi_z20", "group": "open_interest", "description": "OI delta z-score, 20 bars"},
    {"name": "oi_z60", "group": "open_interest", "description": "OI delta z-score, 60 bars"},
    {"name": "oi_trend_10", "group": "open_interest", "description": "OI trend proxy, 10 bars"},
    {"name": "oi_trend_30", "group": "open_interest", "description": "OI trend proxy, 30 bars"},
    {"name": "oi_volume_ratio", "group": "open_interest", "description": "OI over volume ratio"},
    {"name": "sin_tod", "group": "time", "description": "Intraday seasonality sine"},
    {"name": "cos_tod", "group": "time", "description": "Intraday seasonality cosine"},
    {"name": "minute_norm", "group": "time", "description": "Normalized minute of day"},
    {"name": "is_open_30m", "group": "time", "description": "First 30 minutes flag"},
    {"name": "is_close_30m", "group": "time", "description": "Last 30 minutes flag"},
]

FEATURE_COLUMNS = [item["name"] for item in FACTOR_METADATA]


def _safe_zscore(series: pd.Series, window: int) -> pd.Series:
    mean = series.rolling(window, min_periods=window).mean()
    std = series.rolling(window, min_periods=window).std(ddof=0)
    return (series - mean) / std.replace(0.0, np.nan)


def _safe_divide(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    return numerator / denominator.replace(0.0, np.nan)


def build_factor_catalog() -> pd.DataFrame:
    return pd.DataFrame(FACTOR_METADATA)


def build_intraday_factor_frame(min1_df: pd.DataFrame) -> pd.DataFrame:
    df = min1_df.copy().sort_values("ts").reset_index(drop=True)

    close = df["close"].astype(float)
    volume = df["volume"].astype(float)
    turnover = df["turnover"].astype(float)
    open_interest = df["open_interest"].astype(float)

    # Return and momentum family.
    df["ret_1m"] = close.pct_change(1)
    df["ret_3m"] = close.pct_change(3)
    df["ret_5m"] = close.pct_change(5)
    df["ret_10m"] = close.pct_change(10)
    df["ret_15m"] = close.pct_change(15)
    df["ret_30m"] = close.pct_change(30)
    df["ret_60m"] = close.pct_change(60)

    df["mom_5m"] = close / close.shift(5) - 1.0
    df["mom_15m"] = close / close.shift(15) - 1.0
    df["mom_30m"] = close / close.shift(30) - 1.0
    df["rev_3m"] = -(close / close.shift(3) - 1.0)
    df["rev_5m"] = -(close / close.shift(5) - 1.0)
    df["acc_mom_5_15"] = df["mom_5m"] - df["mom_15m"]

    # Trend family.
    ema_5 = close.ewm(span=5, adjust=False).mean()
    ema_10 = close.ewm(span=10, adjust=False).mean()
    ema_20 = close.ewm(span=20, adjust=False).mean()
    ema_30 = close.ewm(span=30, adjust=False).mean()
    ma_10 = close.rolling(10, min_periods=10).mean()
    ma_20 = close.rolling(20, min_periods=20).mean()
    ma_30 = close.rolling(30, min_periods=30).mean()

    df["ema_gap_5_20"] = _safe_divide(ema_5, ema_20) - 1.0
    df["ema_gap_10_30"] = _safe_divide(ema_10, ema_30) - 1.0
    df["ma_slope_10"] = _safe_divide(ma_10 - ma_10.shift(5), ma_10.shift(5))
    df["ma_slope_30"] = _safe_divide(ma_30 - ma_30.shift(10), ma_30.shift(10))
    df["price_z20"] = _safe_zscore(close, 20)
    df["price_z60"] = _safe_zscore(close, 60)
    boll_std_20 = close.rolling(20, min_periods=20).std(ddof=0)
    df["boll_pos_20"] = _safe_divide(close - ma_20, 2.0 * boll_std_20)

    # Volatility family.
    ret = df["ret_1m"].fillna(0.0)
    df["vol_5m"] = ret.rolling(5, min_periods=5).std(ddof=0)
    df["vol_15m"] = ret.rolling(15, min_periods=15).std(ddof=0)
    df["vol_20m"] = ret.rolling(20, min_periods=20).std(ddof=0)
    df["vol_30m"] = ret.rolling(30, min_periods=30).std(ddof=0)
    df["vol_60m"] = ret.rolling(60, min_periods=60).std(ddof=0)
    df["vol_of_vol_30"] = df["vol_5m"].rolling(30, min_periods=30).std(ddof=0)

    downside = ret.clip(upper=0.0)
    upside = ret.clip(lower=0.0)
    df["downside_vol_20"] = downside.rolling(20, min_periods=20).std(ddof=0)
    df["upside_vol_20"] = upside.rolling(20, min_periods=20).std(ddof=0)
    df["up_down_vol_ratio_20"] = _safe_divide(df["upside_vol_20"], df["downside_vol_20"])
    df["up_down_vol_ratio_20"] = df["up_down_vol_ratio_20"].fillna(1.0)
    df["ret_skew_30"] = ret.rolling(30, min_periods=20).skew()
    df["ret_kurt_30"] = ret.rolling(30, min_periods=20).kurt()
    range_max_15 = close.rolling(15, min_periods=15).max()
    range_min_15 = close.rolling(15, min_periods=15).min()
    df["range_proxy_15"] = _safe_divide(range_max_15 - range_min_15, close)
    df["vol_regime_20_60"] = _safe_divide(df["vol_20m"], df["vol_60m"])

    # Volume/turnover/liquidity family.
    df["volume_z20"] = _safe_zscore(volume, 20)
    df["volume_z60"] = _safe_zscore(volume, 60)
    volume_ma_5 = volume.rolling(5, min_periods=5).mean()
    volume_ma_20 = volume.rolling(20, min_periods=20).mean()
    df["volume_ma_ratio_5_20"] = _safe_divide(volume_ma_5, volume_ma_20)
    df["volume_chg_1"] = volume.pct_change(1)
    df["volume_chg_5"] = volume.pct_change(5)

    df["turnover_z20"] = _safe_zscore(turnover, 20)
    df["turnover_z60"] = _safe_zscore(turnover, 60)
    turnover_ma_5 = turnover.rolling(5, min_periods=5).mean()
    turnover_ma_20 = turnover.rolling(20, min_periods=20).mean()
    df["turnover_ma_ratio_5_20"] = _safe_divide(turnover_ma_5, turnover_ma_20)

    abs_ret = ret.abs()
    df["illiq_1m"] = _safe_divide(abs_ret, turnover + 1.0)
    df["amihud_20"] = df["illiq_1m"].rolling(20, min_periods=20).mean()
    df["pv_corr_20"] = ret.rolling(20, min_periods=20).corr(df["volume_chg_1"].fillna(0.0))
    df["pv_corr_20"] = df["pv_corr_20"].fillna(0.0)
    signed_volume = np.sign(ret) * volume
    df["signed_volume_z20"] = _safe_zscore(signed_volume, 20)

    # Open-interest family.
    df["oi_delta"] = open_interest.diff()
    df["oi_z20"] = _safe_zscore(df["oi_delta"].fillna(0.0), 20)
    df["oi_z60"] = _safe_zscore(df["oi_delta"].fillna(0.0), 60)
    oi_ma_10 = open_interest.rolling(10, min_periods=10).mean()
    oi_ma_30 = open_interest.rolling(30, min_periods=30).mean()
    df["oi_trend_10"] = _safe_divide(oi_ma_10 - oi_ma_10.shift(5), oi_ma_10.shift(5))
    df["oi_trend_30"] = _safe_divide(oi_ma_30 - oi_ma_30.shift(10), oi_ma_30.shift(10))
    df["oi_volume_ratio"] = _safe_divide(open_interest, volume + 1.0)

    # Time-of-day family.
    minute_of_day = df["ts"].dt.hour * 60 + df["ts"].dt.minute
    df["sin_tod"] = np.sin(2.0 * np.pi * minute_of_day / 1440.0)
    df["cos_tod"] = np.cos(2.0 * np.pi * minute_of_day / 1440.0)
    df["minute_norm"] = minute_of_day / 1440.0
    df["is_open_30m"] = (minute_of_day <= 30).astype(float)
    df["is_close_30m"] = (minute_of_day >= 1410).astype(float)

    return df
