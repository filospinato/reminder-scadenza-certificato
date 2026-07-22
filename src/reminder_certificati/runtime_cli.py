"""CLI unica con poche operazioni comprensibili e default sicuri."""

from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
from importlib.metadata import version
from pathlib import Path
from typing import Any, Mapping, Sequence
from zoneinfo import ZoneInfo

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
from .admin_schema import (
    NOMI_TAB_AMMINISTRATIVE,
    VERSIONE_SCHEMA_AMMINISTRATIVO,
    crea_schema_amministrativo,
)
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


FUSO_ORARIO_OPERATIVO = ZoneInfo("Europe/Rome")


def _data(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("usa il formato YYYY-MM-DD") from exc


def _limite_invii(value: str) -> int:
    try:
        limite = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("usa un intero tra 1 e 10") from exc
    if not 1 <= limite <= 10:
        raise argparse.ArgumentTypeError("usa un intero tra 1 e 10")
    return limite


def _aggiungi_data_tecnica(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--today",
        type=_data,
        default=_oggi_operativo(),
        help=argparse.SUPPRESS,
    )


def _oggi_operativo(ora: datetime | None = None) -> date:
    istante = ora or datetime.now(timezone.utc)
    if istante.tzinfo is None or istante.utcoffset() is None:
        raise ValueError("ora deve includere il fuso orario")
    return istante.astimezone(FUSO_ORARIO_OPERATIVO).date()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="reminder-certificati",
        description="Gestione semplice del reminder certificati.",
    )
    sub = parser.add_subparsers(dest="comando", required=True)

    setup = sub.add_parser(
        "setup-admin",
        help="controlla o prepara automaticamente il foglio amministrativo",
    )
    setup.add_argument("--spreadsheet-id", required=True)
    setup.add_argument(
        "--apply",
        action="store_true",
        help="applica inizializzazione o aggiornamento; senza il flag mostra l'anteprima",
    )
    setup.add_argument(
        "--backup-path",
        default="admin-migration-backup.json",
        help="backup JSON creato automaticamente prima di aggiornare un foglio esistente",
    )

    controllo = sub.add_parser(
        "check",
        help="controlla configurazione, dati e registro senza inviare email",
    )
    _aggiungi_data_tecnica(controllo)

    sub.add_parser(
        "registry-check",
        help="collauda NOTIFICHE con una sola riga interamente sintetica",
    )

    test_smtp = sub.add_parser(
        "test-smtp",
        help="invia al massimo una email al DESTINATARIO_OVERRIDE",
    )
    _aggiungi_data_tecnica(test_smtp)

    produzione = sub.add_parser(
        "produzione",
        help="esegue gli invii reali se INVIO_AUTOMATICO_ATTIVO è true",
    )
    _aggiungi_data_tecnica(produzione)
    produzione.add_argument(
        "--max-sends",
        type=_limite_invii,
        default=None,
        help="limita questa esecuzione a 1-10 invii reali (default interno: 10)",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.comando == "setup-admin":
            return _setup_admin(
                spreadsheet_id=args.spreadsheet_id,
                applica=bool(args.apply),
                backup_path=Path(args.backup_path),
            )
        if args.comando == "check":
            return _check(oggi=args.today, ambiente=os.environ)
        if args.comando == "registry-check":
            return esegui_collaudo_registro(ambiente=os.environ)
        modalita = {
            "test-smtp": ModalitaEsecuzione.TEST_SMTP,
            "produzione": ModalitaEsecuzione.PRODUZIONE,
        }[args.comando]
        return _run(
            modalita=modalita,
            oggi=args.today,
            ambiente=os.environ,
            limite_invii=getattr(args, "max_sends", None),
        )
    except Exception as exc:
        dettaglio = sanitizza_messaggio(str(exc))
        raise SystemExit(
            f"Errore operativo: {type(exc).__name__}: {dettaglio}"
        ) from exc


def _setup_admin(
    *,
    spreadsheet_id: str,
    applica: bool,
    backup_path: Path,
) -> int:
    identificativo = spreadsheet_id.strip()
    if not identificativo:
        raise ErroreCliRuntime(
            "crea prima uno Spreadsheet vuoto con l'account umano e passa il suo ID"
        )

    servizio = costruisci_servizio_sheets()
    struttura = TrasportoStrutturaGoogleApi(servizio)
    nomi = tuple(
        str(nome).strip()
        for nome in struttura.elenca_tab(spreadsheet_id=identificativo)
    )

    if len(nomi) == 1:
        nome_iniziale = nomi[0]
        escaped = nome_iniziale.replace("'", "''")
        matrice = struttura.leggi_valori(
            spreadsheet_id=identificativo,
            intervallo_a1=f"'{escaped}'!A1:ZZ",
        )
        if not _matrice_vuota(matrice):
            raise ErroreCliRuntime(
                "la singola tab iniziale contiene dati; nessuna modifica automatica è sicura"
            )
        esito = None
        if applica:
            esito = InizializzatoreFoglioAmministrativo(struttura).prepara(
                spreadsheet_id=identificativo
            )
        _stampa(
            {
                "operation": "setup-admin",
                "mode": "APPLY" if applica else "PREVIEW",
                "action": "INITIALIZE",
                "changes_required": True,
                "changes": [f"ADMIN_SCHEMA_V{VERSIONE_SCHEMA_AMMINISTRATIVO}"],
                "tabs_configured": bool(esito and esito.tab_configurate),
                "initialized_tabs": list(esito.tab_inizializzate) if esito else [],
                "backup_written": False,
                "automatic_delivery_enabled_after": False,
                "pii_in_output": False,
            }
        )
        return 0

    if len(nomi) != len(NOMI_TAB_AMMINISTRATIVE) or set(nomi) != set(
        NOMI_TAB_AMMINISTRATIVE
    ):
        raise ErroreCliRuntime("tab amministrative mancanti o non conformi")

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
        trasporto.leggi_valori(
            spreadsheet_id=identificativo,
            intervallo_a1="'DASHBOARD'!A:C",
        ),
    )
    backup_scritto = False
    if applica and piano.necessaria:
        piano.salva_backup(backup_path)
        backup_scritto = True
        applica_piano(
            piano,
            trasporto=trasporto,
            spreadsheet_id=identificativo,
        )

    _stampa(
        {
            "operation": "setup-admin",
            "mode": "APPLY" if applica else "PREVIEW",
            "action": "MIGRATE" if piano.necessaria else "NONE",
            "changes_required": piano.necessaria,
            "changes": list(piano.modifiche),
            "config_rows_after": max(0, len(piano.config_dopo) - 1),
            "notification_rows_after": max(0, len(piano.notifiche_dopo) - 1),
            "dashboard_rows_after": max(0, len(piano.dashboard_dopo) - 1),
            "backup_written": backup_scritto,
            "backup_path": str(backup_path) if backup_scritto else "",
            "automatic_delivery_enabled_after": False if piano.necessaria else None,
            "pii_in_output": False,
        }
    )
    return 0


