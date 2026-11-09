from __future__ import annotations

import re
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

from reminder_certificati.google_runtime import (
    ConfigurazioneRisorseGoogle,
    costruisci_componenti_google,
)


@dataclass
class LettoreFake:
    matrice: list[list[Any]]
    chiamate: list[tuple[str, str]] = field(default_factory=list)
    chiamate_batch: list[tuple[str, tuple[str, ...]]] = field(default_factory=list)

    def leggi_valori(
        self,
        *,
        spreadsheet_id: str,
        intervallo_a1: str,
    ) -> list[list[Any]]:
        self.chiamate.append((spreadsheet_id, intervallo_a1))
        return [list(self.matrice[0])]

    def leggi_intervalli(
        self,
        *,
        spreadsheet_id: str,
        intervalli_a1: tuple[str, ...],
    ) -> list[list[list[Any]]]:
        self.chiamate_batch.append((spreadsheet_id, intervalli_a1))
        risultato: list[list[list[Any]]] = []
        for intervallo in intervalli_a1:
            match = re.search(r"!([A-Z]+)\d+:\1$", intervallo)
            assert match is not None
            indice = _indice_colonna(match.group(1))
            risultato.append(
                [
                    [riga[indice] if indice < len(riga) else ""]
                    for riga in self.matrice[1:]
                ]
            )
        return risultato


def _indice_colonna(colonna: str) -> int:
    valore = 0
    for carattere in colonna:
        valore = valore * 26 + ord(carattere) - ord("A") + 1
    return valore - 1


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


def test_adapter_legge_intestazioni_e_solo_le_colonne_necessarie() -> None:
    lettore = LettoreFake(matrice_valida())
    adapter = AdapterGoogleSheets(
        lettore=lettore,
        spreadsheet_id=" spreadsheet-test ",
        nome_scheda="Arbitri d'Italia",
        colonne_a1="A:F",
    )
    tabella = adapter.leggi()
    assert lettore.chiamate == [
        ("spreadsheet-test", "'Arbitri d''Italia'!A1:F1")
    ]
    assert lettore.chiamate_batch == [
        (
            "spreadsheet-test",
            (
                "'Arbitri d''Italia'!A2:A",
                "'Arbitri d''Italia'!B2:B",
                "'Arbitri d''Italia'!C2:C",
                "'Arbitri d''Italia'!D2:D",
                "'Arbitri d''Italia'!E2:E",
                "'Arbitri d''Italia'!F2:F",
            ),
        )
    ]
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
    assert lettore.chiamate == [("sheet", "'Operativo'!A2:F2")]
    assert lettore.chiamate_batch[0][1][0] == "'Operativo'!A3:A"
    assert tabella.prima_riga_dati == 3


