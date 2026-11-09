from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Protocol

from .validation import (
    EsitoValidazione,
    MappaturaColonne,
    PoliticaStato,
    valida_righe,
)

_NUM_RETRIES_LETTURE_GOOGLE = 5


class ErroreSorgenteDati(RuntimeError):
    """La sorgente non può essere letta o presenta una struttura ambigua."""


@dataclass(frozen=True, slots=True)
class TabellaDati:
    intestazioni: tuple[str, ...]
    righe: tuple[Mapping[str, Any], ...]
    nome_sorgente: str
    prima_riga_dati: int = 2


class SorgenteDati(Protocol):
    def leggi(self) -> TabellaDati: ...


class LettoreValoriSheets(Protocol):
    def leggi_valori(
        self,
        *,
        spreadsheet_id: str,
        intervallo_a1: str,
    ) -> Sequence[Sequence[Any]]: ...

    def leggi_intervalli(
        self,
        *,
        spreadsheet_id: str,
        intervalli_a1: Sequence[str],
    ) -> Sequence[Sequence[Sequence[Any]]]: ...


def _riga_sequenza(value: Any, *, nome_sorgente: str, numero_riga: int) -> Sequence[Any]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ErroreSorgenteDati(
            f"{nome_sorgente}: riga {numero_riga} non è una sequenza di celle"
        )
    return value


def tabella_da_matrice(
    matrice: Sequence[Sequence[Any]],
    *,
    nome_sorgente: str,
    prima_riga_dati: int = 2,
) -> TabellaDati:
    if prima_riga_dati < 2:
        raise ErroreSorgenteDati(
            f"{nome_sorgente}: prima_riga_dati deve essere almeno 2"
        )
    if isinstance(matrice, (str, bytes)) or not isinstance(matrice, Sequence):
        raise ErroreSorgenteDati(f"{nome_sorgente}: matrice non valida")
    if not matrice:
        raise ErroreSorgenteDati(f"{nome_sorgente}: nessun dato disponibile")

    riga_intestazioni = _riga_sequenza(
        matrice[0], nome_sorgente=nome_sorgente, numero_riga=prima_riga_dati - 1
    )
    intestazioni = tuple(str(value).strip() for value in riga_intestazioni)
    if not intestazioni or all(not value for value in intestazioni):
        raise ErroreSorgenteDati(f"{nome_sorgente}: intestazioni mancanti")
    if any(not value for value in intestazioni):
        raise ErroreSorgenteDati(f"{nome_sorgente}: intestazione vuota")

    conteggi = Counter(intestazioni)
    duplicati = sorted(value for value, count in conteggi.items() if count > 1)
    if duplicati:
        raise ErroreSorgenteDati(
            f"{nome_sorgente}: intestazioni duplicate: {', '.join(duplicati)}"
        )

    righe: list[Mapping[str, Any]] = []
    larghezza = len(intestazioni)
    for numero_riga, valori_originali in enumerate(
        matrice[1:], start=prima_riga_dati
    ):
        riga = _riga_sequenza(
            valori_originali,
            nome_sorgente=nome_sorgente,
            numero_riga=numero_riga,
        )
        valori = list(riga)
        eccedenti = valori[larghezza:]
        if any(str(value).strip() for value in eccedenti):
            raise ErroreSorgenteDati(
                f"{nome_sorgente}: riga {numero_riga} contiene valori oltre le intestazioni"
            )
        valori = valori[:larghezza] + [""] * max(0, larghezza - len(valori))
        righe.append(dict(zip(intestazioni, valori, strict=True)))

    return TabellaDati(
        intestazioni=intestazioni,
        righe=tuple(righe),
        nome_sorgente=nome_sorgente,
        prima_riga_dati=prima_riga_dati,
    )


@dataclass(frozen=True, slots=True)
class SorgenteMemoria:
    matrice: Sequence[Sequence[Any]]
    nome: str = "memoria"

    def leggi(self) -> TabellaDati:
        return tabella_da_matrice(self.matrice, nome_sorgente=self.nome)


