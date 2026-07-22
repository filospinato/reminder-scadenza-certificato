from __future__ import annotations

import json
import tomllib
from pathlib import Path

README = Path("README.md")
AGENTS = Path("AGENTS.md")
CHANGELOG = Path("CHANGELOG.md")
CURRENT_STATE = Path("CURRENT_STATE.json")
ENVIRONMENT_CONTRACT = Path("config/github/environment-contract.json")
PYPROJECT = Path("pyproject.toml")

ROOT_DOCUMENTS = {
    "README.md",
    "AGENTS.md",
    "CHANGELOG.md",
    "CURRENT_STATE.json",
}

LEGACY_PATHS = (
    Path("LATEST.md"),
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


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _keys_recursive(value: object) -> set[str]:
    if isinstance(value, dict):
        keys = {str(key) for key in value}
        for child in value.values():
            keys.update(_keys_recursive(child))
        return keys
    if isinstance(value, list):
        keys: set[str] = set()
        for child in value:
            keys.update(_keys_recursive(child))
        return keys
    return set()


def test_root_contiene_esattamente_le_quattro_fonti_canoniche() -> None:
    presenti = {
        path.name
        for path in Path(".").iterdir()
        if path.is_file() and path.suffix in {".md", ".json"}
    }
    assert presenti == ROOT_DOCUMENTS


def test_non_esistono_fonti_documentali_legacy() -> None:
    for path in LEGACY_PATHS:
        assert not path.exists(), path


def test_stato_corrente_e_coerente_con_package_e_release() -> None:
    state = _load_json(CURRENT_STATE)
    project = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    version = project["project"]["version"]

    assert state["application"]["version"] == version
    assert state["application"]["entry_point"] == "reminder-certificati"
    assert state["application"]["admin_schema_version"] == 4

    release_path = Path(state["release"]["artifact_directory"])
    assert release_path.is_dir()
    assert {path.name for path in release_path.iterdir() if path.is_file()} == RELEASE_FILES

    assert f"## [{version}]" in CHANGELOG.read_text(encoding="utf-8")


def test_current_state_non_contiene_cronologia() -> None:
    keys = {key.lower() for key in _keys_recursive(_load_json(CURRENT_STATE))}
    forbidden = {
        "history",
        "previous",
        "previous_version",
        "changes",
        "changelog",
        "timeline",
        "run_log",
    }
    assert keys.isdisjoint(forbidden)


def test_current_state_e_contratto_environment_concordano() -> None:
    state = _load_json(CURRENT_STATE)
    contract = _load_json(ENVIRONMENT_CONTRACT)

    assert state["github"]["environment"] == contract["environment"]
    assert state["github"]["environment_contract"] == str(ENVIRONMENT_CONTRACT)
    assert contract["variables"] == sorted(set(contract["variables"]))
    assert contract["secrets"] == sorted(set(contract["secrets"]))


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
        "config/github/environment-contract.json",
        "releases/",
    }:
        assert path in readme

    assert version not in readme
    assert "ROADMAP.md" not in readme
    assert "LATEST.md" not in readme


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
    ):
        assert requirement in agents

    assert "PROJECT_RULES.md" in agents
    assert "Non creare" in agents
