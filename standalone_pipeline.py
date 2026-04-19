from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, time
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import numpy as np
import pandas as pd
from tqdm import tqdm

try:
    from .intraday import FEATURE_COLUMNS, build_factor_catalog, build_intraday_factor_frame
    from .validation import (
        build_factor_validation_report,
        compute_factor_ic,
        compute_feature_correlation,
        compute_selected_max_abs_corr,
        extract_high_corr_pairs,
        select_features_by_ic_and_corr,
    )
except ImportError:
    # Fallback for running this file directly after copying factor_library only.
    from intraday import FEATURE_COLUMNS, build_factor_catalog, build_intraday_factor_frame
    from validation import (
        build_factor_validation_report,
        compute_factor_ic,
        compute_feature_correlation,
        compute_selected_max_abs_corr,
        extract_high_corr_pairs,
        select_features_by_ic_and_corr,
    )


@dataclass
class StandaloneConfig:
    target_horizon_minutes: int = 15
    entry_z: float = 0.8
    exit_z: float = 0.2
    zscore_window: int = 120
    max_hold_bars: int = 60

    max_position: int = 1
    max_daily_loss: float = 5000.0
    force_flat_time: str = "14:55:00"
    max_consecutive_losses: int = 3
    cooldown_minutes: int = 20

    contract_multiplier: float = 20.0
    tick_size: float = 1.0
    fee_rate: float = 0.00005
    slippage_ticks: float = 1.0
    impact_coeff: float = 0.2

    initial_capital: float = 1_000_000.0

    ic_method: str = "pearson"
    max_pair_corr: float = 0.5
    strict_corr_limit: bool = True
    min_abs_ic: float = 0.005
    min_selected_count: int = 16
    max_selected_count: int = 32

    # Signal generation: rolling 3-month quantile thresholds.
    rolling_window_days: int = 63
    long_quantile: float = 0.995
    short_quantile: float = 0.005

    # Annualization mapping.
    annualization_days: int = 252


@dataclass
class ExecutionConfig:
    contract_multiplier: float
    tick_size: float
    fee_rate: float
    slippage_ticks: float
    impact_coeff: float


@dataclass
class BacktestConfig:
    max_position: int
    max_daily_loss: float
    force_flat_time: str
    max_consecutive_losses: int
    cooldown_minutes: int
    contract_multiplier: float


@dataclass
class FactorAccumulator:
    factor: str
    group: str
    description: str
    coverage: float
    daily_pnl_net: Dict[str, float] = field(default_factory=dict)
    daily_pnl_gross: Dict[str, float] = field(default_factory=dict)
    total_turnover: float = 0.0
    total_cost: float = 0.0
    fill_count: int = 0
    trade_pnls: List[float] = field(default_factory=list)
    run_count: int = 0
    error_count: int = 0


def _safe_ratio(numerator: float, denominator: float) -> float:
    if denominator == 0.0 or np.isnan(denominator):
        return 0.0
    return float(numerator / denominator)


def _filter_days(days: Iterable[str], start_day: Optional[str], end_day: Optional[str]) -> List[str]:
    out = []
    for d in days:
        if start_day is not None and d < start_day:
            continue
        if end_day is not None and d > end_day:
            continue
        out.append(d)
    return out


def _parse_force_flat_time(value: str) -> time:
    hh, mm, ss = value.split(":")
    return time(int(hh), int(mm), int(ss))


def list_trading_days(data_root: Path, subdir: str) -> List[str]:
    day_root = data_root / subdir
    if not day_root.exists():
        return []
    return sorted([p.name for p in day_root.iterdir() if p.is_dir() and p.name.isdigit()])


def _day_file(data_root: Path, subdir: str, day: str) -> Path:
    day_folder = data_root / subdir / day
    files = sorted(day_folder.glob("*.parquet"))
    if not files:
        raise FileNotFoundError(f"No parquet found under {day_folder}")
    return files[0]


def load_min1_day(data_root: Path, subdir: str, day: str) -> pd.DataFrame:
    file_path = _day_file(data_root, subdir, day)
    df = pd.read_parquet(file_path)
    if "datetime" not in df.columns:
        raise ValueError(f"Missing datetime column in {file_path}")

    out = df.copy()
    out["ts"] = pd.to_datetime(out["datetime"])
    out = out.sort_values("ts").drop_duplicates(subset=["ts"]).reset_index(drop=True)
    out["trade_day"] = day

    if "close" not in out.columns:
        raise ValueError(f"Missing close column in {file_path}")

    for col in ["volume", "turnover", "open_interest"]:
        if col not in out.columns:
            out[col] = 0.0

    return out[["trade_day", "ts", "close", "volume", "turnover", "open_interest"]]


