import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from hmmlearn import hmm
from scipy import stats
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
st.markdown("**HMM & Bayesian Change Point Detection for 18 Data Streams**")

# Load data
@st.cache_data
def load_data():
    daily = pd.read_csv('data/merged/slfsi_daily_panel.csv', parse_dates=['date'])
    monthly = pd.read_csv('data/merged/slfsi_monthly_panel.csv', parse_dates=['date'])
    return daily, monthly

daily_df, monthly_df = load_data()

# Define the 18 core data streams
DATA_STREAMS = {
    'D1 - USD/LKR Exchange Rate': 'usd_lkr',
    'D2 - AWCMR (Interbank Rate)': 'awcmr',
    'D3 - ASPI (Equity Index)': 'aspi',
    'D4 - Equity Daily Turnover': 'turnover_lkr_mn',
    'D5 - Market Capitalization': 'market_cap_lkr_bn',
    'D6 - S&P SL20 Index': 'sp_sl20',
    'D7 - Local Gold Price': 'gold_price_lkr',
    'D6 Global - Gold Price USD': 'gold_usd',
    'D8 - T-Bill Yields': 'tbill_91d_primary',
    'D9 - T-Bond Yields': 'tbond_5y',
    'D10 - Policy Rate (SDFR)': 'sdfr',
    'D12 - FX Reserves': 'reserves_usd_mn',
    'D13 - NCPI Inflation': 'inflation_yoy',
    'D14 - REER Index': 'reer',
    'D15 - ISB Yields': 'isb_2025_yield',
    'D17 - Tourism Earnings': 'tourism_usd_mn',
    'D18 - Worker Remittances': 'remittances_usd_mn',
    'Helper - US 10Y Yield': 'us_10y'
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

# Sidebar
st.sidebar.header("Analysis Settings")
analysis_type = st.sidebar.radio(
    "Choose Analysis",
    ["📊 Data Explorer", "🔄 HMM Regime Detection", "📍 Bayesian Change Points", "📈 Combined View"]
)

frequency = st.sidebar.radio("Data Frequency", ["Daily", "Monthly"])
df = daily_df if frequency == "Daily" else monthly_df

# Crisis markers
CRISIS_DATES = {
    'FX Float (2022-03-07)': '2022-03-07',
    'Sovereign Default (2022-04-12)': '2022-04-12',
    'Peak Inflation (2022-09-15)': '2022-09-15',
    'IMF EFF (2023-03-20)': '2023-03-20'
}

# ============================================================================
# DATA EXPLORER
# ============================================================================
if analysis_type == "📊 Data Explorer":
    st.header("📊 All 18 Data Streams + Derived Features")

    tab1, tab2, tab3 = st.tabs(["Core Data Streams", "Derived Features", "Correlation Matrix"])

    with tab1:
        st.subheader("18 Core Data Streams")

        # Select data stream
        selected_stream = st.selectbox("Select Data Stream", list(DATA_STREAMS.keys()))
        col_name = DATA_STREAMS[selected_stream]

        if col_name in df.columns:
            # Create figure
            fig = go.Figure()

            # Add trace
            fig.add_trace(go.Scatter(
                x=df['date'],
                y=df[col_name],
                mode='lines',
                name=selected_stream,
                line=dict(color='#1f77b4', width=2)
            ))

            # Add crisis markers
            for event, date in CRISIS_DATES.items():
                fig.add_shape(
                    type="line",
                    x0=date, x1=date,
                    y0=0, y1=1,
                    yref="paper",
                    line=dict(color="red", width=2, dash="dash")
                )
                # Add annotation separately
                fig.add_annotation(
                    x=date,
                    y=1,
                    yref="paper",
                    text=event,
                    showarrow=False,
                    textangle=-90,
                    xanchor="right",
                    yanchor="bottom"
                )

            fig.update_layout(
                title=f"{selected_stream} Over Time",
                xaxis_title="Date",
                yaxis_title="Value",
                height=500,
                hovermode='x unified'
            )

            st.plotly_chart(fig, use_container_width=True)

            # Statistics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Mean", f"{df[col_name].mean():.2f}")
            with col2:
                st.metric("Std Dev", f"{df[col_name].std():.2f}")
            with col3:
                st.metric("Min", f"{df[col_name].min():.2f}")
            with col4:
                st.metric("Max", f"{df[col_name].max():.2f}")

            # Show raw data
            if st.checkbox("Show Raw Data"):
                st.dataframe(df[['date', col_name]].dropna(), height=300)
        else:
            st.warning(f"Column '{col_name}' not found in {frequency.lower()} dataset")

    with tab2:
        st.subheader("Derived Features")

        # Select derived feature
        selected_feature = st.selectbox("Select Derived Feature", list(DERIVED_FEATURES.keys()))
        col_name = DERIVED_FEATURES[selected_feature]

        if col_name in df.columns:
            # Create figure
            fig = go.Figure()

            fig.add_trace(go.Scatter(
                x=df['date'],
                y=df[col_name],
                mode='lines',
                name=selected_feature,
                line=dict(color='#ff7f0e', width=2)
            ))

            # Add crisis markers
            for event, date in CRISIS_DATES.items():
                fig.add_shape(
                    type="line",
                    x0=date, x1=date,
                    y0=0, y1=1,
                    yref="paper",
                    line=dict(color="red", width=2, dash="dash")
                )
                fig.add_annotation(
                    x=date,
                    y=1,
                    yref="paper",
                    text=event,
                    showarrow=False,
                    textangle=-90,
                    xanchor="right",
                    yanchor="bottom"
                )

            fig.update_layout(
                title=f"{selected_feature} Over Time",
                xaxis_title="Date",
                yaxis_title="Value",
                height=500,
                hovermode='x unified'
            )

            st.plotly_chart(fig, use_container_width=True)

            # Statistics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Mean", f"{df[col_name].mean():.4f}")
            with col2:
                st.metric("Std Dev", f"{df[col_name].std():.4f}")
            with col3:
                st.metric("Min", f"{df[col_name].min():.4f}")
            with col4:
                st.metric("Max", f"{df[col_name].max():.4f}")
        else:
            st.warning(f"Column '{col_name}' not found in {frequency.lower()} dataset")

    with tab3:
        st.subheader("Correlation Matrix")

        # Select features for correlation
        all_features = list(DATA_STREAMS.values()) + list(DERIVED_FEATURES.values())
        available_features = [f for f in all_features if f in df.columns]

        # Compute correlation
        corr_df = df[available_features].corr()

        # Create heatmap
        fig = go.Figure(data=go.Heatmap(
            z=corr_df.values,
            x=corr_df.columns,
            y=corr_df.columns,
            colorscale='RdBu',
            zmid=0,
            text=corr_df.values,
            texttemplate='%{text:.2f}',
            textfont={"size": 8}
        ))

        fig.update_layout(
            title="Correlation Matrix of All Features",
            height=800,
            width=800
        )

        st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# HMM REGIME DETECTION
# ============================================================================
elif analysis_type == "🔄 HMM Regime Detection":
    st.header("🔄 Hidden Markov Model Regime Detection")

    # HMM Settings
    st.sidebar.subheader("HMM Parameters")
    n_regimes = st.sidebar.slider("Number of Regimes", 2, 5, 3)
    n_iter = st.sidebar.slider("Max Iterations", 100, 1000, 500, 100)

    # Feature selection
    st.sidebar.subheader("Features for HMM")
    feature_options = ['r_fx', 'vol_fx_20d', 'r_eq', 'vol_eq_20d', 'awcmr',
                       'gold_premium_pct', 'real_policy_rate', 'inflation_yoy']
    selected_features = st.sidebar.multiselect(
        "Select Features",
        [f for f in feature_options if f in df.columns],
        default=[f for f in ['r_fx', 'vol_fx_20d', 'awcmr'] if f in df.columns]
    )

    if len(selected_features) < 2:
        st.warning("Please select at least 2 features for HMM analysis")
    else:
        # Prepare data
        df_clean = df[['date'] + selected_features].dropna()
        X = df_clean[selected_features].values

        # Standardize
        X_mean = X.mean(axis=0)
        X_std = X.std(axis=0)
        X_scaled = (X - X_mean) / X_std

        # Fit HMM
        if st.sidebar.button("Run HMM"):
            with st.spinner("Fitting Hidden Markov Model..."):
                model = hmm.GaussianHMM(
                    n_components=n_regimes,
                    covariance_type="full",
                    n_iter=n_iter,
                    random_state=42
                )

                model.fit(X_scaled)
                hidden_states = model.predict(X_scaled)

                # Store in session state
                st.session_state['hmm_model'] = model
                st.session_state['hmm_states'] = hidden_states
                st.session_state['hmm_dates'] = df_clean['date'].values
                st.session_state['hmm_features'] = selected_features

        # Display results if available
        if 'hmm_states' in st.session_state:
            hidden_states = st.session_state['hmm_states']
            dates = st.session_state['hmm_dates']

            # Create regime plot
            fig = make_subplots(
                rows=len(selected_features) + 1,
                cols=1,
                shared_xaxes=True,
                subplot_titles=['Detected Regimes'] + selected_features,
                vertical_spacing=0.02
            )

            # Plot regimes
            regime_colors = px.colors.qualitative.Set1[:n_regimes]
            for regime in range(n_regimes):
                mask = hidden_states == regime
                if mask.any():
                    fig.add_trace(
                        go.Scatter(
                            x=dates[mask],
                            y=np.ones(mask.sum()) * regime,
                            mode='markers',
                            name=f'Regime {regime}',
                            marker=dict(color=regime_colors[regime], size=3),
                            showlegend=True
                        ),
                        row=1, col=1
                    )

            # Plot features with regime coloring
            for idx, feature in enumerate(selected_features):
                feature_data = df_clean[feature].values

                for regime in range(n_regimes):
                    mask = hidden_states == regime
                    if mask.any():
                        fig.add_trace(
                            go.Scatter(
                                x=dates[mask],
                                y=feature_data[mask],
                                mode='markers',
                                name=f'Regime {regime}',
                                marker=dict(color=regime_colors[regime], size=3),
                                showlegend=False
                            ),
                            row=idx+2, col=1
                        )

            # Add crisis markers
            for event, date in CRISIS_DATES.items():
                for i in range(len(selected_features) + 1):
                    fig.add_shape(
                        type="line",
                        x0=date, x1=date,
                        y0=0, y1=1,
                        yref="paper",
                        line=dict(color="red", width=1, dash="dash"),
                        row=i+1, col=1
                    )
                    if i == 0:  # Only add annotation to first subplot
                        fig.add_annotation(
                            x=date,
                            y=1,
                            yref="y domain",
                            text=event,
                            showarrow=False,
                            textangle=-90,
                            xanchor="right",
                            yanchor="bottom"
                        )

            fig.update_layout(height=300 * (len(selected_features) + 1), showlegend=True)
            st.plotly_chart(fig, use_container_width=True)

            # Regime statistics
            st.subheader("Regime Statistics")
            regime_stats = []
            for regime in range(n_regimes):
                mask = hidden_states == regime
                stats_dict = {
                    'Regime': regime,
                    'Observations': mask.sum(),
                    'Percentage': f"{100 * mask.sum() / len(hidden_states):.1f}%"
                }
                for feature in selected_features:
                    feature_data = df_clean[feature].values[mask]
                    stats_dict[f'{feature}_mean'] = f"{feature_data.mean():.4f}"
                    stats_dict[f'{feature}_std'] = f"{feature_data.std():.4f}"
                regime_stats.append(stats_dict)

            st.dataframe(pd.DataFrame(regime_stats), use_container_width=True)

            # Transition matrix
            st.subheader("Transition Matrix")
            trans_matrix = st.session_state['hmm_model'].transmat_
            trans_df = pd.DataFrame(
                trans_matrix,
                columns=[f'To Regime {i}' for i in range(n_regimes)],
                index=[f'From Regime {i}' for i in range(n_regimes)]
            )
            st.dataframe(trans_df.style.background_gradient(cmap='Blues'), use_container_width=True)

# ============================================================================
# BAYESIAN CHANGE POINT DETECTION
# ============================================================================
elif analysis_type == "📍 Bayesian Change Points":
    st.header("📍 Bayesian Change Point Detection")

    st.markdown("""
    This analysis uses a Bayesian approach to detect structural breaks in time series.
    The algorithm identifies points where the statistical properties (mean/variance) of the data change significantly.
    """)

    # Feature selection
    st.sidebar.subheader("Change Point Settings")

    # Select single feature
    all_numeric_cols = [col for col in df.columns if col != 'date' and pd.api.types.is_numeric_dtype(df[col])]
    selected_feature = st.sidebar.selectbox("Select Feature", all_numeric_cols)

    # Parameters
    prior_prob = st.sidebar.slider("Prior Probability of Change", 0.01, 0.5, 0.1, 0.01)
    threshold = st.sidebar.slider("Detection Threshold", 0.5, 0.99, 0.8, 0.01)

    if st.sidebar.button("Detect Change Points"):
        df_clean = df[['date', selected_feature]].dropna()
        data = df_clean[selected_feature].values
        dates = df_clean['date'].values

        with st.spinner("Running Bayesian change point detection..."):
            # Bayesian Change Point Detection (Online)
            def bayesian_changepoint_detection(data, hazard_rate=1/100):
                """
                Simple Bayesian online change point detection
                Based on Adams & MacKay 2007
                """
                n = len(data)
                R = np.zeros((n + 1, n + 1))
                R[0, 0] = 1

                change_points = []
                probabilities = []

                # Online algorithm
                mean_vals = np.zeros(n)
                var_vals = np.zeros(n)

                for t in range(1, n + 1):
                    # Prediction
                    predprobs = R[t-1, :t] * hazard_rate

                    # Growth
                    R[t, 1:t+1] = R[t-1, :t] * (1 - hazard_rate)
                    R[t, 0] = np.sum(predprobs)

                    # Calculate statistics for each run length
                    for r in range(t + 1):
                        if r == 0:
                            continue
                        start_idx = max(0, t - r)
                        segment = data[start_idx:t]

                        if len(segment) > 1:
                            mean_vals[t-1] += R[t, r] * np.mean(segment)
                            var_vals[t-1] += R[t, r] * np.var(segment)

                    # Normalize
                    R[t, :] = R[t, :] / np.sum(R[t, :])

                    # Detect change point
                    if R[t, 0] > threshold:
                        change_points.append(t-1)
                        probabilities.append(R[t, 0])

                return change_points, probabilities, mean_vals, var_vals

            cp_indices, cp_probs, means, variances = bayesian_changepoint_detection(
                data,
                hazard_rate=prior_prob
            )

            # Store in session state
            st.session_state['cp_indices'] = cp_indices
            st.session_state['cp_probs'] = cp_probs
            st.session_state['cp_dates'] = dates
            st.session_state['cp_data'] = data
            st.session_state['cp_feature'] = selected_feature

    # Display results
    if 'cp_indices' in st.session_state:
        cp_indices = st.session_state['cp_indices']
        cp_probs = st.session_state['cp_probs']
        dates = st.session_state['cp_dates']
        data = st.session_state['cp_data']
        feature_name = st.session_state['cp_feature']

        st.success(f"Detected {len(cp_indices)} change points")

        # Create visualization
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            subplot_titles=[f'{feature_name} with Change Points', 'Change Point Probabilities'],
            vertical_spacing=0.1,
            row_heights=[0.7, 0.3]
        )

        # Plot original data
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=data,
                mode='lines',
                name=feature_name,
                line=dict(color='blue', width=1.5)
            ),
            row=1, col=1
        )

        # Mark change points
        for idx, prob in zip(cp_indices, cp_probs):
            if idx < len(dates):
                fig.add_vline(
                    x=dates[idx],
                    line_dash="dash",
                    line_color="green",
                    line_width=2,
                    row=1, col=1,
                    annotation_text=f"CP: {prob:.2f}",
                    annotation_position="top"
                )

                fig.add_trace(
                    go.Scatter(
                        x=[dates[idx]],
                        y=[data[idx]],
                        mode='markers',
                        marker=dict(color='red', size=10, symbol='star'),
                        name=f'CP {idx}',
                        showlegend=False
                    ),
                    row=1, col=1
                )

        # Add crisis markers
        for event, date in CRISIS_DATES.items():
            fig.add_shape(
                type="line",
                x0=date, x1=date,
                y0=0, y1=1,
                yref="paper",
                line=dict(color="orange", width=1, dash="dot"),
                row=1, col=1
            )
            fig.add_annotation(
                x=date,
                y=0,
                yref="y domain",
                text=event,
                showarrow=False,
                textangle=-90,
                xanchor="left",
                yanchor="top"
            )

        # Plot change point probabilities over time
        # Create a probability series
        cp_prob_series = np.zeros(len(dates))
        for idx, prob in zip(cp_indices, cp_probs):
            if idx < len(dates):
                cp_prob_series[idx] = prob

        fig.add_trace(
            go.Scatter(
                x=dates,
                y=cp_prob_series,
                mode='lines+markers',
                name='Change Point Probability',
                line=dict(color='red', width=1),
                marker=dict(size=3)
            ),
            row=2, col=1
        )

        fig.add_hline(y=threshold, line_dash="dash", line_color="gray", row=2, col=1,
                     annotation_text=f"Threshold ({threshold})")

        fig.update_layout(height=700, showlegend=True)
        fig.update_xaxes(title_text="Date", row=2, col=1)
        fig.update_yaxes(title_text=feature_name, row=1, col=1)
        fig.update_yaxes(title_text="Probability", row=2, col=1)

        st.plotly_chart(fig, use_container_width=True)

        # Change point details
        st.subheader("Detected Change Points")
        cp_details = []
        for idx, prob in zip(cp_indices, cp_probs):
            if idx < len(dates):
                # Calculate before/after statistics
                window = 20
                before_data = data[max(0, idx-window):idx]
                after_data = data[idx:min(len(data), idx+window)]

                cp_details.append({
                    'Date': dates[idx],
                    'Index': idx,
                    'Probability': f"{prob:.4f}",
                    'Value': f"{data[idx]:.4f}",
                    'Before Mean': f"{np.mean(before_data):.4f}" if len(before_data) > 0 else "N/A",
                    'After Mean': f"{np.mean(after_data):.4f}" if len(after_data) > 0 else "N/A",
                    'Change %': f"{100 * (np.mean(after_data) - np.mean(before_data)) / np.mean(before_data):.2f}%" if len(before_data) > 0 and len(after_data) > 0 else "N/A"
                })

        if cp_details:
            st.dataframe(pd.DataFrame(cp_details), use_container_width=True)
        else:
            st.info("No change points detected above threshold")

