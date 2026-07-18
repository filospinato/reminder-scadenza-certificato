from __future__ import annotations

import re
from pathlib import Path

WORKFLOW_MANUALE = Path(".github/workflows/manual-preproduction.yml")
MODELLO_PRODUZIONE = Path("docs/workflows/production.yml.example")
CONTRATTO = Path("docs/CONTRATTO_ENVIRONMENT_GITHUB.md")


def _riferimenti(testo: str, contesto: str) -> set[str]:
    return set(re.findall(rf"\$\{{\{{\s*{contesto}\.([A-Z0-9_]+)\s*\}}\}}", testo))


def _sezione_documentata(testo: str, nome: str) -> set[str]:
    pattern = rf"<!-- BEGIN {re.escape(nome)} -->\s*```text\s*(.*?)\s*```\s*<!-- END {re.escape(nome)} -->"
    match = re.search(pattern, testo, flags=re.DOTALL)
    assert match is not None, f"Sezione documentale mancante: {nome}"
    return {riga.strip() for riga in match.group(1).splitlines() if riga.strip()}


def test_variables_usate_dai_workflow_sono_documentate():
    contratto = CONTRATTO.read_text(encoding="utf-8")
    manuale = WORKFLOW_MANUALE.read_text(encoding="utf-8")
    produzione = MODELLO_PRODUZIONE.read_text(encoding="utf-8")

    assert _riferimenti(manuale, "vars") <= _sezione_documentata(
        contratto, "PREPRODUCTION VARIABLES"
    )
    assert _riferimenti(produzione, "vars") <= _sezione_documentata(
        contratto, "PRODUCTION VARIABLES"
    )


def test_i_due_workflow_usano_i_segreti_smtp_documentati():
    contratto = CONTRATTO.read_text(encoding="utf-8")
    attesi = _sezione_documentata(contratto, "SMTP SECRETS")
    manuale = _riferimenti(WORKFLOW_MANUALE.read_text(encoding="utf-8"), "secrets")
    produzione = _riferimenti(MODELLO_PRODUZIONE.read_text(encoding="utf-8"), "secrets")

    assert manuale == attesi
    assert produzione == attesi


def test_credenziali_smtp_non_sono_variables():
    contratto = CONTRATTO.read_text(encoding="utf-8")
    pubbliche = _sezione_documentata(contratto, "PREPRODUCTION VARIABLES") | _sezione_documentata(
        contratto, "PRODUCTION VARIABLES"
    )

    assert {"SMTP_USERNAME", "SMTP_PASSWORD"}.isdisjoint(pubbliche)
    assert {"SMTP_FROM_NAME", "SMTP_REPLY_TO"} <= pubbliche
