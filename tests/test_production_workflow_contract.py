from __future__ import annotations

from pathlib import Path


MODELLO = Path("docs/workflows/production.yml.example")
WORKFLOW_ATTIVO = Path(".github/workflows/production.yml")


def _testo_modello() -> str:
    return MODELLO.read_text(encoding="utf-8")


def _blocco_step(testo: str, nome: str, nome_successivo: str | None = None) -> str:
    inizio = testo.index(f"      - name: {nome}")
    if nome_successivo is None:
        return testo[inizio:]
    fine = testo.index(f"      - name: {nome_successivo}", inizio)
    return testo[inizio:fine]


def test_modello_resta_fuori_dai_workflow_attivi_e_dichiara_di_non_essere_attivo():
    testo = _testo_modello()

    assert MODELLO.exists()
    assert not WORKFLOW_ATTIVO.exists()
    assert testo.startswith(
        "# MODELLO NON ATTIVO: non spostare in .github/workflows senza autorizzazione finale."
    )


def test_modello_usa_environment_production_lock_condiviso_e_wif_temporaneo():
    testo = _testo_modello()

    assert "environment: production" in testo
    assert "group: reminder-certificati-runtime" in testo
    assert "cancel-in-progress: false" in testo
    assert "permissions:\n  contents: read\n  id-token: write" in testo
    assert "uses: google-github-actions/auth@v3" in testo
    assert "create_credentials_file: true" in testo


def test_gate_richiede_abilitazione_e_acknowledgement_esterno_prima_del_checkout():
    testo = _testo_modello()
    gate = _blocco_step(testo, "Verifica abilitazione e approvazione production", "Checkout")

    assert "PRODUCTION_ENABLED: ${{ vars.PRODUCTION_ENABLED }}" in gate
    assert "PRODUCTION_WORKFLOW_APPROVED: ${{ vars.PRODUCTION_WORKFLOW_APPROVED }}" in gate
    assert '"${PRODUCTION_ENABLED:-}" == "true"' in gate
    assert (
        '"${PRODUCTION_WORKFLOW_APPROVED:-}" == "REMINDER_CERTIFICATI_SCHEDULE_V1"'
        in gate
    )
    assert 'echo "enabled=true" >> "$GITHUB_OUTPUT"' in gate
    assert "secrets." not in gate

    checkout = _blocco_step(testo, "Checkout", "Autenticazione Google temporanea")
    assert "if: steps.gate.outputs.enabled == 'true'" in checkout


def test_modello_non_contiene_comandi_di_bootstrap_collaudo_o_modalita_non_produttive():
    testo = _testo_modello()

    vietati = (
        "init-admin",
        "check-headers",
        "reminder-certificati-google-preflight",
        "reminder-certificati-registry-check",
        "--mode DRY_RUN",
        "--mode TEST_SMTP",
        "ALLOW_SYNTHETIC_REGISTRY_WRITE",
    )
    for valore in vietati:
        assert valore not in testo

    assert testo.count("reminder-certificati-runtime run") == 1
    assert (
        "run: reminder-certificati-runtime run --mode PRODUZIONE --confirm-email-delivery"
        in testo
    )


def test_segreti_e_consensi_email_restano_nel_solo_step_produttivo():
    testo = _testo_modello()
    produzione = _blocco_step(testo, "Esecuzione produzione")

    assert testo.count("${{ secrets.") == 6
    assert produzione.count("${{ secrets.") == 6
    assert 'ALLOW_EMAIL_DELIVERY: "true"' in produzione
    assert "PRODUCTION_ACTIVATION_ACK: REMINDER_CERTIFICATI_PRODUCTION_V1" in produzione
    assert "--confirm-email-delivery" in produzione

    prima_della_produzione = testo[: testo.index("      - name: Esecuzione produzione")]
    assert "${{ secrets." not in prima_della_produzione
    assert "ALLOW_EMAIL_DELIVERY" not in prima_della_produzione
    assert "PRODUCTION_ACTIVATION_ACK" not in prima_della_produzione


def test_schedule_rimane_esplicita_e_documenta_le_barriere_pre_go_live():
    testo = _testo_modello()

    assert 'cron: "15 6 * * *"' in testo
    assert 'cron: "15 16 * * *"' in testo
    assert "PRODUCTION_ENABLED=true" in testo
    assert (
        "PRODUCTION_WORKFLOW_APPROVED=REMINDER_CERTIFICATI_SCHEDULE_V1" in testo
    )
    assert "vincolare WIF anche a questo workflow_ref" in testo
    assert "verificare gli orari UTC della schedule" in testo
