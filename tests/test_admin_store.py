from datetime import date, datetime, timezone

import pytest

from reminder_certificati.admin_store import (
    ArchivioNotificheMemoria,
    ErroreArchivioNotifiche,
    RigaNotifica,
)
from reminder_certificati.models import Arbitro, CandidatoNotifica
from reminder_certificati.registry import RecordNotifica, StatoNotifica

ORA = datetime(2026, 7, 17, 10, 0, tzinfo=timezone.utc)


def candidato() -> CandidatoNotifica:
    arbitro = Arbitro(
        id_arbitro="A-1",
        nome="Anna Maria",
        cognome="Verdi",
        email="anna@example.it",
        scadenza_certificato=date(2026, 8, 1),
    )
    return CandidatoNotifica(
        arbitro=arbitro,
        tipo="REMINDER_30",
        giorni_residui=15,
        notification_id="A-1|2026-08-01|REMINDER_30",
    )


def record(stato: StatoNotifica = StatoNotifica.SENDING) -> RecordNotifica:
    return RecordNotifica(
        notification_id="A-1|2026-08-01|REMINDER_30",
        stato=stato,
        tentativi=1,
        creato_il=ORA,
        aggiornato_il=ORA,
        message_id="<test@example.it>" if stato is StatoNotifica.SENT else None,
    )


def test_riga_contiene_tutti_i_dati_amministrativi() -> None:
    riga = RigaNotifica.da_record(candidato(), record(), versione_app="0.6.0")
    valori = riga.come_mappa()
    assert valori["nome"] == "Anna Maria"
    assert valori["cognome"] == "Verdi"
    assert valori["email"] == "anna@example.it"
    assert valori["stato"] == "SENDING"
    assert valori["versione_app"] == "0.6.0"


def test_round_trip_mappa_preserva_record() -> None:
    originale = RigaNotifica.da_record(candidato(), record(), versione_app="0.6.0")
    assert RigaNotifica.da_mappa(originale.come_mappa()) == originale


def test_salva_inserisce_e_aggiorna_senza_duplicare() -> None:
    archivio = ArchivioNotificheMemoria()
    iniziale = RigaNotifica.da_record(candidato(), record(), versione_app="0.6.0")
    archivio.salva(iniziale)

    inviato = RecordNotifica(
        notification_id=iniziale.notification_id,
        stato=StatoNotifica.SENT,
        tentativi=1,
        creato_il=ORA,
        aggiornato_il=datetime(2026, 7, 17, 10, 1, tzinfo=timezone.utc),
        message_id="<test@example.it>",
    )
    archivio.salva(RigaNotifica.da_record(candidato(), inviato, versione_app="0.6.0"))

    assert len(archivio.snapshot()) == 1
    assert archivio.ottieni(iniziale.notification_id).stato is StatoNotifica.SENT


def test_rifiuta_chiavi_duplicate_nella_sorgente() -> None:
    riga = RigaNotifica.da_record(candidato(), record(), versione_app="0.6.0")
    with pytest.raises(ErroreArchivioNotifiche, match="duplicato"):
        ArchivioNotificheMemoria([riga, riga])


def test_rifiuta_regressione_temporale() -> None:
    archivio = ArchivioNotificheMemoria()
    riga = RigaNotifica.da_record(candidato(), record(), versione_app="0.6.0")
    archivio.salva(riga)
    precedente = RigaNotifica(
        **{
            **riga.__dict__,
            "aggiornato_il": datetime(2026, 7, 17, 9, 59, tzinfo=timezone.utc),
        }
    )
    with pytest.raises(ErroreArchivioNotifiche, match="precedere"):
        archivio.salva(precedente)


def test_rifiuta_record_e_candidato_non_allineati() -> None:
    diverso = RecordNotifica(
        notification_id="ALTRO",
        stato=StatoNotifica.SENDING,
        tentativi=1,
        creato_il=ORA,
        aggiornato_il=ORA,
    )
    with pytest.raises(ValueError, match="differenti"):
        RigaNotifica.da_record(candidato(), diverso, versione_app="0.6.0")
