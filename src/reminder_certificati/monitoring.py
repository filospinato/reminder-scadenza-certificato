"""Monitoraggio runtime con output aggregato e minimizzazione dei dati."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any, Protocol, Sequence

from .admin_schema import COLONNE_ANOMALIE, COLONNE_DASHBOARD


class ErroreMonitoraggio(RuntimeError):
    """Dashboard o anomalie non possono essere persistite in sicurezza."""


class SeveritaAnomalia(StrEnum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass(frozen=True, slots=True)
class MetricheEsecuzione:
    stato_sistema: str
    ultima_esecuzione: datetime | None
    heartbeat: datetime | None
    righe_lette: int = 0
    righe_valide: int = 0
    candidati: int = 0
    notifiche_gia_presenti: int = 0
    invii_tentati: int = 0
    invii_riusciti: int = 0
    invii_falliti: int = 0
    esiti_incerti: int = 0
    anomalie: int = 0
    kill_switch: bool = True
    versione_app: str = ""
    codice_errore: str = ""

    def come_righe(self) -> tuple[tuple[str, str, str], ...]:
        return (
            ("stato_sistema", self.stato_sistema, "Stato operativo complessivo."),
            ("ultima_esecuzione", _istante_opzionale(self.ultima_esecuzione), "Ultima esecuzione conclusa in UTC."),
            ("heartbeat", _istante_opzionale(self.heartbeat), "Ultimo segnale di vita in UTC."),
            ("righe_lette", str(self.righe_lette), "Righe lette dalla sorgente."),
            ("righe_valide", str(self.righe_valide), "Righe valide dopo i controlli."),
            ("candidati", str(self.candidati), "Promemoria candidati nella finestra."),
            ("notifiche_gia_presenti", str(self.notifiche_gia_presenti), "Notifiche saltate perché già registrate."),
            ("invii_tentati", str(self.invii_tentati), "Invii passati al trasporto SMTP."),
            ("invii_riusciti", str(self.invii_riusciti), "Invii confermati."),
            ("invii_falliti", str(self.invii_falliti), "Invii falliti in modo classificato."),
            ("esiti_incerti", str(self.esiti_incerti), "Esiti che richiedono revisione umana."),
            ("anomalie", str(self.anomalie), "Anomalie rilevate."),
            ("kill_switch", "ATTIVO" if self.kill_switch else "DISATTIVO", "Stato del blocco operativo."),
            ("versione_app", self.versione_app, "Versione del programma."),
            ("codice_errore", self.codice_errore, "Codice sintetico dell'eventuale errore fatale."),
        )


@dataclass(frozen=True, slots=True)
class AnomaliaRuntime:
    anomalia_id: str
    rilevata_il: datetime
    severita: SeveritaAnomalia
    origine: str
    codice: str
    riga_sorgente: int | None
    campo: str | None
    messaggio: str
    versione_app: str
    risolta_il: datetime | None = None

    @classmethod
    def crea(
        cls,
        *,
        severita: SeveritaAnomalia,
        origine: str,
        codice: str,
        messaggio: str,
        versione_app: str,
        riga_sorgente: int | None = None,
        campo: str | None = None,
        rilevata_il: datetime | None = None,
    ) -> "AnomaliaRuntime":
        istante = _utc(rilevata_il or datetime.now(timezone.utc))
        origine_sicura = _testo_breve(origine, "origine", 80)
        codice_sicuro = _testo_breve(codice, "codice", 80)
        campo_sicuro = _opzionale_breve(campo, 80)
        messaggio_sicuro = sanitizza_messaggio(messaggio)
        materiale = "|".join(
            (
                origine_sicura,
                codice_sicuro,
                str(riga_sorgente or ""),
                campo_sicuro or "",
                messaggio_sicuro,
            )
        )
        digest = hashlib.sha256(materiale.encode("utf-8")).hexdigest()[:20]
        return cls(
            anomalia_id=f"ANOM-{digest}",
            rilevata_il=istante,
            severita=severita,
            origine=origine_sicura,
            codice=codice_sicuro,
            riga_sorgente=riga_sorgente,
            campo=campo_sicuro,
            messaggio=messaggio_sicuro,
            versione_app=_testo_breve(versione_app, "versione_app", 40),
        )

    def come_riga(self) -> tuple[str, ...]:
        return (
            self.anomalia_id,
            self.rilevata_il.isoformat(),
            self.severita.value,
            self.origine,
            self.codice,
            "" if self.riga_sorgente is None else str(self.riga_sorgente),
            self.campo or "",
            self.messaggio,
            self.versione_app,
            _istante_opzionale(self.risolta_il),
        )


class ArchivioDashboard(Protocol):
    def aggiorna(self, metriche: MetricheEsecuzione) -> None:
        """Sostituisce la fotografia aggregata della dashboard."""


class ArchivioAnomalie(Protocol):
    def registra(self, anomalia: AnomaliaRuntime) -> None:
        """Registra una nuova anomalia."""


@dataclass(slots=True)
class DashboardMemoria:
    ultima: MetricheEsecuzione | None = None

    def aggiorna(self, metriche: MetricheEsecuzione) -> None:
        self.ultima = metriche


@dataclass(slots=True)
class AnomalieMemoria:
    righe: dict[str, AnomaliaRuntime] = field(default_factory=dict)

    def registra(self, anomalia: AnomaliaRuntime) -> None:
        precedente = self.righe.get(anomalia.anomalia_id)
        if precedente is not None and precedente.risolta_il is None:
            return
        self.righe[anomalia.anomalia_id] = anomalia

    def snapshot(self) -> tuple[AnomaliaRuntime, ...]:
        return tuple(self.righe[chiave] for chiave in sorted(self.righe))


class TrasportoMonitoraggioSheets(Protocol):
    def sostituisci_valori(
        self,
        *,
        spreadsheet_id: str,
        intervallo_a1: str,
        valori: Sequence[Sequence[Any]],
    ) -> None:
        """Scrive la fotografia completa con valueInputOption RAW."""

    def aggiungi_riga(
        self,
        *,
        spreadsheet_id: str,
        intervallo_a1: str,
        valori: Sequence[Any],
    ) -> None:
        """Accoda una riga con valueInputOption RAW."""


@dataclass(frozen=True, slots=True)
class DashboardGoogleSheets:
    trasporto: TrasportoMonitoraggioSheets
    spreadsheet_id: str
    nome_scheda: str = "DASHBOARD"

    def aggiorna(self, metriche: MetricheEsecuzione) -> None:
        identificativo = self.spreadsheet_id.strip()
        if not identificativo:
            raise ErroreMonitoraggio("DASHBOARD: spreadsheet_id mancante")
        valori = [list(COLONNE_DASHBOARD), *[list(riga) for riga in metriche.come_righe()]]
        try:
            self.trasporto.sostituisci_valori(
                spreadsheet_id=identificativo,
                intervallo_a1=f"'{_escape(self.nome_scheda)}'!A1:C",
                valori=valori,
            )
        except Exception as exc:
            raise ErroreMonitoraggio(
                f"DASHBOARD: scrittura non riuscita: {type(exc).__name__}"
            ) from exc


@dataclass(frozen=True, slots=True)
class AnomalieGoogleSheets:
    trasporto: TrasportoMonitoraggioSheets
    spreadsheet_id: str
    nome_scheda: str = "ANOMALIE"

    def registra(self, anomalia: AnomaliaRuntime) -> None:
        identificativo = self.spreadsheet_id.strip()
        if not identificativo:
            raise ErroreMonitoraggio("ANOMALIE: spreadsheet_id mancante")
        try:
            self.trasporto.aggiungi_riga(
                spreadsheet_id=identificativo,
                intervallo_a1=f"'{_escape(self.nome_scheda)}'!A:J",
                valori=anomalia.come_riga(),
            )
        except Exception as exc:
            raise ErroreMonitoraggio(
                f"ANOMALIE: scrittura non riuscita: {type(exc).__name__}"
            ) from exc


@dataclass(frozen=True, slots=True)
class TrasportoMonitoraggioGoogleApi:
    servizio: Any

    def sostituisci_valori(
        self,
        *,
        spreadsheet_id: str,
        intervallo_a1: str,
        valori: Sequence[Sequence[Any]],
    ) -> None:
        # Il numero delle metriche è stabile. Un singolo update evita che un
        # errore tra clear e update lasci la dashboard completamente vuota.
        self.servizio.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=intervallo_a1,
            valueInputOption="RAW",
            body={"majorDimension": "ROWS", "values": [list(riga) for riga in valori]},
        ).execute()

    def aggiungi_riga(
        self,
        *,
        spreadsheet_id: str,
        intervallo_a1: str,
        valori: Sequence[Any],
    ) -> None:
        self.servizio.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range=intervallo_a1,
            valueInputOption="RAW",
            insertDataOption="INSERT_ROWS",
            body={"majorDimension": "ROWS", "values": [list(valori)]},
        ).execute()


_EMAIL_RE = re.compile(r"(?i)\b[^\s@]+@[^\s@]+\.[^\s@]+\b")
_TOKEN_RE = re.compile(r"(?i)\b(?:ya29\.|gh[ps]_|sk-|eyJ)[A-Za-z0-9._-]+")
_NOTIFICATION_ID_RE = re.compile(
    r"(?i)(?<!\S)[^|\s]+\|\d{4}-\d{2}-\d{2}\|(?:TEST_)?REMINDER_\d+(?!\S)"
)


def sanitizza_messaggio(value: str) -> str:
    testo = str(value).replace("\r", " ").replace("\n", " ")
    testo = _EMAIL_RE.sub("[email-rimossa]", testo)
    testo = _TOKEN_RE.sub("[token-rimosso]", testo)
    testo = _NOTIFICATION_ID_RE.sub("[notification-id-rimosso]", testo)
    testo = re.sub(r"\s+", " ", testo).strip()
    if not testo:
        return "dettaglio non disponibile"
    return testo[:500]


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("il timestamp deve includere il fuso orario")
    return value.astimezone(timezone.utc)


def _istante_opzionale(value: datetime | None) -> str:
    return "" if value is None else _utc(value).isoformat()


def _testo_breve(value: str, campo: str, massimo: int) -> str:
    normalizzato = str(value).strip()
    if not normalizzato:
        raise ValueError(f"{campo} non può essere vuoto")
    return normalizzato[:massimo]


def _opzionale_breve(value: str | None, massimo: int) -> str | None:
    if value is None:
        return None
    normalizzato = str(value).strip()
    return normalizzato[:massimo] or None


def _escape(nome: str) -> str:
    normalizzato = nome.strip()
    if not normalizzato:
        raise ErroreMonitoraggio("nome scheda mancante")
    return normalizzato.replace("'", "''")