@pytest.mark.parametrize(
    ("spreadsheet_id", "nome_scheda", "colonne", "riga_intestazioni", "messaggio"),
    [
        ("", "Operativo", "A:ZZ", 1, "spreadsheet_id"),
        ("sheet", "", "A:ZZ", 1, "nome_scheda"),
        ("sheet", "Operativo", "", 1, "forma A:ZZ"),
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


def test_record_conserva_il_numero_di_riga_originale_del_foglio() -> None:
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
    assert esito.anomalie == ()
    assert esito.arbitri[0].numero_riga_sorgente == 3


class RichiestaFake:
    def __init__(self, risposta: Any = None, errore: Exception | None = None) -> None:
        self.risposta = risposta
        self.errore = errore
        self.num_retries: list[int] = []

    def execute(self, *, num_retries: int = 0) -> Any:
        self.num_retries.append(num_retries)
        if self.errore:
            raise self.errore
        return self.risposta


class ServizioGoogleFake:
    def __init__(self, richiesta: RichiestaFake) -> None:
        self.richiesta = richiesta
        self.parametri: dict[str, Any] | None = None

    def spreadsheets(self):
        return self

    def values(self):
        return self

    def get(self, **kwargs: Any) -> RichiestaFake:
        self.parametri = kwargs
        return self.richiesta

    def batchGet(self, **kwargs: Any) -> RichiestaFake:
        self.parametri = kwargs
        return self.richiesta


def test_lettore_google_api_usa_sola_lettura_per_righe() -> None:
    servizio = ServizioGoogleFake(RichiestaFake({"values": matrice_valida()}))
    valori = LettoreGoogleApi(servizio).leggi_valori(
        spreadsheet_id="sheet",
        intervallo_a1="'Operativo'!A2:F2",
    )
    assert valori == matrice_valida()
    assert servizio.parametri == {
        "spreadsheetId": "sheet",
        "range": "'Operativo'!A2:F2",
        "majorDimension": "ROWS",
    }
    assert servizio.richiesta.num_retries == [5]


def test_lettore_google_api_ritenta_anche_la_lettura_batch() -> None:
    richiesta = RichiestaFake(
        {
            "valueRanges": [
                {"values": [["A-1"]]},
                {"values": [["Mario"]]},
            ]
        }
    )
    servizio = ServizioGoogleFake(richiesta)

    valori = LettoreGoogleApi(servizio).leggi_intervalli(
        spreadsheet_id="sheet",
        intervalli_a1=("'Operativo'!A3:A", "'Operativo'!B3:B"),
    )

    assert valori == [[["A-1"]], [["Mario"]]]
    assert servizio.parametri == {
        "spreadsheetId": "sheet",
        "ranges": ["'Operativo'!A3:A", "'Operativo'!B3:B"],
        "majorDimension": "ROWS",
    }
    assert richiesta.num_retries == [5]


def test_lettore_google_api_converte_errori_e_risposte_non_valide() -> None:
    servizio_errore = ServizioGoogleFake(
        RichiestaFake(errore=PermissionError("negato"))
    )
    with pytest.raises(ErroreSorgenteDati, match="PermissionError"):
        LettoreGoogleApi(servizio_errore).leggi_valori(
            spreadsheet_id="sheet",
            intervallo_a1="'Operativo'!A2:F2",
        )

    servizio_risposta = ServizioGoogleFake(RichiestaFake({"values": "non-matrice"}))
    with pytest.raises(ErroreSorgenteDati, match="campo values non valido"):
        LettoreGoogleApi(servizio_risposta).leggi_valori(
            spreadsheet_id="sheet",
            intervallo_a1="'Operativo'!A2:F2",
        )


def test_runtime_legge_attivita_corrente_oltre_as_senza_leggere_colonne_extra() -> None:
    intestazioni = [""] * 50
    valori = [""] * 50
    campi = {
        0: ("Tessera", "T-1"),
        1: ("Cognome", "Rossi"),
        2: ("Nome", "Mario"),
        4: ("Qualifica", "ordinario"),
        5: ("Abilitazione", ""),
        7: ("Data Scadenza Certificato", "2026-11-20"),
        18: ("e-Mail", "mario@example.invalid"),
        43: ("Fa attività quest'anno 2025/2026", "si"),
        47: ("Fa attività quest'anno", "no"),
    }
    for indice, (nome, valore) in campi.items():
        intestazioni[indice] = nome
        valori[indice] = valore

    class ServizioSorgenteFake:
        def __init__(self) -> None:
            self.ranges: list[str] = []
            self.batch_ranges: list[str] = []

        def spreadsheets(self):
            return self

        def values(self):
            return self

        def get(self, **kwargs: Any) -> RichiestaFake:
            intervallo = kwargs["range"]
            self.ranges.append(intervallo)
            match = re.fullmatch(r"'Operativo'!A2:([A-Z]+)2", intervallo)
            assert match is not None
            fine = _indice_colonna(match.group(1)) + 1
            return RichiestaFake({"values": [intestazioni[:fine]]})

        def batchGet(self, **kwargs: Any) -> RichiestaFake:
            self.batch_ranges = kwargs["ranges"]
            colonne = []
            for intervallo in self.batch_ranges:
                match = re.fullmatch(r"'Operativo'!([A-Z]+)3:\1", intervallo)
                assert match is not None
                indice = _indice_colonna(match.group(1))
                colonne.append({"values": [[valori[indice]]]})
            return RichiestaFake({"valueRanges": colonne})

    servizio = ServizioSorgenteFake()
    risorse = ConfigurazioneRisorseGoogle("source-id", "admin-id")
    componenti = costruisci_componenti_google(servizio=servizio, risorse=risorse)
    tabella = componenti.sorgente_operativo.leggi()

    assert len(servizio.ranges) == 1
    assert len(servizio.batch_ranges) == 8
    assert "'Operativo'!AV3:AV" in servizio.batch_ranges
    assert "'Operativo'!AR3:AR" not in servizio.batch_ranges
    assert tabella.righe[0]["Tessera"] == "T-1"
    assert tabella.righe[0]["Fa attività quest'anno"] == "no"
    assert tabella.righe[0]["e-Mail"] == "mario@example.invalid"
    assert len(tabella.righe[0]) == 8
