from __future__ import annotations

from datetime import date

from .certificate_policy import richiede_certificato_medico_per_categoria
from .models import Arbitro, CandidatoNotifica
from .validation import email_valida

TIPO_NOTIFICA_SCADENZA = "CERTIFICATO_SCADENZA_V1"


def notification_id(arbitro: Arbitro, tipo: str) -> str:
    return "|".join(
        (
            arbitro.id_arbitro.strip(),
            arbitro.scadenza_certificato.isoformat(),
            tipo.strip(),
        )
    )


def richiede_certificato_medico(arbitro: Arbitro) -> bool:
    """Esclude le categorie che non sono tenute a caricare il certificato."""

    return richiede_certificato_medico_per_categoria(
        qualifica=arbitro.qualifica,
        abilitazione=arbitro.abilitazione,
    )


def trova_candidati(
    arbitri: list[Arbitro] | tuple[Arbitro, ...],
    *,
    oggi: date,
    giorni_preavviso: int = 30,
) -> list[CandidatoNotifica]:
    if giorni_preavviso < 0:
        raise ValueError("giorni_preavviso deve essere maggiore o uguale a zero")

    candidati: list[CandidatoNotifica] = []
    tipo = TIPO_NOTIFICA_SCADENZA

    for arbitro in arbitri:
        if (
            not arbitro.attivo
            or not email_valida(arbitro.email)
            or not richiede_certificato_medico(arbitro)
        ):
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