@dataclass(frozen=True, slots=True)
class AdapterGoogleSheets:
    """Legge la riga intestazioni e poi soltanto le colonne richieste dalla mappatura."""

    lettore: LettoreValoriSheets
    spreadsheet_id: str
    nome_scheda: str
    colonne_a1: str = "A:ZZ"
    riga_intestazioni: int = 1
    mappatura: MappaturaColonne = MappaturaColonne()

    def leggi(self) -> TabellaDati:
        spreadsheet_id = self.spreadsheet_id.strip()
        nome_scheda = self.nome_scheda.strip()
        if not spreadsheet_id:
            raise ErroreSorgenteDati("Google Sheets: spreadsheet_id mancante")
        if not nome_scheda:
            raise ErroreSorgenteDati("Google Sheets: nome_scheda mancante")
        if self.riga_intestazioni < 1:
            raise ErroreSorgenteDati(
                "Google Sheets: riga_intestazioni deve essere almeno 1"
            )

        inizio, _ = _limiti_colonne(self.colonne_a1)
        scheda = nome_scheda.replace("'", "''")
        header_range = _intervallo_riga(self.colonne_a1, self.riga_intestazioni)
        matrice_header = self.lettore.leggi_valori(
            spreadsheet_id=spreadsheet_id,
            intervallo_a1=f"'{scheda}'!{header_range}",
        )
        intestazioni = _prima_riga(matrice_header)
        posizioni = _posizioni_obbligatorie(
            intestazioni,
            self.mappatura.obbligatorie,
        )

        prima_riga = self.riga_intestazioni + 1
        intervalli = tuple(
            f"'{scheda}'!{_indice_colonna(_colonna_indice(inizio) + indice)}{prima_riga}:"
            f"{_indice_colonna(_colonna_indice(inizio) + indice)}"
            for indice in posizioni
        )
        matrici = self.lettore.leggi_intervalli(
            spreadsheet_id=spreadsheet_id,
            intervalli_a1=intervalli,
        )
        if len(matrici) != len(self.mappatura.obbligatorie):
            raise ErroreSorgenteDati("Google Sheets: batchGet incompleto")

        colonne = [_appiattisci_colonna(matrice) for matrice in matrici]
        numero_righe = max((len(colonna) for colonna in colonne), default=0)
        righe = tuple(
            {
                nome: colonna[indice] if indice < len(colonna) else ""
                for nome, colonna in zip(
                    self.mappatura.obbligatorie,
                    colonne,
                    strict=True,
                )
            }
            for indice in range(numero_righe)
        )
        return TabellaDati(
            intestazioni=self.mappatura.obbligatorie,
            righe=righe,
            nome_sorgente=f"Google Sheets:{nome_scheda}",
            prima_riga_dati=prima_riga,
        )


def _prima_riga(matrice: Sequence[Sequence[Any]]) -> tuple[str, ...]:
    if not matrice:
        return ()
    prima = _riga_sequenza(matrice[0], nome_sorgente="Google Sheets", numero_riga=1)
    valori = tuple("" if valore is None else str(valore).strip() for valore in prima)
    fine = len(valori)
    while fine and not valori[fine - 1]:
        fine -= 1
    return valori[:fine]


def _posizioni_obbligatorie(
    intestazioni: Sequence[str],
    obbligatorie: Sequence[str],
) -> tuple[int, ...]:
    posizioni: list[int] = []
    for nome in obbligatorie:
        trovate = [indice for indice, valore in enumerate(intestazioni) if valore == nome]
        if not trovate:
            raise ErroreSorgenteDati(f"Google Sheets: colonna obbligatoria mancante: {nome}")
        if len(trovate) > 1:
            raise ErroreSorgenteDati(f"Google Sheets: colonna obbligatoria duplicata: {nome}")
        posizioni.append(trovate[0])
    return tuple(posizioni)


def _appiattisci_colonna(matrice: Sequence[Sequence[Any]]) -> list[Any]:
    valori: list[Any] = []
    for riga in matrice:
        sequenza = _riga_sequenza(riga, nome_sorgente="Google Sheets", numero_riga=1)
        valori.append(sequenza[0] if sequenza else "")
    return valori


