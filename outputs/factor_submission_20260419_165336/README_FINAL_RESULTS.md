# Factor Library Standalone Report (20260419_165336)

## Universe
- trading_days: 243
- date_range: 20250102 ~ 20251231
- in_sample_days: 182
- out_of_sample_days: 61
- oos_range: 20250930 ~ 20251231
- factor_count: 56
- ic_method: pearson
- oos_policy: latest_3_calendar_months
- signal_rule: rolling_63_days_quantile, long>= 0.995, short<= 0.005
- annualization_days: 252
- average_sharpe_without_cost: -1.227757
- average_sharpe_with_cost: -11.194394
- average_sharpe_without_cost_oos: -1.189138
- average_sharpe_with_cost_oos: -12.149710

## Correlation matrix (maximal correlation is 0.5)

- selected_factors_max_abs_correlation: 0.479860
- full_matrix_file: factor_corr_matrix.csv
- selected_matrix_file: selected_factor_corr_matrix.csv

## Top10 Sharpe (without cost)

| factor | group | sharpe_wo_cost | ir_wo_cost | annual_return_wo_cost | mdd_wo_cost |
|---|---|---:|---:|---:|---:|
| rev_3m | reversal | 4.2137 | 0.5047 | 0.4335% | -660.00 |
| rev_5m | reversal | 3.7346 | 0.5045 | 0.4273% | -500.00 |
| downside_vol_20 | volatility | 1.7113 | 0.4947 | 0.1514% | -520.00 |
| illiq_1m | liquidity | 1.5909 | 0.5026 | 0.3983% | -1580.00 |
| vol_60m | volatility | 1.4835 | 0.4949 | 0.1410% | -340.00 |
| turnover_ma_ratio_5_20 | turnover | 1.4197 | 0.4930 | 0.0892% | -460.00 |
| volume_ma_ratio_5_20 | volume | 1.4167 | 0.4930 | 0.0892% | -400.00 |
| minute_norm | time | 1.1311 | 0.4935 | 0.1058% | -820.00 |
| oi_delta | open_interest | 0.9276 | 0.4931 | 0.1079% | -1340.00 |
| acc_mom_5_15 | momentum | 0.7970 | 0.4938 | 0.1058% | -640.00 |

## Top10 Annualized Return (without cost)

| factor | group | sharpe_wo_cost | ir_wo_cost | annual_return_wo_cost | mdd_wo_cost |
|---|---|---:|---:|---:|---:|
| rev_3m | reversal | 4.2137 | 0.5047 | 0.4335% | -660.00 |
| rev_5m | reversal | 3.7346 | 0.5045 | 0.4273% | -500.00 |
| illiq_1m | liquidity | 1.5909 | 0.5026 | 0.3983% | -1580.00 |
| is_close_30m | time | 0.5614 | 0.5076 | 0.3070% | -5360.00 |
| is_open_30m | time | 0.5614 | 0.5076 | 0.3070% | -5360.00 |
| downside_vol_20 | volatility | 1.7113 | 0.4947 | 0.1514% | -520.00 |
| vol_60m | volatility | 1.4835 | 0.4949 | 0.1410% | -340.00 |
| oi_delta | open_interest | 0.9276 | 0.4931 | 0.1079% | -1340.00 |
| minute_norm | time | 1.1311 | 0.4935 | 0.1058% | -820.00 |
| acc_mom_5_15 | momentum | 0.7970 | 0.4938 | 0.1058% | -640.00 |

## Top10 Information Ratio (without cost)

| factor | group | sharpe_wo_cost | ir_wo_cost | annual_return_wo_cost | mdd_wo_cost |
|---|---|---:|---:|---:|---:|
| is_open_30m | time | 0.5614 | 0.5076 | 0.3070% | -5360.00 |
| is_close_30m | time | 0.5614 | 0.5076 | 0.3070% | -5360.00 |
| rev_3m | reversal | 4.2137 | 0.5047 | 0.4335% | -660.00 |
| rev_5m | reversal | 3.7346 | 0.5045 | 0.4273% | -500.00 |
| illiq_1m | liquidity | 1.5909 | 0.5026 | 0.3983% | -1580.00 |
| vol_60m | volatility | 1.4835 | 0.4949 | 0.1410% | -340.00 |
| downside_vol_20 | volatility | 1.7113 | 0.4947 | 0.1514% | -520.00 |
| acc_mom_5_15 | momentum | 0.7970 | 0.4938 | 0.1058% | -640.00 |
| minute_norm | time | 1.1311 | 0.4935 | 0.1058% | -820.00 |
| oi_delta | open_interest | 0.9276 | 0.4931 | 0.1079% | -1340.00 |

## Top10 OOS Sharpe (without cost)

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

## Top10 OOS Sharpe (without cost) Correlation Matrix

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
