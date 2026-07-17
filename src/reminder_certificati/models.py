from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class Arbitro:
    """Dati minimi necessari per valutare una scadenza."""

    id_arbitro: str
    nome: str
    email: str
    scadenza_certificato: date
    attivo: bool = True


@dataclass(frozen=True, slots=True)
class CandidatoNotifica:
    """Notifica che sarebbe inviata in una successiva fase SMTP."""

    arbitro: Arbitro
    tipo: str
    giorni_residui: int
    notification_id: str
