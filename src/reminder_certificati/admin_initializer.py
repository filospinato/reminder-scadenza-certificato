"""Inizializzazione non distruttiva dello Spreadsheet amministrativo.

Il file deve essere creato da un'identità umana e condiviso con il service
account. Il service account non crea né possiede file e non legge Operativo.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Protocol

from .admin_schema import (
    SchemaFoglioAmministrativo,
    configurazione_iniziale_sicura,
    crea_schema_amministrativo,
)


class ErroreInizializzazioneFoglio(RuntimeError):
    """La risorsa è ambigua, incompatibile o non può essere inizializzata."""


class TrasportoStrutturaSheets(Protocol):
    def elenca_tab(self, *, spreadsheet_id: str) -> Sequence[str]: ...

    def configura_tab_canoniche(
        self,
        *,
        spreadsheet_id: str,
        nomi_tab: Sequence[str],
    ) -> None: ...

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
    tab_configurate: bool
    tab_inizializzate: tuple[str, ...]
    tab_gia_conformi: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class InizializzatoreFoglioAmministrativo:
    trasporto: TrasportoStrutturaSheets
    schema: SchemaFoglioAmministrativo = field(
        default_factory=crea_schema_amministrativo
    )

    def prepara(self, *, spreadsheet_id: str) -> EsitoInizializzazione:
        """Inizializza tab vuote e verifica senza sovrascrivere tab usate."""

        identificativo = spreadsheet_id.strip()
        if not identificativo:
            raise ErroreInizializzazioneFoglio(
                "spreadsheet_id mancante: crea prima un file vuoto con un account "
                "umano e condividilo con il service account"
            )

        tab_configurate = self._prepara_tab(identificativo)
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
            tab_configurate=tab_configurate,
            tab_inizializzate=tuple(inizializzate),
            tab_gia_conformi=tuple(conformi),
        )

    def verifica(self, *, spreadsheet_id: str) -> None:
        """Verifica presenza e sole intestazioni, senza leggere intere tab."""

        identificativo = spreadsheet_id.strip()
        if not identificativo:
            raise ErroreInizializzazioneFoglio("spreadsheet_id mancante")
        self._verifica_tab_presenti(identificativo)
        for definizione in self.schema.tab:
            attuale = self._leggi(
                identificativo,
                _intervallo_intestazioni(definizione.nome),
            )
            if _prima_riga(attuale) != definizione.intestazioni:
                raise ErroreInizializzazioneFoglio(
                    f"{definizione.nome}: intestazioni diverse dallo schema canonico"
                )

    def _prepara_tab(self, spreadsheet_id: str) -> bool:
        nomi = self._elenca_tab(spreadsheet_id)
        attesi = tuple(tab.nome for tab in self.schema.tab)
        if _stesse_tab(nomi, attesi):
            return False
        if len(nomi) != 1:
            raise ErroreInizializzazioneFoglio(
                "tab amministrative mancanti o non conformi; il bootstrap automatico "
                "è consentito soltanto su un file con una singola tab vuota"
            )
        tab_originale = nomi[0]
        if not _matrice_vuota(
            self._leggi(spreadsheet_id, _intervallo_tab(tab_originale))
        ):
            raise ErroreInizializzazioneFoglio(
                "la singola tab iniziale contiene già dati; nessuna modifica eseguita"
            )
        try:
            self.trasporto.configura_tab_canoniche(
                spreadsheet_id=spreadsheet_id,
                nomi_tab=attesi,
            )
        except Exception as exc:
            raise ErroreInizializzazioneFoglio(
                f"configurazione tab non riuscita: {type(exc).__name__}"
            ) from exc
        self._verifica_tab_presenti(spreadsheet_id)
        return True

    def _verifica_tab_presenti(self, spreadsheet_id: str) -> None:
        attesi = tuple(tab.nome for tab in self.schema.tab)
        if not _stesse_tab(self._elenca_tab(spreadsheet_id), attesi):
            raise ErroreInizializzazioneFoglio(
                "tab amministrative mancanti o duplicate; attese: "
                + ", ".join(attesi)
            )

    def _elenca_tab(self, spreadsheet_id: str) -> tuple[str, ...]:
        try:
            return tuple(
                str(nome).strip()
                for nome in self.trasporto.elenca_tab(
                    spreadsheet_id=spreadsheet_id
                )
            )
        except Exception as exc:
            raise ErroreInizializzazioneFoglio(
                f"lettura metadati non riuscita: {type(exc).__name__}"
            ) from exc

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


def _stesse_tab(attuali: Sequence[str], attese: Sequence[str]) -> bool:
    return len(attuali) == len(attese) and set(attuali) == set(attese)


def _prima_riga(matrice: Sequence[Sequence[Any]]) -> tuple[str, ...]:
    if not matrice:
        return ()
    valori = tuple(
        "" if cella is None else str(cella).strip() for cella in matrice[0]
    )
    fine = len(valori)
    while fine and not valori[fine - 1]:
        fine -= 1
    return valori[:fine]


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
        richieste = {voce.chiave for voce in configurazione_iniziale_sicura()}
        mancanti = richieste - chiavi
        if mancanti:
            raise ErroreInizializzazioneFoglio(
                "CONFIG: chiavi obbligatorie mancanti: "
                + ", ".join(sorted(mancanti))
            )
    if nome_tab == "DASHBOARD":
        mancanti = {
            "stato_sistema",
            "heartbeat",
            "automazione_attiva",
        } - chiavi
        if mancanti:
            raise ErroreInizializzazioneFoglio(
                "DASHBOARD: metriche obbligatorie mancanti: "
                + ", ".join(sorted(mancanti))
            )


def _intervallo_tab(nome: str) -> str:
    escaped = nome.replace("'", "''")
    return f"'{escaped}'!A1:ZZ"


def _intervallo_intestazioni(nome: str) -> str:
    escaped = nome.replace("'", "''")
    return f"'{escaped}'!A1:ZZ1"


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

    spreadsheet: dict[str, dict[str, list[list[Any]]]] = field(
        default_factory=dict
    )
    titoli: dict[str, str] = field(default_factory=dict)
    ordine_tab: dict[str, list[str]] = field(default_factory=dict)
    prossimo_id: int = 1
    letture: list[str] = field(default_factory=list)

    def crea_spreadsheet_vuoto(
        self,
        *,
        titolo: str = "Reminder certificati CIA Lazio — Gestione",
        nome_tab: str = "Foglio1",
    ) -> str:
        identificativo = f"synthetic-{self.prossimo_id}"
        self.prossimo_id += 1
        self.titoli[identificativo] = titolo
        self.ordine_tab[identificativo] = [nome_tab]
        self.spreadsheet[identificativo] = {nome_tab: []}
        return identificativo

    def elenca_tab(self, *, spreadsheet_id: str) -> Sequence[str]:
        return tuple(self.ordine_tab[spreadsheet_id])

    def configura_tab_canoniche(
        self,
        *,
        spreadsheet_id: str,
        nomi_tab: Sequence[str],
    ) -> None:
        nomi = [str(nome).strip() for nome in nomi_tab]
        if len(set(nomi)) != len(nomi) or any(not nome for nome in nomi):
            raise ValueError("nomi tab non validi")
        esistenti = self.ordine_tab[spreadsheet_id]
        if len(esistenti) != 1:
            raise ValueError("il file non contiene una sola tab")
        originale = esistenti[0]
        if self.spreadsheet[spreadsheet_id][originale]:
            raise ValueError("la tab originale non è vuota")
        self.ordine_tab[spreadsheet_id] = list(nomi)
        self.spreadsheet[spreadsheet_id] = {nome: [] for nome in nomi}

    def leggi_valori(
        self,
        *,
        spreadsheet_id: str,
        intervallo_a1: str,
    ) -> Sequence[Sequence[Any]]:
        self.letture.append(intervallo_a1)
        nome = _nome_tab_da_intervallo(intervallo_a1)
        righe = [list(riga) for riga in self.spreadsheet[spreadsheet_id][nome]]
        if intervallo_a1.endswith("1:ZZ1"):
            return righe[:1]
        return righe

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

    def elenca_tab(self, *, spreadsheet_id: str) -> Sequence[str]:
        return tuple(nome for _, _, nome in self._metadati_tab(spreadsheet_id))

    def configura_tab_canoniche(
        self,
        *,
        spreadsheet_id: str,
        nomi_tab: Sequence[str],
    ) -> None:
        metadati = self._metadati_tab(spreadsheet_id)
        if len(metadati) != 1:
            raise ErroreInizializzazioneFoglio(
                "il bootstrap richiede una singola tab vuota"
            )
        sheet_id, _, _ = metadati[0]
        nomi = tuple(str(nome).strip() for nome in nomi_tab)
        if not nomi or any(not nome for nome in nomi) or len(set(nomi)) != len(nomi):
            raise ErroreInizializzazioneFoglio("nomi tab non validi")
        richieste: list[dict[str, Any]] = [
            {
                "updateSheetProperties": {
                    "properties": {
                        "sheetId": sheet_id,
                        "title": nomi[0],
                        "index": 0,
                    },
                    "fields": "title,index",
                }
            }
        ]
        richieste.extend(
            {
                "addSheet": {
                    "properties": {"title": nome, "index": indice}
                }
            }
            for indice, nome in enumerate(nomi[1:], start=1)
        )
        self.servizio.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={"requests": richieste},
        ).execute()

    def _metadati_tab(
        self,
        spreadsheet_id: str,
    ) -> tuple[tuple[int, int, str], ...]:
        risposta = self.servizio.spreadsheets().get(
            spreadsheetId=spreadsheet_id,
            fields="sheets(properties(sheetId,title,index))",
        ).execute()
        if not isinstance(risposta, Mapping):
            raise ErroreInizializzazioneFoglio("risposta metadata non valida")
        sheets = risposta.get("sheets", [])
        if not isinstance(sheets, Sequence) or isinstance(sheets, (str, bytes)):
            raise ErroreInizializzazioneFoglio("campo sheets non valido")
        ordinati: list[tuple[int, int, str]] = []
        for item in sheets:
            if not isinstance(item, Mapping):
                raise ErroreInizializzazioneFoglio("metadato tab non valido")
            properties = item.get("properties", {})
            if not isinstance(properties, Mapping):
                raise ErroreInizializzazioneFoglio("properties tab non valide")
            ordinati.append(
                (
                    int(properties.get("sheetId", -1)),
                    int(properties.get("index", 0)),
                    str(properties.get("title", "")),
                )
            )
        return tuple(sorted(ordinati, key=lambda item: item[1]))

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
