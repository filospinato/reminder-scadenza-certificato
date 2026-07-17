"""Trasporto SMTP individuale per MDaemon, configurabile ma non attivo.

Usa esclusivamente la libreria standard. Non salva copie nella Posta inviata:
consegna il messaggio direttamente al server SMTP. Le credenziali vengono lette
solo dall'ambiente del processo e non sono mai incluse negli errori.
"""

from __future__ import annotations

import mimetypes
import re
import smtplib
import socket
import ssl
from dataclasses import dataclass, field
from email.headerregistry import Address
from email.message import EmailMessage
from email.utils import formatdate, make_msgid
from html import escape
from pathlib import Path
from typing import Callable, Mapping, Protocol

from .email_templates import MessaggioEmail
from .validation import email_valida


class ErroreSmtp(RuntimeError):
    """Errore base del trasporto SMTP."""


class ErroreSmtpRetryable(ErroreSmtp):
    """Errore avvenuto prima di una consegna plausibile; è ritentabile."""


class ErroreSmtpPermanente(ErroreSmtp):
    """Configurazione o risposta SMTP permanente; serve intervento umano."""


class EsitoSmtpIncerto(ErroreSmtp):
    """La consegna potrebbe essere avvenuta e non deve essere ritentata."""


_CID_RE = re.compile(r"^[A-Za-z0-9._-]+$")


@dataclass(frozen=True, slots=True)
class ConfigurazioneSmtp:
    host: str
    porta: int
    mittente: str
    username: str | None = None
    password: str | None = None
    sicurezza: str = "STARTTLS"
    timeout_secondi: float = 20.0
    reply_to: str | None = None
    nome_mittente: str = "CIA Lazio"
    logo_path: Path | None = None
    logo_cid: str = "logo-cia-lazio"

    @classmethod
    def da_ambiente(cls, ambiente: Mapping[str, str]) -> "ConfigurazioneSmtp":
        host = ambiente.get("SMTP_HOST", "").strip()
        mittente = ambiente.get("SMTP_FROM", "").strip()
        if not host:
            raise ErroreSmtpPermanente("SMTP_HOST mancante")
        if not email_valida(mittente):
            raise ErroreSmtpPermanente("SMTP_FROM mancante o non valido")
        try:
            porta = int(ambiente.get("SMTP_PORT", "587"))
        except ValueError as exc:
            raise ErroreSmtpPermanente("SMTP_PORT non valido") from exc
        if not 1 <= porta <= 65535:
            raise ErroreSmtpPermanente("SMTP_PORT fuori intervallo")
        sicurezza = ambiente.get("SMTP_SECURITY", "STARTTLS").strip().upper()
        if sicurezza not in {"STARTTLS", "SSL", "PLAIN"}:
            raise ErroreSmtpPermanente(
                "SMTP_SECURITY deve essere STARTTLS, SSL o PLAIN"
            )
        if sicurezza == "PLAIN" and ambiente.get("ALLOW_PLAIN_SMTP", "").casefold() != "true":
            raise ErroreSmtpPermanente(
                "SMTP PLAIN richiede ALLOW_PLAIN_SMTP=true"
            )
        try:
            timeout = float(ambiente.get("SMTP_TIMEOUT_SECONDS", "20"))
        except ValueError as exc:
            raise ErroreSmtpPermanente("SMTP_TIMEOUT_SECONDS non valido") from exc
        if not 1 <= timeout <= 120:
            raise ErroreSmtpPermanente(
                "SMTP_TIMEOUT_SECONDS deve essere compreso tra 1 e 120"
            )
        username = ambiente.get("SMTP_USERNAME", "").strip() or None
        password = ambiente.get("SMTP_PASSWORD", "") or None
        if bool(username) != bool(password):
            raise ErroreSmtpPermanente(
                "SMTP_USERNAME e SMTP_PASSWORD devono essere entrambi presenti o assenti"
            )
        reply_to = ambiente.get("SMTP_REPLY_TO", "").strip() or None
        if reply_to is not None and not email_valida(reply_to):
            raise ErroreSmtpPermanente("SMTP_REPLY_TO non valido")
        nome_mittente = ambiente.get("SMTP_FROM_NAME", "CIA Lazio").strip() or "CIA Lazio"
        if "\r" in nome_mittente or "\n" in nome_mittente:
            raise ErroreSmtpPermanente("SMTP_FROM_NAME contiene ritorni a capo")
        logo = ambiente.get("SMTP_LOGO_PATH", "").strip()
        logo_cid = ambiente.get("SMTP_LOGO_CID", "logo-cia-lazio").strip() or "logo-cia-lazio"
        if not _CID_RE.fullmatch(logo_cid):
            raise ErroreSmtpPermanente("SMTP_LOGO_CID non valido")
        return cls(
            host=host,
            porta=porta,
            mittente=mittente,
            username=username,
            password=password,
            sicurezza=sicurezza,
            timeout_secondi=timeout,
            reply_to=reply_to,
            nome_mittente=nome_mittente,
            logo_path=Path(logo) if logo else None,
            logo_cid=logo_cid,
        )


