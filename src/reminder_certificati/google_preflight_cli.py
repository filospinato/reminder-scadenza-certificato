"""CLI di preflight Google in sola lettura e con output aggregato."""

from __future__ import annotations

import json
import os

from .google_preflight import (
    ErrorePreflightGoogle,
    PreflightGoogle,
    TrasportoPreflightGoogleApi,
)
from .google_runtime import ConfigurazioneRisorseGoogle, costruisci_servizio_sheets
from .monitoring import sanitizza_messaggio


def _stampa(payload: dict[str, object]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def main() -> int:
    try:
        risorse = ConfigurazioneRisorseGoogle.da_ambiente(os.environ)
        servizio = costruisci_servizio_sheets()
        esito = PreflightGoogle(TrasportoPreflightGoogleApi(servizio)).esegui(
            risorse=risorse
        )
        _stampa(
            {
                "operation": "google-preflight",
                "success": True,
                "operativo_headers_ok": esito.operativo_headers_ok,
                "admin_tabs_ok": esito.admin_tabs_ok,
                "admin_headers_ok": esito.admin_headers_ok,
                "operativo_data_rows_read": esito.operativo_data_rows_read,
                "writes_performed": esito.writes_performed,
                "smtp_checked": esito.smtp_checked,
                "admin_write_verified": esito.admin_write_verified,
                "pii_in_output": False,
            }
        )
        return 0
    except ErrorePreflightGoogle as exc:
        diagnostica = exc.diagnostica
        _stampa(
            {
                "operation": "google-preflight",
                "success": False,
                "error_code": diagnostica.codice.value,
                "message": diagnostica.messaggio,
                "runbook_action": diagnostica.azione_runbook,
                "operativo_data_rows_read": 0,
                "writes_performed": 0,
                "smtp_checked": False,
                "pii_in_output": False,
            }
        )
        return 2
    except Exception as exc:
        _stampa(
            {
                "operation": "google-preflight",
                "success": False,
                "error_code": "PREFLIGHT_UNEXPECTED_ERROR",
                "message": "Il preflight non è stato completato.",
                "runbook_action": "Verificare configurazione WIF e log sanitizzati, quindi ripetere il preflight.",
                "detail": sanitizza_messaggio(type(exc).__name__),
                "operativo_data_rows_read": 0,
                "writes_performed": 0,
                "smtp_checked": False,
                "pii_in_output": False,
            }
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
