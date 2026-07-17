from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol, Sequence

from .validation import (
    EsitoValidazione,
    MappaturaColonne,
    PoliticaStato,
    valida_righe,
)


class ErroreSorgenteDati(RuntimeError):
    """La sorgente non può essere letta o presenta una struttura ambigua."""


@dataclass(frozen=True, slots=True)
class TabellaDati:
    """Tabella normalizzata, indipendente dalla tecnologia di origine."""

    intestazioni: tuple[str, ...]
    righe: tuple[Mapping[str, Any], ...]
    nome_sorgente: str


class SorgenteDati(Protocol):
    def leggi(self) -> TabellaDati:
        """Restituisce intestazioni e righe senza applicare regole di dominio."""


class LettoreValoriSheets(Protocol):
    def leggi_valori(
        self,
        *,
        spreadsheet_id: str,
        intervallo_a1: str,
    ) -> Sequence[Sequence[Any]]:
        """Legge una matrice di valori dalla Google Sheets API."""


def tabella_da_matrice(
    matrice: Sequence[Sequence[Any]],
    *,
    nome_sorgente: str,
) -> TabellaDati:
    """Converte una matrice con intestazione nella prima riga in record mappati.

    Le colonne eccedenti non vuote vengono rifiutate per evitare perdite di dati
    silenziose. Le righe corte vengono invece completate con valori vuoti.
    """

    if not matrice:
        raise ErroreSorgenteDati(f"{nome_sorgente}: nessun dato disponibile")

    intestazioni = tuple(str(value).strip() for value in matrice[0])
    if not intestazioni or all(not value for value in intestazioni):
        raise ErroreSorgenteDati(f"{nome_sorgente}: intestazioni mancanti")
    if any(not value for value in intestazioni):
        raise ErroreSorgenteDati(f"{nome_sorgente}: intestazione vuota")

    duplicati = sorted(
        {value for value in intestazioni if intestazioni.count(value) > 1}
    )
    if duplicati:
        raise ErroreSorgenteDati(
            f"{nome_sorgente}: intestazioni duplicate: {', '.join(duplicati)}"
        )

    righe: list[Mapping[str, Any]] = []
    larghezza = len(intestazioni)
    for numero_riga, valori_originali in enumerate(matrice[1:], start=2):
        valori = list(valori_originali)
        eccedenti = valori[larghezza:]
        if any(str(value).strip() for value in eccedenti):
            raise ErroreSorgenteDati(
                f"{nome_sorgente}: riga {numero_riga} contiene valori oltre "
                "le intestazioni"
            )
        valori = valori[:larghezza] + [""] * max(0, larghezza - len(valori))
        righe.append(dict(zip(intestazioni, valori, strict=True)))

    return TabellaDati(
        intestazioni=intestazioni,
        righe=tuple(righe),
        nome_sorgente=nome_sorgente,
    )


@dataclass(frozen=True, slots=True)
class SorgenteMemoria:
    matrice: Sequence[Sequence[Any]]
    nome: str = "memoria"

    def leggi(self) -> TabellaDati:
        return tabella_da_matrice(self.matrice, nome_sorgente=self.nome)


@dataclass(frozen=True, slots=True)
class AdapterGoogleSheets:
    """Adapter testabile che non gestisce direttamente le credenziali Google."""

    lettore: LettoreValoriSheets
    spreadsheet_id: str
    nome_scheda: str
    colonne_a1: str = "A:ZZ"

    def leggi(self) -> TabellaDati:
        spreadsheet_id = self.spreadsheet_id.strip()
        nome_scheda = self.nome_scheda.strip()
        colonne = self.colonne_a1.strip()
        if not spreadsheet_id:
            raise ErroreSorgenteDati("Google Sheets: spreadsheet_id mancante")
        if not nome_scheda:
            raise ErroreSorgenteDati("Google Sheets: nome_scheda mancante")
        if not colonne:
            raise ErroreSorgenteDati("Google Sheets: intervallo colonne mancante")

        scheda_escaped = nome_scheda.replace("'", "''")
        intervallo = f"'{scheda_escaped}'!{colonne}"
        matrice = self.lettore.leggi_valori(
            spreadsheet_id=spreadsheet_id,
            intervallo_a1=intervallo,
        )
        return tabella_da_matrice(
            matrice,
            nome_sorgente=f"Google Sheets:{nome_scheda}",
        )


@dataclass(frozen=True, slots=True)
class LettoreGoogleApi:
    """Ponte minimale verso un servizio Google API già autenticato.

    Il servizio viene costruito fuori da questo modulo. In produzione sarà
    inizializzato con un service account e scope di sola lettura.
    """

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
                .execute()
            )
        except Exception as exc:  # convertito in errore applicativo stabile
            raise ErroreSorgenteDati(
                f"Google Sheets: lettura non riuscita: {type(exc).__name__}"
            ) from exc

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
    """Collega una sorgente alla validazione senza introdurre effetti collaterali."""

    tabella = sorgente.leggi()
    return valida_righe(
        tabella.righe,
        intestazioni=tabella.intestazioni,
        mappatura=mappatura,
        politica_stato=politica_stato,
        prima_riga_dati=2,
    )
