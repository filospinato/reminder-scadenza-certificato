import pytest

from reminder_certificati.admin_initializer import (
    ErroreInizializzazioneFoglio,
    InizializzatoreFoglioAmministrativo,
    TrasportoStrutturaMemoria,
)
from reminder_certificati.admin_schema import NOMI_TAB_AMMINISTRATIVE


def test_crea_le_quattro_tab_e_scrive_solo_struttura_sintetica() -> None:
    trasporto = TrasportoStrutturaMemoria()
    esito = InizializzatoreFoglioAmministrativo(trasporto).prepara()

    assert esito.creato is True
    assert esito.tab_inizializzate == NOMI_TAB_AMMINISTRATIVE
    assert esito.tab_gia_conformi == ()
    assert trasporto.ordine_tab[esito.spreadsheet_id] == list(NOMI_TAB_AMMINISTRATIVE)
    assert len(trasporto.spreadsheet[esito.spreadsheet_id]["NOTIFICHE"]) == 1
    assert len(trasporto.spreadsheet[esito.spreadsheet_id]["ANOMALIE"]) == 1


def test_seconda_esecuzione_e_idempotente() -> None:
    trasporto = TrasportoStrutturaMemoria()
    inizializzatore = InizializzatoreFoglioAmministrativo(trasporto)
    prima = inizializzatore.prepara()
    seconda = inizializzatore.prepara(spreadsheet_id=prima.spreadsheet_id)

    assert seconda.creato is False
    assert seconda.tab_inizializzate == ()
    assert seconda.tab_gia_conformi == NOMI_TAB_AMMINISTRATIVE
    inizializzatore.verifica(spreadsheet_id=prima.spreadsheet_id)


def test_accetta_config_e_dashboard_aggiornate_legittimamente() -> None:
    trasporto = TrasportoStrutturaMemoria()
    inizializzatore = InizializzatoreFoglioAmministrativo(trasporto)
    prima = inizializzatore.prepara()
    config = trasporto.spreadsheet[prima.spreadsheet_id]["CONFIG"]
    for riga in config[1:]:
        if riga[0] == "GIORNI_PREAVVISO":
            riga[1] = "45"
    dashboard = trasporto.spreadsheet[prima.spreadsheet_id]["DASHBOARD"]
    dashboard.append(["versione_app", "0.11.0", "Versione corrente"])

    inizializzatore.verifica(spreadsheet_id=prima.spreadsheet_id)


def test_rifiuta_contenuto_esistente_incompatibile_senza_sovrascrivere() -> None:
    trasporto = TrasportoStrutturaMemoria()
    inizializzatore = InizializzatoreFoglioAmministrativo(trasporto)
    prima = inizializzatore.prepara()
    trasporto.spreadsheet[prima.spreadsheet_id]["CONFIG"][0][0] = "alterato"

    with pytest.raises(ErroreInizializzazioneFoglio, match="incompatibile"):
        inizializzatore.prepara(spreadsheet_id=prima.spreadsheet_id)

    assert trasporto.spreadsheet[prima.spreadsheet_id]["CONFIG"][0][0] == "alterato"


def test_rifiuta_tab_fuori_ordine() -> None:
    trasporto = TrasportoStrutturaMemoria()
    inizializzatore = InizializzatoreFoglioAmministrativo(trasporto)
    prima = inizializzatore.prepara()
    trasporto.ordine_tab[prima.spreadsheet_id] = list(reversed(NOMI_TAB_AMMINISTRATIVE))

    with pytest.raises(ErroreInizializzazioneFoglio, match="fuori ordine"):
        inizializzatore.verifica(spreadsheet_id=prima.spreadsheet_id)
