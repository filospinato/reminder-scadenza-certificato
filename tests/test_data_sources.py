from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest

from reminder_certificati.data_sources import (
    AdapterGoogleSheets,
    ErroreSorgenteDati,
    LettoreGoogleApi,
    SorgenteMemoria,
    leggi_e_valida,
    tabella_da_matrice,
)


@dataclass
class LettoreFake:
    matrice: list[list[Any]]
    chiamate: list[tuple[str, str]] = field(default_factory=list)

    def leggi_valori(
        self,
        *,
        spreadsheet_id: str,
        intervallo_a1: str,
    ) -> list[list[Any]]:
        self.chiamate.append((spreadsheet_id, intervallo_a1))
        return self.matrice


def matrice_valida() -> list[list[Any]]:
    return [
        [
            "id_arbitro",
            "nome",
            "cognome",
            "email",
            "scadenza_certificato",
            "attivo",
        ],
        ["A-1", "Mario", "Rossi", "mario@example.it", "2026-08-01", "Operativo"],
    ]


def test_tabella_completa_righe_corte_senza_perdere_le_colonne() -> None:
    tabella = tabella_da_matrice(
        [["ID", "Nome", "Email"], ["A-1", "Mario"]],
        nome_sorgente="test",
    )
    assert tabella.intestazioni == ("ID", "Nome", "Email")
    assert tabella.righe == ({"ID": "A-1", "Nome": "Mario", "Email": ""},)
    assert tabella.prima_riga_dati == 2


def test_tabella_conserva_il_numero_della_prima_riga_dati() -> None:
    tabella = tabella_da_matrice(
        [["ID"], ["A-1"]],
        nome_sorgente="test",
        prima_riga_dati=3,
    )
    assert tabella.prima_riga_dati == 3


@pytest.mark.parametrize("prima_riga_dati", [0, 1])
def test_tabella_rifiuta_numero_riga_dati_non_valido(prima_riga_dati: int) -> None:
    with pytest.raises(ErroreSorgenteDati, match="prima_riga_dati"):
        tabella_da_matrice(
            [["ID"]],
            nome_sorgente="test",
            prima_riga_dati=prima_riga_dati,
        )


def test_rifiuta_intestazioni_vuote_o_duplicate() -> None:
    with pytest.raises(ErroreSorgenteDati, match="intestazione vuota"):
        tabella_da_matrice([["ID", ""]], nome_sorgente="test")
    with pytest.raises(ErroreSorgenteDati, match="intestazioni duplicate: ID"):
        tabella_da_matrice([["ID", "ID"]], nome_sorgente="test")


def test_rifiuta_valori_non_rappresentati_dalle_intestazioni() -> None:
    with pytest.raises(ErroreSorgenteDati, match="riga 2"):
        tabella_da_matrice([["ID"], ["A-1", "dato-extra"]], nome_sorgente="test")


def test_rifiuta_righe_che_non_sono_sequenze_di_celle() -> None:
    with pytest.raises(ErroreSorgenteDati, match="riga 2"):
        tabella_da_matrice([["ID"], "A-1"], nome_sorgente="test")  # type: ignore[list-item]


def test_adapter_costruisce_intervallo_a1_e_protegge_apostrofi() -> None:
    lettore = LettoreFake(matrice_valida())
    adapter = AdapterGoogleSheets(
        lettore=lettore,
        spreadsheet_id=" spreadsheet-test ",
        nome_scheda="Arbitri d'Italia",
        colonne_a1="A:F",
    )
    tabella = adapter.leggi()
    assert lettore.chiamate == [("spreadsheet-test", "'Arbitri d''Italia'!A1:F")]
    assert tabella.nome_sorgente == "Google Sheets:Arbitri d'Italia"
    assert tabella.prima_riga_dati == 2
    assert tabella.righe[0]["id_arbitro"] == "A-1"


def test_adapter_legge_intestazioni_dalla_riga_due_di_operativo() -> None:
    lettore = LettoreFake(matrice_valida())
    adapter = AdapterGoogleSheets(
        lettore=lettore,
        spreadsheet_id="sheet",
        nome_scheda="Operativo",
        colonne_a1="A:F",
        riga_intestazioni=2,
    )
    tabella = adapter.leggi()
    assert lettore.chiamate == [("sheet", "'Operativo'!A2:F")]
    assert tabella.prima_riga_dati == 3


