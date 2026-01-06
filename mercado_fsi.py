#!/usr/bin/env python3
"""
Mercado-Park (2014) Financial Stress Index Implementation
=========================================================
Implements the official ADB/ARIC FSI methodology for Sri Lanka.

Components:
1. Banking Sector Beta (β)
2. Equity Market Returns
3. Equity Market Volatility (GARCH)
4. Sovereign Debt Spread
5. Exchange Market Pressure Index (EMPI)

Reference: Mercado & Park (2014), ADB Working Paper
"""

import pandas as pd
import numpy as np
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# CONFIGURATION
# ============================================================

ROLLING_WINDOW = 36  # 36-month rolling for beta calculation
EMPI_LOOKBACK = 60   # 60-month rolling for EMPI standardization
MIN_PERIODS = 12     # Minimum periods for rolling calculations

# ============================================================
# COMPONENT 1: BANKING SECTOR BETA
# ============================================================

def calculate_banking_beta(bank_returns, market_returns, window=ROLLING_WINDOW):
    """
    Calculate rolling banking sector beta.

    β = Cov(r_bank, r_market) / Var(r_market)

    Banking stress ↑ when β > 1 (bank moves more than market)
    """
    # Rolling covariance and variance
    cov = bank_returns.rolling(window, min_periods=MIN_PERIODS).cov(market_returns)
    var = market_returns.rolling(window, min_periods=MIN_PERIODS).var()

    beta = cov / var

    # Handle extreme values
    beta = beta.clip(-5, 5)

    return beta


# ============================================================
# COMPONENT 2: EQUITY MARKET RETURNS
# ============================================================

def calculate_equity_returns(prices):
    """
    Calculate log returns.

    r_t = ln(P_t) - ln(P_{t-1})

    Stress ↑ when returns are negative
    """
    returns = np.log(prices) - np.log(prices.shift(1))
    return returns


# ============================================================
# COMPONENT 3: GARCH(1,1) VOLATILITY
# ============================================================

def calculate_garch_volatility(returns, p=1, q=1):
    """
    Fit GARCH(1,1) and extract conditional volatility.

    σ²_t = ω + α·ε²_{t-1} + β·σ²_{t-1}

    Stress ↑ when volatility is high
    """
    try:
        from arch import arch_model

        # Remove NaN and scale for GARCH fitting
        clean_returns = returns.dropna() * 100  # percentage scale

        if len(clean_returns) < 100:
            print("  Warning: Insufficient data for GARCH, using rolling std")
            return returns.rolling(20, min_periods=5).std()

        # Fit GARCH(1,1)
        model = arch_model(clean_returns, vol='Garch', p=p, q=q, mean='Constant')
        result = model.fit(disp='off', show_warning=False)

        # Get conditional volatility
        cond_vol = result.conditional_volatility / 100  # back to decimal

        # Reindex to original dates
        vol_series = pd.Series(index=returns.index, dtype=float)
        vol_series.loc[clean_returns.index] = cond_vol.values

        return vol_series

    except ImportError:
        print("  Warning: arch package not installed, using rolling std")
        return returns.rolling(20, min_periods=5).std()
    except Exception as e:
        print(f"  Warning: GARCH failed ({e}), using rolling std")
        return returns.rolling(20, min_periods=5).std()


# ============================================================
# COMPONENT 4: SOVEREIGN DEBT SPREAD
# ============================================================

def calculate_debt_spread(long_yield, short_yield):
    """
    Calculate term spread.

    Spread = Long-term yield - Short-term yield

    Typically 10Y - 2Y (using tbond - tbill as proxy)
    Stress ↑ when spread inverts (negative) or extremely high
    """
    spread = long_yield - short_yield
    return spread


# ============================================================
# COMPONENT 5: EXCHANGE MARKET PRESSURE INDEX (EMPI)
# ============================================================

def calculate_empi(fx_rate, reserves, lookback=EMPI_LOOKBACK):
    """
    Calculate Exchange Market Pressure Index.

    EMPI = [(Δe - μ_Δe)/σ_Δe] - [(ΔRES - μ_ΔRES)/σ_ΔRES]

    Where:
    - Δe = % change in exchange rate (depreciation positive)
    - ΔRES = % change in reserves

    Stress ↑ when currency depreciates AND reserves fall
    """
    # Calculate percentage changes
    delta_e = fx_rate.pct_change()
    delta_res = reserves.pct_change()

    # Rolling standardization
    e_mean = delta_e.rolling(lookback, min_periods=MIN_PERIODS).mean()
    e_std = delta_e.rolling(lookback, min_periods=MIN_PERIODS).std()

    res_mean = delta_res.rolling(lookback, min_periods=MIN_PERIODS).mean()
    res_std = delta_res.rolling(lookback, min_periods=MIN_PERIODS).std()

    # Standardized components
    e_standardized = (delta_e - e_mean) / e_std
    res_standardized = (delta_res - res_mean) / res_std

    # EMPI: depreciation pressure - reserve support
    # Positive = stress (depreciation without reserve support)
    empi = e_standardized - res_standardized

    # Clip extreme values
    empi = empi.clip(-5, 5)

    return empi