def _check(*, oggi: date, ambiente: Mapping[str, str]) -> int:
    preflight = esegui_preflight(ambiente)
    if preflight != 0:
        return preflight
    runtime = _run(
        modalita=ModalitaEsecuzione.DRY_RUN,
        oggi=oggi,
        ambiente=ambiente,
    )
    registro = _review_registry(ambiente=ambiente, stale_hours=24)
    return max(runtime, registro)


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
    errori_permanenti = conteggi.get(StatoNotifica.FAILED_PERMANENT.value, 0)
    esiti_incerti = conteggi.get(
        StatoNotifica.UNKNOWN_REVIEW_REQUIRED.value,
        0,
    )
    _stampa(
        {
            "operation": "registry-review",
            "row_count": len(righe),
            "state_counts": {
                _etichetta_stato_notifica(stato): numero
                for stato, numero in sorted(conteggi.items())
            },
            "stale_sending_count": sending_vecchi,
            "retry_exhausted_count": retry_esauriti,
            "permanent_failure_count": errori_permanenti,
            "uncertain_outcome_count": esiti_incerti,
            "pii_in_output": False,
        }
    )
    return (
        2
        if (sending_vecchi or retry_esauriti or errori_permanenti or esiti_incerti)
        else 0
    )


def _run(
    *,
    modalita: ModalitaEsecuzione,
    oggi: date,
    ambiente: Mapping[str, str],
    limite_invii: int | None = None,
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
    if limite_invii is not None:
        if modalita is not ModalitaEsecuzione.PRODUZIONE:
            raise ErroreCliRuntime(
                "il limite esplicito è consentito soltanto in produzione"
            )
        if not 1 <= limite_invii <= configurazione.limite_invii_per_esecuzione:
            raise ErroreCliRuntime(
                "il limite esplicito deve essere compreso tra 1 e il limite interno"
            )
        configurazione = replace(
            configurazione,
            limite_invii_per_esecuzione=limite_invii,
        )

    consenso = modalita is not ModalitaEsecuzione.DRY_RUN
    trasporto = None
    smtp_necessario = modalita is ModalitaEsecuzione.TEST_SMTP or (
        modalita is ModalitaEsecuzione.PRODUZIONE and configurazione.automazione_attiva
    )
    if smtp_necessario:
        trasporto = TrasportoSmtpMdaemon(ConfigurazioneSmtp.da_ambiente(ambiente))

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
            "status_label": _etichetta_stato_sistema(esito.stato),
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


def _matrice_vuota(matrice: Sequence[Sequence[Any]]) -> bool:
    return not any(str(cella).strip() for riga in matrice for cella in riga)


def _etichetta_stato_sistema(stato: str) -> str:
    return {
        "DISATTIVATO": "Invio automatico spento",
        "DRY_RUN_OK": "Controllo completato",
        "OK": "Esecuzione completata",
        "ATTENZIONE": "Attenzione richiesta",
        "REVISIONE_RICHIESTA": "Verifica manuale necessaria",
        "ERRORE": "Errore",
    }.get(stato, stato)


def _etichetta_stato_notifica(stato: str) -> str:
    return {
        "SENDING": "Invio in corso",
        "SENT": "Inviata",
        "FAILED_RETRYABLE": "Da riprovare",
        "FAILED_PERMANENT": "Errore definitivo",
        "UNKNOWN_REVIEW_REQUIRED": "Verifica manuale necessaria",
    }.get(stato, stato)


def _stampa(payload: Mapping[str, object]) -> None:
    print(json.dumps(dict(payload), ensure_ascii=False, indent=2))


def _versione() -> str:
    try:
        return version("reminder-scadenza-certificato")
    except Exception:
        return "0+unknown"


if __name__ == "__main__":
    raise SystemExit(main())
