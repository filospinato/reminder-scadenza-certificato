"""Creazione e verifica non distruttiva dello Spreadsheet amministrativo.

Il modulo non costruisce credenziali. Riceve un trasporto già autenticato oppure
un fake in memoria. Non legge mai ``Operativo`` e non inserisce dati personali.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Protocol

from .admin_schema import (
    NOME_SPREADSHEET_AMMINISTRATIVO,
    SchemaFoglioAmministrativo,
    crea_schema_amministrativo,
)


class ErroreInizializzazioneFoglio(RuntimeError):
    """La risorsa è ambigua, incompatibile o non può essere inizializzata."""


class TrasportoStrutturaSheets(Protocol):
    def crea_spreadsheet(
        self,
        *,
        titolo: str,
        nomi_tab: Sequence[str],
    ) -> str: ...

    def elenca_tab(self, *, spreadsheet_id: str) -> Sequence[str]: ...

    def leggi_valori(
        self,
        *,
        spreadsheet_id: str,
        intervallo_a1: str,
    ) -> Sequence[Sequence[Any]]: ...

    def scrivi_valori(
        self,
        *,
        spreadsheet_id: str,
        intervallo_a1: str,
        valori: Sequence[Sequence[Any]],
    ) -> None: ...


@dataclass(frozen=True, slots=True)
class EsitoInizializzazione:
    spreadsheet_id: str
    creato: bool
    tab_inizializzate: tuple[str, ...]
    tab_gia_conformi: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class InizializzatoreFoglioAmministrativo:
    trasporto: TrasportoStrutturaSheets
    schema: SchemaFoglioAmministrativo = field(default_factory=crea_schema_amministrativo)

    def prepara(self, *, spreadsheet_id: str | None = None) -> EsitoInizializzazione:
        """Crea o verifica il foglio senza sovrascrivere contenuti inattesi.

        Una tab vuota viene inizializzata. Una tab già usata viene verificata per
        intestazioni, larghezza e vincoli minimi, senza richiedere che i valori
        runtime coincidano ancora con quelli sintetici iniziali.
        """

        identificativo = (spreadsheet_id or "").strip()
        creato = False
        if not identificativo:
            try:
                identificativo = self.trasporto.crea_spreadsheet(
                    titolo=self.schema.nome_spreadsheet,
                    nomi_tab=tuple(tab.nome for tab in self.schema.tab),
                ).strip()
            except Exception as exc:
                raise ErroreInizializzazioneFoglio(
                    f"creazione Spreadsheet non riuscita: {type(exc).__name__}"
                ) from exc
            if not identificativo:
                raise ErroreInizializzazioneFoglio(
                    "la creazione non ha restituito uno spreadsheet_id"
                )
            creato = True

        self._verifica_tab(identificativo)
        inizializzate: list[str] = []
        conformi: list[str] = []

        for definizione in self.schema.tab:
            intervallo = _intervallo_tab(definizione.nome)
            attuale = self._leggi(identificativo, intervallo)
            if _matrice_vuota(attuale):
                canonica = definizione.matrice()
                self._scrivi(identificativo, intervallo, canonica)
                riletta = self._leggi(identificativo, intervallo)
                if _normalizza_matrice(riletta) != _normalizza_matrice(canonica):
                    raise ErroreInizializzazioneFoglio(
                        f"{definizione.nome}: verifica dopo scrittura non riuscita"
                    )
                inizializzate.append(definizione.nome)
                continue

            _verifica_matrice_esistente(
                definizione.nome,
                definizione.intestazioni,
                attuale,
            )
            conformi.append(definizione.nome)

        return EsitoInizializzazione(
            spreadsheet_id=identificativo,
            creato=creato,
            tab_inizializzate=tuple(inizializzate),
            tab_gia_conformi=tuple(conformi),
        )

    def verifica(self, *, spreadsheet_id: str) -> None:
        identificativo = spreadsheet_id.strip()
        if not identificativo:
            raise ErroreInizializzazioneFoglio("spreadsheet_id mancante")
        self._verifica_tab(identificativo)
        for definizione in self.schema.tab:
            attuale = self._leggi(
                identificativo,
                _intervallo_tab(definizione.nome),
            )
            if _matrice_vuota(attuale):
                raise ErroreInizializzazioneFoglio(
                    f"{definizione.nome}: tab non inizializzata"
                )
            _verifica_matrice_esistente(
                definizione.nome,
                definizione.intestazioni,
                attuale,
            )

    def _verifica_tab(self, spreadsheet_id: str) -> None:
        try:
            nomi = tuple(
                str(nome).strip()
                for nome in self.trasporto.elenca_tab(
                    spreadsheet_id=spreadsheet_id
                )
            )
        except Exception as exc:
            raise ErroreInizializzazioneFoglio(
                f"lettura metadati non riuscita: {type(exc).__name__}"
            ) from exc
        attesi = tuple(tab.nome for tab in self.schema.tab)
        if nomi != attesi:
            raise ErroreInizializzazioneFoglio(
                "tab mancanti, duplicate o fuori ordine; attese: "
                + ", ".join(attesi)
            )

    def _leggi(
        self,
        spreadsheet_id: str,
        intervallo_a1: str,
    ) -> Sequence[Sequence[Any]]:
        try:
            return self.trasporto.leggi_valori(
                spreadsheet_id=spreadsheet_id,
                intervallo_a1=intervallo_a1,
            )
        except Exception as exc:
            raise ErroreInizializzazioneFoglio(
                f"lettura valori non riuscita: {type(exc).__name__}"
            ) from exc

    def _scrivi(
        self,
        spreadsheet_id: str,
        intervallo_a1: str,
        valori: Sequence[Sequence[Any]],
    ) -> None:
        try:
            self.trasporto.scrivi_valori(
                spreadsheet_id=spreadsheet_id,
                intervallo_a1=intervallo_a1,
                valori=valori,
            )
        except Exception as exc:
            raise ErroreInizializzazioneFoglio(
                f"scrittura valori non riuscita: {type(exc).__name__}"
            ) from exc


def _verifica_matrice_esistente(
    nome_tab: str,
    intestazioni_attese: Sequence[str],
    matrice: Sequence[Sequence[Any]],
) -> None:
    normalizzata = _normalizza_matrice(matrice)
    if not normalizzata:
        raise ErroreInizializzazioneFoglio(f"{nome_tab}: tab vuota")
    intestazioni = tuple(cella.strip() for cella in normalizzata[0])
    if intestazioni != tuple(intestazioni_attese):
        raise ErroreInizializzazioneFoglio(
            f"{nome_tab}: contenuto esistente incompatibile; intestazioni diverse"
        )
    larghezza = len(intestazioni)
    chiavi: set[str] = set()
    for numero_riga, riga in enumerate(normalizzata[1:], start=2):
        if len(riga) != larghezza:
            raise ErroreInizializzazioneFoglio(
                f"{nome_tab}: riga {numero_riga} con larghezza non valida"
            )
        if nome_tab in {"CONFIG", "DASHBOARD"}:
            chiave = riga[0].strip()
            if not chiave:
                raise ErroreInizializzazioneFoglio(
                    f"{nome_tab}: riga {numero_riga} senza chiave"
                )
            if chiave in chiavi:
                raise ErroreInizializzazioneFoglio(
                    f"{nome_tab}: chiave duplicata: {chiave}"
                )
            chiavi.add(chiave)
    if nome_tab == "CONFIG":
        richieste = {
            "SISTEMA_ATTIVO",
            "INVII_REALI_ABILITATI",
            "MODALITA_TEST",
            "KILL_SWITCH",
            "GIORNI_PREAVVISO",
            "LIMITE_INVII_PER_ESECUZIONE",
            "DESTINATARIO_OVERRIDE",
            "OGGETTO_EMAIL",
            "SALUTO_EMAIL",
            "CORPO_EMAIL",
            "FIRMA_TESTO",
            "CONTATTO_SUPPORTO",
        }
        mancanti = richieste - chiavi
        if mancanti:
            raise ErroreInizializzazioneFoglio(
                "CONFIG: chiavi obbligatorie mancanti: " + ", ".join(sorted(mancanti))
            )
    if nome_tab == "DASHBOARD":
        mancanti = {"stato_sistema", "heartbeat", "kill_switch"} - chiavi
        if mancanti:
            raise ErroreInizializzazioneFoglio(
                "DASHBOARD: metriche obbligatorie mancanti: "
                + ", ".join(sorted(mancanti))
            )


def _intervallo_tab(nome: str) -> str:
    escaped = nome.replace("'", "''")
    return f"'{escaped}'!A1:ZZ"


def _normalizza_matrice(
    matrice: Sequence[Sequence[Any]],
) -> tuple[tuple[str, ...], ...]:
    righe = [
        tuple("" if cella is None else str(cella) for cella in riga)
        for riga in matrice
    ]
    while righe and all(not cella.strip() for cella in righe[-1]):
        righe.pop()
    if not righe:
        return ()
    larghezza = max(len(riga) for riga in righe)
    normalizzate = [riga + ("",) * (larghezza - len(riga)) for riga in righe]
    while larghezza > 0 and all(
        not riga[larghezza - 1].strip() for riga in normalizzate
    ):
        larghezza -= 1
    return tuple(riga[:larghezza] for riga in normalizzate)


def _matrice_vuota(matrice: Sequence[Sequence[Any]]) -> bool:
    return not _normalizza_matrice(matrice)


@dataclass(slots=True)
class TrasportoStrutturaMemoria:
    """Fake idempotente per test e collaudi senza rete."""

    spreadsheet: dict[str, dict[str, list[list[Any]]]] = field(default_factory=dict)
    titoli: dict[str, str] = field(default_factory=dict)
    ordine_tab: dict[str, list[str]] = field(default_factory=dict)
    prossimo_id: int = 1

    def crea_spreadsheet(
        self,
        *,
        titolo: str,
        nomi_tab: Sequence[str],
    ) -> str:
        if titolo != NOME_SPREADSHEET_AMMINISTRATIVO:
            raise ValueError("titolo non canonico")
        nomi = [str(nome).strip() for nome in nomi_tab]
        if len(set(nomi)) != len(nomi) or any(not nome for nome in nomi):
            raise ValueError("nomi tab non validi")
        identificativo = f"synthetic-{self.prossimo_id}"
        self.prossimo_id += 1
        self.titoli[identificativo] = titolo
        self.ordine_tab[identificativo] = list(nomi)
        self.spreadsheet[identificativo] = {nome: [] for nome in nomi}
        return identificativo

    def elenca_tab(self, *, spreadsheet_id: str) -> Sequence[str]:
        return tuple(self.ordine_tab[spreadsheet_id])

    def leggi_valori(
        self,
        *,
        spreadsheet_id: str,
        intervallo_a1: str,
    ) -> Sequence[Sequence[Any]]:
        nome = _nome_tab_da_intervallo(intervallo_a1)
        return [list(riga) for riga in self.spreadsheet[spreadsheet_id][nome]]

    def scrivi_valori(
        self,
        *,
        spreadsheet_id: str,
        intervallo_a1: str,
        valori: Sequence[Sequence[Any]],
    ) -> None:
        nome = _nome_tab_da_intervallo(intervallo_a1)
        if self.spreadsheet[spreadsheet_id][nome]:
            raise ValueError("scrittura distruttiva non consentita dal fake")
        self.spreadsheet[spreadsheet_id][nome] = [list(riga) for riga in valori]


def _nome_tab_da_intervallo(intervallo_a1: str) -> str:
    if not intervallo_a1.startswith("'") or "'!" not in intervallo_a1:
        raise ValueError("intervallo A1 non valido")
    return intervallo_a1[1:].split("'!", maxsplit=1)[0].replace("''", "'")


@dataclass(frozen=True, slots=True)
class TrasportoStrutturaGoogleApi:
    """Ponte verso un servizio Google Sheets già autenticato tramite WIF/ADC."""

    servizio: Any

    def crea_spreadsheet(
        self,
        *,
        titolo: str,
        nomi_tab: Sequence[str],
    ) -> str:
        corpo = {
            "properties": {"title": titolo},
            "sheets": [
                {"properties": {"title": nome, "index": indice}}
                for indice, nome in enumerate(nomi_tab)
            ],
        }
        risposta = self.servizio.spreadsheets().create(
            body=corpo,
            fields="spreadsheetId",
        ).execute()
        if not isinstance(risposta, Mapping):
            raise ErroreInizializzazioneFoglio("risposta create non valida")
        return str(risposta.get("spreadsheetId", ""))

    def elenca_tab(self, *, spreadsheet_id: str) -> Sequence[str]:
        risposta = self.servizio.spreadsheets().get(
            spreadsheetId=spreadsheet_id,
            fields="sheets(properties(title,index))",
        ).execute()
        if not isinstance(risposta, Mapping):
            raise ErroreInizializzazioneFoglio("risposta metadata non valida")
        sheets = risposta.get("sheets", [])
        if not isinstance(sheets, Sequence) or isinstance(sheets, (str, bytes)):
            raise ErroreInizializzazioneFoglio("campo sheets non valido")
        ordinati: list[tuple[int, str]] = []
        for item in sheets:
            if not isinstance(item, Mapping):
                raise ErroreInizializzazioneFoglio("metadato tab non valido")
            properties = item.get("properties", {})
            if not isinstance(properties, Mapping):
                raise ErroreInizializzazioneFoglio("properties tab non valide")
            ordinati.append(
                (
                    int(properties.get("index", 0)),
                    str(properties.get("title", "")),
                )
            )
        return tuple(nome for _, nome in sorted(ordinati))

    def leggi_valori(
        self,
        *,
        spreadsheet_id: str,
        intervallo_a1: str,
    ) -> Sequence[Sequence[Any]]:
        risposta = self.servizio.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=intervallo_a1,
            majorDimension="ROWS",
        ).execute()
        if not isinstance(risposta, Mapping):
            raise ErroreInizializzazioneFoglio("risposta values non valida")
        valori = risposta.get("values", [])
        if not isinstance(valori, Sequence) or isinstance(valori, (str, bytes)):
            raise ErroreInizializzazioneFoglio("campo values non valido")
        return valori

    def scrivi_valori(
        self,
        *,
        spreadsheet_id: str,
        intervallo_a1: str,
        valori: Sequence[Sequence[Any]],
    ) -> None:
        self.servizio.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=intervallo_a1,
            valueInputOption="RAW",
            body={
                "majorDimension": "ROWS",
                "values": [list(riga) for riga in valori],
            },
        ).execute()
