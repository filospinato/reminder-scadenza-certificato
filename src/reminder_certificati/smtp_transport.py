"""Trasporto SMTP individuale per MDaemon, configurabile ma non attivo.

Usa esclusivamente la libreria standard. Non salva copie nella Posta inviata:
consegna il messaggio direttamente al server SMTP. Le credenziali vengono lette
solo dall'ambiente del processo e non sono mai incluse negli errori.
"""

from __future__ import annotations

import re
import smtplib
import socket
import ssl
from dataclasses import dataclass, field
from email.headerregistry import Address
from email.message import EmailMessage
from email.utils import formatdate, make_msgid
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
        if (
            sicurezza == "PLAIN"
            and ambiente.get("ALLOW_PLAIN_SMTP", "").casefold() != "true"
        ):
            raise ErroreSmtpPermanente("SMTP PLAIN richiede ALLOW_PLAIN_SMTP=true")
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
        nome_mittente = (
            ambiente.get("SMTP_FROM_NAME", "CIA Lazio").strip() or "CIA Lazio"
        )
        if "\r" in nome_mittente or "\n" in nome_mittente:
            raise ErroreSmtpPermanente("SMTP_FROM_NAME contiene ritorni a capo")
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
                if _rifiuti_solo_temporanei(rifiutati):
                    raise ErroreSmtpRetryable(
                        "destinatario temporaneamente rifiutato dal server SMTP"
                    )
                raise ErroreSmtpPermanente("destinatario rifiutato dal server SMTP")
        except ErroreSmtp:
            raise
        except smtplib.SMTPAuthenticationError as exc:
            if _codice_smtp_temporaneo(exc.smtp_code):
                raise ErroreSmtpRetryable(
                    "autenticazione SMTP temporaneamente non disponibile"
                ) from exc
            raise ErroreSmtpPermanente("autenticazione SMTP rifiutata") from exc
        except smtplib.SMTPRecipientsRefused as exc:
            if _rifiuti_solo_temporanei(exc.recipients):
                raise ErroreSmtpRetryable(
                    "destinatario temporaneamente rifiutato dal server SMTP"
                ) from exc
            raise ErroreSmtpPermanente(
                "destinatario rifiutato dal server SMTP"
            ) from exc
        except smtplib.SMTPSenderRefused as exc:
            if _codice_smtp_temporaneo(exc.smtp_code):
                raise ErroreSmtpRetryable(
                    "mittente temporaneamente rifiutato dal server SMTP"
                ) from exc
            raise ErroreSmtpPermanente("mittente rifiutato dal server SMTP") from exc
        except smtplib.SMTPDataError as exc:
            if _codice_smtp_temporaneo(exc.smtp_code):
                raise ErroreSmtpRetryable(
                    "contenuto temporaneamente rifiutato dal server SMTP"
                ) from exc
            raise ErroreSmtpPermanente("contenuto SMTP rifiutato") from exc
        except smtplib.SMTPResponseException as exc:
            if _codice_smtp_temporaneo(exc.smtp_code):
                raise ErroreSmtpRetryable(
                    f"risposta SMTP temporanea {exc.smtp_code}"
                ) from exc
            raise ErroreSmtpPermanente(
                f"risposta SMTP permanente {exc.smtp_code}"
            ) from exc
        except (
            smtplib.SMTPServerDisconnected,
            TimeoutError,
            socket.timeout,
            OSError,
        ) as exc:
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


def _codice_smtp_temporaneo(codice: int) -> bool:
    return 400 <= codice < 500


def _rifiuti_solo_temporanei(
    rifiuti: Mapping[str, tuple[int, bytes | str]],
) -> bool:
    return bool(rifiuti) and all(
        _codice_smtp_temporaneo(codice) for codice, _messaggio in rifiuti.values()
    )


def costruisci_mime(
    messaggio: MessaggioEmail,
    configurazione: ConfigurazioneSmtp,
) -> EmailMessage:
    if "\r" in configurazione.nome_mittente or "\n" in configurazione.nome_mittente:
        raise ErroreSmtpPermanente("nome mittente non valido")
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

    email.add_alternative(messaggio.html, subtype="html")

    html_part = email.get_payload()[-1]
    cid_visti: set[str] = set()
    for risorsa in messaggio.risorse_inline:
        if not _CID_RE.fullmatch(risorsa.cid):
            raise ErroreSmtpPermanente("CID della risorsa inline non valido")
        if risorsa.cid in cid_visti:
            raise ErroreSmtpPermanente("CID della risorsa inline duplicato")
        if not risorsa.maintype or not risorsa.subtype:
            raise ErroreSmtpPermanente("tipo della risorsa inline non valido")
        if not risorsa.filename or "\r" in risorsa.filename or "\n" in risorsa.filename:
            raise ErroreSmtpPermanente("nome della risorsa inline non valido")
        if f"cid:{risorsa.cid}" not in messaggio.html:
            raise ErroreSmtpPermanente("risorsa inline non referenziata nel corpo HTML")
        cid_visti.add(risorsa.cid)
        html_part.add_related(
            risorsa.contenuto,
            maintype=risorsa.maintype,
            subtype=risorsa.subtype,
            cid=f"<{risorsa.cid}>",
            filename=risorsa.filename,
            disposition="inline",
        )
    return email
