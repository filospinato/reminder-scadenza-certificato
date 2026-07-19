from types import SimpleNamespace

import pytest

from reminder_certificati import registry_probe_cli
from reminder_certificati.registry import StatoNotifica


def test_comando_richiede_flag_e_variabile() -> None:
    with pytest.raises(registry_probe_cli.ErroreCliCollaudo, match="confirm"):
        registry_probe_cli.run(conferma=False, ambiente={})

    with pytest.raises(registry_probe_cli.ErroreCliCollaudo, match="ALLOW_SYNTHETIC"):
        registry_probe_cli.run(conferma=True, ambiente={})


def test_comando_non_legge_operativo_e_stampa_solo_esito_aggregato(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    risorse = SimpleNamespace(admin_spreadsheet_id="admin-sintetico")
    monkeypatch.setattr(
        registry_probe_cli.ConfigurazioneRisorseGoogle,
        "da_ambiente",
        lambda ambiente: risorse,
    )
    monkeypatch.setattr(registry_probe_cli, "costruisci_servizio_sheets", lambda: object())
    monkeypatch.setattr(
        registry_probe_cli,
        "ArchivioNotificheGoogleSheets",
        lambda **kwargs: object(),
    )
    monkeypatch.setattr(
        registry_probe_cli,
        "TrasportoNotificheGoogleApi",
        lambda servizio: object(),
    )
    monkeypatch.setattr(
        registry_probe_cli,
        "esegui_collaudo_registro_sintetico",
        lambda archivio, versione_app: SimpleNamespace(
            append_verificato=True,
            rilettura_verificata=True,
            update_verificato=True,
            una_sola_chiave_verificata=True,
            stato_finale=StatoNotifica.SENT,
        ),
    )

    risultato = registry_probe_cli.run(
        conferma=True,
        ambiente={"ALLOW_SYNTHETIC_REGISTRY_WRITE": "true"},
    )

    output = capsys.readouterr().out
    assert risultato == 0
    assert '"operativo_rows_read": 0' in output
    assert '"synthetic_rows_written": 1' in output
    assert "admin-sintetico" not in output
    assert "notification_id" not in output