# ============================================================
# AGGREGATION: VARIANCE-EQUAL WEIGHTS
# ============================================================

def aggregate_fsi_variance_equal(components_df):
    """
    Aggregate FSI components using variance-equal weights.

    1. Standardize each component (z-score)
    2. Average standardized components

    This gives equal weight to each component's variability.
    """
    # Standardize each component
    standardized = pd.DataFrame(index=components_df.index)

    for col in components_df.columns:
        series = components_df[col]
        mean = series.mean()
        std = series.std()
        if std > 0:
            standardized[col] = (series - mean) / std
        else:
            standardized[col] = 0

    # Equal-weighted average
    fsi = standardized.mean(axis=1)

    return fsi, standardized


def aggregate_fsi_pca(components_df, n_components=1):
    """
    Aggregate FSI using PCA first principal component.

    The first PC captures the common variance across all components.
    """
    from sklearn.preprocessing import StandardScaler
    from sklearn.decomposition import PCA

    # Drop rows with any NaN
    clean_df = components_df.dropna()

    if len(clean_df) < 30:
        print("  Warning: Insufficient data for PCA")
        return None, None

    # Standardize
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(clean_df)

    # PCA
    pca = PCA(n_components=n_components)
    pc1 = pca.fit_transform(X_scaled)[:, 0]

    # Create series with original index
    fsi_pca = pd.Series(pc1, index=clean_df.index, name='FSI_PCA')

    # Component loadings
    loadings = pd.DataFrame(
        pca.components_.T,
        columns=['PC1'],
        index=components_df.columns
    )

    print(f"\n  PCA Explained Variance: {pca.explained_variance_ratio_[0]*100:.1f}%")
    print("  Component Loadings:")
    for idx, val in loadings['PC1'].items():
        print(f"    {idx}: {val:.3f}")

    return fsi_pca, loadings


# ============================================================
# MAIN IMPLEMENTATION
# ============================================================

