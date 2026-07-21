from __future__ import annotations

from pathlib import Path

ORDINARIO = Path(".github/workflows/manual-preproduction.yml")
MANUTENZIONE = Path(".github/workflows/manual-maintenance.yml")


def test_workflow_ordinario_espone_solo_le_due_azioni_quotidiane() -> None:
    testo = ORDINARIO.read_text(encoding="utf-8")

    assert "default: check" in testo
    assert "- check" in testo
    assert "- test-smtp" in testo
    for operazione in (
        "preflight",
        "init-admin",
        "migrate-admin",
        "registry-check",
        "review-registry",
        "dry-run",
    ):
        assert f"- {operazione}" not in testo
    assert "reminder-certificati check" in testo
    assert "reminder-certificati test-smtp" in testo
    assert "today:" not in testo


def test_workflow_ordinario_non_usa_gate_o_conferme_duplicate() -> None:
    testo = ORDINARIO.read_text(encoding="utf-8")

    for valore in (
        "PREPRODUCTION_ENABLED",
        "ALLOW_EMAIL_DELIVERY",
        "--confirm-email-delivery",
        "confirm_email_delivery",
    ):
        assert valore not in testo
    assert "environment: preproduction" in testo
    assert "group: reminder-certificati-runtime" in testo


def test_workflow_ordinario_configura_solo_l_id_di_operativo() -> None:
    testo = ORDINARIO.read_text(encoding="utf-8")

    assert "${{ vars.OPERATIVO_SPREADSHEET_ID }}" in testo
    for nome in (
        "OPERATIVO_SHEET_NAME",
        "OPERATIVO_HEADER_ROW",
        "OPERATIVO_COLUMNS_A1",
    ):
        assert nome not in testo


def test_segreti_smtp_restano_nel_solo_test_email() -> None:
    testo = ORDINARIO.read_text(encoding="utf-8")
    indice = testo.index("- name: Invia una email di prova")
    prima = testo[:indice]
    blocco = testo[indice:]

    assert "${{ secrets." not in prima
    for nome in (
        "SMTP_HOST",
        "SMTP_PORT",
        "SMTP_SECURITY",
        "SMTP_FROM",
        "SMTP_USERNAME",
        "SMTP_PASSWORD",
    ):
        assert f"${{{{ secrets.{nome} }}}}" in blocco
    assert "SMTP_FROM_NAME" not in testo


def test_workflow_manutenzione_separa_setup_e_registro() -> None:
    testo = MANUTENZIONE.read_text(encoding="utf-8")

    for operazione in ("setup-preview", "setup-apply", "registry-check"):
        assert f"- {operazione}" in testo
    assert "reminder-certificati setup-admin" in testo
    assert "--apply --backup-path admin-migration-backup.json" in testo
    assert "actions/upload-artifact@v4" in testo
    assert "if: always() && inputs.operation == 'setup-apply'" in testo
    assert "retention-days: 7" in testo
    assert "reminder-certificati registry-check" in testo
    assert "--confirm-migration" not in testo
    assert "--confirm-synthetic-write" not in testo
    assert "ALLOW_SYNTHETIC_REGISTRY_WRITE" not in testo
    assert "${{ secrets." not in testo


def test_i_due_workflow_mantengono_wif_lock_e_installazione_riproducibile() -> None:
    for percorso in (ORDINARIO, MANUTENZIONE):
        testo = percorso.read_text(encoding="utf-8")
        assert "environment: preproduction" in testo
        assert "group: reminder-certificati-runtime" in testo
        assert "google-github-actions/auth@v3" in testo
        assert "pip install --upgrade pip" not in testo
