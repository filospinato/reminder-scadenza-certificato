from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum
from typing import Any, Iterable, Mapping, Sequence

from .models import Arbitro

_EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


class SchemaError(ValueError):
    """La sorgente non espone le colonne minime richieste."""


class CodiceAnomalia(StrEnum):
    ID_MANCANTE = "ID_MANCANTE"
    NOME_MANCANTE = "NOME_MANCANTE"
    EMAIL_NON_VALIDA = "EMAIL_NON_VALIDA"
    SCADENZA_NON_VALIDA = "SCADENZA_NON_VALIDA"
    STATO_NON_VALIDO = "STATO_NON_VALIDO"
    ID_DUPLICATO = "ID_DUPLICATO"


@dataclass(frozen=True, slots=True)
class MappaturaColonne:
    id_arbitro: str = "id_arbitro"
    nome: str = "nome"
    email: str = "email"
    scadenza_certificato: str = "scadenza_certificato"
    attivo: str = "attivo"
    nome_saluto: str | None = None

    @property
    def obbligatorie(self) -> tuple[str, ...]:
        return (
            self.id_arbitro,
            self.nome,
            self.email,
            self.scadenza_certificato,
            self.attivo,
        )


@dataclass(frozen=True, slots=True)
class PoliticaStato:
    valori_attivi: frozenset[str] = frozenset(
        {"1", "true", "si", "sì", "attivo", "operativo"}
    )
    valori_inattivi: frozenset[str] = frozenset(
        {"0", "false", "no", "inattivo", "non operativo"}
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
    return None


def _parse_attivo(value: Any, politica: PoliticaStato) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and value in (0, 1):
        return bool(value)

    normalizzato = _testo(value).casefold()
    if normalizzato in politica.valori_attivi:
        return True
    if normalizzato in politica.valori_inattivi:
        return False
    return None


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
    """Converte righe grezze in arbitri validi e raccoglie anomalie non fatali.

    Gli ID duplicati vengono esclusi integralmente: inviare a una riga arbitraria
    sarebbe più rischioso che richiedere una correzione del dato sorgente.
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
    candidati: list[tuple[int, Arbitro]] = []
    righe_vuote = 0

    for offset, riga in enumerate(righe):
        numero_riga = prima_riga_dati + offset
        if _riga_vuota(riga):
            righe_vuote += 1
            continue

        id_arbitro = _testo(riga.get(mappatura.id_arbitro))
        nome = _testo(riga.get(mappatura.nome))
        email = _testo(riga.get(mappatura.email))
        scadenza = _parse_data(riga.get(mappatura.scadenza_certificato))
        attivo = _parse_attivo(riga.get(mappatura.attivo), politica_stato)
        nome_saluto = (
            _testo(riga.get(mappatura.nome_saluto))
            if mappatura.nome_saluto
            else ""
        )

        errori_riga: list[AnomaliaDati] = []
        if not id_arbitro:
            errori_riga.append(
                AnomaliaDati(
                    numero_riga,
                    CodiceAnomalia.ID_MANCANTE,
                    mappatura.id_arbitro,
                    "identificativo arbitro mancante",
                )
            )
        if not nome:
            errori_riga.append(
                AnomaliaDati(
                    numero_riga,
                    CodiceAnomalia.NOME_MANCANTE,
                    mappatura.nome,
                    "nome arbitro mancante",
                    id_arbitro or None,
                )
            )
        if not email_valida(email):
            errori_riga.append(
                AnomaliaDati(
                    numero_riga,
                    CodiceAnomalia.EMAIL_NON_VALIDA,
                    mappatura.email,
                    "indirizzo email mancante o non valido",
                    id_arbitro or None,
                )
            )
        if scadenza is None:
            errori_riga.append(
                AnomaliaDati(
                    numero_riga,
                    CodiceAnomalia.SCADENZA_NON_VALIDA,
                    mappatura.scadenza_certificato,
                    "data di scadenza non valida; usare YYYY-MM-DD o GG/MM/AAAA",
                    id_arbitro or None,
                )
            )
        if attivo is None:
            errori_riga.append(
                AnomaliaDati(
                    numero_riga,
                    CodiceAnomalia.STATO_NON_VALIDO,
                    mappatura.attivo,
                    "stato non riconosciuto",
                    id_arbitro or None,
                )
            )

        if errori_riga:
            anomalie.extend(errori_riga)
            continue

        assert scadenza is not None and attivo is not None
        candidati.append(
            (
                numero_riga,
                Arbitro(
                    id_arbitro=id_arbitro,
                    nome=nome,
                    email=email,
                    scadenza_certificato=scadenza,
                    attivo=attivo,
                    nome_saluto=nome_saluto or None,
                ),
            )
        )

    conteggi = Counter(arbitro.id_arbitro for _, arbitro in candidati)
    duplicati = {id_arbitro for id_arbitro, numero in conteggi.items() if numero > 1}

    validi: list[Arbitro] = []
    for numero_riga, arbitro in candidati:
        if arbitro.id_arbitro in duplicati:
            anomalie.append(
                AnomaliaDati(
                    numero_riga,
                    CodiceAnomalia.ID_DUPLICATO,
                    mappatura.id_arbitro,
                    "identificativo presente in più righe; tutte le occorrenze sono escluse",
                    arbitro.id_arbitro,
                )
            )
        else:
            validi.append(arbitro)

    return EsitoValidazione(
        arbitri=tuple(validi),
        anomalie=tuple(sorted(anomalie, key=lambda item: (item.numero_riga, item.codice))),
        righe_totali=len(righe),
        righe_vuote_ignorate=righe_vuote,
    )
