import sys
from types import SimpleNamespace

import pytest

from reminder_certificati import runtime_cli
from reminder_certificati.orchestrator import ModalitaEsecuzione


def test_init_admin_richiede_spreadsheet_id() -> None:
    parser = runtime_cli.build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["init-admin"])
    args = parser.parse_args(
        ["init-admin", "--spreadsheet-id", "synthetic-sheet"]
    )
    assert args.spreadsheet_id == "synthetic-sheet"


def test_unica_cli_espone_i_sottocomandi_operativi() -> None:
    parser = runtime_cli.build_parser()
    assert parser.parse_args(["preflight"]).comando == "preflight"
    assert parser.parse_args(["registry-check"]).comando == "registry-check"
    assert parser.parse_args(["review-registry"]).comando == "review-registry"
    assert parser.parse_args(["dry-run"]).comando == "dry-run"
    assert parser.parse_args(["test-smtp"]).comando == "test-smtp"
    assert parser.parse_args(["produzione"]).comando == "produzione"
    migrazione = parser.parse_args(
        ["migrate-admin", "--spreadsheet-id", "admin"]
    )
    assert migrazione.comando == "migrate-admin"
    assert migrazione.apply is False


def test_consenso_email_richiede_flag_e_variabile() -> None:
    with pytest.raises(runtime_cli.ErroreCliRuntime, match="richiede"):
        runtime_cli._consenso_esterno(
            ModalitaEsecuzione.TEST_SMTP,
            flag_cli=True,
            ambiente={},
        )
    assert runtime_cli._consenso_esterno(
        ModalitaEsecuzione.TEST_SMTP,
        flag_cli=True,
        ambiente={"ALLOW_EMAIL_DELIVERY": "true"},
    ) is True


def _predisponi_run_fake(monkeypatch: pytest.MonkeyPatch, *, attiva: bool, stato: str):
    risorse = SimpleNamespace(admin_spreadsheet_id="admin")
    componenti = SimpleNamespace(
        trasporto_struttura=object(),
        lettore=object(),
        archivio_notifiche=object(),
        sorgente_operativo=object(),
        dashboard=object(),
        anomalie=object(),
    )
    config = SimpleNamespace(automazione_attiva=attiva)
    esito = SimpleNamespace(
        modalita=ModalitaEsecuzione.PRODUZIONE,
        stato=stato,
        righe_lette=0,
        righe_valide=0,
        anomalie=1 if stato == "ATTENZIONE" else 0,
        candidati=0,
        notifiche_gia_presenti=0,
        messaggi_composti=0,
        invii_tentati=0,
        invii_riusciti=0,
        invii_falliti=1 if stato == "ATTENZIONE" else 0,
        esiti_incerti=0,
    )
    monkeypatch.setattr(
        runtime_cli.ConfigurazioneRisorseGoogle,
        "da_ambiente",
        lambda ambiente: risorse,
    )
    monkeypatch.setattr(runtime_cli, "costruisci_servizio_sheets", lambda: object())
    monkeypatch.setattr(
        runtime_cli,
        "costruisci_componenti_google",
        lambda **kwargs: componenti,
    )
    monkeypatch.setattr(runtime_cli, "_verifica_struttura_admin", lambda *args, **kwargs: None)
    monkeypatch.setattr(runtime_cli, "leggi_matrice_config", lambda **kwargs: [[]])
    monkeypatch.setattr(runtime_cli, "carica_configurazione", lambda matrice: config)
    monkeypatch.setattr(runtime_cli, "RegistroPersistente", lambda *args, **kwargs: object())

    class OrchestratoreFake:
        def __init__(self, **kwargs):
            self.trasporto_email = kwargs["trasporto_email"]

        def esegui(self, **kwargs):
            return esito

    monkeypatch.setattr(runtime_cli, "OrchestratoreReminder", OrchestratoreFake)


def test_automazione_spenta_non_inizializza_smtp(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _predisponi_run_fake(monkeypatch, attiva=False, stato="DISATTIVATO")

    def smtp_vietato(_ambiente):
        raise AssertionError("SMTP non deve essere inizializzato")

    monkeypatch.setattr(runtime_cli.ConfigurazioneSmtp, "da_ambiente", smtp_vietato)
    risultato = runtime_cli._run(
        modalita=ModalitaEsecuzione.PRODUZIONE,
        oggi=runtime_cli.date(2026, 7, 20),
        conferma_email=False,
        ambiente={},
    )
    assert risultato == 0
    assert '"status": "DISATTIVATO"' in capsys.readouterr().out


def test_attenzione_restituisce_exit_code_non_zero(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _predisponi_run_fake(monkeypatch, attiva=True, stato="ATTENZIONE")
    risultato = runtime_cli._run(
        modalita=ModalitaEsecuzione.DRY_RUN,
        oggi=runtime_cli.date(2026, 7, 20),
        conferma_email=False,
        ambiente={},
    )
    assert risultato == 3


def test_errore_cli_non_stampa_notification_id(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["reminder-certificati", "dry-run"])

    def fallisce(*args, **kwargs):
        raise RuntimeError("duplicato A-123|2026-08-01|CERTIFICATO_SCADENZA_V1")

    monkeypatch.setattr(runtime_cli, "_run", fallisce)
    with pytest.raises(SystemExit) as exc_info:
        runtime_cli.main()
    messaggio = str(exc_info.value)
    assert "A-123" not in messaggio
    assert "notification-id-rimosso" in messaggio
