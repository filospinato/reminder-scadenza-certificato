from datetime import date, timedelta

import pytest

from reminder_certificati.models import Arbitro
from reminder_certificati.rules import (
    TIPO_NOTIFICA_SCADENZA,
    notification_id,
    trova_candidati,
)


def arbitro(*, offset: int, attivo: bool = True, email: str = "mario@example.it") -> Arbitro:
    oggi = date(2026, 7, 17)
    return Arbitro(
        id_arbitro=f"A-{offset}",
        nome="Mario",
        cognome="Rossi",
        email=email,
        scadenza_certificato=oggi + timedelta(days=offset),
        attivo=attivo,
    )


def test_include_oggi_e_limite() -> None:
    oggi = date(2026, 7, 17)
    candidati = trova_candidati([arbitro(offset=0), arbitro(offset=30)], oggi=oggi)
    assert [c.giorni_residui for c in candidati] == [0, 30]


def test_esclude_fuori_finestra_e_scaduti() -> None:
    oggi = date(2026, 7, 17)
    candidati = trova_candidati([arbitro(offset=-1), arbitro(offset=31)], oggi=oggi)
    assert candidati == []


def test_esclude_inattivi_ed_email_non_valide() -> None:
    oggi = date(2026, 7, 17)
    candidati = trova_candidati(
        [arbitro(offset=10, attivo=False), arbitro(offset=10, email="non-valida")],
        oggi=oggi,
    )
    assert candidati == []


def test_chiave_deterministica_non_dipende_dalla_finestra() -> None:
    record = arbitro(offset=10)
    trenta = trova_candidati([record], oggi=date(2026, 7, 17), giorni_preavviso=30)[0]
    quarantacinque = trova_candidati(
        [record], oggi=date(2026, 7, 17), giorni_preavviso=45
    )[0]
    attesa = f"A-10|2026-07-27|{TIPO_NOTIFICA_SCADENZA}"
    assert trenta.notification_id == attesa
    assert quarantacinque.notification_id == attesa
    assert notification_id(record, TIPO_NOTIFICA_SCADENZA) == attesa


def test_preavviso_negativo_non_valido() -> None:
    with pytest.raises(ValueError):
        trova_candidati([], oggi=date(2026, 7, 17), giorni_preavviso=-1)
