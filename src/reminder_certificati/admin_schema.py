"""Contratto sicuro dello Spreadsheet amministrativo separato."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from .admin_store import COLONNE_NOTIFICHE
from .email_templates import ConfigurazioneEmail

NOME_SPREADSHEET_AMMINISTRATIVO = "Reminder certificati CIA Lazio — Gestione"
VERSIONE_SCHEMA_AMMINISTRATIVO = 4
NOMI_TAB_AMMINISTRATIVE: tuple[str, ...] = (
    "CONFIG",
    "NOTIFICHE",
    "DASHBOARD",
    "ANOMALIE",
)

COLONNE_CONFIG: tuple[str, ...] = (
    "chiave",
    "valore",
    "descrizione",
)
COLONNE_DASHBOARD: tuple[str, ...] = (
    "metrica",
    "valore",
    "descrizione",
)
COLONNE_ANOMALIE: tuple[str, ...] = (
    "anomalia_id",
    "rilevata_il",
    "severita",
    "origine",
    "codice",
    "riga_sorgente",
    "campo",
    "messaggio",
    "versione_app",
    "risolta_il",
)


class ErroreSchemaAmministrativo(ValueError):
    """Lo schema amministrativo è incompleto, ambiguo o non sicuro."""


class TipoValoreConfig(StrEnum):
    BOOLEANO = "BOOLEANO"
    INTERO = "INTERO"
    TESTO = "TESTO"
    EMAIL_OPZIONALE = "EMAIL_OPZIONALE"
    TEMPLATE = "TEMPLATE"


@dataclass(frozen=True, slots=True)
class VoceConfig:
    chiave: str
    valore: str
    tipo: TipoValoreConfig
    descrizione: str
    modificabile: bool

    def come_riga(self) -> tuple[str, ...]:
        return self.chiave, self.valore, self.descrizione


@dataclass(frozen=True, slots=True)
class DefinizioneTab:
    nome: str
    intestazioni: tuple[str, ...]
    righe_iniziali: tuple[tuple[str, ...], ...] = ()

    def __post_init__(self) -> None:
        if not self.nome.strip():
            raise ErroreSchemaAmministrativo("il nome della tab non può essere vuoto")
        if not self.intestazioni:
            raise ErroreSchemaAmministrativo(
                f"la tab {self.nome} deve avere almeno un'intestazione"
            )
        if any(not colonna.strip() for colonna in self.intestazioni):
            raise ErroreSchemaAmministrativo(
                f"la tab {self.nome} contiene intestazioni vuote"
            )
        if len(set(self.intestazioni)) != len(self.intestazioni):
            raise ErroreSchemaAmministrativo(
                f"la tab {self.nome} contiene intestazioni duplicate"
            )
        for indice, riga in enumerate(self.righe_iniziali, start=2):
            if len(riga) != len(self.intestazioni):
                raise ErroreSchemaAmministrativo(
                    f"la riga {indice} della tab {self.nome} ha {len(riga)} celle; "
                    f"ne servono {len(self.intestazioni)}"
                )

    def matrice(self) -> tuple[tuple[str, ...], ...]:
        return (self.intestazioni, *self.righe_iniziali)


@dataclass(frozen=True, slots=True)
class SchemaFoglioAmministrativo:
    nome_spreadsheet: str
    tab: tuple[DefinizioneTab, ...]

    def __post_init__(self) -> None:
        if self.nome_spreadsheet != NOME_SPREADSHEET_AMMINISTRATIVO:
            raise ErroreSchemaAmministrativo(
                "nome dello Spreadsheet amministrativo non canonico"
            )
        nomi = tuple(definizione.nome for definizione in self.tab)
        if len(nomi) != len(NOMI_TAB_AMMINISTRATIVE) or set(nomi) != set(
            NOMI_TAB_AMMINISTRATIVE
        ):
            raise ErroreSchemaAmministrativo(
                "le quattro tab amministrative devono essere presenti una sola volta"
            )

    def ottieni_tab(self, nome: str) -> DefinizioneTab:
        for definizione in self.tab:
            if definizione.nome == nome:
                return definizione
        raise KeyError(nome)

    def matrici(self) -> dict[str, tuple[tuple[str, ...], ...]]:
        return {definizione.nome: definizione.matrice() for definizione in self.tab}


def configurazione_iniziale_sicura() -> tuple[VoceConfig, ...]:
    email = ConfigurazioneEmail()
    voci = (
        VoceConfig(
            "SCHEMA_VERSION",
            str(VERSIONE_SCHEMA_AMMINISTRATIVO),
            TipoValoreConfig.INTERO,
            "Versione tecnica del foglio; è gestita dal programma e non va modificata.",
            False,
        ),
        VoceConfig(
            "INVIO_AUTOMATICO_ATTIVO",
            "false",
            TipoValoreConfig.BOOLEANO,
            "Unico interruttore: true consente gli invii programmati, false li arresta.",
            True,
        ),
        VoceConfig(
            "GIORNI_PREAVVISO",
            "30",
            TipoValoreConfig.INTERO,
            "Finestra inclusiva dei certificati in scadenza.",
            True,
        ),
        VoceConfig(
            "DESTINATARIO_OVERRIDE",
            "",
            TipoValoreConfig.EMAIL_OPZIONALE,
            "Indirizzo sostitutivo usato soltanto per una prova SMTP.",
            True,
        ),
        VoceConfig(
            "OGGETTO_EMAIL",
            email.oggetto,
            TipoValoreConfig.TEMPLATE,
            "Oggetto del promemoria.",
            True,
        ),
        VoceConfig(
            "CORPO_EMAIL",
            email.corpo,
            TipoValoreConfig.TEMPLATE,
            "Messaggio completo; può usare placeholder come {{nome}} e {{data_scadenza}}.",
            True,
        ),
    )
    _valida_configurazione_sicura(voci)
    return voci


def crea_schema_amministrativo() -> SchemaFoglioAmministrativo:
    config = tuple(voce.come_riga() for voce in configurazione_iniziale_sicura())
    dashboard = (
        ("stato_sistema", "Spento", "Stato operativo complessivo."),
        ("ultima_esecuzione", "", "Timestamp UTC dell'ultima esecuzione conclusa."),
        ("heartbeat", "", "Timestamp UTC dell'ultimo segnale di vita."),
        ("righe_lette", "0", "Righe lette dalla sorgente nell'ultima esecuzione."),
        ("candidati", "0", "Promemoria candidati nell'ultima esecuzione."),
        ("invii_tentati", "0", "Invii tentati nell'ultima esecuzione."),
        ("invii_riusciti", "0", "Invii confermati nell'ultima esecuzione."),
        ("anomalie", "0", "Anomalie rilevate nell'ultima esecuzione."),
        (
            "automazione_attiva",
            "NO",
            "Indica se gli invii programmati sono abilitati.",
        ),
    )
    return SchemaFoglioAmministrativo(
        nome_spreadsheet=NOME_SPREADSHEET_AMMINISTRATIVO,
        tab=(
            DefinizioneTab("CONFIG", COLONNE_CONFIG, config),
            DefinizioneTab("NOTIFICHE", COLONNE_NOTIFICHE),
            DefinizioneTab("DASHBOARD", COLONNE_DASHBOARD, dashboard),
            DefinizioneTab("ANOMALIE", COLONNE_ANOMALIE),
        ),
    )


def _valida_configurazione_sicura(voci: tuple[VoceConfig, ...]) -> None:
    per_chiave = {voce.chiave: voce for voce in voci}
    if len(per_chiave) != len(voci):
        raise ErroreSchemaAmministrativo("CONFIG contiene chiavi duplicate")

    valori_attesi = {
        "SCHEMA_VERSION": str(VERSIONE_SCHEMA_AMMINISTRATIVO),
        "INVIO_AUTOMATICO_ATTIVO": "false",
    }
    for chiave, valore in valori_attesi.items():
        voce = per_chiave.get(chiave)
        if voce is None or voce.valore != valore:
            raise ErroreSchemaAmministrativo(
                f"CONFIG deve inizializzare {chiave} a {valore}"
            )

    if per_chiave["DESTINATARIO_OVERRIDE"].valore:
        raise ErroreSchemaAmministrativo(
            "DESTINATARIO_OVERRIDE deve essere vuoto nello schema iniziale"
        )
    for chiave in ("OGGETTO_EMAIL", "CORPO_EMAIL"):
        if not per_chiave[chiave].valore.strip():
            raise ErroreSchemaAmministrativo(f"{chiave} non può essere vuoto")
