from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def test_foundation_docs_exist():
    expected_docs = [
        "SEFI_G2_CONSTITUTION.md",
        "ONTOLOGY.md",
        "GRAPH_DESIGN.md",
        "DATABASE_SCHEMA_DRAFT.md",
    ]

    missing = [name for name in expected_docs if not (DOCS / name).is_file()]

    assert missing == []


def test_core_ontology_terms_are_documented():
    ontology = (DOCS / "ONTOLOGY.md").read_text(encoding="utf-8")

    for term in [
        "Observation Fact",
        "Expectation Expression",
        "Expectation",
        "Theme",
        "Entity",
        "Evidence Source",
    ]:
        assert term in ontology
