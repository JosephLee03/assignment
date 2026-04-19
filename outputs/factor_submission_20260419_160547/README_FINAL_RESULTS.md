# Factor Library Standalone Report (20260419_160547)

## Universe
- trading_days: 243
- date_range: 20250102 ~ 20251231
- factor_count: 56
- ic_method: pearson
- signal_rule: rolling_63_days_quantile, long>= 0.995, short<= 0.005
- annualization_days: 252
- average_sharpe_without_cost: -1.227757
- average_sharpe_with_cost: -11.194394

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