def load_min1_days(data_root: Path, subdir: str, days: Iterable[str]) -> pd.DataFrame:
    frames = [load_min1_day(data_root, subdir, d) for d in days]
    if not frames:
        return pd.DataFrame(columns=["trade_day", "ts", "close", "volume", "turnover", "open_interest"])
    return pd.concat(frames, axis=0, ignore_index=True)


def load_ticks_day(data_root: Path, subdir: str, day: str) -> pd.DataFrame:
    file_path = _day_file(data_root, subdir, day)
    df = pd.read_parquet(file_path)
    if "datetime" not in df.columns:
        raise ValueError(f"Missing datetime column in {file_path}")

    out = df.copy()
    out["ts"] = pd.to_datetime(out["datetime"])
    out = out.sort_values("ts").drop_duplicates(subset=["ts"]).reset_index(drop=True)

    for col in ["price", "bid_price_0", "ask_price_0", "volume"]:
        if col not in out.columns:
            out[col] = 0.0

    return out[["ts", "price", "bid_price_0", "ask_price_0", "volume"]]


def add_forward_returns(df: pd.DataFrame, horizon: int) -> Tuple[pd.DataFrame, str]:
    out = df.copy()
    target_col = f"fwd_ret_{horizon}m"
    out[target_col] = out["close"].shift(-horizon) / out["close"] - 1.0
    return out, target_col


def generate_target_position_rolling_quantile(
    df: pd.DataFrame,
    factor_col: str,
    rolling_window_days: int,
    long_quantile: float,
    short_quantile: float,
) -> pd.Series:
    if factor_col not in df.columns:
        raise ValueError(f"Factor column not found: {factor_col}")

    if not (0.0 < short_quantile < long_quantile < 1.0):
        raise ValueError(
            f"Invalid quantiles. Require 0 < short < long < 1, got short={short_quantile}, long={long_quantile}"
        )

    out = pd.Series(0, index=df.index, dtype=int, name="target_pos")
    days = sorted(df["trade_day"].astype(str).unique().tolist())

    history_windows: List[np.ndarray] = []
    for day in days:
        idx = df.index[df["trade_day"].astype(str) == day]
        if len(idx) == 0:
            continue

        if history_windows:
            recent_hist = history_windows[-rolling_window_days:]
            hist_values = np.concatenate(recent_hist) if recent_hist else np.array([], dtype=float)
            hist_values = hist_values[np.isfinite(hist_values)]
        else:
            hist_values = np.array([], dtype=float)

        if hist_values.size == 0:
            q_high = np.inf
            q_low = -np.inf
        else:
            q_high = float(np.quantile(hist_values, long_quantile))
            q_low = float(np.quantile(hist_values, short_quantile))

        day_factor = pd.to_numeric(df.loc[idx, factor_col], errors="coerce").replace([np.inf, -np.inf], np.nan)
        day_signal = np.where(day_factor >= q_high, 1, np.where(day_factor <= q_low, -1, 0))
        out.loc[idx] = day_signal.astype(int)

        day_values = day_factor.dropna().to_numpy(dtype=float)
        history_windows.append(day_values)

    return out


