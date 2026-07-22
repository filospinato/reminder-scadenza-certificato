from __future__ import annotations

import re
from pathlib import Path

WORKFLOW_ORDINARIO = Path(".github/workflows/manual-preproduction.yml")
WORKFLOW_MANUTENZIONE = Path(".github/workflows/manual-maintenance.yml")
WORKFLOW_PRODUZIONE = Path(".github/workflows/production.yml")
CONTRATTO = Path("docs/CONTRATTO_ENVIRONMENT_GITHUB.md")


def _riferimenti(testo: str, contesto: str) -> set[str]:
    return set(re.findall(rf"\$\{{\{{\s*{contesto}\.([A-Z0-9_]+)\s*\}}\}}", testo))


def _sezione_documentata(testo: str, nome: str) -> set[str]:
    pattern = rf"<!-- BEGIN {re.escape(nome)} -->\s*```text\s*(.*?)\s*```\s*<!-- END {re.escape(nome)} -->"
    match = re.search(pattern, testo, flags=re.DOTALL)
    assert match is not None, f"Sezione documentale mancante: {nome}"
    return {riga.strip() for riga in match.group(1).splitlines() if riga.strip()}


def test_variables_usate_dai_workflow_sono_documentate() -> None:
    contratto = CONTRATTO.read_text(encoding="utf-8")
    manuali = "\n".join(
        percorso.read_text(encoding="utf-8")
        for percorso in (WORKFLOW_ORDINARIO, WORKFLOW_MANUTENZIONE)
    )
    produzione = WORKFLOW_PRODUZIONE.read_text(encoding="utf-8")

    assert _riferimenti(manuali, "vars") <= _sezione_documentata(
        contratto, "PREPRODUCTION VARIABLES"
    )
    assert _riferimenti(produzione, "vars") <= _sezione_documentata(
        contratto, "PREPRODUCTION VARIABLES"
    )


def test_workflow_smtp_usano_i_segreti_documentati() -> None:
    contratto = CONTRATTO.read_text(encoding="utf-8")
    attesi = _sezione_documentata(contratto, "SMTP SECRETS")
    ordinario = _riferimenti(WORKFLOW_ORDINARIO.read_text(encoding="utf-8"), "secrets")
    manutenzione = _riferimenti(
        WORKFLOW_MANUTENZIONE.read_text(encoding="utf-8"), "secrets"
    )
    produzione = _riferimenti(
        WORKFLOW_PRODUZIONE.read_text(encoding="utf-8"), "secrets"
    )

    assert ordinario == attesi
    assert manutenzione == set()
    assert produzione == attesi


def test_solo_la_password_smtp_e_un_secret() -> None:
    contratto = CONTRATTO.read_text(encoding="utf-8")
    pubbliche = _sezione_documentata(contratto, "PREPRODUCTION VARIABLES")

    assert "SMTP_PASSWORD" not in pubbliche
    for nome in (
        "SMTP_HOST",
        "SMTP_PORT",
        "SMTP_SECURITY",
        "SMTP_REPLY_TO",
        "SMTP_USERNAME",
    ):
        assert nome in pubbliche
    assert "SMTP_FROM" not in pubbliche
    assert "SMTP_FROM_NAME" not in pubbliche


def test_struttura_operativo_non_e_una_configurazione_github() -> None:
    testo = "\n".join(
        percorso.read_text(encoding="utf-8")
        for percorso in (
            WORKFLOW_ORDINARIO,
            WORKFLOW_MANUTENZIONE,
            WORKFLOW_PRODUZIONE,
            CONTRATTO,
        )
    )
    for nome in (
        "OPERATIVO_SHEET_NAME",
        "OPERATIVO_HEADER_ROW",
        "OPERATIVO_COLUMNS_A1",
    ):
        assert nome not in testo


def test_non_esistono_gate_ridondanti() -> None:
    testo = "\n".join(
        percorso.read_text(encoding="utf-8")
        for percorso in (
            WORKFLOW_ORDINARIO,
            WORKFLOW_MANUTENZIONE,
            WORKFLOW_PRODUZIONE,
            CONTRATTO,
        )
    )
    for nome in (
        "PREPRODUCTION_ENABLED",
        "PRODUCTION_ENABLED",
        "ALLOW_EMAIL_DELIVERY",
        "ALLOW_SYNTHETIC_REGISTRY_WRITE",
    ):
        assert nome not in testo
