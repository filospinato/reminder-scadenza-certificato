"""Lettura rigorosa della tab CONFIG e barriere di attivazione.

La configurazione del foglio non è sufficiente da sola ad abilitare invii reali:
serve anche un consenso esterno esplicito fornito dal workflow.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from .admin_schema import COLONNE_CONFIG, configurazione_iniziale_sicura
from .email_templates import ConfigurazioneEmail
from .validation import email_valida


class ErroreConfigurazioneRuntime(ValueError):
    """CONFIG è incompleta, duplicata, incoerente o non sicura."""


@dataclass(frozen=True, slots=True)
class ConfigurazioneRuntime:
    sistema_attivo: bool
    invii_reali_abilitati: bool
    modalita_test: bool
    kill_switch: bool
    giorni_preavviso: int
    limite_invii_per_esecuzione: int
    destinatario_override: str | None
    email: ConfigurazioneEmail
    contatto_supporto: str | None

    @property
    def elaborazione_consentita(self) -> bool:
        return self.sistema_attivo and not self.kill_switch

    def invio_reale_consentito(self, *, consenso_esterno: bool) -> bool:
        """Richiede simultaneamente foglio, modalità e consenso del workflow."""

        return (
            consenso_esterno
            and self.elaborazione_consentita
            and self.invii_reali_abilitati
            and not self.modalita_test
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

    righe: dict[str, Mapping[str, str]] = {}
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

    _verifica_metadati(righe)
    sistema_attivo = _booleano(righe["SISTEMA_ATTIVO"]["valore"], "SISTEMA_ATTIVO")
    invii_reali = _booleano(
        righe["INVII_REALI_ABILITATI"]["valore"],
        "INVII_REALI_ABILITATI",
    )
    modalita_test = _booleano(righe["MODALITA_TEST"]["valore"], "MODALITA_TEST")
    kill_switch = _booleano(righe["KILL_SWITCH"]["valore"], "KILL_SWITCH")
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
    supporto = _email_opzionale(
        righe["CONTATTO_SUPPORTO"]["valore"],
        "CONTATTO_SUPPORTO",
    )
    if modalita_test and sistema_attivo and override is None:
        raise ErroreConfigurazioneRuntime(
            "CONFIG: DESTINATARIO_OVERRIDE obbligatorio quando il sistema è "
            "attivo in MODALITA_TEST"
        )

    saluto = righe["SALUTO_EMAIL"]["valore"]
    if saluto != "Ciao {{nome}},":
        raise ErroreConfigurazioneRuntime(
            "CONFIG: SALUTO_EMAIL deve restare 'Ciao {{nome}},'"
        )

    oggetto = righe["OGGETTO_EMAIL"]["valore"]
    corpo = righe["CORPO_EMAIL"]["valore"]
    firma = righe["FIRMA_TESTO"]["valore"]
    if not oggetto or "\n" in oggetto or "\r" in oggetto:
        raise ErroreConfigurazioneRuntime(
            "CONFIG: OGGETTO_EMAIL vuoto o contenente ritorni a capo"
        )
    if not corpo.casefold().startswith("ricevi questa mail"):
        raise ErroreConfigurazioneRuntime(
            "CONFIG: CORPO_EMAIL deve iniziare con 'ricevi questa mail'"
        )
    if not firma:
        raise ErroreConfigurazioneRuntime("CONFIG: FIRMA_TESTO non può essere vuota")

    if invii_reali and (modalita_test or kill_switch or not sistema_attivo):
        # È lecito preparare la chiave, ma non dichiarare una configurazione
        # contraddittoria che sembri operativa quando una barriera è attiva.
        raise ErroreConfigurazioneRuntime(
            "CONFIG: INVII_REALI_ABILITATI richiede sistema attivo, modalità test "
            "disattivata e kill switch disattivato"
        )

    return ConfigurazioneRuntime(
        sistema_attivo=sistema_attivo,
        invii_reali_abilitati=invii_reali,
        modalita_test=modalita_test,
        kill_switch=kill_switch,
        giorni_preavviso=giorni,
        limite_invii_per_esecuzione=limite,
        destinatario_override=override,
        email=ConfigurazioneEmail(oggetto=oggetto, corpo=corpo, firma=firma),
        contatto_supporto=supporto,
    )


def _verifica_metadati(righe: Mapping[str, Mapping[str, str]]) -> None:
    canoniche = {voce.chiave: voce for voce in configurazione_iniziale_sicura()}
    for chiave, mappa in righe.items():
        attesa = canoniche[chiave]
        if mappa["tipo"] != attesa.tipo.value:
            raise ErroreConfigurazioneRuntime(
                f"CONFIG: tipo non valido per {chiave}: {mappa['tipo']}"
            )
        modificabile = _booleano(mappa["modificabile"], f"{chiave}.modificabile")
        if modificabile != attesa.modificabile:
            raise ErroreConfigurazioneRuntime(
                f"CONFIG: attributo modificabile alterato per {chiave}"
            )
        if not mappa["descrizione"]:
            raise ErroreConfigurazioneRuntime(
                f"CONFIG: descrizione mancante per {chiave}"
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
