from __future__ import annotations

from pathlib import Path

WORKFLOW = Path(".github/workflows/production.yml")


def _testo() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def test_workflow_produttivo_e_attivo_solo_manualmente() -> None:
    testo = _testo()
    assert WORKFLOW.exists()
    assert "workflow_dispatch:" in testo
    assert "schedule:" not in testo
    assert "cron:" not in testo


def test_workflow_usa_unico_environment_wif_e_lock_condiviso() -> None:
    testo = _testo()
    assert "environment: preproduction" in testo
    assert "environment: production" not in testo
    assert "group: reminder-certificati-runtime" in testo
    assert "cancel-in-progress: false" in testo
    assert "contents: read" in testo
    assert "id-token: write" in testo
    assert "google-github-actions/auth@" in testo
    assert "# v3" in testo


def test_produzione_usa_il_solo_interruttore_del_foglio() -> None:
    testo = _testo()
    assert "run: reminder-certificati produzione --max-sends" in testo
    assert 'default: "1"' in testo
    for valore in (
        "PRODUCTION_ENABLED",
        "ALLOW_EMAIL_DELIVERY",
        "--confirm-email-delivery",
    ):
        assert valore not in testo
    assert "INVIO_AUTOMATICO_ATTIVO" in testo


def test_schedule_non_e_preconfigurata_prima_del_go_live() -> None:
    testo = _testo()
    assert "schedule:" not in testo
    assert "cron:" not in testo
    assert "Aggiungerne una sola" in testo


def test_invio_reale_e_limitato_al_branch_main() -> None:
    assert "if: github.ref == 'refs/heads/main'" in _testo()


def test_workflow_non_contiene_bootstrap_collaudi_o_modalita_non_produttive() -> None:
    testo = _testo()
    for valore in (
        "init-admin",
        "setup-admin",
        "check-headers",
        "preflight",
        "registry-check",
        "dry-run",
        "test-smtp",
        "ALLOW_SYNTHETIC_REGISTRY_WRITE",
    ):
        assert valore not in testo
    assert testo.count("reminder-certificati produzione") == 1


def test_segreti_smtp_restano_nello_step_produttivo() -> None:
    testo = _testo()
    indice = testo.index("- name: Esecuzione produzione")
    prima = testo[:indice]
    produzione = testo[indice:]

    assert "${{ secrets." not in prima
    for nome in (
        "SMTP_HOST",
        "SMTP_PORT",
        "SMTP_SECURITY",
        "SMTP_USERNAME",
    ):
        assert f"${{{{ vars.{nome} }}}}" in produzione
    assert "SMTP_FROM: ${{ vars.SMTP_USERNAME }}" in produzione
    assert "${{ secrets.REMINDER_SMTP_PASSWORD }}" in produzione
    assert "SMTP_FROM_NAME" not in testo


def test_workflow_configura_solo_l_id_del_foglio_operativo() -> None:
    testo = _testo()
    assert "${{ vars.OPERATIVO_SPREADSHEET_ID }}" in testo
    for nome in (
        "OPERATIVO_SHEET_NAME",
        "OPERATIVO_HEADER_ROW",
        "OPERATIVO_COLUMNS_A1",
    ):
        assert nome not in testo


def test_workflow_non_esegue_upgrade_dinamici_del_package_manager() -> None:
    assert "pip install --upgrade pip" not in _testo()
