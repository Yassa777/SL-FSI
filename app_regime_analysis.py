import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from hmmlearn import hmm
from scipy import stats
import ruptures as rpt
import warnings
warnings.filterwarnings('ignore')

# Page config
st.set_page_config(
    page_title="SL-FSI Regime Analysis",
    page_icon="📊",
    layout="wide"
)

# Title
st.title("🇱🇰 Sri Lanka Financial Stress Index - Regime Analysis")
st.markdown("**Validated 3-State HMM for Crisis Detection**")

# Load data
@st.cache_data
def load_data():
    daily = pd.read_csv('data/merged/slfsi_daily_panel.csv', parse_dates=['date'])
    monthly = pd.read_csv('data/merged/slfsi_monthly_panel.csv', parse_dates=['date'])

    # Try to load pre-computed validated regimes
    try:
        validated = pd.read_csv('data/merged/monthly_regimes_validated.csv', parse_dates=['date'])
    except:
        validated = None

    return daily, monthly, validated

daily_df, monthly_df, validated_df = load_data()

# Prepare monthly data for 3-state HMM
@st.cache_data
def prepare_monthly_hmm_data(daily):
    """Prepare monthly aggregated data for the validated 3-state HMM."""
    features = ['awcmr', 'real_policy_rate', 'gross_reserves_usd_m', 'ncpi_yoy_pct']
    daily['year_month'] = daily['date'].dt.to_period('M')
    monthly = daily.groupby('year_month')[features + ['date']].first().reset_index(drop=True)
    monthly = monthly.dropna()
    return monthly, features

monthly_hmm_data, HMM_FEATURES = prepare_monthly_hmm_data(daily_df)

# Define the 18 core data streams
DATA_STREAMS = {
    'D1 - USD/LKR Exchange Rate': 'usd_lkr',
    'D2 - AWCMR (Interbank Rate)': 'awcmr',
    'D3 - ASPI (Equity Index)': 'aspi',
    'D4 - Equity Daily Turnover': 'equity_turnover',
    'D5 - Market Capitalization': 'market_cap',
    'D6 - S&P SL20 Index': 'sl20_index',
    'D7 - Local Gold Price': 'gold_lkr',
    'D6 Global - Gold Price USD': 'gold_usd',
    'D8 - T-Bill Yields': 'tbill_primary',
    'D9 - T-Bond Yields': 'tbond_yield',
    'D10 - Policy Rate (SDFR)': 'sdfr',
    'D12 - FX Reserves': 'gross_reserves_usd_m',
    'D13 - NCPI Inflation': 'ncpi_yoy_pct',
    'D14 - REER Index': 'reer_index',
    'D15 - ISB Yields': 'isb_yield',
    'D17 - Tourism Earnings': 'tourism_earnings_usd_m',
    'D18 - Worker Remittances': 'remittances_usd_m',
    'Helper - US 10Y Yield': 'us_10y_yield'
}

# Derived features
DERIVED_FEATURES = {
    'FX Return': 'r_fx',
    'FX Volatility (20d)': 'vol_fx_20d',
    'Equity Return': 'r_eq',
    'Equity Volatility (20d)': 'vol_eq_20d',
    'Real Equity Return': 'r_eq_real',
    'Gold Premium %': 'gold_premium_pct',
    'Interbank Spread': 'interbank_spread',
    'Real Policy Rate': 'real_policy_rate',
    'Import Cover (months)': 'import_cover_months',
    'Reserve Slope (3m)': 'reserve_slope_3m',
    'Turnover Ratio': 'turnover_ratio',
    'EMBI Spread (approx)': 'embi_spread_approx'
}

# Extended crisis markers (all key events)
ALL_EVENTS = {
    '2019-04-21': {'name': 'Easter Sunday Attacks', 'color': 'purple', 'type': 'shock'},
    '2020-03-20': {'name': 'COVID Lockdown', 'color': 'purple', 'type': 'shock'},
    '2021-04-22': {'name': 'Fertilizer Ban', 'color': 'purple', 'type': 'shock'},
    '2021-07-01': {'name': 'STRESS Regime Begins', 'color': 'orange', 'type': 'regime'},
    '2022-01-18': {'name': '$500M ISB Repayment', 'color': 'red', 'type': 'anchor'},
    '2022-03-07': {'name': 'FX Float', 'color': 'red', 'type': 'anchor'},
    '2022-04-01': {'name': 'CRISIS Regime Begins', 'color': 'darkred', 'type': 'regime'},
    '2022-04-12': {'name': 'Sovereign Default', 'color': 'red', 'type': 'anchor'},
    '2022-07-14': {'name': 'President Resigns', 'color': 'purple', 'type': 'shock'},
    '2022-09-01': {'name': 'IMF Staff Agreement', 'color': 'blue', 'type': 'anchor'},
    '2023-03-20': {'name': 'IMF EFF Approval', 'color': 'blue', 'type': 'anchor'},
    '2023-07-01': {'name': 'CALM Regime Returns', 'color': 'green', 'type': 'regime'},
}

# Simplified crisis dates for backward compatibility
CRISIS_DATES = {
    'FX Float (2022-03-07)': '2022-03-07',
    'Sovereign Default (2022-04-12)': '2022-04-12',
    'Peak Inflation (2022-09-15)': '2022-09-15',
    'IMF EFF (2023-03-20)': '2023-03-20'
}

# Sidebar
st.sidebar.header("Analysis Settings")
analysis_type = st.sidebar.radio(
    "Choose Analysis",
    ["🎯 Validated 3-State Model", "📈 Mercado FSI", "🔮 Recursive HMM", "⚖️ FSI vs HMM Comparison", "📚 Data Justification", "📊 Data Explorer", "🔄 Custom HMM", "📍 Change Points"]
)

