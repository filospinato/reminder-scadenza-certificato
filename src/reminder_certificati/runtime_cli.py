"""CLI operativa con default sicuri e output esclusivamente aggregato."""

from __future__ import annotations

import argparse
import json
import os
from datetime import date
from importlib.metadata import version
from typing import Any, Mapping, Sequence

from .admin_initializer import InizializzatoreFoglioAmministrativo
from .google_runtime import (
    MAPPATURA_OPERATIVO_REALE,
    ConfigurazioneRisorseGoogle,
    costruisci_componenti_google,
    costruisci_servizio_sheets,
    leggi_matrice_config,
)
from .orchestrator import ModalitaEsecuzione, OrchestratoreReminder
from .persistent_registry import RegistroPersistente
from .runtime_config import carica_configurazione
from .smtp_transport import ConfigurazioneSmtp, TrasportoSmtpMdaemon


COLONNE_OPERATIVO_VERIFICATE: tuple[str, ...] = (
    "Tessera",
    "Cognome",
    "Nome",
    "Qualifica",
    "Stato Rinnovo",
    "Data Scadenza Certificato",
    "e-Mail",
    "Certificato medico",
    "Rinnovato senza lista",
    "Lista effettiva di appartenenza",
    "Esordiente",
    "Note",
    "Fa attività quest'anno",
)


class ErroreCliRuntime(RuntimeError):
    """Configurazione o comando operativo non valido."""


