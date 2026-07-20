from datetime import date
import html

import pytest

from reminder_certificati.email_templates import (
    ConfigurazioneEmail,
    ErroreTemplate,
    componi_email,
)
from reminder_certificati.models import Arbitro, CandidatoNotifica


def candidato(*, nome: str = "Mario", cognome: str = "Rossi") -> CandidatoNotifica:
    arbitro = Arbitro(
        id_arbitro="A-1",
        nome=nome,
        cognome=cognome,
        email="mario@example.it",
        scadenza_certificato=date(2026, 8, 1),
    )
    return CandidatoNotifica(
        arbitro=arbitro,
        tipo="REMINDER_30",
        giorni_residui=15,
        notification_id="A-1|2026-08-01|REMINDER_30",
    )


def test_template_predefinito_usa_la_colonna_nome() -> None:
    messaggio = componi_email(candidato(nome="Mario", cognome="Rossi"))
    assert messaggio.testo.startswith("Ciao Mario, ricevi questa mail")
    assert messaggio.html.startswith("<p>Ciao Mario, ricevi questa mail")


@pytest.mark.parametrize(
    ("nome_operativo", "nome_atteso"),
    (
        ("SILVIA", "Silvia"),
        ("FILIPPO", "Filippo"),
        ("PIER SILVIO", "Pier Silvio"),
        ("ALFONSO ARIO", "Alfonso Ario"),
        ("NICOLA GIULIO", "Nicola Giulio"),
        ("  PIER   SILVIO  ", "Pier Silvio"),
    ),
)
def test_nome_maiuscolo_di_operativo_diventa_leggibile(
    nome_operativo: str,
    nome_atteso: str,
) -> None:
    messaggio = componi_email(candidato(nome=nome_operativo))

    assert messaggio.testo.startswith(f"Ciao {nome_atteso}, ricevi questa mail")
    assert messaggio.html.startswith(f"<p>Ciao {nome_atteso}, ricevi questa mail")


@pytest.mark.parametrize(
    ("cognome_operativo", "cognome_atteso"),
    (
        ("ROSSI", "Rossi"),
        ("DE LUCA", "De Luca"),
        ("D'ANGELO", "D'Angelo"),
        ("ROSSI-BIANCHI", "Rossi-Bianchi"),
        ("  DE   LUCA  ", "De Luca"),
    ),
)
def test_cognome_maiuscolo_di_operativo_diventa_leggibile(
    cognome_operativo: str,
    cognome_atteso: str,
) -> None:
    config = ConfigurazioneEmail(corpo="Cognome: {{cognome}}.")
    messaggio = componi_email(candidato(cognome=cognome_operativo), config)

    assert messaggio.testo.startswith(f"Cognome: {cognome_atteso}.")
    assert messaggio.html.startswith(
        f"<p>Cognome: {html.escape(cognome_atteso)}.</p>"
    )


def test_nome_completo_normalizza_nome_e_cognome() -> None:
    config = ConfigurazioneEmail(corpo="Gentile {{nome_completo}}, promemoria.")
    messaggio = componi_email(
        candidato(nome="PIER SILVIO", cognome="DE LUCA"),
        config,
    )

    assert messaggio.testo.startswith("Gentile Pier Silvio De Luca, promemoria.")
    assert messaggio.html.startswith("<p>Gentile Pier Silvio De Luca, promemoria.</p>")


def test_nome_composto_non_viene_troncato() -> None:
    messaggio = componi_email(candidato(nome="Anna Maria", cognome="Verdi"))
    assert messaggio.testo.startswith("Ciao Anna Maria, ricevi questa mail")


def test_nome_e_cognome_completo_sono_disponibili_nei_template() -> None:
    config = ConfigurazioneEmail(
        corpo=(
            "Gentile {{nome_completo}}, il certificato "
            "scade il {{data_scadenza}}."
        ),
        firma="Cordiali saluti,\nCIA Lazio",
    )
    messaggio = componi_email(candidato(nome="Anna", cognome="Verdi"), config)
    assert "Anna Verdi" in messaggio.testo
    assert messaggio.testo.startswith("Gentile Anna Verdi, il certificato")


def test_nome_vuoto_produce_errore_se_usato_dal_template() -> None:
    with pytest.raises(ErroreTemplate, match="nome"):
        componi_email(candidato(nome=""))


def test_template_senza_nome_non_impone_un_saluto_nascosto() -> None:
    config = ConfigurazioneEmail(corpo="Il certificato sta per scadere.")
    messaggio = componi_email(candidato(nome=""), config)

    assert messaggio.testo.startswith("Il certificato sta per scadere.")
    assert "Ciao" not in messaggio.testo


def test_data_e_firma_sono_presenti_in_testo_e_html() -> None:
    messaggio = componi_email(candidato())
    assert "01/08/2026" in messaggio.testo
    assert "Cordiali saluti,\nCIA Lazio" in messaggio.testo
    assert "01/08/2026" in messaggio.html
    assert "Cordiali saluti,<br>CIA Lazio" in messaggio.html


def test_paragrafi_html_restano_separati() -> None:
    messaggio = componi_email(candidato())
    assert "</p><p>Ti invitiamo" in messaggio.html
    assert messaggio.html.count("<p>") == 3
    assert messaggio.html.count("</p>") == 3


def test_html_esegue_escape_dei_dati_personalizzati() -> None:
    messaggio = componi_email(candidato(nome="Mario <Admin>"))
    assert "Mario &lt;Admin&gt;" in messaggio.html
    assert "Mario <Admin>" not in messaggio.html


def test_placeholder_sconosciuto_viene_rifiutato() -> None:
    config = ConfigurazioneEmail(
        corpo="Promemoria per {{dato_segreto}}.",
    )
    with pytest.raises(ErroreTemplate, match="placeholder non consentiti"):
        componi_email(candidato(), config)


def test_corpo_puo_avere_una_formulazione_libera() -> None:
    config = ConfigurazioneEmail(corpo="Il certificato sta per scadere.")
    messaggio = componi_email(candidato(), config)

    assert messaggio.testo.startswith("Il certificato sta per scadere.")
    assert not messaggio.testo.startswith("Ciao")


def test_corpo_vuoto_viene_rifiutato() -> None:
    config = ConfigurazioneEmail(corpo="   ")
    with pytest.raises(ErroreTemplate, match="non può essere vuoto"):
        componi_email(candidato(), config)


def test_oggetto_non_accetta_ritorni_a_capo() -> None:
    config = ConfigurazioneEmail(oggetto="Avviso\nBCC: altro@example.it")
    with pytest.raises(ErroreTemplate, match="ritorni a capo"):
        componi_email(candidato(), config)
