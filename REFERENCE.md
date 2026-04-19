# References

## Factor Research and CTA Methodology

1. Moskowitz, T. J., Ooi, Y. H., Pedersen, L. H. (2012). Time Series Momentum. Journal of Financial Economics.
2. Baz, J., Granger, N., Harvey, C. R., Le Roux, N., Rattray, S. (2015). Dissecting Investment Strategies in the Cross Section and Time Series.
3. Cartea, A., Jaimungal, S., Penalva, J. (2015). Algorithmic and High-Frequency Trading.
4. Hasbrouck, J. (2007). Empirical Market Microstructure.
5. Almgren, R., Chriss, N. (2001). Optimal Execution of Portfolio Transactions.
6. Amihud, Y. (2002). Illiquidity and stock returns: cross-section and time-series effects.

## Risk and Performance Metrics

1. Sharpe, W. F. (1994). The Sharpe Ratio.
2. Grinold, R. C., Kahn, R. N. (2000). Active Portfolio Management.
3. Magdon-Ismail, M., Atiya, A. F. (2004). Maximum Drawdown.

## Implementation Notes

- Correlation-constrained factor selection is implemented in `validation.py`.
- Strict max pairwise correlation control is configured by:
  - `factor.max_pair_corr`
  - `factor.strict_corr_limit`
- Average Sharpe without transaction cost for all factors is reported in:
  - `artifacts/all_factor_backtest_<run_id>/run_summary.json`