def compute_mercado_fsi(data, freq='M'):
    """
    Compute the full Mercado-Park FSI.

    Parameters:
    -----------
    data : DataFrame with daily data
    freq : 'M' for monthly, 'D' for daily

    Returns:
    --------
    fsi_df : DataFrame with FSI and components
    """
    print("=" * 70)
    print("MERCADO-PARK FSI IMPLEMENTATION")
    print("=" * 70)

    # Convert to specified frequency
    if freq == 'M':
        print(f"\nConverting to monthly frequency...")
        df = data.set_index('date').resample('MS').first().reset_index()
    else:
        df = data.copy()

    print(f"Observations: {len(df)}")
    print(f"Date range: {df['date'].min()} to {df['date'].max()}")

    # Initialize components DataFrame
    components = pd.DataFrame(index=df.index)
    components['date'] = df['date']

    # ----------------------------------------------------------
    # Component 1: Banking Beta
    # ----------------------------------------------------------
    print("\n" + "-" * 50)
    print("Component 1: BANKING SECTOR BETA")
    print("-" * 50)

    if 'sl20_index' in df.columns and 'aspi' in df.columns:
        # Calculate returns
        bank_returns = calculate_equity_returns(df['sl20_index'])
        market_returns = calculate_equity_returns(df['aspi'])

        # Calculate beta
        beta = calculate_banking_beta(bank_returns, market_returns)
        components['banking_beta'] = beta.values

        valid = components['banking_beta'].notna().sum()
        print(f"  Using: SL20 Index vs ASPI")
        print(f"  Valid observations: {valid}")
        print(f"  Mean beta: {components['banking_beta'].mean():.3f}")
    else:
        print("  ⚠ Missing sl20_index or aspi - component unavailable")
        components['banking_beta'] = np.nan

    # ----------------------------------------------------------
    # Component 2: Equity Returns
    # ----------------------------------------------------------
    print("\n" + "-" * 50)
    print("Component 2: EQUITY MARKET RETURNS")
    print("-" * 50)

    if 'aspi' in df.columns:
        eq_returns = calculate_equity_returns(df['aspi'])
        # Invert so positive = stress (negative returns = stress)
        components['equity_returns_inv'] = -eq_returns.values

        valid = components['equity_returns_inv'].notna().sum()
        print(f"  Using: ASPI log returns (inverted)")
        print(f"  Valid observations: {valid}")
        print(f"  Mean monthly return: {eq_returns.mean()*100:.2f}%")
    else:
        print("  ⚠ Missing aspi - component unavailable")
        components['equity_returns_inv'] = np.nan

    # ----------------------------------------------------------
    # Component 3: GARCH Volatility
    # ----------------------------------------------------------
    print("\n" + "-" * 50)
    print("Component 3: EQUITY VOLATILITY (GARCH)")
    print("-" * 50)

    if 'aspi' in df.columns:
        eq_returns = calculate_equity_returns(df['aspi'])
        garch_vol = calculate_garch_volatility(eq_returns)
        components['equity_volatility'] = garch_vol.values

        valid = components['equity_volatility'].notna().sum()
        print(f"  Using: GARCH(1,1) on ASPI returns")
        print(f"  Valid observations: {valid}")
        if valid > 0:
            print(f"  Mean volatility: {components['equity_volatility'].mean()*100:.2f}%")
    else:
        print("  ⚠ Missing aspi - component unavailable")
        components['equity_volatility'] = np.nan

    # ----------------------------------------------------------
    # Component 4: Sovereign Debt Spread
    # ----------------------------------------------------------
    print("\n" + "-" * 50)
    print("Component 4: SOVEREIGN DEBT SPREAD")
    print("-" * 50)

    if 'tbond_yield' in df.columns and 'tbill_secondary' in df.columns:
        spread = calculate_debt_spread(df['tbond_yield'], df['tbill_secondary'])
        components['debt_spread'] = spread.values

        valid = components['debt_spread'].notna().sum()
        print(f"  Using: T-Bond yield - T-Bill secondary")
        print(f"  Valid observations: {valid}")
        if valid > 0:
            print(f"  Mean spread: {components['debt_spread'].mean()*100:.2f} bps")
    elif 'yield_curve_slope' in df.columns:
        # Use pre-calculated slope
        components['debt_spread'] = df['yield_curve_slope'].values
        valid = components['debt_spread'].notna().sum()
        print(f"  Using: Pre-calculated yield_curve_slope")
        print(f"  Valid observations: {valid}")
    else:
        print("  ⚠ Missing yield data - component unavailable")
        components['debt_spread'] = np.nan

    # ----------------------------------------------------------
    # Component 5: EMPI
    # ----------------------------------------------------------
    print("\n" + "-" * 50)
    print("Component 5: EXCHANGE MARKET PRESSURE INDEX")
    print("-" * 50)

    if 'usd_lkr' in df.columns and 'gross_reserves_usd_m' in df.columns:
        empi = calculate_empi(df['usd_lkr'], df['gross_reserves_usd_m'])
        components['empi'] = empi.values

        valid = components['empi'].notna().sum()
        print(f"  Using: USD/LKR + Gross Reserves")
        print(f"  Valid observations: {valid}")
        if valid > 0:
            print(f"  Mean EMPI: {components['empi'].mean():.3f}")
    else:
        print("  ⚠ Missing FX or reserves data - component unavailable")
        components['empi'] = np.nan

    # ----------------------------------------------------------
    # Aggregation
    # ----------------------------------------------------------
    print("\n" + "=" * 70)
    print("FSI AGGREGATION")
    print("=" * 70)

    # Select available components
    component_cols = ['banking_beta', 'equity_returns_inv', 'equity_volatility',
                      'debt_spread', 'empi']

    available_components = []
    for col in component_cols:
        if col in components.columns and components[col].notna().sum() > 30:
            available_components.append(col)

    print(f"\nAvailable components: {len(available_components)}/5")
    for col in available_components:
        print(f"  ✓ {col}")

    if len(available_components) < 2:
        print("\n⚠ Insufficient components for FSI aggregation")
        return components

    # Method 1: Variance-equal weights
    print("\n--- Method 1: Variance-Equal Weights ---")
    components_only = components[available_components].copy()
    fsi_ve, standardized = aggregate_fsi_variance_equal(components_only)
    components['fsi_variance_equal'] = fsi_ve.values

    # Add standardized components
    for col in standardized.columns:
        components[f'{col}_std'] = standardized[col].values

    print(f"  FSI range: {fsi_ve.min():.2f} to {fsi_ve.max():.2f}")
    print(f"  Valid observations: {fsi_ve.notna().sum()}")

    # Method 2: PCA
    print("\n--- Method 2: PCA (First Principal Component) ---")
    fsi_pca, loadings = aggregate_fsi_pca(components_only)
    if fsi_pca is not None:
        # Align to components index
        components['fsi_pca'] = np.nan
        components.loc[fsi_pca.index, 'fsi_pca'] = fsi_pca.values

    return components


