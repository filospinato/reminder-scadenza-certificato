"""Firma istituzionale HTML e testuale per i reminder."""

from __future__ import annotations

from base64 import b64decode
from functools import lru_cache
from importlib.resources import files


LOGO_CID = "fip-lazio-logo"
LOGO_FILENAME = "fip-lazio.png"

FIRMA_TESTO_PREDEFINITA = """CIA Lazio
Mail: cia@lazio.fip.it

Lungotevere Flaminio, 80
00196 Roma RM
06 36005548
fip.it/cia"""

FIRMA_HTML = f"""
<div style="font-family:Tahoma,Arial,sans-serif;font-size:10pt;line-height:1.18;color:#0000CC;">
  <div style="font-weight:700;">CIA Lazio</div>
  <div style="font-weight:400;">Mail: <a href="mailto:cia@lazio.fip.it" style="color:#0000CC;text-decoration:underline;font-weight:400;">cia@lazio.fip.it</a></div>
  <div style="margin:18px 0 18px 0;">
    <img src="cid:{LOGO_CID}" alt="FIP Lazio" width="98" height="56"
         style="display:block;width:98px;height:56px;border:0;">
  </div>
  <div><a href="https://www.google.com/maps/search/?api=1&amp;query=Lungotevere+Flaminio%2C+80%2C+00196+Roma+RM" style="color:#0000CC;text-decoration:underline;">Lungotevere Flaminio, 80<br>00196 Roma RM</a></div>
  <div><a href="tel:+390636005548" style="color:#0000CC;text-decoration:none;">06 36005548</a></div>
  <div><a href="https://cia.fip.it/" style="color:#0000CC;text-decoration:underline;">fip.it/cia</a></div>
</div>
""".strip()


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
