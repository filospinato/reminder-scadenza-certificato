from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class StatoNotifica(StrEnum):
    """Stati persistibili del ciclo di vita di una notifica."""

    SENDING = "SENDING"
    SENT = "SENT"
    FAILED_RETRYABLE = "FAILED_RETRYABLE"
    FAILED_PERMANENT = "FAILED_PERMANENT"
    UNKNOWN_REVIEW_REQUIRED = "UNKNOWN_REVIEW_REQUIRED"


@dataclass(frozen=True, slots=True)
class RecordNotifica:
    """Stato serializzabile usato dall'unico registro applicativo persistente."""

    notification_id: str
    stato: StatoNotifica
    tentativi: int
    creato_il: datetime
    aggiornato_il: datetime
    message_id: str | None = None
    errore: str | None = None
