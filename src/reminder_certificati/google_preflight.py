"""Preflight Google in sola lettura prima dei collaudi esterni.

Il modulo verifica soltanto identificatori, metadati delle tab e righe di
intestazione. Non legge righe operative, non scrive celle e non usa SMTP.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol, Sequence

from .admin_schema import NOMI_TAB_AMMINISTRATIVE, crea_schema_amministrativo
from .google_runtime import ConfigurazioneRisorseGoogle


COLONNE_OPERATIVO_VERIFICATE: tuple[str, ...] = (
    "Tessera",
    "Cognome",
    "Nome",
    "Qualifica",
    "Stato Rinnovo",
    "Data Scadenza Certificato",
    "e-Mail",
    "Certificato medico",
    "Rinnovato senza lista",
    "Lista effettiva di appartenenza",
    "Esordiente",
    "Note",
    "Fa attività quest'anno",
)


class ErrorePreflightGoogle(RuntimeError):
    """Risorse Google mancanti, ambigue o strutturalmente incompatibili."""


class TrasportoPreflightGoogle(Protocol):
    def elenca_tab(self, *, spreadsheet_id: str) -> Sequence[str]: ...

    def leggi_intestazioni(
        self,
        *,
        spreadsheet_id: str,
        nome_tab: str,
        riga: int,
    ) -> Sequence[Any]: ...


@dataclass(frozen=True, slots=True)
class EsitoPreflightGoogle:
    operativo_headers_ok: bool
    admin_tabs_ok: bool
    admin_headers_ok: bool
    operativo_data_rows_read: int = 0
    writes_performed: int = 0
    smtp_checked: bool = False
    admin_write_verified: bool = False


@dataclass(frozen=True, slots=True)
class PreflightGoogle:
    trasporto: TrasportoPreflightGoogle

    def esegui(self, *, risorse: ConfigurazioneRisorseGoogle) -> EsitoPreflightGoogle:
        if risorse.operativo_spreadsheet_id == risorse.admin_spreadsheet_id:
            raise ErrorePreflightGoogle(
                "OPERATIVO_SPREADSHEET_ID e ADMIN_SPREADSHEET_ID devono indicare file distinti"
            )

        tab_admin = tuple(
            str(nome).strip()
            for nome in self.trasporto.elenca_tab(
                spreadsheet_id=risorse.admin_spreadsheet_id
            )
        )
        if tab_admin != NOMI_TAB_AMMINISTRATIVE:
            raise ErrorePreflightGoogle(
                "Spreadsheet amministrativo: tab mancanti, duplicate o fuori ordine"
            )

        schema = crea_schema_amministrativo()
        for definizione in schema.tab:
            attuali = _normalizza_intestazioni(
                self.trasporto.leggi_intestazioni(
                    spreadsheet_id=risorse.admin_spreadsheet_id,
                    nome_tab=definizione.nome,
                    riga=1,
                )
            )
            if attuali != definizione.intestazioni:
                raise ErrorePreflightGoogle(
                    f"Spreadsheet amministrativo: intestazioni non conformi nella tab {definizione.nome}"
                )

        intestazioni_operativo = _normalizza_intestazioni(
            self.trasporto.leggi_intestazioni(
                spreadsheet_id=risorse.operativo_spreadsheet_id,
                nome_tab=risorse.operativo_sheet_name,
                riga=risorse.operativo_header_row,
            )
        )
        mancanti = [
            nome
            for nome in COLONNE_OPERATIVO_VERIFICATE
            if nome not in intestazioni_operativo
        ]
        if mancanti:
            raise ErrorePreflightGoogle(
                "Operativo: intestazioni obbligatorie mancanti: " + ", ".join(mancanti)
            )

        return EsitoPreflightGoogle(
            operativo_headers_ok=True,
            admin_tabs_ok=True,
            admin_headers_ok=True,
        )


def _normalizza_intestazioni(valori: Sequence[Any]) -> tuple[str, ...]:
    normalizzate = tuple("" if valore is None else str(valore).strip() for valore in valori)
    fine = len(normalizzate)
    while fine and not normalizzate[fine - 1]:
        fine -= 1
    return normalizzate[:fine]


@dataclass(frozen=True, slots=True)
class TrasportoPreflightGoogleApi:
    servizio: Any

    def elenca_tab(self, *, spreadsheet_id: str) -> Sequence[str]:
        risposta = (
            self.servizio.spreadsheets()
            .get(
                spreadsheetId=spreadsheet_id,
                includeGridData=False,
                fields="sheets.properties.title",
            )
            .execute()
        )
        fogli = risposta.get("sheets", []) if isinstance(risposta, Mapping) else []
        return tuple(
            str(foglio.get("properties", {}).get("title", ""))
            for foglio in fogli
            if isinstance(foglio, Mapping)
        )

    def leggi_intestazioni(
        self,
        *,
        spreadsheet_id: str,
        nome_tab: str,
        riga: int,
    ) -> Sequence[Any]:
        escaped = nome_tab.replace("'", "''")
        risposta = (
            self.servizio.spreadsheets()
            .values()
            .get(
                spreadsheetId=spreadsheet_id,
                range=f"'{escaped}'!A{riga}:ZZ{riga}",
                majorDimension="ROWS",
            )
            .execute()
        )
        valori = risposta.get("values", []) if isinstance(risposta, Mapping) else []
        if not valori:
            return ()
        prima = valori[0]
        return tuple(prima) if isinstance(prima, Sequence) else ()
