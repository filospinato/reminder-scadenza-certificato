from __future__ import annotations

import tomllib
from pathlib import Path

README = Path("README.md")
AGENTS = Path("AGENTS.md")
CHANGELOG = Path("CHANGELOG.md")
ENVIRONMENT_CONTRACT = Path("config/github/environment-contract.json")
PYPROJECT = Path("pyproject.toml")

ROOT_DOCUMENTS = {
    "README.md",
    "AGENTS.md",
    "CHANGELOG.md",
}

LEGACY_PATHS = (
    Path("LATEST.md"),
    Path("CURRENT_STATE.md"),
    Path("CURRENT_STATE.json"),
    Path("ROADMAP.md"),
    Path("PROJECT_RULES.md"),
    Path("PROJECT_INSTRUCTION.md"),
    Path("docs"),
)

RELEASE_FILES = {
    "README.md",
    "OPERATOR_GUIDE.md",
    "DEPLOYMENT.md",
    "REFERENCE.md",
    "VALIDATION.md",
}


def test_root_contiene_esattamente_le_tre_fonti_documentali_canoniche() -> None:
    presenti = {
        path.name
        for path in Path(".").iterdir()
        if path.is_file() and path.suffix in {".md", ".json"}
    }
    assert presenti == ROOT_DOCUMENTS


def test_non_esistono_fonti_documentali_legacy_o_manifesti_di_stato() -> None:
    for path in LEGACY_PATHS:
        assert not path.exists(), path


def test_versione_changelog_e_release_sono_coerenti() -> None:
    project = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    version = project["project"]["version"]
    release_path = Path(f"releases/v{version}")

    assert project["project"]["scripts"]["reminder-certificati"]
    assert release_path.is_dir()
    assert {path.name for path in release_path.iterdir() if path.is_file()} == RELEASE_FILES
    assert f"## [{version}]" in CHANGELOG.read_text(encoding="utf-8")


def test_readme_e_solo_ssot_semantica() -> None:
    readme = README.read_text(encoding="utf-8")
    version = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))["project"]["version"]

    for section in (
        "## Obiettivo",
        "## Architettura",
        "## Modello di sicurezza",
        "## Stato semantico",
        "## Fonti di verità",
    ):
        assert section in readme

    for path in ROOT_DOCUMENTS | {
        "pyproject.toml",
        ".github/workflows/",
        "config/github/environment-contract.json",
        "releases/",
    }:
        assert path in readme

    assert version not in readme
    assert "ROADMAP.md" not in readme
    assert "LATEST.md" not in readme
    assert "CURRENT_STATE" not in readme


def test_agents_e_unica_ssot_operativa() -> None:
    agents = AGENTS.read_text(encoding="utf-8")

    for requirement in (
        "## 1. Sicurezza e invarianti non negoziabili",
        "## 2. Fonti di verità",
        "## 3. Metodo di modifica",
        "## 4. Verifica automatica obbligatoria",
        "## 5. Collaudi esterni",
        "## 6. Versioni e artefatti di release",
        "## 7. Pull request e revisione finale",
        "INVIO_AUTOMATICO_ATTIVO=false",
        "setup-preview",
        "registry-check",
        "pull request in bozza",
        "pyproject.toml",
        ".github/workflows/",
    ):
        assert requirement in agents

    assert "PROJECT_RULES.md" in agents
    assert "CURRENT_STATE.json" in agents
    assert "Non creare" in agents


def test_contratto_environment_esiste_fuori_dalla_root() -> None:
    assert ENVIRONMENT_CONTRACT.is_file()
