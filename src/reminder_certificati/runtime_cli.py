"""Unica CLI operativa con default sicuri e output aggregato."""

from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from importlib.metadata import version
from pathlib import Path
from typing import Any, Mapping, Sequence

from .admin_initializer import (
    InizializzatoreFoglioAmministrativo,
    TrasportoStrutturaGoogleApi,
    TrasportoStrutturaSheets,
)
from .admin_migration import (
    TrasportoMigrazioneGoogleApi,
    applica_piano,
    prepara_piano,
)
from .admin_schema import NOMI_TAB_AMMINISTRATIVE, crea_schema_amministrativo
from .google_preflight_cli import run as esegui_preflight
from .google_runtime import (
    MAPPATURA_OPERATIVO_REALE,
    ConfigurazioneRisorseGoogle,
    costruisci_componenti_google,
    costruisci_servizio_sheets,
    leggi_matrice_config,
)
from .monitoring import sanitizza_messaggio
from .notifications_sheets import (
    ArchivioNotificheGoogleSheets,
    TrasportoNotificheGoogleApi,
)
from .orchestrator import ModalitaEsecuzione, OrchestratoreReminder
from .persistent_registry import RegistroPersistente
from .registry import StatoNotifica
from .registry_probe_cli import run as esegui_collaudo_registro
from .runtime_config import carica_configurazione
from .smtp_transport import ConfigurazioneSmtp, TrasportoSmtpMdaemon


class ErroreCliRuntime(RuntimeError):
    """Configurazione o comando operativo non valido."""


