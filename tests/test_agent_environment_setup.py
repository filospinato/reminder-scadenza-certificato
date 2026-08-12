from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

SETTINGS = Path(".claude/settings.json")
SESSION_HOOK = Path(".claude/hooks/session-start.sh")
SETUP_SCRIPT = Path("scripts/setup.sh")
VERIFY_SCRIPT = Path("scripts/verify.sh")
AGENT_RULES = Path("AGENTS.md")
README = Path("README.md")

# Lo strato di wrapper per Codex è stato rimosso: una sola procedura resta in
# `scripts/setup.sh`, e le tre superfici che la richiamavano non hanno più file
# propri da tenere allineati. Elencarli qui serve a impedire che rientrino in
# silenzio insieme alla duplicazione che portavano con sé.
WRAPPER_RIMOSSI = (
    Path(".codex/hooks.json"),
    Path(".codex/hooks/session-start.sh"),
    Path("config/codex/ENVIRONMENT_SETUP.md"),
)

EXPECTED_HOOK_COMMAND = 'bash "${CLAUDE_PROJECT_DIR:-.}/.claude/hooks/session-start.sh"'
EXPECTED_PIP_COMMAND = (
    "-m pip install --quiet --disable-pip-version-check "
    "--root-user-action=ignore --timeout 60 --retries 5 "
    "--editable .[dev,google]"
)
EXPECTED_FORCED_PIP_COMMAND = (
    "-m pip install --quiet --disable-pip-version-check "
    "--root-user-action=ignore --timeout 60 --retries 5 "
    "--force-reinstall --editable .[dev,google]"
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


def _prepara_setup_con_comandi_fake(
    tmp_path: Path,
    *,
    successo_al_tentativo: int,
) -> tuple[Path, dict[str, str], Path, Path]:
    progetto = tmp_path / "repository con spazi"
    setup = progetto / SETUP_SCRIPT
    setup.parent.mkdir(parents=True)
    shutil.copyfile(SETUP_SCRIPT, setup)
    setup.chmod(0o755)
    (progetto / "pyproject.toml").write_text(
        "[project]\nname = 'progetto-fake'\n",
        encoding="utf-8",
    )

    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    tentativi = tmp_path / "tentativi-pip"
    log_pip = tmp_path / "pip.log"
    log_sleep = tmp_path / "sleep.log"
    stato_core = tmp_path / "stato-core"
    stato_google = tmp_path / "stato-google"
    stato_pip_check = tmp_path / "stato-pip-check"

    _scrivi_eseguibile(
        fake_bin / "python3",
        r"""#!/usr/bin/env bash
if [ "${1:-}" = "-m" ] && [ "${2:-}" = "venv" ]; then
    mkdir -p "$3/bin"
    cp "$0" "$3/bin/python"
    cp "${FAKE_BIN:?}/pip" "$3/bin/pip"
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
        if [ "${FAKE_GOOGLE_REPAIR_ON_PIP:?}" = "1" ]; then
            printf 'ok\n' > "${FAKE_GOOGLE_STATE:?}"
        fi
        # pip vero riscrive un eseguibile solo quando reinstalla per davvero:
        # con il requisito soddisfatto non tocca il file e un tool rotto resta rotto.
        case "$*" in
            *--force-reinstall*)
                for tool in pip pytest ruff; do
                    printf '#!/usr/bin/env bash\nexit 0\n' > "$(dirname "$0")/$tool"
                    chmod 755 "$(dirname "$0")/$tool"
                done
                ;;
        esac
        exit 0
    fi
    exit 1
fi
if [ "${1:-}" = "--version" ]; then
    printf 'Python 3.12.9\n'
    exit 0
fi
if [ "${1:-}" = "-c" ]; then
    if printf '%s\n' "${2:-}" | grep -q 'UF_HIDDEN' &&
       [ "${FAKE_BREAK_CORE_ON_FLAG_NORMALIZATION:-0}" = "1" ] &&
       [ -f "${FAKE_PROJECT:?}/.venv/.setup-environment.sha256" ]; then
        printf 'rotto\n' > "${FAKE_CORE_STATE:?}"
    fi
    if [ "$#" -ge 4 ]; then
        cksum "$3" "$4" | cksum | awk '{print $1}'
    elif printf '%s\n' "${2:-}" | grep -q 'reminder_certificati' &&
         [ -f "${FAKE_CORE_STATE:?}" ] &&
         grep -q '^rotto$' "${FAKE_CORE_STATE:?}"; then
        exit 1
    elif printf '%s\n' "${2:-}" | grep -q 'google' &&
         [ -f "${FAKE_GOOGLE_STATE:?}" ] &&
         grep -q '^rotto$' "${FAKE_GOOGLE_STATE:?}"; then
        exit 1
    fi
    exit 0
fi
exit 97
""",
    )
    _scrivi_eseguibile(
        fake_bin / "pip",
        r"""#!/usr/bin/env bash
if [ "${1:-}" = "check" ] &&
   [ -f "${FAKE_PIP_CHECK_STATE:?}" ] &&
   grep -q '^rotto$' "${FAKE_PIP_CHECK_STATE:?}"; then
    exit 1
fi
exit 0
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
            "FAKE_BREAK_CORE_ON_FLAG_NORMALIZATION": "0",
            "FAKE_CORE_STATE": str(stato_core),
            "FAKE_GOOGLE_REPAIR_ON_PIP": "1",
            "FAKE_GOOGLE_STATE": str(stato_google),
            "FAKE_PIP_CHECK_STATE": str(stato_pip_check),
            "FAKE_PIP_ATTEMPTS": str(tentativi),
            "FAKE_PIP_LOG": str(log_pip),
            "FAKE_PIP_SUCCESS_ON": str(successo_al_tentativo),
            "FAKE_SLEEP_LOG": str(log_sleep),
        }
    )

    return progetto, env, log_pip, log_sleep


def _senza_andate_a_capo(testo: str) -> str:
    # Un requisito cercato in un documento non deve dipendere da dove il
    # paragrafo va a capo: riscrivere una riga per stare nei 79 caratteri non è
    # un cambiamento di regola, e non deve poter far fallire un test.
    return " ".join(testo.split())


def _righe(percorso: Path) -> list[str]:
    # Il setup può fermarsi prima di invocare pip — per esempio quando
    # rifiuta una `.venv` simbolica — e in quel caso il log non esiste.
    if not percorso.exists():
        return []
    return percorso.read_text(encoding="utf-8").splitlines()


def _esegui_setup_con_comandi_fake(
    tmp_path: Path,
    *,
    successo_al_tentativo: int,
    venv_simbolica: bool = False,
) -> tuple[subprocess.CompletedProcess[str], list[str], list[str]]:
    progetto, env, log_pip, log_sleep = _prepara_setup_con_comandi_fake(
        tmp_path,
        successo_al_tentativo=successo_al_tentativo,
    )
    if venv_simbolica:
        esterna = tmp_path / "ambiente esterno"
        esterna.mkdir()
        (progetto / ".venv").symlink_to(esterna, target_is_directory=True)

    risultato = _esegui(["bash", "scripts/setup.sh"], cwd=progetto, env=env)

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
    for script in (SESSION_HOOK, SETUP_SCRIPT, VERIFY_SCRIPT):
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


def test_lo_strato_wrapper_di_codex_resta_rimosso() -> None:
    for percorso in WRAPPER_RIMOSSI:
        assert not percorso.exists(), percorso

    # Nessun documento deve rimandare a file che non esistono più, altrimenti la
    # rimozione lascia dietro istruzioni che nessuno può seguire.
    for documento in (AGENT_RULES, README):
        testo = documento.read_text(encoding="utf-8")
        for percorso in WRAPPER_RIMOSSI:
            assert str(percorso) not in testo, f"{documento}: {percorso}"


def test_verify_dichiara_ogni_controllo_ed_e_l_unico_elenco() -> None:
    verifica = VERIFY_SCRIPT.read_text(encoding="utf-8")

    # Comandi, non prosa: se un controllo sparisce da qui, sparisce dal gate.
    for controllo in (
        '"$venv/bin/ruff" check .',
        '"$venv/bin/python" -m compileall -q src',
        '"$venv/bin/python" -m pip check',
        '"$venv/bin/pytest"',
        "git diff --check",
        "git status --porcelain",
    ):
        assert controllo in verifica

    # Il punto dell'intero contratto: l'elenco vive in `verify.sh` e in nessun
    # altro posto. Un blocco di comandi ricopiato in un documento diverge da ciò
    # che viene eseguito davvero, e diverge senza che nessuno se ne accorga.
    for documento in (AGENT_RULES, README):
        testo = documento.read_text(encoding="utf-8")
        for comando in (
            ".venv/bin/ruff",
            ".venv/bin/pytest",
            ".venv/bin/python -m compileall",
            ".venv/bin/python -m pip check",
        ):
            assert comando not in testo, f"{documento}: {comando}"

    workflow = Path(".github/workflows/ci.yml").read_text(encoding="utf-8")
    righe = [
        riga for riga in workflow.splitlines() if not riga.lstrip().startswith("#")
    ]
    corpo = "\n".join(righe)
    assert "bash scripts/setup.sh" in corpo
    assert "bash scripts/verify.sh" in corpo
    for delegato in ("ruff", "compileall", "pip check", "pip install"):
        assert delegato not in corpo, delegato


def test_verify_fallisce_chiuso_senza_ambiente_preparato(tmp_path: Path) -> None:
    progetto = tmp_path / "repository con spazi"
    verifica = progetto / VERIFY_SCRIPT
    verifica.parent.mkdir(parents=True)
    shutil.copyfile(VERIFY_SCRIPT, verifica)

    risultato = _esegui(["bash", "scripts/verify.sh"], cwd=progetto)

    assert risultato.returncode == 1
    assert "ambiente non pronto" in risultato.stderr
    assert "bash scripts/setup.sh" in risultato.stderr
    # Nessun controllo deve essere stato eseguito: un'assenza di strumenti non
    # va mai letta come un esito verde.
    assert "== Ruff ==" not in risultato.stdout
    assert "controlli dichiarati sono superati" not in risultato.stdout


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


def test_setup_warm_offline_non_invoca_pip(tmp_path: Path) -> None:
    progetto, env, log_pip, _ = _prepara_setup_con_comandi_fake(
        tmp_path,
        successo_al_tentativo=1,
    )

    primo = _esegui(["bash", "scripts/setup.sh"], cwd=progetto, env=env)
    env["FAKE_PIP_SUCCESS_ON"] = "0"
    secondo = _esegui(["bash", "scripts/setup.sh"], cwd=progetto, env=env)

    assert primo.returncode == secondo.returncode == 0
    assert _righe(log_pip) == [EXPECTED_PIP_COMMAND]
    assert "setup: dipendenze e configurazione già aggiornate" in secondo.stdout
    assert "setup: ambiente pronto (Python 3.12.9)" in secondo.stdout
    assert (progetto / ".venv" / ".setup-environment.sha256").is_file()


def test_setup_cambio_dipendenze_invalida_stamp(tmp_path: Path) -> None:
    progetto, env, log_pip, _ = _prepara_setup_con_comandi_fake(
        tmp_path,
        successo_al_tentativo=1,
    )
    stamp = progetto / ".venv" / ".setup-environment.sha256"

    primo = _esegui(["bash", "scripts/setup.sh"], cwd=progetto, env=env)
    impronta_iniziale = stamp.read_text(encoding="utf-8")
    pyproject = progetto / "pyproject.toml"
    pyproject.write_text(
        pyproject.read_text(encoding="utf-8") + "\n[project.optional-dependencies]\ndev = []\n",
        encoding="utf-8",
    )
    secondo = _esegui(["bash", "scripts/setup.sh"], cwd=progetto, env=env)

    assert primo.returncode == secondo.returncode == 0
    assert _righe(log_pip) == [EXPECTED_PIP_COMMAND, EXPECTED_PIP_COMMAND]
    assert stamp.read_text(encoding="utf-8") != impronta_iniziale
    assert "dipendenze installate da pyproject.toml" in secondo.stdout


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


def test_agents_impone_setup_come_primo_gate() -> None:
    regole = AGENT_RULES.read_text(encoding="utf-8")
    inizio = regole.index("### Il gate d’ambiente")
    fine = regole.index("### La verifica del progetto", inizio)
    gate = _senza_andate_a_capo(regole[inizio:fine])

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


def test_agents_dichiara_le_tre_modalita_di_accesso() -> None:
    regole = AGENT_RULES.read_text(encoding="utf-8")
    inizio = regole.index("### Modalità di accesso")
    modalita = _senza_andate_a_capo(regole[inizio : regole.index("\n## ", inizio)])

    for requisito in (
        "**Checkout con shell.**",
        "**Solo connettore GitHub.**",
        "**Nessun accesso al repository.**",
        # Una sessione senza shell non può eseguire i due comandi, e il rischio
        # non è che se ne accorga: è che li dichiari eseguiti comunque.
        "non simularli",
        "in bozza o bloccato",
    ):
        assert requisito in modalita

    # Il confine di ciò che il gate certifica deve restare scritto: i collaudi
    # sulle risorse live non passano da `verify.sh` e non sono coperti da un
    # esito verde.
    verifica = _senza_andate_a_capo(
        regole[
            regole.index("### La verifica del progetto") : regole.index(
                "### Modalità di accesso"
            )
        ]
    )
    assert "esattamente una cosa" in verifica
    assert "§5" in verifica


def test_setup_ripara_uno_strumento_guasto_con_reinstallazione_forzata(tmp_path: Path) -> None:
    progetto, env, log_pip, _ = _prepara_setup_con_comandi_fake(
        tmp_path,
        successo_al_tentativo=1,
    )
    primo = _esegui(["bash", "scripts/setup.sh"], cwd=progetto, env=env)
    log_pip.write_text("", encoding="utf-8")
    _scrivi_eseguibile(progetto / ".venv" / "bin" / "ruff", "#!/usr/bin/env bash\nexit 1\n")

    riparazione = _esegui(["bash", "scripts/setup.sh"], cwd=progetto, env=env)

    # Un'installazione ordinaria non riscrive un eseguibile che pip considera
    # già a posto: con stamp valido la riparazione passa direttamente alla
    # reinstallazione forzata, senza un tentativo ordinario preliminare.
    assert primo.returncode == riparazione.returncode == 0
    assert "ambiente riparato con una reinstallazione forzata" in riparazione.stdout
    assert _righe(log_pip) == [EXPECTED_FORCED_PIP_COMMAND]


def test_setup_ripara_dipendenze_google_mancanti_con_reinstallazione_forzata(
    tmp_path: Path,
) -> None:
    progetto, env, log_pip, _ = _prepara_setup_con_comandi_fake(
        tmp_path,
        successo_al_tentativo=1,
    )
    primo = _esegui(["bash", "scripts/setup.sh"], cwd=progetto, env=env)
    log_pip.write_text("", encoding="utf-8")
    Path(env["FAKE_GOOGLE_STATE"]).write_text("rotto\n", encoding="utf-8")

    riparazione = _esegui(["bash", "scripts/setup.sh"], cwd=progetto, env=env)

    assert primo.returncode == riparazione.returncode == 0
    assert "ambiente riparato con una reinstallazione forzata" in riparazione.stdout
    assert _righe(log_pip) == [EXPECTED_FORCED_PIP_COMMAND]


def test_setup_non_ripete_force_reinstall_se_la_riparazione_non_riesce(
    tmp_path: Path,
) -> None:
    progetto, env, log_pip, _ = _prepara_setup_con_comandi_fake(
        tmp_path,
        successo_al_tentativo=1,
    )
    primo = _esegui(["bash", "scripts/setup.sh"], cwd=progetto, env=env)
    log_pip.write_text("", encoding="utf-8")
    Path(env["FAKE_GOOGLE_STATE"]).write_text("rotto\n", encoding="utf-8")
    env["FAKE_GOOGLE_REPAIR_ON_PIP"] = "0"

    fallimento = _esegui(["bash", "scripts/setup.sh"], cwd=progetto, env=env)

    assert primo.returncode == 0
    assert fallimento.returncode == 1
    assert "ambiente riparato" not in fallimento.stdout
    assert "dipendenze Google non importabili" in fallimento.stderr
    assert _righe(log_pip) == [EXPECTED_FORCED_PIP_COMMAND]


def test_setup_ripara_un_pip_check_guasto_con_reinstallazione_forzata(
    tmp_path: Path,
) -> None:
    progetto, env, log_pip, _ = _prepara_setup_con_comandi_fake(
        tmp_path,
        successo_al_tentativo=1,
    )
    primo = _esegui(["bash", "scripts/setup.sh"], cwd=progetto, env=env)
    log_pip.write_text("", encoding="utf-8")
    Path(env["FAKE_PIP_CHECK_STATE"]).write_text("rotto\n", encoding="utf-8")

    riparazione = _esegui(["bash", "scripts/setup.sh"], cwd=progetto, env=env)

    assert primo.returncode == riparazione.returncode == 0
    assert "ambiente riparato con una reinstallazione forzata" in riparazione.stdout
    assert _righe(log_pip) == [EXPECTED_FORCED_PIP_COMMAND]


def test_setup_riverifica_dopo_stamp_e_normalizzazione_macos(tmp_path: Path) -> None:
    progetto, env, log_pip, _ = _prepara_setup_con_comandi_fake(
        tmp_path,
        successo_al_tentativo=1,
    )
    env["FAKE_PROJECT"] = str(progetto)
    env["FAKE_BREAK_CORE_ON_FLAG_NORMALIZATION"] = "1"

    fallimento = _esegui(["bash", "scripts/setup.sh"], cwd=progetto, env=env)

    assert fallimento.returncode == 1
    assert "setup: ambiente pronto" not in fallimento.stdout
    assert "pacchetto reminder_certificati non importabile" in fallimento.stderr
    assert _righe(log_pip) == [EXPECTED_PIP_COMMAND]


def test_setup_normalizza_i_flag_macos_senza_chflags_esterno() -> None:
    setup = SETUP_SCRIPT.read_text(encoding="utf-8")

    assert "os.chflags" in setup
    assert "stat.UF_HIDDEN" in setup
    assert "command -v chflags" not in setup
