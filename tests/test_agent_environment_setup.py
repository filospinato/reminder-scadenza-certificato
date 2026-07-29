from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

SETTINGS = Path(".claude/settings.json")
SESSION_HOOK = Path(".claude/hooks/session-start.sh")
SETUP_SCRIPT = Path("scripts/setup.sh")
CODEX_SETUP = Path("config/codex/ENVIRONMENT_SETUP.md")
CODEX_HOOKS = Path(".codex/hooks.json")
CODEX_SESSION_HOOK = Path(".codex/hooks/session-start.sh")
AGENT_RULES = Path("AGENTS.md")

EXPECTED_HOOK_COMMAND = 'bash "${CLAUDE_PROJECT_DIR:-.}/.claude/hooks/session-start.sh"'
EXPECTED_PIP_COMMAND = (
    "-m pip install --quiet --disable-pip-version-check "
    "--root-user-action=ignore --timeout 60 --retries 5 "
    "--editable .[dev,google]"
)


def _esegui(
    comando: list[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        comando,
        cwd=cwd,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )


def _scrivi_eseguibile(path: Path, contenuto: str) -> None:
    path.write_text(contenuto, encoding="utf-8")
    path.chmod(0o755)


def _esegui_setup_con_comandi_fake(
    tmp_path: Path,
    *,
    successo_al_tentativo: int,
    venv_simbolica: bool = False,
) -> tuple[subprocess.CompletedProcess[str], list[str], list[str]]:
    progetto = tmp_path / "repository con spazi"
    setup = progetto / SETUP_SCRIPT
    setup.parent.mkdir(parents=True)
    shutil.copyfile(SETUP_SCRIPT, setup)
    setup.chmod(0o755)

    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    tentativi = tmp_path / "tentativi-pip"
    log_pip = tmp_path / "pip.log"
    log_sleep = tmp_path / "sleep.log"

    _scrivi_eseguibile(
        fake_bin / "python3",
        r"""#!/usr/bin/env bash
if [ "${1:-}" = "-m" ] && [ "${2:-}" = "venv" ]; then
    mkdir -p "$3/bin"
    cp "$0" "$3/bin/python"
    cp "${FAKE_BIN:?}/pytest" "$3/bin/pytest"
    cp "${FAKE_BIN:?}/ruff" "$3/bin/ruff"
    exit 0
fi
if [ "${1:-}" = "-m" ] && [ "${2:-}" = "pip" ]; then
    tentativo=0
    if [ -f "${FAKE_PIP_ATTEMPTS:?}" ]; then
        IFS= read -r tentativo < "${FAKE_PIP_ATTEMPTS:?}"
    fi
    tentativo=$((tentativo + 1))
    printf '%s\n' "$tentativo" > "${FAKE_PIP_ATTEMPTS:?}"
    printf '%s\n' "$*" >> "${FAKE_PIP_LOG:?}"
    if [ "${FAKE_PIP_SUCCESS_ON:?}" -gt 0 ] &&
       [ "$tentativo" -ge "${FAKE_PIP_SUCCESS_ON:?}" ]; then
        exit 0
    fi
    exit 1
fi
if [ "${1:-}" = "--version" ]; then
    printf 'Python 3.12.9\n'
    exit 0
fi
if [ "${1:-}" = "-c" ]; then
    exit 0
fi
exit 97
""",
    )
    for comando in ("pytest", "ruff"):
        _scrivi_eseguibile(fake_bin / comando, "#!/usr/bin/env bash\nexit 0\n")
    _scrivi_eseguibile(
        fake_bin / "sleep",
        "#!/usr/bin/env bash\nprintf '%s\\n' \"${1:-}\" >> \"${FAKE_SLEEP_LOG:?}\"\n",
    )

    env = os.environ.copy()
    env.update(
        {
            "PATH": f"{fake_bin}{os.pathsep}{env['PATH']}",
            "FAKE_BIN": str(fake_bin),
            "FAKE_PIP_ATTEMPTS": str(tentativi),
            "FAKE_PIP_LOG": str(log_pip),
            "FAKE_PIP_SUCCESS_ON": str(successo_al_tentativo),
            "FAKE_SLEEP_LOG": str(log_sleep),
        }
    )
    if venv_simbolica:
        esterna = tmp_path / "ambiente esterno"
        esterna.mkdir()
        (progetto / ".venv").symlink_to(esterna, target_is_directory=True)

    risultato = _esegui(["bash", "scripts/setup.sh"], cwd=progetto, env=env)

    def _righe(percorso: Path) -> list[str]:
        # Il setup può fermarsi prima di invocare pip — per esempio quando
        # rifiuta una `.venv` simbolica — e in quel caso il log non esiste.
        if not percorso.exists():
            return []
        return percorso.read_text(encoding="utf-8").splitlines()

    return risultato, _righe(log_pip), _righe(log_sleep)


def test_settings_registra_tutte_le_origini_con_comando_robusto() -> None:
    settings = json.loads(SETTINGS.read_text(encoding="utf-8"))

    assert settings["hooks"]["SessionStart"] == [
        {
            "matcher": "startup|resume|clear|compact|fork",
            "hooks": [{"type": "command", "command": EXPECTED_HOOK_COMMAND}],
        }
    ]


def test_comando_hook_gestisce_percorso_con_spazi_e_fallback_locale(tmp_path: Path) -> None:
    progetto = tmp_path / "repository con spazi"
    hook = progetto / SESSION_HOOK
    setup = progetto / SETUP_SCRIPT
    hook.parent.mkdir(parents=True)
    setup.parent.mkdir(parents=True)
    shutil.copyfile(SESSION_HOOK, hook)
    hook.chmod(0o600)
    setup.write_text("#!/usr/bin/env bash\nprintf 'setup simulato\\n'\n", encoding="utf-8")
    setup.chmod(0o600)

    for project_dir, cwd in ((str(progetto), tmp_path), (None, progetto)):
        env = os.environ.copy()
        env["CLAUDE_CODE_REMOTE"] = "true"
        if project_dir is None:
            env.pop("CLAUDE_PROJECT_DIR", None)
        else:
            env["CLAUDE_PROJECT_DIR"] = project_dir

        risultato = _esegui(["bash", "-c", EXPECTED_HOOK_COMMAND], cwd=cwd, env=env)

        assert risultato.returncode == 0, risultato.stderr
        assert risultato.stdout == "setup simulato\n"
        assert risultato.stderr == ""


def test_script_shell_hanno_sintassi_valida() -> None:
    for script in (SESSION_HOOK, CODEX_SESSION_HOOK, SETUP_SCRIPT):
        risultato = _esegui(["bash", "-n", str(script)])
        assert risultato.returncode == 0, f"{script}: {risultato.stderr}"


def test_hook_locale_esegue_il_setup_condiviso(tmp_path: Path) -> None:
    progetto = tmp_path / "repository"
    setup = progetto / SETUP_SCRIPT
    setup.parent.mkdir(parents=True)
    setup.write_text(
        "#!/usr/bin/env bash\nprintf 'invocato\\n' > \"$CLAUDE_PROJECT_DIR/invocato\"\n",
        encoding="utf-8",
    )
    env = os.environ.copy()
    env.pop("CLAUDE_CODE_REMOTE", None)
    env["CLAUDE_PROJECT_DIR"] = str(progetto)

    risultato = _esegui(["bash", str(SESSION_HOOK)], env=env)

    assert risultato.returncode == 0
    assert risultato.stdout == ""
    assert risultato.stderr == ""
    assert (progetto / "invocato").read_text(encoding="utf-8") == "invocato\n"

    setup.write_text(
        "#!/usr/bin/env bash\nprintf 'setup fallito\\n' >&2\nexit 9\n",
        encoding="utf-8",
    )
    fallimento = _esegui(["bash", str(SESSION_HOOK)], env=env)
    assert fallimento.returncode == 0
    assert "setup fallito" in fallimento.stdout
    assert "GATE BLOCCANTE" in fallimento.stdout
    assert fallimento.stderr == ""


def test_hook_codex_e_scoped_e_blocca_setup_fallito(tmp_path: Path) -> None:
    hooks = json.loads(CODEX_HOOKS.read_text(encoding="utf-8"))
    comando = 'bash "$(git rev-parse --show-toplevel)/.codex/hooks/session-start.sh"'
    assert hooks["hooks"]["SessionStart"] == [
        {
            "matcher": "^(startup|resume|clear|compact)$",
            "hooks": [
                {
                    "type": "command",
                    "command": comando,
                    "timeout": 1800,
                    "statusMessage": "Preparo l'ambiente del repository",
                }
            ],
        }
    ]

    progetto = tmp_path / "repository con spazi"
    hook = progetto / CODEX_SESSION_HOOK
    setup = progetto / SETUP_SCRIPT
    hook.parent.mkdir(parents=True)
    setup.parent.mkdir(parents=True)
    shutil.copyfile(CODEX_SESSION_HOOK, hook)

    setup.write_text("#!/usr/bin/env bash\nprintf 'setup simulato\\n'\n", encoding="utf-8")
    successo = _esegui(["bash", str(hook)])
    assert successo.returncode == 0
    assert successo.stdout == "setup simulato\n"
    assert successo.stderr == ""

    setup.write_text(
        "#!/usr/bin/env bash\nprintf 'errore simulato\\n' >&2\nexit 9\n",
        encoding="utf-8",
    )
    fallimento = _esegui(["bash", str(hook)])
    assert fallimento.returncode == 0
    assert json.loads(fallimento.stdout) == {
        "continue": False,
        "stopReason": "Setup del repository fallito.",
        "systemMessage": (
            "Il setup locale non è riuscito: correggere l’ambiente prima di continuare."
        ),
    }
    assert fallimento.stderr == "errore simulato\n"


def test_setup_ritenta_senza_rete_ne_attese_reali(tmp_path: Path) -> None:
    risultato, chiamate_pip, attese = _esegui_setup_con_comandi_fake(
        tmp_path,
        successo_al_tentativo=3,
    )

    assert risultato.returncode == 0, risultato.stderr
    assert chiamate_pip == [EXPECTED_PIP_COMMAND] * 3
    assert attese == ["5", "10"]
    assert (
        "setup: dipendenze installate da pyproject.toml in .venv "
        "(extra dev, google)"
    ) in (
        risultato.stdout
    )
    assert "setup: ambiente pronto (Python 3.12.9)" in risultato.stdout


def test_setup_propaga_il_fallimento_dopo_tre_tentativi_fake(tmp_path: Path) -> None:
    risultato, chiamate_pip, attese = _esegui_setup_con_comandi_fake(
        tmp_path,
        successo_al_tentativo=0,
    )

    assert risultato.returncode == 1
    assert chiamate_pip == [EXPECTED_PIP_COMMAND] * 3
    assert attese == ["5", "10"]
    assert "installazione delle dipendenze non riuscita" in risultato.stderr
    assert "setup: ambiente pronto" not in risultato.stdout


def test_setup_rifiuta_venv_simbolica_fuori_checkout(tmp_path: Path) -> None:
    risultato, chiamate_pip, attese = _esegui_setup_con_comandi_fake(
        tmp_path,
        successo_al_tentativo=1,
        venv_simbolica=True,
    )

    assert risultato.returncode == 1
    assert "rifiutata .venv simbolica" in risultato.stderr
    assert chiamate_pip == []
    assert attese == []


def test_documentazione_codex_impone_il_gate_del_branch_predefinito() -> None:
    documentazione = CODEX_SETUP.read_text(encoding="utf-8")

    for requisito in ("soltanto dopo", "`scripts/setup.sh`", "`main`", "pull request"):
        assert requisito in documentazione

    for requisito in ("Codex Cloud", "Local", "Worktree", "`.codex/hooks.json`"):
        assert requisito in documentazione


def test_agents_impone_setup_come_primo_gate_codex_locale() -> None:
    regole = AGENT_RULES.read_text(encoding="utf-8")
    inizio = regole.index("Il `SessionStart` di Codex Local/Worktree")
    fine = regole.index("\n\nEseguire almeno:", inizio)
    gate = regole[inizio:fine]

    for requisito in (
        "`bash scripts/setup.sh`",
        "primo gate operativo",
        "prima di analizzare altri file",
        "modificare file",
        "eseguire test",
        "codice `0`",
        "`setup: ambiente pronto`",
        "fermarsi",
    ):
        assert requisito in gate
