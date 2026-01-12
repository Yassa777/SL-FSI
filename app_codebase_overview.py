from __future__ import annotations

from pathlib import Path
import textwrap

import pandas as pd
import streamlit as st


ROOT = Path(__file__).resolve().parent
SRC_DIR = ROOT / "src" / "slfsi"
DOCS_DIR = ROOT / "DOCS"
CONFIGS_DIR = ROOT / "configs"

IGNORE_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    "data",
    "figures",
    "outputs",
    ".mypy_cache",
    ".pytest_cache",
}

PIPELINES = [
    {
        "Command": "build-panel",
        "Entrypoint": "src/slfsi/pipelines/build_panel.py",
        "Config": "configs/etl.yml",
        "Outputs": "data/merged/slfsi_daily_panel.csv, data/merged/slfsi_monthly_panel.csv",
    },
    {
        "Command": "download-external",
        "Entrypoint": "src/slfsi/pipelines/download_external.py",
        "Config": "configs/external_data.yml",
        "Outputs": "data/external/* and templates",
    },
    {
        "Command": "fetch-historical",
        "Entrypoint": "src/slfsi/pipelines/fetch_historical.py",
        "Config": "configs/historical_data.yml",
        "Outputs": "data/external/historical_*.csv",
    },
    {
        "Command": "train-hmm",
        "Entrypoint": "src/slfsi/pipelines/train_hmm.py",
        "Config": "configs/hmm.yml",
        "Outputs": "data/merged/hmm_regimes_*.csv, data/merged/hmm_probs_monthly.csv",
    },
    {
        "Command": "validate",
        "Entrypoint": "src/slfsi/pipelines/validate.py",
        "Config": "configs/validation.yml",
        "Outputs": "data/merged/validation_report.json, validation tables",
    },
    {
        "Command": "leading-indicators",
        "Entrypoint": "src/slfsi/pipelines/leading_indicators.py",
        "Config": "configs/leading_indicators.yml",
        "Outputs": "data/merged/monthly_with_indicators.csv",
    },
    {
        "Command": "mercado",
        "Entrypoint": "src/slfsi/pipelines/mercado.py",
        "Config": "configs/mercado.yml",
        "Outputs": "data/merged/mercado_fsi_monthly.csv",
    },
    {
        "Command": "combine",
        "Entrypoint": "src/slfsi/pipelines/combine.py",
        "Config": "configs/combine.yml",
        "Outputs": "data/merged/combined_fsi_hmm.csv",
    },
    {
        "Command": "theory",
        "Entrypoint": "src/slfsi/pipelines/theory.py",
        "Config": "configs/theory.yml",
        "Outputs": "data/merged/monthly_with_theory_regimes.csv",
    },
    {
        "Command": "analyze",
        "Entrypoint": "src/slfsi/pipelines/analyze.py",
        "Config": "configs/analysis.yml",
        "Outputs": "tables/plots from validation comparison",
    },
]

MODULES = [
    {
        "name": "config",
        "path": "src/slfsi/config",
        "summary": "Configuration loading, schema mapping, logging, and repo paths.",
        "highlights": [
            "settings.py centralizes repo and data directories",
            "schema.py defines canonical column names and groups",
            "loader.py reads YAML/JSON configs",
        ],
    },
    {
        "name": "etl",
        "path": "src/slfsi/etl",
        "summary": "Ingestion, cleaning, merging, and data-quality checks.",
        "highlights": [
            "ingest.py reads raw sources with rename rules",
            "merge.py builds daily and monthly panels plus overlays",
            "quality.py audits coverage and crisis-window gaps",
        ],
    },
    {
        "name": "features",
        "path": "src/slfsi/features",
        "summary": "Daily and monthly feature engineering for stress signals.",
        "highlights": [
            "daily.py computes returns, volatility, spreads, slopes",
            "monthly.py computes reserve cover and real rates",
            "transforms.py contains shared feature helpers",
        ],
    },
    {
        "name": "models/hmm",
        "path": "src/slfsi/models/hmm",
        "summary": "Hidden Markov Model training and validation utilities.",
        "highlights": [
            "fit.py standardizes features and labels regimes",
            "realtime.py simulates recursive real-time fitting",
            "oos.py evaluates train/test splits and calibration",
        ],
    },
    {
        "name": "models",
        "path": "src/slfsi/models",
        "summary": "FSI model variants and regime combination logic.",
        "highlights": [
            "mercado.py builds the Mercado-Park FSI",
            "combine.py fuses FSI scores with HMM probabilities",
            "theory.py applies threshold-based regime rules",
        ],
    },
    {
        "name": "pipelines",
        "path": "src/slfsi/pipelines",
        "summary": "CLI-exposed workflows that orchestrate the full stack.",
        "highlights": [
            "build_panel, train_hmm, validate, theory, combine",
            "download_external and fetch_historical data helpers",
        ],
    },
    {
        "name": "validation",
        "path": "src/slfsi/validation",
        "summary": "Evaluation framework, event alignment, and reporting.",
        "highlights": [
            "framework.py compares HMM vs z-score baselines",
            "enhanced.py computes tactical/strategic alerts",
            "reporting.py outputs JSON and markdown summaries",
        ],
    },
    {
        "name": "plots",
        "path": "src/slfsi/plots",
        "summary": "Reusable plot helpers for reporting and dashboards.",
        "highlights": ["three_panel.py builds multi-panel comparisons"],
    },
]

