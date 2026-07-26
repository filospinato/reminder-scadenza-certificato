from __future__ import annotations

import math
import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from enum import StrEnum
from typing import Any, Iterable, Mapping, Sequence

from .certificate_policy import richiede_certificato_medico_per_categoria
from .models import Arbitro

_EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
_SERIALE_GOOGLE_RE = re.compile(r"^\d+(?:[.,]\d+)?$")
_EPOCA_SERIALE_GOOGLE = date(1899, 12, 30)
_MINIMO_SERIALE_GOOGLE = 10_000


class SchemaError(ValueError):
    """La sorgente non espone le colonne minime richieste."""


class CodiceAnomalia(StrEnum):
    ID_MANCANTE = "ID_MANCANTE"
    NOME_MANCANTE = "NOME_MANCANTE"
    COGNOME_MANCANTE = "COGNOME_MANCANTE"
    EMAIL_NON_VALIDA = "EMAIL_NON_VALIDA"
    SCADENZA_NON_VALIDA = "SCADENZA_NON_VALIDA"
    STATO_NON_VALIDO = "STATO_NON_VALIDO"
    ID_DUPLICATO = "ID_DUPLICATO"


@dataclass(frozen=True, slots=True)
class MappaturaColonne:
    """Associa i campi logici alle intestazioni effettive di Operativo."""

    id_arbitro: str = "id_arbitro"
    nome: str = "nome"
    cognome: str = "cognome"
    email: str = "email"
    scadenza_certificato: str = "scadenza_certificato"
    attivo: str = "attivo"
    qualifica: str | None = None
    abilitazione: str | None = None

    @property
    def obbligatorie(self) -> tuple[str, ...]:
        base = (
            self.id_arbitro,
            self.nome,
            self.cognome,
            self.email,
            self.scadenza_certificato,
            self.attivo,
        )
        categorie = tuple(
            nome
            for nome in (self.qualifica, self.abilitazione)
            if nome is not None and nome.strip()
        )
        return base + categorie


@dataclass(frozen=True, slots=True)
class PoliticaStato:
    valori_attivi: frozenset[str] = frozenset(
        {"1", "true", "si", "sì", "attivo", "operativo"}
    )


@dataclass(frozen=True, slots=True)
class AnomaliaDati:
    numero_riga: int
    codice: CodiceAnomalia
    campo: str
    messaggio: str
    id_arbitro: str | None = None


@dataclass(frozen=True, slots=True)
class EsitoValidazione:
    arbitri: tuple[Arbitro, ...]
    anomalie: tuple[AnomaliaDati, ...]
    righe_totali: int
    righe_vuote_ignorate: int


def email_valida(value: str) -> bool:
    return bool(_EMAIL_RE.fullmatch(value.strip()))


def valida_intestazioni(
    intestazioni: Iterable[str],
    mappatura: MappaturaColonne = MappaturaColonne(),
) -> None:
    disponibili = {str(item).strip() for item in intestazioni}
    mancanti = [nome for nome in mappatura.obbligatorie if nome not in disponibili]
    if mancanti:
        raise SchemaError("colonne obbligatorie mancanti: " + ", ".join(mancanti))


def _testo(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _parse_seriale_google(value: Any) -> date | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        seriale = float(value)
    else:
        testo = _testo(value)
        if not _SERIALE_GOOGLE_RE.fullmatch(testo):
            return None
        seriale = float(testo.replace(",", "."))

    if not math.isfinite(seriale) or seriale < _MINIMO_SERIALE_GOOGLE:
        return None
    try:
        return _EPOCA_SERIALE_GOOGLE + timedelta(days=int(seriale))
    except OverflowError:
        return None


def _parse_data(value: Any) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value

    text = _testo(value)
    for formato in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(text, formato).date()
        except ValueError:
            continue
    return _parse_seriale_google(value)


def _parse_attivo(value: Any, politica: PoliticaStato) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and value in (0, 1):
        return bool(value)

    normalizzato = _testo(value).casefold()
    # Convenzione di Operativo: la cella vuota è riservata a chi fa attività.
    if not normalizzato:
        return True
    if normalizzato in politica.valori_attivi:
        return True
    # Qualsiasi annotazione non affermativa indica che la persona non fa attività.
    return False


def _riga_vuota(riga: Mapping[str, Any]) -> bool:
    return all(not _testo(value) for value in riga.values())


def valida_righe(
    righe: Sequence[Mapping[str, Any]],
    *,
    intestazioni: Iterable[str] | None = None,
    mappatura: MappaturaColonne = MappaturaColonne(),
    politica_stato: PoliticaStato = PoliticaStato(),
    prima_riga_dati: int = 2,
) -> EsitoValidazione:
    """Converte le righe con scadenza interpretabile in record utilizzabili.

    Le categorie non tenute al certificato e le righe prive di una data di
    scadenza vengono ignorate senza anomalie. Nome, cognome, email, ID e
    duplicati vengono verificati successivamente soltanto per le scadenze che
    rientrano nella finestra del reminder.
    """

    if prima_riga_dati < 1:
        raise ValueError("prima_riga_dati deve essere maggiore o uguale a 1")

    headers = intestazioni
    if headers is None:
        headers = (
            {chiave for riga in righe for chiave in riga.keys()}
            if righe
            else mappatura.obbligatorie
        )
    valida_intestazioni(headers, mappatura)

    anomalie: list[AnomaliaDati] = []
    arbitri: list[Arbitro] = []
    righe_vuote = 0

    for offset, riga in enumerate(righe):
        numero_riga = prima_riga_dati + offset
        if _riga_vuota(riga):
            righe_vuote += 1
            continue

        id_arbitro = _testo(riga.get(mappatura.id_arbitro))
        nome = _testo(riga.get(mappatura.nome))
        cognome = _testo(riga.get(mappatura.cognome))
        email = _testo(riga.get(mappatura.email))
        attivo = _parse_attivo(riga.get(mappatura.attivo), politica_stato)
        qualifica = (
            _testo(riga.get(mappatura.qualifica))
            if mappatura.qualifica is not None
            else ""
        )
        abilitazione = (
            _testo(riga.get(mappatura.abilitazione))
            if mappatura.abilitazione is not None
            else ""
        )

        if not richiede_certificato_medico_per_categoria(
            qualifica=qualifica,
            abilitazione=abilitazione,
        ):
            continue

        valore_scadenza = riga.get(mappatura.scadenza_certificato)
        if not _testo(valore_scadenza):
            continue

        scadenza = _parse_data(valore_scadenza)
        if scadenza is None:
            anomalie.append(
                AnomaliaDati(
                    numero_riga,
                    CodiceAnomalia.SCADENZA_NON_VALIDA,
                    mappatura.scadenza_certificato,
                    "data non valida; usare YYYY-MM-DD, GG/MM/AAAA o un seriale Google Sheets",
                    id_arbitro or None,
                )
            )
            continue

        arbitri.append(
            Arbitro(
                id_arbitro=id_arbitro,
                nome=nome,
                cognome=cognome,
                email=email,
                scadenza_certificato=scadenza,
                attivo=attivo,
                qualifica=qualifica,
                abilitazione=abilitazione,
                numero_riga_sorgente=numero_riga,
            )
        )

    return EsitoValidazione(
        arbitri=tuple(arbitri),
        anomalie=tuple(sorted(anomalie, key=lambda item: (item.numero_riga, item.codice))),
        righe_totali=len(righe),
        righe_vuote_ignorate=righe_vuote,
    )
