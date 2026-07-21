from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date

from .models import Arbitro, CandidatoNotifica
from .rules import richiede_certificato_medico, trova_candidati
from .validation import (
    AnomaliaDati,
    CodiceAnomalia,
    MappaturaColonne,
    email_valida,
)


@dataclass(frozen=True, slots=True)
class EsitoSelezioneCandidati:
    candidati: tuple[CandidatoNotifica, ...]
    anomalie: tuple[AnomaliaDati, ...]


def seleziona_candidati(
    arbitri: Sequence[Arbitro],
    *,
    oggi: date,
    giorni_preavviso: int,
    mappatura: MappaturaColonne = MappaturaColonne(),
) -> EsitoSelezioneCandidati:
    """Valida i dati obbligatori soltanto per le scadenze nella finestra.

    Le righe fuori finestra, inattive o appartenenti a categorie escluse non
    producono anomalie per nome, cognome, email o ID. Le righe senza scadenza
    non arrivano a questa fase perché vengono ignorate durante la lettura.
    """

    if giorni_preavviso < 0:
        raise ValueError("giorni_preavviso deve essere maggiore o uguale a zero")

    anomalie: list[AnomaliaDati] = []
    rilevanti: list[Arbitro] = []

    for arbitro in arbitri:
        giorni_residui = (arbitro.scadenza_certificato - oggi).days
        if (
            not arbitro.attivo
            or not richiede_certificato_medico(arbitro)
            or not 0 <= giorni_residui <= giorni_preavviso
        ):
            continue
        rilevanti.append(arbitro)

    conteggi = Counter(
        arbitro.id_arbitro.strip()
        for arbitro in rilevanti
        if arbitro.id_arbitro.strip()
    )
    duplicati = {id_arbitro for id_arbitro, numero in conteggi.items() if numero > 1}
    univoci_validi: list[Arbitro] = []

    for arbitro in rilevanti:
        errori: list[AnomaliaDati] = []
        numero_riga = arbitro.numero_riga_sorgente
        id_arbitro = arbitro.id_arbitro.strip()
        if not id_arbitro:
            errori.append(
                AnomaliaDati(
                    numero_riga,
                    CodiceAnomalia.ID_MANCANTE,
                    mappatura.id_arbitro,
                    "identificativo arbitro mancante",
                )
            )
        if not arbitro.nome.strip():
            errori.append(
                AnomaliaDati(
                    numero_riga,
                    CodiceAnomalia.NOME_MANCANTE,
                    mappatura.nome,
                    "nome arbitro mancante",
                    arbitro.id_arbitro.strip() or None,
                )
            )
        if not arbitro.cognome.strip():
            errori.append(
                AnomaliaDati(
                    numero_riga,
                    CodiceAnomalia.COGNOME_MANCANTE,
                    mappatura.cognome,
                    "cognome arbitro mancante",
                    arbitro.id_arbitro.strip() or None,
                )
            )
        if not email_valida(arbitro.email):
            errori.append(
                AnomaliaDati(
                    numero_riga,
                    CodiceAnomalia.EMAIL_NON_VALIDA,
                    mappatura.email,
                    "indirizzo email mancante o non valido",
                    arbitro.id_arbitro.strip() or None,
                )
            )
        if id_arbitro in duplicati:
            errori.append(
                AnomaliaDati(
                    numero_riga,
                    CodiceAnomalia.ID_DUPLICATO,
                    mappatura.id_arbitro,
                    "identificativo presente in più righe rilevanti; tutte le occorrenze sono escluse",
                    id_arbitro,
                )
            )

        if errori:
            anomalie.extend(errori)
            continue
        univoci_validi.append(arbitro)

    candidati = trova_candidati(
        univoci_validi,
        oggi=oggi,
        giorni_preavviso=giorni_preavviso,
    )
    return EsitoSelezioneCandidati(
        candidati=tuple(candidati),
        anomalie=tuple(
            sorted(anomalie, key=lambda item: (item.numero_riga, item.codice))
        ),
    )
