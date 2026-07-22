"""Firma istituzionale HTML e testuale per i reminder."""

from __future__ import annotations

from base64 import b64decode
from dataclasses import dataclass
from functools import lru_cache
from html import escape
from importlib.resources import files


LOGO_CID = "fip-lazio-logo"
LOGO_FILENAME = "fip-lazio.png"


@dataclass(frozen=True, slots=True)
class DatiFirma:
    nome: str
    etichetta_email: str
    email: str
    indirizzo: tuple[str, str]
    telefono: str
    telefono_uri: str
    sito: str
    sito_url: str
    mappa_url: str


DATI_FIRMA = DatiFirma(
    nome="CIA Lazio",
    etichetta_email="Mail",
    email="cia@lazio.fip.it",
    indirizzo=("Lungotevere Flaminio, 80", "00196 Roma RM"),
    telefono="06 36005548",
    telefono_uri="+390636005548",
    sito="fip.it/cia",
    sito_url="https://cia.fip.it/",
    mappa_url=(
        "https://www.google.com/maps/search/"
        "?api=1&query=Lungotevere+Flaminio%2C+80%2C+00196+Roma+RM"
    ),
)


def _crea_firma_testo(dati: DatiFirma) -> str:
    return "\n".join(
        (
            dati.nome,
            f"{dati.etichetta_email}: {dati.email}",
            "",
            *dati.indirizzo,
            dati.telefono,
            dati.sito,
        )
    )


def _crea_firma_html(dati: DatiFirma) -> str:
    nome = escape(dati.nome)
    etichetta_email = escape(dati.etichetta_email)
    email = escape(dati.email)
    indirizzo_1, indirizzo_2 = (escape(riga) for riga in dati.indirizzo)
    telefono = escape(dati.telefono)
    sito = escape(dati.sito)
    mailto = escape(f"mailto:{dati.email}", quote=True)
    telefono_uri = escape(f"tel:{dati.telefono_uri}", quote=True)
    sito_url = escape(dati.sito_url, quote=True)
    mappa_url = escape(dati.mappa_url, quote=True)

    return f"""
<div style="font-family:Tahoma,Arial,sans-serif;font-size:10pt;line-height:1.18;color:#0000CC;">
  <div style="font-weight:700;">{nome}</div>
  <div style="font-weight:400;">{etichetta_email}: <a href="{mailto}" style="color:#0000CC;text-decoration:underline;font-weight:400;">{email}</a></div>
  <div style="margin:18px 0 18px 0;">
    <img src="cid:{LOGO_CID}" alt="FIP Lazio" width="98" height="56"
         style="display:block;width:98px;height:56px;border:0;">
  </div>
  <div><a href="{mappa_url}" style="color:#0000CC;text-decoration:underline;">{indirizzo_1}<br>{indirizzo_2}</a></div>
  <div><a href="{telefono_uri}" style="color:#0000CC;text-decoration:none;">{telefono}</a></div>
  <div><a href="{sito_url}" style="color:#0000CC;text-decoration:underline;">{sito}</a></div>
</div>
""".strip()


# Le due rappresentazioni sono generate dagli stessi dati: non vanno mantenute a mano.
FIRMA_TESTO = _crea_firma_testo(DATI_FIRMA)
FIRMA_HTML = _crea_firma_html(DATI_FIRMA)


@lru_cache(maxsize=1)
def carica_logo_fip_lazio() -> bytes:
    """Restituisce senza trasformazioni il PNG istituzionale incluso nel pacchetto."""

    contenuto_base64 = (
        files("reminder_certificati")
        .joinpath("assets/fip-lazio.png.b64")
        .read_text(encoding="ascii")
        .strip()
    )
    return b64decode(contenuto_base64, validate=True)
