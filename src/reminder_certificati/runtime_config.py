"""Lettura rigorosa della tab CONFIG e barriere di attivazione."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

from .admin_schema import (
    COLONNE_CONFIG,
    VERSIONE_SCHEMA_AMMINISTRATIVO,
    configurazione_iniziale_sicura,
)
from .email_templates import ConfigurazioneEmail
from .validation import email_valida


class ErroreConfigurazioneRuntime(ValueError):
    """CONFIG è incompleta, duplicata, incoerente o non sicura."""


@dataclass(frozen=True, slots=True)
class ConfigurazioneRuntime:
    automazione_attiva: bool
    invii_reali_abilitati: bool
    giorni_preavviso: int
    limite_invii_per_esecuzione: int
    destinatario_override: str | None
    email: ConfigurazioneEmail
    schema_version: int = VERSIONE_SCHEMA_AMMINISTRATIVO

    @property
    def elaborazione_consentita(self) -> bool:
        return self.automazione_attiva

    def invio_reale_consentito(self, *, consenso_esterno: bool) -> bool:
        return (
            consenso_esterno
            and self.automazione_attiva
            and self.invii_reali_abilitati
        )


_CHIAVI_CANONICHE = tuple(voce.chiave for voce in configurazione_iniziale_sicura())


def carica_configurazione(
    matrice: Sequence[Sequence[Any]],
) -> ConfigurazioneRuntime:
    if isinstance(matrice, (str, bytes)) or not isinstance(matrice, Sequence):
        raise ErroreConfigurazioneRuntime("CONFIG: matrice non valida")
    if not matrice:
        raise ErroreConfigurazioneRuntime("CONFIG: tab vuota")

    intestazioni = tuple(str(cella).strip() for cella in matrice[0])
    if intestazioni != COLONNE_CONFIG:
        raise ErroreConfigurazioneRuntime(
            "CONFIG: intestazioni diverse dallo schema canonico"
        )

    righe: dict[str, dict[str, str]] = {}
    for numero_riga, valori_originali in enumerate(matrice[1:], start=2):
        valori = list(valori_originali)
        if not any(str(cella).strip() for cella in valori):
            continue
        if len(valori) != len(COLONNE_CONFIG):
            raise ErroreConfigurazioneRuntime(
                f"CONFIG: riga {numero_riga} con numero di celle errato"
            )
        mappa = {
            colonna: "" if valore is None else str(valore).strip()
            for colonna, valore in zip(COLONNE_CONFIG, valori, strict=True)
        }
        chiave = mappa["chiave"]
        if not chiave:
            raise ErroreConfigurazioneRuntime(
                f"CONFIG: riga {numero_riga} senza chiave"
            )
        if chiave in righe:
            raise ErroreConfigurazioneRuntime(f"CONFIG: chiave duplicata: {chiave}")
        righe[chiave] = mappa

    mancanti = [chiave for chiave in _CHIAVI_CANONICHE if chiave not in righe]
    sconosciute = sorted(set(righe) - set(_CHIAVI_CANONICHE))
    if mancanti:
        raise ErroreConfigurazioneRuntime(
            "CONFIG: chiavi mancanti: " + ", ".join(mancanti)
        )
    if sconosciute:
        raise ErroreConfigurazioneRuntime(
            "CONFIG: chiavi sconosciute: " + ", ".join(sconosciute)
        )

    schema_version = _intero_limitato(
        righe["SCHEMA_VERSION"]["valore"],
        campo="SCHEMA_VERSION",
        minimo=1,
        massimo=999,
    )
    if schema_version != VERSIONE_SCHEMA_AMMINISTRATIVO:
        raise ErroreConfigurazioneRuntime(
            "CONFIG: versione schema non supportata; eseguire migrate-admin"
        )

    automazione_attiva = _booleano(
        righe["AUTOMAZIONE_ATTIVA"]["valore"],
        "AUTOMAZIONE_ATTIVA",
    )
    invii_reali = _booleano(
        righe["INVII_REALI_ABILITATI"]["valore"],
        "INVII_REALI_ABILITATI",
    )
    giorni = _intero_limitato(
        righe["GIORNI_PREAVVISO"]["valore"],
        campo="GIORNI_PREAVVISO",
        minimo=0,
        massimo=365,
    )
    limite = _intero_limitato(
        righe["LIMITE_INVII_PER_ESECUZIONE"]["valore"],
        campo="LIMITE_INVII_PER_ESECUZIONE",
        minimo=1,
        massimo=500,
    )

    override = _email_opzionale(
        righe["DESTINATARIO_OVERRIDE"]["valore"],
        "DESTINATARIO_OVERRIDE",
    )

    oggetto = righe["OGGETTO_EMAIL"]["valore"]
    corpo = righe["CORPO_EMAIL"]["valore"]
    firma = righe["FIRMA_TESTO"]["valore"]
    if not oggetto or "\n" in oggetto or "\r" in oggetto:
        raise ErroreConfigurazioneRuntime(
            "CONFIG: OGGETTO_EMAIL vuoto o contenente ritorni a capo"
        )
    if not corpo:
        raise ErroreConfigurazioneRuntime("CONFIG: CORPO_EMAIL non può essere vuoto")
    if not firma:
        raise ErroreConfigurazioneRuntime("CONFIG: FIRMA_TESTO non può essere vuota")

    if invii_reali and not automazione_attiva:
        raise ErroreConfigurazioneRuntime(
            "CONFIG: INVII_REALI_ABILITATI richiede AUTOMAZIONE_ATTIVA=true"
        )

    return ConfigurazioneRuntime(
        automazione_attiva=automazione_attiva,
        invii_reali_abilitati=invii_reali,
        giorni_preavviso=giorni,
        limite_invii_per_esecuzione=limite,
        destinatario_override=override,
        email=ConfigurazioneEmail(oggetto=oggetto, corpo=corpo, firma=firma),
        schema_version=schema_version,
    )


def _booleano(value: str, campo: str) -> bool:
    normalizzato = value.strip().casefold()
    if normalizzato == "true":
        return True
    if normalizzato == "false":
        return False
    raise ErroreConfigurazioneRuntime(f"CONFIG: {campo} deve essere true o false")


def _intero_limitato(value: str, *, campo: str, minimo: int, massimo: int) -> int:
    try:
        risultato = int(value)
    except ValueError as exc:
        raise ErroreConfigurazioneRuntime(f"CONFIG: {campo} deve essere intero") from exc
    if not minimo <= risultato <= massimo:
        raise ErroreConfigurazioneRuntime(
            f"CONFIG: {campo} deve essere compreso tra {minimo} e {massimo}"
        )
    return risultato


def _email_opzionale(value: str, campo: str) -> str | None:
    normalizzato = value.strip()
    if not normalizzato:
        return None
    if not email_valida(normalizzato):
        raise ErroreConfigurazioneRuntime(f"CONFIG: {campo} non è una email valida")
    return normalizzato
