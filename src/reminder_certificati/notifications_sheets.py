from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Protocol

from .admin_store import (
    COLONNE_NOTIFICHE,
    ErroreArchivioNotifiche,
    RigaNotifica,
)
from .data_sources import ErroreSorgenteDati, tabella_da_matrice


class TrasportoNotificheSheets(Protocol):
    def leggi_valori(
        self,
        *,
        spreadsheet_id: str,
        intervallo_a1: str,
    ) -> Sequence[Sequence[Any]]: ...

    def aggiungi_riga(
        self,
        *,
        spreadsheet_id: str,
        intervallo_a1: str,
        valori: Sequence[Any],
    ) -> int: ...

    def aggiorna_riga(
        self,
        *,
        spreadsheet_id: str,
        intervallo_a1: str,
        valori: Sequence[Any],
    ) -> None: ...


def _obbligatorio(value: str, campo: str) -> str:
    normalizzato = value.strip()
    if not normalizzato:
        raise ErroreArchivioNotifiche(f"{campo} mancante")
    return normalizzato


def _nome_scheda_a1(nome_scheda: str) -> str:
    return nome_scheda.replace("'", "''")


def _valori_riga(riga: RigaNotifica) -> tuple[str, ...]:
    valori = riga.come_mappa()
    return tuple(valori[colonna] for colonna in COLONNE_NOTIFICHE)


@dataclass(slots=True)
class ArchivioNotificheGoogleSheets:
    trasporto: TrasportoNotificheSheets
    spreadsheet_id: str
    nome_scheda: str = "NOTIFICHE"
    colonne_a1: str = "A:K"
    _indice: dict[str, tuple[int, RigaNotifica]] | None = field(
        default=None,
        init=False,
        repr=False,
    )

    def _configurazione(self) -> tuple[str, str, str]:
        spreadsheet_id = _obbligatorio(self.spreadsheet_id, "spreadsheet_id")
        nome_scheda = _obbligatorio(self.nome_scheda, "nome_scheda")
        colonne = _obbligatorio(self.colonne_a1, "colonne_a1")
        scheda = _nome_scheda_a1(nome_scheda)
        return spreadsheet_id, nome_scheda, f"'{scheda}'!{colonne}"

    def _carica_indice(self) -> dict[str, tuple[int, RigaNotifica]]:
        if self._indice is not None:
            return self._indice

        spreadsheet_id, nome_scheda, intervallo = self._configurazione()
        try:
            matrice = self.trasporto.leggi_valori(
                spreadsheet_id=spreadsheet_id,
                intervallo_a1=intervallo,
            )
            tabella = tabella_da_matrice(
                matrice,
                nome_sorgente=f"Google Sheets:{nome_scheda}",
            )
        except (ErroreSorgenteDati, ErroreArchivioNotifiche):
            raise
        except Exception as exc:
            raise ErroreArchivioNotifiche(
                f"NOTIFICHE: lettura non riuscita: {type(exc).__name__}"
            ) from exc

        if tabella.intestazioni != COLONNE_NOTIFICHE:
            raise ErroreArchivioNotifiche(
                "NOTIFICHE: intestazioni diverse dallo schema canonico"
            )

        indice: dict[str, tuple[int, RigaNotifica]] = {}
        for numero_riga, valori in enumerate(tabella.righe, start=2):
            if all(not str(value).strip() for value in valori.values()):
                continue
            riga = RigaNotifica.da_mappa(valori)
            if riga.notification_id in indice:
                raise ErroreArchivioNotifiche(
                    f"NOTIFICHE: notification_id duplicato: {riga.notification_id}"
                )
            indice[riga.notification_id] = (numero_riga, riga)

        self._indice = indice
        return indice

    def ottieni(self, notification_id: str) -> RigaNotifica | None:
        chiave = _obbligatorio(notification_id, "notification_id")
        elemento = self._carica_indice().get(chiave)
        return elemento[1] if elemento is not None else None

    def elenca(self) -> tuple[RigaNotifica, ...]:
        indice = self._carica_indice()
        return tuple(indice[chiave][1] for chiave in sorted(indice))

    def ricarica(self) -> tuple[RigaNotifica, ...]:
        """Invalida la cache e rilegge il registro dalla sorgente remota."""

        self._indice = None
        return self.elenca()

    def salva(self, riga: RigaNotifica) -> RigaNotifica:
        spreadsheet_id, nome_scheda, _ = self._configurazione()
        indice = self._carica_indice()
        esistente = indice.get(riga.notification_id)
        valori = _valori_riga(riga)
        scheda = _nome_scheda_a1(nome_scheda)

        try:
            if esistente is None:
                numero_riga = self.trasporto.aggiungi_riga(
                    spreadsheet_id=spreadsheet_id,
                    intervallo_a1=f"'{scheda}'!A:K",
                    valori=valori,
                )
                if numero_riga < 2:
                    raise ErroreArchivioNotifiche(
                        "NOTIFICHE: numero della riga aggiunta non valido"
                    )
                indice[riga.notification_id] = (numero_riga, riga)
                return riga

            numero_riga, precedente = esistente
            if riga.creato_il != precedente.creato_il:
                raise ErroreArchivioNotifiche(
                    "NOTIFICHE: creato_il non può cambiare durante una transizione"
                )
            if riga.aggiornato_il < precedente.aggiornato_il:
                raise ErroreArchivioNotifiche(
                    "NOTIFICHE: aggiornato_il non può precedere la versione persistita"
                )
            self.trasporto.aggiorna_riga(
                spreadsheet_id=spreadsheet_id,
                intervallo_a1=f"'{scheda}'!A{numero_riga}:K{numero_riga}",
                valori=valori,
            )
            indice[riga.notification_id] = (numero_riga, riga)
            return riga
        except ErroreArchivioNotifiche:
            raise
        except Exception as exc:
            raise ErroreArchivioNotifiche(
                f"NOTIFICHE: scrittura non riuscita: {type(exc).__name__}"
            ) from exc


