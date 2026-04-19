from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List

try:
    from .standalone_pipeline import StandaloneConfig, run_factor_submission_pipeline
except ImportError:
    from standalone_pipeline import StandaloneConfig, run_factor_submission_pipeline


def _is_valid_data_root(path: Path) -> bool:
    return (path / "min1").is_dir() and (path / "ticks").is_dir()


def _resolve_data_root(raw_value: str) -> Path:
    raw = Path(raw_value).expanduser()
    cwd = Path.cwd().resolve()
    script_dir = Path(__file__).resolve().parent

    candidates: List[Path] = []
    if raw.is_absolute():
        candidates.append(raw.resolve())
    else:
        candidates.append((cwd / raw).resolve())
        candidates.append((script_dir / raw).resolve())

    # Auto-discover common project layout: <project>/data/CZCE/sa
    for base in [cwd, *cwd.parents]:
        candidates.append((base / "data" / "CZCE" / "sa").resolve())
    for base in [script_dir, *script_dir.parents]:
        candidates.append((base / "data" / "CZCE" / "sa").resolve())

    unique_candidates: List[Path] = []
    seen = set()
    for c in candidates:
        key = str(c).lower()
        if key in seen:
            continue
        seen.add(key)
        unique_candidates.append(c)

    for c in unique_candidates:
        if _is_valid_data_root(c):
            return c

    tried = "\n".join([f"- {c}" for c in unique_candidates[:10]])
    raise ValueError(
        "Unable to resolve a valid --data-root. A valid root must contain both 'min1/' and 'ticks/' subfolders.\n"
        f"Input: {raw_value}\n"
        f"Current working directory: {cwd}\n"
        f"Script directory: {script_dir}\n"
        f"Tried paths:\n{tried}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run standalone factor-library validation + all-factor backtest.")
    parser.add_argument("--data-root", required=True, help="Path to SA dataset root, e.g. data/CZCE/sa")
    parser.add_argument("--output-dir", default="./outputs", help="Output root for standalone submission results")
    parser.add_argument("--start-day", default=None)
    parser.add_argument("--end-day", default=None)
    parser.add_argument("--ic-method", default="pearson", help="IC method: pearson|spearman|kendall (supports 'person' alias)")
    parser.add_argument("--rolling-window-days", type=int, default=63, help="Rolling window in trading days (3 months ~= 63)")
    parser.add_argument("--long-quantile", type=float, default=0.995, help="Long threshold quantile")
    parser.add_argument("--short-quantile", type=float, default=0.005, help="Short threshold quantile")
    parser.add_argument("--annualization-days", type=int, default=252, help="Annualization base days")
    parser.add_argument("--no-progress", action="store_true", help="Disable tqdm progress bar")
    args = parser.parse_args()

    resolved_data_root = _resolve_data_root(args.data_root)

    ic_method = str(args.ic_method).strip().lower()
    if ic_method == "person":
        ic_method = "pearson"

    cfg = StandaloneConfig(
        ic_method=ic_method,
        rolling_window_days=int(args.rolling_window_days),
        long_quantile=float(args.long_quantile),
        short_quantile=float(args.short_quantile),
        annualization_days=int(args.annualization_days),
    )

    if abs((cfg.long_quantile + cfg.short_quantile) - 1.0) > 1e-12:
        raise ValueError(
            "Long/short quantiles must be symmetric. "
            f"Require long + short = 1.0, got long={cfg.long_quantile}, short={cfg.short_quantile}"
        )

    result = run_factor_submission_pipeline(
        data_root=resolved_data_root,
        output_dir=Path(args.output_dir),
        start_day=args.start_day,
        end_day=args.end_day,
        show_progress=not args.no_progress,
        config=cfg,
    )
    result["resolved_data_root"] = str(resolved_data_root)
    print(json.dumps(result, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
