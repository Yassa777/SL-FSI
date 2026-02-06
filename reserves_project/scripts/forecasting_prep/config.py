"""Configuration for forecasting dataset preparation."""

from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DIAG_DIR = DATA_DIR / "diagnostics"
OUTPUT_DIR = DATA_DIR / "forecast_prep"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TARGET_VAR = "gross_reserves_usd_m"

ARIMA_EXOG_VARS = [
    "exports_usd_m",
    "imports_usd_m",
    "remittances_usd_m",
    "usd_lkr",
]

VECM_SYSTEM_VARS = [
    "gross_reserves_usd_m",
    "exports_usd_m",
    "imports_usd_m",
    "remittances_usd_m",
    "usd_lkr",
]

MS_VAR_SYSTEM_VARS = [
    "gross_reserves_usd_m",
    "usd_lkr",
    "exports_usd_m",
    "imports_usd_m",
]

TRAIN_END = pd.Timestamp("2019-12-01")
VALID_END = pd.Timestamp("2022-12-01")

MIN_OBS_VECM = 100
MIN_OBS_MS = 80
