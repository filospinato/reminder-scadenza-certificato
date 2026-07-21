from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import date

from .models import Arbitro, CandidatoNotifica
from .rules import trova_candidati
from .validation import AnomaliaDati, CodiceAnomalia, email_valida


@dataclass(frozen=True, slots=True)
class EsitoSelezioneCandidati:
    candidati: tuple[CandidatoNotifica, ...]
    anomalie: tuple[AnomaliaDati, ...]


def seleziona_candidati(
    arbitri: tuple[Arbitro, ...] | list[Arbitro],
    *,
    oggi: date,
    giorni_preavviso: int,
) -> EsitoSelezioneCandidati:
    """Valida i dati di contatto soltanto per le scadenze nella finestra.

    Le righe fuori finestra non producono anomalie per nome, cognome, email o ID.
    Le righe senza scadenza non arrivano a questa fase perché vengono ignorate
    durante la lettura di Operativo.
    """

    if giorni_preavviso < 0:
        raise ValueError("giorni_preavviso deve essere maggiore o uguale a zero")

    anomalie: list[AnomaliaDati] = []
    rilevanti_validi: list[Arbitro] = []

    for arbitro in arbitri:
        giorni_residui = (arbitro.scadenza_certificato - oggi).days
        if not arbitro.attivo or not 0 <= giorni_residui <= giorni_preavviso:
            continue

        errori: list[AnomaliaDati] = []
        numero_riga = arbitro.numero_riga_sorgente
        if not arbitro.id_arbitro.strip():
            errori.append(
                AnomaliaDati(
                    numero_riga,
                    CodiceAnomalia.ID_MANCANTE,
                    "id_arbitro",
                    "identificativo arbitro mancante",
                )
            )
        if not arbitro.nome.strip():
            errori.append(
                AnomaliaDati(
                    numero_riga,
                    CodiceAnomalia.NOME_MANCANTE,
                    "nome",
                    "nome arbitro mancante",
                    arbitro.id_arbitro.strip() or None,
                )
            )
        if not arbitro.cognome.strip():
            errori.append(
                AnomaliaDati(
                    numero_riga,
                    CodiceAnomalia.COGNOME_MANCANTE,
                    "cognome",
                    "cognome arbitro mancante",
                    arbitro.id_arbitro.strip() or None,
                )
            )
        if not email_valida(arbitro.email):
            errori.append(
                AnomaliaDati(
                    numero_riga,
                    CodiceAnomalia.EMAIL_NON_VALIDA,
                    "email",
                    "indirizzo email mancante o non valido",
                    arbitro.id_arbitro.strip() or None,
                )
            )

        if errori:
            anomalie.extend(errori)
            continue
        rilevanti_validi.append(arbitro)

    conteggi = Counter(arbitro.id_arbitro for arbitro in rilevanti_validi)
    duplicati = {
        id_arbitro for id_arbitro, numero in conteggi.items() if numero > 1
    }
    univoci: list[Arbitro] = []
    for arbitro in rilevanti_validi:
        if arbitro.id_arbitro in duplicati:
            anomalie.append(
                AnomaliaDati(
                    arbitro.numero_riga_sorgente,
                    CodiceAnomalia.ID_DUPLICATO,
                    "id_arbitro",
                    "identificativo presente in più righe rilevanti; tutte le occorrenze sono escluse",
                    arbitro.id_arbitro,
                )
            )
        else:
            univoci.append(arbitro)

    candidati = trova_candidati(
        univoci,
        oggi=oggi,
        giorni_preavviso=giorni_preavviso,
    )
    return EsitoSelezioneCandidati(
        candidati=tuple(candidati),
        anomalie=tuple(
            sorted(anomalie, key=lambda item: (item.numero_riga, item.codice))
        ),
    )
