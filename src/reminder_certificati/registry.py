from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from enum import StrEnum
from threading import Lock


class StatoNotifica(StrEnum):
    """Stati persistibili del ciclo di vita di una notifica."""

    SENDING = "SENDING"
    SENT = "SENT"
    FAILED_RETRYABLE = "FAILED_RETRYABLE"
    UNKNOWN_REVIEW_REQUIRED = "UNKNOWN_REVIEW_REQUIRED"


class ErroreRegistro(RuntimeError):
    """Errore base del registro delle notifiche."""


class NotificaNonPrenotabile(ErroreRegistro):
    """La notifica non può essere prenotata senza rischiare un duplicato."""


class TransizioneRegistroNonValida(ErroreRegistro):
    """La transizione richiesta non rispetta il ciclo di vita previsto."""


@dataclass(frozen=True, slots=True)
class RecordNotifica:
    notification_id: str
    stato: StatoNotifica
    tentativi: int
    creato_il: datetime
    aggiornato_il: datetime
    message_id: str | None = None
    errore: str | None = None


def _notification_id(value: str) -> str:
    normalizzato = value.strip()
    if not normalizzato:
        raise ValueError("notification_id non può essere vuoto")
    return normalizzato


def _istante(value: datetime | None) -> datetime:
    risultato = value or datetime.now(timezone.utc)
    if risultato.tzinfo is None or risultato.utcoffset() is None:
        raise ValueError("l'istante deve includere il fuso orario")
    return risultato.astimezone(timezone.utc)


def _dettaglio(value: str, *, campo: str) -> str:
    normalizzato = value.strip()
    if not normalizzato:
        raise ValueError(f"{campo} non può essere vuoto")
    return normalizzato[:1000]


class RegistroMemoria:
    """Registro atomico in memoria usato da dominio, test e dry-run.

    La futura implementazione Google Sheets dovrà rispettare lo stesso contratto.
    Una prenotazione crea `SENDING` prima dell'invio. Soltanto un errore dichiarato
    retryable può tornare automaticamente a `SENDING`; `SENT`, `SENDING` e
    `UNKNOWN_REVIEW_REQUIRED` bloccano nuove prenotazioni.
    """

    def __init__(self) -> None:
        self._records: dict[str, RecordNotifica] = {}
        self._lock = Lock()

    def ottieni(self, notification_id: str) -> RecordNotifica | None:
        chiave = _notification_id(notification_id)
        with self._lock:
            return self._records.get(chiave)

    def snapshot(self) -> tuple[RecordNotifica, ...]:
        with self._lock:
            return tuple(self._records[chiave] for chiave in sorted(self._records))

    def puo_prenotare(self, notification_id: str) -> bool:
        chiave = _notification_id(notification_id)
        with self._lock:
            record = self._records.get(chiave)
            return record is None or record.stato is StatoNotifica.FAILED_RETRYABLE

    def prenota(
        self,
        notification_id: str,
        *,
        ora: datetime | None = None,
    ) -> RecordNotifica:
        """Crea atomicamente `SENDING` o riprende un errore retryable."""

        chiave = _notification_id(notification_id)
        istante = _istante(ora)
        with self._lock:
            esistente = self._records.get(chiave)
            if esistente is None:
                record = RecordNotifica(
                    notification_id=chiave,
                    stato=StatoNotifica.SENDING,
                    tentativi=1,
                    creato_il=istante,
                    aggiornato_il=istante,
                )
                self._records[chiave] = record
                return record

            if esistente.stato is not StatoNotifica.FAILED_RETRYABLE:
                raise NotificaNonPrenotabile(
                    f"{chiave}: stato {esistente.stato} non prenotabile"
                )

            if istante < esistente.aggiornato_il:
                raise ValueError("l'istante non può precedere l'ultimo aggiornamento")

            record = replace(
                esistente,
                stato=StatoNotifica.SENDING,
                tentativi=esistente.tentativi + 1,
                aggiornato_il=istante,
                message_id=None,
                errore=None,
            )
            self._records[chiave] = record
            return record

    def segna_inviata(
        self,
        notification_id: str,
        *,
        message_id: str,
        ora: datetime | None = None,
    ) -> RecordNotifica:
        return self._da_sending(
            notification_id,
            nuovo_stato=StatoNotifica.SENT,
            ora=ora,
            message_id=_dettaglio(message_id, campo="message_id"),
        )

    def segna_errore_retryable(
        self,
        notification_id: str,
        *,
        errore: str,
        ora: datetime | None = None,
    ) -> RecordNotifica:
        return self._da_sending(
            notification_id,
            nuovo_stato=StatoNotifica.FAILED_RETRYABLE,
            ora=ora,
            errore=_dettaglio(errore, campo="errore"),
        )

    def segna_esito_incerto(
        self,
        notification_id: str,
        *,
        errore: str,
        ora: datetime | None = None,
    ) -> RecordNotifica:
        return self._da_sending(
            notification_id,
            nuovo_stato=StatoNotifica.UNKNOWN_REVIEW_REQUIRED,
            ora=ora,
            errore=_dettaglio(errore, campo="errore"),
        )

    def _da_sending(
        self,
        notification_id: str,
        *,
        nuovo_stato: StatoNotifica,
        ora: datetime | None,
        message_id: str | None = None,
        errore: str | None = None,
    ) -> RecordNotifica:
        chiave = _notification_id(notification_id)
        istante = _istante(ora)
        with self._lock:
            esistente = self._records.get(chiave)
            if esistente is None:
                raise TransizioneRegistroNonValida(f"{chiave}: notifica non registrata")
            if esistente.stato is not StatoNotifica.SENDING:
                raise TransizioneRegistroNonValida(
                    f"{chiave}: transizione da {esistente.stato} a {nuovo_stato} non valida"
                )
            if istante < esistente.aggiornato_il:
                raise ValueError("l'istante non può precedere l'ultimo aggiornamento")

            record = replace(
                esistente,
                stato=nuovo_stato,
                aggiornato_il=istante,
                message_id=message_id,
                errore=errore,
            )
            self._records[chiave] = record
            return record
