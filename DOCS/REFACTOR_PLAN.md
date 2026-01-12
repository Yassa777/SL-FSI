# SL-FSI Refactor Plan (Single Source of Truth)
Date: 2026-01-XX
Status: Draft for multi-agent execution

This document is the single source of truth for the refactor plan. If any other doc or ticket conflicts with this plan, this plan wins. Update this file first as decisions change.

---

## Context Header (for multi-agent handoff)

- Repo: `/Users/dim/Desktop/Spill Projects/SL-FSI`
- Goal: Refactor the current script-based workflow into a production-grade, modular Python package with strong reproducibility, typing, and economic-intent documentation.
- Non-goals (for now): Model changes or new data sources. The refactor should preserve outputs unless explicitly noted.
- Hard requirements:
  - No hardcoded file paths or column names in core logic.
  - Central config and loader.
  - Strict type hints on all functions.
  - Google-style docstrings that explain the economic intent.
  - Replace all `print()` with structured logging.
  - Monthly data upsampling to daily must be documented and performed after volatility calculations to avoid artifacts.
  - Add checks for critical data gaps.
- Key inputs/outputs (current):
  - ETL entrypoint: `scripts/merge_all_data.py`
  - Outputs: `data/merged/slfsi_daily_panel.csv`, `data/merged/slfsi_monthly_panel.csv`
- Known hardcoded sources:
  - Columns like `USD_Spot_Rate`, `EQUITY__All_share_price_index`, `Primary`, `Secondary` (see `scripts/merge_all_data.py`)
  - Paths like `data/processed`, `data/external`, `data/merged` (see `scripts/merge_all_data.py`)
- Data frequency rule (critical):
  - Compute daily volatility on native daily series.
  - Compute monthly features on monthly series.
  - Upsample monthly to daily only after monthly features are computed.

---

## Target Package Skeleton (proposed)

```
pyproject.toml
src/
  slfsi/
    __init__.py
    cli.py
    config/
      __init__.py
      settings.py        # pydantic/dataclass settings + env overrides
      paths.py           # repo root + data directory resolution
      schema.py          # canonical column names + mappings
      loader.py          # YAML/JSON config loader
      logging.py         # logging setup (format, level, handlers)
    io/
      __init__.py
      readers.py         # typed CSV/Excel readers
      writers.py
    etl/
      __init__.py
      ingest.py          # source-by-source ingestion
      clean.py           # numeric/date parsing, cleaning rules
      merge.py           # merge/join logic
      resample.py        # monthly->daily upsample rules
      quality.py         # gap checks and coverage reporting
    features/
      __init__.py
      daily.py           # returns, daily volatility, daily transforms
      monthly.py         # monthly transforms (reserves, inflation, etc)
      transforms.py      # shared transforms (winsorize, z-score)
    models/
      __init__.py
      hmm/
        __init__.py
        fit.py
        diagnostics.py
      regime.py
    validation/
      __init__.py
      event_alignment.py
      gaps.py
    pipelines/
      __init__.py
      build_panel.py     # end-to-end ETL pipeline
      train_hmm.py
    utils/
      __init__.py
      dates.py
      typing.py
configs/
  data_sources.yml
  schema.yml
  features.yml
  logging.yml
tests/
  test_etl_quality.py
  test_feature_defs.py
  test_pipeline_smoke.py
```

Notes:
- Keep data files in `data/` (outside `src/`) to avoid packaging them by default.
- Use a `src/` layout so imports are explicit and reliable.
- Scripts become thin CLI entrypoints or are replaced by `slfsi.cli`.

---

## Config + Schema Strategy (removes hardcoding)

**Design**
- `configs/data_sources.yml` defines each source: path, date column, frequency, rename map.
- `configs/schema.yml` defines canonical column names and groups (daily, monthly, market, macro).
- `configs/features.yml` defines feature formulas (e.g., rolling windows).

**Example (data_sources.yml)**
```
sources:
  usd_lkr:
    path: data/processed/D1_usd_lkr.csv
    date_col: date
    rename:
      USD_Spot_Rate: usd_lkr
    frequency: daily
  aspi:
    path: data/processed/D3_aspi.csv
    date_col: date
    rename:
      EQUITY__All_share_price_index: aspi
    frequency: daily
```

**Economic intent in docstrings**
- Each transform must state the economic meaning, e.g.:
  - “Rolling FX volatility captures market stress and liquidity uncertainty.”
  - “Real policy rate reflects monetary stance and inflation-adjusted funding cost.”

---

## Logging Strategy

- Centralized logging config in `slfsi/config/logging.py` or `configs/logging.yml`.
- Use module-level loggers (`logger = logging.getLogger(__name__)`).
- Standard format includes timestamp, level, module, and message.
- Pipeline entrypoints log start/end, row counts, and missingness summaries.

---

## Data Quality and Gap Checks

