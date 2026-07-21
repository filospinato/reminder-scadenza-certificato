import smtplib

import pytest

from reminder_certificati.email_templates import MessaggioEmail, RisorsaInline
from reminder_certificati.smtp_transport import (
    ConfigurazioneSmtp,
    ErroreSmtpPermanente,
    ErroreSmtpRetryable,
    TrasportoEmailMemoria,
    TrasportoSmtpMdaemon,
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


def test_nome_mittente_rifiuta_header_injection() -> None:
    base = {
        "SMTP_HOST": "smtp.example.invalid",
        "SMTP_FROM": "cia@example.invalid",
    }
    with pytest.raises(ErroreSmtpPermanente, match="SMTP_FROM_NAME"):
        ConfigurazioneSmtp.da_ambiente(
            {**base, "SMTP_FROM_NAME": "CIA Lazio\nBcc: altro@example.invalid"}
        )


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


def test_risorsa_inline_con_cid_non_valido_viene_rifiutata() -> None:
    messaggio = MessaggioEmail(
        destinatario="destinatario@example.invalid",
        oggetto="Oggetto",
        testo="Testo",
        html='<img src="cid:logo>\r\nBcc">',
        risorse_inline=(
            RisorsaInline(b"logo", "image", "png", "logo>\r\nBcc", "logo.png"),
        ),
    )
    config = ConfigurazioneSmtp(
        host="smtp.example.invalid",
        porta=587,
        mittente="cia@example.invalid",
    )
    with pytest.raises(ErroreSmtpPermanente, match="CID"):
        costruisci_mime(messaggio, config)


def test_risorsa_inline_allegata_e_referenziata_nel_corpo_html() -> None:
    messaggio = MessaggioEmail(
        destinatario="destinatario@example.invalid",
        oggetto="Oggetto",
        testo="Testo",
        html='<p>Testo</p><img src="cid:fip-lazio-logo">',
        risorse_inline=(
            RisorsaInline(
                b"\x89PNG\r\n\x1a\nsynthetic",
                "image",
                "png",
                "fip-lazio-logo",
                "fip-lazio.png",
            ),
        ),
    )
    config = ConfigurazioneSmtp(
        host="smtp.example.invalid",
        porta=587,
        mittente="cia@example.invalid",
    )

    mime = costruisci_mime(messaggio, config)
    html_parts = [
        parte for parte in mime.walk() if parte.get_content_type() == "text/html"
    ]
    immagini = [
        parte for parte in mime.walk() if parte.get_content_maintype() == "image"
    ]

    assert len(html_parts) == 1
    assert 'src="cid:fip-lazio-logo"' in html_parts[0].get_content()
    assert len(immagini) == 1
    assert immagini[0]["Content-ID"] == "<fip-lazio-logo>"
    assert immagini[0].get_content_disposition() == "inline"
    assert immagini[0].get_filename() == "fip-lazio.png"


def test_risorsa_inline_deve_essere_referenziata_nell_html() -> None:
    messaggio = MessaggioEmail(
        destinatario="destinatario@example.invalid",
        oggetto="Oggetto",
        testo="Testo",
        html="<p>Testo</p>",
        risorse_inline=(
            RisorsaInline(b"logo", "image", "png", "logo", "logo.png"),
        ),
    )
    config = ConfigurazioneSmtp(
        host="smtp.example.invalid",
        porta=587,
        mittente="cia@example.invalid",
    )

    with pytest.raises(ErroreSmtpPermanente, match="non referenziata"):
        costruisci_mime(messaggio, config)


class _SmtpConErrore:
    errore: Exception

    def __init__(self, *args, **kwargs) -> None:
        pass

    def ehlo(self) -> None:
        pass

    def send_message(self, *args, **kwargs):
        raise self.errore

    def quit(self) -> None:
        pass


def _trasporto_con_errore(errore: Exception) -> TrasportoSmtpMdaemon:
    class SmtpSpecifico(_SmtpConErrore):
        pass

    SmtpSpecifico.errore = errore
    return TrasportoSmtpMdaemon(
        ConfigurazioneSmtp(
            host="smtp.example.invalid",
            porta=25,
            mittente="cia@example.invalid",
            sicurezza="PLAIN",
        ),
        smtp_factory=SmtpSpecifico,
    )


@pytest.mark.parametrize(
    "errore",
    [
        smtplib.SMTPAuthenticationError(454, b"temporary auth failure"),
        smtplib.SMTPSenderRefused(450, b"mailbox busy", "cia@example.invalid"),
        smtplib.SMTPRecipientsRefused(
            {"destinatario@example.invalid": (450, b"mailbox busy")}
        ),
        smtplib.SMTPDataError(451, b"local processing error"),
    ],
)
def test_risposte_smtp_4xx_sono_ritentabili(errore: Exception) -> None:
    with pytest.raises(ErroreSmtpRetryable):
        _trasporto_con_errore(errore).invia(_messaggio())


@pytest.mark.parametrize(
    "errore",
    [
        smtplib.SMTPAuthenticationError(535, b"invalid credentials"),
        smtplib.SMTPSenderRefused(550, b"sender rejected", "cia@example.invalid"),
        smtplib.SMTPRecipientsRefused(
            {"destinatario@example.invalid": (550, b"recipient rejected")}
        ),
        smtplib.SMTPDataError(554, b"message rejected"),
    ],
)
def test_risposte_smtp_5xx_sono_permanenti(errore: Exception) -> None:
    with pytest.raises(ErroreSmtpPermanente):
        _trasporto_con_errore(errore).invia(_messaggio())