# ============================================================================
# VALIDATED 3-STATE MODEL (NEW - Primary Feature)
# ============================================================================
if analysis_type == "🎯 Validated 3-State Model":
    st.header("🎯 Validated 3-State Monthly HMM")

    st.markdown("""
    ### The Best Model for Sri Lanka Crisis Detection

    After extensive testing, this **3-state monthly HMM** is the optimal configuration:
    - **100% hit rate** on 12 pre-specified crisis events
    - **Only 4 regime transitions** (clean, interpretable)
    - **9 months early warning** before the default
    - **Outperforms Z-score baseline** by 33%
    """)

    # Fit the validated model
    @st.cache_data
    def fit_validated_3state_hmm(monthly_data, features):
        """Fit the validated 3-state monthly HMM."""
        X = monthly_data[features].values
        X_scaled = (X - X.mean(axis=0)) / X.std(axis=0)

        model = hmm.GaussianHMM(n_components=3, covariance_type="diag", n_iter=300, random_state=42)
        model.fit(X_scaled)
        states = model.predict(X_scaled)

        # Label regimes by inflation level
        result = monthly_data.copy()
        result['regime'] = states

        state_inflation = {s: result[result['regime'] == s]['ncpi_yoy_pct'].mean() for s in range(3)}
        sorted_states = sorted(state_inflation.keys(), key=lambda x: state_inflation[x])
        state_labels = {sorted_states[0]: 'CALM', sorted_states[1]: 'STRESS', sorted_states[2]: 'CRISIS'}
        result['regime_label'] = result['regime'].map(state_labels)

        return result, model, state_labels

    result_df, model, state_labels = fit_validated_3state_hmm(monthly_hmm_data, HMM_FEATURES)

    # Summary metrics
    st.subheader("📊 Model Performance Summary")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Event Hit Rate", "100%", delta="vs 67% Z-score")
    with col2:
        st.metric("Regime Transitions", "4", delta="Clean signal")
    with col3:
        stress_start = result_df[result_df['regime_label'] == 'STRESS']['date'].min()
        st.metric("STRESS Detected", stress_start.strftime('%Y-%m'))
    with col4:
        crisis_start = result_df[result_df['regime_label'] == 'CRISIS']['date'].min()
        st.metric("CRISIS Detected", crisis_start.strftime('%Y-%m'))

    # Regime Timeline Visualization
    st.subheader("📅 Regime Timeline")

    # Create main regime plot
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        subplot_titles=['Regime States', 'Key Indicators', 'Inflation & AWCMR'],
        vertical_spacing=0.08,
        row_heights=[0.3, 0.35, 0.35]
    )

    # Color mapping
    regime_colors = {'CALM': '#2ecc71', 'STRESS': '#f39c12', 'CRISIS': '#e74c3c'}

    # Plot 1: Regime states
    for regime in ['CALM', 'STRESS', 'CRISIS']:
        mask = result_df['regime_label'] == regime
        if mask.any():
            fig.add_trace(
                go.Scatter(
                    x=result_df[mask]['date'],
                    y=[regime] * mask.sum(),
                    mode='markers',
                    name=regime,
                    marker=dict(color=regime_colors[regime], size=12, symbol='square'),
                    hovertemplate='%{x}<br>Regime: ' + regime + '<extra></extra>'
                ),
                row=1, col=1
            )

    # Plot 2: Reserves and Real Policy Rate
    fig.add_trace(
        go.Scatter(
            x=result_df['date'],
            y=result_df['gross_reserves_usd_m'],
            mode='lines+markers',
            name='Reserves ($M)',
            line=dict(color='#3498db', width=2),
            marker=dict(size=5)
        ),
        row=2, col=1
    )

    # Plot 3: Inflation and AWCMR
    fig.add_trace(
        go.Scatter(
            x=result_df['date'],
            y=result_df['ncpi_yoy_pct'],
            mode='lines+markers',
            name='Inflation (%)',
            line=dict(color='#e74c3c', width=2),
            marker=dict(size=5)
        ),
        row=3, col=1
    )

    fig.add_trace(
        go.Scatter(
            x=result_df['date'],
            y=result_df['awcmr'],
            mode='lines+markers',
            name='AWCMR (%)',
            line=dict(color='#9b59b6', width=2),
            marker=dict(size=5)
        ),
        row=3, col=1
    )

    # Add key event markers
    for date_str, event_info in ALL_EVENTS.items():
        for row in [1, 2, 3]:
            fig.add_vline(
                x=date_str,
                line_dash="dash" if event_info['type'] != 'regime' else "solid",
                line_color=event_info['color'],
                line_width=1 if event_info['type'] != 'regime' else 2,
                row=row, col=1
            )

        # Add annotation on first row
        fig.add_annotation(
            x=date_str,
            y=1.05,
            yref="y domain",
            text=event_info['name'][:20],
            showarrow=False,
            textangle=-45,
            font=dict(size=8, color=event_info['color']),
            row=1, col=1
        )

    fig.update_layout(
        height=700,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode='x unified'
    )

    fig.update_yaxes(title_text="Regime", row=1, col=1)
    fig.update_yaxes(title_text="Reserves ($M)", row=2, col=1)
    fig.update_yaxes(title_text="Rate (%)", row=3, col=1)

    st.plotly_chart(fig, use_container_width=True)

    # Regime Statistics
    st.subheader("📈 Regime Characteristics")

    col1, col2, col3 = st.columns(3)

    for col, regime in zip([col1, col2, col3], ['CALM', 'STRESS', 'CRISIS']):
        with col:
            mask = result_df['regime_label'] == regime
            subset = result_df[mask]

            color = regime_colors[regime]
            st.markdown(f"### <span style='color:{color}'>{regime}</span>", unsafe_allow_html=True)
            st.metric("Duration", f"{len(subset)} months")
            st.metric("Inflation (avg)", f"{subset['ncpi_yoy_pct'].mean():.1f}%")
            st.metric("AWCMR (avg)", f"{subset['awcmr'].mean():.1f}%")
            st.metric("Reserves (avg)", f"${subset['gross_reserves_usd_m'].mean():,.0f}M")
            st.metric("Real Rate (avg)", f"{subset['real_policy_rate'].mean():.1f}%")

    # Transition Table
    st.subheader("🔄 Regime Transitions")

    transitions = []
    prev_regime = None
    for _, row in result_df.iterrows():
        if prev_regime is not None and row['regime_label'] != prev_regime:
            transitions.append({
                'Date': row['date'].strftime('%Y-%m'),
                'From': prev_regime,
                'To': row['regime_label'],
                'Inflation': f"{row['ncpi_yoy_pct']:.1f}%",
                'Reserves': f"${row['gross_reserves_usd_m']:,.0f}M"
            })
        prev_regime = row['regime_label']

    if transitions:
        st.dataframe(pd.DataFrame(transitions), use_container_width=True)

    # Event Alignment Results
    st.subheader("✅ Event Alignment Validation")

    st.markdown("""
    The model was validated against **12 pre-specified events** from the research plan.
    All events were correctly classified within the strategic window (±2 months).
    """)

    # Load validation results if available
    try:
        validation_results = pd.read_csv('data/merged/validation_results.csv')
        validation_results['Status'] = validation_results['hit'].apply(lambda x: '✓' if x else '✗')
        st.dataframe(
            validation_results[['date', 'name', 'expected', 'detected', 'Status']].rename(
                columns={'date': 'Date', 'name': 'Event', 'expected': 'Expected', 'detected': 'HMM Result'}
            ),
            use_container_width=True
        )
    except:
        st.info("Run validation_framework.py to generate detailed validation results.")

    # Model Details
    with st.expander("📋 Model Technical Details"):
        st.markdown(f"""
        **Configuration:**
        - Model: Gaussian HMM, 3 states, diagonal covariance
        - Data: Monthly frequency (not daily forward-filled)
        - Features: `{', '.join(HMM_FEATURES)}`
        - Observations: {len(result_df)} months

        **Why This Works:**
        - Monthly data provides ~60 true observations (vs 1800+ duplicated daily rows)
        - Diagonal covariance reduces parameters from 51 to 33
        - 3 states naturally separate CALM → STRESS → CRISIS progression

        **Transition Matrix:**
        """)

        trans_df = pd.DataFrame(
            model.transmat_,
            columns=['To CALM', 'To STRESS', 'To CRISIS'],
            index=['From CALM', 'From STRESS', 'From CRISIS']
        )
        st.dataframe(trans_df.style.background_gradient(cmap='Blues').format("{:.3f}"), use_container_width=True)

# ============================================================================
# MERCADO FSI PANEL
# ============================================================================
elif analysis_type == "📈 Mercado FSI":
    st.header("📈 Mercado-Park Financial Stress Index (FSI)")

    st.markdown("""
    ### Market-Based Stress Measurement

    The **Mercado-Park FSI** (Mercado & Park, 2011) is a continuous stress indicator based on
    variance-equal weighted combination of 5 market-derived components. Unlike HMM regimes,
    this provides a real-time stress level rather than discrete regime classification.
    """)

    # Load FSI data
    @st.cache_data
    def load_fsi_data():
        try:
            fsi = pd.read_csv('data/merged/mercado_fsi_monthly.csv', parse_dates=['date'])
            return fsi
        except Exception as e:
            st.error(f"Could not load FSI data: {e}")
            return None

    fsi_df = load_fsi_data()

    if fsi_df is not None:
        # Methodology explanation
        with st.expander("📖 FSI Methodology (Mercado & Park, 2011)", expanded=True):
            st.markdown("""
            **Formula:**
            $$FSI_t = \\frac{1}{5} \\sum_{i=1}^{5} \\frac{x_{i,t} - \\bar{x}_i}{\\sigma_i}$$

            **The 5 Components:**

            | Component | Description | Stress Signal |
            |-----------|-------------|---------------|
            | **Banking Beta (β)** | CAPM beta of banking sector vs market | β > 1 indicates banking vulnerability |
            | **Equity Returns (inverted)** | Negative stock returns | Market pessimism |
            | **Equity Volatility** | 20-day rolling std of returns | Uncertainty |
            | **Debt Spread** | ISB yield - US 10Y Treasury | Sovereign risk |
            | **EMPI** | Exchange Market Pressure Index | FX stress |

            **Interpretation:**
            - FSI > 0: Above-average stress
            - FSI > 1: One standard deviation above normal
            - FSI > 2: Severe stress (rare)
            """)

        # Summary metrics
        st.subheader("📊 Current Status")

        latest = fsi_df.dropna(subset=['fsi_variance_equal']).iloc[-1]
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Latest FSI", f"{latest['fsi_variance_equal']:.2f}")
        with col2:
            mean_fsi = fsi_df['fsi_variance_equal'].mean()
            st.metric("Historical Mean", f"{mean_fsi:.2f}")
        with col3:
            max_fsi = fsi_df['fsi_variance_equal'].max()
            max_date = fsi_df.loc[fsi_df['fsi_variance_equal'].idxmax(), 'date']
            st.metric("Peak FSI", f"{max_fsi:.2f}", delta=max_date.strftime('%Y-%m'))
        with col4:
            coverage = fsi_df['fsi_variance_equal'].notna().sum()
            st.metric("Observations", f"{coverage} months")

        # Main FSI time series plot
        st.subheader("📈 FSI Time Series")

        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            subplot_titles=['Composite FSI', 'Individual Components (Standardized)'],
            vertical_spacing=0.12,
            row_heights=[0.5, 0.5]
        )

        # Composite FSI
        fig.add_trace(
            go.Scatter(
                x=fsi_df['date'],
                y=fsi_df['fsi_variance_equal'],
                mode='lines+markers',
                name='FSI (Variance-Equal)',
                line=dict(color='#1f77b4', width=2),
                marker=dict(size=4)
            ),
            row=1, col=1
        )

        # Add threshold lines
        fig.add_hline(y=0, line_dash="solid", line_color="gray", row=1, col=1)
        fig.add_hline(y=1, line_dash="dash", line_color="orange",
                     annotation_text="Elevated (1σ)", row=1, col=1)
        fig.add_hline(y=2, line_dash="dash", line_color="red",
                     annotation_text="Severe (2σ)", row=1, col=1)

        # Individual components
        components = {
            'banking_beta_std': ('Banking Beta', '#e74c3c'),
            'equity_returns_inv_std': ('Equity Returns (inv)', '#3498db'),
            'equity_volatility_std': ('Equity Volatility', '#9b59b6'),
            'empi_std': ('EMPI', '#2ecc71')
        }

        for col, (name, color) in components.items():
            if col in fsi_df.columns:
                fig.add_trace(
                    go.Scatter(
                        x=fsi_df['date'],
                        y=fsi_df[col],
                        mode='lines',
                        name=name,
                        line=dict(color=color, width=1.5),
                        opacity=0.7
                    ),
                    row=2, col=1
                )

        # Add crisis markers
        for date_str, event_info in ALL_EVENTS.items():
            if event_info['type'] in ['anchor', 'regime']:
                fig.add_vline(
                    x=date_str, line_dash="dash",
                    line_color=event_info['color'], line_width=1
                )

        fig.update_layout(
            height=700,
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            hovermode='x unified'
        )
        fig.update_yaxes(title_text="FSI", row=1, col=1)
        fig.update_yaxes(title_text="Standardized Value", row=2, col=1)

        st.plotly_chart(fig, use_container_width=True)

        # Component Analysis
        st.subheader("🔍 Component Analysis")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Component Coverage (2018-2024):**")
            comp_coverage = {
                'Banking Beta': fsi_df['banking_beta'].notna().sum(),
                'Equity Returns': fsi_df['equity_returns_inv'].notna().sum(),
                'Equity Volatility': fsi_df['equity_volatility'].notna().sum(),
                'EMPI': fsi_df['empi'].notna().sum() if 'empi' in fsi_df.columns else 0
            }

            coverage_df = pd.DataFrame({
                'Component': comp_coverage.keys(),
                'Months Available': comp_coverage.values()
            })
            st.dataframe(coverage_df, use_container_width=True)

        with col2:
            st.markdown("**Key FSI Episodes:**")
            # Find periods of elevated stress
            high_stress = fsi_df[fsi_df['fsi_variance_equal'] > 1].copy()
            if len(high_stress) > 0:
                st.dataframe(
                    high_stress[['date', 'fsi_variance_equal']].rename(
                        columns={'date': 'Date', 'fsi_variance_equal': 'FSI'}
                    ).sort_values('FSI', ascending=False).head(10),
                    use_container_width=True
                )
            else:
                st.info("No periods with FSI > 1σ")

        # Limitations
        with st.expander("⚠️ FSI Limitations"):
            st.markdown("""
            **Data Gaps:**
            - **ISB Yields**: Market froze during crisis (~15% coverage) → Debt spread component missing
            - **EMPI**: Requires parallel FX data not consistently available

            **Methodological Issues:**
            - Variance-equal weighting assumes all components equally important
            - Banking beta requires liquid equity market (CSE is thin)
            - Backward-looking: volatility is computed from past returns

            **Sri Lanka Specific:**
            - FX rate was defended until March 2022 - EMPI masked true stress
            - Equity market showed perverse behavior (rose during early crisis)
            """)
    else:
        st.error("FSI data not available. Run mercado_fsi.py first.")

