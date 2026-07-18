from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from reminder_certificati.admin_schema import crea_schema_amministrativo
from reminder_certificati.google_preflight import (
    CodiceErrorePreflight,
    ErrorePreflightGoogle,
    PreflightGoogle,
)
from reminder_certificati.google_runtime import ConfigurazioneRisorseGoogle


@dataclass
class TrasportoFake:
    tab: dict[str, tuple[str, ...]]
    intestazioni: dict[tuple[str, str, int], tuple[str, ...]]
    letture: list[tuple[str, str, int]] = field(default_factory=list)
    errore_tab: Exception | None = None
    errore_lettura: Exception | None = None

    def elenca_tab(self, *, spreadsheet_id: str):
        if self.errore_tab:
            raise self.errore_tab
        return self.tab[spreadsheet_id]

    def leggi_intestazioni(self, *, spreadsheet_id: str, nome_tab: str, riga: int):
        self.letture.append((spreadsheet_id, nome_tab, riga))
        if self.errore_lettura:
            raise self.errore_lettura
        return self.intestazioni[(spreadsheet_id, nome_tab, riga)]


def _scenario():
    schema = crea_schema_amministrativo()
    headers_operativo = (
        "Tessera", "Cognome", "Nome", "Qualifica", "Stato Rinnovo",
        "Data Scadenza Certificato", "e-Mail", "Certificato medico",
        "Rinnovato senza lista", "Lista effettiva di appartenenza",
        "Esordiente", "Note", "Fa attività quest'anno",
    )
    intestazioni = {
        ("operativo-id", "Operativo", 2): headers_operativo,
        **{
            ("admin-id", definizione.nome, 1): definizione.intestazioni
            for definizione in schema.tab
        },
    }
    trasporto = TrasportoFake(
        tab={"admin-id": tuple(tab.nome for tab in schema.tab)},
        intestazioni=intestazioni,
    )
    risorse = ConfigurazioneRisorseGoogle(
        operativo_spreadsheet_id="operativo-id",
        admin_spreadsheet_id="admin-id",
    )
    return trasporto, risorse


def _diagnostica(exc_info: pytest.ExceptionInfo[ErrorePreflightGoogle]):
    return exc_info.value.diagnostica


def test_preflight_legge_soltanto_le_righe_di_intestazione():
    trasporto, risorse = _scenario()

    esito = PreflightGoogle(trasporto).esegui(risorse=risorse)

    assert esito.operativo_headers_ok is True
    assert esito.admin_tabs_ok is True
    assert esito.admin_headers_ok is True
    assert esito.operativo_data_rows_read == 0
    assert esito.writes_performed == 0
    assert esito.admin_write_verified is False
    assert ("operativo-id", "Operativo", 2) in trasporto.letture
    assert all(riga in {1, 2} for _, _, riga in trasporto.letture)


def test_preflight_rifiuta_lo_stesso_file_con_codice_stabile():
    trasporto, _ = _scenario()
    risorse = ConfigurazioneRisorseGoogle(
        operativo_spreadsheet_id="stesso-id",
        admin_spreadsheet_id="stesso-id",
    )

    with pytest.raises(ErrorePreflightGoogle) as exc_info:
        PreflightGoogle(trasporto).esegui(risorse=risorse)

    assert _diagnostica(exc_info).codice is CodiceErrorePreflight.RISORSE_COINCIDENTI
    assert trasporto.letture == []


def test_preflight_rifiuta_tab_amministrative_fuori_ordine_con_codice_stabile():
    trasporto, risorse = _scenario()
    trasporto.tab["admin-id"] = ("NOTIFICHE", "CONFIG", "DASHBOARD", "ANOMALIE")

    with pytest.raises(ErrorePreflightGoogle) as exc_info:
        PreflightGoogle(trasporto).esegui(risorse=risorse)

    assert _diagnostica(exc_info).codice is CodiceErrorePreflight.ADMIN_TAB_NON_CONFORMI


def test_preflight_rifiuta_intestazioni_operativo_incomplete_senza_elencarle():
    trasporto, risorse = _scenario()
    trasporto.intestazioni[("operativo-id", "Operativo", 2)] = ("Tessera", "Nome")

    with pytest.raises(ErrorePreflightGoogle) as exc_info:
        PreflightGoogle(trasporto).esegui(risorse=risorse)

    diagnostica = _diagnostica(exc_info)
    assert diagnostica.codice is CodiceErrorePreflight.OPERATIVO_INTESTAZIONI_MANCANTI
    assert "Cognome" not in diagnostica.messaggio


def test_preflight_traduce_errore_google_admin_senza_esporre_payload():
    trasporto, risorse = _scenario()
    trasporto.errore_tab = RuntimeError("spreadsheet-id-segreto token@example.test")

    with pytest.raises(ErrorePreflightGoogle) as exc_info:
        PreflightGoogle(trasporto).esegui(risorse=risorse)

    diagnostica = _diagnostica(exc_info)
    assert diagnostica.codice is CodiceErrorePreflight.ADMIN_NON_RAGGIUNGIBILE
    assert "spreadsheet-id-segreto" not in str(exc_info.value)
    assert "token@example.test" not in str(exc_info.value)
