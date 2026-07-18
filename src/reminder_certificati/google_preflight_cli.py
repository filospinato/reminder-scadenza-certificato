"""CLI di preflight Google in sola lettura e con output aggregato."""

from __future__ import annotations

import json
import os

from .google_preflight import PreflightGoogle, TrasportoPreflightGoogleApi
from .google_runtime import ConfigurazioneRisorseGoogle, costruisci_servizio_sheets
from .monitoring import sanitizza_messaggio


def main() -> int:
    try:
        risorse = ConfigurazioneRisorseGoogle.da_ambiente(os.environ)
        servizio = costruisci_servizio_sheets()
        esito = PreflightGoogle(TrasportoPreflightGoogleApi(servizio)).esegui(
            risorse=risorse
        )
        print(
            json.dumps(
                {
                    "operation": "google-preflight",
                    "operativo_headers_ok": esito.operativo_headers_ok,
                    "admin_tabs_ok": esito.admin_tabs_ok,
                    "admin_headers_ok": esito.admin_headers_ok,
                    "operativo_data_rows_read": esito.operativo_data_rows_read,
                    "writes_performed": esito.writes_performed,
                    "smtp_checked": esito.smtp_checked,
                    "admin_write_verified": esito.admin_write_verified,
                    "pii_in_output": False,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    except Exception as exc:
        dettaglio = sanitizza_messaggio(str(exc))
        raise SystemExit(
            f"Errore preflight: {type(exc).__name__}: {dettaglio}"
        ) from exc


if __name__ == "__main__":
    raise SystemExit(main())
