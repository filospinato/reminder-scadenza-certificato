#!/usr/bin/env bash
# Prepara l'ambiente di sviluppo del repository.
#
# È il punto unico da cui passano tutti gli agenti: l'hook di avvio di Claude
# Code lo richiama, Codex lo esegue nella fase di setup — l'unica in cui la rete
# è disponibile, perché la fase agente gira isolata — e una persona può
# lanciarlo a mano. Una sola procedura, tre modi di invocarla.
#
# La lista delle dipendenze resta in `pyproject.toml`: duplicarla qui farebbe
# divergere le due fonti e l'ambiente finirebbe per mentire su cosa è installato.
# Gli extra installati sono gli stessi della CI, `dev` e `google`, perché una
# verifica locale che gira su un insieme diverso non dimostra nulla.
#
# Idempotente e non interattivo: eseguirlo due volte non cambia il risultato e
# non chiede mai niente.

set -uo pipefail

radice="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$radice" || exit 1

# Fotografa il checkout prima che questo script possa toccare qualsiasi cosa,
# così `scripts/verify.sh` può dimostrare che né il setup né la verifica lo
# hanno modificato. La fotografia vive dentro `.git/`, fuori dal working tree,
# quindi registrarla non altera ciò che misura. Si confronta il contenuto e non
# i soli codici di stato: `git status --porcelain` non distingue un file già
# modificato dallo stesso file modificato di nuovo. Se non si riesce a
# registrarla non si dice niente e `verify.sh` ricade sulla propria baseline più
# ristretta: stdout e stderr del setup sono fissati dai test e restano identici.
# `git rev-parse --git-path` risolve correttamente anche in un worktree
# collegato, dove `.git` è un file e non una directory.
stato_albero_iniziale() {
    git status --porcelain=v1 --untracked-files=all &&
        printf -- '--- contenuto tracciato ---\n' &&
        git diff --binary --no-ext-diff HEAD
}

percorso_baseline="$(git rev-parse --git-path reminder-tree-baseline 2>/dev/null)"
if [ -n "$percorso_baseline" ]; then
    stato_albero_iniziale > "$percorso_baseline" 2>/dev/null || \
        rm -f "$percorso_baseline" 2>/dev/null || :
fi

venv="$radice/.venv"
python_venv="$venv/bin/python"
stamp_dipendenze="$venv/.setup-environment.sha256"
esito=0

avviso() {
    printf 'setup: %s\n' "$1" >&2
    esito=1
}

# Riporta il primo guasto trovato in `problema` invece di segnalarlo subito,
# così la stessa verifica serve sia a decidere se riparare sia a dare il verdetto.
problema=''
verifica() {
    problema=''
    if ! "$python_venv" -c 'import reminder_certificati' >/dev/null 2>&1; then
        problema='pacchetto reminder_certificati non importabile dalla .venv'
        return 1
    fi
    if ! "$python_venv" -c \
        'import google.auth, googleapiclient.discovery' >/dev/null 2>&1; then
        problema='dipendenze Google non importabili dalla .venv'
        return 1
    fi
    local comando
    for comando in pip pytest ruff; do
        if [ ! -x "$venv/bin/$comando" ] ||
           ! "$venv/bin/$comando" --version >/dev/null 2>&1; then
            problema="$comando non funzionante in .venv dopo l'installazione"
            return 1
        fi
    done
    if ! "$venv/bin/pip" check >/dev/null 2>&1; then
        problema='dipendenze incoerenti nella .venv'
        return 1
    fi
    return 0
}

rimuovi_flag_nascosto_macos() {
    if ! "$python_venv" -c '
import os
import stat
import sys
from pathlib import Path

if not hasattr(os, "chflags") or not hasattr(stat, "UF_HIDDEN"):
    raise SystemExit(0)

root = Path(sys.argv[1])
targets = list(root.rglob("*.pth"))
stamp = root / ".setup-environment.sha256"
if stamp.is_file():
    targets.append(stamp)

for path in targets:
    os.chflags(path, path.stat().st_flags & ~stat.UF_HIDDEN)
' "$venv" 2>/dev/null; then
        avviso 'impossibile rimuovere il flag hidden macOS dalla .venv'
    fi
}

