from datetime import date, datetime, timedelta, timezone

import pytest

from reminder_certificati.admin_store import ArchivioNotificheMemoria
from reminder_certificati.models import Arbitro, CandidatoNotifica
from reminder_certificati.persistent_registry import (
    ErroreRegistroPersistente,
    RegistroPersistente,
)
from reminder_certificati.registry import StatoNotifica


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


def test_prenota_e_conclude_in_sent() -> None:
    archivio = ArchivioNotificheMemoria()
    registro = RegistroPersistente(archivio, versione_app="0.11.0")
    candidato = _candidato()
    ora = datetime(2026, 7, 17, 10, tzinfo=timezone.utc)

    sending = registro.prenota(candidato, ora=ora)
    sent = registro.segna_inviata(
        candidato,
        message_id="<test@example.invalid>",
        ora=ora + timedelta(seconds=1),
    )

    assert sending.stato is StatoNotifica.SENDING
    assert sent.stato is StatoNotifica.SENT
    assert sent.message_id == "<test@example.invalid>"
    assert registro.puo_prenotare(candidato.notification_id) is False


def test_retry_solo_da_failed_retryable() -> None:
    archivio = ArchivioNotificheMemoria()
    registro = RegistroPersistente(archivio, versione_app="0.11.0")
    candidato = _candidato()
    ora = datetime(2026, 7, 17, 10, tzinfo=timezone.utc)

    registro.prenota(candidato, ora=ora)
    failed = registro.segna_errore_retryable(
        candidato,
        errore="timeout",
        ora=ora + timedelta(seconds=1),
    )
    retry = registro.prenota(candidato, ora=ora + timedelta(seconds=2))

    assert failed.stato is StatoNotifica.FAILED_RETRYABLE
    assert retry.stato is StatoNotifica.SENDING
    assert retry.tentativi == 2


def test_blocca_dati_diversi_per_la_stessa_chiave() -> None:
    archivio = ArchivioNotificheMemoria()
    registro = RegistroPersistente(archivio, versione_app="0.11.0")
    ora = datetime(2026, 7, 17, 10, tzinfo=timezone.utc)
    registro.prenota(_candidato(), ora=ora)
    registro.segna_errore_retryable(
        _candidato(), errore="timeout", ora=ora + timedelta(seconds=1)
    )

    with pytest.raises(ErroreRegistroPersistente, match="non coincide"):
        registro.prenota(
            _candidato(nome="Nome Alterato"),
            ora=ora + timedelta(seconds=2),
        )