@dataclass(slots=True)
class TrasportoNotificheMemoria:
    matrice: list[list[Any]]
    letture: int = 0

    def leggi_valori(
        self,
        *,
        spreadsheet_id: str,
        intervallo_a1: str,
    ) -> Sequence[Sequence[Any]]:
        _obbligatorio(spreadsheet_id, "spreadsheet_id")
        _obbligatorio(intervallo_a1, "intervallo_a1")
        self.letture += 1
        return [list(riga) for riga in self.matrice]

    def aggiungi_riga(
        self,
        *,
        spreadsheet_id: str,
        intervallo_a1: str,
        valori: Sequence[Any],
    ) -> int:
        _obbligatorio(spreadsheet_id, "spreadsheet_id")
        _obbligatorio(intervallo_a1, "intervallo_a1")
        self.matrice.append(list(valori))
        return len(self.matrice)

    def aggiorna_riga(
        self,
        *,
        spreadsheet_id: str,
        intervallo_a1: str,
        valori: Sequence[Any],
    ) -> None:
        _obbligatorio(spreadsheet_id, "spreadsheet_id")
        riferimento = _obbligatorio(intervallo_a1, "intervallo_a1")
        match = re.search(r"!A(\d+):K\d+$", riferimento)
        if match is None:
            raise ErroreArchivioNotifiche(
                f"intervallo di aggiornamento non valido: {riferimento}"
            )
        numero_riga = int(match.group(1))
        if numero_riga < 2 or numero_riga > len(self.matrice):
            raise ErroreArchivioNotifiche(
                f"riga di aggiornamento inesistente: {numero_riga}"
            )
        self.matrice[numero_riga - 1] = list(valori)


@dataclass(frozen=True, slots=True)
class TrasportoNotificheGoogleApi:
    servizio: Any

    def leggi_valori(
        self,
        *,
        spreadsheet_id: str,
        intervallo_a1: str,
    ) -> Sequence[Sequence[Any]]:
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
        if not isinstance(risposta, Mapping):
            raise ErroreArchivioNotifiche(
                "Google Sheets: risposta di lettura non valida"
            )
        valori = risposta.get("values", [])
        if not isinstance(valori, Sequence) or isinstance(valori, (str, bytes)):
            raise ErroreArchivioNotifiche("Google Sheets: campo values non valido")
        return valori

    def aggiungi_riga(
        self,
        *,
        spreadsheet_id: str,
        intervallo_a1: str,
        valori: Sequence[Any],
    ) -> int:
        risposta = (
            self.servizio.spreadsheets()
            .values()
            .append(
                spreadsheetId=spreadsheet_id,
                range=intervallo_a1,
                valueInputOption="RAW",
                insertDataOption="INSERT_ROWS",
                body={"majorDimension": "ROWS", "values": [list(valori)]},
            )
            .execute()
        )
        if not isinstance(risposta, Mapping):
            raise ErroreArchivioNotifiche("Google Sheets: risposta append non valida")
        aggiornamenti = risposta.get("updates", {})
        intervallo = (
            aggiornamenti.get("updatedRange", "")
            if isinstance(aggiornamenti, Mapping)
            else ""
        )
        match = re.search(r"![A-Z]+(\d+):[A-Z]+\d+$", str(intervallo))
        if match is None:
            raise ErroreArchivioNotifiche(
                "Google Sheets: riga aggiunta non determinabile"
            )
        return int(match.group(1))

    def aggiorna_riga(
        self,
        *,
        spreadsheet_id: str,
        intervallo_a1: str,
        valori: Sequence[Any],
    ) -> None:
        (
            self.servizio.spreadsheets()
            .values()
            .update(
                spreadsheetId=spreadsheet_id,
                range=intervallo_a1,
                valueInputOption="RAW",
                body={"majorDimension": "ROWS", "values": [list(valori)]},
            )
            .execute()
        )