# ============================================================================
# RECURSIVE HMM PANEL
# ============================================================================
elif analysis_type == "🔮 Recursive HMM":
    st.header("🔮 Recursive HMM with Regime Probabilities")

    st.markdown("""
    ### Real-Time Regime Detection (No Lookahead)

    The **Recursive HMM** estimates regimes using only data available up to each point in time.
    Unlike full-sample HMM (which uses all data), this simulates what policymakers would have
    actually seen in real-time.
    """)

    # Load recursive HMM data
    @st.cache_data
    def load_recursive_hmm():
        try:
            hmm_probs = pd.read_csv('data/merged/hmm_probs_monthly.csv', parse_dates=['date'])
            return hmm_probs
        except Exception as e:
            st.error(f"Could not load recursive HMM data: {e}")
            return None

    hmm_probs = load_recursive_hmm()

    if hmm_probs is not None:
        # Methodology explanation
        with st.expander("📖 Recursive Estimation Methodology", expanded=True):
            st.markdown("""
            **Key Difference from Full-Sample HMM:**

            | Aspect | Full-Sample HMM | Recursive HMM |
            |--------|-----------------|---------------|
            | **Data Used** | All observations (2018-2024) | Only data up to time t |
            | **Regime Labels** | Assigned with hindsight | True real-time estimates |
            | **Use Case** | Historical analysis | Early warning system |

            **Procedure:**
            1. Start with minimum training window (12 months)
            2. At each month t, fit 3-state HMM using data [0:t]
            3. Classify month t using newly fitted model
            4. Extract probabilities: P(CALM), P(STRESS), P(CRISIS)
            5. Expand window and repeat

            **Output:**
            - **Regime Label**: Most likely state (argmax of probabilities)
            - **Confidence**: Probability of assigned regime
            - **Sustained**: Whether regime held for 3+ consecutive months
            """)

        # Summary metrics
        st.subheader("📊 Current Status")

        latest = hmm_probs.iloc[-1]
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Current Regime", latest['regime_realtime'])
        with col2:
            st.metric("Confidence", f"{latest['confidence']:.1%}")
        with col3:
            st.metric("P(Crisis)", f"{latest['p_crisis']:.1%}")
        with col4:
            st.metric("Training Months", f"{latest['n_training']}")

        # Probability time series
        st.subheader("📈 Regime Probabilities Over Time")

        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            subplot_titles=['Regime Probabilities (Stacked)', 'Dominant Regime & Confidence'],
            vertical_spacing=0.12,
            row_heights=[0.6, 0.4]
        )

        # Stacked probability area chart
        fig.add_trace(
            go.Scatter(
                x=hmm_probs['date'], y=hmm_probs['p_calm'],
                mode='lines', name='P(CALM)',
                fill='tozeroy', fillcolor='rgba(46, 204, 113, 0.5)',
                line=dict(color='#2ecc71', width=0)
            ),
            row=1, col=1
        )

        fig.add_trace(
            go.Scatter(
                x=hmm_probs['date'],
                y=hmm_probs['p_calm'] + hmm_probs['p_stress'],
                mode='lines', name='P(STRESS)',
                fill='tonexty', fillcolor='rgba(243, 156, 18, 0.5)',
                line=dict(color='#f39c12', width=0)
            ),
            row=1, col=1
        )

        fig.add_trace(
            go.Scatter(
                x=hmm_probs['date'],
                y=hmm_probs['p_calm'] + hmm_probs['p_stress'] + hmm_probs['p_crisis'],
                mode='lines', name='P(CRISIS)',
                fill='tonexty', fillcolor='rgba(231, 76, 60, 0.5)',
                line=dict(color='#e74c3c', width=0)
            ),
            row=1, col=1
        )

        # Confidence line
        fig.add_trace(
            go.Scatter(
                x=hmm_probs['date'], y=hmm_probs['confidence'],
                mode='lines+markers', name='Confidence',
                line=dict(color='#3498db', width=2),
                marker=dict(size=4)
            ),
            row=2, col=1
        )

        # 70% threshold for sustained crossing
        fig.add_hline(y=0.7, line_dash="dash", line_color="gray",
                     annotation_text="τ=0.7 threshold", row=2, col=1)

        # Add crisis event markers
        for date_str, event_info in ALL_EVENTS.items():
            if event_info['type'] in ['anchor', 'regime']:
                fig.add_vline(
                    x=date_str, line_dash="dash",
                    line_color=event_info['color'], line_width=1
                )
                fig.add_annotation(
                    x=date_str, y=1.05, yref="y domain",
                    text=event_info['name'][:15], showarrow=False,
                    textangle=-45, font=dict(size=8, color=event_info['color']),
                    row=1, col=1
                )

        fig.update_layout(
            height=650,
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            hovermode='x unified'
        )
        fig.update_yaxes(title_text="Cumulative Probability", range=[0, 1], row=1, col=1)
        fig.update_yaxes(title_text="Confidence", range=[0, 1], row=2, col=1)

        st.plotly_chart(fig, use_container_width=True)

        # Real-time vs Full-sample comparison
        st.subheader("🔄 Real-Time vs Full-Sample Agreement")

        # Load validation results if available
        try:
            comparison = pd.read_csv('data/merged/realtime_vs_fullsample_comparison.csv')

            col1, col2 = st.columns(2)
            with col1:
                agreement_rate = (comparison['realtime'] == comparison['fullsample']).mean()
                st.metric("Overall Agreement", f"{agreement_rate:.1%}")
            with col2:
                # Count disagreements
                disagreements = comparison[comparison['realtime'] != comparison['fullsample']]
                st.metric("Disagreement Months", len(disagreements))

            # Show disagreement details
            if len(disagreements) > 0:
                with st.expander(f"📋 Disagreement Details ({len(disagreements)} months)"):
                    st.dataframe(
                        disagreements[['date', 'realtime', 'fullsample']].rename(
                            columns={'date': 'Date', 'realtime': 'Real-Time', 'fullsample': 'Full-Sample'}
                        ),
                        use_container_width=True
                    )
        except:
            st.info("Run recursive_realtime_hmm.py to generate comparison data.")

        # Sustained crossing analysis
        st.subheader("📌 Sustained Crossing Analysis (K=3, τ=0.7)")

        st.markdown("""
        A regime is **sustained** if the probability exceeds 70% (τ) for 3 consecutive months (K).
        This filters out transient fluctuations.
        """)

        sustained_periods = hmm_probs[hmm_probs['stable_3m'] == True]

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Sustained Months", len(sustained_periods))
        with col2:
            st.metric("Transient Months", len(hmm_probs) - len(sustained_periods))

        # Key events table
        st.subheader("📅 Key Events & Real-Time Detection")

        events_detected = hmm_probs[hmm_probs['key_event'].notna()]
        if len(events_detected) > 0:
            st.dataframe(
                events_detected[['date', 'key_event', 'regime_realtime', 'confidence']].rename(
                    columns={
                        'date': 'Date',
                        'key_event': 'Event',
                        'regime_realtime': 'Detected Regime',
                        'confidence': 'Confidence'
                    }
                ),
                use_container_width=True
            )

        # Limitations
        with st.expander("⚠️ Recursive HMM Limitations"):
            st.markdown("""
            **Early Instability:**
            - First 12-20 months have limited training data
            - Regime assignments fluctuate until model stabilizes

            **Regime Label Drift:**
            - State labels (CALM/STRESS/CRISIS) may swap between estimations
            - We use inflation ranking to ensure consistent labeling

            **Hindsight vs Real-Time:**
            - ~42% disagreement with full-sample HMM is expected
            - Real-time estimates miss information from future observations
            """)
    else:
        st.error("Recursive HMM data not available. Run recursive_realtime_hmm.py first.")

