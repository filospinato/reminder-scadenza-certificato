from pathlib import Path

import pytest

from reminder_certificati.email_templates import MessaggioEmail
from reminder_certificati.smtp_transport import (
    ConfigurazioneSmtp,
    ErroreSmtpPermanente,
    TrasportoEmailMemoria,
    costruisci_mime,
)


def _messaggio() -> MessaggioEmail:
    return MessaggioEmail(
        destinatario="destinatario@example.invalid",
        oggetto="Certificato medico in scadenza",
        testo="Ciao Anna Maria, ricevi questa mail...",
        html="<p>Ciao Anna Maria, ricevi questa mail...</p>",
    )


def test_configurazione_smtp_richiede_host_e_mittente() -> None:
    with pytest.raises(ErroreSmtpPermanente, match="SMTP_HOST"):
        ConfigurazioneSmtp.da_ambiente({})

    with pytest.raises(ErroreSmtpPermanente, match="SMTP_FROM"):
        ConfigurazioneSmtp.da_ambiente({"SMTP_HOST": "smtp.example.invalid"})


def test_plain_richiede_consenso_esplicito() -> None:
    ambiente = {
        "SMTP_HOST": "smtp.example.invalid",
        "SMTP_FROM": "cia@example.invalid",
        "SMTP_SECURITY": "PLAIN",
    }
    with pytest.raises(ErroreSmtpPermanente, match="ALLOW_PLAIN_SMTP"):
        ConfigurazioneSmtp.da_ambiente(ambiente)


def test_username_e_password_devono_essere_entrambi_presenti() -> None:
    ambiente = {
        "SMTP_HOST": "smtp.example.invalid",
        "SMTP_FROM": "cia@example.invalid",
        "SMTP_USERNAME": "utente",
    }
    with pytest.raises(ErroreSmtpPermanente, match="entrambi"):
        ConfigurazioneSmtp.da_ambiente(ambiente)


def test_mime_contiene_testo_html_message_id_e_non_crea_copia_sent() -> None:
    config = ConfigurazioneSmtp(
        host="smtp.example.invalid",
        porta=587,
        mittente="cia@example.invalid",
        reply_to="supporto@example.invalid",
    )
    mime = costruisci_mime(_messaggio(), config)

    assert mime["To"] == "destinatario@example.invalid"
    assert mime["Reply-To"] == "supporto@example.invalid"
    assert mime["Message-ID"].startswith("<")
    assert mime.is_multipart()
    assert len(mime.get_payload()) == 2
    assert "Sent" not in mime


def test_fake_restituisce_message_id_sintetico() -> None:
    trasporto = TrasportoEmailMemoria()
    esito = trasporto.invia(_messaggio())

    assert esito.destinatario == "destinatario@example.invalid"
    assert esito.message_id.endswith("@example.invalid>")
    assert len(trasporto.inviati) == 1


def test_logo_opzionale_deve_esistere(tmp_path: Path) -> None:
    config = ConfigurazioneSmtp(
        host="smtp.example.invalid",
        porta=587,
        mittente="cia@example.invalid",
        logo_path=tmp_path / "mancante.png",
    )
    with pytest.raises(ErroreSmtpPermanente, match="non trovato"):
        costruisci_mime(_messaggio(), config)
