from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Protocol

from .admin_store import (
    COLONNE_NOTIFICHE,
    ErroreArchivioNotifiche,
    RigaNotifica,
)
from .data_sources import ErroreSorgenteDati, tabella_da_matrice


class TrasportoNotificheSheets(Protocol):
    """Operazioni minime richieste alla Google Sheets API."""

    def leggi_valori(
        self,
        *,
        spreadsheet_id: str,
        intervallo_a1: str,
    ) -> Sequence[Sequence[Any]]:
        """Legge intestazioni e righe della tab NOTIFICHE."""

    def aggiungi_riga(
        self,
        *,
        spreadsheet_id: str,
        intervallo_a1: str,
        valori: Sequence[Any],
    ) -> None:
        """Accoda una riga al registro."""

    def aggiorna_riga(
        self,
        *,
        spreadsheet_id: str,
        intervallo_a1: str,
        valori: Sequence[Any],
    ) -> None:
        """Sostituisce una riga già individuata in modo univoco."""


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


@dataclass(frozen=True, slots=True)
class ArchivioNotificheGoogleSheets:
    """Adapter della tab NOTIFICHE, testabile senza credenziali reali.

    Ogni salvataggio rilegge il registro, cerca la chiave esatta e accetta
    esclusivamente zero o una corrispondenza. Più corrispondenze bloccano la
    scrittura perché il foglio è ambiguo. La serializzazione tra esecuzioni
    resta responsabilità del workflow GitHub Actions tramite ``concurrency``.
    """

    trasporto: TrasportoNotificheSheets
    spreadsheet_id: str
    nome_scheda: str = "NOTIFICHE"
    colonne_a1: str = "A:N"

    def _configurazione(self) -> tuple[str, str, str]:
        spreadsheet_id = _obbligatorio(self.spreadsheet_id, "spreadsheet_id")
        nome_scheda = _obbligatorio(self.nome_scheda, "nome_scheda")
        colonne = _obbligatorio(self.colonne_a1, "colonne_a1")
        scheda = _nome_scheda_a1(nome_scheda)
        return spreadsheet_id, nome_scheda, f"'{scheda}'!{colonne}"

    def _leggi_righe_numerate(self) -> tuple[tuple[int, RigaNotifica], ...]:
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

        risultato: list[tuple[int, RigaNotifica]] = []
        for numero_riga, valori in enumerate(tabella.righe, start=2):
            if all(not str(value).strip() for value in valori.values()):
                continue
            risultato.append((numero_riga, RigaNotifica.da_mappa(valori)))
        return tuple(risultato)

    def ottieni(self, notification_id: str) -> RigaNotifica | None:
        chiave = _obbligatorio(notification_id, "notification_id")
        corrispondenze = [
            riga
            for _, riga in self._leggi_righe_numerate()
            if riga.notification_id == chiave
        ]
        if len(corrispondenze) > 1:
            raise ErroreArchivioNotifiche(
                f"NOTIFICHE: notification_id duplicato: {chiave}"
            )
        return corrispondenze[0] if corrispondenze else None

    def salva(self, riga: RigaNotifica) -> RigaNotifica:
        spreadsheet_id, nome_scheda, _ = self._configurazione()
        corrispondenze = [
            (numero_riga, esistente)
            for numero_riga, esistente in self._leggi_righe_numerate()
            if esistente.notification_id == riga.notification_id
        ]
        if len(corrispondenze) > 1:
            raise ErroreArchivioNotifiche(
                f"NOTIFICHE: notification_id duplicato: {riga.notification_id}"
            )

        valori = _valori_riga(riga)
        scheda = _nome_scheda_a1(nome_scheda)
        try:
            if not corrispondenze:
                self.trasporto.aggiungi_riga(
                    spreadsheet_id=spreadsheet_id,
                    intervallo_a1=f"'{scheda}'!A:N",
                    valori=valori,
                )
                return riga

            numero_riga, precedente = corrispondenze[0]
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
                intervallo_a1=f"'{scheda}'!A{numero_riga}:N{numero_riga}",
                valori=valori,
            )
            return riga
        except ErroreArchivioNotifiche:
            raise
        except Exception as exc:
            raise ErroreArchivioNotifiche(
                f"NOTIFICHE: scrittura non riuscita: {type(exc).__name__}"
            ) from exc


@dataclass(slots=True)
class TrasportoNotificheMemoria:
    """Fake tabellare che riproduce lettura, append e update di Sheets."""

    matrice: list[list[Any]]

    def leggi_valori(
        self,
        *,
        spreadsheet_id: str,
        intervallo_a1: str,
    ) -> Sequence[Sequence[Any]]:
        _obbligatorio(spreadsheet_id, "spreadsheet_id")
        _obbligatorio(intervallo_a1, "intervallo_a1")
        return [list(riga) for riga in self.matrice]

    def aggiungi_riga(
        self,
        *,
        spreadsheet_id: str,
        intervallo_a1: str,
        valori: Sequence[Any],
    ) -> None:
        _obbligatorio(spreadsheet_id, "spreadsheet_id")
        _obbligatorio(intervallo_a1, "intervallo_a1")
        self.matrice.append(list(valori))

    def aggiorna_riga(
        self,
        *,
        spreadsheet_id: str,
        intervallo_a1: str,
        valori: Sequence[Any],
    ) -> None:
        _obbligatorio(spreadsheet_id, "spreadsheet_id")
        riferimento = _obbligatorio(intervallo_a1, "intervallo_a1")
        try:
            numero_riga = int(riferimento.rsplit("A", maxsplit=1)[1].split(":", maxsplit=1)[0])
        except (IndexError, ValueError) as exc:
            raise ErroreArchivioNotifiche(
                f"intervallo di aggiornamento non valido: {riferimento}"
            ) from exc
        if numero_riga < 2 or numero_riga > len(self.matrice):
            raise ErroreArchivioNotifiche(
                f"riga di aggiornamento inesistente: {numero_riga}"
            )
        self.matrice[numero_riga - 1] = list(valori)


@dataclass(frozen=True, slots=True)
class TrasportoNotificheGoogleApi:
    """Ponte verso un servizio Google Sheets già autenticato."""

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
            raise ErroreArchivioNotifiche("Google Sheets: risposta di lettura non valida")
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
    ) -> None:
        (
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
