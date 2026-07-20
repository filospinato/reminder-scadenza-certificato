from datetime import date, datetime, timedelta, timezone

import pytest

from reminder_certificati.admin_store import ArchivioNotificheMemoria
from reminder_certificati.models import Arbitro, CandidatoNotifica
from reminder_certificati.persistent_registry import (
    ErroreRegistroPersistente,
    RegistroPersistente,
)
from reminder_certificati.registry import StatoNotifica
from reminder_certificati.rules import TIPO_NOTIFICA_SCADENZA

ORA = datetime(2026, 7, 17, 10, tzinfo=timezone.utc)
ID = f"A-001|2026-08-01|{TIPO_NOTIFICA_SCADENZA}"


def _candidato(scadenza: date = date(2026, 8, 1)) -> CandidatoNotifica:
    arbitro = Arbitro(
        id_arbitro="A-001",
        nome="Anna Maria",
        cognome="Verdi",
        email="anna@example.invalid",
        scadenza_certificato=scadenza,
    )
    return CandidatoNotifica(
        arbitro=arbitro,
        tipo=TIPO_NOTIFICA_SCADENZA,
        giorni_residui=15,
        notification_id=ID,
    )


def _registro() -> tuple[RegistroPersistente, ArchivioNotificheMemoria]:
    archivio = ArchivioNotificheMemoria()
    return RegistroPersistente(archivio, versione_app="0.13.0"), archivio


def test_prenota_e_conclude_in_sent() -> None:
    registro, _ = _registro()
    candidato = _candidato()
    sending = registro.prenota(candidato, ora=ORA)
    sent = registro.segna_inviata(
        candidato,
        message_id="<test@example.invalid>",
        ora=ORA + timedelta(seconds=1),
    )
    assert sending.stato is StatoNotifica.SENDING
    assert sent.stato is StatoNotifica.SENT
    assert sent.message_id == "<test@example.invalid>"
    assert registro.puo_prenotare(candidato.notification_id) is False


def test_sent_e_sending_bloccano_nuove_prenotazioni() -> None:
    registro, _ = _registro()
    candidato = _candidato()
    registro.prenota(candidato, ora=ORA)
    assert registro.puo_prenotare(candidato.notification_id) is False
    with pytest.raises(ErroreRegistroPersistente, match="non prenotabile"):
        registro.prenota(candidato, ora=ORA + timedelta(seconds=1))
    registro.segna_inviata(
        candidato,
        message_id="<test@example.invalid>",
        ora=ORA + timedelta(seconds=2),
    )
    assert registro.puo_prenotare(candidato.notification_id) is False


def test_retry_solo_da_failed_retryable() -> None:
    registro, _ = _registro()
    candidato = _candidato()
    registro.prenota(candidato, ora=ORA)
    failed = registro.segna_errore_retryable(
        candidato,
        errore="timeout",
        ora=ORA + timedelta(seconds=1),
    )
    retry = registro.prenota(candidato, ora=ORA + timedelta(seconds=2))
    assert failed.stato is StatoNotifica.FAILED_RETRYABLE
    assert retry.stato is StatoNotifica.SENDING
    assert retry.tentativi == 2
    assert retry.errore is None


def test_retry_si_ferma_dopo_tre_tentativi() -> None:
    registro, archivio = _registro()
    candidato = _candidato()
    istante = ORA
    for tentativo in range(3):
        registro.prenota(candidato, ora=istante)
        istante += timedelta(seconds=1)
        registro.segna_errore_retryable(candidato, errore="timeout", ora=istante)
        istante += timedelta(seconds=1)
        if tentativo < 2:
            assert registro.puo_prenotare(ID) is True
    riga = archivio.ottieni(ID)
    assert riga is not None
    assert riga.tentativi == 3
    assert registro.tentativi_esauriti(riga) is True
    assert registro.puo_prenotare(ID) is False
    with pytest.raises(ErroreRegistroPersistente, match="massimo"):
        registro.prenota(candidato, ora=istante)


def test_unknown_richiede_revisione_e_blocca_retry() -> None:
    registro, _ = _registro()
    candidato = _candidato()
    registro.prenota(candidato, ora=ORA)
    incerto = registro.segna_esito_incerto(
        candidato,
        errore="consegna incerta",
        ora=ORA + timedelta(seconds=1),
    )
    assert incerto.stato is StatoNotifica.UNKNOWN_REVIEW_REQUIRED
    assert registro.puo_prenotare(candidato.notification_id) is False


def test_errore_permanente_blocca_retry() -> None:
    registro, _ = _registro()
    candidato = _candidato()
    registro.prenota(candidato, ora=ORA)
    permanente = registro.segna_errore_permanente(
        candidato,
        errore="destinatario rifiutato",
        ora=ORA + timedelta(seconds=1),
    )
    assert permanente.stato is StatoNotifica.FAILED_PERMANENT
    assert registro.puo_prenotare(ID) is False


def test_non_conclude_una_notifica_non_registrata_o_gia_conclusa() -> None:
    registro, _ = _registro()
    candidato = _candidato()
    with pytest.raises(ErroreRegistroPersistente, match="non registrata"):
        registro.segna_inviata(
            candidato,
            message_id="<test@example.invalid>",
            ora=ORA,
        )
    registro.prenota(candidato, ora=ORA)
    registro.segna_errore_retryable(
        candidato,
        errore="timeout",
        ora=ORA + timedelta(seconds=1),
    )
    with pytest.raises(ErroreRegistroPersistente, match="transizione"):
        registro.segna_inviata(
            candidato,
            message_id="<test@example.invalid>",
            ora=ORA + timedelta(seconds=2),
        )


def test_blocca_certificato_diverso_per_la_stessa_chiave() -> None:
    registro, _ = _registro()
    registro.prenota(_candidato(), ora=ORA)
    registro.segna_errore_retryable(
        _candidato(), errore="timeout", ora=ORA + timedelta(seconds=1)
    )
    with pytest.raises(ErroreRegistroPersistente, match="certificato"):
        registro.prenota(
            _candidato(scadenza=date(2026, 9, 1)),
            ora=ORA + timedelta(seconds=2),
        )


def test_rifiuta_istanti_regressivi() -> None:
    registro, _ = _registro()
    candidato = _candidato()
    registro.prenota(candidato, ora=ORA)
    with pytest.raises(ErroreRegistroPersistente, match="precedere"):
        registro.segna_errore_retryable(
            candidato,
            errore="timeout",
            ora=ORA - timedelta(seconds=1),
        )