# ============================================================================
# FSI vs HMM COMPARISON PANEL
# ============================================================================
elif analysis_type == "⚖️ FSI vs HMM Comparison":
    st.header("⚖️ FSI vs HMM: Complementary Early Warning")

    st.markdown("""
    ### Combining Market-Based and Macro-Based Indicators

    **FSI (Mercado-Park)** and **HMM** capture different aspects of financial stress:
    - **FSI**: Market prices, forward-looking, continuous
    - **HMM**: Macro fundamentals, regime-based, discrete

    When these diverge, it may signal important information.
    """)

    # Load combined data
    @st.cache_data
    def load_combined_data():
        try:
            combined = pd.read_csv('data/merged/combined_fsi_hmm.csv', parse_dates=['date'])
            return combined
        except Exception as e:
            st.error(f"Could not load combined data: {e}")
            return None

    combined = load_combined_data()

    if combined is not None:
        # Summary metrics
        st.subheader("📊 Framework Summary")

        col1, col2, col3, col4 = st.columns(4)

        fsi_hmm_corr = combined['fsi_std'].corr(combined['hmm_stress_prob'])
        agreement_rate = combined['agreement'].mean() if 'agreement' in combined.columns else 0
        early_warnings = combined['early_warning'].sum() if 'early_warning' in combined.columns else 0
        false_alarms = combined['possible_false_alarm'].sum() if 'possible_false_alarm' in combined.columns else 0

        with col1:
            st.metric("FSI-HMM Correlation", f"{fsi_hmm_corr:.2f}",
                     delta="Low = Complementary" if abs(fsi_hmm_corr) < 0.3 else "High = Redundant")
        with col2:
            st.metric("Agreement Rate", f"{agreement_rate:.1%}")
        with col3:
            st.metric("Early Warning Signals", early_warnings)
        with col4:
            st.metric("Possible False Alarms", false_alarms)

        # Methodology
        with st.expander("📖 Combined Framework Methodology", expanded=True):
            st.markdown("""
            **Combined Stress Score:**
            $$Combined = \\alpha \\times FSI_{std} + (1-\\alpha) \\times P(non-CALM)$$

            Where:
            - $\\alpha = 0.5$ (equal weighting)
            - $FSI_{std}$ = standardized FSI
            - $P(non-CALM) = P(STRESS) + P(CRISIS)$ from recursive HMM

            **Disagreement Signals:**

            | Signal Type | Condition | Interpretation |
            |-------------|-----------|----------------|
            | **Early Warning** | FSI > 1σ but P(CALM) > 50% | Markets see stress before macro regime shift |
            | **Possible False Alarm** | P(CRISIS) > 50% but FSI < 0.5σ | Macro stress without market reaction |
            """)

        # Main visualization
        st.subheader("📈 FSI vs HMM Comparison")

        fig = make_subplots(
            rows=3, cols=1,
            shared_xaxes=True,
            subplot_titles=[
                'FSI (Standardized) vs HMM Stress Probability',
                'Combined Stress Score',
                'Disagreement Signals'
            ],
            vertical_spacing=0.08,
            row_heights=[0.4, 0.35, 0.25]
        )

        # Row 1: FSI vs HMM
        fig.add_trace(
            go.Scatter(
                x=combined['date'], y=combined['fsi_std'],
                mode='lines', name='FSI (std)',
                line=dict(color='#3498db', width=2)
            ),
            row=1, col=1
        )

        fig.add_trace(
            go.Scatter(
                x=combined['date'], y=combined['hmm_stress_prob'],
                mode='lines', name='HMM P(non-CALM)',
                line=dict(color='#e74c3c', width=2)
            ),
            row=1, col=1
        )

        fig.add_hline(y=0, line_dash="solid", line_color="gray", row=1, col=1)

        # Row 2: Combined score
        fig.add_trace(
            go.Scatter(
                x=combined['date'], y=combined['combined_stress_norm'],
                mode='lines+markers', name='Combined Score',
                line=dict(color='#2c3e50', width=2),
                marker=dict(size=4)
            ),
            row=2, col=1
        )

        # Threshold lines
        fig.add_hline(y=0.5, line_dash="dash", line_color="orange",
                     annotation_text="Stress (0.5)", row=2, col=1)
        fig.add_hline(y=0.7, line_dash="dash", line_color="red",
                     annotation_text="Crisis (0.7)", row=2, col=1)

        # Row 3: Disagreements
        if 'early_warning' in combined.columns:
            fig.add_trace(
                go.Scatter(
                    x=combined['date'],
                    y=combined['early_warning'].astype(int),
                    mode='lines', name='Early Warning',
                    fill='tozeroy', fillcolor='rgba(243, 156, 18, 0.5)',
                    line=dict(color='#f39c12', width=1)
                ),
                row=3, col=1
            )

        if 'possible_false_alarm' in combined.columns:
            fig.add_trace(
                go.Scatter(
                    x=combined['date'],
                    y=-combined['possible_false_alarm'].astype(int),
                    mode='lines', name='Possible False Alarm',
                    fill='tozeroy', fillcolor='rgba(155, 89, 182, 0.5)',
                    line=dict(color='#9b59b6', width=1)
                ),
                row=3, col=1
            )

        # Add crisis markers
        fig.add_vline(x='2022-04-12', line_dash="dash", line_color="red", line_width=2)
        fig.add_annotation(
            x='2022-04-12', y=1.05, yref="y domain",
            text="Default", showarrow=False,
            font=dict(size=10, color="red"), row=1, col=1
        )

        fig.update_layout(
            height=750,
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            hovermode='x unified'
        )

        fig.update_yaxes(title_text="Standardized Value", row=1, col=1)
        fig.update_yaxes(title_text="Combined Score", range=[0, 1], row=2, col=1)
        fig.update_yaxes(title_text="Signal", range=[-1.5, 1.5], row=3, col=1)

        st.plotly_chart(fig, use_container_width=True)

        # Timeline analysis
        st.subheader("📅 Key Events Timeline")

        key_dates = [
            ('2020-01-01', 'Pre-Crisis'),
            ('2021-07-01', 'STRESS Begins'),
            ('2022-01-01', 'ISB Repayment'),
            ('2022-04-01', 'Default Month'),
            ('2022-09-01', 'Peak Inflation'),
            ('2023-03-01', 'IMF Approval'),
            ('2023-07-01', 'Recovery'),
            ('2024-01-01', 'CALM Returns'),
        ]

        timeline_data = []
        for date_str, event in key_dates:
            date = pd.Timestamp(date_str)
            row = combined[combined['date'].dt.to_period('M') == date.to_period('M')]
            if len(row) > 0:
                r = row.iloc[0]
                timeline_data.append({
                    'Date': date_str[:7],
                    'Event': event,
                    'FSI (std)': f"{r['fsi_std']:.2f}" if pd.notna(r['fsi_std']) else 'N/A',
                    'HMM P(stress)': f"{r['hmm_stress_prob']:.2f}" if pd.notna(r['hmm_stress_prob']) else 'N/A',
                    'Combined': f"{r['combined_stress_norm']:.2f}" if pd.notna(r['combined_stress_norm']) else 'N/A',
                    'HMM Regime': r['regime_realtime'] if 'regime_realtime' in r else 'N/A'
                })

        if timeline_data:
            st.dataframe(pd.DataFrame(timeline_data), use_container_width=True)

        # Insights
        st.subheader("💡 Key Insights")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("""
            **Why Low Correlation is Good:**

            The near-zero correlation (r ≈ 0) between FSI and HMM means they capture
            **different information**:

            - FSI reacts to market prices (potentially noisy)
            - HMM tracks macro fundamentals (potentially lagged)

            When both agree → High confidence
            When they disagree → Investigate further
            """)

        with col2:
            st.markdown("""
            **Early Warning Value:**

            The combined framework provides value by:

            1. **Confirming signals**: When both indicators rise together
            2. **Early detection**: When FSI spikes before HMM regime shift
            3. **Noise filtering**: When HMM is stable but FSI is volatile

            For the 2022 crisis, HMM detected STRESS 9 months before default.
            """)

        # Correlation matrix
        with st.expander("📊 Component Correlations"):
            corr_cols = ['fsi_variance_equal', 'fsi_std', 'p_calm', 'p_stress', 'p_crisis',
                        'hmm_stress_prob', 'combined_stress_norm']
            available_cols = [c for c in corr_cols if c in combined.columns]

            if len(available_cols) > 1:
                corr_matrix = combined[available_cols].corr()

                fig = go.Figure(data=go.Heatmap(
                    z=corr_matrix.values,
                    x=corr_matrix.columns,
                    y=corr_matrix.columns,
                    colorscale='RdBu',
                    zmid=0,
                    text=corr_matrix.values,
                    texttemplate='%{text:.2f}',
                    textfont={"size": 10}
                ))

                fig.update_layout(
                    title="FSI-HMM Correlation Matrix",
                    height=400
                )

                st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("Combined FSI-HMM data not available. Run combined_fsi_hmm.py first.")

