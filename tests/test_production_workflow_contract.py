from __future__ import annotations

from pathlib import Path

MODELLO = Path("docs/workflows/production.yml.example")
WORKFLOW_ATTIVO = Path(".github/workflows/production.yml")


def _testo() -> str:
    return MODELLO.read_text(encoding="utf-8")


def test_modello_resta_non_attivo_e_fuori_dai_workflow_eseguibili():
    testo = _testo()
    assert MODELLO.exists()
    assert not WORKFLOW_ATTIVO.exists()
    assert testo.startswith("# MODELLO NON ATTIVO:")


def test_modello_usa_environment_wif_e_lock_condiviso():
    testo = _testo()
    assert "environment: production" in testo
    assert "group: reminder-certificati-runtime" in testo
    assert "cancel-in-progress: false" in testo
    assert "contents: read" in testo
    assert "id-token: write" in testo
    assert "google-github-actions/auth@v3" in testo


def test_produzione_usa_un_solo_gate_esterno_reale():
    testo = _testo()
    assert "PRODUCTION_ENABLED: ${{ vars.PRODUCTION_ENABLED }}" in testo
    assert '"${PRODUCTION_ENABLED:-}" == "true"' in testo
    assert "run: reminder-certificati produzione" in testo
    assert "ALLOW_EMAIL_DELIVERY" not in testo
    assert "--confirm-email-delivery" not in testo


def test_modello_ha_una_sola_esecuzione_giornaliera():
    testo = _testo()
    assert testo.count("cron:") == 1


def test_modello_non_contiene_bootstrap_collaudi_o_modalita_non_produttive():
    testo = _testo()
    for valore in (
        "init-admin",
        "check-headers",
        "preflight",
        "registry-check",
        "dry-run",
        "test-smtp",
        "ALLOW_SYNTHETIC_REGISTRY_WRITE",
    ):
        assert valore not in testo
    assert "run: reminder-certificati-runtime" not in testo
    assert testo.count("reminder-certificati produzione") == 1


def test_segreti_smtp_restano_nello_step_produttivo():
    testo = _testo()
    indice = testo.index("- name: Esecuzione produzione")
    prima = testo[:indice]
    produzione = testo[indice:]

    assert "${{ secrets." not in prima
    for nome in (
        "SMTP_HOST",
        "SMTP_PORT",
        "SMTP_SECURITY",
        "SMTP_FROM",
        "SMTP_USERNAME",
        "SMTP_PASSWORD",
    ):
        assert f"${{{{ secrets.{nome} }}}}" in produzione


def test_modello_non_esegue_upgrade_dinamici_del_package_manager():
    assert "pip install --upgrade pip" not in _testo()
