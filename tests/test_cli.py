from reminder_certificati import cli


def test_cli_storica_non_elabora_o_stampa_record(capsys) -> None:
    assert cli.main() == 2

    output = capsys.readouterr().out
    assert "non elabora più file con record" in output
    assert "@" not in output
    assert "notification_id" not in output
    assert "candidate" not in output.casefold()
