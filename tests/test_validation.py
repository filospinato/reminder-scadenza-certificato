from datetime import date

import pytest

from reminder_certificati.validation import (
    CodiceAnomalia,
    MappaturaColonne,
    SchemaError,
    valida_intestazioni,
    valida_righe,
)


def riga(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "id_arbitro": "A-1",
        "nome": "Mario",
        "cognome": "Rossi",
        "email": "mario@example.it",
        "scadenza_certificato": "2026-08-01",
        "attivo": "Operativo",
    }
    base.update(overrides)
    return base


def test_accetta_formati_data_e_stato_previsti() -> None:
    esito = valida_righe(
        [
            riga(),
            riga(
                id_arbitro="A-2",
                nome="Anna Maria",
                cognome="Verdi",
                scadenza_certificato="02/08/2026",
                attivo=1,
            ),
        ]
    )
    assert [item.id_arbitro for item in esito.arbitri] == ["A-1", "A-2"]
    assert esito.arbitri[1].nome_per_saluto == "Anna Maria"
    assert esito.arbitri[1].nome_completo == "Anna Maria Verdi"
    assert esito.arbitri[1].scadenza_certificato == date(2026, 8, 2)
    assert esito.anomalie == ()


@pytest.mark.parametrize("valore", ["", "   ", None])
def test_stato_vuoto_significa_che_fa_attivita(valore: object) -> None:
    esito = valida_righe([riga(attivo=valore)])

    assert len(esito.arbitri) == 1
    assert esito.arbitri[0].attivo is True
    assert esito.anomalie == ()


@pytest.mark.parametrize(
    "valore",
    ["No", "no", "NO", "sospeso", "non convocabile", "altro"],
)
def test_qualsiasi_annotazione_non_affermativa_significa_inattivo(valore: str) -> None:
    esito = valida_righe([riga(attivo=valore)])

    assert len(esito.arbitri) == 1
    assert esito.arbitri[0].attivo is False
    assert esito.anomalie == ()


def test_raccoglie_piu_anomalie_senza_bloccare_le_righe_valide() -> None:
    esito = valida_righe(
        [
            riga(),
            riga(
                id_arbitro="",
                nome="",
                cognome="",
                email="x",
                scadenza_certificato="31-12-2026",
                attivo="forse",
            ),
        ]
    )
    assert len(esito.arbitri) == 1
    assert {item.codice for item in esito.anomalie} == {
        CodiceAnomalia.ID_MANCANTE,
        CodiceAnomalia.NOME_MANCANTE,
        CodiceAnomalia.COGNOME_MANCANTE,
        CodiceAnomalia.EMAIL_NON_VALIDA,
        CodiceAnomalia.SCADENZA_NON_VALIDA,
    }


def test_esclude_tutte_le_occorrenze_di_un_id_duplicato() -> None:
    esito = valida_righe([riga(), riga(email="altro@example.it")])
    assert esito.arbitri == ()
    assert [item.codice for item in esito.anomalie] == [
        CodiceAnomalia.ID_DUPLICATO,
        CodiceAnomalia.ID_DUPLICATO,
    ]


def test_ignora_righe_interamente_vuote() -> None:
    esito = valida_righe([riga(), {"id_arbitro": "", "nome": ""}])
    assert len(esito.arbitri) == 1
    assert esito.righe_vuote_ignorate == 1


def test_mappatura_colonne_personalizzata() -> None:
    mapping = MappaturaColonne(
        id_arbitro="ID",
        nome="Nome",
        cognome="Cognome",
        email="Email",
        scadenza_certificato="Scadenza",
        attivo="Stato",
        qualifica="Qualifica",
        abilitazione="Abilitazione",
    )
    esito = valida_righe(
        [
            {
                "ID": "A-9",
                "Nome": "Anna Maria",
                "Cognome": "Verdi",
                "Email": "anna@example.it",
                "Scadenza": "2026-09-01",
                "Stato": "Sì",
                "Qualifica": "Arbitro Benemerito",
                "Abilitazione": "Benemerito",
            }
        ],
        mappatura=mapping,
    )
    assert esito.arbitri[0].id_arbitro == "A-9"
    assert esito.arbitri[0].nome_per_saluto == "Anna Maria"
    assert esito.arbitri[0].nome_completo == "Anna Maria Verdi"
    assert esito.arbitri[0].qualifica == "Arbitro Benemerito"
    assert esito.arbitri[0].abilitazione == "Benemerito"


def test_cognome_e_colonna_obbligatoria() -> None:
    with pytest.raises(SchemaError, match="cognome"):
        valida_intestazioni(
            ["id_arbitro", "nome", "email", "scadenza_certificato", "attivo"]
        )


def test_intestazioni_mancanti_sono_errore_fatale() -> None:
    with pytest.raises(SchemaError, match="scadenza_certificato"):
        valida_intestazioni(["id_arbitro", "nome", "cognome", "email", "attivo"])


def test_numero_riga_parte_dalla_riga_dati_configurata() -> None:
    esito = valida_righe([riga(email="non-valida")], prima_riga_dati=2)
    assert esito.anomalie[0].numero_riga == 2


def test_lista_vuota_e_valida_in_dry_run() -> None:
    esito = valida_righe([])
    assert esito.arbitri == ()
    assert esito.anomalie == ()
    assert esito.righe_totali == 0
