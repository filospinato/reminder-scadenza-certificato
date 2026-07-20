from __future__ import annotations

import tomllib
from pathlib import Path

README = Path("README.md")
ROADMAP = Path("ROADMAP.md")
CHANGELOG = Path("CHANGELOG.md")
OPERATIONS = Path("docs/OPERATIONS.md")
TEST_PLAN = Path("docs/TEST_PLAN.md")
PYPROJECT = Path("pyproject.toml")

DOCUMENTI_CON_SCOPO = (
    README,
    ROADMAP,
    CHANGELOG,
    OPERATIONS,
    TEST_PLAN,
)


def test_non_esiste_un_file_di_stato_corrente_duplicato() -> None:
    assert not Path("LATEST.md").exists()


def test_i_documenti_dichiarano_subito_il_proprio_scopo() -> None:
    for percorso in DOCUMENTI_CON_SCOPO:
        righe = percorso.read_text(encoding="utf-8").splitlines()
        assert righe[0].startswith("# "), percorso
        assert righe[1] == "", percorso
        descrizione = righe[2].strip()
        assert descrizione, percorso
        assert not descrizione.startswith(("#", "-", "```")), percorso
        assert len(descrizione) >= 40, percorso


def test_readme_dichiara_le_fonti_di_verita() -> None:
    testo = README.read_text(encoding="utf-8")
    assert "## Fonti di verità" in testo
    for percorso in (
        "pyproject.toml",
        "CHANGELOG.md",
        "ROADMAP.md",
        "docs/OPERATIONS.md",
        "docs/DEPLOYMENT_CHECKLIST.md",
        "docs/EMERGENCY.md",
    ):
        assert percorso in testo


def test_roadmap_contiene_soltanto_lavoro_aperto() -> None:
    testo = ROADMAP.read_text(encoding="utf-8")
    assert "- [ ]" in testo
    assert "- [x]" not in testo


def test_versione_corrente_vive_in_pyproject_e_changelog() -> None:
    progetto = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    versione = progetto["project"]["version"]
    changelog = CHANGELOG.read_text(encoding="utf-8")
    readme = README.read_text(encoding="utf-8")
    roadmap = ROADMAP.read_text(encoding="utf-8")

    assert f"## [{versione}]" in changelog
    assert versione not in readme
    assert versione not in roadmap