Minimum checks (configurable):
- Maximum consecutive gap per series (e.g., > 30 days for daily, > 2 months for monthly).
- Coverage ratio in crisis window (e.g., 2020-01-01 to 2023-12-31).
- Zero placeholders (ASPI/SL20) are treated as missing.
- Date monotonicity and duplicate date checks.

Output: `quality_report.json` or `quality_report.csv` stored in `data/quality/`.

---

## Multi-Chunk Execution Plan (handoff-ready)

### Chunk 0: Inventory + Interface Map
Goal: Build a complete map of current scripts, data sources, and outputs.
Scope:
- Read all pipeline scripts: `scripts/merge_all_data.py`, `enhanced_validation.py`, `validation_framework.py`, `cross_country_framework.py`.
- Produce an inventory table of: source file, expected columns, frequency, output artifacts.
Deliverables:
- `DOCS/refactor_inventory.md` with source -> canonical mapping.
Definition of done:
- All current outputs and sources are identified, and risks are listed.

### Chunk 1: Package Scaffolding + Tooling
Goal: Create the package skeleton with config and logging infrastructure.
Scope:
- Add `pyproject.toml` with dependencies and tool config (ruff, mypy, pytest).
- Create `src/slfsi` layout with `config/`, `etl/`, `features/`, `pipelines/`.
- Add logging setup (no code migration yet).
Deliverables:
- Package skeleton and `slfsi/config/logging.py`.
Definition of done:
- `python -m slfsi.cli --help` works; logging config is importable.

### Chunk 2: Central Config + Schema Migration
Goal: Remove hardcoded paths/columns by moving them to config.
Scope:
- Create `configs/data_sources.yml` and `configs/schema.yml`.
- Replace `PROJECT_ROOT`, `PROCESSED_DIR`, `EXTERNAL_DIR` in `scripts/merge_all_data.py` with config lookups.
- Move rename maps (e.g., `USD_Spot_Rate -> usd_lkr`) into config.
Deliverables:
- Config files + loader in `slfsi/config/loader.py`.
Definition of done:
- `scripts/merge_all_data.py` (or new pipeline) runs using only config.

### Chunk 3: ETL Module + Frequency Discipline
Goal: Implement modular ETL with explicit frequency handling.
Scope:
- `slfsi/etl/ingest.py`: source loaders with typed outputs.
- `slfsi/etl/clean.py`: numeric conversion, date parsing, zero-as-missing.
- `slfsi/etl/merge.py`: merged daily + monthly panels.
- `slfsi/etl/resample.py`: upsample monthly -> daily after monthly features.
Deliverables:
- `slfsi/pipelines/build_panel.py` end-to-end.
Definition of done:
- Monthly features are computed before any upsampling step; documented in docstrings.

### Chunk 4: Feature Engineering Modules
Goal: Move feature logic into `slfsi/features`.
Scope:
- Daily: returns, rolling volatility, spreads.
- Monthly: reserve changes, inflation metrics, real rates.
- Shared: z-scores, winsorization, scaling.
Deliverables:
- `slfsi/features/daily.py`, `slfsi/features/monthly.py`, `slfsi/features/transforms.py`.
Definition of done:
- Feature computations no longer live in scripts.

### Chunk 5: Data Quality + Validation Utilities
Goal: Add automated checks for critical data gaps and summary metrics.
Scope:
- Implement gap checks in `slfsi/etl/quality.py` and `slfsi/validation/gaps.py`.
- Add coverage checks for crisis window.
Deliverables:
- `data/quality/quality_report.csv`.
Definition of done:
- Pipeline fails fast on critical gaps (configurable thresholds).

### Chunk 6: Model + Validation Refactor
Goal: Encapsulate HMM and validation logic in `slfsi/models` and `slfsi/validation`.
Scope:
- Move HMM fit and diagnostics into `slfsi/models/hmm`.
- Move event-alignment evaluation into `slfsi/validation/event_alignment.py`.
Deliverables:
- Model pipeline uses the new package modules.
Definition of done:
- Existing model outputs preserved (within tolerance).

### Chunk 7: CLI + Script Deprecation
Goal: Provide a clean CLI and thin wrappers for backward compatibility.
Scope:
- `slfsi/cli.py` with commands: `build-panel`, `train-hmm`, `validate`.
- Update old scripts to call into package or mark deprecated.
Deliverables:
- CLI help + stable entrypoints.
Definition of done:
- Users can run pipelines without touching scripts.

---

## Migration Map + Ordered Checklist (Executable Plan)

This section translates the inventory into a concrete migration order. Each step
should preserve outputs while removing hardcoded paths/columns from core logic.

### Script -> Module Map

