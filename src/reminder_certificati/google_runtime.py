"""Factory dei componenti Google usando ADC prodotti da WIF/OIDC.

Le importazioni Google sono intenzionalmente lazy: test e dry-run locali non
richiedono dipendenze Google. Il modulo non accetta chiavi JSON permanenti.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from .admin_initializer import TrasportoStrutturaGoogleApi
from .data_sources import AdapterGoogleSheets, LettoreGoogleApi
from .google_credentials_guard import verifica_credenziali_google_temporanee
from .monitoring import (
    AnomalieGoogleSheets,
    DashboardGoogleSheets,
    TrasportoMonitoraggioGoogleApi,
)
from .notifications_sheets import (
    ArchivioNotificheGoogleSheets,
    TrasportoNotificheGoogleApi,
)
from .validation import MappaturaColonne


class ErroreGoogleRuntime(RuntimeError):
    """Dipendenze, ADC o identificatori Google non sono disponibili."""


@dataclass(frozen=True, slots=True)
class ConfigurazioneRisorseGoogle:
    operativo_spreadsheet_id: str
    admin_spreadsheet_id: str
    operativo_sheet_name: str = "Operativo"
    operativo_header_row: int = 2
    operativo_columns_a1: str = "A:ZZ"

    @classmethod
    def da_ambiente(
        cls,
        ambiente: Mapping[str, str],
        *,
        richiedi_admin: bool = True,
    ) -> "ConfigurazioneRisorseGoogle":
        operativo = ambiente.get("OPERATIVO_SPREADSHEET_ID", "").strip()
        admin = ambiente.get("ADMIN_SPREADSHEET_ID", "").strip()
        if not operativo:
            raise ErroreGoogleRuntime("OPERATIVO_SPREADSHEET_ID mancante")
        if richiedi_admin and not admin:
            raise ErroreGoogleRuntime("ADMIN_SPREADSHEET_ID mancante")
        try:
            header = int(ambiente.get("OPERATIVO_HEADER_ROW", "2"))
        except ValueError as exc:
            raise ErroreGoogleRuntime("OPERATIVO_HEADER_ROW non valido") from exc
        if header < 1:
            raise ErroreGoogleRuntime("OPERATIVO_HEADER_ROW deve essere almeno 1")
        colonne = ambiente.get("OPERATIVO_COLUMNS_A1", "A:ZZ").strip()
        if not colonne:
            raise ErroreGoogleRuntime("OPERATIVO_COLUMNS_A1 mancante")
        return cls(
            operativo_spreadsheet_id=operativo,
            admin_spreadsheet_id=admin,
            operativo_sheet_name=ambiente.get(
                "OPERATIVO_SHEET_NAME", "Operativo"
            ).strip()
            or "Operativo",
            operativo_header_row=header,
            operativo_columns_a1=colonne,
        )


MAPPATURA_OPERATIVO_REALE = MappaturaColonne(
    id_arbitro="Tessera",
    nome="Nome",
    cognome="Cognome",
    email="e-Mail",
    scadenza_certificato="Data Scadenza Certificato",
    attivo="Fa attività quest'anno",
)


def costruisci_servizio_sheets() -> Any:
    """Costruisce il client soltanto con ADC temporanee prodotte da WIF/OIDC."""

    verifica_credenziali_google_temporanee(os.environ)
    try:
        from googleapiclient.discovery import build
    except ImportError as exc:
        raise ErroreGoogleRuntime(
            "installa l'extra [google] per usare Google Sheets"
        ) from exc
    try:
        return build("sheets", "v4", cache_discovery=False)
    except Exception as exc:
        raise ErroreGoogleRuntime(
            f"costruzione client Sheets non riuscita: {type(exc).__name__}"
        ) from exc


@dataclass(frozen=True, slots=True)
class ComponentiGoogle:
    sorgente_operativo: AdapterGoogleSheets
    archivio_notifiche: ArchivioNotificheGoogleSheets
    dashboard: DashboardGoogleSheets
    anomalie: AnomalieGoogleSheets
    trasporto_struttura: TrasportoStrutturaGoogleApi
    lettore: LettoreGoogleApi


def costruisci_componenti_google(
    *,
    servizio: Any,
    risorse: ConfigurazioneRisorseGoogle,
) -> ComponentiGoogle:
    lettore = LettoreGoogleApi(servizio)
    trasporto_notifiche = TrasportoNotificheGoogleApi(servizio)
    trasporto_monitoraggio = TrasportoMonitoraggioGoogleApi(servizio)
    return ComponentiGoogle(
        sorgente_operativo=AdapterGoogleSheets(
            lettore=lettore,
            spreadsheet_id=risorse.operativo_spreadsheet_id,
            nome_scheda=risorse.operativo_sheet_name,
            colonne_a1=risorse.operativo_columns_a1,
            riga_intestazioni=risorse.operativo_header_row,
        ),
        archivio_notifiche=ArchivioNotificheGoogleSheets(
            trasporto=trasporto_notifiche,
            spreadsheet_id=risorse.admin_spreadsheet_id,
        ),
        dashboard=DashboardGoogleSheets(
            trasporto=trasporto_monitoraggio,
            spreadsheet_id=risorse.admin_spreadsheet_id,
        ),
        anomalie=AnomalieGoogleSheets(
            trasporto=trasporto_monitoraggio,
            spreadsheet_id=risorse.admin_spreadsheet_id,
        ),
        trasporto_struttura=TrasportoStrutturaGoogleApi(servizio),
        lettore=lettore,
    )


def leggi_matrice_config(
    *,
    lettore: LettoreGoogleApi,
    spreadsheet_id: str,
) -> Sequence[Sequence[Any]]:
    identificativo = spreadsheet_id.strip()
    if not identificativo:
        raise ErroreGoogleRuntime("ADMIN_SPREADSHEET_ID mancante")
    return lettore.leggi_valori(
        spreadsheet_id=identificativo,
        intervallo_a1="'CONFIG'!A:E",
    )
