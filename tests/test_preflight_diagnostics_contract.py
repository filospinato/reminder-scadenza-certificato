from __future__ import annotations

import json
import re
from pathlib import Path

from reminder_certificati import google_preflight_cli
from reminder_certificati.google_preflight import CodiceErrorePreflight


CODICI_APPLICATIVI_ATTESI = (
    "PREFLIGHT_RESOURCE_IDS_EQUAL",
    "PREFLIGHT_ADMIN_UNREACHABLE",
    "PREFLIGHT_ADMIN_TABS_INVALID",
    "PREFLIGHT_ADMIN_HEADERS_UNREADABLE",
    "PREFLIGHT_ADMIN_HEADERS_INVALID",
    "PREFLIGHT_OPERATIVO_UNREACHABLE",
    "PREFLIGHT_OPERATIVO_HEADERS_MISSING",
)
CODICE_INATTESO = "PREFLIGHT_UNEXPECTED_ERROR"
CHIAVI_COMUNI_OUTPUT = {
    "operation",
    "success",
    "operativo_data_rows_read",
    "writes_performed",
    "smtp_checked",
    "pii_in_output",
}


def test_codici_applicativi_pubblici_restano_esatti_e_ordinati():
    assert tuple(codice.value for codice in CodiceErrorePreflight) == CODICI_APPLICATIVI_ATTESI
    assert len(set(CODICI_APPLICATIVI_ATTESI)) == len(CODICI_APPLICATIVI_ATTESI)
    assert all(codice.startswith("PREFLIGHT_") for codice in CODICI_APPLICATIVI_ATTESI)


def test_documentazione_elenca_esattamente_tutti_i_codici_pubblici():
    testo = Path("docs/PREFLIGHT_DIAGNOSTICA.md").read_text(encoding="utf-8")
    codici_documentati = set(re.findall(r"`(PREFLIGHT_[A-Z_]+)`", testo))
    codici_attesi = set(CODICI_APPLICATIVI_ATTESI) | {CODICE_INATTESO}

    assert codici_documentati == codici_attesi
    assert all(testo.count(f"`{codice}`") == 1 for codice in codici_attesi)


def test_output_json_di_successo_mantiene_lo_schema_pubblico(monkeypatch, capsys):
    monkeypatch.setattr(
        google_preflight_cli.ConfigurazioneRisorseGoogle,
        "da_ambiente",
        lambda _env: object(),
    )
    monkeypatch.setattr(google_preflight_cli, "costruisci_servizio_sheets", lambda: object())

    class Esito:
        operativo_headers_ok = True
        admin_tabs_ok = True
        admin_headers_ok = True
        operativo_data_rows_read = 0
        writes_performed = 0
        smtp_checked = False
        admin_write_verified = False

    monkeypatch.setattr(
        google_preflight_cli.PreflightGoogle,
        "esegui",
        lambda _self, *, risorse: Esito(),
    )

    assert google_preflight_cli.main() == 0
    payload = json.loads(capsys.readouterr().out)

    assert set(payload) == CHIAVI_COMUNI_OUTPUT | {
        "operativo_headers_ok",
        "admin_tabs_ok",
        "admin_headers_ok",
        "admin_write_verified",
    }
    assert payload["operation"] == "google-preflight"
    assert payload["success"] is True
    assert payload["operativo_data_rows_read"] == 0
    assert payload["writes_performed"] == 0
    assert payload["smtp_checked"] is False
    assert payload["pii_in_output"] is False


def test_output_json_inatteso_mantiene_lo_schema_pubblico(monkeypatch, capsys):
    monkeypatch.setattr(
        google_preflight_cli.ConfigurazioneRisorseGoogle,
        "da_ambiente",
        lambda _env: (_ for _ in ()).throw(RuntimeError("dato-riservato@example.test")),
    )

    assert google_preflight_cli.main() == 2
    payload = json.loads(capsys.readouterr().out)

    assert set(payload) == CHIAVI_COMUNI_OUTPUT | {
        "error_code",
        "message",
        "runbook_action",
        "detail",
    }
    assert payload["error_code"] == CODICE_INATTESO
    assert payload["detail"] == "RuntimeError"
    assert payload["operativo_data_rows_read"] == 0
    assert payload["writes_performed"] == 0
    assert payload["smtp_checked"] is False
    assert payload["pii_in_output"] is False
    assert "dato-riservato@example.test" not in json.dumps(payload)
