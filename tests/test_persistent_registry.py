from datetime import date, datetime, timedelta, timezone

import pytest

from reminder_certificati.admin_store import ArchivioNotificheMemoria
from reminder_certificati.models import Arbitro, CandidatoNotifica
from reminder_certificati.persistent_registry import (
    ErroreRegistroPersistente,
    RegistroPersistente,
)
from reminder_certificati.registry import StatoNotifica

ORA = datetime(2026, 7, 17, 10, tzinfo=timezone.utc)


def _candidato(nome: str = "Anna Maria") -> CandidatoNotifica:
    arbitro = Arbitro(
        id_arbitro="A-001",
        nome=nome,
        cognome="Verdi",
        email="anna@example.invalid",
        scadenza_certificato=date(2026, 8, 1),
    )
    return CandidatoNotifica(
        arbitro=arbitro,
        tipo="REMINDER_30",
        giorni_residui=15,
        notification_id="A-001|2026-08-01|REMINDER_30",
    )


def _registro() -> tuple[RegistroPersistente, ArchivioNotificheMemoria]:
    archivio = ArchivioNotificheMemoria()
    return RegistroPersistente(archivio, versione_app="0.12.0"), archivio


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
    with pytest.raises(ErroreRegistroPersistente, match="non prenotabile"):
        registro.prenota(candidato, ora=ORA + timedelta(seconds=2))


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


def test_blocca_dati_diversi_per_la_stessa_chiave() -> None:
    registro, _ = _registro()
    registro.prenota(_candidato(), ora=ORA)
    registro.segna_errore_retryable(
        _candidato(), errore="timeout", ora=ORA + timedelta(seconds=1)
    )

    with pytest.raises(ErroreRegistroPersistente, match="non coincide"):
        registro.prenota(
            _candidato(nome="Nome Alterato"),
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
