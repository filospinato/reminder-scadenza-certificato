"""Migrazione conservativa dello Spreadsheet amministrativo."""

from __future__ import annotations

import json
import os
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from .admin_schema import (
    COLONNE_CONFIG,
    COLONNE_DASHBOARD,
    VERSIONE_SCHEMA_AMMINISTRATIVO,
    configurazione_iniziale_sicura,
    crea_schema_amministrativo,
)
from .admin_store import COLONNE_NOTIFICHE
from .rules import TIPO_NOTIFICA_SCADENZA
from .runtime_config import carica_configurazione

COLONNE_CONFIG_V2: tuple[str, ...] = (
    "chiave",
    "valore",
    "tipo",
    "descrizione",
    "modificabile",
)
COLONNE_NOTIFICHE_LEGACY: tuple[str, ...] = (
    "notification_id",
    "id_arbitro",
    "nome",
    "cognome",
    "email",
    "scadenza_certificato",
    "tipo",
    "stato",
    "tentativi",
    "creato_il",
    "aggiornato_il",
    "message_id",
    "versione_app",
    "errore",
)


class ErroreMigrazioneAmministrativa(RuntimeError):
    """Il foglio non può essere migrato senza perdere controllo o dati."""


class TrasportoMigrazione(Protocol):
    def leggi_valori(
        self, *, spreadsheet_id: str, intervallo_a1: str
    ) -> Sequence[Sequence[Any]]: ...

    def sostituisci_tab(
        self,
        *,
        spreadsheet_id: str,
        nome_tab: str,
        valori: Sequence[Sequence[Any]],
    ) -> None: ...