# ============================================================================
# COMBINED VIEW
# ============================================================================
else:  # Combined View
    st.header("📈 Combined Regime Analysis")

    st.markdown("""
    This view combines HMM regime detection and Bayesian change point detection to provide
    a comprehensive understanding of market regimes and structural breaks.
    """)

    # Check if both analyses have been run
    hmm_available = 'hmm_states' in st.session_state
    cp_available = 'cp_indices' in st.session_state

    if not hmm_available and not cp_available:
        st.warning("Please run HMM Regime Detection and/or Bayesian Change Point Detection first")
    else:
        # Select a feature to visualize
        all_numeric_cols = [col for col in df.columns if col != 'date' and pd.api.types.is_numeric_dtype(df[col])]
        selected_feature = st.selectbox("Select Feature to Visualize", all_numeric_cols)

        df_clean = df[['date', selected_feature]].dropna()

        # Create combined plot
        fig = make_subplots(
            rows=3, cols=1,
            shared_xaxes=True,
            subplot_titles=[
                f'{selected_feature}',
                'HMM Regimes' if hmm_available else 'No HMM Results',
                'Change Point Probability' if cp_available else 'No CP Results'
            ],
            vertical_spacing=0.05,
            row_heights=[0.4, 0.3, 0.3]
        )

        # Plot 1: Feature with both overlays
        fig.add_trace(
            go.Scatter(
                x=df_clean['date'],
                y=df_clean[selected_feature],
                mode='lines',
                name=selected_feature,
                line=dict(color='blue', width=1.5)
            ),
            row=1, col=1
        )

        # Add HMM regimes if available
        if hmm_available:
            hmm_states = st.session_state['hmm_states']
            hmm_dates = st.session_state['hmm_dates']
            n_regimes = len(np.unique(hmm_states))
            regime_colors = px.colors.qualitative.Set1[:n_regimes]

            # Plot regime backgrounds
            for regime in range(n_regimes):
                mask = hmm_states == regime
                if mask.any():
                    # Find continuous segments
                    segments = []
                    start = None
                    for i, (date, is_regime) in enumerate(zip(hmm_dates, mask)):
                        if is_regime and start is None:
                            start = date
                        elif not is_regime and start is not None:
                            segments.append((start, hmm_dates[i-1]))
                            start = None
                    if start is not None:
                        segments.append((start, hmm_dates[-1]))

                    # Add shaded regions
                    for start_date, end_date in segments:
                        fig.add_vrect(
                            x0=start_date, x1=end_date,
                            fillcolor=regime_colors[regime],
                            opacity=0.2,
                            layer="below",
                            line_width=0,
                            row=1, col=1
                        )

            # Plot 2: HMM Regimes
            for regime in range(n_regimes):
                mask = hmm_states == regime
                if mask.any():
                    fig.add_trace(
                        go.Scatter(
                            x=hmm_dates[mask],
                            y=np.ones(mask.sum()) * regime,
                            mode='markers',
                            name=f'Regime {regime}',
                            marker=dict(color=regime_colors[regime], size=4)
                        ),
                        row=2, col=1
                    )

        # Add change points if available
        if cp_available:
            cp_indices = st.session_state['cp_indices']
            cp_probs = st.session_state['cp_probs']
            cp_dates = st.session_state['cp_dates']
            cp_data = st.session_state['cp_data']

            # Mark change points on main plot
            for idx, prob in zip(cp_indices, cp_probs):
                if idx < len(cp_dates):
                    fig.add_vline(
                        x=cp_dates[idx],
                        line_dash="dash",
                        line_color="green",
                        line_width=2,
                        row=1, col=1
                    )

            # Plot 3: Change point probabilities
            cp_prob_series = np.zeros(len(cp_dates))
            for idx, prob in zip(cp_indices, cp_probs):
                if idx < len(cp_dates):
                    cp_prob_series[idx] = prob

            fig.add_trace(
                go.Scatter(
                    x=cp_dates,
                    y=cp_prob_series,
                    mode='lines+markers',
                    name='CP Probability',
                    line=dict(color='red', width=1),
                    marker=dict(size=3)
                ),
                row=3, col=1
            )

        # Add crisis markers to all plots
        for event, date in CRISIS_DATES.items():
            for row in [1, 2, 3]:
                fig.add_shape(
                    type="line",
                    x0=date, x1=date,
                    y0=0, y1=1,
                    yref="paper",
                    line=dict(color="orange", width=1, dash="dot"),
                    row=row, col=1
                )
            # Add annotation only to first plot
            fig.add_annotation(
                x=date,
                y=1,
                yref="y domain",
                text=event,
                showarrow=False,
                textangle=-90,
                xanchor="right",
                yanchor="bottom"
            )

        fig.update_layout(height=900, showlegend=True)
        fig.update_xaxes(title_text="Date", row=3, col=1)
        fig.update_yaxes(title_text=selected_feature, row=1, col=1)
        fig.update_yaxes(title_text="Regime", row=2, col=1)
        fig.update_yaxes(title_text="Probability", row=3, col=1)

        st.plotly_chart(fig, use_container_width=True)

        # Summary statistics
        st.subheader("Analysis Summary")

        col1, col2 = st.columns(2)

        with col1:
            if hmm_available:
                st.markdown("#### HMM Regimes")
                n_regimes = len(np.unique(st.session_state['hmm_states']))
                st.metric("Number of Regimes", n_regimes)
                st.metric("Features Used", len(st.session_state['hmm_features']))

                # Most common regime
                regime_counts = np.bincount(st.session_state['hmm_states'])
                most_common = np.argmax(regime_counts)
                st.metric("Most Common Regime", most_common)

        with col2:
            if cp_available:
                st.markdown("#### Change Points")
                st.metric("Change Points Detected", len(st.session_state['cp_indices']))
                if len(st.session_state['cp_probs']) > 0:
                    st.metric("Avg Probability", f"{np.mean(st.session_state['cp_probs']):.3f}")
                    st.metric("Max Probability", f"{np.max(st.session_state['cp_probs']):.3f}")

# Footer
st.markdown("---")
st.markdown("**Data Source:** Central Bank of Sri Lanka, External Sources | **Analysis:** HMM & Bayesian Change Point Detection")