# ============================================================
# MAIN EXECUTION
# ============================================================

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("LOADING DATA")
    print("=" * 70)

    # Load data
    panel = pd.read_csv('data/merged/slfsi_daily_panel.csv', parse_dates=['date'])
    print(f"Loaded {len(panel)} daily observations")

    # Compute monthly FSI
    fsi_df = compute_mercado_fsi(panel, freq='M')

    # Save results
    output_path = 'data/merged/mercado_fsi_monthly.csv'
    fsi_df.to_csv(output_path, index=False)
    print(f"\n✓ Saved to {output_path}")

    # Summary statistics
    print("\n" + "=" * 70)
    print("FSI SUMMARY STATISTICS")
    print("=" * 70)

    fsi_cols = ['fsi_variance_equal', 'fsi_pca']
    for col in fsi_cols:
        if col in fsi_df.columns:
            series = fsi_df[col].dropna()
            print(f"\n{col}:")
            print(f"  N: {len(series)}")
            print(f"  Mean: {series.mean():.3f}")
            print(f"  Std: {series.std():.3f}")
            print(f"  Min: {series.min():.3f}")
            print(f"  Max: {series.max():.3f}")

            # Identify stress periods (FSI > 1)
            stress_periods = fsi_df[fsi_df[col] > 1][['date', col]]
            if len(stress_periods) > 0:
                print(f"\n  Stress periods (FSI > 1):")
                for _, row in stress_periods.head(10).iterrows():
                    print(f"    {row['date'].strftime('%Y-%m')}: {row[col]:.2f}")

    # Plot if possible
    try:
        import matplotlib.pyplot as plt

        fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=True)

        # FSI
        ax1 = axes[0]
        fsi_df.set_index('date')['fsi_variance_equal'].plot(ax=ax1, linewidth=1.5, color='navy')
        ax1.axhline(0, color='gray', linestyle='--', alpha=0.5)
        ax1.axhline(1, color='red', linestyle='--', alpha=0.5, label='Stress threshold')
        ax1.axhline(-1, color='green', linestyle='--', alpha=0.5)
        ax1.set_ylabel('FSI')
        ax1.set_title('Mercado-Park Financial Stress Index - Sri Lanka')
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # Add crisis annotations
        crisis_dates = [
            ('2019-04', 'Easter\nBombing'),
            ('2020-03', 'COVID'),
            ('2022-04', 'Debt\nDefault'),
        ]
        for date_str, label in crisis_dates:
            try:
                ax1.axvline(pd.Timestamp(date_str + '-01'), color='red', alpha=0.3, linestyle=':')
            except:
                pass

        # Components
        ax2 = axes[1]
        component_cols = ['banking_beta_std', 'equity_returns_inv_std', 'equity_volatility_std']
        available_cols = [c for c in component_cols if c in fsi_df.columns]
        if available_cols:
            fsi_df.set_index('date')[available_cols].plot(ax=ax2, alpha=0.7, linewidth=1)
            ax2.set_ylabel('Standardized')
            ax2.set_title('Equity Market Components')
            ax2.legend(loc='upper left')
            ax2.grid(True, alpha=0.3)

        # EMPI
        ax3 = axes[2]
        if 'empi_std' in fsi_df.columns:
            fsi_df.set_index('date')['empi_std'].plot(ax=ax3, color='darkgreen', linewidth=1.5)
            ax3.set_ylabel('EMPI (Standardized)')
            ax3.set_title('Exchange Market Pressure Index')
            ax3.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig('figures/mercado_fsi.png', dpi=150, bbox_inches='tight')
        print("\n✓ Saved plot to figures/mercado_fsi.png")
        plt.close()

    except Exception as e:
        print(f"\n⚠ Could not create plot: {e}")

    print("\n" + "=" * 70)
    print("MERCADO FSI IMPLEMENTATION COMPLETE")
    print("=" * 70)