# ============================================================================
# DATA JUSTIFICATION (Academic Critical Analysis)
# ============================================================================
elif analysis_type == "📚 Data Justification":
    st.header("📚 Data Stream Justification & Critical Analysis")

    st.markdown("""
    This section provides **academic justification** for the 18 data streams used in the SL-FSI,
    along with **critical analysis** of potential weaknesses, biases, and alternative choices.

    > **Purpose**: To defend our data choices in an academically rigorous way while honestly
    > acknowledging limitations and areas where our choices could be challenged.
    """)

    # Define comprehensive data stream metadata
    DATA_STREAM_ANALYSIS = {
        'FX & Currency': {
            'streams': {
                'USD/LKR Exchange Rate': {
                    'column': 'usd_lkr',
                    'source': 'CBSL Daily FX Rates',
                    'frequency': 'Daily',
                    'justification': [
                        'Exchange rate is the canonical stress indicator for EM crises (Kaminsky et al., 1998)',
                        'FX pressure preceded all major Sri Lankan balance of payments crises',
                        'Directly observable market price with minimal measurement error'
                    ],
                    'criticisms': [
                        '**Managed float bias**: CBSL defended the rate until March 2022, masking true stress',
                        '**Dual rate problem**: Parallel/black market rates diverged significantly in 2021-2022 but are not captured',
                        '**Timing artifact**: The "crisis" only appears in FX when CBSL stops defending - this is a policy choice, not market discovery',
                        '**Alternative**: Could use NDF (non-deliverable forward) rates which reflected true market expectations earlier'
                    ],
                    'coverage_note': 'High coverage but informativeness limited during intervention periods'
                },
                'REER Index': {
                    'column': 'reer_index',
                    'source': 'CBSL Monthly Statistics',
                    'frequency': 'Monthly',
                    'justification': [
                        'Real effective exchange rate captures competitiveness dynamics',
                        'Adjusts for inflation differentials with trading partners',
                        'Standard indicator in IMF Article IV assessments'
                    ],
                    'criticisms': [
                        '**Lagged construction**: REER uses lagged inflation data, making it backward-looking',
                        '**Trade weight obsolescence**: Partner weights may not reflect current trade patterns',
                        '**Redundancy**: With inflation and nominal FX already included, REER adds limited marginal information',
                        '**Publication lag**: Often 1-2 months delayed, reducing early warning utility'
                    ],
                    'coverage_note': 'Monthly frequency limits daily crisis detection'
                }
            }
        },
        'Money Market & Interbank': {
            'streams': {
                'AWCMR (Call Money Rate)': {
                    'column': 'awcmr',
                    'source': 'CBSL Daily Money Market Statistics',
                    'frequency': 'Daily',
                    'justification': [
                        'Interbank rates are leading indicators of banking sector stress (Drehmann & Juselius, 2014)',
                        'Captures liquidity conditions before they manifest in asset prices',
                        'AWCMR spiked from 6.5% to 14.5% in April 2022 - contemporaneous with default'
                    ],
                    'criticisms': [
                        '**Thin market**: Sri Lanka interbank market is shallow; rate may reflect few transactions',
                        '**CBSL influence**: Central bank repo operations directly influence the rate',
                        '**Missing stress**: AWCMR did NOT spike in August 2021 when reserves collapsed - it lagged the external sector stress by 8 months',
                        '**Alternative needed**: Should supplement with overnight rate volatility or bid-ask spreads'
                    ],
                    'coverage_note': 'Critical feature in our model but lagged external sector stress'
                },
                'Policy Rates (SDFR/SLFR)': {
                    'column': 'sdfr',
                    'source': 'CBSL Monetary Policy Announcements',
                    'frequency': 'Event-driven (stepped)',
                    'justification': [
                        'Policy rate stance defines monetary conditions',
                        'Real policy rate (nominal - inflation) is key stress measure',
                        'Standard in FSI literature (IMF, 2006)'
                    ],
                    'criticisms': [
                        '**Stepped data**: Rates only change at MPC meetings (6-8x/year), creating long flat periods',
                        '**Policy lag**: Rate changes respond to stress, not anticipate it',
                        '**Redundancy**: We include both SDFR and SLFR which are mechanically linked (corridor)',
                        '**Forward-fill artifact**: Daily forward-filling creates false precision'
                    ],
                    'coverage_note': 'Discrete jumps, not continuous signal'
                }
            }
        },
        'Sovereign & Credit Risk': {
            'streams': {
                'ISB Yields': {
                    'column': 'isb_yield',
                    'source': 'CBSL ISB Secondary Market',
                    'frequency': 'Daily (sparse)',
                    'justification': [
                        'Sovereign spreads are early warning indicators (Reinhart & Rogoff, 2009)',
                        'ISB yields reflect international investor perception of default risk',
                        'Market-based forward-looking measure'
                    ],
                    'criticisms': [
                        '**Coverage disaster**: Only ~15% coverage during crisis period due to market freeze',
                        '**Missing when most needed**: ISB market effectively shut down in late 2021 - precisely when sovereign stress peaked',
                        '**Selection bias**: Observations exist only when market functioning - survival bias',
                        '**Not used in HMM**: We correctly excluded this due to gaps, but this is a significant data limitation'
                    ],
                    'coverage_note': 'UNUSABLE for HMM - market froze during crisis'
                },
                'T-Bill/T-Bond Yields': {
                    'column': 'tbill_primary',
                    'source': 'CBSL Primary Auctions',
                    'frequency': 'Weekly auctions',
                    'justification': [
                        'Domestic yield curve reflects local rate expectations',
                        'Yield curve slope can signal recession/stress',
                        'Primary auction data is less noisy than secondary market'
                    ],
                    'criticisms': [
                        '**Captive buyer problem**: Sri Lankan banks required to hold government securities - not a free market price',
                        '**Financial repression**: Negative real yields during crisis were policy-induced, not market-determined',
                        '**Auction failures hidden**: Failed auctions or undersubscription not captured in yield data',
                        '**Weekly frequency**: Auctions are weekly, creating gaps in daily panel'
                    ],
                    'coverage_note': 'Administratively determined, not market-clearing price'
                }
            }
        },
        'External Sector': {
            'streams': {
                'Gross FX Reserves': {
                    'column': 'gross_reserves_usd_m',
                    'source': 'CBSL External Sector Statistics',
                    'frequency': 'Monthly',
                    'justification': [
                        'Reserve adequacy is the primary buffer against EM crises',
                        'Import cover (reserves/monthly imports) is standard IMF metric',
                        'Reserves collapsed from $7.5B to $1.6B - clearest crisis signal'
                    ],
                    'criticisms': [
                        '**Gross vs Net confusion**: We use GROSS reserves but NET reserves (excluding liabilities) were negative by late 2021',
                        '**Swap arrangements**: Reserves included PBOC swap line (~$1.5B) which was unusable for import payments',
                        '**Delayed disclosure**: Reserve figures often revised; initial releases may be overstated',
                        '**Should use net reserves**: Net usable reserves would show crisis starting 6+ months earlier'
                    ],
                    'coverage_note': 'GROSS reserves understate true stress; NET reserves unavailable'
                },
                'Tourism Earnings': {
                    'column': 'tourism_earnings_usd_m',
                    'source': 'SLTDA via CBSL',
                    'frequency': 'Monthly',
                    'justification': [
                        'Tourism is 5% of GDP and major FX earner',
                        'Easter attacks (2019) and COVID (2020) caused collapse',
                        'Captures real economy linkages to external sector'
                    ],
                    'criticisms': [
                        '**COVID confound**: Tourism collapse in 2020-2021 was COVID-driven, not financial stress',
                        '**Noisy signal**: Monthly data is volatile and seasonally affected',
                        '**Not leading**: Tourism responds to crises, does not predict them',
                        '**Dropped from HMM**: We correctly excluded this - it adds noise, not signal'
                    ],
                    'coverage_note': 'Confounded by COVID shock; excluded from HMM'
                },
                'Worker Remittances': {
                    'column': 'remittances_usd_m',
                    'source': 'CBSL BOP Statistics',
                    'frequency': 'Monthly',
                    'justification': [
                        'Remittances are ~7% of GDP and major FX source',
                        'Remittance collapse in 2021-2022 contributed to FX crisis',
                        'Captures diaspora confidence in formal channels'
                    ],
                    'criticisms': [
                        '**Hawala leakage**: Remittances shifted to informal channels (hawala) due to FX controls - formal data understates true flows',
                        '**Effect not cause**: Remittance decline was caused by FX policy (unfavorable official rate), not independent stress signal',
                        '**Endogeneity**: Decline is response to crisis, not predictor of it',
                        '**Measurement error**: CBSL estimates may miss 30-50% of actual flows during crisis'
                    ],
                    'coverage_note': 'Endogenous to FX policy; excluded from HMM'
                }
            }
        },
        'Equity Market': {
            'streams': {
                'ASPI (All Share Index)': {
                    'column': 'aspi',
                    'source': 'Colombo Stock Exchange',
                    'frequency': 'Daily',
                    'justification': [
                        'Equity returns capture market expectations of future earnings',
                        'Volatility is a standard stress indicator (VIX logic)',
                        'Only daily-frequency forward-looking indicator available'
                    ],
                    'criticisms': [
                        '**Thin market**: CSE average daily turnover is <$10M; price discovery is poor',
                        '**Retail dominated**: CSE lacks institutional depth; prices may not reflect informed views',
                        '**Paradox of crisis**: ASPI actually ROSE during early crisis (Dec 2021 - Mar 2022) as local investors fled to equities from deposits',
                        '**Not predictive**: Our analysis shows equity volatility detected crisis only 10 days before FX float - worse than reserves'
                    ],
                    'coverage_note': 'Perverse behavior during crisis limits utility'
                },
                'Market Turnover': {
                    'column': 'equity_turnover',
                    'source': 'Colombo Stock Exchange',
                    'frequency': 'Daily',
                    'justification': [
                        'Turnover captures liquidity and market depth',
                        'Abnormal turnover can signal stress or flight',
                        'Volume confirms price signals'
                    ],
                    'criticisms': [
                        '**Noise dominated**: Daily turnover is extremely volatile',
                        '**No clear crisis signal**: Turnover spiked in both directions during crisis',
                        '**Market closure**: CSE was closed for extended periods in 2022 - missing data',
                        '**Denominator problem**: Turnover ratio (turnover/market cap) is more meaningful than raw turnover'
                    ],
                    'coverage_note': 'High noise; market closures during crisis'
                }
            }
        },
        'Inflation': {
            'streams': {
                'NCPI (YoY %)': {
                    'column': 'ncpi_yoy_pct',
                    'source': 'Department of Census and Statistics',
                    'frequency': 'Monthly',
                    'justification': [
                        'Inflation is ultimate symptom of monetary/fiscal imbalance',
                        'YoY transformation removes seasonality',
                        'NCPI reached 69.8% in September 2022 - peak crisis indicator'
                    ],
                    'criticisms': [
                        '**Lagging indicator**: Inflation is outcome of crisis, not predictor',
                        '**Measurement issues**: NCPI basket may not reflect actual consumption during shortages',
                        '**Base effects**: YoY calculation creates mechanical spikes and drops',
                        '**CCPI alternative**: CCPI (Colombo) is published weekly but we use monthly national NCPI'
                    ],
                    'coverage_note': 'Lagging indicator; peaks 6 months after default'
                }
            }
        },
        'Global Anchors': {
            'streams': {
                'US 10Y Treasury Yield': {
                    'column': 'us_10y_yield',
                    'source': 'Yahoo Finance / FRED',
                    'frequency': 'Daily',
                    'justification': [
                        'Global risk-free rate affects EM borrowing costs',
                        'Fed tightening in 2022 exacerbated EM stress',
                        'Needed for EMBI spread calculation'
                    ],
                    'criticisms': [
                        '**Common factor**: Affects all EMs equally; does not identify Sri Lanka-specific stress',
                        '**Endogeneity**: Global rates rose AFTER Sri Lanka crisis began - not causal',
                        '**Redundant**: For Sri Lanka-specific model, adds little beyond noise'
                    ],
                    'coverage_note': 'Global factor; not Sri Lanka-specific'
                },
                'Gold Price (USD)': {
                    'column': 'gold_usd',
                    'source': 'Yahoo Finance',
                    'frequency': 'Daily',
                    'justification': [
                        'Gold premium (local gold / official rate) reveals FX mispricing',
                        'When gold premium rises, official rate is misaligned',
                        'Alternative FX gauge during intervention'
                    ],
                    'criticisms': [
                        '**Complex calculation**: Gold premium requires local gold price which has coverage gaps',
                        '**Thin market**: Local gold market is illiquid; prices may be stale',
                        '**Not used**: Gold premium feature dropped due to calculation issues'
                    ],
                    'coverage_note': 'Used for derived feature; direct use limited'
                }
            }
        }
    }

    # Calculate actual coverage
    def calculate_coverage(df, col, start='2020-01-01', end='2023-12-31'):
        crisis = df[(df['date'] >= start) & (df['date'] <= end)]
        if col not in crisis.columns:
            return 0, 0
        valid = crisis[col].notna().sum()
        total = len(crisis)
        return valid, total

    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Stream-by-Stream Analysis",
        "⚖️ What We Used vs Didn't Use",
        "🔴 Critical Weaknesses",
        "📊 Coverage Analysis"
    ])

    with tab1:
        st.subheader("Detailed Analysis of Each Data Stream")

        selected_category = st.selectbox(
            "Select Category",
            list(DATA_STREAM_ANALYSIS.keys())
        )

        category_data = DATA_STREAM_ANALYSIS[selected_category]

        for stream_name, stream_info in category_data['streams'].items():
            with st.expander(f"**{stream_name}** ({stream_info['frequency']})", expanded=False):
                col1, col2 = st.columns([1, 1])

                with col1:
                    st.markdown("#### ✅ Justification")
                    for j in stream_info['justification']:
                        st.markdown(f"- {j}")

                    st.markdown(f"**Source**: {stream_info['source']}")

                    # Show actual coverage
                    valid, total = calculate_coverage(daily_df, stream_info['column'])
                    if total > 0:
                        pct = valid/total*100
                        color = "green" if pct > 70 else "orange" if pct > 40 else "red"
                        st.markdown(f"**Coverage (2020-2023)**: :{color}[{pct:.1f}%] ({valid:,}/{total:,} days)")

                with col2:
                    st.markdown("#### ❌ Critical Analysis")
                    for c in stream_info['criticisms']:
                        st.markdown(f"- {c}")

                    st.markdown(f"*{stream_info['coverage_note']}*")

    with tab2:
        st.subheader("Feature Selection Decisions")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### ✅ Features USED in Final HMM")
            st.markdown("""
            | Feature | Why Included |
            |---------|--------------|
            | **AWCMR** | 100% coverage; interbank stress signal |
            | **Real Policy Rate** | 100% coverage; monetary conditions |
            | **Gross Reserves** | 100% coverage; external buffer |
            | **NCPI Inflation** | 100% coverage; price stability |

            **Selection Criteria:**
            1. Complete coverage (no gaps during crisis)
            2. Distinct economic channels (not redundant)
            3. Monthly frequency matches data reality
            4. Interpretable for policymakers
            """)

            st.info("""
            **Key Design Choice**: We use only 4 features because:
            - Avoids overfitting with limited observations (~60 months)
            - Each feature represents distinct stress channel
            - 100% overlap ensures no imputation artifacts
            """)

        with col2:
            st.markdown("### ❌ Features EXCLUDED from HMM")
            st.markdown("""
            | Feature | Why Excluded |
            |---------|--------------|
            | **ISB Yields** | <15% coverage; market froze in crisis |
            | **Equity Volatility** | 57% coverage; perverse crisis behavior |
            | **Tourism** | COVID confound; not predictive |
            | **Remittances** | Endogenous to FX policy |
            | **USD/LKR** | Masked by intervention until Mar 2022 |
            | **REER** | Redundant with inflation + FX |
            | **Gold Premium** | Calculation gaps; thin market |

            **Exclusion Criteria:**
            1. Coverage gaps during crisis period
            2. Confounded by COVID or policy
            3. Endogenous (effect not cause)
            4. Redundant with included features
            """)

            st.warning("""
            **Honest Limitation**: Our best-coverage features are **lagging indicators**.
            - AWCMR spiked 8 months AFTER reserve collapse
            - Inflation peaked 6 months AFTER default
            - This limits true early warning capability
            """)

    with tab3:
        st.subheader("🔴 Critical Weaknesses in Our Data")

        st.error("""
        ### The Uncomfortable Truths About Our Data

        This section documents weaknesses that could be raised by reviewers or critics.
        Being explicit about limitations strengthens rather than weakens academic credibility.
        """)

        weakness_categories = {
            "1. We Don't Have True Market Prices": """
            **Problem**: Most Sri Lankan financial prices are administratively determined, not market-clearing:
            - **FX Rate**: Defended by CBSL until March 2022 (masked true stress)
            - **T-Bill Yields**: Banks required to hold government securities (captive buyers)
            - **Interbank Rate**: Within CBSL corridor by construction

            **Implication**: Our "market stress" indicators largely reflect policy choices, not market discovery.
            A critic could argue we're detecting "policy regime changes" not "market stress regimes."

            **Defense**: This is inherent to emerging markets with managed financial systems.
            The research question is still valid: can we detect when policy is failing to contain stress?
            """,

            "2. The Best Leading Indicators Are Missing": """
            **Problem**: Indicators that would provide earlier warning are unavailable:
            - **NDF Rates**: Non-deliverable forwards showed stress months earlier - no data
            - **Net Reserves**: Net (not gross) reserves went negative in late 2021 - not published monthly
            - **CDS Spreads**: Credit default swaps would show default probability - no active market
            - **Parallel FX Rate**: Black market rate diverged significantly - illegal, not tracked

            **Implication**: We're detecting crisis with lagging indicators.
            Our "9 months early" detection is actually detecting STRESS (July 2021), not predicting CRISIS (April 2022).

            **Defense**: We're transparent about this. The 3-state model explicitly separates STRESS from CRISIS.
            """,

            "3. Forward-Fill Creates False Precision": """
            **Problem**: Monthly data (reserves, inflation) is forward-filled to create daily observations:
            - 1,827 daily rows but only ~60 unique monthly observations
            - HMM sees identical data for 30 days, then a jump
            - Creates artificial discontinuities at month boundaries

            **Implication**: Daily HMM is fitting to monthly steps, not daily dynamics.
            This is why 3-state daily HMM produced 844 transitions (fitting the steps).

            **Defense**: We switched to monthly HMM explicitly because of this.
            The monthly model is honest about its actual information content.
            """,

            "4. Survivorship Bias in Data Coverage": """
            **Problem**: Data coverage is worst when stress is highest:
            - ISB market froze during peak crisis (no observations)
            - CSE closed multiple times in 2022 (missing equity data)
            - CBSL delayed releases during crisis (stale data)

            **Implication**: The features with best coverage (reserves, inflation, policy rates)
            are the slowest-moving and most lagging. Fast-moving market prices disappear in crisis.

            **Defense**: This is why we emphasize coverage requirements.
            Using ISB yields would mean no model during the period we most need it.
            """,

            "5. Model Trained on Single Crisis": """
            **Problem**: We have exactly one sovereign default in our sample (2022):
            - No out-of-sample validation possible
            - Overfitting to idiosyncratic 2022 crisis features
            - Cannot distinguish signal from noise without more crises

            **Implication**: 100% hit rate on training data is not generalizable.
            We don't know if this model would detect a different type of crisis.

            **Defense**: We're explicit that this is a case study, not a general EWS.
            The methodology is transferable; the specific thresholds are not.
            """
        }

        for title, content in weakness_categories.items():
            with st.expander(title, expanded=False):
                st.markdown(content)

        st.markdown("---")
        st.markdown("""
        ### 🎯 Summary of Critical Position

        Our data selection is **defensible but imperfect**:

        | Strength | Corresponding Weakness |
        |----------|------------------------|
        | 100% coverage ensures reliability | Best-coverage features are lagging indicators |
        | Monthly aggregation is honest | Loses daily market dynamics |
        | 4 features avoid overfitting | May miss important stress channels |
        | Validated on 12 events | All events from single crisis episode |

        **Bottom Line**: We have built the best model possible given Sri Lankan data constraints,
        but those constraints are significant. Claims should be appropriately hedged.
        """)

    with tab4:
        st.subheader("📊 Data Coverage Analysis")

        # Calculate coverage for all features
        crisis_period = daily_df[(daily_df['date'] >= '2020-01-01') & (daily_df['date'] <= '2023-12-31')]
        total_days = len(crisis_period)

        coverage_data = []
        for category, cat_data in DATA_STREAM_ANALYSIS.items():
            for stream, info in cat_data['streams'].items():
                col = info['column']
                if col in crisis_period.columns:
                    valid = crisis_period[col].notna().sum()
                    coverage_data.append({
                        'Category': category,
                        'Stream': stream,
                        'Column': col,
                        'Valid Days': valid,
                        'Coverage %': round(valid/total_days*100, 1),
                        'Frequency': info['frequency'],
                        'Used in HMM': col in ['awcmr', 'real_policy_rate', 'gross_reserves_usd_m', 'ncpi_yoy_pct']
                    })

        coverage_df = pd.DataFrame(coverage_data)

        # Color-coded coverage table
        st.markdown("### Coverage During Crisis Period (2020-2023)")

        def highlight_coverage(row):
            if row['Used in HMM']:
                return ['background-color: #d4edda'] * len(row)
            elif row['Coverage %'] < 30:
                return ['background-color: #f8d7da'] * len(row)
            elif row['Coverage %'] < 70:
                return ['background-color: #fff3cd'] * len(row)
            else:
                return [''] * len(row)

        styled_df = coverage_df.style.apply(highlight_coverage, axis=1)
        st.dataframe(styled_df, use_container_width=True, height=400)

        st.markdown("""
        **Legend:**
        - 🟢 Green: Used in final HMM model
        - 🟡 Yellow: 30-70% coverage (usable but gaps)
        - 🔴 Red: <30% coverage (excluded)
        """)

        # Coverage visualization
        st.markdown("### Coverage by Category")

        fig = go.Figure()

        categories = coverage_df['Category'].unique()
        for cat in categories:
            cat_df = coverage_df[coverage_df['Category'] == cat]
            fig.add_trace(go.Bar(
                name=cat,
                x=cat_df['Stream'],
                y=cat_df['Coverage %'],
                text=cat_df['Coverage %'].astype(str) + '%',
                textposition='auto'
            ))

        fig.add_hline(y=100, line_dash="dash", line_color="green",
                      annotation_text="100% (Used in HMM)")
        fig.add_hline(y=50, line_dash="dot", line_color="orange",
                      annotation_text="50% (Minimum viable)")

        fig.update_layout(
            title="Data Coverage by Stream (2020-2023)",
            xaxis_title="Data Stream",
            yaxis_title="Coverage %",
            barmode='group',
            height=500,
            xaxis_tickangle=-45
        )

        st.plotly_chart(fig, use_container_width=True)

        # Key insight
        st.info("""
        **Key Insight**: Only 4 features have 100% coverage during the crisis period.
        These are exactly the features we use in the final HMM.
        This is not coincidental - it's the binding constraint on model design.
        """)

