"""
production_validation_config.py
"""

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class ValidationConfig:
    singapore_timezone: str = "Asia/Singapore"

    outputs_dir: str = "outputs"

    validation_report_path: str = "outputs/validation_report.json"

    # ============================================================
    # CORRECT PRODUCTION FILES
    # ============================================================

    signal_output_csv_pattern: str = "outputs/ai_stock_signal_scores_v7_*.csv"

    portfolio_output_csv_pattern: str = "outputs/ai_portfolio_v7_holdings_*.csv"

    monitoring_summary_csv: str = "outputs/ai_portfolio_v7_summary_latest.csv"

    # ============================================================
    # SIGNAL VALIDATION
    # ============================================================

    expected_universe_size: int = 104

    min_signal_rows_warning: int = 90
    min_signal_rows_error: int = 80
    min_signal_rows_hard_fail: int = 60

    max_null_alpha_score_pct_warning: float = 0.05
    max_null_alpha_score_pct_error: float = 0.10
    max_null_alpha_score_pct_hard_fail: float = 0.25

    max_nan_cell_pct_warning: float = 0.10
    max_nan_cell_pct_error: float = 0.20
    max_nan_cell_pct_hard_fail: float = 0.35

    min_alpha_score_std_warning: float = 0.02
    min_alpha_score_std_error: float = 0.005

    max_single_alpha_concentration_warning: float = 0.20
    max_single_alpha_concentration_error: float = 0.35

    max_signal_run_date_lag_days_warning: int = 1
    max_signal_run_date_lag_days_error: int = 2
    max_signal_run_date_lag_days_hard_fail: int = 4

    # ============================================================
    # PORTFOLIO VALIDATION
    # ============================================================

    min_portfolio_rows_hard_fail: int = 1

    max_portfolio_rows_error: int = 30

    min_total_weight_error: float = 0.98
    max_total_weight_error: float = 1.02

    min_total_weight_hard_fail: float = 0.95
    max_total_weight_hard_fail: float = 1.05

    max_cash_weight_warning: float = 0.30
    max_cash_weight_error: float = 0.50
    max_cash_weight_hard_fail: float = 0.80

    max_single_holding_weight_warning: float = 0.20
    max_single_holding_weight_error: float = 0.30
    max_single_holding_weight_hard_fail: float = 0.50

    max_subsector_weight_warning: float = 0.40
    max_subsector_weight_error: float = 0.55
    max_subsector_weight_hard_fail: float = 0.70

    # ============================================================
    # MONITORING
    # ============================================================

    required_monitoring_files: List[str] = None

    # ============================================================
    # OPERATIONAL
    # ============================================================

    min_runtime_seconds_warning: float = 5.0

    max_runtime_seconds_warning: float = 1800.0

    max_runtime_seconds_error: float = 3600.0

    # ============================================================
    # FAILURE POLICY
    # ============================================================

    fail_on_warning: bool = False

    fail_on_error: bool = True


def get_config() -> ValidationConfig:
    cfg = ValidationConfig()

    object.__setattr__(
        cfg,
        "required_monitoring_files",
        [
            "outputs/ai_portfolio_v7_summary_latest.csv",
        ],
    )

    return cfg