# I mirror dei pacchetti rispondono a intermittenza e un timeout a metà lavoro
# costa più di qualche secondo di attesa qui.
#
# `forzata` aggiunge --force-reinstall: è l'unico modo di riscrivere un
# eseguibile che pip considera già a posto. Serve solo alla riparazione.
installa() {
    local -a forzata=()
    if [ "${1:-}" = 'forzata' ]; then
        forzata=(--force-reinstall)
    fi

    local tentativo
    for tentativo in 1 2 3; do
        if "$python_venv" -m pip install --quiet --disable-pip-version-check \
            --root-user-action=ignore --timeout 60 --retries 5 \
            ${forzata[@]+"${forzata[@]}"} \
            --editable '.[dev,google]'; then
            return 0
        fi
        if [ "$tentativo" -lt 3 ]; then
            printf 'setup: installazione non riuscita (tentativo %s/3), riprovo fra %ss\n' \
                "$tentativo" "$((tentativo * 5))" >&2
            sleep "$((tentativo * 5))"
        fi
    done
    return 1
}

if [ -L "$venv" ]; then
    avviso 'rifiutata .venv simbolica: l’ambiente deve restare nel checkout'
elif [ ! -x "$python_venv" ] && ! python3 -m venv "$venv"; then
    avviso "creazione dell'ambiente virtuale non riuscita: $venv"
fi

if [ "$esito" -eq 0 ] && [ -x "$python_venv" ]; then
    rimuovi_flag_nascosto_macos
elif [ "$esito" -eq 0 ]; then
    avviso 'python non disponibile nell’ambiente virtuale'
fi

impronta_dipendenze=''
if [ "$esito" -eq 0 ] && ! impronta_dipendenze="$(
        "$python_venv" -c \
            'import hashlib, pathlib, sys; digest = hashlib.sha256(); [digest.update(pathlib.Path(path).read_bytes()) for path in sys.argv[1:]]; print(digest.hexdigest())' \
            "$radice/pyproject.toml" "$radice/scripts/setup.sh"
    )"; then
    avviso 'impossibile calcolare l’impronta delle dipendenze e della configurazione'
fi

if [ "$esito" -eq 0 ]; then
    impronta_salvata=''
    if [ -f "$stamp_dipendenze" ]; then
        IFS= read -r impronta_salvata < "$stamp_dipendenze"
    fi
    riparazione_forzata_tentata=0
    riparazione_forzata_completata=0

    if verifica && [ "$impronta_salvata" = "$impronta_dipendenze" ]; then
        printf 'setup: dipendenze e configurazione già aggiornate\n'
    elif [ "$impronta_salvata" = "$impronta_dipendenze" ]; then
        # Con dipendenze invariate, un tool guasto è una corruzione locale:
        # l'installazione ordinaria sarebbe un no-op, quindi si ripara subito.
        riparazione_forzata_tentata=1
        if installa forzata; then
            rimuovi_flag_nascosto_macos
            riparazione_forzata_completata=1
        else
            avviso 'riparazione forzata dell’ambiente non riuscita'
        fi
    elif installa; then
        rimuovi_flag_nascosto_macos
        printf 'setup: dipendenze installate da pyproject.toml in .venv (extra dev, google)\n'
    else
        avviso 'installazione delle dipendenze non riuscita: pytest e ruff potrebbero mancare'
    fi
fi

# Dopo un'installazione ordinaria, uno strumento rotto ma presente può restare
# invariato perché pip considera il requisito già soddisfatto. La reinstallazione
# forzata riscrive davvero gli eseguibili e mantiene il gate fail-closed.
if [ "$esito" -eq 0 ] && ! verifica; then
    if [ "$riparazione_forzata_tentata" -eq 0 ]; then
        riparazione_forzata_tentata=1
        if installa forzata; then
            rimuovi_flag_nascosto_macos
            riparazione_forzata_completata=1
        fi
    fi
    if ! verifica; then
        avviso "$problema"
    fi
fi

if [ "$esito" -eq 0 ] && [ "$riparazione_forzata_completata" -eq 1 ]; then
    printf 'setup: ambiente riparato con una reinstallazione forzata\n'
fi

if [ "$esito" -eq 0 ]; then
    if ! printf '%s\n' "$impronta_dipendenze" > "$stamp_dipendenze"; then
        avviso 'impossibile salvare lo stamp delle dipendenze dell’ambiente'
    else
        rimuovi_flag_nascosto_macos
    fi
fi

if [ "$esito" -eq 0 ] && ! verifica; then
    avviso "$problema"
fi

if [ "$esito" -eq 0 ]; then
    printf 'setup: ambiente pronto (%s)\n' "$("$python_venv" --version)"
fi

exit "$esito"
