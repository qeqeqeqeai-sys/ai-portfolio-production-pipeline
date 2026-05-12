import hashlib
import json
import math
import os
import re
import time
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple

from graph_supabase_client import SupabaseRestClient


PIPELINE_NAME = "PHASE_3A1_EVIDENCE_DENSITY_EXPANSION"

THEME_NAME = os.getenv("THEME_NAME", "ai").strip().lower()
THEME_VERSION = os.getenv("THEME_VERSION", "v1").strip().lower()
MAX_ROWS_PER_SOURCE = int(os.getenv("MAX_ROWS_PER_SOURCE", "1000"))
MIN_SCORE_THRESHOLD = float(os.getenv("MIN_SCORE_THRESHOLD", "0"))

SOURCE_TABLES = [
    "structural_theme_explanations",
    "ai_transmission_scores",
    "structural_theme_scores",
    "ai_transmission_observations",
    "ai_transmission_backtest_results",
]

GENERIC_MACRO_FACTORS = {
    "interest_rates": ["interest rate", "rates", "yield", "treasury", "fed", "fomc", "us10y"],
    "inflation": ["inflation", "cpi", "ppi", "price pressure"],
    "liquidity": ["liquidity", "money supply", "m2", "qe", "qt"],
    "credit_stress": ["credit spread", "high yield", "default", "bbb spread"],
    "energy": ["oil", "brent", "wti", "natural gas", "energy"],
    "regulation": ["regulation", "regulatory", "antitrust", "policy", "compliance"],
    "geopolitics": ["geopolitical", "sanction", "tariff", "export control", "war"],
    "supply_chain": ["supply chain", "shortage", "inventory", "logistics"],
    "labor": ["labor", "employment", "wage", "unemployment", "jobless"],
}

