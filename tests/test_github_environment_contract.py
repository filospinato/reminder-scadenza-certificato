from __future__ import annotations

import re
from pathlib import Path


WORKFLOW_MANUALE = Path(".github/workflows/manual-preproduction.yml")
MODELLO_PRODUZIONE = Path("docs/workflows/production.yml.example")
CONTRATTO = Path("docs/CONTRATTO_ENVIRONMENT_GITHUB.md")

PREPRODUCTION_VARIABLES = {
    "ADMIN_SPREADSHEET_ID",
    "GCP_PROJECT_ID",
    "GCP_SERVICE_ACCOUNT",
    "GCP_WORKLOAD_IDENTITY_PROVIDER",
    "OPERATIVO_COLUMNS_A1",
    "OPERATIVO_HEADER_ROW",
    "OPERATIVO_SHEET_NAME",
    "OPERATIVO_SPREADSHEET_ID",
    "PREPRODUCTION_ENABLED",
    "SMTP_FROM_NAME",
    "SMTP_REPLY_TO",
}

PRODUCTION_VARIABLES = {
    "ADMIN_SPREADSHEET_ID",
    "GCP_PROJECT_ID",
    "GCP_SERVICE_ACCOUNT",
    "GCP_WORKLOAD_IDENTITY_PROVIDER",
    "OPERATIVO_COLUMNS_A1",
    "OPERATIVO_SPREADSHEET_ID",
    "PRODUCTION_ENABLED",
    "PRODUCTION_WORKFLOW_APPROVED",
    "SMTP_FROM_NAME",
    "SMTP_REPLY_TO",
}

SMTP_SECRETS = {
    "SMTP_FROM",
    "SMTP_HOST",
    "SMTP_PASSWORD",
    "SMTP_PORT",
    "SMTP_SECURITY",
    "SMTP_USERNAME",
}


def _riferimenti(testo: str, contesto: str) -> set[str]:
    return set(re.findall(rf"\$\{{\{{\s*{contesto}\.([A-Z0-9_]+)\s*\}}\}}", testo))


def _sezione_documentata(testo: str, nome: str) -> set[str]:
    pattern = rf"<!-- BEGIN {re.escape(nome)} -->\s*```text\s*(.*?)\s*```\s*<!-- END {re.escape(nome)} -->"
    match = re.search(pattern, testo, flags=re.DOTALL)
    assert match is not None, f"Sezione documentale mancante: {nome}"
    return {riga.strip() for riga in match.group(1).splitlines() if riga.strip()}


def test_workflow_manuale_usa_esattamente_le_variables_documentate():
    testo = WORKFLOW_MANUALE.read_text(encoding="utf-8")
    assert _riferimenti(testo, "vars") == PREPRODUCTION_VARIABLES


def test_modello_produzione_usa_esattamente_le_variables_documentate():
    testo = MODELLO_PRODUZIONE.read_text(encoding="utf-8")
    assert _riferimenti(testo, "vars") == PRODUCTION_VARIABLES


def test_i_due_workflow_usano_lo_stesso_contratto_di_secrets_smtp():
    manuale = WORKFLOW_MANUALE.read_text(encoding="utf-8")
    produzione = MODELLO_PRODUZIONE.read_text(encoding="utf-8")

    assert _riferimenti(manuale, "secrets") == SMTP_SECRETS
    assert _riferimenti(produzione, "secrets") == SMTP_SECRETS


def test_documentazione_corrisponde_esattamente_ai_workflow():
    testo = CONTRATTO.read_text(encoding="utf-8")

    assert _sezione_documentata(testo, "PREPRODUCTION VARIABLES") == PREPRODUCTION_VARIABLES
    assert _sezione_documentata(testo, "PRODUCTION VARIABLES") == PRODUCTION_VARIABLES
    assert _sezione_documentata(testo, "SMTP SECRETS") == SMTP_SECRETS


def test_dati_smtp_non_vengono_riclassificati_in_modo_pericoloso():
    assert "SMTP_FROM_NAME" not in SMTP_SECRETS
    assert "SMTP_REPLY_TO" not in SMTP_SECRETS
    assert {"SMTP_USERNAME", "SMTP_PASSWORD"}.isdisjoint(
        PREPRODUCTION_VARIABLES | PRODUCTION_VARIABLES
    )
