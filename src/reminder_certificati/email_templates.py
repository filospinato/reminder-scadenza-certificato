from __future__ import annotations

import html
import re
from dataclasses import dataclass
from typing import Mapping

from .models import CandidatoNotifica

_PLACEHOLDER_RE = re.compile(r"{{\s*([a-z_]+)\s*}}")
_PLACEHOLDER_CONSENTITI = frozenset(
    {"nome", "cognome", "nome_completo", "data_scadenza", "giorni_residui"}
)


class ErroreTemplate(ValueError):
    """Il template non è sicuro o non rispetta il contratto del messaggio."""


@dataclass(frozen=True, slots=True)
class ConfigurazioneEmail:
    oggetto: str = "Certificato medico in scadenza"
    corpo: str = (
        "Ciao {{nome}}, ricevi questa mail perché il certificato medico presente "
        "nei nostri archivi risulta in scadenza il {{data_scadenza}}.\n\n"
        "Ti invitiamo a provvedere al rinnovo e alla trasmissione della nuova "
        "documentazione secondo le modalità previste."
    )
    firma: str = "Cordiali saluti,\nCIA Lazio"


@dataclass(frozen=True, slots=True)
class MessaggioEmail:
    destinatario: str
    oggetto: str
    testo: str
    html: str


def _valori(candidato: CandidatoNotifica) -> dict[str, str]:
    arbitro = candidato.arbitro
    return {
        "nome": arbitro.nome_per_saluto,
        "cognome": arbitro.cognome.strip(),
        "nome_completo": arbitro.nome_completo,
        "data_scadenza": arbitro.scadenza_certificato.strftime("%d/%m/%Y"),
        "giorni_residui": str(candidato.giorni_residui),
    }


def _render(template: str, valori: Mapping[str, str], *, campo: str) -> str:
    sconosciuti = set(_PLACEHOLDER_RE.findall(template)) - _PLACEHOLDER_CONSENTITI
    if sconosciuti:
        raise ErroreTemplate(
            f"{campo}: placeholder non consentiti: {', '.join(sorted(sconosciuti))}"
        )

    def sostituisci(match: re.Match[str]) -> str:
        nome = match.group(1)
        valore = valori.get(nome, "").strip()
        if not valore:
            raise ErroreTemplate(f"{campo}: valore mancante per {{{{{nome}}}}}")
        return valore

    risultato = _PLACEHOLDER_RE.sub(sostituisci, template).strip()
    if "{{" in risultato or "}}" in risultato:
        raise ErroreTemplate(f"{campo}: placeholder non valido o non chiuso")
    if not risultato:
        raise ErroreTemplate(f"{campo}: non può essere vuoto")
    return risultato


def _contenuto_paragrafo_html(testo: str) -> str:
    return "<br>".join(html.escape(riga) for riga in testo.splitlines())


def _paragrafi_html(testo: str) -> list[str]:
    return [
        f"<p>{_contenuto_paragrafo_html(paragrafo)}</p>"
        for paragrafo in testo.split("\n\n")
    ]


def componi_email(
    candidato: CandidatoNotifica,
    configurazione: ConfigurazioneEmail = ConfigurazioneEmail(),
) -> MessaggioEmail:
    """Compone testo e HTML senza effettuare alcun invio.

    Oggetto, corpo completo e firma vengono renderizzati esattamente dai template
    configurati. Il codice non aggiunge saluti o altre frasi implicite.
    """

    valori = _valori(candidato)
    oggetto = _render(configurazione.oggetto, valori, campo="oggetto")
    corpo = _render(configurazione.corpo, valori, campo="corpo")
    firma = _render(configurazione.firma, valori, campo="firma")

    if "\n" in oggetto or "\r" in oggetto:
        raise ErroreTemplate("oggetto: non sono consentiti ritorni a capo")

    testo = f"{corpo}\n\n{firma}"
    html_completo = "".join([*_paragrafi_html(corpo), *_paragrafi_html(firma)])

    return MessaggioEmail(
        destinatario=candidato.arbitro.email.strip(),
        oggetto=oggetto,
        testo=testo,
        html=html_completo,
    )
