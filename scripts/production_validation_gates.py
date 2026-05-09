"""
production_validation_gates.py

Institutional-style validation gates for AI portfolio production pipeline.

This module separates:
- validation logic
- orchestration logic
- reporting logic

It intentionally raises no exceptions during normal validation.
Instead, it returns structured ValidationResult objects.
"""

import json
import math
import os
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, date
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import requests

from production_validation_config import get_config


try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo


class Severity(str, Enum):
    WARNING = "WARNING"
    ERROR = "ERROR"
    HARD_FAIL = "HARD_FAIL"


@dataclass
class ValidationResult:
    check_name: str
    severity: Severity
    passed: bool
    message: str
    details: Dict[str, Any]


@dataclass
class ValidationSummary:
    status: str
    generated_at_sgt: str
    warning_count: int
    error_count: int
    hard_fail_count: int
    should_fail_pipeline: bool
    results: List[ValidationResult]


def now_sgt() -> datetime:
    return datetime.now(ZoneInfo("Asia/Singapore"))


def today_sgt() -> date:
    return now_sgt().date()


def safe_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    try:
        if value is None:
            return default
        if isinstance(value, float) and math.isnan(value):
            return default
        return float(value)
    except Exception:
        return default


def add_result(
    results: List[ValidationResult],
    check_name: str,
    severity: Severity,
    passed: bool,
    message: str,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    results.append(
        ValidationResult(
            check_name=check_name,
            severity=severity,
            passed=passed,
            message=message,
            details=details or {},
        )
    )


def read_csv_if_exists(path: str) -> Optional[pd.DataFrame]:
    if not Path(path).exists():
        return None
    try:
        return pd.read_csv(path)
    except Exception:
        return None


def detect_column(df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
    cols = set(df.columns)
    for col in candidates:
        if col in cols:
            return col
    return None


# ---------------------------------------------------------------------
# Environment validations
# ---------------------------------------------------------------------

def validate_environment(results: List[ValidationResult]) -> None:
    required_env_vars = [
        "SUPABASE_URL",
        "SUPABASE_SERVICE_ROLE_KEY",
    ]

    optional_but_recommended_env_vars = [
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_CHAT_ID",
        "GITHUB_RUN_ID",
        "GITHUB_WORKFLOW",
        "GITHUB_SHA",
    ]

    missing_required = [v for v in required_env_vars if not os.getenv(v)]
    missing_optional = [v for v in optional_but_recommended_env_vars if not os.getenv(v)]

    add_result(
        results,
        "environment_required_variables",
        Severity.HARD_FAIL,
        passed=len(missing_required) == 0,
        message=(
            "All required environment variables exist."
            if not missing_required
            else f"Missing required environment variables: {missing_required}"
        ),
        details={"missing_required": missing_required},
    )

    add_result(
        results,
        "environment_optional_variables",
        Severity.WARNING,
        passed=len(missing_optional) == 0,
        message=(
            "All recommended environment variables exist."
            if not missing_optional
            else f"Missing recommended environment variables: {missing_optional}"
        ),
        details={"missing_optional": missing_optional},
    )


def validate_outputs_folder(results: List[ValidationResult], outputs_dir: str) -> None:
    path = Path(outputs_dir)

    add_result(
        results,
        "outputs_folder_exists",
        Severity.HARD_FAIL,
        passed=path.exists() and path.is_dir(),
        message=(
            f"Outputs folder exists: {outputs_dir}"
            if path.exists() and path.is_dir()
            else f"Missing outputs folder: {outputs_dir}"
        ),
        details={"outputs_dir": outputs_dir},
    )


# ---------------------------------------------------------------------
# Signal validations
# ---------------------------------------------------------------------

def validate_signal_engine(results: List[ValidationResult], signal_csv: str) -> None:
    cfg = get_config()
    df = read_csv_if_exists(signal_csv)

    add_result(
        results,
        "signal_file_exists",
        Severity.HARD_FAIL,
        passed=df is not None,
        message=(
            f"Signal output file found: {signal_csv}"
            if df is not None
            else f"Signal output file missing or unreadable: {signal_csv}"
        ),
        details={"path": signal_csv},
    )

    if df is None:
        return

    row_count = len(df)

    if row_count < cfg.min_signal_rows_hard_fail:
        severity = Severity.HARD_FAIL
        passed = False
    elif row_count < cfg.min_signal_rows_error:
        severity = Severity.ERROR
        passed = False
    elif row_count < cfg.min_signal_rows_warning:
        severity = Severity.WARNING
        passed = False
    else:
        severity = Severity.WARNING
        passed = True

    add_result(
        results,
        "signal_minimum_row_count",
        severity,
        passed,
        f"Signal row count = {row_count}",
        {
            "row_count": row_count,
            "expected_universe_size": cfg.expected_universe_size,
            "warning_threshold": cfg.min_signal_rows_warning,
            "error_threshold": cfg.min_signal_rows_error,
            "hard_fail_threshold": cfg.min_signal_rows_hard_fail,
        },
    )

    ticker_col = detect_column(df, ["ticker", "symbol"])
    alpha_col = detect_column(
        df,
        [
            "alpha_score_v7",
            "alpha_score",
            "composite_score",
            "overall_score",
            "overall_ai_risk_score",
        ],
    )
    subsector_col = detect_column(df, ["ai_subsector", "subsector", "sector"])
    run_date_col = detect_column(df, ["run_date_sgt", "run_date", "date"])

    add_result(
        results,
        "signal_required_columns",
        Severity.HARD_FAIL,
        passed=bool(ticker_col and alpha_col),
        message=(
            "Required signal columns found."
            if ticker_col and alpha_col
            else "Missing required signal columns. Need ticker and alpha/composite score column."
        ),
        details={
            "ticker_col": ticker_col,
            "alpha_col": alpha_col,
            "subsector_col": subsector_col,
            "run_date_col": run_date_col,
            "columns": list(df.columns),
        },
    )

    if not ticker_col or not alpha_col:
        return

    duplicate_count = int(df[ticker_col].duplicated().sum())

    add_result(
        results,
        "signal_duplicate_tickers",
        Severity.HARD_FAIL,
        passed=duplicate_count == 0,
        message=(
            "No duplicate signal tickers detected."
            if duplicate_count == 0
            else f"Duplicate signal tickers detected: {duplicate_count}"
        ),
        details={"duplicate_count": duplicate_count},
    )

    null_alpha_pct = float(df[alpha_col].isna().mean())

    if null_alpha_pct >= cfg.max_null_alpha_score_pct_hard_fail:
        severity = Severity.HARD_FAIL
        passed = False
    elif null_alpha_pct >= cfg.max_null_alpha_score_pct_error:
        severity = Severity.ERROR
        passed = False
    elif null_alpha_pct >= cfg.max_null_alpha_score_pct_warning:
        severity = Severity.WARNING
        passed = False
    else:
        severity = Severity.WARNING
        passed = True

    add_result(
        results,
        "signal_null_alpha_score_coverage",
        severity,
        passed,
        f"Null alpha score percentage = {null_alpha_pct:.2%}",
        {
            "null_alpha_pct": null_alpha_pct,
            "warning_threshold": cfg.max_null_alpha_score_pct_warning,
            "error_threshold": cfg.max_null_alpha_score_pct_error,
            "hard_fail_threshold": cfg.max_null_alpha_score_pct_hard_fail,
        },
    )

    total_cells = max(df.shape[0] * df.shape[1], 1)
    nan_cell_pct = float(df.isna().sum().sum() / total_cells)

    if nan_cell_pct >= cfg.max_nan_cell_pct_hard_fail:
        severity = Severity.HARD_FAIL
        passed = False
    elif nan_cell_pct >= cfg.max_nan_cell_pct_error:
        severity = Severity.ERROR
        passed = False
    elif nan_cell_pct >= cfg.max_nan_cell_pct_warning:
        severity = Severity.WARNING
        passed = False
    else:
        severity = Severity.WARNING
        passed = True

    add_result(
        results,
        "signal_excessive_nan_coverage",
        severity,
        passed,
        f"NaN cell percentage = {nan_cell_pct:.2%}",
        {"nan_cell_pct": nan_cell_pct},
    )

    alpha_series = pd.to_numeric(df[alpha_col], errors="coerce").dropna()

    if len(alpha_series) > 0:
        alpha_std = float(alpha_series.std())

        if alpha_std < cfg.min_alpha_score_std_error:
            severity = Severity.ERROR
            passed = False
        elif alpha_std < cfg.min_alpha_score_std_warning:
            severity = Severity.WARNING
            passed = False
        else:
            severity = Severity.WARNING
            passed = True

        add_result(
            results,
            "signal_alpha_score_distribution_std",
            severity,
            passed,
            f"Alpha score standard deviation = {alpha_std:.6f}",
            {
                "alpha_std": alpha_std,
                "warning_min_std": cfg.min_alpha_score_std_warning,
                "error_min_std": cfg.min_alpha_score_std_error,
            },
        )

        abs_alpha_sum = float(alpha_series.abs().sum())

        if abs_alpha_sum > 0:
            max_single_alpha_concentration = float(alpha_series.abs().max() / abs_alpha_sum)
        else:
            max_single_alpha_concentration = 1.0

        if max_single_alpha_concentration >= cfg.max_single_alpha_concentration_error:
            severity = Severity.ERROR
            passed = False
        elif max_single_alpha_concentration >= cfg.max_single_alpha_concentration_warning:
            severity = Severity.WARNING
            passed = False
        else:
            severity = Severity.WARNING
            passed = True

        add_result(
            results,
            "signal_extreme_alpha_concentration",
            severity,
            passed,
            f"Max single-name alpha concentration = {max_single_alpha_concentration:.2%}",
            {
                "max_single_alpha_concentration": max_single_alpha_concentration,
                "warning_threshold": cfg.max_single_alpha_concentration_warning,
                "error_threshold": cfg.max_single_alpha_concentration_error,
            },
        )

    if subsector_col:
        missing_subsector_pct = float(df[subsector_col].isna().mean())

        add_result(
            results,
            "signal_missing_subsectors",
            Severity.ERROR if missing_subsector_pct > 0.10 else Severity.WARNING,
            passed=missing_subsector_pct <= 0.10,
            message=f"Missing subsector percentage = {missing_subsector_pct:.2%}",
            details={"missing_subsector_pct": missing_subsector_pct},
        )
    else:
        add_result(
            results,
            "signal_subsector_column_exists",
            Severity.ERROR,
            passed=False,
            message="No subsector column found in signal output.",
            details={},
        )

    if run_date_col:
        parsed_dates = pd.to_datetime(df[run_date_col], errors="coerce").dt.date.dropna()

        if len(parsed_dates) == 0:
            add_result(
                results,
                "signal_run_date_parseable",
                Severity.ERROR,
                passed=False,
                message="Signal run_date exists but cannot be parsed.",
                details={"run_date_col": run_date_col},
            )
        else:
            latest_run_date = max(parsed_dates)
            lag_days = (today_sgt() - latest_run_date).days

            if lag_days >= cfg.max_signal_run_date_lag_days_hard_fail:
                severity = Severity.HARD_FAIL
                passed = False
            elif lag_days >= cfg.max_signal_run_date_lag_days_error:
                severity = Severity.ERROR
                passed = False
            elif lag_days >= cfg.max_signal_run_date_lag_days_warning:
                severity = Severity.WARNING
                passed = False
            else:
                severity = Severity.WARNING
                passed = True

            add_result(
                results,
                "signal_stale_run_date",
                severity,
                passed,
                f"Latest signal run_date = {latest_run_date}, lag_days = {lag_days}",
                {
                    "latest_run_date": str(latest_run_date),
                    "lag_days": lag_days,
                },
            )
    else:
        add_result(
            results,
            "signal_run_date_column_exists",
            Severity.ERROR,
            passed=False,
            message="No run_date column found in signal output.",
            details={},
        )


# ---------------------------------------------------------------------
# Portfolio validations
# ---------------------------------------------------------------------

def validate_portfolio_engine(results: List[ValidationResult], portfolio_csv: str) -> None:
    cfg = get_config()
    df = read_csv_if_exists(portfolio_csv)

    add_result(
        results,
        "portfolio_file_exists",
        Severity.HARD_FAIL,
        passed=df is not None,
        message=(
            f"Portfolio output file found: {portfolio_csv}"
            if df is not None
            else f"Portfolio output file missing or unreadable: {portfolio_csv}"
        ),
        details={"path": portfolio_csv},
    )

    if df is None:
        return

    row_count = len(df)

    add_result(
        results,
        "portfolio_not_empty",
        Severity.HARD_FAIL,
        passed=row_count >= cfg.min_portfolio_rows_hard_fail,
        message=f"Portfolio row count = {row_count}",
        details={"row_count": row_count},
    )

    add_result(
        results,
        "portfolio_row_count_limit",
        Severity.ERROR,
        passed=row_count <= cfg.max_portfolio_rows_error,
        message=f"Portfolio row count = {row_count}",
        details={"row_count": row_count, "max_portfolio_rows_error": cfg.max_portfolio_rows_error},
    )

    ticker_col = detect_column(df, ["ticker", "symbol"])
    weight_col = detect_column(df, ["weight", "portfolio_weight", "target_weight"])
    subsector_col = detect_column(df, ["ai_subsector", "subsector", "sector"])

    add_result(
        results,
        "portfolio_required_columns",
        Severity.HARD_FAIL,
        passed=bool(ticker_col and weight_col),
        message=(
            "Required portfolio columns found."
            if ticker_col and weight_col
            else "Missing required portfolio columns. Need ticker and weight columns."
        ),
        details={
            "ticker_col": ticker_col,
            "weight_col": weight_col,
            "subsector_col": subsector_col,
            "columns": list(df.columns),
        },
    )

    if not ticker_col or not weight_col:
        return

    df[weight_col] = pd.to_numeric(df[weight_col], errors="coerce")

    invalid_weights = df[weight_col].isna().sum()
    negative_weights = (df[weight_col] < 0).sum()
    above_one_weights = (df[weight_col] > 1).sum()

    add_result(
        results,
        "portfolio_invalid_weights",
        Severity.HARD_FAIL,
        passed=invalid_weights == 0 and negative_weights == 0 and above_one_weights == 0,
        message=(
            "All portfolio weights are valid."
            if invalid_weights == 0 and negative_weights == 0 and above_one_weights == 0
            else "Invalid portfolio weights detected."
        ),
        details={
            "invalid_weights": int(invalid_weights),
            "negative_weights": int(negative_weights),
            "above_one_weights": int(above_one_weights),
        },
    )

    duplicate_count = int(df[ticker_col].duplicated().sum())

    add_result(
        results,
        "portfolio_duplicate_holdings",
        Severity.HARD_FAIL,
        passed=duplicate_count == 0,
        message=(
            "No duplicate portfolio holdings detected."
            if duplicate_count == 0
            else f"Duplicate portfolio holdings detected: {duplicate_count}"
        ),
        details={"duplicate_count": duplicate_count},
    )

    total_weight = float(df[weight_col].sum())

    if total_weight < cfg.min_total_weight_hard_fail or total_weight > cfg.max_total_weight_hard_fail:
        severity = Severity.HARD_FAIL
        passed = False
    elif total_weight < cfg.min_total_weight_error or total_weight > cfg.max_total_weight_error:
        severity = Severity.ERROR
        passed = False
    else:
        severity = Severity.WARNING
        passed = True

    add_result(
        results,
        "portfolio_total_weight_close_to_one",
        severity,
        passed,
        f"Total portfolio weight = {total_weight:.6f}",
        {
            "total_weight": total_weight,
            "error_range": [cfg.min_total_weight_error, cfg.max_total_weight_error],
            "hard_fail_range": [cfg.min_total_weight_hard_fail, cfg.max_total_weight_hard_fail],
        },
    )

    cash_rows = df[df[ticker_col].astype(str).str.upper() == "CASH"]
    cash_weight = float(cash_rows[weight_col].sum()) if not cash_rows.empty else 0.0

    if cash_weight >= cfg.max_cash_weight_hard_fail:
        severity = Severity.HARD_FAIL
        passed = False
    elif cash_weight >= cfg.max_cash_weight_error:
        severity = Severity.ERROR
        passed = False
    elif cash_weight >= cfg.max_cash_weight_warning:
        severity = Severity.WARNING
        passed = False
    else:
        severity = Severity.WARNING
        passed = True

    add_result(
        results,
        "portfolio_cash_weight_threshold",
        severity,
        passed,
        f"Cash weight = {cash_weight:.2%}",
        {
            "cash_weight": cash_weight,
            "warning_threshold": cfg.max_cash_weight_warning,
            "error_threshold": cfg.max_cash_weight_error,
            "hard_fail_threshold": cfg.max_cash_weight_hard_fail,
        },
    )

    max_single_weight = float(df[weight_col].max())

    if max_single_weight >= cfg.max_single_holding_weight_hard_fail:
        severity = Severity.HARD_FAIL
        passed = False
    elif max_single_weight >= cfg.max_single_holding_weight_error:
        severity = Severity.ERROR
        passed = False
    elif max_single_weight >= cfg.max_single_holding_weight_warning:
        severity = Severity.WARNING
        passed = False
    else:
        severity = Severity.WARNING
        passed = True

    add_result(
        results,
        "portfolio_single_holding_concentration",
        severity,
        passed,
        f"Max single holding weight = {max_single_weight:.2%}",
        {
            "max_single_weight": max_single_weight,
            "warning_threshold": cfg.max_single_holding_weight_warning,
            "error_threshold": cfg.max_single_holding_weight_error,
            "hard_fail_threshold": cfg.max_single_holding_weight_hard_fail,
        },
    )

    if subsector_col:
        non_cash_df = df[df[ticker_col].astype(str).str.upper() != "CASH"].copy()
        missing_subsector_pct = float(non_cash_df[subsector_col].isna().mean()) if len(non_cash_df) else 0.0

        add_result(
            results,
            "portfolio_missing_subsectors",
            Severity.ERROR if missing_subsector_pct > 0.10 else Severity.WARNING,
            passed=missing_subsector_pct <= 0.10,
            message=f"Missing portfolio subsector percentage = {missing_subsector_pct:.2%}",
            details={"missing_subsector_pct": missing_subsector_pct},
        )

        if len(non_cash_df):
            subsector_weights = non_cash_df.groupby(subsector_col)[weight_col].sum().sort_values(ascending=False)
            max_subsector_weight = float(subsector_weights.iloc[0]) if len(subsector_weights) else 0.0
            top_subsector = str(subsector_weights.index[0]) if len(subsector_weights) else None

            if max_subsector_weight >= cfg.max_subsector_weight_hard_fail:
                severity = Severity.HARD_FAIL
                passed = False
            elif max_subsector_weight >= cfg.max_subsector_weight_error:
                severity = Severity.ERROR
                passed = False
            elif max_subsector_weight >= cfg.max_subsector_weight_warning:
                severity = Severity.WARNING
                passed = False
            else:
                severity = Severity.WARNING
                passed = True

            add_result(
                results,
                "portfolio_subsector_concentration",
                severity,
                passed,
                f"Top subsector weight = {max_subsector_weight:.2%}",
                {
                    "top_subsector": top_subsector,
                    "max_subsector_weight": max_subsector_weight,
                    "warning_threshold": cfg.max_subsector_weight_warning,
                    "error_threshold": cfg.max_subsector_weight_error,
                    "hard_fail_threshold": cfg.max_subsector_weight_hard_fail,
                },
            )
    else:
        add_result(
            results,
            "portfolio_subsector_column_exists",
            Severity.ERROR,
            passed=False,
            message="No subsector column found in portfolio output.",
            details={},
        )


# ---------------------------------------------------------------------
# Monitoring validations
# ---------------------------------------------------------------------

def validate_monitoring_outputs(results: List[ValidationResult]) -> None:
    cfg = get_config()

    for file_path in cfg.required_monitoring_files:
        exists = Path(file_path).exists()
        non_empty = exists and Path(file_path).stat().st_size > 0

        add_result(
            results,
            f"monitoring_file_exists::{Path(file_path).name}",
            Severity.ERROR,
            passed=exists and non_empty,
            message=(
                f"Monitoring artifact exists and is non-empty: {file_path}"
                if exists and non_empty
                else f"Missing or empty monitoring artifact: {file_path}"
            ),
            details={
                "file_path": file_path,
                "exists": exists,
                "size_bytes": Path(file_path).stat().st_size if exists else 0,
            },
        )

    outputs_dir = Path(cfg.outputs_dir)
    if outputs_dir.exists():
        csv_files = list(outputs_dir.glob("*.csv"))
        json_files = list(outputs_dir.glob("*.json"))
        png_files = list(outputs_dir.glob("*.png"))

        add_result(
            results,
            "monitoring_csv_generation_check",
            Severity.ERROR,
            passed=len(csv_files) >= 1,
            message=f"CSV artifact count = {len(csv_files)}",
            details={"csv_files": [str(p) for p in csv_files]},
        )

        add_result(
            results,
            "monitoring_json_generation_check",
            Severity.WARNING,
            passed=len(json_files) >= 1,
            message=f"JSON artifact count = {len(json_files)}",
            details={"json_files": [str(p) for p in json_files]},
        )

        add_result(
            results,
            "monitoring_chart_generation_check",
            Severity.WARNING,
            passed=True,
            message=f"PNG chart artifact count = {len(png_files)}",
            details={"png_files": [str(p) for p in png_files]},
        )


# ---------------------------------------------------------------------
# Operational validations
# ---------------------------------------------------------------------

def validate_runtime_duration(results: List[ValidationResult]) -> None:
    cfg = get_config()

    runtime_seconds = safe_float(os.getenv("PIPELINE_RUNTIME_SECONDS"))

    if runtime_seconds is None:
        add_result(
            results,
            "pipeline_runtime_duration_available",
            Severity.WARNING,
            passed=False,
            message="PIPELINE_RUNTIME_SECONDS not available.",
            details={},
        )
        return

    if runtime_seconds >= cfg.max_runtime_seconds_error:
        severity = Severity.ERROR
        passed = False
    elif runtime_seconds >= cfg.max_runtime_seconds_warning:
        severity = Severity.WARNING
        passed = False
    elif runtime_seconds <= cfg.min_runtime_seconds_warning:
        severity = Severity.WARNING
        passed = False
    else:
        severity = Severity.WARNING
        passed = True

    add_result(
        results,
        "pipeline_runtime_duration_anomaly",
        severity,
        passed,
        f"Pipeline runtime seconds = {runtime_seconds:.2f}",
        {
            "runtime_seconds": runtime_seconds,
            "min_runtime_warning": cfg.min_runtime_seconds_warning,
            "max_runtime_warning": cfg.max_runtime_seconds_warning,
            "max_runtime_error": cfg.max_runtime_seconds_error,
        },
    )


def validate_supabase_connectivity(results: List[ValidationResult]) -> None:
    """
    Lightweight Supabase REST connectivity check.

    This does not modify production data.
    """
    supabase_url = os.getenv("SUPABASE_URL")
    service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not supabase_url or not service_key:
        add_result(
            results,
            "supabase_connectivity",
            Severity.HARD_FAIL,
            passed=False,
            message="Cannot test Supabase connectivity because required env vars are missing.",
            details={},
        )
        return

    url = f"{supabase_url.rstrip('/')}/rest/v1/production_pipeline_runs?select=id&limit=1"
    headers = {
        "apikey": service_key,
        "Authorization": f"Bearer {service_key}",
    }

    try:
        response = requests.get(url, headers=headers, timeout=20)
        passed = response.status_code < 400

        add_result(
            results,
            "supabase_connectivity",
            Severity.ERROR,
            passed=passed,
            message=(
                "Supabase connectivity check passed."
                if passed
                else f"Supabase connectivity check failed: HTTP {response.status_code}"
            ),
            details={
                "status_code": response.status_code,
                "response_text_sample": response.text[:500],
            },
        )
    except Exception as exc:
        add_result(
            results,
            "supabase_connectivity",
            Severity.ERROR,
            passed=False,
            message=f"Supabase connectivity check raised exception: {exc}",
            details={"exception": str(exc)},
        )


# ---------------------------------------------------------------------
# Summary / orchestration
# ---------------------------------------------------------------------

def build_summary(results: List[ValidationResult]) -> ValidationSummary:
    cfg = get_config()

    failed_warnings = [r for r in results if not r.passed and r.severity == Severity.WARNING]
    failed_errors = [r for r in results if not r.passed and r.severity == Severity.ERROR]
    failed_hard = [r for r in results if not r.passed and r.severity == Severity.HARD_FAIL]

    should_fail = False

    if failed_hard:
        should_fail = True
    elif failed_errors and cfg.fail_on_error:
        should_fail = True
    elif failed_warnings and cfg.fail_on_warning:
        should_fail = True

    status = "FAILED" if should_fail else "PASSED"

    return ValidationSummary(
        status=status,
        generated_at_sgt=now_sgt().isoformat(),
        warning_count=len(failed_warnings),
        error_count=len(failed_errors),
        hard_fail_count=len(failed_hard),
        should_fail_pipeline=should_fail,
        results=results,
    )


def write_validation_report(summary: ValidationSummary, path: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)

    payload = asdict(summary)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, default=str)


def print_human_summary(summary: ValidationSummary) -> None:
    print("=" * 100)
    print("PRODUCTION VALIDATION GATE SUMMARY")
    print("=" * 100)
    print(f"Status: {summary.status}")
    print(f"Generated at SGT: {summary.generated_at_sgt}")
    print(f"Warnings failed: {summary.warning_count}")
    print(f"Errors failed: {summary.error_count}")
    print(f"Hard fails: {summary.hard_fail_count}")
    print("-" * 100)

    for r in summary.results:
        icon = "PASS" if r.passed else "FAIL"
        print(f"[{icon}] [{r.severity}] {r.check_name}: {r.message}")

    print("=" * 100)


def run_all_validations() -> ValidationSummary:
    cfg = get_config()
    results: List[ValidationResult] = []

    validate_environment(results)
    validate_outputs_folder(results, cfg.outputs_dir)
    validate_supabase_connectivity(results)

    validate_signal_engine(results, cfg.signal_output_csv)
    validate_portfolio_engine(results, cfg.portfolio_output_csv)
    validate_monitoring_outputs(results)

    validate_runtime_duration(results)

    summary = build_summary(results)
    write_validation_report(summary, cfg.validation_report_path)
    print_human_summary(summary)

    return summary