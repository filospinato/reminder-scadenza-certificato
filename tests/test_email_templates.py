from datetime import date

import pytest

from reminder_certificati.email_templates import (
    ConfigurazioneEmail,
    ErroreTemplate,
    componi_email,
)
from reminder_certificati.models import Arbitro, CandidatoNotifica


def candidato(*, nome: str = "Mario Rossi", nome_saluto: str | None = None) -> CandidatoNotifica:
    arbitro = Arbitro(
        id_arbitro="A-1",
        nome=nome,
        nome_saluto=nome_saluto,
        email="mario@example.it",
        scadenza_certificato=date(2026, 8, 1),
    )
    return CandidatoNotifica(
        arbitro=arbitro,
        tipo="REMINDER_30",
        giorni_residui=15,
        notification_id="A-1|2026-08-01|REMINDER_30",
    )


def test_apertura_concordata_usa_nome_personalizzato() -> None:
    messaggio = componi_email(candidato(nome_saluto="Mario"))
    assert messaggio.testo.startswith("Ciao Mario, ricevi questa mail")
    assert messaggio.html.startswith("<p>Ciao Mario, ricevi questa mail")


def test_fallback_usa_prima_parola_del_nominativo() -> None:
    messaggio = componi_email(candidato(nome="Anna Verdi"))
    assert messaggio.testo.startswith("Ciao Anna, ricevi questa mail")


def test_nome_vuoto_produce_errore_controllato() -> None:
    with pytest.raises(ErroreTemplate, match="valore mancante"):
        componi_email(candidato(nome=""))


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
    messaggio = componi_email(candidato(nome_saluto="Mario <Admin>"))
    assert "Mario &lt;Admin&gt;" in messaggio.html
    assert "Mario <Admin>" not in messaggio.html


def test_placeholder_sconosciuto_viene_rifiutato() -> None:
    config = ConfigurazioneEmail(
        corpo="ricevi questa mail per {{dato_segreto}}.",
    )
    with pytest.raises(ErroreTemplate, match="placeholder non consentiti"):
        componi_email(candidato(), config)


def test_corpo_deve_mantenere_apertura_concordata() -> None:
    config = ConfigurazioneEmail(corpo="il certificato sta per scadere.")
    with pytest.raises(ErroreTemplate, match="deve iniziare"):
        componi_email(candidato(), config)


def test_oggetto_non_accetta_ritorni_a_capo() -> None:
    config = ConfigurazioneEmail(oggetto="Avviso\nBCC: altro@example.it")
    with pytest.raises(ErroreTemplate, match="ritorni a capo"):
        componi_email(candidato(), config)
