from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "reserves_project" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from run_diagnostics import run_all_diagnostics  # noqa: E402


def test_modular_runner_produces_all_phases() -> None:
    results, summaries = run_all_diagnostics(verbose=False)

    assert "phase2_stationarity" in results
    assert "phase3_temporal" in results
    assert "phase4_volatility" in results
    assert "phase5_breaks" in results
    assert "phase6_relationships" in results
    assert "phase7_cointegration" in results
    assert "phase8_svar" in results
    assert "phase9_multiple_breaks" in results
    assert "integration" in summaries
    assert "cointegration_engle_granger" in summaries
    assert "svar_model" in summaries
    assert "bai_perron" in summaries
    assert len(results["phase2_stationarity"]["integration_summary"]) > 0


def test_fx_column_repaired_and_tested() -> None:
    results, summaries = run_all_diagnostics(verbose=False)

    quality = summaries["quality"]
    usd_row = quality.loc[quality["variable"] == "usd_lkr"].iloc[0]
    assert bool(usd_row["is_usable"])
    assert int(usd_row["non_null_obs"]) > 200

    tested_vars = results["metadata"]["variables_tested"]
    assert "usd_lkr" in tested_vars


def test_advanced_diagnostics_have_outputs() -> None:
    results, summaries = run_all_diagnostics(verbose=False)

    eg_rows = results["phase7_cointegration"]["engle_granger"]
    assert len(eg_rows) > 0
    assert "johansen" in results["phase7_cointegration"]

    svar_meta = results["phase8_svar"]["metadata"]
    assert "variables" in svar_meta
    assert len(svar_meta.get("variables", [])) >= 3

    bp_rows = results["phase9_multiple_breaks"]["bai_perron"]
    assert len(bp_rows) > 0
    assert "bai_perron" in summaries