ROOT_SCRIPTS = {
    "app_regime_analysis.py": "Streamlit dashboard for regime analysis.",
    "cross_country_framework.py": "Framework for Pakistan/Ghana regime analysis.",
    "cross_country_synthesis.py": "Cross-country synthesis outputs.",
    "hmm_cross_country.py": "HMM training for cross-country data.",
    "stress_test_hmm.py": "Stress tests for HMM robustness.",
    "validate_cross_country_data.py": "Quality checks for cross-country sources.",
    "enhance_cross_country_data.py": "Feature enhancements for cross-country panels.",
    "test_feature_dimensionality.py": "Feature dimensionality experiments.",
}


def _iter_files(root: Path, pattern: str) -> list[Path]:
    paths: list[Path] = []
    for path in root.rglob(pattern):
        if any(part in IGNORE_DIRS for part in path.parts):
            continue
        paths.append(path)
    return sorted(paths)


def _build_tree(root: Path, max_depth: int = 2) -> str:
    lines: list[str] = []
    root_depth = len(root.parts)
    for path in sorted(root.rglob("*")):
        if any(part in IGNORE_DIRS for part in path.parts):
            continue
        depth = len(path.parts) - root_depth
        if depth > max_depth:
            continue
        indent = "  " * depth
        suffix = "/" if path.is_dir() else ""
        lines.append(f"{indent}- {path.name}{suffix}")
    return "\n".join(lines)


def _read_text(path: Path, limit: int = 12000) -> tuple[str, bool]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    truncated = len(text) > limit
    if truncated:
        text = text[:limit].rstrip() + "\n\n... (truncated)"
    return text, truncated


