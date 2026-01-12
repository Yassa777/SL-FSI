"""Mercado-Park FSI implementation."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Mapping

import numpy as np
import pandas as pd

from slfsi.config.schema import ColumnSchema


@dataclass(frozen=True)
class MercadoConfig:
    """Configuration for Mercado-Park FSI."""

    rolling_window: int = 36
    empi_lookback: int = 60
    min_periods: int = 12
    debt_spread_min_obs: int = 36


def calculate_banking_beta(
    bank_returns: pd.Series, market_returns: pd.Series, window: int, min_periods: int
) -> pd.Series:
    cov = bank_returns.rolling(window, min_periods=min_periods).cov(market_returns)
    var = market_returns.rolling(window, min_periods=min_periods).var()
    beta = cov / var
    return beta.clip(-5, 5)


def calculate_equity_returns(prices: pd.Series) -> pd.Series:
    return np.log(prices) - np.log(prices.shift(1))


def calculate_garch_volatility(returns: pd.Series) -> pd.Series:
    try:
        from arch import arch_model
    except ImportError:
        return returns.rolling(20, min_periods=5).std()

    clean_returns = returns.dropna() * 100
    if len(clean_returns) < 100:
        return returns.rolling(20, min_periods=5).std()

    model = arch_model(clean_returns, vol="Garch", p=1, q=1, mean="Constant")
    result = model.fit(disp="off", show_warning=False)
    cond_vol = result.conditional_volatility / 100

    vol_series = pd.Series(index=returns.index, dtype=float)
    vol_series.loc[clean_returns.index] = cond_vol.values
    return vol_series


def calculate_debt_spread(long_yield: pd.Series, short_yield: pd.Series) -> pd.Series:
    return long_yield - short_yield


def calculate_empi(
    fx_rate: pd.Series,
    reserves: pd.Series,
    lookback: int,
    min_periods: int,
) -> pd.Series:
    delta_e = fx_rate.pct_change()
    delta_res = reserves.pct_change()

    e_mean = delta_e.rolling(lookback, min_periods=min_periods).mean()
    e_std = delta_e.rolling(lookback, min_periods=min_periods).std()
    res_mean = delta_res.rolling(lookback, min_periods=min_periods).mean()
    res_std = delta_res.rolling(lookback, min_periods=min_periods).std()

    e_standardized = (delta_e - e_mean) / e_std
    res_standardized = (delta_res - res_mean) / res_std
    empi = e_standardized - res_standardized
    return empi.clip(-5, 5)


def aggregate_fsi_variance_equal(components: pd.DataFrame) -> tuple[pd.Series, pd.DataFrame]:
    standardized = pd.DataFrame(index=components.index)
    for col in components.columns:
        series = components[col]
        std = series.std()
        standardized[col] = (series - series.mean()) / std if std else 0.0
    fsi = standardized.mean(axis=1)
    return fsi, standardized


def aggregate_fsi_pca(components: pd.DataFrame) -> tuple[pd.Series | None, pd.DataFrame | None]:
    try:
        from sklearn.preprocessing import StandardScaler
        from sklearn.decomposition import PCA
    except ImportError:
        return None, None

    clean = components.dropna()
    if len(clean) < 30:
        return None, None

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(clean)
    pca = PCA(n_components=1)
    pc1 = pca.fit_transform(X_scaled)[:, 0]

    fsi_pca = pd.Series(pc1, index=clean.index, name="fsi_pca")
    loadings = pd.DataFrame(pca.components_.T, columns=["pc1"], index=components.columns)
    return fsi_pca, loadings


def compute_mercado_fsi(
    data: pd.DataFrame,
    schema: ColumnSchema,
    config: MercadoConfig,
    *,
    data_is_monthly: bool = True,
) -> pd.DataFrame:
    """Compute Mercado-Park FSI components and index."""
    logger = logging.getLogger(__name__)
    if not data_is_monthly:
        df = data.set_index(schema.date).resample("MS").first().reset_index()
    else:
        df = data.copy()

    components = pd.DataFrame(index=df.index)
    components[schema.date] = df[schema.date]

    if schema.sl20_index in df.columns and schema.aspi in df.columns:
        bank_returns = calculate_equity_returns(df[schema.sl20_index])
        market_returns = calculate_equity_returns(df[schema.aspi])
        components["banking_beta"] = calculate_banking_beta(
            bank_returns, market_returns, config.rolling_window, config.min_periods
        )
    else:
        logger.warning("Missing sl20_index/aspi for banking beta")
        components["banking_beta"] = np.nan

    if schema.aspi in df.columns:
        eq_returns = calculate_equity_returns(df[schema.aspi])
        components["equity_returns_inv"] = -eq_returns.values
        components["equity_volatility"] = calculate_garch_volatility(eq_returns).values
    else:
        logger.warning("Missing aspi for equity components")
        components["equity_returns_inv"] = np.nan
        components["equity_volatility"] = np.nan

    if schema.tbond_yield in df.columns and schema.tbill_secondary in df.columns:
        components["debt_spread"] = calculate_debt_spread(
            df[schema.tbond_yield], df[schema.tbill_secondary]
        ).values
    else:
        logger.warning("Missing tbond/tbill for debt spread")
        components["debt_spread"] = np.nan

    if schema.usd_lkr in df.columns and schema.gross_reserves_usd_m in df.columns:
        components["empi"] = calculate_empi(
            df[schema.usd_lkr],
            df[schema.gross_reserves_usd_m],
            config.empi_lookback,
            config.min_periods,
        ).values
    else:
        logger.warning("Missing fx/reserves for EMPI")
        components["empi"] = np.nan

    component_cols = [
        col
        for col in ["banking_beta", "equity_returns_inv", "equity_volatility", "debt_spread", "empi"]
        if col in components.columns and components[col].notna().sum() > 30
    ]

    if len(component_cols) < 2:
        logger.warning("Insufficient components for FSI aggregation")
        return components

    fsi_ve, standardized = aggregate_fsi_variance_equal(components[component_cols])
    components["fsi_variance_equal"] = fsi_ve.values
    for col in standardized.columns:
        components[f"{col}_std"] = standardized[col].values

    fsi_pca, _ = aggregate_fsi_pca(components[component_cols])
    if fsi_pca is not None:
        components["fsi_pca"] = fsi_pca.values

    return components