def _limiti_colonne(colonne_a1: str) -> tuple[str, str]:
    parti = colonne_a1.strip().split(":")
    if len(parti) != 2 or not all(parte.isalpha() for parte in parti):
        raise ErroreSorgenteDati(
            "Google Sheets: intervallo colonne deve avere forma A:ZZ"
        )
    inizio, fine = (parte.upper() for parte in parti)
    if _colonna_indice(inizio) > _colonna_indice(fine):
        raise ErroreSorgenteDati("Google Sheets: intervallo colonne invertito")
    return inizio, fine


def _intervallo_riga(colonne_a1: str, riga: int) -> str:
    inizio, fine = _limiti_colonne(colonne_a1)
    return f"{inizio}{riga}:{fine}{riga}"


def _colonna_indice(colonna: str) -> int:
    risultato = 0
    for carattere in colonna.upper():
        risultato = risultato * 26 + ord(carattere) - ord("A") + 1
    return risultato


def _indice_colonna(indice: int) -> str:
    if indice < 1:
        raise ValueError("indice colonna non valido")
    lettere: list[str] = []
    corrente = indice
    while corrente:
        corrente, resto = divmod(corrente - 1, 26)
        lettere.append(chr(ord("A") + resto))
    return "".join(reversed(lettere))


@dataclass(frozen=True, slots=True)
class LettoreGoogleApi:
    servizio: Any

    def leggi_valori(
        self,
        *,
        spreadsheet_id: str,
        intervallo_a1: str,
    ) -> Sequence[Sequence[Any]]:
        try:
            risposta = (
                self.servizio.spreadsheets()
                .values()
                .get(
                    spreadsheetId=spreadsheet_id,
                    range=intervallo_a1,
                    majorDimension="ROWS",
                )
                .execute(num_retries=_NUM_RETRIES_LETTURE_GOOGLE)
            )
        except Exception as exc:
            raise ErroreSorgenteDati(
                f"Google Sheets: lettura non riuscita: {type(exc).__name__}"
            ) from exc
        return _valori_risposta(risposta)

    def leggi_intervalli(
        self,
        *,
        spreadsheet_id: str,
        intervalli_a1: Sequence[str],
    ) -> Sequence[Sequence[Sequence[Any]]]:
        try:
            risposta = (
                self.servizio.spreadsheets()
                .values()
                .batchGet(
                    spreadsheetId=spreadsheet_id,
                    ranges=list(intervalli_a1),
                    majorDimension="ROWS",
                )
                .execute(num_retries=_NUM_RETRIES_LETTURE_GOOGLE)
            )
        except Exception as exc:
            raise ErroreSorgenteDati(
                f"Google Sheets: lettura batch non riuscita: {type(exc).__name__}"
            ) from exc
        if not isinstance(risposta, Mapping):
            raise ErroreSorgenteDati("Google Sheets: risposta batch non valida")
        elementi = risposta.get("valueRanges", [])
        if not isinstance(elementi, Sequence) or isinstance(elementi, (str, bytes)):
            raise ErroreSorgenteDati("Google Sheets: valueRanges non valido")
        risultato: list[Sequence[Sequence[Any]]] = []
        for elemento in elementi:
            if not isinstance(elemento, Mapping):
                raise ErroreSorgenteDati("Google Sheets: elemento batch non valido")
            risultato.append(_valori_risposta(elemento))
        return risultato


def _valori_risposta(risposta: Any) -> Sequence[Sequence[Any]]:
    if not isinstance(risposta, Mapping):
        raise ErroreSorgenteDati("Google Sheets: risposta API non valida")
    valori = risposta.get("values", [])
    if not isinstance(valori, Sequence) or isinstance(valori, (str, bytes)):
        raise ErroreSorgenteDati("Google Sheets: campo values non valido")
    return valori


def leggi_e_valida(
    sorgente: SorgenteDati,
    *,
    mappatura: MappaturaColonne = MappaturaColonne(),
    politica_stato: PoliticaStato = PoliticaStato(),
) -> EsitoValidazione:
    tabella = sorgente.leggi()
    return valida_righe(
        tabella.righe,
        intestazioni=tabella.intestazioni,
        mappatura=mappatura,
        politica_stato=politica_stato,
        prima_riga_dati=tabella.prima_riga_dati,
    )
