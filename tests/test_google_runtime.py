import pytest

from reminder_certificati.google_runtime import (
    MAPPATURA_OPERATIVO_REALE,
    ConfigurazioneRisorseGoogle,
    ErroreGoogleRuntime,
)


def test_configurazione_google_usa_operativo_riga_due() -> None:
    config = ConfigurazioneRisorseGoogle.da_ambiente(
        {
            "OPERATIVO_SPREADSHEET_ID": "source-id",
            "ADMIN_SPREADSHEET_ID": "admin-id",
        }
    )

    assert config.operativo_sheet_name == "Operativo"
    assert config.operativo_header_row == 2
    assert MAPPATURA_OPERATIVO_REALE.id_arbitro == "Tessera"
    assert MAPPATURA_OPERATIVO_REALE.nome == "Nome"
    assert MAPPATURA_OPERATIVO_REALE.email == "e-Mail"
    assert MAPPATURA_OPERATIVO_REALE.attivo == "Fa attività quest'anno"
    assert MAPPATURA_OPERATIVO_REALE.qualifica == "Qualifica"
    assert MAPPATURA_OPERATIVO_REALE.abilitazione == "Abilitazione"
    assert len(MAPPATURA_OPERATIVO_REALE.obbligatorie) == 8


def test_check_headers_puo_non_richiedere_admin() -> None:
    config = ConfigurazioneRisorseGoogle.da_ambiente(
        {"OPERATIVO_SPREADSHEET_ID": "source-id"},
        richiedi_admin=False,
    )
    assert config.admin_spreadsheet_id == ""


def test_run_richiede_entrambi_gli_id() -> None:
    with pytest.raises(ErroreGoogleRuntime, match="OPERATIVO"):
        ConfigurazioneRisorseGoogle.da_ambiente({})
    with pytest.raises(ErroreGoogleRuntime, match="ADMIN"):
        ConfigurazioneRisorseGoogle.da_ambiente(
            {"OPERATIVO_SPREADSHEET_ID": "source-id"}
        )
