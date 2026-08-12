import re
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def _leggi(path: str) -> str:
    return (REPOSITORY_ROOT / path).read_text(encoding="utf-8")


def test_workflow_ordinario_non_usa_data_fissa_o_gate_ridondanti() -> None:
    workflow = _leggi(".github/workflows/manual-preproduction.yml")

    assert 'default: "2026-07-17"' not in workflow
    assert "today:" not in workflow
    assert "group: reminder-certificati-runtime" in workflow
    assert "environment: preproduction" in workflow
    assert "PREPRODUCTION_ENABLED" not in workflow
    assert "steps.gate.outputs.enabled" not in workflow
    assert "reminder-certificati check" in workflow


def test_manutenzione_gestisce_il_foglio_amministrativo() -> None:
    workflow = _leggi(".github/workflows/manual-maintenance.yml")

    assert 'ADMIN_SPREADSHEET_ID: ${{ vars.ADMIN_SPREADSHEET_ID }}' in workflow
    assert 'setup-admin --spreadsheet-id "$ADMIN_SPREADSHEET_ID"' in workflow
    assert "setup-admin --spreadsheet-id \"$ADMIN_SPREADSHEET_ID\" --apply" in workflow
    assert "actions/upload-artifact@" in workflow
    assert "# v7.0.1" in workflow
    assert "init-admin" not in workflow
    assert "migrate-admin" not in workflow


def test_segreti_smtp_ordinari_esistono_solo_nello_step_di_invio() -> None:
    workflow = _leggi(".github/workflows/manual-preproduction.yml")
    nome_step = "- name: Invia una email di prova all'override"
    assert nome_step in workflow
    prima_dell_invio = workflow.split(nome_step, maxsplit=1)[0]

    assert "SMTP_PASSWORD" not in prima_dell_invio
    assert "SMTP_USERNAME" not in prima_dell_invio
    assert "SMTP_PASSWORD" in workflow
    assert "reminder-certificati test-smtp" in workflow


def test_workflow_produzione_condivide_lock_e_limita_i_segreti() -> None:
    workflow = _leggi(".github/workflows/production.yml")
    prima_dell_invio = workflow.split("- name: Esecuzione produzione", maxsplit=1)[0]

    assert "group: reminder-certificati-runtime" in workflow
    assert "PRODUCTION_ENABLED" not in workflow
    assert "steps.gate.outputs.enabled" not in workflow
    assert "SMTP_PASSWORD" not in prima_dell_invio
    assert "SMTP_PASSWORD" in workflow
    assert "schedule:" not in workflow
    assert "reminder-certificati produzione" in workflow


def test_ci_annulla_i_run_superati_solo_sulle_pull_request() -> None:
    workflow = _leggi(".github/workflows/ci.yml")

    assert "cancel-in-progress: ${{ github.event_name == 'pull_request' }}" in workflow
    # Il gruppo per i push a main e distinto per commit: senza lo SHA GitHub
    # terrebbe un solo run in attesa per gruppo e annullerebbe i precedenti.
    assert (
        "group: ${{ github.workflow }}-"
        "${{ github.event_name == 'pull_request' && github.ref || github.sha }}" in workflow
    )


def test_ci_usa_solo_python_3_12_sui_trigger_ordinari() -> None:
    workflow = _leggi(".github/workflows/ci.yml")
    trigger = workflow.split("on:\n", maxsplit=1)[1].split("\npermissions:", maxsplit=1)[0]

    assert re.findall(r"^  ([a-z_]+):", trigger, flags=re.MULTILINE) == [
        "push",
        "pull_request",
        "workflow_dispatch",
    ]
    assert "schedule:" not in trigger
    assert 'python-version: "3.12"' in workflow
    assert "matrix." not in workflow
    assert "strategy:" not in workflow


def test_tutte_le_actions_sono_fissate_a_sha_immutabili() -> None:
    percorsi = (
        ".github/workflows/ci.yml",
        ".github/workflows/manual-maintenance.yml",
        ".github/workflows/manual-preproduction.yml",
        ".github/workflows/production.yml",
    )

    for percorso in percorsi:
        workflow = _leggi(percorso)
        riferimenti = re.findall(r"uses:\s*[^@\s]+@([^\s#]+)", workflow)
        assert riferimenti, percorso
        assert all(re.fullmatch(r"[0-9a-f]{40}", ref) for ref in riferimenti), percorso
