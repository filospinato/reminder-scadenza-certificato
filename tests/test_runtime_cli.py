import sys
from types import SimpleNamespace

import pytest

from reminder_certificati import runtime_cli
from reminder_certificati.orchestrator import ModalitaEsecuzione


def test_setup_admin_richiede_spreadsheet_id() -> None:
    parser = runtime_cli.build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["setup-admin"])
    args = parser.parse_args(
        ["setup-admin", "--spreadsheet-id", "synthetic-sheet"]
    )
    assert args.spreadsheet_id == "synthetic-sheet"
    assert args.apply is False


def test_cli_espone_solo_le_operazioni_semplici() -> None:
    parser = runtime_cli.build_parser()
    for comando in (
        "setup-admin",
        "check",
        "registry-check",
        "test-smtp",
        "produzione",
    ):
        args = [comando]
        if comando == "setup-admin":
            args.extend(["--spreadsheet-id", "admin"])
        assert parser.parse_args(args).comando == comando

    for comando in (
        "init-admin",
        "migrate-admin",
        "preflight",
        "review-registry",
        "dry-run",
    ):
        with pytest.raises(SystemExit):
            parser.parse_args([comando])


def test_cli_non_accetta_vecchie_conferme() -> None:
    parser = runtime_cli.build_parser()
    for args in (
        ["test-smtp", "--confirm-email-delivery"],
        ["registry-check", "--confirm-synthetic-write"],
        ["setup-admin", "--spreadsheet-id", "admin", "--confirm-migration"],
    ):
        with pytest.raises(SystemExit):
            parser.parse_args(args)


def _predisponi_run_fake(
    monkeypatch: pytest.MonkeyPatch,
    *,
    attiva: bool,
    stato: str,
    modalita: ModalitaEsecuzione,
):
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
        modalita=modalita,
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
    monkeypatch.setattr(
        runtime_cli,
        "_verifica_struttura_admin",
        lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(runtime_cli, "leggi_matrice_config", lambda **kwargs: [[]])
    monkeypatch.setattr(runtime_cli, "carica_configurazione", lambda matrice: config)
    monkeypatch.setattr(runtime_cli, "RegistroPersistente", lambda *args, **kwargs: object())

    class OrchestratoreFake:
        def __init__(self, **kwargs):
            self.trasporto_email = kwargs["trasporto_email"]

        def esegui(self, **kwargs):
            return esito

    monkeypatch.setattr(runtime_cli, "OrchestratoreReminder", OrchestratoreFake)


def test_produzione_spenta_non_inizializza_smtp(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _predisponi_run_fake(
        monkeypatch,
        attiva=False,
        stato="DISATTIVATO",
        modalita=ModalitaEsecuzione.PRODUZIONE,
    )

    def smtp_vietato(_ambiente):
        raise AssertionError("SMTP non deve essere inizializzato")

    monkeypatch.setattr(runtime_cli.ConfigurazioneSmtp, "da_ambiente", smtp_vietato)
    risultato = runtime_cli._run(
        modalita=ModalitaEsecuzione.PRODUZIONE,
        oggi=runtime_cli.date(2026, 7, 20),
        ambiente={},
    )

    assert risultato == 0
    output = capsys.readouterr().out
    assert '"status": "DISATTIVATO"' in output
    assert '"status_label": "Invio automatico spento"' in output


def test_test_smtp_inizializza_smtp_anche_con_automazione_spenta(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _predisponi_run_fake(
        monkeypatch,
        attiva=False,
        stato="OK",
        modalita=ModalitaEsecuzione.TEST_SMTP,
    )
    configurazione_smtp = object()
    monkeypatch.setattr(
        runtime_cli.ConfigurazioneSmtp,
        "da_ambiente",
        lambda ambiente: configurazione_smtp,
    )
    trasporto = object()
    monkeypatch.setattr(
        runtime_cli,
        "TrasportoSmtpMdaemon",
        lambda config: trasporto,
    )

    assert runtime_cli._run(
        modalita=ModalitaEsecuzione.TEST_SMTP,
        oggi=runtime_cli.date(2026, 7, 20),
        ambiente={},
    ) == 0


def test_attenzione_restituisce_exit_code_non_zero(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _predisponi_run_fake(
        monkeypatch,
        attiva=False,
        stato="ATTENZIONE",
        modalita=ModalitaEsecuzione.DRY_RUN,
    )
    risultato = runtime_cli._run(
        modalita=ModalitaEsecuzione.DRY_RUN,
        oggi=runtime_cli.date(2026, 7, 20),
        ambiente={},
    )
    assert risultato == 3


def test_errore_cli_non_stampa_notification_id(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["reminder-certificati", "check"])

    def fallisce(*args, **kwargs):
        raise RuntimeError("duplicato A-123|2026-08-01|REMINDER_30")

    monkeypatch.setattr(runtime_cli, "_check", fallisce)
    with pytest.raises(SystemExit) as exc_info:
        runtime_cli.main()
    messaggio = str(exc_info.value)
    assert "A-123" not in messaggio
    assert "notification-id-rimosso" in messaggio
