from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from reminder_certificati.admin_schema import crea_schema_amministrativo
from reminder_certificati.google_preflight import ErrorePreflightGoogle, PreflightGoogle
from reminder_certificati.google_runtime import ConfigurazioneRisorseGoogle


@dataclass
class TrasportoFake:
    tab: dict[str, tuple[str, ...]]
    intestazioni: dict[tuple[str, str, int], tuple[str, ...]]
    letture: list[tuple[str, str, int]] = field(default_factory=list)

    def elenca_tab(self, *, spreadsheet_id: str):
        return self.tab[spreadsheet_id]

    def leggi_intestazioni(self, *, spreadsheet_id: str, nome_tab: str, riga: int):
        self.letture.append((spreadsheet_id, nome_tab, riga))
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


def test_preflight_rifiuta_lo_stesso_file_per_operativo_e_admin():
    trasporto, risorse = _scenario()
    risorse = ConfigurazioneRisorseGoogle(
        operativo_spreadsheet_id="stesso-id",
        admin_spreadsheet_id="stesso-id",
    )

    with pytest.raises(ErrorePreflightGoogle, match="file distinti"):
        PreflightGoogle(trasporto).esegui(risorse=risorse)

    assert trasporto.letture == []


def test_preflight_rifiuta_tab_amministrative_fuori_ordine():
    trasporto, risorse = _scenario()
    trasporto.tab["admin-id"] = ("NOTIFICHE", "CONFIG", "DASHBOARD", "ANOMALIE")

    with pytest.raises(ErrorePreflightGoogle, match="fuori ordine"):
        PreflightGoogle(trasporto).esegui(risorse=risorse)


def test_preflight_rifiuta_intestazioni_operativo_incomplete():
    trasporto, risorse = _scenario()
    trasporto.intestazioni[("operativo-id", "Operativo", 2)] = ("Tessera", "Nome")

    with pytest.raises(ErrorePreflightGoogle, match="obbligatorie mancanti"):
        PreflightGoogle(trasporto).esegui(risorse=risorse)
