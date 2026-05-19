from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from transmission_layers.intelligence.tier3i.path_explainability import SCORING_VERSION, explain_paths


def _path(
    path_id: str = "path::a->b->c",
    nodes: list[str] | None = None,
    band: str = "medium",
    suppressed: bool = False,
    contaminated: bool = False,
    reinforcement: float = 0.0,
):
    node_list = nodes or ["a", "b", "c"]
    return {
        "path_id": path_id,
        "source_node_id": node_list[0],
        "terminal_node_id": node_list[-1],
        "path_nodes": node_list,
        "path_edges": [
            {"source_node_id": "a", "target_node_id": "b", "edge_quality_score": 0.9, "confidence_band": "high"},
            {"source_node_id": "b", "target_node_id": "c", "edge_quality_score": 0.3, "confidence_band": "low"},
        ],
        "hop_count": max(1, len(node_list) - 1),
        "path_quality_score": 0.52,
        "hop_decay_factor": 0.75,
        "reinforcement_score": reinforcement,
        "path_confidence_band": band,
        "suppressed_for_propagation": suppressed,
        "contamination_warning": contaminated,
        "explainability_payload": {"warnings": ["contains_low_confidence_edge"]},
    }


def test_deterministic_explanations():
    src = [_path()]
    assert explain_paths(src) == explain_paths(src)


def test_causal_chain_summary_uses_path_nodes_order():
    record = explain_paths([_path(nodes=["n1", "n2", "n3", "n4"])])[0]
    assert "n1 -> n2 -> n3 -> n4" in record["causal_chain_summary"]


def test_confidence_sentence_matches_confidence_band():
    high = explain_paths([_path(band="high")])[0]
    medium = explain_paths([_path(band="medium")])[0]
    low = explain_paths([_path(band="low")])[0]
    assert "high" in high["confidence_sentence"].lower()
    assert "medium" in medium["confidence_sentence"].lower()
    assert "low" in low["confidence_sentence"].lower()


def test_suppressed_paths_labelled_suppressed_noise():
    record = explain_paths([_path(suppressed=True, contaminated=False)])[0]
    assert record["decision_usefulness_label"] == "suppressed_noise"


def test_contamination_warning_labelled_contaminated_chain():
    record = explain_paths([_path(contaminated=True)])[0]
    assert record["decision_usefulness_label"] == "contaminated_chain"
    assert record["contamination_notes"]


def test_weak_links_are_surfaced():
    record = explain_paths([_path()])[0]
    assert any("b->c" in link for link in record["weak_links_in_path"])


def test_reinforcement_mentioned_when_meaningful():
    record = explain_paths([_path(reinforcement=0.09)])[0]
    assert record["key_reinforcement_drivers"]


def test_hop_decay_mentioned_for_multi_hop_paths():
    record = explain_paths([_path(nodes=["a", "b", "c"])])[0]
    assert "hop_decay_factor" in record["path_rationale"]


def test_forbidden_causal_words_not_used():
    record = explain_paths([_path()])[0]
    text = " ".join(
        [
            record["causal_chain_summary"],
            record["path_rationale"],
            record["confidence_sentence"],
        ]
    ).lower()
    assert "proves" not in text
    assert " causes " not in f" {text} "


def test_cli_writes_summary_json(tmp_path: Path):
    env = dict(os.environ)
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1])
    result = subprocess.run(
        [sys.executable, "-m", "transmission_layers.intelligence.tier3i.path_explainability"],
        cwd=tmp_path,
        check=True,
        text=True,
        capture_output=True,
        env=env,
    )
    assert "[tier3i]" in result.stdout
    payload = json.loads((tmp_path / "logs" / "tier3i_path_explainability_summary.json").read_text(encoding="utf-8"))
    assert payload["tier"] == "3I"
    assert payload["phase"] == "2B"
    assert payload["status"] == "success"


def test_no_dependency_on_tier3h5_governance_modules():
    import transmission_layers.intelligence.tier3i.path_explainability as module

    source = Path(module.__file__).read_text(encoding="utf-8").lower()
    assert "tier3h5" not in source
    assert "governance" not in source
    assert SCORING_VERSION == "3I.2B.v1"
