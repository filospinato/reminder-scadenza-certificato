from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from threading import Lock
from typing import Iterable, Mapping

from .models import CandidatoNotifica
from .registry import RecordNotifica, StatoNotifica

COLONNE_NOTIFICHE: tuple[str, ...] = (
    "notification_id",
    "id_arbitro",
    "scadenza_certificato",
    "tipo",
    "stato",
    "tentativi",
    "creato_il",
    "aggiornato_il",
    "message_id",
    "versione_app",
    "errore",
)


class ErroreArchivioNotifiche(RuntimeError):
    """Il contenuto della tab NOTIFICHE è incoerente o ambiguo."""


@dataclass(frozen=True, slots=True)
class RigaNotifica:
    notification_id: str
    id_arbitro: str
    scadenza_certificato: date
    tipo: str
    stato: StatoNotifica
    tentativi: int
    creato_il: datetime
    aggiornato_il: datetime
    message_id: str | None
    versione_app: str
    errore: str | None

    @classmethod
    def da_record(
        cls,
        candidato: CandidatoNotifica,
        record: RecordNotifica,
        *,
        versione_app: str,
    ) -> "RigaNotifica":
        if candidato.notification_id != record.notification_id:
            raise ValueError("candidato e record hanno notification_id differenti")
        arbitro = candidato.arbitro
        return cls(
            notification_id=record.notification_id,
            id_arbitro=arbitro.id_arbitro.strip(),
            scadenza_certificato=arbitro.scadenza_certificato,
            tipo=candidato.tipo.strip(),
            stato=record.stato,
            tentativi=record.tentativi,
            creato_il=_utc(record.creato_il),
            aggiornato_il=_utc(record.aggiornato_il),
            message_id=_opzionale(record.message_id),
            versione_app=_obbligatorio(versione_app, "versione_app"),
            errore=_opzionale(record.errore),
        )

    def come_mappa(self) -> dict[str, str]:
        return {
            "notification_id": self.notification_id,
            "id_arbitro": self.id_arbitro,
            "scadenza_certificato": self.scadenza_certificato.isoformat(),
            "tipo": self.tipo,
            "stato": self.stato.value,
            "tentativi": str(self.tentativi),
            "creato_il": self.creato_il.isoformat(),
            "aggiornato_il": self.aggiornato_il.isoformat(),
            "message_id": self.message_id or "",
            "versione_app": self.versione_app,
            "errore": self.errore or "",
        }

    @classmethod
    def da_mappa(cls, valori: Mapping[str, object]) -> "RigaNotifica":
        mancanti = [campo for campo in COLONNE_NOTIFICHE if campo not in valori]
        if mancanti:
            raise ErroreArchivioNotifiche(
                "colonne NOTIFICHE mancanti: " + ", ".join(mancanti)
            )
        try:
            tentativi = int(_testo(valori["tentativi"]))
            if tentativi < 1:
                raise ValueError("tentativi deve essere almeno 1")
            return cls(
                notification_id=_obbligatorio(valori["notification_id"], "notification_id"),
                id_arbitro=_obbligatorio(valori["id_arbitro"], "id_arbitro"),
                scadenza_certificato=date.fromisoformat(
                    _obbligatorio(
                        valori["scadenza_certificato"], "scadenza_certificato"
                    )
                ),
                tipo=_obbligatorio(valori["tipo"], "tipo"),
                stato=StatoNotifica(_obbligatorio(valori["stato"], "stato")),
                tentativi=tentativi,
                creato_il=_parse_istante(valori["creato_il"]),
                aggiornato_il=_parse_istante(valori["aggiornato_il"]),
                message_id=_opzionale(valori["message_id"]),
                versione_app=_obbligatorio(valori["versione_app"], "versione_app"),
                errore=_opzionale(valori["errore"]),
            )
        except (TypeError, ValueError) as exc:
            raise ErroreArchivioNotifiche(f"riga NOTIFICHE non valida: {exc}") from exc


class ArchivioNotificheMemoria:
    """Fake thread-safe della tab NOTIFICHE."""

    def __init__(self, righe: Iterable[RigaNotifica] = ()) -> None:
        self._lock = Lock()
        self._righe: dict[str, RigaNotifica] = {}
        for riga in righe:
            if riga.notification_id in self._righe:
                raise ErroreArchivioNotifiche(
                    f"notification_id duplicato: {riga.notification_id}"
                )
            self._righe[riga.notification_id] = riga

    def ottieni(self, notification_id: str) -> RigaNotifica | None:
        chiave = _obbligatorio(notification_id, "notification_id")
        with self._lock:
            return self._righe.get(chiave)

    def salva(self, riga: RigaNotifica) -> RigaNotifica:
        with self._lock:
            precedente = self._righe.get(riga.notification_id)
            if precedente and riga.creato_il != precedente.creato_il:
                raise ErroreArchivioNotifiche(
                    "creato_il non può cambiare durante una transizione"
                )
            if precedente and riga.aggiornato_il < precedente.aggiornato_il:
                raise ErroreArchivioNotifiche(
                    "aggiornato_il non può precedere la versione persistita"
                )
            self._righe[riga.notification_id] = riga
            return riga

    def elenca(self) -> tuple[RigaNotifica, ...]:
        with self._lock:
            return tuple(self._righe[chiave] for chiave in sorted(self._righe))

    def snapshot(self) -> tuple[RigaNotifica, ...]:
        return self.elenca()


def _testo(value: object) -> str:
    return "" if value is None else str(value).strip()


def _obbligatorio(value: object, campo: str) -> str:
    testo = _testo(value)
    if not testo:
        raise ValueError(f"{campo} non può essere vuoto")
    return testo


def _opzionale(value: object) -> str | None:
    return _testo(value) or None


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("i timestamp devono includere il fuso orario")
    return value.astimezone(timezone.utc)


def _parse_istante(value: object) -> datetime:
    return _utc(datetime.fromisoformat(_obbligatorio(value, "timestamp")))