class TickExecutionSimulator:
    def __init__(self, ticks_df: pd.DataFrame, config: ExecutionConfig):
        if ticks_df.empty:
            raise ValueError("ticks_df is empty")
        self.ticks = ticks_df.sort_values("ts").reset_index(drop=True)
        self.ts_values = self.ticks["ts"].to_numpy(dtype="datetime64[ns]")
        self.config = config

    def simulate(self, order_ts: pd.Timestamp, qty: int) -> Dict[str, float]:
        if qty == 0:
            raise ValueError("qty cannot be 0")
        side = 1 if qty > 0 else -1
        idx = int(np.searchsorted(self.ts_values, np.datetime64(order_ts), side="left"))
        if idx >= len(self.ticks):
            idx = len(self.ticks) - 1

        tick = self.ticks.iloc[idx]
        decision_price = float(tick["price"])
        bid = float(tick.get("bid_price_0", np.nan))
        ask = float(tick.get("ask_price_0", np.nan))

        if np.isnan(bid) or bid <= 0.0:
            bid = decision_price - self.config.tick_size
        if np.isnan(ask) or ask <= 0.0:
            ask = decision_price + self.config.tick_size

        spread = max(ask - bid, self.config.tick_size)
        base_fill = ask if side > 0 else bid

        tick_volume = max(float(tick.get("volume", 1.0)), 1.0)
        impact_ticks = self.config.impact_coeff * abs(qty) / tick_volume
        impact_px = impact_ticks * self.config.tick_size
        fill_price = base_fill + side * self.config.slippage_ticks * self.config.tick_size + side * impact_px

        notional = abs(qty) * fill_price * self.config.contract_multiplier
        fee = notional * self.config.fee_rate
        spread_cost = abs(qty) * 0.5 * spread * self.config.contract_multiplier
        slippage_cost = abs(qty) * self.config.slippage_ticks * self.config.tick_size * self.config.contract_multiplier
        impact_cost = abs(qty) * abs(impact_px) * self.config.contract_multiplier
        total_cost = fee + spread_cost + slippage_cost + impact_cost

        return {
            "ts": pd.Timestamp(tick["ts"]),
            "fill_price": float(fill_price),
            "side": float(side),
            "qty": float(qty),
            "spread_cost": float(spread_cost),
            "slippage_cost": float(slippage_cost),
            "impact_cost": float(impact_cost),
            "fee": float(fee),
            "total_cost": float(total_cost),
        }


