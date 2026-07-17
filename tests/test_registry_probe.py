from datetime import datetime, timezone

from reminder_certificati.admin_store import COLONNE_NOTIFICHE
from reminder_certificati.notifications_sheets import (
    ArchivioNotificheGoogleSheets,
    TrasportoNotificheMemoria,
)
from reminder_certificati.registry import StatoNotifica
from reminder_certificati.registry_probe import esegui_collaudo_registro_sintetico


def test_collaudo_sintetico_usa_una_sola_riga_e_conclude_sent() -> None:
    matrice: list[list[str]] = [list(COLONNE_NOTIFICHE)]
    archivio = ArchivioNotificheGoogleSheets(
        trasporto=TrasportoNotificheMemoria(matrice),
        spreadsheet_id="spreadsheet-sintetico",
    )

    esito = esegui_collaudo_registro_sintetico(
        archivio,
        versione_app="test",
        ora=lambda: datetime(2026, 7, 18, 0, 0, tzinfo=timezone.utc),
        genera_id=lambda: "ABC123",
    )

    assert esito.append_verificato is True
    assert esito.rilettura_verificata is True
    assert esito.update_verificato is True
    assert esito.una_sola_chiave_verificata is True
    assert esito.stato_finale is StatoNotifica.SENT
    assert len(matrice) == 2
    assert matrice[1][0] == "SYNTHETIC-REGISTRY-ABC123|2099-12-31|SYNTHETIC_REGISTRY_CHECK"
    assert matrice[1][4] == "synthetic@example.invalid"
    assert matrice[1][7] == "SENT"


def test_collaudo_rifiuta_identificativo_non_sintetico_valido() -> None:
    matrice: list[list[str]] = [list(COLONNE_NOTIFICHE)]
    archivio = ArchivioNotificheGoogleSheets(
        trasporto=TrasportoNotificheMemoria(matrice),
        spreadsheet_id="spreadsheet-sintetico",
    )

    try:
        esegui_collaudo_registro_sintetico(
            archivio,
            versione_app="test",
            genera_id=lambda: "../non-valido",
        )
    except ValueError as exc:
        assert "identificativo sintetico" in str(exc)
    else:
        raise AssertionError("identificativo non valido accettato")

    assert len(matrice) == 1