@dataclass(frozen=True, slots=True)
class EsitoInvio:
    message_id: str
    destinatario: str


class TrasportoEmail(Protocol):
    def invia(self, messaggio: MessaggioEmail) -> EsitoInvio:
        """Invia un singolo messaggio individuale."""


@dataclass(slots=True)
class TrasportoEmailMemoria:
    """Fake che conserva solo messaggi sintetici forniti dai test."""

    inviati: list[MessaggioEmail] = field(default_factory=list)
    errore: Exception | None = None

    def invia(self, messaggio: MessaggioEmail) -> EsitoInvio:
        if self.errore is not None:
            raise self.errore
        self.inviati.append(messaggio)
        return EsitoInvio(
            message_id=f"<synthetic-{len(self.inviati)}@example.invalid>",
            destinatario=messaggio.destinatario,
        )


@dataclass(frozen=True, slots=True)
class TrasportoSmtpMdaemon:
    configurazione: ConfigurazioneSmtp
    smtp_factory: Callable[..., smtplib.SMTP] = smtplib.SMTP
    smtp_ssl_factory: Callable[..., smtplib.SMTP_SSL] = smtplib.SMTP_SSL

    def invia(self, messaggio: MessaggioEmail) -> EsitoInvio:
        if not email_valida(messaggio.destinatario):
            raise ErroreSmtpPermanente("destinatario non valido")
        try:
            email = costruisci_mime(messaggio, self.configurazione)
        except ErroreSmtp:
            raise
        except (TypeError, ValueError, OSError) as exc:
            raise ErroreSmtpPermanente(
                f"costruzione MIME non riuscita: {type(exc).__name__}"
            ) from exc

        connessione: smtplib.SMTP | smtplib.SMTP_SSL | None = None
        consegna_iniziata = False
        try:
            if self.configurazione.sicurezza == "SSL":
                connessione = self.smtp_ssl_factory(
                    self.configurazione.host,
                    self.configurazione.porta,
                    timeout=self.configurazione.timeout_secondi,
                    context=ssl.create_default_context(),
                )
            else:
                connessione = self.smtp_factory(
                    self.configurazione.host,
                    self.configurazione.porta,
                    timeout=self.configurazione.timeout_secondi,
                )
                connessione.ehlo()
                if self.configurazione.sicurezza == "STARTTLS":
                    connessione.starttls(context=ssl.create_default_context())
                    connessione.ehlo()
            if self.configurazione.username is not None:
                connessione.login(
                    self.configurazione.username,
                    self.configurazione.password or "",
                )
            consegna_iniziata = True
            rifiutati = connessione.send_message(
                email,
                from_addr=self.configurazione.mittente,
                to_addrs=[messaggio.destinatario],
            )
            if rifiutati:
                raise ErroreSmtpPermanente("destinatario rifiutato dal server SMTP")
        except ErroreSmtp:
            raise
        except smtplib.SMTPAuthenticationError as exc:
            raise ErroreSmtpPermanente("autenticazione SMTP rifiutata") from exc
        except smtplib.SMTPRecipientsRefused as exc:
            raise ErroreSmtpPermanente("destinatario rifiutato dal server SMTP") from exc
        except smtplib.SMTPSenderRefused as exc:
            raise ErroreSmtpPermanente("mittente rifiutato dal server SMTP") from exc
        except smtplib.SMTPDataError as exc:
            if 400 <= exc.smtp_code < 500:
                raise EsitoSmtpIncerto("risposta temporanea dopo avvio consegna") from exc
            raise ErroreSmtpPermanente("contenuto SMTP rifiutato") from exc
        except smtplib.SMTPResponseException as exc:
            if consegna_iniziata:
                raise EsitoSmtpIncerto(
                    f"risposta SMTP {exc.smtp_code} durante la consegna"
                ) from exc
            if 400 <= exc.smtp_code < 500:
                raise ErroreSmtpRetryable(
                    f"risposta SMTP temporanea {exc.smtp_code}"
                ) from exc
            raise ErroreSmtpPermanente(
                f"risposta SMTP permanente {exc.smtp_code}"
            ) from exc
        except (smtplib.SMTPServerDisconnected, TimeoutError, socket.timeout, OSError) as exc:
            if consegna_iniziata:
                raise EsitoSmtpIncerto(
                    "connessione interrotta durante la consegna"
                ) from exc
            raise ErroreSmtpRetryable(
                f"connessione SMTP non disponibile: {type(exc).__name__}"
            ) from exc
        finally:
            if connessione is not None:
                try:
                    connessione.quit()
                except Exception:
                    pass
        return EsitoInvio(
            message_id=str(email["Message-ID"]),
            destinatario=messaggio.destinatario,
        )


