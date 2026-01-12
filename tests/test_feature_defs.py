from __future__ import annotations

import pandas as pd

from slfsi.config.schema import ColumnSchema
from slfsi.features.daily import compute_daily_features, compute_post_upsample_features
from slfsi.features.monthly import compute_monthly_features


def test_daily_feature_columns_created() -> None:
    schema = ColumnSchema()
    daily = pd.DataFrame(
        {
            "date": pd.date_range("2020-01-01", periods=5, freq="D"),
            "usd_lkr": [100, 101, 102, 103, 104],
            "aspi": [2000, 1990, 2010, 2020, 2030],
            "gold_lkr": [9000, 9050, 9100, 9200, 9300],
            "gold_usd": [1500, 1505, 1510, 1520, 1530],
            "equity_turnover": [10, 12, 11, 13, 12],
            "market_cap": [100, 101, 102, 103, 104],
            "isb_yield": [7.0, 7.1, 7.2, 7.3, 7.4],
            "us_10y_yield": [2.0, 2.0, 2.1, 2.1, 2.2],
            "tbond_yield": [8.0, 8.1, 8.2, 8.3, 8.4],
            "tbill_primary": [6.0, 6.1, 6.1, 6.2, 6.2],
            "awcmr": [5.0, 5.1, 5.2, 5.3, 5.4],
            "policy_ceiling": [6.0, 6.0, 6.0, 6.0, 6.0],
            "ncpi_yoy_pct": [4.0, 4.1, 4.2, 4.3, 4.4],
            "gross_reserves_usd_m": [3000, 2990, 2980, 2970, 2960],
        }
    )

    daily = compute_daily_features(daily, schema, vol_window=2, vol_min_periods=1)
    daily = compute_post_upsample_features(daily, schema)

    for col in [
        schema.r_fx,
        schema.vol_fx_20d,
        schema.r_eq,
        schema.vol_eq_20d,
        schema.r_eq_real,
        schema.implied_fx,
        schema.gold_premium_pct,
        schema.turnover_ratio,
        schema.embi_spread_approx,
        schema.yield_curve_slope,
        schema.interbank_spread,
        schema.real_policy_rate,
        schema.reserve_slope_3m,
    ]:
        assert col in daily.columns


def test_monthly_feature_columns_created() -> None:
    schema = ColumnSchema()
    monthly = pd.DataFrame(
        {
            "date": pd.to_datetime(["2020-01-01", "2020-02-01"]),
            "gross_reserves_usd_m": [3000, 2500],
            "policy_ceiling": [6.0, 6.0],
            "ncpi_yoy_pct": [4.0, 5.0],
        }
    )

    result = compute_monthly_features(
        monthly,
        schema,
        monthly_imports_usd_m=1500,
        pboc_swap_usd_m=500,
        pboc_swap_start=pd.Timestamp("2020-02-01"),
    )

    assert schema.import_cover_months in result.columns
    assert schema.net_import_cover_months in result.columns
    assert schema.net_usable_reserves_usd_m in result.columns
    assert schema.real_policy_rate in result.columns

    assert result.loc[0, schema.net_usable_reserves_usd_m] == 3000
    assert result.loc[1, schema.net_usable_reserves_usd_m] == 2000
