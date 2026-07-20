from __future__ import annotations

from pathlib import Path

WORKFLOW = Path(".github/workflows/manual-preproduction.yml")


def _testo() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def test_workflow_espone_le_operazioni_della_cli_unica():
    testo = _testo()
    for operazione in (
        "preflight",
        "init-admin",
        "migrate-admin",
        "registry-check",
        "review-registry",
        "dry-run",
        "test-smtp",
    ):
        assert f"- {operazione}" in testo
    assert "check-headers" not in testo
    assert "reminder-certificati preflight" in testo
    assert "reminder-certificati registry-check --confirm-synthetic-write" in testo
    assert "reminder-certificati review-registry" in testo
    assert "run: reminder-certificati-runtime" not in testo


def test_migrazione_richiede_conferma_e_salva_backup():
    testo = _testo()
    indice = testo.index("inputs.operation == 'migrate-admin'")
    blocco = testo[indice : testo.index("inputs.operation == 'registry-check'", indice)]
    assert "inputs.confirm_admin_migration" in blocco
    assert "--apply --confirm-migration" in blocco
    assert "admin-migration-backup.json" in blocco
    assert "actions/upload-artifact@v4" in blocco
    assert "retention-days: 3" in blocco
    assert "${{ secrets." not in blocco


def test_scrittura_sintetica_richiede_doppio_consenso_senza_segreti_smtp():
    testo = _testo()
    indice = testo.index("inputs.operation == 'registry-check'")
    blocco = testo[indice : testo.index("inputs.operation == 'review-registry'", indice)]
    assert "inputs.confirm_synthetic_registry_write" in blocco
    assert 'ALLOW_SYNTHETIC_REGISTRY_WRITE: "true"' in blocco
    assert "--confirm-synthetic-write" in blocco
    assert "${{ secrets." not in blocco
    assert "ALLOW_EMAIL_DELIVERY" not in blocco


def test_preflight_non_riceve_consensi_di_scrittura_o_email():
    testo = _testo()
    indice = testo.index("inputs.operation == 'preflight'")
    blocco = testo[indice : testo.index("inputs.operation == 'init-admin'", indice)]
    assert "reminder-certificati preflight" in blocco
    assert "ALLOW_SYNTHETIC_REGISTRY_WRITE" not in blocco
    assert "ALLOW_EMAIL_DELIVERY" not in blocco
    assert "${{ secrets." not in blocco


def test_segreti_smtp_restano_nel_solo_test_email():
    testo = _testo()
    indice = testo.index("inputs.operation == 'test-smtp'")
    blocco = testo[indice:]
    assert "${{ secrets." not in testo[:indice]
    for nome in (
        "SMTP_HOST",
        "SMTP_PORT",
        "SMTP_SECURITY",
        "SMTP_FROM",
        "SMTP_USERNAME",
        "SMTP_PASSWORD",
    ):
        assert f"${{{{ secrets.{nome} }}}}" in blocco
    assert 'ALLOW_EMAIL_DELIVERY: "true"' in blocco


def test_workflow_mantiene_environment_lock_e_installazione_riproducibile():
    testo = _testo()
    assert "environment: preproduction" in testo
    assert "group: reminder-certificati-runtime" in testo
    assert "PREPRODUCTION_ENABLED: ${{ vars.PREPRODUCTION_ENABLED }}" in testo
    assert "pip install --upgrade pip" not in testo