def costruisci_mime(
    messaggio: MessaggioEmail,
    configurazione: ConfigurazioneSmtp,
) -> EmailMessage:
    if "\r" in configurazione.nome_mittente or "\n" in configurazione.nome_mittente:
        raise ErroreSmtpPermanente("nome mittente non valido")
    if not _CID_RE.fullmatch(configurazione.logo_cid):
        raise ErroreSmtpPermanente("logo CID non valido")

    username, dominio = configurazione.mittente.rsplit("@", 1)
    email = EmailMessage()
    email["Subject"] = messaggio.oggetto
    email["From"] = Address(
        display_name=configurazione.nome_mittente,
        username=username,
        domain=dominio,
    )
    email["To"] = messaggio.destinatario
    email["Date"] = formatdate(localtime=False, usegmt=True)
    email["Message-ID"] = make_msgid(domain=dominio)
    if configurazione.reply_to:
        reply_user, reply_domain = configurazione.reply_to.rsplit("@", 1)
        email["Reply-To"] = Address(username=reply_user, domain=reply_domain)
    email.set_content(messaggio.testo)

    html_messaggio = messaggio.html
    logo_path = configurazione.logo_path
    if logo_path is not None:
        if not logo_path.is_file():
            raise ErroreSmtpPermanente("file logo SMTP non trovato")
        tipo, _ = mimetypes.guess_type(logo_path.name)
        if tipo is None or not tipo.startswith("image/"):
            raise ErroreSmtpPermanente("formato logo SMTP non riconosciuto")
        html_messaggio += (
            '<p><img src="cid:'
            + escape(configurazione.logo_cid, quote=True)
            + '" alt="Logo CIA Lazio"></p>'
        )

    email.add_alternative(html_messaggio, subtype="html")

    if logo_path is not None:
        tipo, _ = mimetypes.guess_type(logo_path.name)
        assert tipo is not None
        maintype, subtype = tipo.split("/", 1)
        html_part = email.get_payload()[-1]
        html_part.add_related(
            logo_path.read_bytes(),
            maintype=maintype,
            subtype=subtype,
            cid=f"<{configurazione.logo_cid}>",
            filename=logo_path.name,
            disposition="inline",
        )
    return email
