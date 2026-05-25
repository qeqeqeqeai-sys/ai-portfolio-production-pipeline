from pathlib import Path
from collections import Counter
import re

CONFIG_PATH = Path("configs/sde1_curated_entity_ecosystems.yaml")
REPORT_PATH = Path("reports/sde1_curated_semantic_ecosystem_blueprint.md")

REQUIRED_FIELDS = [
    "entity_id",
    "symbol",
    "name",
    "entity_type",
    "primary_ecosystem",
    "secondary_ecosystems",
    "structural_role",
    "expectation_role",
    "propagation_role",
    "propagation_links",
    "contradiction_surfaces",
    "regime_exposures",
    "information_quality_score",
    "replay_ecology_value",
    "inclusion_reason",
]


def _text() -> str:
    assert CONFIG_PATH.exists()
    return CONFIG_PATH.read_text()


def test_taxonomy_determinism_and_reproducibility_markers_present():
    text = _text()
    assert "deterministic_seed: 'SDE1_CURATED_ECOSYSTEM_V1'" in text
    assert "target_candidate_count: 350" in text
    assert "pruning_target_count: 300" in text


def test_metadata_schema_consistency():
    text = _text()
    for field in REQUIRED_FIELDS:
        assert f"- {field}" in text


def test_candidate_universe_size_bounds():
    candidates = re.findall(r"^  - entity_id:\s+E\d{3}$", _text(), flags=re.MULTILINE)
    assert len(candidates) == 350
    assert 330 <= len(candidates) <= 380


def test_anti_monoculture_and_ecosystem_diversity_balancing():
    ecosystems = re.findall(r"^    primary_ecosystem:\s+([a-z0-9_]+)$", _text(), flags=re.MULTILINE)
    assert len(ecosystems) == 350
    counts = Counter(ecosystems)
    assert len(counts) == 12
    max_share = max(counts.values()) / len(ecosystems)
    assert max_share <= 0.20


def test_no_direct_sql_introduced_in_sde1_artifacts():
    blob = (CONFIG_PATH.read_text() + "\n" + REPORT_PATH.read_text()).lower()
    banned = ["select ", "insert ", "update ", "delete ", "create table", "drop table"]
    assert all(token not in blob for token in banned)


def test_governance_and_additive_architecture_preservation_documented():
    report = REPORT_PATH.read_text().lower()
    assert "planning/config/report/test artifacts only" in report
    assert "does not add replay execution" in report
    assert "does not add" in report and "governance" in report


def test_no_replay_execution_path_introduced():
    report = REPORT_PATH.read_text().lower()
    assert "does not add replay execution" in report
