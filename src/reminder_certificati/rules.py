from __future__ import annotations

import re
from datetime import date

from .models import Arbitro, CandidatoNotifica

_EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def notification_id(arbitro: Arbitro, tipo: str) -> str:
    """Restituisce una chiave leggibile e deterministica anti-duplicazione."""

    return "|".join(
        (
            arbitro.id_arbitro.strip(),
            arbitro.scadenza_certificato.isoformat(),
            tipo,
        )
    )


def trova_candidati(
    arbitri: list[Arbitro],
    *,
    oggi: date,
    giorni_preavviso: int = 30,
) -> list[CandidatoNotifica]:
    """Seleziona gli arbitri attivi con certificato in scadenza nella finestra.

    La finestra include oggi e il giorno limite. I certificati già scaduti non
    vengono inclusi: saranno gestiti da un eventuale reminder separato.
    """

    if giorni_preavviso < 0:
        raise ValueError("giorni_preavviso deve essere maggiore o uguale a zero")

    candidati: list[CandidatoNotifica] = []
    tipo = f"REMINDER_{giorni_preavviso}"

    for arbitro in arbitri:
        if not arbitro.attivo or not _EMAIL_RE.fullmatch(arbitro.email.strip()):
            continue

        giorni_residui = (arbitro.scadenza_certificato - oggi).days
        if 0 <= giorni_residui <= giorni_preavviso:
            candidati.append(
                CandidatoNotifica(
                    arbitro=arbitro,
                    tipo=tipo,
                    giorni_residui=giorni_residui,
                    notification_id=notification_id(arbitro, tipo),
                )
            )

    return sorted(
        candidati,
        key=lambda candidato: (
            candidato.arbitro.scadenza_certificato,
            candidato.arbitro.id_arbitro,
        ),
    )