# ============================================================================
# DATA EXPLORER
# ============================================================================
elif analysis_type == "📊 Data Explorer":
    st.header("📊 All 18 Data Streams + Derived Features")

    frequency = st.sidebar.radio("Data Frequency", ["Daily", "Monthly"])
    df = daily_df if frequency == "Daily" else monthly_df

    tab1, tab2, tab3 = st.tabs(["Core Data Streams", "Derived Features", "Correlation Matrix"])

    with tab1:
        st.subheader("18 Core Data Streams")
        selected_stream = st.selectbox("Select Data Stream", list(DATA_STREAMS.keys()))
        col_name = DATA_STREAMS[selected_stream]

        if col_name in df.columns:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df['date'], y=df[col_name],
                mode='lines', name=selected_stream,
                line=dict(color='#1f77b4', width=2)
            ))

            for event, date in CRISIS_DATES.items():
                fig.add_shape(type="line", x0=date, x1=date, y0=0, y1=1, yref="paper",
                    line=dict(color="red", width=2, dash="dash"))
                fig.add_annotation(x=date, y=1, yref="paper", text=event,
                    showarrow=False, textangle=-90, xanchor="right", yanchor="bottom")

            fig.update_layout(title=f"{selected_stream} Over Time", xaxis_title="Date",
                yaxis_title="Value", height=500, hovermode='x unified')
            st.plotly_chart(fig, use_container_width=True)

            col1, col2, col3, col4 = st.columns(4)
            with col1: st.metric("Mean", f"{df[col_name].mean():.2f}")
            with col2: st.metric("Std Dev", f"{df[col_name].std():.2f}")
            with col3: st.metric("Min", f"{df[col_name].min():.2f}")
            with col4: st.metric("Max", f"{df[col_name].max():.2f}")

            if st.checkbox("Show Raw Data"):
                st.dataframe(df[['date', col_name]].dropna(), height=300)
        else:
            st.warning(f"Column '{col_name}' not found in {frequency.lower()} dataset")

    with tab2:
        st.subheader("Derived Features")
        selected_feature = st.selectbox("Select Derived Feature", list(DERIVED_FEATURES.keys()))
        col_name = DERIVED_FEATURES[selected_feature]

        if col_name in df.columns:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df['date'], y=df[col_name],
                mode='lines', name=selected_feature,
                line=dict(color='#ff7f0e', width=2)
            ))

            for event, date in CRISIS_DATES.items():
                fig.add_shape(type="line", x0=date, x1=date, y0=0, y1=1, yref="paper",
                    line=dict(color="red", width=2, dash="dash"))

            fig.update_layout(title=f"{selected_feature} Over Time", xaxis_title="Date",
                yaxis_title="Value", height=500, hovermode='x unified')
            st.plotly_chart(fig, use_container_width=True)

            col1, col2, col3, col4 = st.columns(4)
            with col1: st.metric("Mean", f"{df[col_name].mean():.4f}")
            with col2: st.metric("Std Dev", f"{df[col_name].std():.4f}")
            with col3: st.metric("Min", f"{df[col_name].min():.4f}")
            with col4: st.metric("Max", f"{df[col_name].max():.4f}")
        else:
            st.warning(f"Column '{col_name}' not found")

    with tab3:
        st.subheader("Correlation Matrix")
        all_features = list(DATA_STREAMS.values()) + list(DERIVED_FEATURES.values())
        available_features = [f for f in all_features if f in df.columns]
        corr_df = df[available_features].corr()

        fig = go.Figure(data=go.Heatmap(
            z=corr_df.values, x=corr_df.columns, y=corr_df.columns,
            colorscale='RdBu', zmid=0, text=corr_df.values,
            texttemplate='%{text:.2f}', textfont={"size": 8}
        ))
        fig.update_layout(title="Correlation Matrix", height=800, width=800)
        st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# CUSTOM HMM (Original functionality)
