import pytest

from reminder_certificati.admin_schema import (
    COLONNE_ANOMALIE,
    COLONNE_CONFIG,
    COLONNE_DASHBOARD,
    NOMI_TAB_AMMINISTRATIVE,
    NOME_SPREADSHEET_AMMINISTRATIVO,
    VERSIONE_SCHEMA_AMMINISTRATIVO,
    DefinizioneTab,
    ErroreSchemaAmministrativo,
    SchemaFoglioAmministrativo,
    configurazione_iniziale_sicura,
    crea_schema_amministrativo,
)
from reminder_certificati.admin_store import COLONNE_NOTIFICHE


def test_schema_canonico_crea_le_quattro_tab() -> None:
    schema = crea_schema_amministrativo()

    assert schema.nome_spreadsheet == NOME_SPREADSHEET_AMMINISTRATIVO
    assert tuple(tab.nome for tab in schema.tab) == NOMI_TAB_AMMINISTRATIVE
    assert schema.ottieni_tab("CONFIG").intestazioni == COLONNE_CONFIG
    assert schema.ottieni_tab("NOTIFICHE").intestazioni == COLONNE_NOTIFICHE
    assert schema.ottieni_tab("DASHBOARD").intestazioni == COLONNE_DASHBOARD
    assert schema.ottieni_tab("ANOMALIE").intestazioni == COLONNE_ANOMALIE


def test_config_iniziale_ha_un_solo_interruttore() -> None:
    voci = {voce.chiave: voce for voce in configurazione_iniziale_sicura()}

    assert VERSIONE_SCHEMA_AMMINISTRATIVO == 3
    assert voci["INVIO_AUTOMATICO_ATTIVO"].valore == "false"
    assert voci["DESTINATARIO_OVERRIDE"].valore == ""
    assert voci["GIORNI_PREAVVISO"].valore == "30"
    for chiave in (
        "AUTOMAZIONE_ATTIVA",
        "INVII_REALI_ABILITATI",
        "LIMITE_INVII_PER_ESECUZIONE",
        "SISTEMA_ATTIVO",
        "MODALITA_TEST",
        "KILL_SWITCH",
    ):
        assert chiave not in voci


def test_config_visibile_contiene_solo_tre_colonne() -> None:
    assert COLONNE_CONFIG == ("chiave", "valore", "descrizione")
    matrice = crea_schema_amministrativo().ottieni_tab("CONFIG").matrice()
    assert all(len(riga) == 3 for riga in matrice)


def test_config_contiene_destinatario_e_template_modificabili() -> None:
    voci = {voce.chiave: voce for voce in configurazione_iniziale_sicura()}

    for chiave in (
        "DESTINATARIO_OVERRIDE",
        "OGGETTO_EMAIL",
        "CORPO_EMAIL",
        "FIRMA_TESTO",
    ):
        assert chiave in voci
        assert voci[chiave].modificabile is True


def test_notifiche_e_anomalie_non_contengono_righe_iniziali() -> None:
    schema = crea_schema_amministrativo()

    assert schema.ottieni_tab("NOTIFICHE").righe_iniziali == ()
    assert schema.ottieni_tab("ANOMALIE").righe_iniziali == ()


def test_dashboard_parte_spenta_con_conteggi_a_zero() -> None:
    dashboard = crea_schema_amministrativo().ottieni_tab("DASHBOARD")
    valori = {riga[0]: riga[1] for riga in dashboard.righe_iniziali}

    assert valori["stato_sistema"] == "Spento"
    assert valori["automazione_attiva"] == "NO"
    assert valori["righe_lette"] == "0"
    assert valori["invii_tentati"] == "0"
    assert valori["invii_riusciti"] == "0"
    assert valori["anomalie"] == "0"


def test_matrici_includono_intestazioni_come_prima_riga() -> None:
    matrici = crea_schema_amministrativo().matrici()

    assert matrici["CONFIG"][0] == COLONNE_CONFIG
    assert matrici["NOTIFICHE"] == (COLONNE_NOTIFICHE,)
    assert matrici["DASHBOARD"][0] == COLONNE_DASHBOARD
    assert matrici["ANOMALIE"] == (COLONNE_ANOMALIE,)


def test_rifiuta_riga_iniziale_con_numero_di_celle_errato() -> None:
    with pytest.raises(ErroreSchemaAmministrativo, match="ha 1 celle"):
        DefinizioneTab("CONFIG", ("a", "b"), (("solo-una",),))


def test_rifiuta_intestazioni_duplicate() -> None:
    with pytest.raises(ErroreSchemaAmministrativo, match="duplicate"):
        DefinizioneTab("CONFIG", ("chiave", "chiave"))


def test_accetta_le_tab_in_un_ordine_diverso() -> None:
    schema = SchemaFoglioAmministrativo(
        nome_spreadsheet=NOME_SPREADSHEET_AMMINISTRATIVO,
        tab=(
            DefinizioneTab("NOTIFICHE", COLONNE_NOTIFICHE),
            DefinizioneTab("CONFIG", COLONNE_CONFIG),
            DefinizioneTab("DASHBOARD", COLONNE_DASHBOARD),
            DefinizioneTab("ANOMALIE", COLONNE_ANOMALIE),
        ),
    )

    assert schema.ottieni_tab("CONFIG").nome == "CONFIG"


def test_rifiuta_tab_mancanti() -> None:
    with pytest.raises(ErroreSchemaAmministrativo, match="quattro tab"):
        SchemaFoglioAmministrativo(
            nome_spreadsheet=NOME_SPREADSHEET_AMMINISTRATIVO,
            tab=(
                DefinizioneTab("CONFIG", COLONNE_CONFIG),
                DefinizioneTab("DASHBOARD", COLONNE_DASHBOARD),
                DefinizioneTab("ANOMALIE", COLONNE_ANOMALIE),
            ),
        )


def test_rifiuta_nome_spreadsheet_non_canonico() -> None:
    schema = crea_schema_amministrativo()

    with pytest.raises(ErroreSchemaAmministrativo, match="non canonico"):
        SchemaFoglioAmministrativo(
            nome_spreadsheet="Foglio sbagliato",
            tab=schema.tab,
        )
