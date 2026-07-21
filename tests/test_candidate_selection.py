from datetime import date, timedelta

from reminder_certificati.candidate_selection import seleziona_candidati
from reminder_certificati.models import Arbitro
from reminder_certificati.validation import CodiceAnomalia


OGGI = date(2026, 7, 17)


def arbitro(
    *,
    offset: int,
    id_arbitro: str = "A-1",
    nome: str = "Mario",
    cognome: str = "Rossi",
    email: str = "mario@example.it",
    attivo: bool = True,
    riga: int = 3,
) -> Arbitro:
    return Arbitro(
        id_arbitro=id_arbitro,
        nome=nome,
        cognome=cognome,
        email=email,
        scadenza_certificato=OGGI + timedelta(days=offset),
        attivo=attivo,
        qualifica="Arbitro Regionale",
        abilitazione="5a Categoria",
        numero_riga_sorgente=riga,
    )


def test_non_segnala_dati_mancanti_fuori_dalla_finestra() -> None:
    esito = seleziona_candidati(
        [
            arbitro(
                offset=31,
                id_arbitro="",
                nome="",
                cognome="",
                email="",
            ),
            arbitro(
                offset=-1,
                id_arbitro="",
                nome="",
                cognome="",
                email="",
                riga=4,
            ),
        ],
        oggi=OGGI,
        giorni_preavviso=30,
    )

    assert esito.candidati == ()
    assert esito.anomalie == ()


def test_segnala_tutti_i_dati_obbligatori_mancanti_nella_finestra() -> None:
    esito = seleziona_candidati(
        [
            arbitro(
                offset=10,
                id_arbitro="",
                nome="",
                cognome="",
                email="",
                riga=8,
            )
        ],
        oggi=OGGI,
        giorni_preavviso=30,
    )

    assert esito.candidati == ()
    assert {anomalia.codice for anomalia in esito.anomalie} == {
        CodiceAnomalia.ID_MANCANTE,
        CodiceAnomalia.NOME_MANCANTE,
        CodiceAnomalia.COGNOME_MANCANTE,
        CodiceAnomalia.EMAIL_NON_VALIDA,
    }
    assert {anomalia.numero_riga for anomalia in esito.anomalie} == {8}


def test_il_cognome_resta_obbligatorio_per_un_candidato() -> None:
    esito = seleziona_candidati(
        [arbitro(offset=10, cognome="")],
        oggi=OGGI,
        giorni_preavviso=30,
    )

    assert esito.candidati == ()
    assert [anomalia.codice for anomalia in esito.anomalie] == [
        CodiceAnomalia.COGNOME_MANCANTE
    ]


def test_inattivi_non_generano_anomalie_di_contatto() -> None:
    esito = seleziona_candidati(
        [
            arbitro(
                offset=10,
                nome="",
                cognome="",
                email="",
                attivo=False,
            )
        ],
        oggi=OGGI,
        giorni_preavviso=30,
    )

    assert esito.candidati == ()
    assert esito.anomalie == ()


def test_esclude_duplicati_solo_se_entrambi_rilevanti() -> None:
    esito = seleziona_candidati(
        [
            arbitro(offset=10, riga=3),
            arbitro(offset=20, riga=4),
            arbitro(offset=60, riga=5),
        ],
        oggi=OGGI,
        giorni_preavviso=30,
    )

    assert esito.candidati == ()
    assert [anomalia.codice for anomalia in esito.anomalie] == [
        CodiceAnomalia.ID_DUPLICATO,
        CodiceAnomalia.ID_DUPLICATO,
    ]
    assert [anomalia.numero_riga for anomalia in esito.anomalie] == [3, 4]


def test_crea_un_candidato_completo_nella_finestra() -> None:
    esito = seleziona_candidati(
        [arbitro(offset=10)],
        oggi=OGGI,
        giorni_preavviso=30,
    )

    assert len(esito.candidati) == 1
    assert esito.candidati[0].giorni_residui == 10
    assert esito.anomalie == ()
