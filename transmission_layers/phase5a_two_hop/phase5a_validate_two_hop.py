# transmission_layers/phase5a_two_hop/phase5a_validate_two_hop.py

import os
import json
import requests
from datetime import datetime, timezone, timedelta


SUPABASE_URL = os.environ["SUPABASE_URL"].rstrip("/")
SUPABASE_KEY = (
    os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    or os.environ.get("SUPABASE_ANON_KEY")
    or os.environ.get("SUPABASE_KEY")
)

if not SUPABASE_KEY:
    raise RuntimeError("Missing SUPABASE_SERVICE_ROLE_KEY / SUPABASE_ANON_KEY / SUPABASE_KEY")

THEME_NAME = os.environ.get("THEME_NAME", "ai").lower()
RUN_DATE_SGT = os.environ.get("RUN_DATE_SGT")

PROPAGATION_TABLE = "structural_theme_graph_two_hop_propagation"
TELEMETRY_TABLE = "structural_theme_graph_two_hop_telemetry"


def sgt_today():
    return (datetime.now(timezone.utc) + timedelta(hours=8)).date().isoformat()


class SupabaseRestClient:
    def __init__(self):
        self.base_url = f"{SUPABASE_URL}/rest/v1"
        self.headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
        }

    def get(self, table, params=None):
        url = f"{self.base_url}/{table}"

        headers = dict(self.headers)
        headers["Accept"] = "application/json"

        response = requests.get(
            url,
            headers=headers,
            params=params or {},
            timeout=60,
        )

        if response.status_code >= 400:
            raise RuntimeError(
                f"GET {table} failed "
                f"{response.status_code}: {response.text[:2000]}"
            )

        return response.json()


class Phase5ATwoHopValidator:
    def __init__(self):
        self.client = SupabaseRestClient()
        self.run_date_sgt = RUN_DATE_SGT or sgt_today()
        self.theme_name = THEME_NAME

    def load_propagation_rows(self):
        params = {
            "select": "id,path_hash,two_hop_path_score",
            "run_date_sgt": f"eq.{self.run_date_sgt}",
            "theme_name": f"eq.{self.theme_name}",
            "limit": "5000",
        }

        return self.client.get(PROPAGATION_TABLE, params=params)

    def load_latest_telemetry(self):
        params = {
            "select": "*",
            "run_date_sgt": f"eq.{self.run_date_sgt}",
            "theme_name": f"eq.{self.theme_name}",
            "order": "created_at.desc",
            "limit": "1",
        }

        rows = self.client.get(TELEMETRY_TABLE, params=params)

        if rows:
            return rows[0]

        return None

    def validate(self):
        propagation_rows = self.load_propagation_rows()
        telemetry = self.load_latest_telemetry()

        failures = []
        warnings = []

        rows_checked = len(propagation_rows)

        source_edges_loaded = 0
        candidate_paths = 0
        accepted_paths = 0

        if telemetry:
            source_edges_loaded = int(
                telemetry.get("source_edges_loaded") or 0
            )

            candidate_paths = int(
                telemetry.get("candidate_paths") or 0
            )

            accepted_paths = int(
                telemetry.get("accepted_paths") or 0
            )

        # --------------------------------------------------
        # HARD VALIDATIONS
        # --------------------------------------------------

        # Only fail if loader itself failed
        if source_edges_loaded == 0:
            failures.append(
                "No single-hop source edges loaded"
            )

        # Detect duplicate hashes
        path_hashes = [
            r.get("path_hash")
            for r in propagation_rows
            if r.get("path_hash")
        ]

        if len(path_hashes) != len(set(path_hashes)):
            failures.append(
                "Duplicate two-hop path hashes detected"
            )

        # Detect invalid negative scores
        negative_scores = [
            r for r in propagation_rows
            if (r.get("two_hop_path_score") or 0) < 0
        ]

        if negative_scores:
            failures.append(
                f"Detected {len(negative_scores)} negative two-hop scores"
            )

        # --------------------------------------------------
        # SOFT STRUCTURAL CONDITIONS
        # --------------------------------------------------

        # Valid graph state:
        # no chainable A→B→C paths yet
        if (
            source_edges_loaded > 0
            and candidate_paths == 0
            and accepted_paths == 0
            and rows_checked == 0
        ):
            warnings.append(
                "No chainable two-hop paths detected in current graph state"
            )

        # Candidate paths existed but all filtered out
        if (
            candidate_paths > 0
            and accepted_paths == 0
        ):
            warnings.append(
                "Candidate paths detected but none passed thresholds"
            )

        # Weak propagation regime
        if (
            rows_checked > 0
            and rows_checked < 5
        ):
            warnings.append(
                f"Very low two-hop propagation density detected ({rows_checked} rows)"
            )

        # --------------------------------------------------
        # FINAL STATUS
        # --------------------------------------------------

        if failures:
            status = "failed"
        elif warnings:
            status = "success_with_warnings"
        else:
            status = "success"

        result = {
            "status": status,
            "run_date_sgt": self.run_date_sgt,
            "theme_name": self.theme_name,
            "rows_checked": rows_checked,
            "source_edges_loaded": source_edges_loaded,
            "candidate_paths": candidate_paths,
            "accepted_paths": accepted_paths,
            "failures": failures,
            "warnings": warnings,
        }

        print(json.dumps(result, indent=2))

        if failures:
            raise RuntimeError(
                "Phase 5A validation failed"
            )

        return result


if __name__ == "__main__":
    Phase5ATwoHopValidator().validate()