def run_backtest(
    signal_df: pd.DataFrame,
    ticks_df: pd.DataFrame,
    exec_cfg: ExecutionConfig,
    bt_cfg: BacktestConfig,
    initial_capital: float,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if signal_df.empty:
        raise ValueError("signal_df is empty")

    df = signal_df.sort_values("ts").reset_index(drop=True).copy()
    df["target_pos"] = df["target_pos"].clip(-bt_cfg.max_position, bt_cfg.max_position).astype(int)

    simulator = TickExecutionSimulator(ticks_df=ticks_df, config=exec_cfg)
    force_flat_clock = _parse_force_flat_time(bt_cfg.force_flat_time)

    fills: List[Dict[str, float]] = []
    trades: List[Dict[str, float]] = []
    records: List[Dict[str, float]] = []

    position = 0
    prev_close: Optional[float] = None
    cum_pnl = 0.0

    current_day: Optional[str] = None
    day_pnl = 0.0
    day_trading_blocked = False
    consecutive_losses = 0
    cooldown_until: Optional[pd.Timestamp] = None
    open_trade: Optional[Dict[str, float]] = None

    def execute_single(order_ts: pd.Timestamp, qty: int, pos_before: int) -> Tuple[int, float]:
        nonlocal open_trade
        nonlocal consecutive_losses
        nonlocal cooldown_until

        fill = simulator.simulate(order_ts=order_ts, qty=qty)
        fill["pos_before"] = float(pos_before)
        fill["pos_after"] = float(pos_before + qty)
        fills.append(fill)

        pos_after = pos_before + qty
        fill_cost = float(fill["total_cost"])

        if pos_before == 0 and pos_after != 0:
            open_trade = {
                "entry_ts": pd.Timestamp(fill["ts"]),
                "entry_price": float(fill["fill_price"]),
                "side": float(np.sign(pos_after)),
                "qty": float(abs(pos_after)),
                "entry_cost": float(fill_cost),
            }
        elif pos_before != 0 and pos_after == 0 and open_trade is not None:
            side = float(open_trade["side"])
            qty_abs = float(open_trade["qty"])
            gross = (float(fill["fill_price"]) - float(open_trade["entry_price"])) * side * qty_abs * bt_cfg.contract_multiplier
            net = gross - float(open_trade["entry_cost"]) - fill_cost
            trades.append(
                {
                    "entry_ts": open_trade["entry_ts"],
                    "exit_ts": pd.Timestamp(fill["ts"]),
                    "side": side,
                    "qty": qty_abs,
                    "gross_pnl": float(gross),
                    "net_pnl": float(net),
                }
            )
            if net < 0.0:
                consecutive_losses += 1
                if consecutive_losses >= bt_cfg.max_consecutive_losses:
                    cooldown_until = pd.Timestamp(fill["ts"]) + pd.Timedelta(minutes=bt_cfg.cooldown_minutes)
                    consecutive_losses = 0
            else:
                consecutive_losses = 0
            open_trade = None

        return pos_after, fill_cost

    for row in df.itertuples(index=False):
        ts = pd.Timestamp(row.ts)
        trade_day = str(row.trade_day)
        close = float(row.close)

        if current_day != trade_day:
            current_day = trade_day
            day_pnl = 0.0
            day_trading_blocked = False
            consecutive_losses = 0
            cooldown_until = None

        if day_pnl <= -bt_cfg.max_daily_loss:
            day_trading_blocked = True

        desired = int(row.target_pos)
        if day_trading_blocked:
            desired = 0
        if cooldown_until is not None and ts < cooldown_until:
            desired = 0
        if ts.time() >= force_flat_clock:
            desired = 0

        pnl_gross = 0.0
        if prev_close is not None:
            pnl_gross = position * (close - prev_close) * bt_cfg.contract_multiplier

        trade_cost = 0.0
        if desired != position:
            if position != 0 and desired != 0 and np.sign(position) != np.sign(desired):
                position, close_cost = execute_single(ts, -position, position)
                trade_cost += close_cost
                position, open_cost = execute_single(ts, desired, position)
                trade_cost += open_cost
            else:
                qty = desired - position
                position, one_cost = execute_single(ts, qty, position)
                trade_cost += one_cost

        pnl_net = pnl_gross - trade_cost
        day_pnl += pnl_net
        cum_pnl += pnl_net

        records.append(
            {
                "ts": ts,
                "trade_day": trade_day,
                "close": close,
                "position": float(position),
                "pnl_gross": float(pnl_gross),
                "trade_cost": float(trade_cost),
                "pnl_net": float(pnl_net),
                "day_pnl": float(day_pnl),
                "cum_pnl": float(cum_pnl),
                "equity": float(initial_capital + cum_pnl),
            }
        )

        prev_close = close

    equity_df = pd.DataFrame(records)
    if not equity_df.empty:
        equity_df["running_peak"] = equity_df["equity"].cummax()
        equity_df["drawdown"] = equity_df["equity"] - equity_df["running_peak"]
        equity_df = equity_df.drop(columns=["running_peak"])
    fills_df = pd.DataFrame(fills)
    trades_df = pd.DataFrame(trades)
    return equity_df, fills_df, trades_df


def _compute_performance(
    accum: FactorAccumulator,
    all_days: List[str],
    benchmark_daily_ret: pd.Series,
    initial_capital: float,
    annualization_days: int,
) -> Dict[str, object]:
    day_pnl_net = pd.Series([accum.daily_pnl_net.get(d, 0.0) for d in all_days], index=all_days, dtype=float)
    day_pnl_gross = pd.Series([accum.daily_pnl_gross.get(d, 0.0) for d in all_days], index=all_days, dtype=float)

    def calc_metric(day_pnl: pd.Series) -> Dict[str, float]:
        day_ret = day_pnl / initial_capital
        sharpe = 0.0
        if len(day_ret) > 1 and float(day_ret.std(ddof=0)) > 0.0:
            sharpe = float(np.sqrt(float(annualization_days)) * day_ret.mean() / day_ret.std(ddof=0))

        active_ret = day_ret.reindex(benchmark_daily_ret.index).fillna(0.0) - benchmark_daily_ret
        information_ratio = 0.0
        if len(active_ret) > 1 and float(active_ret.std(ddof=0)) > 0.0:
            information_ratio = float(np.sqrt(float(annualization_days)) * active_ret.mean() / active_ret.std(ddof=0))

        equity = initial_capital + day_pnl.cumsum()
        drawdown = equity - equity.cummax()
        max_drawdown = float(drawdown.min()) if len(drawdown) else 0.0
        total_return = float(equity.iloc[-1] / initial_capital - 1.0) if len(equity) else 0.0

        n_days = max(len(day_ret), 1)
        base = 1.0 + total_return
        if base > 0.0:
            annualized_return = float(base ** (float(annualization_days) / float(n_days)) - 1.0)
        else:
            annualized_return = -1.0

        annualized_vol = float(day_ret.std(ddof=0) * np.sqrt(float(annualization_days))) if len(day_ret) > 1 else 0.0

        return {
            "total_return": total_return,
            "annualized_return": annualized_return,
            "annualized_vol": annualized_vol,
            "sharpe": sharpe,
            "information_ratio": information_ratio,
            "max_drawdown": max_drawdown,
        }

    net_metric = calc_metric(day_pnl_net)
    gross_metric = calc_metric(day_pnl_gross)

    trade_arr = np.array(accum.trade_pnls, dtype=float)
    if trade_arr.size == 0:
        win_rate = 0.0
        profit_factor = 0.0
    else:
        win_rate = float((trade_arr > 0.0).mean())
        gain = float(trade_arr[trade_arr > 0.0].sum())
        loss = float(-trade_arr[trade_arr < 0.0].sum())
        profit_factor = _safe_ratio(gain, loss)

    return {
        "factor": accum.factor,
        "group": accum.group,
        "description": accum.description,
        "coverage": accum.coverage,
        "total_return_with_cost": net_metric["total_return"],
        "annualized_return_with_cost": net_metric["annualized_return"],
        "annualized_vol_with_cost": net_metric["annualized_vol"],
        "sharpe_with_cost": net_metric["sharpe"],
        "information_ratio_with_cost": net_metric["information_ratio"],
        "max_drawdown_with_cost": net_metric["max_drawdown"],
        "total_return_without_cost": gross_metric["total_return"],
        "annualized_return_without_cost": gross_metric["annualized_return"],
        "annualized_vol_without_cost": gross_metric["annualized_vol"],
        "sharpe_without_cost": gross_metric["sharpe"],
        "information_ratio_without_cost": gross_metric["information_ratio"],
        "max_drawdown_without_cost": gross_metric["max_drawdown"],
        "total_return": net_metric["total_return"],
        "sharpe": net_metric["sharpe"],
        "information_ratio": net_metric["information_ratio"],
        "max_drawdown": net_metric["max_drawdown"],
        "win_rate": win_rate,
        "profit_factor": profit_factor,
        "turnover": float(accum.total_turnover),
        "total_cost": float(accum.total_cost),
        "fill_count": float(accum.fill_count),
        "avg_cost_per_fill": _safe_ratio(accum.total_cost, float(accum.fill_count)),
        "trade_count": float(len(accum.trade_pnls)),
        "run_count": float(accum.run_count),
        "error_count": float(accum.error_count),
    }


def _build_markdown_report(
    report_path: Path,
    run_id: str,
    all_days: List[str],
    perf_df: pd.DataFrame,
    avg_sharpe_without_cost: float,
    avg_sharpe_with_cost: float,
    cfg: StandaloneConfig,
) -> None:
    top_sharpe = perf_df.sort_values("sharpe_without_cost", ascending=False).head(10)
    top_return = perf_df.sort_values("annualized_return_without_cost", ascending=False).head(10)
    top_ir = perf_df.sort_values("information_ratio_without_cost", ascending=False).head(10)

    lines: List[str] = []
    lines.append(f"# Factor Library Standalone Report ({run_id})")
    lines.append("")
    lines.append("## Universe")
    lines.append(f"- trading_days: {len(all_days)}")
    lines.append(f"- date_range: {all_days[0]} ~ {all_days[-1]}")
    lines.append(f"- factor_count: {len(perf_df)}")
    lines.append(f"- ic_method: {cfg.ic_method}")
    lines.append(
        f"- signal_rule: rolling_{cfg.rolling_window_days}_days_quantile, long>= {cfg.long_quantile:.3f}, short<= {cfg.short_quantile:.3f}"
    )
    lines.append(f"- annualization_days: {cfg.annualization_days}")
    lines.append(f"- average_sharpe_without_cost: {avg_sharpe_without_cost:.6f}")
    lines.append(f"- average_sharpe_with_cost: {avg_sharpe_with_cost:.6f}")
    lines.append("")

    def append_table(title: str, frame: pd.DataFrame) -> None:
        lines.append(f"## {title}")
        lines.append("")
        lines.append("| factor | group | sharpe_wo_cost | ir_wo_cost | annual_return_wo_cost | mdd_wo_cost |")
        lines.append("|---|---|---:|---:|---:|---:|")
        for row in frame.itertuples(index=False):
            lines.append(
                f"| {row.factor} | {row.group} | {row.sharpe_without_cost:.4f} | {row.information_ratio_without_cost:.4f} | {row.annualized_return_without_cost:.4%} | {row.max_drawdown_without_cost:.2f} |"
            )
        lines.append("")

    append_table("Top10 Sharpe (without cost)", top_sharpe)
    append_table("Top10 Annualized Return (without cost)", top_return)
    append_table("Top10 Information Ratio (without cost)", top_ir)

    report_path.write_text("\n".join(lines), encoding="utf-8")


def run_factor_submission_pipeline(
    data_root: str | Path,
    output_dir: str | Path,
    start_day: Optional[str] = None,
    end_day: Optional[str] = None,
    show_progress: bool = True,
    config: Optional[StandaloneConfig] = None,
) -> Dict[str, object]:
    cfg = config or StandaloneConfig()

    if abs((cfg.long_quantile + cfg.short_quantile) - 1.0) > 1e-12:
        raise ValueError(
            "Long/short quantiles must be symmetric. "
            f"Require long + short = 1.0, got long={cfg.long_quantile}, short={cfg.short_quantile}"
        )

    data_root_path = Path(data_root).resolve()
    output_root = Path(output_dir).resolve()

    if not data_root_path.exists():
        raise ValueError(f"Data root does not exist: {data_root_path}")

    if not (data_root_path / "min1").is_dir() or not (data_root_path / "ticks").is_dir():
        raise ValueError(
            "Invalid data root for standalone factor submission. "
            f"Expected subfolders 'min1' and 'ticks' under: {data_root_path}"
        )

    min1_days = list_trading_days(data_root_path, "min1")
    tick_days = list_trading_days(data_root_path, "ticks")
    if not min1_days or not tick_days:
        raise ValueError(
            f"No trading days found. min1_days={len(min1_days)}, tick_days={len(tick_days)}, root={data_root_path}"
        )

    all_days = _filter_days(sorted(set(min1_days).intersection(set(tick_days))), start_day, end_day)
    if not all_days:
        raise ValueError(
            "No common trading days found after date filtering. "
            f"min1_days={len(min1_days)}, tick_days={len(tick_days)}, "
            f"start_day={start_day}, end_day={end_day}, root={data_root_path}"
        )

    min1_df = load_min1_days(data_root_path, "min1", all_days)
    factor_df = build_intraday_factor_frame(min1_df)
    factor_catalog_df = build_factor_catalog()

    labeled_df, target_col = add_forward_returns(factor_df, cfg.target_horizon_minutes)
    eval_df = labeled_df.dropna(subset=["trade_day", "ts", "close", target_col]).reset_index(drop=True)

    ic_df = compute_factor_ic(eval_df, FEATURE_COLUMNS, target_col, method=cfg.ic_method)
    corr_df = compute_feature_correlation(eval_df, FEATURE_COLUMNS)
    high_corr_pairs_df = extract_high_corr_pairs(corr_df, threshold=cfg.max_pair_corr)
    selection = select_features_by_ic_and_corr(
        ic_df=ic_df,
        corr_df=corr_df,
        max_pair_corr=cfg.max_pair_corr,
        min_abs_ic=cfg.min_abs_ic,
        min_selected_count=cfg.min_selected_count,
        max_selected_count=cfg.max_selected_count,
        allow_threshold_relaxation=not cfg.strict_corr_limit,
    )
    selected_features = list(selection["selected_features"])
    selected_corr_df = corr_df.loc[selected_features, selected_features] if selected_features else pd.DataFrame()
    selected_max_abs_corr = compute_selected_max_abs_corr(corr_df, selected_features)
    if cfg.strict_corr_limit and selected_max_abs_corr > cfg.max_pair_corr + 1e-12:
        raise ValueError(
            f"Strict correlation limit violated: {selected_max_abs_corr:.6f} > {cfg.max_pair_corr:.6f}"
        )

    validation_summary = build_factor_validation_report(ic_df, high_corr_pairs_df, selected_features)

    exec_cfg = ExecutionConfig(
        contract_multiplier=cfg.contract_multiplier,
        tick_size=cfg.tick_size,
        fee_rate=cfg.fee_rate,
        slippage_ticks=cfg.slippage_ticks,
        impact_coeff=cfg.impact_coeff,
    )
    bt_cfg = BacktestConfig(
        max_position=cfg.max_position,
        max_daily_loss=cfg.max_daily_loss,
        force_flat_time=cfg.force_flat_time,
        max_consecutive_losses=cfg.max_consecutive_losses,
        cooldown_minutes=cfg.cooldown_minutes,
        contract_multiplier=cfg.contract_multiplier,
    )

    features = list(FEATURE_COLUMNS)
    signal_matrix = pd.DataFrame(index=factor_df.index)
    for factor in features:
        signal_matrix[factor] = generate_target_position_rolling_quantile(
            df=factor_df,
            factor_col=factor,
            rolling_window_days=cfg.rolling_window_days,
            long_quantile=cfg.long_quantile,
            short_quantile=cfg.short_quantile,
        ).astype(int)

    catalog_map = factor_catalog_df.set_index("name").to_dict(orient="index")
    accumulators: Dict[str, FactorAccumulator] = {}
    for factor in features:
        meta = catalog_map.get(factor, {})
        coverage = float(factor_df[factor].replace([np.inf, -np.inf], np.nan).notna().mean())
        accumulators[factor] = FactorAccumulator(
            factor=factor,
            group=str(meta.get("group", "unknown")),
            description=str(meta.get("description", "")),
            coverage=coverage,
        )

    progress = tqdm(
        total=len(all_days) * len(features),
        desc="Standalone factor backtest",
        unit="run",
        disable=not show_progress,
    )

    for day in all_days:
        try:
            ticks_day = load_ticks_day(data_root_path, "ticks", day)
        except Exception:
            for factor in features:
                accumulators[factor].error_count += 1
                accumulators[factor].daily_pnl_net[day] = 0.0
                accumulators[factor].daily_pnl_gross[day] = 0.0
                progress.update(1)
            continue

        day_idx = factor_df.index[factor_df["trade_day"] == day]
        day_frame = factor_df.loc[day_idx, ["trade_day", "ts", "close"]].copy()

        for factor in features:
            accum = accumulators[factor]
            signal_df = day_frame.copy()
            signal_df["target_pos"] = signal_matrix.loc[day_idx, factor].to_numpy(dtype=int)
            try:
                equity_df, fills_df, trades_df = run_backtest(
                    signal_df=signal_df,
                    ticks_df=ticks_day,
                    exec_cfg=exec_cfg,
                    bt_cfg=bt_cfg,
                    initial_capital=cfg.initial_capital,
                )
                accum.daily_pnl_net[day] = float(equity_df["pnl_net"].sum()) if not equity_df.empty else 0.0
                accum.daily_pnl_gross[day] = float(equity_df["pnl_gross"].sum()) if not equity_df.empty else 0.0
                if not equity_df.empty:
                    accum.total_turnover += float(equity_df["position"].diff().abs().fillna(0.0).sum())
                if not fills_df.empty:
                    accum.total_cost += float(fills_df["total_cost"].sum())
                    accum.fill_count += int(len(fills_df))
                if not trades_df.empty:
                    accum.trade_pnls.extend(trades_df["net_pnl"].astype(float).tolist())
                accum.run_count += 1
            except Exception:
                accum.error_count += 1
                accum.daily_pnl_net[day] = 0.0
                accum.daily_pnl_gross[day] = 0.0

            progress.update(1)

    progress.close()

    benchmark_close = min1_df.groupby("trade_day", as_index=True)["close"].last()
    benchmark_daily_ret = benchmark_close.pct_change().reindex(all_days).fillna(0.0)

    perf_rows = [
        _compute_performance(
            accumulators[f],
            all_days,
            benchmark_daily_ret,
            cfg.initial_capital,
            cfg.annualization_days,
        )
        for f in features
    ]
    perf_df = pd.DataFrame(perf_rows).sort_values("sharpe_without_cost", ascending=False).reset_index(drop=True)

    perf_df["rank_sharpe_without_cost"] = perf_df["sharpe_without_cost"].rank(method="dense", ascending=False)
    perf_df["rank_return_without_cost"] = perf_df["total_return_without_cost"].rank(method="dense", ascending=False)
    perf_df["rank_ir_without_cost"] = perf_df["information_ratio_without_cost"].rank(method="dense", ascending=False)

    avg_sharpe_without_cost = float(perf_df["sharpe_without_cost"].mean()) if not perf_df.empty else 0.0
    avg_sharpe_with_cost = float(perf_df["sharpe_with_cost"].mean()) if not perf_df.empty else 0.0

    group_df = (
        perf_df.groupby("group", as_index=False)
        .agg(
            factor_count=("factor", "count"),
            avg_sharpe_without_cost=("sharpe_without_cost", "mean"),
            avg_annualized_return_without_cost=("annualized_return_without_cost", "mean"),
            avg_ir_without_cost=("information_ratio_without_cost", "mean"),
            avg_total_return_without_cost=("total_return_without_cost", "mean"),
            avg_sharpe_with_cost=("sharpe_with_cost", "mean"),
            avg_annualized_return_with_cost=("annualized_return_with_cost", "mean"),
            avg_ir_with_cost=("information_ratio_with_cost", "mean"),
            avg_total_return_with_cost=("total_return_with_cost", "mean"),
            best_factor=("factor", "first"),
        )
        .sort_values("avg_sharpe_without_cost", ascending=False)
        .reset_index(drop=True)
    )

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = output_root / f"factor_submission_{run_id}"
    out_dir.mkdir(parents=True, exist_ok=True)

    factor_catalog_df.to_csv(out_dir / "factor_catalog.csv", index=False)
    ic_df.to_csv(out_dir / "factor_ic.csv", index=False)
    corr_df.to_csv(out_dir / "factor_corr_matrix.csv", index=True)
    high_corr_pairs_df.to_csv(out_dir / "factor_high_corr_pairs.csv", index=False)
    if not selected_corr_df.empty:
        selected_corr_df.to_csv(out_dir / "selected_factor_corr_matrix.csv", index=True)

    perf_df.to_csv(out_dir / "factor_backtest_metrics.csv", index=False)
    group_df.to_csv(out_dir / "factor_group_metrics.csv", index=False)
    perf_df.sort_values("sharpe_without_cost", ascending=False).head(10).to_csv(
        out_dir / "top10_sharpe_without_cost.csv", index=False
    )
    perf_df.sort_values("annualized_return_without_cost", ascending=False).head(10).to_csv(
        out_dir / "top10_annualized_return_without_cost.csv", index=False
    )
    perf_df.sort_values("information_ratio_without_cost", ascending=False).head(10).to_csv(
        out_dir / "top10_information_ratio_without_cost.csv", index=False
    )

    _build_markdown_report(
        report_path=out_dir / "README_FINAL_RESULTS.md",
        run_id=run_id,
        all_days=all_days,
        perf_df=perf_df,
        avg_sharpe_without_cost=avg_sharpe_without_cost,
        avg_sharpe_with_cost=avg_sharpe_with_cost,
        cfg=cfg,
    )

    selection_payload = {
        "selected_features": selected_features,
        "selection": selection,
        "validation": validation_summary,
        "constraints": {
            "ic_method": cfg.ic_method,
            "max_pair_corr": cfg.max_pair_corr,
            "strict_corr_limit": cfg.strict_corr_limit,
            "min_abs_ic": cfg.min_abs_ic,
            "min_selected_count": cfg.min_selected_count,
            "max_selected_count": cfg.max_selected_count,
        },
        "selected_max_abs_corr": selected_max_abs_corr,
    }
    with (out_dir / "factor_selection.json").open("w", encoding="utf-8") as f:
        json.dump(selection_payload, f, ensure_ascii=True, indent=2)

    summary_payload = {
        "run_id": run_id,
        "start_day": all_days[0],
        "end_day": all_days[-1],
        "day_count": len(all_days),
        "factor_count": len(features),
        "avg_sharpe_without_cost": avg_sharpe_without_cost,
        "avg_sharpe_with_cost": avg_sharpe_with_cost,
        "avg_annualized_return_without_cost": float(perf_df["annualized_return_without_cost"].mean())
        if not perf_df.empty
        else 0.0,
        "avg_annualized_return_with_cost": float(perf_df["annualized_return_with_cost"].mean()) if not perf_df.empty else 0.0,
        "selected_factor_count": len(selected_features),
        "selected_max_abs_corr": selected_max_abs_corr,
        "ic_method": cfg.ic_method,
        "signal_method": {
            "type": "rolling_quantile",
            "rolling_window_days": cfg.rolling_window_days,
            "long_quantile": cfg.long_quantile,
            "short_quantile": cfg.short_quantile,
        },
        "annualization_days": cfg.annualization_days,
        "output_dir": str(out_dir),
        "files": {
            "factor_catalog": str(out_dir / "factor_catalog.csv"),
            "factor_ic": str(out_dir / "factor_ic.csv"),
            "factor_corr_matrix": str(out_dir / "factor_corr_matrix.csv"),
            "selected_factor_corr_matrix": str(out_dir / "selected_factor_corr_matrix.csv"),
            "factor_high_corr_pairs": str(out_dir / "factor_high_corr_pairs.csv"),
            "factor_selection": str(out_dir / "factor_selection.json"),
            "factor_backtest_metrics": str(out_dir / "factor_backtest_metrics.csv"),
            "factor_group_metrics": str(out_dir / "factor_group_metrics.csv"),
            "top10_sharpe_without_cost": str(out_dir / "top10_sharpe_without_cost.csv"),
            "top10_annualized_return_without_cost": str(out_dir / "top10_annualized_return_without_cost.csv"),
            "top10_information_ratio_without_cost": str(out_dir / "top10_information_ratio_without_cost.csv"),
            "readme_final_results": str(out_dir / "README_FINAL_RESULTS.md"),
            "run_summary": str(out_dir / "run_summary.json"),
        },
    }
    with (out_dir / "run_summary.json").open("w", encoding="utf-8") as f:
        json.dump(summary_payload, f, ensure_ascii=True, indent=2)

    return summary_payload
