from __future__ import annotations

import json
import re
from pathlib import Path

WORKFLOW_ORDINARIO = Path(".github/workflows/manual-preproduction.yml")
WORKFLOW_MANUTENZIONE = Path(".github/workflows/manual-maintenance.yml")
WORKFLOW_PRODUZIONE = Path(".github/workflows/production.yml")
CONTRATTO = Path("config/github/environment-contract.json")


def _riferimenti(testo: str, contesto: str) -> set[str]:
    return set(re.findall(rf"\$\{{\{{\s*{contesto}\.([A-Z0-9_]+)\s*\}}\}}", testo))


def _contratto() -> dict:
    return json.loads(CONTRATTO.read_text(encoding="utf-8"))


def test_variables_usate_dai_workflow_sono_documentate() -> None:
    contract = _contratto()
    documented = set(contract["variables"])
    workflows = (WORKFLOW_ORDINARIO, WORKFLOW_MANUTENZIONE, WORKFLOW_PRODUZIONE)

    used = set().union(
        *(_riferimenti(path.read_text(encoding="utf-8"), "vars") for path in workflows)
    )
    assert used <= documented


def test_workflow_smtp_usano_i_segreti_documentati() -> None:
    expected = set(_contratto()["secrets"])
    ordinary = _riferimenti(WORKFLOW_ORDINARIO.read_text(encoding="utf-8"), "secrets")
    maintenance = _riferimenti(
        WORKFLOW_MANUTENZIONE.read_text(encoding="utf-8"), "secrets"
    )
    production = _riferimenti(WORKFLOW_PRODUZIONE.read_text(encoding="utf-8"), "secrets")

    assert ordinary == expected
    assert maintenance == set()
    assert production == expected


def test_solo_la_password_smtp_e_un_secret() -> None:
    contract = _contratto()
    public = set(contract["variables"])
    secrets = set(contract["secrets"])

    assert secrets == {"REMINDER_SMTP_PASSWORD"}
    assert contract["secrets_scope"] == "repository"
    assert contract["variables_scope"] == "environment"
    assert "REMINDER_SMTP_PASSWORD" not in public
    assert "SMTP_PASSWORD" not in public
    for name in (
        "SMTP_HOST",
        "SMTP_PORT",
        "SMTP_SECURITY",
        "SMTP_REPLY_TO",
        "SMTP_USERNAME",
    ):
        assert name in public
    assert "SMTP_FROM" not in public
    assert "SMTP_FROM_NAME" not in public


def test_struttura_operativo_non_e_una_configurazione_github() -> None:
    text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (
            WORKFLOW_ORDINARIO,
            WORKFLOW_MANUTENZIONE,
            WORKFLOW_PRODUZIONE,
            CONTRATTO,
        )
    )
    for name in (
        "OPERATIVO_SHEET_NAME",
        "OPERATIVO_HEADER_ROW",
        "OPERATIVO_COLUMNS_A1",
    ):
        assert name not in text


def test_non_esistono_gate_ridondanti() -> None:
    text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (
            WORKFLOW_ORDINARIO,
            WORKFLOW_MANUTENZIONE,
            WORKFLOW_PRODUZIONE,
            CONTRATTO,
        )
    )
    for name in (
        "PREPRODUCTION_ENABLED",
        "PRODUCTION_ENABLED",
        "ALLOW_EMAIL_DELIVERY",
        "ALLOW_SYNTHETIC_REGISTRY_WRITE",
    ):
        assert name not in text


def test_environment_del_contratto_e_usato_da_tutti_i_workflow() -> None:
    environment = _contratto()["environment"]

    for workflow in (
        WORKFLOW_ORDINARIO,
        WORKFLOW_MANUTENZIONE,
        WORKFLOW_PRODUZIONE,
    ):
        assert f"environment: {environment}" in workflow.read_text(encoding="utf-8")