def _data(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("usa il formato YYYY-MM-DD") from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Strumenti pre-produzione del reminder certificati."
    )
    sub = parser.add_subparsers(dest="comando", required=True)

    inizializza = sub.add_parser(
        "init-admin",
        help="crea o verifica lo Spreadsheet amministrativo senza PII",
    )
    inizializza.add_argument(
        "--spreadsheet-id",
        default="",
        help="ID esistente; omettere per creare il file canonico",
    )

    sub.add_parser(
        "check-headers",
        help="verifica solo metadati e intestazioni di Operativo",
    )

    esegui = sub.add_parser("run", help="esegue il flusso con output aggregato")
    esegui.add_argument(
        "--mode",
        choices=[item.value for item in ModalitaEsecuzione],
        default=ModalitaEsecuzione.DRY_RUN.value,
    )
    esegui.add_argument("--today", type=_data, default=date.today())
    esegui.add_argument(
        "--confirm-email-delivery",
        action="store_true",
        help="seconda conferma richiesta per TEST_SMTP o PRODUZIONE",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.comando == "init-admin":
            return _init_admin(args.spreadsheet_id)
        if args.comando == "check-headers":
            return _check_headers(os.environ)
        return _run(args, os.environ)
    except Exception as exc:
        raise SystemExit(f"Errore operativo: {type(exc).__name__}: {exc}") from exc


def _init_admin(spreadsheet_id: str) -> int:
    servizio = costruisci_servizio_sheets()
    componenti = costruisci_componenti_google(
        servizio=servizio,
        risorse=ConfigurazioneRisorseGoogle(
            operativo_spreadsheet_id="placeholder-not-used",
            admin_spreadsheet_id=spreadsheet_id.strip() or "placeholder-not-used",
        ),
    )
    esito = InizializzatoreFoglioAmministrativo(
        componenti.trasporto_struttura
    ).prepara(spreadsheet_id=spreadsheet_id.strip() or None)
    print(
        json.dumps(
            {
                "operation": "init-admin",
                "spreadsheet_id": esito.spreadsheet_id,
                "created": esito.creato,
                "initialized_tabs": list(esito.tab_inizializzate),
                "already_compliant_tabs": list(esito.tab_gia_conformi),
                "contains_personal_data": False,
                "email_delivery_enabled": False,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def _check_headers(ambiente: Mapping[str, str]) -> int:
    risorse = ConfigurazioneRisorseGoogle.da_ambiente(
        ambiente,
        richiedi_admin=False,
    )
    servizio = costruisci_servizio_sheets()
    escaped = risorse.operativo_sheet_name.replace("'", "''")
    range_a1 = (
        f"'{escaped}'!A{risorse.operativo_header_row}:ZZ{risorse.operativo_header_row}"
    )
    risposta = servizio.spreadsheets().values().get(
        spreadsheetId=risorse.operativo_spreadsheet_id,
        range=range_a1,
        majorDimension="ROWS",
    ).execute()
    valori = risposta.get("values", []) if isinstance(risposta, Mapping) else []
    intestazioni = tuple(str(cella).strip() for cella in (valori[0] if valori else []))
    mancanti = [nome for nome in COLONNE_OPERATIVO_VERIFICATE if nome not in intestazioni]
    if mancanti:
        raise ErroreCliRuntime(
            "intestazioni Operativo mancanti: " + ", ".join(mancanti)
        )
    print(
        json.dumps(
            {
                "operation": "check-headers",
                "sheet": risorse.operativo_sheet_name,
                "header_row": risorse.operativo_header_row,
                "header_count": len(intestazioni),
                "required_headers_present": True,
                "data_rows_read": 0,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def _run(args: argparse.Namespace, ambiente: Mapping[str, str]) -> int:
    modalita = ModalitaEsecuzione(args.mode)
    consenso = _consenso_esterno(
        modalita,
        flag_cli=bool(args.confirm_email_delivery),
        ambiente=ambiente,
    )
    risorse = ConfigurazioneRisorseGoogle.da_ambiente(ambiente)
    servizio = costruisci_servizio_sheets()
    componenti = costruisci_componenti_google(servizio=servizio, risorse=risorse)

    InizializzatoreFoglioAmministrativo(
        componenti.trasporto_struttura
    ).verifica(spreadsheet_id=risorse.admin_spreadsheet_id)
    configurazione = carica_configurazione(
        leggi_matrice_config(
            lettore=componenti.lettore,
            spreadsheet_id=risorse.admin_spreadsheet_id,
        )
    )

    trasporto = None
    registro = None
    if modalita is not ModalitaEsecuzione.DRY_RUN:
        trasporto = TrasportoSmtpMdaemon(
            ConfigurazioneSmtp.da_ambiente(ambiente)
        )
        registro = RegistroPersistente(
            componenti.archivio_notifiche,
            versione_app=_versione(),
        )

    orchestratore = OrchestratoreReminder(
        sorgente=componenti.sorgente_operativo,
        configurazione=configurazione,
        dashboard=componenti.dashboard,
        anomalie=componenti.anomalie,
        versione_app=_versione(),
        registro=registro,
        trasporto_email=trasporto,
        mappatura=MAPPATURA_OPERATIVO_REALE,
    )
    esito = orchestratore.esegui(
        oggi=args.today,
        modalita=modalita,
        consenso_esterno_invio=consenso,
    )
    print(
        json.dumps(
            {
                "mode": esito.modalita.value,
                "status": esito.stato,
                "input_row_count": esito.righe_lette,
                "valid_record_count": esito.righe_valide,
                "anomaly_count": esito.anomalie,
                "candidate_count": esito.candidati,
                "already_registered_count": esito.notifiche_gia_presenti,
                "message_composed_count": esito.messaggi_composti,
                "send_attempt_count": esito.invii_tentati,
                "send_success_count": esito.invii_riusciti,
                "send_failure_count": esito.invii_falliti,
                "uncertain_outcome_count": esito.esiti_incerti,
                "pii_in_output": False,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if esito.stato not in {"ERRORE", "REVISIONE_RICHIESTA"} else 2


def _consenso_esterno(
    modalita: ModalitaEsecuzione,
    *,
    flag_cli: bool,
    ambiente: Mapping[str, str],
) -> bool:
    if modalita is ModalitaEsecuzione.DRY_RUN:
        return False
    if not flag_cli or ambiente.get("ALLOW_EMAIL_DELIVERY", "").casefold() != "true":
        raise ErroreCliRuntime(
            "l'invio richiede --confirm-email-delivery e ALLOW_EMAIL_DELIVERY=true"
        )
    if modalita is ModalitaEsecuzione.PRODUZIONE:
        if ambiente.get("PRODUCTION_ACTIVATION_ACK", "") != "REMINDER_CERTIFICATI_PRODUCTION_V1":
            raise ErroreCliRuntime("PRODUCTION_ACTIVATION_ACK mancante o errato")
    return True


def _versione() -> str:
    try:
        return version("reminder-scadenza-certificato")
    except Exception:
        return "0+unknown"


if __name__ == "__main__":
    raise SystemExit(main())