def _data(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("usa il formato YYYY-MM-DD") from exc


def _intero_positivo(value: str) -> int:
    try:
        risultato = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("deve essere un intero") from exc
    if risultato < 1:
        raise argparse.ArgumentTypeError("deve essere almeno 1")
    return risultato


def _aggiungi_data(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--today", type=_data, default=date.today())


def _aggiungi_conferma_email(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--confirm-email-delivery",
        action="store_true",
        help="conferma esplicita richiesta per qualsiasi invio SMTP",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="reminder-certificati",
        description="Gestione del reminder certificati con un solo comando.",
    )
    sub = parser.add_subparsers(dest="comando", required=True)

    inizializza = sub.add_parser(
        "init-admin",
        help="inizializza un file vuoto già creato e condiviso dall'utente",
    )
    inizializza.add_argument("--spreadsheet-id", required=True)

    migra = sub.add_parser(
        "migrate-admin",
        help="mostra o applica la migrazione controllata dello schema amministrativo",
    )
    migra.add_argument("--spreadsheet-id", required=True)
    migra.add_argument("--apply", action="store_true")
    migra.add_argument("--confirm-migration", action="store_true")
    migra.add_argument(
        "--backup-path",
        default="admin-migration-backup.json",
        help="file JSON locale scritto prima di ogni migrazione applicata",
    )

    sub.add_parser(
        "preflight",
        help="verifica file, tab, intestazioni e CONFIG senza leggere righe operative",
    )

    registro = sub.add_parser(
        "registry-check",
        help="collauda NOTIFICHE con una sola riga sintetica",
    )
    registro.add_argument("--confirm-synthetic-write", action="store_true")

    revisione = sub.add_parser(
        "review-registry",
        help="mostra conteggi aggregati degli stati che richiedono attenzione",
    )
    revisione.add_argument(
        "--stale-hours",
        type=_intero_positivo,
        default=24,
        help="età minima di una riga SENDING da considerare bloccata",
    )

    dry_run = sub.add_parser("dry-run", help="esegue il flusso senza inviare email")
    _aggiungi_data(dry_run)

    test_smtp = sub.add_parser(
        "test-smtp",
        help="invia al massimo una email al destinatario override",
    )
    _aggiungi_data(test_smtp)
    _aggiungi_conferma_email(test_smtp)

    produzione = sub.add_parser(
        "produzione",
        help="esegue gli invii reali protetti",
    )
    _aggiungi_data(produzione)
    _aggiungi_conferma_email(produzione)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.comando == "init-admin":
            return _init_admin(args.spreadsheet_id)
        if args.comando == "migrate-admin":
            return _migrate_admin(
                spreadsheet_id=args.spreadsheet_id,
                applica=bool(args.apply),
                conferma=bool(args.confirm_migration),
                backup_path=Path(args.backup_path),
            )
        if args.comando == "preflight":
            return esegui_preflight(os.environ)
        if args.comando == "registry-check":
            return esegui_collaudo_registro(
                conferma=bool(args.confirm_synthetic_write),
                ambiente=os.environ,
            )
        if args.comando == "review-registry":
            return _review_registry(
                ambiente=os.environ,
                stale_hours=args.stale_hours,
            )
        modalita = {
            "dry-run": ModalitaEsecuzione.DRY_RUN,
            "test-smtp": ModalitaEsecuzione.TEST_SMTP,
            "produzione": ModalitaEsecuzione.PRODUZIONE,
        }[args.comando]
        return _run(
            modalita=modalita,
            oggi=args.today,
            conferma_email=bool(getattr(args, "confirm_email_delivery", False)),
            ambiente=os.environ,
        )
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
    _stampa(
        {
            "operation": "init-admin",
            "tabs_configured": esito.tab_configurate,
            "initialized_tabs": list(esito.tab_inizializzate),
            "already_compliant_tabs": list(esito.tab_gia_conformi),
            "contains_personal_data": False,
            "email_delivery_enabled": False,
        }
    )
    return 0


def _migrate_admin(
    *,
    spreadsheet_id: str,
    applica: bool,
    conferma: bool,
    backup_path: Path,
) -> int:
    identificativo = spreadsheet_id.strip()
    if not identificativo:
        raise ErroreCliRuntime("spreadsheet_id mancante")
    servizio = costruisci_servizio_sheets()
    trasporto = TrasportoMigrazioneGoogleApi(servizio)
    piano = prepara_piano(
        trasporto.leggi_valori(
            spreadsheet_id=identificativo,
            intervallo_a1="'CONFIG'!A:E",
        ),
        trasporto.leggi_valori(
            spreadsheet_id=identificativo,
            intervallo_a1="'NOTIFICHE'!A:N",
        ),
    )
    if applica:
        if not conferma:
            raise ErroreCliRuntime(
                "--apply richiede anche --confirm-migration"
            )
        piano.salva_backup(backup_path)
        applica_piano(
            piano,
            trasporto=trasporto,
            spreadsheet_id=identificativo,
        )
    _stampa(
        {
            "operation": "migrate-admin",
            "mode": "APPLY" if applica else "PREVIEW",
            "migration_required": piano.necessaria,
            "changes": list(piano.modifiche),
            "config_rows_after": max(0, len(piano.config_dopo) - 1),
            "notification_rows_after": max(0, len(piano.notifiche_dopo) - 1),
            "backup_written": applica,
            "backup_path": str(backup_path) if applica else "",
            "automation_enabled_after": False,
            "real_delivery_enabled_after": False,
            "pii_in_output": False,
        }
    )
    return 0


def _review_registry(
    *,
    ambiente: Mapping[str, str],
    stale_hours: int,
) -> int:
    risorse = ConfigurazioneRisorseGoogle.da_ambiente(
        ambiente,
        richiedi_operativo=False,
    )
    servizio = costruisci_servizio_sheets()
    archivio = ArchivioNotificheGoogleSheets(
        trasporto=TrasportoNotificheGoogleApi(servizio),
        spreadsheet_id=risorse.admin_spreadsheet_id,
    )
    registro = RegistroPersistente(archivio, versione_app=_versione())
    righe = registro.elenca()
    conteggi = Counter(riga.stato.value for riga in righe)
    soglia = datetime.now(timezone.utc) - timedelta(hours=stale_hours)
    sending_vecchi = sum(
        1
        for riga in righe
        if riga.stato is StatoNotifica.SENDING and riga.aggiornato_il <= soglia
    )
    retry_esauriti = sum(1 for riga in righe if registro.tentativi_esauriti(riga))
    _stampa(
        {
            "operation": "review-registry",
            "row_count": len(righe),
            "state_counts": dict(sorted(conteggi.items())),
            "stale_sending_count": sending_vecchi,
            "retry_exhausted_count": retry_esauriti,
            "permanent_failure_count": conteggi.get(
                StatoNotifica.FAILED_PERMANENT.value, 0
            ),
            "uncertain_outcome_count": conteggi.get(
                StatoNotifica.UNKNOWN_REVIEW_REQUIRED.value, 0
            ),
            "pii_in_output": False,
        }
    )
    return 2 if sending_vecchi or retry_esauriti or conteggi.get(
        StatoNotifica.UNKNOWN_REVIEW_REQUIRED.value, 0
    ) else 0


def _run(
    *,
    modalita: ModalitaEsecuzione,
    oggi: date,
    conferma_email: bool,
    ambiente: Mapping[str, str],
) -> int:
    risorse = ConfigurazioneRisorseGoogle.da_ambiente(ambiente)
    servizio = costruisci_servizio_sheets()
    componenti = costruisci_componenti_google(servizio=servizio, risorse=risorse)

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

    consenso = False
    trasporto = None
    if configurazione.automazione_attiva:
        consenso = _consenso_esterno(
            modalita,
            flag_cli=conferma_email,
            ambiente=ambiente,
        )
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
        oggi=oggi,
        modalita=modalita,
        consenso_esterno_invio=consenso,
    )
    _stampa(
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
        }
    )
    return {
        "ATTENZIONE": 3,
        "REVISIONE_RICHIESTA": 4,
        "ERRORE": 2,
    }.get(esito.stato, 0)


def _verifica_struttura_admin(
    trasporto: TrasportoStrutturaSheets,
    *,
    spreadsheet_id: str,
) -> None:
    identificativo = spreadsheet_id.strip()
    if not identificativo:
        raise ErroreCliRuntime("ADMIN_SPREADSHEET_ID mancante")
    nomi = tuple(
        str(nome).strip()
        for nome in trasporto.elenca_tab(spreadsheet_id=identificativo)
    )
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


def _stampa(payload: Mapping[str, object]) -> None:
    print(json.dumps(dict(payload), ensure_ascii=False, indent=2))


def _versione() -> str:
    try:
        return version("reminder-scadenza-certificato")
    except Exception:
        return "0+unknown"


if __name__ == "__main__":
    raise SystemExit(main())