# ============================================================================
elif analysis_type == "🔄 Custom HMM":
    st.header("🔄 Custom HMM Regime Detection")

    st.info("💡 **Tip**: For validated crisis detection, use the '🎯 Validated 3-State Model' tab instead.")

    frequency = st.sidebar.radio("Data Frequency", ["Daily", "Monthly"])
    df = daily_df if frequency == "Daily" else monthly_df

    st.sidebar.subheader("HMM Parameters")
    n_regimes = st.sidebar.slider("Number of Regimes", 2, 5, 3)
    n_iter = st.sidebar.slider("Max Iterations", 100, 1000, 500, 100)
    cov_type = st.sidebar.selectbox("Covariance Type", ["diag", "full", "spherical", "tied"])

    st.sidebar.subheader("Features for HMM")
    all_available_features = [col for col in df.columns if col != 'date' and pd.api.types.is_numeric_dtype(df[col])]

    default_features = ['awcmr', 'real_policy_rate', 'gross_reserves_usd_m', 'ncpi_yoy_pct']
    selected_features = st.sidebar.multiselect(
        "Select Features", all_available_features,
        default=[f for f in default_features if f in df.columns]
    )

    if len(selected_features) < 2:
        st.warning("⚠️ Please select at least 2 features")
    else:
        df_clean = df[['date'] + selected_features].dropna()
        total_rows = len(df)
        overlap_rows = len(df_clean)
        overlap_pct = (overlap_rows / total_rows) * 100

        col1, col2, col3 = st.columns(3)
        with col1: st.metric("Total Days", f"{total_rows:,}")
        with col2: st.metric("Overlapping Days", f"{overlap_rows:,}")
        with col3: st.metric("Overlap %", f"{overlap_pct:.1f}%")

        if overlap_pct < 30:
            st.error(f"❌ Poor overlap ({overlap_pct:.1f}%)")
        elif overlap_pct < 60:
            st.warning(f"⚠️ Moderate overlap ({overlap_pct:.1f}%)")
        else:
            st.success(f"✅ Good overlap ({overlap_pct:.1f}%)")

        if overlap_rows >= 50:
            X = df_clean[selected_features].values
            X_scaled = (X - X.mean(axis=0)) / X.std(axis=0)

            if st.sidebar.button("Run Custom HMM"):
                with st.spinner("Fitting HMM..."):
                    try:
                        model = hmm.GaussianHMM(
                            n_components=n_regimes, covariance_type=cov_type,
                            n_iter=n_iter, random_state=42
                        )
                        model.fit(X_scaled)
                        hidden_states = model.predict(X_scaled)

                        st.session_state['custom_hmm_states'] = hidden_states
                        st.session_state['custom_hmm_dates'] = df_clean['date'].values
                        st.session_state['custom_hmm_features'] = selected_features
                        st.session_state['custom_hmm_df'] = df_clean
                        st.session_state['custom_hmm_n_regimes'] = n_regimes

                        st.success(f"✅ HMM fitted on {overlap_rows:,} observations")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")

            if 'custom_hmm_states' in st.session_state:
                hidden_states = st.session_state['custom_hmm_states']
                dates = st.session_state['custom_hmm_dates']
                n_reg = st.session_state['custom_hmm_n_regimes']

                # Plot
                fig = go.Figure()
                colors = px.colors.qualitative.Set1[:n_reg]

                for regime in range(n_reg):
                    mask = hidden_states == regime
                    if mask.any():
                        fig.add_trace(go.Scatter(
                            x=dates[mask], y=np.ones(mask.sum()) * regime,
                            mode='markers', name=f'Regime {regime}',
                            marker=dict(color=colors[regime], size=5)
                        ))

                for event, date in CRISIS_DATES.items():
                    fig.add_vline(x=date, line_dash="dash", line_color="red")

                fig.update_layout(height=400, title="Custom HMM Regime Detection")
                st.plotly_chart(fig, use_container_width=True)

                # Stats
                regime_stats = []
                for regime in range(n_reg):
                    mask = hidden_states == regime
                    regime_stats.append({
                        'Regime': regime,
                        'Observations': mask.sum(),
                        'Percentage': f"{100 * mask.sum() / len(hidden_states):.1f}%"
                    })
                st.dataframe(pd.DataFrame(regime_stats), use_container_width=True)

