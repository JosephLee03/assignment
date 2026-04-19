from __future__ import annotations

from typing import Dict, List

import numpy as np
import pandas as pd


def compute_factor_ic(
    train_df: pd.DataFrame,
    feature_cols: List[str],
    target_col: str,
    method: str = "spearman",
) -> pd.DataFrame:
    rows = []
    n_total = float(len(train_df)) if len(train_df) > 0 else 1.0

    for feature in feature_cols:
        valid = train_df[["trade_day", feature, target_col]].dropna()
        if valid.empty:
            rows.append(
                {
                    "factor": feature,
                    "mean_ic": 0.0,
                    "ic_std": 0.0,
                    "ic_ir": 0.0,
                    "positive_ic_ratio": 0.0,
                    "abs_mean_ic": 0.0,
                    "coverage": 0.0,
                    "ic_days": 0.0,
                }
            )
            continue

        daily_ic = (
            valid.groupby("trade_day", as_index=True)
            .apply(lambda g: g[feature].corr(g[target_col], method=method))
            .dropna()
        )
        mean_ic = float(daily_ic.mean()) if len(daily_ic) else 0.0
        ic_std = float(daily_ic.std(ddof=0)) if len(daily_ic) else 0.0
        ic_ir = float(np.sqrt(len(daily_ic)) * mean_ic / ic_std) if ic_std > 0.0 else 0.0
        positive_ic_ratio = float((daily_ic > 0.0).mean()) if len(daily_ic) else 0.0
        coverage = float(train_df[feature].notna().sum() / n_total)

        rows.append(
            {
                "factor": feature,
                "mean_ic": mean_ic,
                "ic_std": ic_std,
                "ic_ir": ic_ir,
                "positive_ic_ratio": positive_ic_ratio,
                "abs_mean_ic": abs(mean_ic),
                "coverage": coverage,
                "ic_days": float(len(daily_ic)),
            }
        )

    ic_df = pd.DataFrame(rows)
    if ic_df.empty:
        return pd.DataFrame(columns=["factor", "mean_ic", "ic_std", "ic_ir", "positive_ic_ratio", "abs_mean_ic", "coverage", "ic_days"])
    return ic_df.sort_values(["abs_mean_ic", "ic_ir"], ascending=[False, False]).reset_index(drop=True)


def compute_feature_correlation(train_df: pd.DataFrame, feature_cols: List[str]) -> pd.DataFrame:
    if not feature_cols:
        return pd.DataFrame()
    corr = train_df[feature_cols].corr(method="pearson")
    return corr


def extract_high_corr_pairs(corr_df: pd.DataFrame, threshold: float) -> pd.DataFrame:
    if corr_df.empty:
        return pd.DataFrame(columns=["factor_a", "factor_b", "corr", "abs_corr"])

    factors = corr_df.columns.tolist()
    rows = []
    for i in range(len(factors)):
        for j in range(i + 1, len(factors)):
            a = factors[i]
            b = factors[j]
            corr_val = float(corr_df.loc[a, b])
            if np.isnan(corr_val):
                continue
            abs_corr = abs(corr_val)
            if abs_corr >= threshold:
                rows.append({"factor_a": a, "factor_b": b, "corr": corr_val, "abs_corr": abs_corr})

    if not rows:
        return pd.DataFrame(columns=["factor_a", "factor_b", "corr", "abs_corr"])
    return pd.DataFrame(rows).sort_values("abs_corr", ascending=False).reset_index(drop=True)


def select_features_by_ic_and_corr(
    ic_df: pd.DataFrame,
    corr_df: pd.DataFrame,
    max_pair_corr: float,
    min_abs_ic: float,
    min_selected_count: int,
    max_selected_count: int,
    allow_threshold_relaxation: bool = True,
) -> Dict[str, object]:
    if ic_df.empty:
        return {
            "selected_features": [],
            "dropped_low_ic": [],
            "dropped_high_corr": [],
            "effective_corr_threshold": max_pair_corr,
        }

    ranked = ic_df.sort_values(["abs_mean_ic", "ic_ir"], ascending=[False, False]).copy()
    low_ic_mask = ranked["abs_mean_ic"] < min_abs_ic
    dropped_low_ic = ranked.loc[low_ic_mask, "factor"].tolist()
    candidates = ranked.loc[~low_ic_mask, "factor"].tolist()
    if not candidates:
        candidates = ranked["factor"].tolist()

    selected: List[str] = []
    dropped_high_corr: List[str] = []

    def can_add(feature: str, threshold: float) -> bool:
        if corr_df.empty:
            return True
        for chosen in selected:
            if feature not in corr_df.index or chosen not in corr_df.columns:
                continue
            c = corr_df.loc[feature, chosen]
            if pd.notna(c) and abs(float(c)) > threshold:
                return False
        return True

    effective_threshold = max_pair_corr
    for factor in candidates:
        if len(selected) >= max_selected_count:
            break
        if can_add(factor, effective_threshold):
            selected.append(factor)
        else:
            dropped_high_corr.append(factor)

    # Ensure a minimum feature count for model robustness by slightly relaxing threshold.
    if allow_threshold_relaxation and len(selected) < min_selected_count:
        effective_threshold = min(0.95, max_pair_corr + 0.10)
        for factor in candidates:
            if factor in selected:
                continue
            if len(selected) >= min_selected_count or len(selected) >= max_selected_count:
                break
            if can_add(factor, effective_threshold):
                selected.append(factor)

    return {
        "selected_features": selected,
        "dropped_low_ic": dropped_low_ic,
        "dropped_high_corr": dropped_high_corr,
        "effective_corr_threshold": effective_threshold,
    }


def compute_selected_max_abs_corr(corr_df: pd.DataFrame, selected_features: List[str]) -> float:
    if corr_df.empty or len(selected_features) < 2:
        return 0.0

    subset = corr_df.reindex(index=selected_features, columns=selected_features)
    if subset.empty:
        return 0.0

    arr = subset.to_numpy(dtype=float)
    mask = ~np.eye(arr.shape[0], dtype=bool)
    vals = np.abs(arr[mask])
    vals = vals[~np.isnan(vals)]
    if vals.size == 0:
        return 0.0
    return float(vals.max())


def build_factor_validation_report(
    ic_df: pd.DataFrame,
    corr_pairs_df: pd.DataFrame,
    selected_features: List[str],
) -> Dict[str, float]:
    return {
        "raw_factor_count": float(len(ic_df)),
        "selected_factor_count": float(len(selected_features)),
        "avg_abs_ic": float(ic_df["abs_mean_ic"].mean()) if not ic_df.empty else 0.0,
        "max_abs_ic": float(ic_df["abs_mean_ic"].max()) if not ic_df.empty else 0.0,
        "high_corr_pair_count": float(len(corr_pairs_df)),
    }