@pytest.mark.parametrize(
    ("spreadsheet_id", "nome_scheda", "colonne", "riga_intestazioni", "messaggio"),
    [
        ("", "Operativo", "A:ZZ", 1, "spreadsheet_id"),
        ("sheet", "", "A:ZZ", 1, "nome_scheda"),
        ("sheet", "Operativo", "", 1, "intervallo colonne"),
        ("sheet", "Operativo", "A:ZZ", 0, "riga_intestazioni"),
        ("sheet", "Operativo", "A2:ZZ", 1, "forma A:ZZ"),
    ],
)
def test_adapter_rifiuta_configurazione_incompleta(
    spreadsheet_id: str,
    nome_scheda: str,
    colonne: str,
    riga_intestazioni: int,
    messaggio: str,
) -> None:
    adapter = AdapterGoogleSheets(
        lettore=LettoreFake(matrice_valida()),
        spreadsheet_id=spreadsheet_id,
        nome_scheda=nome_scheda,
        colonne_a1=colonne,
        riga_intestazioni=riga_intestazioni,
    )
    with pytest.raises(ErroreSorgenteDati, match=messaggio):
        adapter.leggi()


def test_sorgente_memoria_si_collega_alla_validazione_esistente() -> None:
    esito = leggi_e_valida(SorgenteMemoria(matrice_valida()))
    assert [arbitro.id_arbitro for arbitro in esito.arbitri] == ["A-1"]
    assert esito.arbitri[0].nome_per_saluto == "Mario"
    assert esito.arbitri[0].nome_completo == "Mario Rossi"
    assert esito.anomalie == ()


def test_anomalia_usa_il_numero_di_riga_originale_del_foglio() -> None:
    adapter = AdapterGoogleSheets(
        lettore=LettoreFake(
            [
                matrice_valida()[0],
                ["A-1", "", "Rossi", "mario@example.it", "2026-08-01", "Operativo"],
            ]
        ),
        spreadsheet_id="sheet",
        nome_scheda="Operativo",
        colonne_a1="A:F",
        riga_intestazioni=2,
    )
    esito = leggi_e_valida(adapter)
    assert len(esito.anomalie) == 1
    assert esito.anomalie[0].numero_riga == 3


class RichiestaFake:
    def __init__(self, risposta: Any = None, errore: Exception | None = None) -> None:
        self.risposta = risposta
        self.errore = errore

    def execute(self) -> Any:
        if self.errore:
            raise self.errore
        return self.risposta


class ServizioGoogleFake:
    def __init__(self, richiesta: RichiestaFake) -> None:
        self.richiesta = richiesta
        self.parametri: dict[str, Any] | None = None

    def spreadsheets(self) -> ServizioGoogleFake:
        return self

    def values(self) -> ServizioGoogleFake:
        return self

    def get(self, **kwargs: Any) -> RichiestaFake:
        self.parametri = kwargs
        return self.richiesta


def test_lettore_google_api_usa_sola_lettura_per_righe() -> None:
    servizio = ServizioGoogleFake(RichiestaFake({"values": matrice_valida()}))
    valori = LettoreGoogleApi(servizio).leggi_valori(
        spreadsheet_id="sheet",
        intervallo_a1="'Operativo'!A2:F",
    )
    assert valori == matrice_valida()
    assert servizio.parametri == {
        "spreadsheetId": "sheet",
        "range": "'Operativo'!A2:F",
        "majorDimension": "ROWS",
    }


def test_lettore_google_api_converte_errori_e_risposte_non_valide() -> None:
    servizio_errore = ServizioGoogleFake(
        RichiestaFake(errore=PermissionError("negato"))
    )
    with pytest.raises(ErroreSorgenteDati, match="PermissionError"):
        LettoreGoogleApi(servizio_errore).leggi_valori(
            spreadsheet_id="sheet",
            intervallo_a1="'Operativo'!A2:F",
        )

    servizio_risposta = ServizioGoogleFake(RichiestaFake({"values": "non-matrice"}))
    with pytest.raises(ErroreSorgenteDati, match="campo values non valido"):
        LettoreGoogleApi(servizio_risposta).leggi_valori(
            spreadsheet_id="sheet",
            intervallo_a1="'Operativo'!A2:F",
        )
