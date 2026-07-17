"""Ciclo di vita persistente delle notifiche sopra l'archivio tabellare."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol

from .admin_store import RigaNotifica
from .models import CandidatoNotifica
from .registry import RecordNotifica, StatoNotifica


class ErroreRegistroPersistente(RuntimeError):
    """La transizione persistente non è sicura o non è applicabile."""


class ArchivioRigheNotifica(Protocol):
    def ottieni(self, notification_id: str) -> RigaNotifica | None:
        """Restituisce la riga corrente per chiave."""

    def salva(self, riga: RigaNotifica) -> RigaNotifica:
        """Inserisce o aggiorna la riga in modo controllato."""


@dataclass(frozen=True, slots=True)
class RegistroPersistente:
    archivio: ArchivioRigheNotifica
    versione_app: str

    def puo_prenotare(self, notification_id: str) -> bool:
        esistente = self.archivio.ottieni(_chiave(notification_id))
        return esistente is None or esistente.stato is StatoNotifica.FAILED_RETRYABLE

    def prenota(
        self,
        candidato: CandidatoNotifica,
        *,
        ora: datetime | None = None,
    ) -> RigaNotifica:
        istante = _istante(ora)
        esistente = self.archivio.ottieni(candidato.notification_id)
        if esistente is None:
            record = RecordNotifica(
                notification_id=candidato.notification_id,
                stato=StatoNotifica.SENDING,
                tentativi=1,
                creato_il=istante,
                aggiornato_il=istante,
            )
            return self.archivio.salva(
                RigaNotifica.da_record(
                    candidato,
                    record,
                    versione_app=self.versione_app,
                )
            )

        if esistente.stato is not StatoNotifica.FAILED_RETRYABLE:
            raise ErroreRegistroPersistente(
                f"{candidato.notification_id}: stato {esistente.stato} non prenotabile"
            )
        if istante < esistente.aggiornato_il:
            raise ErroreRegistroPersistente(
                "l'istante non può precedere l'ultimo aggiornamento"
            )
        _verifica_identita(candidato, esistente)
        record = RecordNotifica(
            notification_id=esistente.notification_id,
            stato=StatoNotifica.SENDING,
            tentativi=esistente.tentativi + 1,
            creato_il=esistente.creato_il,
            aggiornato_il=istante,
        )
        return self.archivio.salva(
            RigaNotifica.da_record(
                candidato,
                record,
                versione_app=self.versione_app,
            )
        )

    def segna_inviata(
        self,
        candidato: CandidatoNotifica,
        *,
        message_id: str,
        ora: datetime | None = None,
    ) -> RigaNotifica:
        return self._transizione(
            candidato,
            nuovo_stato=StatoNotifica.SENT,
            ora=ora,
            message_id=_dettaglio(message_id, "message_id"),
        )

    def segna_errore_retryable(
        self,
        candidato: CandidatoNotifica,
        *,
        errore: str,
        ora: datetime | None = None,
    ) -> RigaNotifica:
        return self._transizione(
            candidato,
            nuovo_stato=StatoNotifica.FAILED_RETRYABLE,
            ora=ora,
            errore=_dettaglio(errore, "errore"),
        )

    def segna_esito_incerto(
        self,
        candidato: CandidatoNotifica,
        *,
        errore: str,
        ora: datetime | None = None,
    ) -> RigaNotifica:
        return self._transizione(
            candidato,
            nuovo_stato=StatoNotifica.UNKNOWN_REVIEW_REQUIRED,
            ora=ora,
            errore=_dettaglio(errore, "errore"),
        )

    def _transizione(
        self,
        candidato: CandidatoNotifica,
        *,
        nuovo_stato: StatoNotifica,
        ora: datetime | None,
        message_id: str | None = None,
        errore: str | None = None,
    ) -> RigaNotifica:
        istante = _istante(ora)
        esistente = self.archivio.ottieni(candidato.notification_id)
        if esistente is None:
            raise ErroreRegistroPersistente("notifica non registrata")
        if esistente.stato is not StatoNotifica.SENDING:
            raise ErroreRegistroPersistente(
                f"transizione da {esistente.stato} a {nuovo_stato} non valida"
            )
        if istante < esistente.aggiornato_il:
            raise ErroreRegistroPersistente(
                "l'istante non può precedere l'ultimo aggiornamento"
            )
        _verifica_identita(candidato, esistente)
        record = RecordNotifica(
            notification_id=esistente.notification_id,
            stato=nuovo_stato,
            tentativi=esistente.tentativi,
            creato_il=esistente.creato_il,
            aggiornato_il=istante,
            message_id=message_id,
            errore=errore,
        )
        return self.archivio.salva(
            RigaNotifica.da_record(
                candidato,
                record,
                versione_app=self.versione_app,
            )
        )


def _verifica_identita(candidato: CandidatoNotifica, riga: RigaNotifica) -> None:
    arbitro = candidato.arbitro
    attuale = (
        arbitro.id_arbitro.strip(),
        arbitro.nome.strip(),
        arbitro.cognome.strip(),
        arbitro.email.strip(),
        arbitro.scadenza_certificato,
        candidato.tipo.strip(),
    )
    persistita = (
        riga.id_arbitro,
        riga.nome,
        riga.cognome,
        riga.email,
        riga.scadenza_certificato,
        riga.tipo,
    )
    if attuale != persistita:
        raise ErroreRegistroPersistente(
            "la notifica esistente non coincide con i dati correnti della stessa riga"
        )


def _istante(value: datetime | None) -> datetime:
    risultato = value or datetime.now(timezone.utc)
    if risultato.tzinfo is None or risultato.utcoffset() is None:
        raise ValueError("l'istante deve includere il fuso orario")
    return risultato.astimezone(timezone.utc)


def _chiave(value: str) -> str:
    normalizzato = value.strip()
    if not normalizzato:
        raise ValueError("notification_id non può essere vuoto")
    return normalizzato


def _dettaglio(value: str, campo: str) -> str:
    normalizzato = value.strip()
    if not normalizzato:
        raise ValueError(f"{campo} non può essere vuoto")
    return normalizzato[:1000]
