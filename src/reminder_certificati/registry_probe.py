from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Callable, Protocol
from uuid import uuid4

from .admin_store import RigaNotifica
from .models import Arbitro, CandidatoNotifica
from .registry import RecordNotifica, StatoNotifica


class ArchivioNotificheProbe(Protocol):
    def ottieni(self, notification_id: str) -> RigaNotifica | None: ...

    def salva(self, riga: RigaNotifica) -> RigaNotifica: ...


@dataclass(frozen=True, slots=True)
class EsitoCollaudoRegistro:
    append_verificato: bool
    rilettura_verificata: bool
    update_verificato: bool
    una_sola_chiave_verificata: bool
    stato_finale: StatoNotifica


def esegui_collaudo_registro_sintetico(
    archivio: ArchivioNotificheProbe,
    *,
    versione_app: str,
    ora: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    genera_id: Callable[[], str] = lambda: uuid4().hex,
) -> EsitoCollaudoRegistro:
    """Verifica append, rilettura e update usando esclusivamente dati sintetici."""

    istante = _utc(ora())
    suffisso = genera_id().strip()
    if not suffisso or not suffisso.replace("-", "").isalnum():
        raise ValueError("identificativo sintetico non valido")

    id_arbitro = f"SYNTHETIC-REGISTRY-{suffisso}"
    tipo = "SYNTHETIC_REGISTRY_CHECK"
    notification_id = f"{id_arbitro}|2099-12-31|{tipo}"
    candidato = CandidatoNotifica(
        arbitro=Arbitro(
            id_arbitro=id_arbitro,
            nome="Synthetic",
            cognome="Registry Check",
            email="synthetic@example.invalid",
            scadenza_certificato=date(2099, 12, 31),
        ),
        tipo=tipo,
        giorni_residui=0,
        notification_id=notification_id,
    )

    if archivio.ottieni(notification_id) is not None:
        raise RuntimeError("chiave sintetica già presente")

    prenotazione = RigaNotifica.da_record(
        candidato,
        RecordNotifica(
            notification_id=notification_id,
            stato=StatoNotifica.SENDING,
            tentativi=1,
            creato_il=istante,
            aggiornato_il=istante,
        ),
        versione_app=versione_app,
    )
    archivio.salva(prenotazione)

    riletta = archivio.ottieni(notification_id)
    if riletta is None or riletta.stato is not StatoNotifica.SENDING:
        raise RuntimeError("rilettura della prenotazione sintetica non riuscita")

    conclusa = RigaNotifica.da_record(
        candidato,
        RecordNotifica(
            notification_id=notification_id,
            stato=StatoNotifica.SENT,
            tentativi=1,
            creato_il=istante,
            aggiornato_il=istante,
            message_id="<synthetic-registry-check@example.invalid>",
        ),
        versione_app=versione_app,
    )
    archivio.salva(conclusa)

    finale = archivio.ottieni(notification_id)
    if finale is None or finale.stato is not StatoNotifica.SENT:
        raise RuntimeError("aggiornamento sintetico del registro non riuscito")
    if finale.message_id != "<synthetic-registry-check@example.invalid>":
        raise RuntimeError("Message-ID sintetico non conservato")

    return EsitoCollaudoRegistro(
        append_verificato=True,
        rilettura_verificata=True,
        update_verificato=True,
        una_sola_chiave_verificata=True,
        stato_finale=finale.stato,
    )


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("il timestamp del collaudo deve includere il fuso orario")
    return value.astimezone(timezone.utc)
