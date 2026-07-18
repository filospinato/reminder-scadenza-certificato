"""CLI operativa con default sicuri e output esclusivamente aggregato."""

from __future__ import annotations

import argparse
import json
import os
from datetime import date
from importlib.metadata import version
from typing import Any, Mapping, Sequence

from .admin_initializer import (
    InizializzatoreFoglioAmministrativo,
    TrasportoStrutturaGoogleApi,
    TrasportoStrutturaSheets,
)
from .admin_schema import NOMI_TAB_AMMINISTRATIVE, crea_schema_amministrativo
from .google_runtime import (
    COLONNE_OPERATIVO_OBBLIGATORIE,
    MAPPATURA_OPERATIVO_REALE,
    ConfigurazioneRisorseGoogle,
    costruisci_componenti_google,
    costruisci_servizio_sheets,
    leggi_matrice_config,
)
from .monitoring import sanitizza_messaggio
from .orchestrator import ModalitaEsecuzione, OrchestratoreReminder
from .persistent_registry import RegistroPersistente
from .runtime_config import carica_configurazione
from .smtp_transport import ConfigurazioneSmtp, TrasportoSmtpMdaemon


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
        help="inizializza un file vuoto già creato e condiviso dall'utente",
    )
    inizializza.add_argument(
        "--spreadsheet-id",
        required=True,
        help="ID del file vuoto creato dall'amministratore umano",
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
        dettaglio = sanitizza_messaggio(str(exc))
        raise SystemExit(
            f"Errore operativo: {type(exc).__name__}: {dettaglio}"
        ) from exc


def _init_admin(spreadsheet_id: str) -> int:
    identificativo = spreadsheet_id.strip()
    if not identificativo:
        raise ErroreCliRuntime(
            "crea prima uno Spreadsheet vuoto con l'account umano e passa il suo ID"
        )
    servizio = costruisci_servizio_sheets()
    esito = InizializzatoreFoglioAmministrativo(
        TrasportoStrutturaGoogleApi(servizio)
    ).prepara(spreadsheet_id=identificativo)
    print(
        json.dumps(
            {
                "operation": "init-admin",
                "spreadsheet_id": esito.spreadsheet_id,
                "tabs_configured": esito.tab_configurate,
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
    mancanti = [
        nome for nome in COLONNE_OPERATIVO_OBBLIGATORIE if nome not in intestazioni
    ]
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

    # Controllo leggero: una lettura dei metadati e una sola riga per tab. La
    # CONFIG completa viene validata subito dopo; NOTIFICHE e ANOMALIE non sono
    # più rilette integralmente prima di ogni esecuzione.
    _verifica_struttura_admin(
        componenti.trasporto_struttura,
        spreadsheet_id=risorse.admin_spreadsheet_id,
    )
    configurazione = carica_configurazione(
        leggi_matrice_config(
            lettore=componenti.lettore,
            spreadsheet_id=risorse.admin_spreadsheet_id,
        )
    )

    registro = RegistroPersistente(
        componenti.archivio_notifiche,
        versione_app=_versione(),
    )
    trasporto = None
    if modalita is not ModalitaEsecuzione.DRY_RUN:
        trasporto = TrasportoSmtpMdaemon(
            ConfigurazioneSmtp.da_ambiente(ambiente)
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


def _verifica_struttura_admin(
    trasporto: TrasportoStrutturaSheets,
    *,
    spreadsheet_id: str,
) -> None:
    identificativo = spreadsheet_id.strip()
    if not identificativo:
        raise ErroreCliRuntime("ADMIN_SPREADSHEET_ID mancante")
    nomi = tuple(str(nome).strip() for nome in trasporto.elenca_tab(
        spreadsheet_id=identificativo
    ))
    if len(nomi) != len(NOMI_TAB_AMMINISTRATIVE) or set(nomi) != set(
        NOMI_TAB_AMMINISTRATIVE
    ):
        raise ErroreCliRuntime("tab amministrative mancanti o non conformi")

    for definizione in crea_schema_amministrativo().tab:
        escaped = definizione.nome.replace("'", "''")
        matrice = trasporto.leggi_valori(
            spreadsheet_id=identificativo,
            intervallo_a1=f"'{escaped}'!A1:ZZ1",
        )
        intestazioni = _prima_riga_normalizzata(matrice)
        if intestazioni != definizione.intestazioni:
            raise ErroreCliRuntime(
                f"{definizione.nome}: intestazioni diverse dallo schema canonico"
            )


def _prima_riga_normalizzata(
    matrice: Sequence[Sequence[Any]],
) -> tuple[str, ...]:
    if not matrice:
        return ()
    prima = matrice[0]
    valori = tuple("" if cella is None else str(cella).strip() for cella in prima)
    fine = len(valori)
    while fine and not valori[fine - 1]:
        fine -= 1
    return valori[:fine]


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
    return True


def _versione() -> str:
    try:
        return version("reminder-scadenza-certificato")
    except Exception:
        return "0+unknown"


if __name__ == "__main__":
    raise SystemExit(main())
