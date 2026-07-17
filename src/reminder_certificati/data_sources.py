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


class ErroreSorgenteDati(RuntimeError):
    """La sorgente non può essere letta o presenta una struttura ambigua."""


@dataclass(frozen=True, slots=True)
class TabellaDati:
    """Tabella normalizzata, indipendente dalla tecnologia di origine."""

    intestazioni: tuple[str, ...]
    righe: tuple[Mapping[str, Any], ...]
    nome_sorgente: str
    prima_riga_dati: int = 2


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
    """Converte una matrice con intestazione nella prima riga in record mappati.

    Le colonne eccedenti non vuote vengono rifiutate per evitare perdite di dati
    silenziose. Le righe corte vengono invece completate con valori vuoti.
    ``prima_riga_dati`` conserva il numero di riga originale della sorgente, così
    le anomalie possono essere ricondotte alla riga corretta del foglio.
    """
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
                f"{nome_sorgente}: riga {numero_riga} contiene valori oltre "
                "le intestazioni"
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
    """Adapter testabile che non gestisce direttamente le credenziali Google."""

    lettore: LettoreValoriSheets
    spreadsheet_id: str
    nome_scheda: str
    colonne_a1: str = "A:ZZ"
    riga_intestazioni: int = 1

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
        if self.riga_intestazioni < 1:
            raise ErroreSorgenteDati(
                "Google Sheets: riga_intestazioni deve essere almeno 1"
            )

        scheda_escaped = nome_scheda.replace("'", "''")
        colonne_con_riga = _intervallo_da_riga(colonne, self.riga_intestazioni)
        intervallo = f"'{scheda_escaped}'!{colonne_con_riga}"
        matrice = self.lettore.leggi_valori(
            spreadsheet_id=spreadsheet_id,
            intervallo_a1=intervallo,
        )
        return tabella_da_matrice(
            matrice,
            nome_sorgente=f"Google Sheets:{nome_scheda}",
            prima_riga_dati=self.riga_intestazioni + 1,
        )


def _intervallo_da_riga(colonne_a1: str, riga: int) -> str:
    """Trasforma ``A:F`` in ``A2:F`` senza accettare range ambigui."""
    parti = colonne_a1.split(":")
    if len(parti) != 2 or not all(parte.isalpha() for parte in parti):
        raise ErroreSorgenteDati(
            "Google Sheets: intervallo colonne deve avere forma A:ZZ"
        )
    inizio, fine = (parte.upper() for parte in parti)
    return f"{inizio}{riga}:{fine}"


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
        prima_riga_dati=tabella.prima_riga_dati,
    )