COMPONENT_CATEGORY_MAP = {
    "valuation": "valuation",
    "momentum": "momentum",
    "sentiment": "sentiment",
    "quality": "quality",
    "growth": "growth",
    "risk": "risk",
    "macro": "macro",
    "evidence": "evidence",
    "transmission": "transmission",
    "reversal": "technical",
    "technical": "technical",
    "sharpe": "backtest_performance",
    "return": "backtest_performance",
    "cagr": "backtest_performance",
    "drawdown": "backtest_risk",
    "volatility": "backtest_risk",
    "hit_rate": "backtest_performance",
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_date_sgt() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d")


def slug(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text or "unknown"


def safe_float(value: Any, default: Optional[float] = 0.0) -> Optional[float]:
    try:
        if value is None:
            return default
        number = float(value)
        if math.isnan(number) or math.isinf(number):
            return default
        return number
    except Exception:
        return default


def score_0_100(value: Any, default: float = 50.0) -> float:
    number = safe_float(value, default)
    if number is None:
        number = default

    # Most strategy metrics like CAGR, returns, drawdown may be ratios.
    # Normal score fields may be 0-1 or 0-100.
    if -1 <= number <= 1:
        number *= 100

    return max(0.0, min(100.0, number))


def evidence_hash(row: Dict[str, Any]) -> str:
    key = "|".join([
        str(row.get("run_date_sgt")),
        str(row.get("theme_name")),
        str(row.get("theme_version")),
        str(row.get("ticker")),
        str(row.get("evidence_type")),
        str(row.get("driver_category")),
        str(row.get("evidence_title")),
        str(row.get("evidence_text")),
    ])
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def compact_text(value: Any, max_len: int = 2000) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        text = json.dumps(value, ensure_ascii=False)
    else:
        text = str(value)
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return None
    return text[:max_len]


def json_safe(value: Any) -> Any:
    try:
        json.dumps(value)
        return value
    except Exception:
        return str(value)


def infer_direction(score: Any, neutral_low: float = 45.0, neutral_high: float = 55.0) -> str:
    s = score_0_100(score, 50)
    if s > neutral_high:
        return "positive"
    if s < neutral_low:
        return "negative"
    return "neutral"


def normalize_direction(value: Any, fallback_score: Any = None) -> str:
    direction = slug(value)

    if direction in {"positive", "negative", "neutral", "mixed"}:
        return direction

    if direction in {"bullish", "benefit", "benefits", "up", "strong"}:
        return "positive"

    if direction in {"bearish", "harm", "harms", "down", "weak", "risk"}:
        return "negative"

    return infer_direction(fallback_score)


def first_present(row: Dict[str, Any], fields: Iterable[str]) -> Any:
    for field in fields:
        if field in row and row.get(field) not in (None, ""):
            return row.get(field)
    return None


def row_blob(row: Dict[str, Any]) -> str:
    values = []

    for _, value in row.items():
        if value is None:
            continue
        if isinstance(value, (dict, list)):
            try:
                values.append(json.dumps(value))
            except Exception:
                values.append(str(value))
        else:
            values.append(str(value))

    return " ".join(values).lower()


def extract_macro_categories(row: Dict[str, Any]) -> List[str]:
    blob = row_blob(row)
    categories = []

    for category, keywords in GENERIC_MACRO_FACTORS.items():
        if any(keyword in blob for keyword in keywords):
            categories.append(category)

    return sorted(set(categories))


def component_category(component_name: str) -> str:
    name = slug(component_name)
    for keyword, category in COMPONENT_CATEGORY_MAP.items():
        if keyword in name:
            return category
    return "component"


def base_identity(row: Dict[str, Any]) -> Dict[str, Any]:
    run_date = first_present(row, ["run_date_sgt", "backtest_run_date_sgt", "date", "created_at"]) or run_date_sgt()

    if isinstance(run_date, str) and "T" in run_date:
        run_date = run_date[:10]

    return {
        "theme_name": slug(first_present(row, ["theme_name", "theme"]) or THEME_NAME),
        "theme_version": str(first_present(row, ["theme_version"]) or THEME_VERSION),
        "ticker": str(first_present(row, ["ticker", "symbol", "asset"]) or "PORTFOLIO").upper(),
        "company": first_present(row, ["company", "company_name", "name", "strategy_name"]),
        "sector": first_present(row, ["sector"]),
        "subsector": first_present(row, ["subsector", "industry"]),
        "run_date_sgt": str(run_date),
    }


def make_evidence_row(
    *,
    identity: Dict[str, Any],
    evidence_type: str,
    source_name: str,
    evidence_title: Optional[str],
    evidence_text: Optional[str],
    relevance_score: Any,
    confidence_score: Any,
    driver_direction: Optional[str],
    driver_category: Optional[str],
    extracted_features: Optional[Dict[str, Any]],
    raw_payload: Optional[Dict[str, Any]],
    source_url: Optional[str] = None,
) -> Dict[str, Any]:
    row = {
        "run_date_sgt": identity["run_date_sgt"],
        "theme_name": identity["theme_name"],
        "theme_version": identity["theme_version"],
        "ticker": identity["ticker"],
        "company": identity.get("company"),
        "sector": identity.get("sector"),
        "subsector": identity.get("subsector"),
        "evidence_type": evidence_type,
        "source_name": source_name,
        "source_url": source_url,
        "evidence_title": compact_text(evidence_title, 500),
        "evidence_text": compact_text(evidence_text, 3000),
        "sentiment_score": score_0_100(relevance_score, 50),
        "relevance_score": score_0_100(relevance_score, 50),
        "confidence_score": score_0_100(confidence_score, 50),
        "driver_direction": normalize_direction(driver_direction, relevance_score),
        "driver_category": driver_category or "derived_signal",
        "extracted_features": extracted_features or {},
        "raw_payload": raw_payload or {},
    }

    row["evidence_hash"] = evidence_hash(row)
    return row


def evidence_from_structural_explanations(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    output = []

    for row in rows:
        identity = base_identity(row)
        final_score = first_present(row, ["final_score"])
        confidence = first_present(row, ["confidence_score"])

        output.append(make_evidence_row(
            identity=identity,
            evidence_type="explanation_summary",
            source_name="structural_theme_explanations",
            evidence_title=f"{identity['theme_name']} explanation summary for {identity['ticker']}",
            evidence_text=first_present(row, ["evidence_summary"]),
            relevance_score=final_score,
            confidence_score=confidence,
            driver_direction=infer_direction(final_score),
            driver_category="explainability_summary",
            extracted_features={
                "evidence_count": row.get("evidence_count"),
                "relationship_count": row.get("relationship_count"),
                "final_score": row.get("final_score"),
            },
            raw_payload=row,
        ))

        for driver_field, direction in [("top_positive_drivers", "positive"), ("top_negative_drivers", "negative")]:
            drivers = row.get(driver_field)

            if isinstance(drivers, str):
                try:
                    drivers = json.loads(drivers)
                except Exception:
                    drivers = [drivers]

            if isinstance(drivers, dict):
                drivers = list(drivers.values())

            if not isinstance(drivers, list):
                continue

            for idx, driver in enumerate(drivers):
                driver_text = compact_text(driver, 1500)
                if not driver_text:
                    continue

                output.append(make_evidence_row(
                    identity=identity,
                    evidence_type="explainability_driver",
                    source_name="structural_theme_explanations",
                    evidence_title=f"{direction.title()} driver {idx + 1} for {identity['ticker']}",
                    evidence_text=driver_text,
                    relevance_score=final_score,
                    confidence_score=confidence,
                    driver_direction=direction,
                    driver_category="driver_attribution",
                    extracted_features={
                        "driver_rank": idx + 1,
                        "driver_source_field": driver_field,
                    },
                    raw_payload={"parent_row": row.get("id"), "driver": json_safe(driver)},
                ))

        components = row.get("component_decomposition")
        if isinstance(components, str):
            try:
                components = json.loads(components)
            except Exception:
                components = None

        if isinstance(components, dict):
            for component, value in components.items():
                score = value.get("score") if isinstance(value, dict) else value
                output.append(make_evidence_row(
                    identity=identity,
                    evidence_type="component_decomposition",
                    source_name="structural_theme_explanations",
                    evidence_title=f"{component} component for {identity['ticker']}",
                    evidence_text=f"{component} component value: {compact_text(value, 1000)}",
                    relevance_score=score,
                    confidence_score=confidence,
                    driver_direction=infer_direction(score),
                    driver_category=component_category(component),
                    extracted_features={
                        "component_name": component,
                        "component_value": json_safe(value),
                    },
                    raw_payload={"parent_row": row.get("id"), "component": component, "value": json_safe(value)},
                ))

        pathways = row.get("transmission_pathways")
        if isinstance(pathways, str):
            try:
                pathways = json.loads(pathways)
            except Exception:
                pathways = None

        if isinstance(pathways, dict):
            pathways = list(pathways.values())

        if isinstance(pathways, list):
            for idx, pathway in enumerate(pathways):
                pathway_text = compact_text(pathway, 1500)
                if not pathway_text:
                    continue

                output.append(make_evidence_row(
                    identity=identity,
                    evidence_type="transmission_pathway",
                    source_name="structural_theme_explanations",
                    evidence_title=f"Transmission pathway {idx + 1} for {identity['ticker']}",
                    evidence_text=pathway_text,
                    relevance_score=final_score,
                    confidence_score=confidence,
                    driver_direction=infer_direction(final_score),
                    driver_category="transmission_pathway",
                    extracted_features={
                        "pathway_rank": idx + 1,
                    },
                    raw_payload={"parent_row": row.get("id"), "pathway": json_safe(pathway)},
                ))

    return output


def evidence_from_score_table(rows: List[Dict[str, Any]], source_name: str) -> List[Dict[str, Any]]:
    output = []

    score_fields = [
        "final_score",
        "theme_score",
        "structural_theme_score",
        "transmission_score",
        "ai_transmission_score",
        "overall_score",
        "composite_score",
        "momentum_score",
        "valuation_score",
        "quality_score",
        "sentiment_score",
        "risk_score",
        "confidence_score",
    ]

    for row in rows:
        identity = base_identity(row)
        confidence = first_present(row, ["confidence_score"]) or 60

        for field in score_fields:
            if field not in row or row.get(field) is None:
                continue

            score = row.get(field)

            if score_0_100(score, 0) < MIN_SCORE_THRESHOLD:
                continue

            output.append(make_evidence_row(
                identity=identity,
                evidence_type="score_component",
                source_name=source_name,
                evidence_title=f"{field} evidence for {identity['ticker']}",
                evidence_text=f"{identity['ticker']} has {field}={score}. This is converted into dense structural evidence for graph expansion.",
                relevance_score=score,
                confidence_score=confidence,
                driver_direction=infer_direction(score),
                driver_category=component_category(field),
                extracted_features={
                    "score_field": field,
                    "score_value": score,
                    "source_table": source_name,
                },
                raw_payload=row,
            ))

        for macro_category in extract_macro_categories(row):
            output.append(make_evidence_row(
                identity=identity,
                evidence_type="macro_linkage",
                source_name=source_name,
                evidence_title=f"{macro_category} linkage for {identity['ticker']}",
                evidence_text=f"{identity['ticker']} record contains structural linkage to {macro_category}.",
                relevance_score=65,
                confidence_score=confidence,
                driver_direction="neutral",
                driver_category=macro_category,
                extracted_features={
                    "macro_category": macro_category,
                    "source_table": source_name,
                },
                raw_payload=row,
            ))

    return output


def evidence_from_backtest_results(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    output = []

    for row in rows:
        identity = base_identity(row)
        identity["ticker"] = "PORTFOLIO"
        identity["company"] = row.get("strategy_name")

        sharpe = safe_float(row.get("sharpe_ratio"), 0.0) or 0.0
        cagr = safe_float(row.get("cagr"), 0.0) or 0.0
        total_return = safe_float(row.get("total_return"), 0.0) or 0.0
        max_drawdown = safe_float(row.get("max_drawdown"), 0.0) or 0.0
        hit_rate = safe_float(row.get("hit_rate"), 0.0) or 0.0
        observations = safe_float(row.get("observations"), 0.0) or 0.0

        # Convert backtest quality into a rough 0-100 evidence score.
        # This is intentionally simple and not a graph algorithm.
        perf_score = 50.0
        perf_score += min(25.0, max(-25.0, sharpe * 15.0))
        perf_score += min(15.0, max(-15.0, cagr * 100.0))
        perf_score += min(10.0, max(-10.0, total_return * 25.0))
        perf_score -= min(20.0, abs(max_drawdown) * 100.0 if max_drawdown < 0 else max_drawdown)
        perf_score += min(10.0, max(0.0, (hit_rate - 0.5) * 50.0))
        perf_score = max(0.0, min(100.0, perf_score))

        confidence = max(35.0, min(90.0, 35.0 + observations / 5.0))

        evidence_text = (
            f"Backtest strategy={row.get('strategy_name')}; "
            f"frequency={row.get('rebalance_frequency')}; "
            f"period={row.get('start_date')} to {row.get('end_date')}; "
            f"long_bucket={row.get('long_bucket')}; short_bucket={row.get('short_bucket')}; "
            f"total_return={row.get('total_return')}; cagr={row.get('cagr')}; "
            f"volatility={row.get('volatility')}; sharpe={row.get('sharpe_ratio')}; "
            f"max_drawdown={row.get('max_drawdown')}; hit_rate={row.get('hit_rate')}; "
            f"observations={row.get('observations')}; notes={row.get('notes')}"
        )

        output.append(make_evidence_row(
            identity=identity,
            evidence_type="backtest_result",
            source_name="ai_transmission_backtest_results",
            evidence_title=f"Backtest evidence for {row.get('strategy_name')}",
            evidence_text=evidence_text,
            relevance_score=perf_score,
            confidence_score=confidence,
            driver_direction=infer_direction(perf_score),
            driver_category="backtest_performance",
            extracted_features={
                "strategy_name": row.get("strategy_name"),
                "rebalance_frequency": row.get("rebalance_frequency"),
                "start_date": row.get("start_date"),
                "end_date": row.get("end_date"),
                "long_bucket": row.get("long_bucket"),
                "short_bucket": row.get("short_bucket"),
                "total_return": row.get("total_return"),
                "cagr": row.get("cagr"),
                "volatility": row.get("volatility"),
                "sharpe_ratio": row.get("sharpe_ratio"),
                "max_drawdown": row.get("max_drawdown"),
                "hit_rate": row.get("hit_rate"),
                "observations": row.get("observations"),
                "derived_performance_score": perf_score,
            },
            raw_payload=row,
        ))

    return output


def validate_evidence(rows: List[Dict[str, Any]]) -> Tuple[str, List[str], List[str]]:
    errors = []
    warnings = []

    if not rows:
        warnings.append("No evidence rows generated.")

    for row in rows:
        required = [
            "run_date_sgt",
            "theme_name",
            "theme_version",
            "ticker",
            "evidence_hash",
        ]

        for field in required:
            if not row.get(field):
                errors.append(f"Missing {field}: {row}")

        for metric in ["sentiment_score", "relevance_score", "confidence_score"]:
            value = safe_float(row.get(metric), None)
            if value is None or value < 0 or value > 100:
                errors.append(f"{metric} out of range: {value}")

        direction = row.get("driver_direction")
        if direction not in {"positive", "negative", "neutral", "mixed"}:
            errors.append(f"Invalid driver_direction: {direction}")

    if errors:
        return "failed", errors, warnings

    if warnings:
        return "warning", errors, warnings

    return "passed", errors, warnings


def fetch_source_rows(client: SupabaseRestClient, table: str) -> List[Dict[str, Any]]:
    filters = {}

    if table in {"structural_theme_explanations", "structural_theme_scores"}:
        filters["theme_name"] = f"eq.{THEME_NAME}"

    order_column_map = {
        "ai_transmission_backtest_results": "backtest_run_date_sgt.desc",
    }

    order_column = order_column_map.get(table, "run_date_sgt.desc")

    return client.select(
        table,
        columns="*",
        filters=filters,
        order=order_column,
        limit=MAX_ROWS_PER_SOURCE,
    )


def write_run(
    client: SupabaseRestClient,
    *,
    status: str,
    source_rows_read: int,
    evidence_rows_generated: int,
    evidence_rows_inserted: int,
    skipped_rows: int,
    validation_status: Optional[str],
    validation_errors: List[str],
    validation_warnings: List[str],
    runtime_seconds: float,
    error_message: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
):
    client.insert("structural_theme_evidence_density_runs", [{
        "theme_name": THEME_NAME,
        "status": status,
        "source_rows_read": source_rows_read,
        "evidence_rows_generated": evidence_rows_generated,
        "evidence_rows_inserted": evidence_rows_inserted,
        "skipped_rows": skipped_rows,
        "validation_status": validation_status,
        "validation_error_count": len(validation_errors),
        "validation_warning_count": len(validation_warnings),
        "runtime_seconds": round(runtime_seconds, 3),
        "github_run_id": os.getenv("GITHUB_RUN_ID"),
        "github_workflow": os.getenv("GITHUB_WORKFLOW"),
        "github_repository": os.getenv("GITHUB_REPOSITORY"),
        "github_branch": os.getenv("GITHUB_REF_NAME"),
        "error_message": error_message,
        "metadata": metadata or {},
    }])


def main():
    start = time.time()
    client = SupabaseRestClient()

    all_evidence: List[Dict[str, Any]] = []
    source_counts: Dict[str, Any] = {}
    generated_counts: Dict[str, int] = {}
    total_source_rows = 0

    try:
        for table in SOURCE_TABLES:
            try:
                rows = fetch_source_rows(client, table)
                source_counts[table] = len(rows)
                total_source_rows += len(rows)

                if table == "structural_theme_explanations":
                    evidence = evidence_from_structural_explanations(rows)
                elif table == "ai_transmission_backtest_results":
                    evidence = evidence_from_backtest_results(rows)
                else:
                    evidence = evidence_from_score_table(rows, table)

                generated_counts[table] = len(evidence)
                all_evidence.extend(evidence)

                print(f"{table}: rows={len(rows)}, evidence_generated={len(evidence)}")

            except Exception as exc:
                source_counts[table] = f"skipped: {exc}"
                generated_counts[table] = 0
                print(f"WARNING: skipped {table}: {exc}")

        unique_by_hash = {}
        for row in all_evidence:
            unique_by_hash[row["evidence_hash"]] = row

        deduped = list(unique_by_hash.values())

        validation_status, validation_errors, validation_warnings = validate_evidence(deduped)

        if validation_status == "failed":
            raise RuntimeError("Evidence density validation failed: " + " | ".join(validation_errors[:10]))

        inserted_count = 0

        if deduped:
            client.upsert(
                "structural_theme_evidence",
                deduped,
                on_conflict="run_date_sgt,theme_name,theme_version,ticker,evidence_hash",
                return_rows=False,
            )
            inserted_count = len(deduped)

        status = "success" if validation_status == "passed" else "warning"

        write_run(
            client,
            status=status,
            source_rows_read=total_source_rows,
            evidence_rows_generated=len(all_evidence),
            evidence_rows_inserted=inserted_count,
            skipped_rows=max(0, len(all_evidence) - len(deduped)),
            validation_status=validation_status,
            validation_errors=validation_errors,
            validation_warnings=validation_warnings,
            runtime_seconds=time.time() - start,
            metadata={
                "source_counts": source_counts,
                "generated_counts": generated_counts,
                "unique_evidence_rows": len(deduped),
                "source_tables": SOURCE_TABLES,
            },
        )

        print("Phase 3A.1 Evidence Density Expansion completed.")
        print(f"Source rows read: {total_source_rows}")
        print(f"Evidence generated: {len(all_evidence)}")
        print(f"Evidence upserted: {inserted_count}")
        print(f"Validation: {validation_status}")

    except Exception as exc:
        write_run(
            client,
            status="failed",
            source_rows_read=total_source_rows,
            evidence_rows_generated=len(all_evidence),
            evidence_rows_inserted=0,
            skipped_rows=0,
            validation_status="failed",
            validation_errors=[str(exc)],
            validation_warnings=[],
            runtime_seconds=time.time() - start,
            error_message=str(exc),
            metadata={
                "source_counts": source_counts,
                "generated_counts": generated_counts,
                "source_tables": SOURCE_TABLES,
            },
        )
        raise


if __name__ == "__main__":
    main()
