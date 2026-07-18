import pytest

from reminder_certificati.admin_initializer import (
    ErroreInizializzazioneFoglio,
    InizializzatoreFoglioAmministrativo,
    TrasportoStrutturaMemoria,
)
from reminder_certificati.admin_schema import NOMI_TAB_AMMINISTRATIVE


def _file_vuoto(trasporto: TrasportoStrutturaMemoria) -> str:
    return trasporto.crea_spreadsheet_vuoto()


def test_configura_le_quattro_tab_e_scrive_solo_struttura_sintetica() -> None:
    trasporto = TrasportoStrutturaMemoria()
    spreadsheet_id = _file_vuoto(trasporto)
    esito = InizializzatoreFoglioAmministrativo(trasporto).prepara(
        spreadsheet_id=spreadsheet_id
    )

    assert esito.tab_configurate is True
    assert esito.tab_inizializzate == NOMI_TAB_AMMINISTRATIVE
    assert esito.tab_gia_conformi == ()
    assert trasporto.ordine_tab[spreadsheet_id] == list(NOMI_TAB_AMMINISTRATIVE)
    assert len(trasporto.spreadsheet[spreadsheet_id]["NOTIFICHE"]) == 1
    assert len(trasporto.spreadsheet[spreadsheet_id]["ANOMALIE"]) == 1


def test_seconda_esecuzione_e_idempotente() -> None:
    trasporto = TrasportoStrutturaMemoria()
    spreadsheet_id = _file_vuoto(trasporto)
    inizializzatore = InizializzatoreFoglioAmministrativo(trasporto)
    inizializzatore.prepara(spreadsheet_id=spreadsheet_id)
    seconda = inizializzatore.prepara(spreadsheet_id=spreadsheet_id)

    assert seconda.tab_configurate is False
    assert seconda.tab_inizializzate == ()
    assert seconda.tab_gia_conformi == NOMI_TAB_AMMINISTRATIVE
    inizializzatore.verifica(spreadsheet_id=spreadsheet_id)


def test_verifica_legge_solo_la_riga_delle_intestazioni() -> None:
    trasporto = TrasportoStrutturaMemoria()
    spreadsheet_id = _file_vuoto(trasporto)
    inizializzatore = InizializzatoreFoglioAmministrativo(trasporto)
    inizializzatore.prepara(spreadsheet_id=spreadsheet_id)
    trasporto.letture.clear()

    inizializzatore.verifica(spreadsheet_id=spreadsheet_id)

    assert len(trasporto.letture) == 4
    assert all(intervallo.endswith("A1:ZZ1") for intervallo in trasporto.letture)


def test_accetta_config_e_dashboard_aggiornate_legittimamente() -> None:
    trasporto = TrasportoStrutturaMemoria()
    spreadsheet_id = _file_vuoto(trasporto)
    inizializzatore = InizializzatoreFoglioAmministrativo(trasporto)
    inizializzatore.prepara(spreadsheet_id=spreadsheet_id)
    config = trasporto.spreadsheet[spreadsheet_id]["CONFIG"]
    for riga in config[1:]:
        if riga[0] == "GIORNI_PREAVVISO":
            riga[1] = "45"
    dashboard = trasporto.spreadsheet[spreadsheet_id]["DASHBOARD"]
    dashboard.append(["versione_app", "0.12.0", "Versione corrente"])

    inizializzatore.verifica(spreadsheet_id=spreadsheet_id)


def test_rifiuta_contenuto_esistente_incompatibile_senza_sovrascrivere() -> None:
    trasporto = TrasportoStrutturaMemoria()
    spreadsheet_id = _file_vuoto(trasporto)
    inizializzatore = InizializzatoreFoglioAmministrativo(trasporto)
    inizializzatore.prepara(spreadsheet_id=spreadsheet_id)
    trasporto.spreadsheet[spreadsheet_id]["CONFIG"][0][0] = "alterato"

    with pytest.raises(ErroreInizializzazioneFoglio, match="incompatibile"):
        inizializzatore.prepara(spreadsheet_id=spreadsheet_id)

    assert trasporto.spreadsheet[spreadsheet_id]["CONFIG"][0][0] == "alterato"


def test_accetta_tab_riordinate_dopo_l_inizializzazione() -> None:
    trasporto = TrasportoStrutturaMemoria()
    spreadsheet_id = _file_vuoto(trasporto)
    inizializzatore = InizializzatoreFoglioAmministrativo(trasporto)
    inizializzatore.prepara(spreadsheet_id=spreadsheet_id)
    trasporto.ordine_tab[spreadsheet_id] = list(reversed(NOMI_TAB_AMMINISTRATIVE))

    inizializzatore.verifica(spreadsheet_id=spreadsheet_id)
    seconda = inizializzatore.prepara(spreadsheet_id=spreadsheet_id)

    assert seconda.tab_configurate is False


def test_rifiuta_file_con_singola_tab_non_vuota() -> None:
    trasporto = TrasportoStrutturaMemoria()
    spreadsheet_id = _file_vuoto(trasporto)
    trasporto.spreadsheet[spreadsheet_id]["Foglio1"] = [["dato esistente"]]

    with pytest.raises(ErroreInizializzazioneFoglio, match="contiene già dati"):
        InizializzatoreFoglioAmministrativo(trasporto).prepara(
            spreadsheet_id=spreadsheet_id
        )

    assert trasporto.ordine_tab[spreadsheet_id] == ["Foglio1"]


def test_richiede_un_file_creato_da_una_identita_umana() -> None:
    with pytest.raises(ErroreInizializzazioneFoglio, match="account umano"):
        InizializzatoreFoglioAmministrativo(
            TrasportoStrutturaMemoria()
        ).prepara(spreadsheet_id="")
