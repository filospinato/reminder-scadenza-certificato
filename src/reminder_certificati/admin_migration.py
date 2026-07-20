"""Migrazione esplicita e conservativa dello Spreadsheet amministrativo."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from .admin_schema import COLONNE_CONFIG, configurazione_iniziale_sicura
from .admin_store import COLONNE_NOTIFICHE
from .rules import TIPO_NOTIFICA_SCADENZA

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
    config_dopo: tuple[tuple[str, ...], ...]
    notifiche_dopo: tuple[tuple[str, ...], ...]
    modifiche: tuple[str, ...]

    @property
    def necessaria(self) -> bool:
        return bool(self.modifiche)

    def salva_backup(self, path: Path) -> None:
        payload = {
            "config": [list(riga) for riga in self.config_prima],
            "notifiche": [list(riga) for riga in self.notifiche_prima],
        }
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


def prepara_piano(
    config: Sequence[Sequence[Any]],
    notifiche: Sequence[Sequence[Any]],
) -> PianoMigrazione:
    config_prima = _normalizza(config)
    notifiche_prima = _normalizza(notifiche)
    config_dopo = _migra_config(config_prima)
    notifiche_dopo = _migra_notifiche(notifiche_prima)
    modifiche: list[str] = []
    if config_dopo != config_prima:
        modifiche.append("CONFIG_SCHEMA_V2")
    if notifiche_dopo != notifiche_prima:
        modifiche.append("NOTIFICHE_MINIMIZZATE")
    return PianoMigrazione(
        config_prima=config_prima,
        notifiche_prima=notifiche_prima,
        config_dopo=config_dopo,
        notifiche_dopo=notifiche_dopo,
        modifiche=tuple(modifiche),
    )


def applica_piano(
    piano: PianoMigrazione,
    *,
    trasporto: TrasportoMigrazione,
    spreadsheet_id: str,
) -> None:
    if not piano.necessaria:
        return
    trasporto.sostituisci_tab(
        spreadsheet_id=spreadsheet_id,
        nome_tab="CONFIG",
        valori=piano.config_dopo,
    )
    trasporto.sostituisci_tab(
        spreadsheet_id=spreadsheet_id,
        nome_tab="NOTIFICHE",
        valori=piano.notifiche_dopo,
    )


def _migra_config(
    matrice: tuple[tuple[str, ...], ...],
) -> tuple[tuple[str, ...], ...]:
    if not matrice or matrice[0] != COLONNE_CONFIG:
        raise ErroreMigrazioneAmministrativa("CONFIG: intestazioni non riconosciute")
    per_chiave: dict[str, tuple[str, ...]] = {}
    for riga in matrice[1:]:
        if not any(cella.strip() for cella in riga):
            continue
        if len(riga) != len(COLONNE_CONFIG):
            raise ErroreMigrazioneAmministrativa("CONFIG: riga con larghezza non valida")
        chiave = riga[0].strip()
        if not chiave or chiave in per_chiave:
            raise ErroreMigrazioneAmministrativa("CONFIG: chiave vuota o duplicata")
        per_chiave[chiave] = riga

    valori = {chiave: riga[1] for chiave, riga in per_chiave.items()}
    canoniche = configurazione_iniziale_sicura()
    righe: list[tuple[str, ...]] = [COLONNE_CONFIG]
    for voce in canoniche:
        valore = voce.valore
        if voce.chiave in valori:
            valore = valori[voce.chiave]
        elif voce.chiave == "AUTOMAZIONE_ATTIVA":
            valore = "false"
        elif voce.chiave == "INVII_REALI_ABILITATI":
            valore = "false"
        elif voce.chiave in {
            "GIORNI_PREAVVISO",
            "LIMITE_INVII_PER_ESECUZIONE",
            "DESTINATARIO_OVERRIDE",
            "OGGETTO_EMAIL",
            "CORPO_EMAIL",
            "FIRMA_TESTO",
        }:
            valore = valori.get(voce.chiave, voce.valore)
        righe.append(
            (
                voce.chiave,
                valore,
                voce.tipo.value,
                voce.descrizione,
                "true" if voce.modificabile else "false",
            )
        )

    # Ogni migrazione lascia intenzionalmente il sistema spento.
    righe = [
        tuple("false" if riga[0] in {"AUTOMAZIONE_ATTIVA", "INVII_REALI_ABILITATI"} and indice == 1 else cella for indice, cella in enumerate(riga))
        if riga and riga[0] in {"AUTOMAZIONE_ATTIVA", "INVII_REALI_ABILITATI"}
        else riga
        for riga in righe
    ]
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
        risposta = self.servizio.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=intervallo_a1,
            majorDimension="ROWS",
        ).execute()
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
            body={"majorDimension": "ROWS", "values": [list(riga) for riga in valori]},
        ).execute()
