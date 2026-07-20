from __future__ import annotations

import json
from pathlib import Path

from reminder_certificati import google_preflight_cli
from reminder_certificati.google_preflight import CodiceErrorePreflight

CODICE_INATTESO = "PREFLIGHT_UNEXPECTED_ERROR"
CHIAVI_MINIME = {
    "operation",
    "success",
    "operativo_data_rows_read",
    "writes_performed",
    "smtp_checked",
    "pii_in_output",
}


def test_codici_applicativi_sono_univoci_e_documentati():
    codici = {codice.value for codice in CodiceErrorePreflight}
    assert len(codici) == len(CodiceErrorePreflight)
    assert all(codice.startswith("PREFLIGHT_") for codice in codici)

    testo = Path("docs/PREFLIGHT_DIAGNOSTICA.md").read_text(encoding="utf-8")
    for codice in codici | {CODICE_INATTESO}:
        assert f"`{codice}`" in testo


def test_output_json_di_successo_mantiene_le_garanzie_minime(monkeypatch, capsys):
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
        admin_config_ok = True
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
    assert CHIAVI_MINIME <= set(payload)
    assert payload["operation"] == "google-preflight"
    assert payload["success"] is True
    assert payload["admin_config_ok"] is True
    assert payload["operativo_data_rows_read"] == 0
    assert payload["writes_performed"] == 0
    assert payload["smtp_checked"] is False
    assert payload["pii_in_output"] is False


def test_output_json_inatteso_non_espone_dettagli_sensibili(monkeypatch, capsys):
    monkeypatch.setattr(
        google_preflight_cli.ConfigurazioneRisorseGoogle,
        "da_ambiente",
        lambda _env: (_ for _ in ()).throw(RuntimeError("dato-riservato@example.test")),
    )

    assert google_preflight_cli.main() == 2
    payload = json.loads(capsys.readouterr().out)
    assert CHIAVI_MINIME <= set(payload)
    assert payload["error_code"] == CODICE_INATTESO
    assert payload["detail"] == "RuntimeError"
    assert payload["operativo_data_rows_read"] == 0
    assert payload["writes_performed"] == 0
    assert payload["smtp_checked"] is False
    assert payload["pii_in_output"] is False
    assert "dato-riservato@example.test" not in json.dumps(payload)
