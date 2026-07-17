"""Valutazione deterministica della salute operativa senza servizi esterni."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import StrEnum

from .monitoring import MetricheEsecuzione


class LivelloSalute(StrEnum):
    OK = "OK"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


@dataclass(frozen=True, slots=True)
class SegnaleSalute:
    codice: str
    livello: LivelloSalute
    messaggio: str


@dataclass(frozen=True, slots=True)
class ValutazioneSalute:
    livello: LivelloSalute
    segnali: tuple[SegnaleSalute, ...]


def valuta_salute(
    metriche: MetricheEsecuzione,
    *,
    ora: datetime,
    massimo_silenzio: timedelta = timedelta(hours=36),
) -> ValutazioneSalute:
    corrente = _utc(ora)
    segnali: list[SegnaleSalute] = []

    if metriche.heartbeat is None:
        segnali.append(
            SegnaleSalute(
                "HEARTBEAT_ASSENTE",
                LivelloSalute.WARNING,
                "Il sistema non ha ancora registrato un heartbeat.",
            )
        )
    elif corrente - _utc(metriche.heartbeat) > massimo_silenzio:
        segnali.append(
            SegnaleSalute(
                "HEARTBEAT_SCADUTO",
                LivelloSalute.CRITICAL,
                "L'ultimo heartbeat è oltre la soglia prevista.",
            )
        )

    if metriche.esiti_incerti > 0:
        segnali.append(
            SegnaleSalute(
                "ESITI_INCERTI",
                LivelloSalute.CRITICAL,
                "Sono presenti invii che richiedono revisione umana.",
            )
        )
    if metriche.invii_falliti > 0:
        segnali.append(
            SegnaleSalute(
                "INVII_FALLITI",
                LivelloSalute.WARNING,
                "L'ultima esecuzione contiene invii falliti.",
            )
        )
    if metriche.codice_errore:
        segnali.append(
            SegnaleSalute(
                metriche.codice_errore,
                LivelloSalute.CRITICAL,
                "L'ultima esecuzione si è conclusa con un errore fatale.",
            )
        )
    if metriche.kill_switch:
        segnali.append(
            SegnaleSalute(
                "KILL_SWITCH_ATTIVO",
                LivelloSalute.WARNING,
                "Il kill switch impedisce l'elaborazione.",
            )
        )

    livello = LivelloSalute.OK
    if any(segnale.livello is LivelloSalute.CRITICAL for segnale in segnali):
        livello = LivelloSalute.CRITICAL
    elif segnali:
        livello = LivelloSalute.WARNING
    return ValutazioneSalute(livello=livello, segnali=tuple(segnali))


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("ora deve includere il fuso orario")
    return value.astimezone(timezone.utc)
