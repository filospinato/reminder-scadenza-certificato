"""Preflight Google in sola lettura prima dei collaudi esterni.

Il modulo verifica soltanto identificatori, metadati delle tab e righe di
intestazione. Non legge righe operative, non scrive celle e non usa SMTP.
Gli errori pubblici usano codici stabili e indicazioni operative prive di PII.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Mapping, Protocol, Sequence

from .admin_schema import NOMI_TAB_AMMINISTRATIVE, crea_schema_amministrativo
from .google_runtime import (
    COLONNE_OPERATIVO_OBBLIGATORIE,
    ConfigurazioneRisorseGoogle,
)


class CodiceErrorePreflight(StrEnum):
    RISORSE_COINCIDENTI = "PREFLIGHT_RESOURCE_IDS_EQUAL"
    ADMIN_NON_RAGGIUNGIBILE = "PREFLIGHT_ADMIN_UNREACHABLE"
    ADMIN_TAB_NON_CONFORMI = "PREFLIGHT_ADMIN_TABS_INVALID"
    ADMIN_INTESTAZIONI_NON_LEGGIBILI = "PREFLIGHT_ADMIN_HEADERS_UNREADABLE"
    ADMIN_INTESTAZIONI_NON_CONFORMI = "PREFLIGHT_ADMIN_HEADERS_INVALID"
    OPERATIVO_NON_RAGGIUNGIBILE = "PREFLIGHT_OPERATIVO_UNREACHABLE"
    OPERATIVO_INTESTAZIONI_MANCANTI = "PREFLIGHT_OPERATIVO_HEADERS_MISSING"


@dataclass(frozen=True, slots=True)
class DiagnosticaPreflight:
    codice: CodiceErrorePreflight
    messaggio: str
    azione_runbook: str


class ErrorePreflightGoogle(RuntimeError):
    """Errore pubblico, stabile e privo di payload Google o identificatori."""

    def __init__(self, diagnostica: DiagnosticaPreflight) -> None:
        super().__init__(diagnostica.messaggio)
        self.diagnostica = diagnostica


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
                DiagnosticaPreflight(
                    CodiceErrorePreflight.RISORSE_COINCIDENTI,
                    "Operativo e amministrazione devono indicare file distinti.",
                    "Correggere le Variables pubbliche dei due Spreadsheet e ripetere il preflight.",
                )
            )

        try:
            tab_admin = tuple(
                str(nome).strip()
                for nome in self.trasporto.elenca_tab(
                    spreadsheet_id=risorse.admin_spreadsheet_id
                )
            )
        except Exception as exc:
            raise ErrorePreflightGoogle(
                DiagnosticaPreflight(
                    CodiceErrorePreflight.ADMIN_NON_RAGGIUNGIBILE,
                    "Lo Spreadsheet amministrativo non è raggiungibile in lettura.",
                    "Verificare condivisione, ID pubblico e identità WIF del service account.",
                )
            ) from exc

        if len(tab_admin) != len(NOMI_TAB_AMMINISTRATIVE) or set(tab_admin) != set(
            NOMI_TAB_AMMINISTRATIVE
        ):
            raise ErrorePreflightGoogle(
                DiagnosticaPreflight(
                    CodiceErrorePreflight.ADMIN_TAB_NON_CONFORMI,
                    "Le tab amministrative sono mancanti o non conformi.",
                    "Eseguire o verificare init-admin sul solo Spreadsheet amministrativo.",
                )
            )

        schema = crea_schema_amministrativo()
        for definizione in schema.tab:
            try:
                attuali = _normalizza_intestazioni(
                    self.trasporto.leggi_intestazioni(
                        spreadsheet_id=risorse.admin_spreadsheet_id,
                        nome_tab=definizione.nome,
                        riga=1,
                    )
                )
            except Exception as exc:
                raise ErrorePreflightGoogle(
                    DiagnosticaPreflight(
                        CodiceErrorePreflight.ADMIN_INTESTAZIONI_NON_LEGGIBILI,
                        "Le intestazioni amministrative non sono leggibili.",
                        "Verificare permessi e integrità delle quattro tab amministrative.",
                    )
                ) from exc
            if attuali != definizione.intestazioni:
                raise ErrorePreflightGoogle(
                    DiagnosticaPreflight(
                        CodiceErrorePreflight.ADMIN_INTESTAZIONI_NON_CONFORMI,
                        "Le intestazioni amministrative non rispettano lo schema previsto.",
                        "Confrontare la riga 1 delle tab con docs/SCHEMA_FOGLI.md senza modificare Operativo.",
                    )
                )

        try:
            intestazioni_operativo = _normalizza_intestazioni(
                self.trasporto.leggi_intestazioni(
                    spreadsheet_id=risorse.operativo_spreadsheet_id,
                    nome_tab=risorse.operativo_sheet_name,
                    riga=risorse.operativo_header_row,
                )
            )
        except Exception as exc:
            raise ErrorePreflightGoogle(
                DiagnosticaPreflight(
                    CodiceErrorePreflight.OPERATIVO_NON_RAGGIUNGIBILE,
                    "La riga delle intestazioni di Operativo non è raggiungibile in lettura.",
                    "Verificare condivisione in sola lettura, nome tab e riga intestazioni.",
                )
            ) from exc

        mancanti = [
            nome
            for nome in COLONNE_OPERATIVO_OBBLIGATORIE
            if nome not in intestazioni_operativo
        ]
        if mancanti:
            raise ErrorePreflightGoogle(
                DiagnosticaPreflight(
                    CodiceErrorePreflight.OPERATIVO_INTESTAZIONI_MANCANTI,
                    "Operativo non contiene tutte le intestazioni usate dal reminder.",
                    "Verificare la sola riga 2 e aggiornare la mappatura soltanto dopo controllo umano.",
                )
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
