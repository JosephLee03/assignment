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

### Top10 OOS Sharpe (without cost)

| factor | group | sharpe_wo_cost | ir_wo_cost | annual_return_wo_cost | mdd_wo_cost |
|---|---|---:|---:|---:|---:|
| rev_3m | reversal | 6.0367 | 0.9643 | 0.2812% | -100.00 |
| rev_5m | reversal | 5.1114 | 0.9583 | 0.1571% | -20.00 |
| oi_volume_ratio | open_interest | 4.1243 | 0.9578 | 0.1488% | -40.00 |
| turnover_ma_ratio_5_20 | turnover | 3.7798 | 0.9601 | 0.1984% | -160.00 |
| volume_ma_ratio_5_20 | volume | 3.6248 | 0.9597 | 0.1902% | -160.00 |
| downside_vol_20 | volatility | 3.6103 | 0.9555 | 0.0992% | -100.00 |
| sin_tod | time | 3.4076 | 0.9627 | 0.2398% | -240.00 |
| volume_chg_5 | volume | 1.9238 | 0.9561 | 0.1157% | -180.00 |
| illiq_1m | liquidity | 1.7936 | 0.9649 | 0.3806% | -540.00 |
| turnover_z20 | turnover | 1.7339 | 0.9559 | 0.1075% | -280.00 |

#3# Top10 OOS Sharpe (without cost) Correlation Matrix

| factor | rev_3m | rev_5m | oi_volume_ratio | turnover_ma_ratio_5_20 | volume_ma_ratio_5_20 | downside_vol_20 | sin_tod | volume_chg_5 | illiq_1m | turnover_z20 |
|---|---|---|---|---|---|---|---|---|---|---|
| rev_3m | 1.000 | 0.741 | -0.018 | 0.001 | 0.002 | 0.134 | 0.010 | -0.015 | -0.173 | 0.003 |
| rev_5m | 0.741 | 1.000 | -0.020 | 0.003 | 0.006 | 0.174 | 0.013 | -0.031 | -0.125 | -0.002 |
| oi_volume_ratio | -0.018 | -0.020 | 1.000 | -0.040 | -0.040 | -0.030 | -0.092 | -0.004 | 0.030 | -0.134 |
| turnover_ma_ratio_5_20 | 0.001 | 0.003 | -0.040 | 1.000 | 1.000 | -0.007 | 0.010 | 0.061 | 0.000 | 0.530 |
| volume_ma_ratio_5_20 | 0.002 | 0.006 | -0.040 | 1.000 | 1.000 | -0.006 | 0.010 | 0.061 | -0.000 | 0.530 |
| downside_vol_20 | 0.134 | 0.174 | -0.030 | -0.007 | -0.006 | 1.000 | 0.016 | 0.005 | 0.006 | -0.034 |
| sin_tod | 0.010 | 0.013 | -0.092 | 0.010 | 0.010 | 0.016 | 1.000 | -0.002 | -0.006 | -0.001 |
| volume_chg_5 | -0.015 | -0.031 | -0.004 | 0.061 | 0.061 | 0.005 | -0.002 | 1.000 | -0.000 | 0.049 |
| illiq_1m | -0.173 | -0.125 | 0.030 | 0.000 | -0.000 | 0.006 | -0.006 | -0.000 | 1.000 | -0.008 |
| turnover_z20 | 0.003 | -0.002 | -0.134 | 0.530 | 0.530 | -0.034 | -0.001 | 0.049 | -0.008 | 1.000 |


