from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def _leggi(path: str) -> str:
    return (REPOSITORY_ROOT / path).read_text(encoding="utf-8")


def test_workflow_preproduzione_non_usa_data_fissa_o_gate_job_level() -> None:
    workflow = _leggi(".github/workflows/manual-preproduction.yml")

    assert 'default: "2026-07-17"' not in workflow
    assert "group: reminder-certificati-runtime" in workflow
    assert "if: vars.PREPRODUCTION_ENABLED" not in workflow
    assert "environment: preproduction" in workflow
    assert "steps.gate.outputs.enabled == 'true'" in workflow


def test_workflow_preproduzione_richiede_file_amministrativo_esistente() -> None:
    workflow = _leggi(".github/workflows/manual-preproduction.yml")

    assert "ADMIN_SPREADSHEET_ID mancante" in workflow
    assert 'init-admin --spreadsheet-id "$ADMIN_SPREADSHEET_ID"' in workflow
    assert "reminder-certificati-runtime init-admin\n" not in workflow


def test_segreti_smtp_preproduzione_esistono_solo_nello_step_di_invio() -> None:
    workflow = _leggi(".github/workflows/manual-preproduction.yml")
    prima_dell_invio = workflow.split(
        "- name: Esegui test SMTP all'override", maxsplit=1
    )[0]

    assert "SMTP_PASSWORD" not in prima_dell_invio
    assert "SMTP_USERNAME" not in prima_dell_invio
    assert "SMTP_PASSWORD" in workflow


def test_modello_produzione_condivide_lock_e_limita_i_segreti() -> None:
    workflow = _leggi("docs/workflows/production.yml.example")
    prima_dell_invio = workflow.split("- name: Esecuzione produzione", maxsplit=1)[0]

    assert "group: reminder-certificati-runtime" in workflow
    assert "if: vars.PRODUCTION_ENABLED" not in workflow
    assert "steps.gate.outputs.enabled == 'true'" in workflow
    assert "SMTP_PASSWORD" not in prima_dell_invio
    assert "SMTP_PASSWORD" in workflow
