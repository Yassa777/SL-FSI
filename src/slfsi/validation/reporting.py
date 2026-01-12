"""Reporting helpers for validation outputs."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional

import pandas as pd


def build_framework_report(
    *,
    hmm_config: Mapping[str, Any],
    windows: Mapping[str, Any],
    costs: Mapping[str, Any],
    tactical_metrics: Mapping[str, Mapping[str, float]],
    strategic_metrics: Mapping[str, Mapping[str, float]],
    false_alarm: Mapping[str, float],
    transitions: pd.DataFrame,
    hmm_tactical: Mapping[str, Any],
    hmm_strategic: Mapping[str, Any],
    baseline_tactical: Mapping[str, Any],
    baseline_strategic: Mapping[str, Any],
) -> Dict[str, Any]:
    """Build a structured report for the validation framework.

    Economic intent:
        A structured report makes model validation auditable by preserving
        the exact assumptions and event alignment outcomes.

    Args:
        hmm_config: Configuration for the HMM model.
        windows: Evaluation window configuration.
        costs: Cost-weighted scoring configuration.
        tactical_metrics: Tactical window metrics.
        strategic_metrics: Strategic window metrics.
        false_alarm: False alarm summary.
        transitions: Dataframe of regime transitions.
        hmm_tactical: HMM tactical event alignment results.
        hmm_strategic: HMM strategic event alignment results.
        baseline_tactical: Baseline tactical event alignment results.
        baseline_strategic: Baseline strategic event alignment results.

    Returns:
        Structured report dictionary.
    """
    transition_rows = []
    if not transitions.empty:
        for row in transitions.to_dict(orient="records"):
            date_val = row.get("date")
            if isinstance(date_val, pd.Timestamp):
                row["date"] = date_val.strftime("%Y-%m-%d")
            transition_rows.append(row)

    first_stress = next((row for row in transition_rows if row.get("to") == "STRESS"), None)
    first_crisis = next((row for row in transition_rows if row.get("to") == "CRISIS"), None)

    return {
        "hmm_config": hmm_config,
        "windows": windows,
        "costs": costs,
        "metrics": {
            "tactical": tactical_metrics,
            "strategic": strategic_metrics,
        },
        "false_alarm": false_alarm,
        "transitions": transition_rows,
        "first_stress": first_stress,
        "first_crisis": first_crisis,
        "event_alignment": {
            "tactical": hmm_tactical.get("details", []),
            "strategic": hmm_strategic.get("details", []),
            "baseline_tactical": baseline_tactical.get("details", []),
            "baseline_strategic": baseline_strategic.get("details", []),
        },
    }


def build_enhanced_report(
    *,
    tau: float,
    k: int,
    tactical_months: int,
    strategic_months: int,
    tactical_df: pd.DataFrame,
    strategic_df: pd.DataFrame,
) -> Dict[str, Any]:
    """Build a structured report for enhanced validation.

    Economic intent:
        Sustained crossing rules are sensitive to tau/K choices, so the
        report captures those parameters alongside hit rates.

    Args:
        tau: Probability threshold.
        k: Consecutive months required.
        tactical_months: Tactical window size.
        strategic_months: Strategic window size.
        tactical_df: Tactical results dataframe.
        strategic_df: Strategic results dataframe.

    Returns:
        Structured report dictionary.
    """
    tactical_hit_rate = float(tactical_df["is_hit"].mean()) if not tactical_df.empty else 0.0
    strategic_hit_rate = float(strategic_df["is_hit"].mean()) if not strategic_df.empty else 0.0

    return {
        "tau": tau,
        "k": k,
        "tactical_months": tactical_months,
        "strategic_months": strategic_months,
        "tactical_hit_rate": tactical_hit_rate,
        "strategic_hit_rate": strategic_hit_rate,
        "tactical_results": tactical_df.to_dict(orient="records"),
        "strategic_results": strategic_df.to_dict(orient="records"),
    }


def render_markdown(report: Mapping[str, Any]) -> str:
    """Render a validation report as Markdown.

    Economic intent:
        A human-readable report supports review and sign-off of model
        validation decisions.

    Args:
        report: Structured report dictionary.

    Returns:
        Markdown string.
    """
    lines = ["# SL-FSI Validation Report", ""]
    lines.append(f"Generated: {report.get('generated_at', '')}")
    lines.append("")

    framework = report.get("framework")
    if framework:
        lines.append("## Framework Validation")
        lines.append("")
        hmm_cfg = framework.get("hmm_config", {})
        lines.append("### HMM Configuration")
        lines.append("")
        lines.append("- features: " + ", ".join(hmm_cfg.get("features", [])))
        lines.append(f"- n_states: {hmm_cfg.get('n_states')}")
        lines.append(f"- covariance_type: {hmm_cfg.get('covariance_type')}")
        lines.append(f"- n_iter: {hmm_cfg.get('n_iter')}")
        lines.append(f"- random_state: {hmm_cfg.get('random_state')}")
        lines.append("")

        metrics = framework.get("metrics", {})
        lines.append("### Metrics Summary")
        lines.append("")
        lines.append("| Window | Model | Hit Rate | Misses | Hits | Cost Score |")
        lines.append("| --- | --- | --- | --- | --- | --- |")
        for window_label in ("tactical", "strategic"):
            window_metrics = metrics.get(window_label, {})
            for model_name, vals in window_metrics.items():
                hit_rate = vals.get("hit_rate", 0)
                lines.append(
                    f"| {window_label} | {model_name} | {hit_rate:.1%} | "
                    f"{vals.get('misses')} | {vals.get('hits')} | {vals.get('cost_weighted_score')} |"
                )
        lines.append("")

        false_alarm = framework.get("false_alarm", {})
        lines.append("### False Alarm Summary")
        lines.append("")
        lines.append(
            f"- total_transitions: {false_alarm.get('total_transitions')}\n"
            f"- justified: {false_alarm.get('justified')}\n"
            f"- false_alarms: {false_alarm.get('false_alarms')}\n"
            f"- false_alarm_rate: {false_alarm.get('false_alarm_rate')}"
        )
        lines.append("")

        lines.append("### Strategic Event Alignment (HMM)")
        lines.append("")
        lines.append("| Date | Event | Expected | Detected | Hit |")
        lines.append("| --- | --- | --- | --- | --- |")
        for detail in framework.get("event_alignment", {}).get("strategic", []):
            lines.append(
                f"| {detail.get('date')} | {detail.get('name')} | {detail.get('expected')} | "
                f"{detail.get('detected')} | {detail.get('hit')} |"
            )
        lines.append("")

    enhanced = report.get("enhanced")
    if enhanced:
        lines.append("## Enhanced Validation")
        lines.append("")
        lines.append(
            f"- tau: {enhanced.get('tau')}\n"
            f"- k: {enhanced.get('k')}\n"
            f"- tactical_hit_rate: {enhanced.get('tactical_hit_rate'):.1%}\n"
            f"- strategic_hit_rate: {enhanced.get('strategic_hit_rate'):.1%}"
        )
        lines.append("")

    return "\n".join(lines)


def write_report(report: Mapping[str, Any], json_path: Path, md_path: Optional[Path] = None) -> None:
    """Write report outputs to disk.

    Args:
        report: Structured report dictionary.
        json_path: Path to JSON output.
        md_path: Optional path to Markdown output.
    """
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=True), encoding="utf-8")
    if md_path:
        md_path.write_text(render_markdown(report), encoding="utf-8")


def build_base_report() -> Dict[str, Any]:
    """Create the base report payload with a timestamp."""
    return {"generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z"}
