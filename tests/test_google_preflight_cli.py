from __future__ import annotations

import json

from reminder_certificati.google_preflight import (
    CodiceErrorePreflight,
    DiagnosticaPreflight,
    ErrorePreflightGoogle,
)
from reminder_certificati import google_preflight_cli


def test_cli_restituisce_json_diagnostico_senza_identificatori(monkeypatch, capsys):
    monkeypatch.setattr(
        google_preflight_cli.ConfigurazioneRisorseGoogle,
        "da_ambiente",
        lambda _env: object(),
    )
    monkeypatch.setattr(google_preflight_cli, "costruisci_servizio_sheets", lambda: object())

    def fallisce(_self, *, risorse):
        raise ErrorePreflightGoogle(
            DiagnosticaPreflight(
                CodiceErrorePreflight.ADMIN_NON_RAGGIUNGIBILE,
                "Lo Spreadsheet amministrativo non è raggiungibile in lettura.",
                "Verificare condivisione, ID pubblico e identità WIF del service account.",
            )
        )

    monkeypatch.setattr(google_preflight_cli.PreflightGoogle, "esegui", fallisce)

    assert google_preflight_cli.run({}) == 2
    payload = json.loads(capsys.readouterr().out)

    assert payload["success"] is False
    assert payload["error_code"] == "PREFLIGHT_ADMIN_UNREACHABLE"
    assert payload["writes_performed"] == 0
    assert payload["operativo_data_rows_read"] == 0
    assert payload["pii_in_output"] is False
    testo = json.dumps(payload)
    assert "spreadsheet-id" not in testo
    assert "@" not in testo


def test_cli_traduce_errori_inattesi_senza_dettaglio_originale(monkeypatch, capsys):
    monkeypatch.setattr(
        google_preflight_cli.ConfigurazioneRisorseGoogle,
        "da_ambiente",
        lambda _env: (_ for _ in ()).throw(RuntimeError("segreto@example.test")),
    )

    assert google_preflight_cli.run({}) == 2
    payload = json.loads(capsys.readouterr().out)

    assert payload["error_code"] == "PREFLIGHT_UNEXPECTED_ERROR"
    assert payload["detail"] == "RuntimeError"
    assert "segreto@example.test" not in json.dumps(payload)
