from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "reserves_project" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from prepare_forecasting_data import run_forecasting_prep  # noqa: E402


def test_forecasting_prep_outputs_exist() -> None:
    outputs, metadata, readiness = run_forecasting_prep(verbose=False)

    for path in outputs.values():
        assert Path(path).exists()

    assert metadata["arima"]["rows"] > 100
    assert metadata["vecm"]["rows_levels"] > 100
    assert metadata["ms_var"]["rows"] > 100

    models = set(readiness["model"].tolist())
    assert {"ARIMA", "VECM", "MS-VAR", "MS-VECM"}.issubset(models)


def test_forecasting_prep_split_labels_present() -> None:
    outputs, _, _ = run_forecasting_prep(verbose=False)

    for key in ["arima", "vecm_levels", "vecm_state", "ms_var_raw", "ms_var_scaled"]:
        df = pd.read_csv(outputs[key])
        assert "split" in df.columns
        assert set(df["split"].unique()).issubset({"train", "validation", "test"})
