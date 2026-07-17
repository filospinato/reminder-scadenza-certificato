from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

import pytest

from reminder_certificati.registry import (
    NotificaNonPrenotabile,
    RegistroMemoria,
    StatoNotifica,
    TransizioneRegistroNonValida,
)


T0 = datetime(2026, 7, 17, 9, 0, tzinfo=timezone.utc)
NOTIFICATION_ID = "A-1|2026-08-01|REMINDER_30"


def test_prenotazione_nuova_crea_sending() -> None:
    registro = RegistroMemoria()
    record = registro.prenota(NOTIFICATION_ID, ora=T0)

    assert record.notification_id == NOTIFICATION_ID
    assert record.stato is StatoNotifica.SENDING
    assert record.tentativi == 1
    assert record.creato_il == T0
    assert record.aggiornato_il == T0
    assert registro.ottieni(NOTIFICATION_ID) == record


def test_due_prenotazioni_concorrenti_non_possono_vincere_entrambe() -> None:
    registro = RegistroMemoria()

    def prova(_: int) -> bool:
        try:
            registro.prenota(NOTIFICATION_ID, ora=T0)
            return True
        except NotificaNonPrenotabile:
            return False

    with ThreadPoolExecutor(max_workers=12) as executor:
        risultati = list(executor.map(prova, range(40)))

    assert risultati.count(True) == 1
    assert risultati.count(False) == 39
    assert registro.ottieni(NOTIFICATION_ID).stato is StatoNotifica.SENDING  # type: ignore[union-attr]


def test_sent_blocca_ogni_reinvio_automatico() -> None:
    registro = RegistroMemoria()
    registro.prenota(NOTIFICATION_ID, ora=T0)
    inviato = registro.segna_inviata(
        NOTIFICATION_ID,
        message_id="<test-message@example.it>",
        ora=T0 + timedelta(seconds=1),
    )

    assert inviato.stato is StatoNotifica.SENT
    assert inviato.message_id == "<test-message@example.it>"
    assert not registro.puo_prenotare(NOTIFICATION_ID)
    with pytest.raises(NotificaNonPrenotabile):
        registro.prenota(NOTIFICATION_ID, ora=T0 + timedelta(minutes=1))


def test_errore_retryable_permette_un_nuovo_tentativo() -> None:
    registro = RegistroMemoria()
    registro.prenota(NOTIFICATION_ID, ora=T0)
    fallito = registro.segna_errore_retryable(
        NOTIFICATION_ID,
        errore="timeout SMTP sintetico",
        ora=T0 + timedelta(seconds=1),
    )

    assert fallito.stato is StatoNotifica.FAILED_RETRYABLE
    assert fallito.errore == "timeout SMTP sintetico"
    assert registro.puo_prenotare(NOTIFICATION_ID)

    ripreso = registro.prenota(NOTIFICATION_ID, ora=T0 + timedelta(minutes=1))
    assert ripreso.stato is StatoNotifica.SENDING
    assert ripreso.tentativi == 2
    assert ripreso.errore is None
    assert ripreso.message_id is None


def test_unknown_richiede_revisione_e_non_viene_ritentato() -> None:
    registro = RegistroMemoria()
    registro.prenota(NOTIFICATION_ID, ora=T0)
    incerto = registro.segna_esito_incerto(
        NOTIFICATION_ID,
        errore="SMTP ha accettato la connessione ma la conferma è incerta",
        ora=T0 + timedelta(seconds=1),
    )

    assert incerto.stato is StatoNotifica.UNKNOWN_REVIEW_REQUIRED
    assert not registro.puo_prenotare(NOTIFICATION_ID)
    with pytest.raises(NotificaNonPrenotabile):
        registro.prenota(NOTIFICATION_ID, ora=T0 + timedelta(minutes=1))


def test_non_si_puo_chiudere_una_notifica_non_in_sending() -> None:
    registro = RegistroMemoria()
    with pytest.raises(TransizioneRegistroNonValida, match="non registrata"):
        registro.segna_inviata(
            NOTIFICATION_ID,
            message_id="<test@example.it>",
            ora=T0,
        )

    registro.prenota(NOTIFICATION_ID, ora=T0)
    registro.segna_errore_retryable(
        NOTIFICATION_ID,
        errore="errore sintetico",
        ora=T0 + timedelta(seconds=1),
    )
    with pytest.raises(TransizioneRegistroNonValida, match="transizione"):
        registro.segna_inviata(
            NOTIFICATION_ID,
            message_id="<test@example.it>",
            ora=T0 + timedelta(seconds=2),
        )


def test_snapshot_e_ordinato_e_non_espone_lo_storage_mutabile() -> None:
    registro = RegistroMemoria()
    registro.prenota("B|2026-08-02|REMINDER_30", ora=T0)
    registro.prenota("A|2026-08-01|REMINDER_30", ora=T0)

    snapshot = registro.snapshot()
    assert [item.notification_id for item in snapshot] == [
        "A|2026-08-01|REMINDER_30",
        "B|2026-08-02|REMINDER_30",
    ]
    assert isinstance(snapshot, tuple)


def test_rifiuta_identificativi_vuoti_istanti_naive_e_dettagli_vuoti() -> None:
    registro = RegistroMemoria()
    with pytest.raises(ValueError, match="notification_id"):
        registro.prenota("   ", ora=T0)
    with pytest.raises(ValueError, match="fuso orario"):
        registro.prenota(NOTIFICATION_ID, ora=datetime(2026, 7, 17, 9, 0))

    registro.prenota(NOTIFICATION_ID, ora=T0)
    with pytest.raises(ValueError, match="message_id"):
        registro.segna_inviata(
            NOTIFICATION_ID,
            message_id=" ",
            ora=T0 + timedelta(seconds=1),
        )


def test_non_accetta_un_istante_precedente_all_ultimo_aggiornamento() -> None:
    registro = RegistroMemoria()
    registro.prenota(NOTIFICATION_ID, ora=T0)
    with pytest.raises(ValueError, match="precedere"):
        registro.segna_errore_retryable(
            NOTIFICATION_ID,
            errore="errore sintetico",
            ora=T0 - timedelta(seconds=1),
        )