| Script | Target module(s) | Notes |
| --- | --- | --- |
| `scripts/merge_all_data.py` | `slfsi/pipelines/build_panel.py`, `slfsi/etl/*` | Already migrated; deprecate script with wrapper. |
| `scripts/download_external_data.py` | `slfsi/pipelines/download_external.py`, `slfsi/io/readers.py` | New pipeline + shared IO. |
| `scripts/fetch_historical_data.py` | `slfsi/pipelines/fetch_historical.py`, `slfsi/io/readers.py` | New pipeline + shared IO. |
| `scripts/compute_leading_indicators.py` | `slfsi/pipelines/leading_indicators.py` | Mostly migrated; replace script. |
| `validation_framework.py` | `slfsi/validation/framework.py`, `slfsi/pipelines/validate.py` | Mostly migrated. |
| `enhanced_validation.py` | `slfsi/validation/enhanced.py`, `slfsi/pipelines/validate.py` | Migrated. |
| `recursive_realtime_hmm.py` | `slfsi/models/hmm/realtime.py`, `slfsi/pipelines/train_hmm.py` | Pending. |
| `out_of_sample_validation.py` | `slfsi/models/hmm/oos.py`, `slfsi/pipelines/validate.py` | Pending. |
| `mercado_fsi.py` | `slfsi/models/mercado.py`, `slfsi/pipelines/mercado.py` | Pending. |
| `combined_fsi_hmm.py` | `slfsi/models/combine.py`, `slfsi/pipelines/combine.py` | Pending. |
| `compare_fsi_hmm.py` | `slfsi/validation/compare.py` | Pending. |
| `three_panel_comparison.py` | `slfsi/plots/three_panel.py` | Pending. |
| `feature_overlap_analysis.py` | `slfsi/validation/feature_overlap.py` | Pending. |
| `transition_dynamics.py` | `slfsi/validation/transitions.py` | Pending. |
| `theory_based_classification.py` | `slfsi/models/theory.py` | Pending. |
| `app_regime_analysis.py` | keep as app; read from `slfsi` modules/configs | Replace hardcoded lists. |

### Ordered Checklist (Migrate in This Sequence)

1) Core IO + external data pipelines  
   - Add `slfsi/io/readers.py`  
   - Migrate `scripts/download_external_data.py`  
   - Migrate `scripts/fetch_historical_data.py`  
   - Add configs for external sources as needed  

2) Deprecate old ETL entrypoint  
   - Replace `scripts/merge_all_data.py` with wrapper calling `slfsi build-panel`  
   - Remove hardcoded paths/columns from the script wrapper  

3) Feature modules + Mercado FSI  
   - Implement `slfsi/features/daily.py`, `slfsi/features/monthly.py`, `slfsi/features/transforms.py`  
   - Migrate `mercado_fsi.py` into model + pipeline modules  

4) HMM model pipelines  
   - Implement `slfsi/models/hmm/*` and `slfsi/pipelines/train_hmm.py`  
   - Migrate `recursive_realtime_hmm.py` and `out_of_sample_validation.py`  

5) Validation utilities  
   - Migrate `feature_overlap_analysis.py`, `transition_dynamics.py`, `compare_fsi_hmm.py`  

6) Visualization + app  
   - Migrate `three_panel_comparison.py` into `slfsi/plots/three_panel.py`  
   - Update `app_regime_analysis.py` to use config + modules  

7) Final cleanup  
   - Deprecate remaining scripts with thin wrappers + warnings  
   - Enforce structured logging and schema use across modules  

---

### Updated Checklist (Status)

#### ETL + Data Ingestion
- [x] Shared IO helpers in `src/slfsi/io/readers.py` and `src/slfsi/io/writers.py`.  
- [x] External data pipeline in `src/slfsi/pipelines/download_external.py` and wrapper script.  
- [x] Historical data pipeline in `src/slfsi/pipelines/fetch_historical.py` and wrapper script.  
- [x] Config-driven panel build in `src/slfsi/pipelines/build_panel.py`.  
- [x] Replace `scripts/merge_all_data.py` with a wrapper calling `slfsi build-panel`.  
- [x] Add crisis-window coverage checks to `src/slfsi/etl/quality.py` and `configs/quality.yml`.  

#### Remaining Migration Buckets
- [x] Create feature modules under `src/slfsi/features/` and move feature logic out of ETL.  
- [x] Complete `src/slfsi/models/hmm/*` and finish `src/slfsi/pipelines/train_hmm.py`.  
- [x] Migrate remaining validation, plotting, and app hardcoding into config.  

---

## Agent Handoff Template (copy into each chunk ticket)

```
Context:
- Repo: /Users/dim/Desktop/Spill Projects/SL-FSI
- SSOT plan: REFACTOR_PLAN.md (this file)
- Goal for this chunk: <chunk goal>
- Non-goals: <what not to change>
- Inputs: <files / configs>
- Outputs: <new files, updated files>
- Definition of done: <tests, output artifacts>
- Risks: <data dependencies or edge cases>
```

---

## Immediate Next Action (recommended)

Start with Chunk 0 to build the inventory and agree on canonical columns and data sources before touching code. This minimizes rework when the config schema is finalized.
