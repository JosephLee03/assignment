# Factor Library Submission Guide

This folder is fully standalone for factor submission.

It depends only on:
- data files (`min1/` and `ticks/` parquet)
- third-party libraries in `requirements.txt`

It does not import modules outside this folder.

## Contents

- `intraday.py`: alpha factor generation (56 factors)
- `validation.py`: IC/correlation/selection utilities
- `standalone_pipeline.py`: standalone factor validation + all-factor backtest
- `run_submission.py`: CLI entrypoint
- `requirements.txt`: minimal dependency list
- `REFERENCE.md`: references

## Backtest Method (Optimized)

- IC method: `pearson` (supports alias `person` in CLI)
- Evaluation split: latest 3 calendar months are held out as OOS (default `--oos-months 3`)
- Signal rule: rolling 3-month window (`63` trading days)
  - long threshold: `0.995` quantile
  - short threshold: `0.005` quantile
- Long/short mapping:
  - factor >= rolling quantile(99.5%) => long `+1`
  - factor <= rolling quantile(0.5%) => short `-1`
  - otherwise `0`
- Metrics mapping to annualized:
  - annualized return
  - annualized volatility
  - annualized Sharpe / Information Ratio

## How to Run

Run in this folder:

```bash
pip install -r requirements.txt
python run_submission.py --data-root <PATH_TO_DATA_ROOT> --output-dir ./outputs
```

Example with explicit parameters:

```bash
python run_submission.py --data-root ../../../data/CZCE/sa --output-dir ./outputs --ic-method person --rolling-window-days 63 --long-quantile 0.995 --short-quantile 0.005 --oos-months 3
```

Notes:
- `run_submission.py` validates symmetric quantiles: `long_quantile + short_quantile = 1.0`.
- IC/correlation selection is computed on in-sample data; OOS is used for out-of-sample performance reporting.
- `run_submission.py` will auto-try common project layouts if `--data-root` is wrong.
- tqdm progress is shown by default.

## Final Output (Detailed)

Each run generates:

```text
outputs/
  factor_submission_<run_id>/
    factor_catalog.csv
    factor_ic.csv
    factor_corr_matrix.csv
    selected_factor_corr_matrix.csv
    factor_high_corr_pairs.csv
    factor_selection.json
    factor_backtest_metrics.csv
    factor_backtest_metrics_oos.csv
    factor_group_metrics.csv
    top10_sharpe_without_cost.csv
    top10_sharpe_without_cost_oos.csv
    top10_annualized_return_without_cost.csv
    top10_information_ratio_without_cost.csv
    README_FINAL_RESULTS.md
    run_summary.json
```

### 1) Correlation Matrix Requirement (max correlation = 0.5)

- `factor_corr_matrix.csv`: full matrix
- `selected_factor_corr_matrix.csv`: selected subset matrix
- `factor_selection.json` key fields:
  - `constraints.max_pair_corr`
  - `constraints.strict_corr_limit`
  - `selected_max_abs_corr`

### 2) Average Sharpe for All Alpha Factors (without cost)

- `run_summary.json` key field:
  - `avg_sharpe_without_cost`

### 3) Annualized Mapping Output

In `factor_backtest_metrics.csv`, each factor includes:
- `annualized_return_without_cost`
- `annualized_vol_without_cost`
- `sharpe_without_cost`
- `information_ratio_without_cost`
- corresponding `*_with_cost` fields

In `factor_backtest_metrics_oos.csv`, OOS metrics are provided with `_oos` suffix columns.

### 4) Detailed Final Readme for This Run

- `README_FINAL_RESULTS.md` includes:
  - data range and factor count
  - in-sample/OOS split range and OOS months
  - method settings (`pearson`, rolling quantile thresholds)
  - average sharpe (with/without cost, full sample and OOS)
  - Top10 tables by Sharpe / Annualized Return / Information Ratio
  - Top10 OOS Sharpe table

### 5) Quick Summary File

`run_summary.json` includes:
- run range and factor count
- in-sample/OOS day counts and OOS range
- average Sharpe (with/without cost, full sample and OOS)
- average annualized return (with/without cost, full sample and OOS)
- selected factor count and max selected correlation
- resolved output path and generated file paths