def _section_title(title: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <div class="section-card">
          <div class="section-title">{title}</div>
          <div class="section-subtitle">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


st.set_page_config(page_title="SL-FSI Codebase Atlas", layout="wide")

st.markdown(
    """
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Fraunces:wght@600;700&family=Space+Grotesk:wght@400;600&display=swap');
      :root {
        --bg: #f6f1e9;
        --bg-2: #efe3d2;
        --ink: #1f1a12;
        --muted: #5b4f45;
        --accent: #0f6d6a;
        --accent-2: #d9792b;
        --card: #fffaf2;
        --line: #e2d6c7;
      }
      .stApp {
        background: radial-gradient(1200px 600px at 10% 10%, #fdf7ef 0%, #f6f1e9 50%, #efe3d2 100%);
        color: var(--ink);
      }
      h1, h2, h3, h4, h5, h6, .hero-title, .section-title {
        font-family: "Fraunces", serif;
        letter-spacing: -0.02em;
      }
      body, p, li, div, span {
        font-family: "Space Grotesk", sans-serif;
        color: var(--ink);
      }
      .hero {
        background: linear-gradient(120deg, rgba(15,109,106,0.15), rgba(217,121,43,0.12));
        border: 1px solid var(--line);
        border-radius: 18px;
        padding: 24px 28px;
        margin-bottom: 18px;
      }
      .hero-title {
        font-size: 36px;
        margin-bottom: 8px;
      }
      .hero-subtitle {
        font-size: 16px;
        color: var(--muted);
      }
      .section-card {
        background: var(--card);
        border: 1px solid var(--line);
        border-radius: 14px;
        padding: 16px 18px;
        margin: 12px 0 16px 0;
      }
      .section-title {
        font-size: 22px;
        margin-bottom: 6px;
      }
      .section-subtitle {
        color: var(--muted);
        font-size: 14px;
      }
      .tag {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 999px;
        background: rgba(15,109,106,0.12);
        color: var(--accent);
        font-size: 12px;
        margin-right: 6px;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
      <div class="hero-title">SL-FSI Codebase Atlas</div>
      <div class="hero-subtitle">
        Interactive map of pipelines, models, configs, and docs for the Sri Lanka Financial Stress Index project.
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

section = st.sidebar.radio(
    "Navigate",
    [
        "Overview",
        "Architecture",
        "Pipelines",
        "Modules",
        "Configs",
        "Docs",
        "Scripts",
        "Testing",
    ],
)

python_files = _iter_files(ROOT, "*.py")
doc_files = _iter_files(DOCS_DIR, "*.md") if DOCS_DIR.exists() else []
config_files = _iter_files(CONFIGS_DIR, "*.yml") if CONFIGS_DIR.exists() else []
test_files = _iter_files(ROOT / "tests", "test_*.py") if (ROOT / "tests").exists() else []

if section == "Overview":
    _section_title("Repository Snapshot", "What lives where and how the pieces fit together.")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Python files", f"{len(python_files)}")
    col2.metric("Docs", f"{len(doc_files)}")
    col3.metric("Configs", f"{len(config_files)}")
    col4.metric("Tests", f"{len(test_files)}")

    st.markdown("Key entrypoints:")
    st.code(
        textwrap.dedent(
            """
            streamlit run app_regime_analysis.py
            streamlit run app_codebase_overview.py
            python -m slfsi --help
            python -m slfsi build-panel
            python -m slfsi train-hmm
            python -m slfsi validate
            """
        ).strip(),
        language="bash",
    )

    with st.expander("Show repository tree (depth 2)"):
        tree = _build_tree(ROOT, max_depth=2)
        st.code(tree, language="text")

    st.markdown(
        """
        This project centers on constructing daily and monthly panels, engineering stress features,
        fitting HMM regimes, and validating regimes against known crisis events. The CLI wraps
        these workflows, while Streamlit apps provide interactive exploration.
        """
    )

elif section == "Architecture":
    _section_title("System Flow", "From raw data to regimes, validation, and dashboards.")

    st.graphviz_chart(
        """
        digraph {
          rankdir=LR;
          node [shape=box, style="rounded,filled", fillcolor="#fffaf2", color="#e2d6c7"];
          edge [color="#6a5b4a"];
          "data/raw + data/external" -> "ETL (ingest, merge)";
          "ETL (ingest, merge)" -> "Panels (daily/monthly)";
          "Panels (daily/monthly)" -> "Features (daily/monthly)";
          "Features (daily/monthly)" -> "HMM training";
          "HMM training" -> "Regimes + probabilities";
          "Regimes + probabilities" -> "Validation";
          "Regimes + probabilities" -> "Streamlit app";
          "Panels (daily/monthly)" -> "Mercado FSI";
          "Mercado FSI" -> "Combine FSI + HMM";
        }
        """
    )

    st.markdown(
        """
        The core loop is data ingestion -> feature engineering -> regime modeling -> validation.
        Additional branches include the Mercado FSI pipeline and theory-based regimes.
        """
    )

    _section_title("Data Layout", "Where inputs and outputs live on disk.")
    st.code(
        textwrap.dedent(
            """
            data/
              raw/        manual inputs and historical source files
              external/   downloaded global series and templates
              processed/  intermediate transforms
              merged/     daily/monthly panels and model outputs
              quality/    quality checks and coverage reports
            """
        ).strip(),
        language="text",
    )

elif section == "Pipelines":
    _section_title("CLI Pipelines", "Commands exposed via python -m slfsi.")
    st.dataframe(pd.DataFrame(PIPELINES), use_container_width=True, hide_index=True)

    st.markdown("Each command reads its config from `configs/` unless a custom path is provided.")

elif section == "Modules":
    _section_title("Module Map", "Primary packages and what they own.")
    for module in MODULES:
        with st.expander(f"{module['name']}  |  {module['path']}"):
            st.markdown(module["summary"])
            for item in module["highlights"]:
                st.markdown(f"- {item}")

    _section_title("CLI Surface", "The slfsi package exposes a single CLI.")
    st.code(
        textwrap.dedent(
            """
            python -m slfsi version
            python -m slfsi show-config
            python -m slfsi build-panel
            python -m slfsi train-hmm
            python -m slfsi validate
            """
        ).strip(),
        language="bash",
    )

elif section == "Configs":
    _section_title("Config Library", "YAML configs used by pipelines and apps.")
    if not config_files:
        st.warning("No configs folder detected.")
    else:
        selected = st.selectbox(
            "Select a config file",
            options=[str(path.relative_to(ROOT)) for path in config_files],
        )
        if selected:
            path = ROOT / selected
            content, _ = _read_text(path)
            st.code(content, language="yaml")

elif section == "Docs":
    _section_title("Project Docs", "Narrative references and validation notes.")
    if not doc_files:
        st.warning("No docs folder detected.")
    else:
        selected = st.selectbox(
            "Select a doc",
            options=[str(path.relative_to(ROOT)) for path in doc_files],
        )
        if selected:
            path = ROOT / selected
            content, _ = _read_text(path)
            st.markdown(content)

elif section == "Scripts":
    _section_title("Root Scripts", "One-off analyses and experiments.")
    script_rows = []
    for script, desc in ROOT_SCRIPTS.items():
        path = ROOT / script
        if path.exists():
            script_rows.append({"Script": script, "Purpose": desc})
    if script_rows:
        st.dataframe(pd.DataFrame(script_rows), use_container_width=True, hide_index=True)
    else:
        st.info("No root scripts detected.")

    with st.expander("Show script contents"):
        script_names = [row["Script"] for row in script_rows]
        if script_names:
            selected = st.selectbox("Script", options=script_names)
            content, _ = _read_text(ROOT / selected)
            st.code(content, language="python")

elif section == "Testing":
    _section_title("Tests", "Lightweight checks for features, quality, and CLI.")
    if not test_files:
        st.info("No tests detected.")
    else:
        st.markdown("Available tests:")
        for path in test_files:
            st.markdown(f"- {path.relative_to(ROOT)}")

        with st.expander("Show a test file"):
            selected = st.selectbox(
                "Test file",
                options=[str(path.relative_to(ROOT)) for path in test_files],
            )
            content, _ = _read_text(ROOT / selected)
            st.code(content, language="python")
