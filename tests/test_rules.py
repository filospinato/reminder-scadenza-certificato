from datetime import date, timedelta

import pytest

from reminder_certificati.models import Arbitro
from reminder_certificati.rules import (
    TIPO_NOTIFICA_SCADENZA,
    notification_id,
    richiede_certificato_medico,
    trova_candidati,
)


def arbitro(
    *,
    offset: int,
    attivo: bool = True,
    email: str = "mario@example.it",
    qualifica: str = "Arbitro Regionale",
    abilitazione: str = "5a Categoria",
) -> Arbitro:
    oggi = date(2026, 7, 17)
    return Arbitro(
        id_arbitro=f"A-{offset}",
        nome="Mario",
        cognome="Rossi",
        email=email,
        scadenza_certificato=oggi + timedelta(days=offset),
        attivo=attivo,
        qualifica=qualifica,
        abilitazione=abilitazione,
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


@pytest.mark.parametrize(
    ("qualifica", "abilitazione"),
    [
        ("Arbitro Benemerito", "Benemerito"),
        ("Arbitro D'Onore", "Benemerito"),
        ("Osservatore Regionale", "Osservatore"),
        ("osservatore", ""),
    ],
)
def test_esclude_categorie_non_tenute_al_certificato(
    qualifica: str,
    abilitazione: str,
) -> None:
    record = arbitro(
        offset=10,
        qualifica=qualifica,
        abilitazione=abilitazione,
    )
    assert not richiede_certificato_medico(record)
    assert trova_candidati([record], oggi=date(2026, 7, 17)) == []


def test_non_esclude_arbitri_operativi_o_fuori_quadro_per_la_sola_qualifica() -> None:
    oggi = date(2026, 7, 17)
    candidati = trova_candidati(
        [
            arbitro(offset=10),
            arbitro(
                offset=11,
                qualifica="Arbitro Fuori Quadro",
                abilitazione="Fuori Quadro",
            ),
        ],
        oggi=oggi,
    )
    assert [c.giorni_residui for c in candidati] == [10, 11]


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
