import sys

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


def test_errore_cli_non_stampa_notification_id(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["runtime", "run"])

    def fallisce(*args, **kwargs):
        raise RuntimeError("duplicato A-123|2026-08-01|REMINDER_30")

    monkeypatch.setattr(runtime_cli, "_run", fallisce)

    with pytest.raises(SystemExit) as exc_info:
        runtime_cli.main()

    messaggio = str(exc_info.value)
    assert "A-123" not in messaggio
    assert "notification-id-rimosso" in messaggio
