from __future__ import annotations

from pathlib import Path


WORKFLOW = Path(".github/workflows/manual-preproduction.yml")


def _testo_workflow() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def _blocco_step(testo: str, nome: str, nome_successivo: str | None = None) -> str:
    inizio = testo.index(f"      - name: {nome}")
    if nome_successivo is None:
        return testo[inizio:]
    fine = testo.index(f"      - name: {nome_successivo}", inizio)
    return testo[inizio:fine]


def test_workflow_espone_preflight_e_collaudo_registro_come_operazioni_distinte():
    testo = _testo_workflow()

    assert "default: google-preflight" in testo
    assert "          - google-preflight" in testo
    assert "          - registry-check" in testo
    assert "run: reminder-certificati-google-preflight" in testo
    assert "run: reminder-certificati-registry-check --confirm-synthetic-write" in testo


def test_scrittura_sintetica_richiede_due_consensi_e_non_eredita_segreti_smtp():
    testo = _testo_workflow()
    blocco = _blocco_step(
        testo,
        "Collauda il registro con una riga sintetica",
        "Rifiuta collaudo registro senza conferma",
    )

    assert "inputs.confirm_synthetic_registry_write" in blocco
    assert 'ALLOW_SYNTHETIC_REGISTRY_WRITE: "true"' in blocco
    assert "--confirm-synthetic-write" in blocco
    assert "secrets." not in blocco
    assert "ALLOW_EMAIL_DELIVERY" not in blocco


def test_preflight_resta_in_sola_lettura_e_senza_consensi_di_scrittura_o_email():
    testo = _testo_workflow()
    blocco = _blocco_step(testo, "Esegui preflight Google in sola lettura", "Controlla intestazioni")

    assert "inputs.operation == 'google-preflight'" in blocco
    assert "reminder-certificati-google-preflight" in blocco
    assert "ALLOW_SYNTHETIC_REGISTRY_WRITE" not in blocco
    assert "ALLOW_EMAIL_DELIVERY" not in blocco
    assert "secrets." not in blocco


def test_segreti_smtp_restano_limitati_al_solo_step_test_smtp():
    testo = _testo_workflow()
    blocco_smtp = _blocco_step(testo, "Esegui test SMTP all'override", "Rifiuta test SMTP senza conferma")

    assert testo.count("${{ secrets.") == 6
    assert blocco_smtp.count("${{ secrets.") == 6
    assert 'ALLOW_EMAIL_DELIVERY: "true"' in blocco_smtp


def test_workflow_mantiene_gate_environment_e_lock_condiviso():
    testo = _testo_workflow()

    assert "environment: preproduction" in testo
    assert "group: reminder-certificati-runtime" in testo
    assert "PREPRODUCTION_ENABLED: ${{ vars.PREPRODUCTION_ENABLED }}" in testo
    assert "if: steps.gate.outputs.enabled == 'true'" in testo