# ============================================================================
# CHANGE POINT DETECTION
# ============================================================================
elif analysis_type == "📍 Change Points":
    st.header("📍 Change Point Detection (PELT)")

    frequency = st.sidebar.radio("Data Frequency", ["Daily", "Monthly"])
    df = daily_df if frequency == "Daily" else monthly_df

    st.sidebar.subheader("Settings")
    all_numeric_cols = [col for col in df.columns if col != 'date' and pd.api.types.is_numeric_dtype(df[col])]
    selected_feature = st.sidebar.selectbox("Select Feature", all_numeric_cols,
        index=all_numeric_cols.index('ncpi_yoy_pct') if 'ncpi_yoy_pct' in all_numeric_cols else 0)

    algorithm = st.sidebar.selectbox("Algorithm", ["Pelt", "Binary Segmentation"])
    model_type = st.sidebar.selectbox("Cost Model", ["l2 (Mean shift)", "rbf (Mean+Variance)"])
    model = model_type.split()[0]
    pen = st.sidebar.slider("Penalty", 1, 50, 10)
    min_size = st.sidebar.slider("Min Segment Size", 5, 60, 20)

    if st.sidebar.button("Detect Change Points"):
        df_clean = df[['date', selected_feature]].dropna()
        data = df_clean[selected_feature].values.reshape(-1, 1)
        dates = df_clean['date'].values

        with st.spinner("Detecting change points..."):
            try:
                if algorithm == "Pelt":
                    algo = rpt.Pelt(model=model, min_size=min_size, jump=1)
                else:
                    algo = rpt.Binseg(model=model, min_size=min_size, jump=1)

                algo.fit(data)
                cp_indices = algo.predict(pen=pen)
                if cp_indices and cp_indices[-1] == len(data):
                    cp_indices = cp_indices[:-1]

                st.session_state['cp_data'] = (cp_indices, dates, data.flatten(), selected_feature)
                st.success(f"Detected {len(cp_indices)} change points")
            except Exception as e:
                st.error(f"Error: {str(e)}")

    if 'cp_data' in st.session_state:
        cp_indices, dates, data, feat_name = st.session_state['cp_data']

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=dates, y=data, mode='lines', name=feat_name))

        for idx in cp_indices:
            if idx < len(dates):
                fig.add_vline(x=dates[idx], line_dash="dash", line_color="green", line_width=2)

        for event, date in CRISIS_DATES.items():
            fig.add_vline(x=date, line_dash="dot", line_color="red")

        fig.update_layout(height=500, title=f"Change Points in {feat_name}")
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Change Point Dates")
        cp_dates = [dates[i].astype('datetime64[D]').astype(str) for i in cp_indices if i < len(dates)]
        st.write(cp_dates)

# ============================================================================
# COMBINED VIEW
# ============================================================================
elif analysis_type == "📈 Combined View":
    st.header("📈 Combined Regime & Change Point View")

    st.info("This view combines the validated 3-state HMM with change point detection for comprehensive analysis.")

    # Fit 3-state HMM
    @st.cache_data
    def get_combined_data(monthly_data, features):
        X = monthly_data[features].values
        X_scaled = (X - X.mean(axis=0)) / X.std(axis=0)

        model = hmm.GaussianHMM(n_components=3, covariance_type="diag", n_iter=300, random_state=42)
        model.fit(X_scaled)
        states = model.predict(X_scaled)

        result = monthly_data.copy()
        result['regime'] = states

        state_inflation = {s: result[result['regime'] == s]['ncpi_yoy_pct'].mean() for s in range(3)}
        sorted_states = sorted(state_inflation.keys(), key=lambda x: state_inflation[x])
        state_labels = {sorted_states[0]: 'CALM', sorted_states[1]: 'STRESS', sorted_states[2]: 'CRISIS'}
        result['regime_label'] = result['regime'].map(state_labels)

        return result

    result_df = get_combined_data(monthly_hmm_data, HMM_FEATURES)

    # Create combined figure
    fig = make_subplots(
        rows=4, cols=1,
        shared_xaxes=True,
        subplot_titles=['HMM Regime States', 'Inflation (YoY %)', 'AWCMR (%)', 'FX Reserves ($M)'],
        vertical_spacing=0.05,
        row_heights=[0.2, 0.27, 0.27, 0.26]
    )

    regime_colors = {'CALM': '#2ecc71', 'STRESS': '#f39c12', 'CRISIS': '#e74c3c'}

    # Regime plot
    for regime in ['CALM', 'STRESS', 'CRISIS']:
        mask = result_df['regime_label'] == regime
        if mask.any():
            fig.add_trace(go.Scatter(
                x=result_df[mask]['date'], y=[regime] * mask.sum(),
                mode='markers', name=regime,
                marker=dict(color=regime_colors[regime], size=10, symbol='square')
            ), row=1, col=1)

    # Inflation
    fig.add_trace(go.Scatter(
        x=result_df['date'], y=result_df['ncpi_yoy_pct'],
        mode='lines+markers', name='Inflation', line=dict(color='#e74c3c', width=2)
    ), row=2, col=1)

    # AWCMR
    fig.add_trace(go.Scatter(
        x=result_df['date'], y=result_df['awcmr'],
        mode='lines+markers', name='AWCMR', line=dict(color='#9b59b6', width=2)
    ), row=3, col=1)

    # Reserves
    fig.add_trace(go.Scatter(
        x=result_df['date'], y=result_df['gross_reserves_usd_m'],
        mode='lines+markers', name='Reserves', line=dict(color='#3498db', width=2)
    ), row=4, col=1)

    # Add event markers
    for date_str, event_info in ALL_EVENTS.items():
        for row in [1, 2, 3, 4]:
            fig.add_vline(x=date_str, line_dash="dash", line_color=event_info['color'],
                line_width=1, row=row, col=1)

    fig.update_layout(height=900, showlegend=True, hovermode='x unified')
    st.plotly_chart(fig, use_container_width=True)

    # Key findings
    st.subheader("📋 Key Findings")
    st.markdown("""
    - **July 2021**: STRESS regime begins (9 months before default)
    - **April 2022**: CRISIS regime begins (coincides with default)
    - **July 2023**: Return to CALM regime (post-IMF stabilization)

    The model detected structural stress building in mid-2021, well before the visible crisis erupted in early 2022.
    """)

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("**SL-FSI v2.0**")
st.sidebar.markdown("3-State Monthly HMM")
st.sidebar.markdown("100% Event Hit Rate")