@dataclass(frozen=True, slots=True)
class PianoMigrazione:
    config_prima: tuple[tuple[str, ...], ...]
    notifiche_prima: tuple[tuple[str, ...], ...]
    dashboard_prima: tuple[tuple[str, ...], ...]
    config_dopo: tuple[tuple[str, ...], ...]
    notifiche_dopo: tuple[tuple[str, ...], ...]
    dashboard_dopo: tuple[tuple[str, ...], ...]
    modifiche: tuple[str, ...]

    @property
    def necessaria(self) -> bool:
        return bool(self.modifiche)

    def salva_backup(self, path: Path) -> None:
        payload = {
            "config": [list(riga) for riga in self.config_prima],
            "notifiche": [list(riga) for riga in self.notifiche_prima],
            "dashboard": [list(riga) for riga in self.dashboard_prima],
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        contenuto = json.dumps(payload, ensure_ascii=False, indent=2)
        descrittore = os.open(
            path,
            os.O_WRONLY | os.O_CREAT | os.O_TRUNC,
            0o600,
        )
        try:
            with os.fdopen(descrittore, "w", encoding="utf-8") as file:
                file.write(contenuto)
        except Exception:
            try:
                os.close(descrittore)
            except OSError:
                pass
            raise
        path.chmod(0o600)


def prepara_piano(
    config: Sequence[Sequence[Any]],
    notifiche: Sequence[Sequence[Any]],
    dashboard: Sequence[Sequence[Any]] | None = None,
) -> PianoMigrazione:
    config_prima = _normalizza(config)
    notifiche_prima = _normalizza(notifiche)
    dashboard_prima = _normalizza(dashboard or ()) if dashboard is not None else ()

    notifiche_dopo = _migra_notifiche(notifiche_prima)
    config_legacy = not _config_corrente(config_prima)
    dashboard_legacy = dashboard is not None and not _dashboard_corrente(
        dashboard_prima
    )
    migrazione_necessaria = (
        config_legacy or notifiche_dopo != notifiche_prima or dashboard_legacy
    )

    config_dopo = _migra_config(
        config_prima,
        forza_disattivazione=migrazione_necessaria,
    )
    dashboard_dopo = (
        _migra_dashboard(
            dashboard_prima,
            forza_disattivazione=migrazione_necessaria,
        )
        if dashboard is not None
        else ()
    )
    carica_configurazione(config_dopo)

    modifiche: list[str] = []
    if config_dopo != config_prima:
        modifiche.append("CONFIG_SCHEMA_V3")
    if notifiche_dopo != notifiche_prima:
        modifiche.append("NOTIFICHE_MINIMIZZATE")
    if dashboard is not None and dashboard_dopo != dashboard_prima:
        modifiche.append("DASHBOARD_SCHEMA_V3")
    return PianoMigrazione(
        config_prima=config_prima,
        notifiche_prima=notifiche_prima,
        dashboard_prima=dashboard_prima,
        config_dopo=config_dopo,
        notifiche_dopo=notifiche_dopo,
        dashboard_dopo=dashboard_dopo,
        modifiche=tuple(modifiche),
    )


def applica_piano(
    piano: PianoMigrazione,
    *,
    trasporto: TrasportoMigrazione,
    spreadsheet_id: str,
) -> None:
    if piano.config_dopo != piano.config_prima:
        trasporto.sostituisci_tab(
            spreadsheet_id=spreadsheet_id,
            nome_tab="CONFIG",
            valori=piano.config_dopo,
        )
    if piano.notifiche_dopo != piano.notifiche_prima:
        trasporto.sostituisci_tab(
            spreadsheet_id=spreadsheet_id,
            nome_tab="NOTIFICHE",
            valori=piano.notifiche_dopo,
        )
    if piano.dashboard_dopo != piano.dashboard_prima:
        trasporto.sostituisci_tab(
            spreadsheet_id=spreadsheet_id,
            nome_tab="DASHBOARD",
            valori=piano.dashboard_dopo,
        )


def _config_corrente(matrice: tuple[tuple[str, ...], ...]) -> bool:
    if not matrice or matrice[0] != COLONNE_CONFIG:
        return False
    canoniche = {voce.chiave for voce in configurazione_iniziale_sicura()}
    valori = {
        riga[0]: riga[1]
        for riga in matrice[1:]
        if len(riga) == len(COLONNE_CONFIG) and riga[0]
    }
    return set(valori) == canoniche and valori.get("SCHEMA_VERSION") == str(
        VERSIONE_SCHEMA_AMMINISTRATIVO
    )


def _migra_config(
    matrice: tuple[tuple[str, ...], ...],
    *,
    forza_disattivazione: bool,
) -> tuple[tuple[str, ...], ...]:
    if not matrice or matrice[0] not in {COLONNE_CONFIG, COLONNE_CONFIG_V2}:
        raise ErroreMigrazioneAmministrativa("CONFIG: intestazioni non riconosciute")
    larghezza = len(matrice[0])
    valori: dict[str, str] = {}
    for riga in matrice[1:]:
        if not any(cella.strip() for cella in riga):
            continue
        if len(riga) != larghezza:
            raise ErroreMigrazioneAmministrativa(
                "CONFIG: riga con larghezza non valida"
            )
        chiave = riga[0].strip()
        if not chiave or chiave in valori:
            raise ErroreMigrazioneAmministrativa("CONFIG: chiave vuota o duplicata")
        valori[chiave] = riga[1]

    attivazione_precedente = valori.get(
        "INVIO_AUTOMATICO_ATTIVO",
        valori.get("AUTOMAZIONE_ATTIVA", "false"),
    )
    righe: list[tuple[str, ...]] = [COLONNE_CONFIG]
    for voce in configurazione_iniziale_sicura():
        valore = valori.get(voce.chiave, voce.valore)
        if voce.chiave == "SCHEMA_VERSION":
            valore = str(VERSIONE_SCHEMA_AMMINISTRATIVO)
        elif voce.chiave == "INVIO_AUTOMATICO_ATTIVO":
            valore = "false" if forza_disattivazione else attivazione_precedente
        righe.append((voce.chiave, valore, voce.descrizione))
    return tuple(righe)


def _dashboard_corrente(matrice: tuple[tuple[str, ...], ...]) -> bool:
    if not matrice or matrice[0] != COLONNE_DASHBOARD:
        return False
    chiavi: set[str] = set()
    for riga in matrice[1:]:
        if not any(cella.strip() for cella in riga):
            continue
        if len(riga) != len(COLONNE_DASHBOARD):
            return False
        chiave = riga[0].strip()
        if not chiave or chiave in chiavi:
            return False
        chiavi.add(chiave)
    return (
        "automazione_attiva" in chiavi
        and "invio_automatico_attivo" not in chiavi
        and "kill_switch" not in chiavi
    )


def _migra_dashboard(
    matrice: tuple[tuple[str, ...], ...],
    *,
    forza_disattivazione: bool,
) -> tuple[tuple[str, ...], ...]:
    canonica = crea_schema_amministrativo().ottieni_tab("DASHBOARD").matrice()
    if not matrice:
        return canonica
    if matrice[0] != COLONNE_DASHBOARD:
        raise ErroreMigrazioneAmministrativa("DASHBOARD: intestazioni non riconosciute")

    chiavi_originali: set[str] = set()
    for riga in matrice[1:]:
        if not any(cella.strip() for cella in riga):
            continue
        if len(riga) != len(COLONNE_DASHBOARD):
            raise ErroreMigrazioneAmministrativa(
                "DASHBOARD: riga con larghezza non valida"
            )
        chiave = riga[0].strip()
        if not chiave or chiave in chiavi_originali:
            raise ErroreMigrazioneAmministrativa("DASHBOARD: metrica vuota o duplicata")
        chiavi_originali.add(chiave)

    descrizione = "Indica se gli invii programmati sono abilitati."
    righe: list[tuple[str, ...]] = [COLONNE_DASHBOARD]
    metrica_presente = "automazione_attiva" in chiavi_originali
    for riga in matrice[1:]:
        if not any(cella.strip() for cella in riga):
            continue
        chiave = riga[0].strip()
        if chiave in {"kill_switch", "invio_automatico_attivo"}:
            if metrica_presente:
                continue
            righe.append(("automazione_attiva", "NO", descrizione))
            metrica_presente = True
            continue
        if chiave == "automazione_attiva" and forza_disattivazione:
            righe.append(("automazione_attiva", "NO", descrizione))
            continue
        righe.append(riga)

    if not metrica_presente:
        righe.append(("automazione_attiva", "NO", descrizione))
    return tuple(righe)


def _migra_notifiche(
    matrice: tuple[tuple[str, ...], ...],
) -> tuple[tuple[str, ...], ...]:
    if not matrice:
        return (COLONNE_NOTIFICHE,)
    intestazioni = matrice[0]
    if intestazioni == COLONNE_NOTIFICHE:
        return matrice
    if intestazioni != COLONNE_NOTIFICHE_LEGACY:
        raise ErroreMigrazioneAmministrativa("NOTIFICHE: intestazioni non riconosciute")

    indice = {nome: posizione for posizione, nome in enumerate(intestazioni)}
    righe: list[tuple[str, ...]] = [COLONNE_NOTIFICHE]
    chiavi: set[str] = set()
    for numero, riga in enumerate(matrice[1:], start=2):
        if not any(cella.strip() for cella in riga):
            continue
        if len(riga) != len(intestazioni):
            raise ErroreMigrazioneAmministrativa(
                f"NOTIFICHE: riga {numero} con larghezza non valida"
            )
        tipo = _tipo_stabile(riga[indice["tipo"]])
        id_arbitro = riga[indice["id_arbitro"]].strip()
        scadenza = riga[indice["scadenza_certificato"]].strip()
        notification_id = "|".join((id_arbitro, scadenza, tipo))
        if notification_id in chiavi:
            raise ErroreMigrazioneAmministrativa(
                "NOTIFICHE: la migrazione produrrebbe chiavi duplicate"
            )
        chiavi.add(notification_id)
        mappa = {
            "notification_id": notification_id,
            "id_arbitro": id_arbitro,
            "scadenza_certificato": scadenza,
            "tipo": tipo,
            "stato": riga[indice["stato"]],
            "tentativi": riga[indice["tentativi"]],
            "creato_il": riga[indice["creato_il"]],
            "aggiornato_il": riga[indice["aggiornato_il"]],
            "message_id": riga[indice["message_id"]],
            "versione_app": riga[indice["versione_app"]],
            "errore": riga[indice["errore"]],
        }
        righe.append(tuple(mappa[colonna] for colonna in COLONNE_NOTIFICHE))
    return tuple(righe)


def _tipo_stabile(tipo: str) -> str:
    normalizzato = tipo.strip()
    if re.fullmatch(r"REMINDER_\d+", normalizzato):
        return TIPO_NOTIFICA_SCADENZA
    if re.fullmatch(r"TEST_REMINDER_\d+", normalizzato):
        return f"TEST_{TIPO_NOTIFICA_SCADENZA}"
    return normalizzato


def _normalizza(
    matrice: Sequence[Sequence[Any]],
) -> tuple[tuple[str, ...], ...]:
    righe = [
        tuple("" if cella is None else str(cella).strip() for cella in riga)
        for riga in matrice
    ]
    while righe and all(not cella for cella in righe[-1]):
        righe.pop()
    return tuple(righe)


@dataclass(frozen=True, slots=True)
class TrasportoMigrazioneGoogleApi:
    servizio: Any

    def leggi_valori(
        self, *, spreadsheet_id: str, intervallo_a1: str
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
            raise ErroreMigrazioneAmministrativa("risposta Google non valida")
        valori = risposta.get("values", [])
        if not isinstance(valori, Sequence) or isinstance(valori, (str, bytes)):
            raise ErroreMigrazioneAmministrativa("values Google non valido")
        return valori

    def sostituisci_tab(
        self,
        *,
        spreadsheet_id: str,
        nome_tab: str,
        valori: Sequence[Sequence[Any]],
    ) -> None:
        escaped = nome_tab.replace("'", "''")
        self.servizio.spreadsheets().values().clear(
            spreadsheetId=spreadsheet_id,
            range=f"'{escaped}'!A:ZZ",
            body={},
        ).execute()
        self.servizio.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=f"'{escaped}'!A1",
            valueInputOption="RAW",
            body={
                "majorDimension": "ROWS",
                "values": [list(riga) for riga in valori],
            },
        ).execute()
