from __future__ import annotations

import argparse
import json
import os
from importlib.metadata import version
from typing import Mapping

from .google_runtime import ConfigurazioneRisorseGoogle, costruisci_servizio_sheets
from .monitoring import sanitizza_messaggio
from .notifications_sheets import ArchivioNotificheGoogleSheets, TrasportoNotificheGoogleApi
from .registry_probe import esegui_collaudo_registro_sintetico


class ErroreCliCollaudo(RuntimeError):
    """Il comando di collaudo non dispone delle conferme richieste."""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Collaudo sintetico protetto della tab NOTIFICHE."
    )
    parser.add_argument(
        "--confirm-synthetic-write",
        action="store_true",
        help="conferma la scrittura di una sola riga interamente sintetica",
    )
    return parser


def run(*, conferma: bool, ambiente: Mapping[str, str]) -> int:
    if not conferma:
        raise ErroreCliCollaudo("richiesta --confirm-synthetic-write")
    if ambiente.get("ALLOW_SYNTHETIC_REGISTRY_WRITE", "").casefold() != "true":
        raise ErroreCliCollaudo(
            "richiesta anche ALLOW_SYNTHETIC_REGISTRY_WRITE=true"
        )

    risorse = ConfigurazioneRisorseGoogle.da_ambiente(
        ambiente,
        richiedi_operativo=False,
    )
    servizio = costruisci_servizio_sheets()
    archivio = ArchivioNotificheGoogleSheets(
        trasporto=TrasportoNotificheGoogleApi(servizio),
        spreadsheet_id=risorse.admin_spreadsheet_id,
    )
    esito = esegui_collaudo_registro_sintetico(
        archivio,
        versione_app=_versione(),
    )
    print(
        json.dumps(
            {
                "operation": "synthetic-registry-check",
                "append_verified": esito.append_verificato,
                "reread_verified": esito.rilettura_verificata,
                "update_verified": esito.update_verificato,
                "single_key_verified": esito.una_sola_chiave_verificata,
                "final_status": esito.stato_finale.value,
                "synthetic_rows_written": 1,
                "operativo_rows_read": 0,
                "email_delivery_enabled": False,
                "pii_in_output": False,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def main() -> int:
    args = build_parser().parse_args()
    try:
        return run(
            conferma=bool(args.confirm_synthetic_write),
            ambiente=os.environ,
        )
    except Exception as exc:
        dettaglio = sanitizza_messaggio(str(exc))
        raise SystemExit(
            f"Errore collaudo registro: {type(exc).__name__}: {dettaglio}"
        ) from exc


def _versione() -> str:
    try:
        return version("reminder-scadenza-certificato")
    except Exception:
        return "0+unknown"


if __name__ == "__main__":
    raise SystemExit(main())
