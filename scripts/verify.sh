#!/usr/bin/env bash
# Unico punto pubblico di verifica del progetto.
#
# È il comando che eseguono allo stesso modo una persona, un agente e la CI:
# l'elenco dei controlli vive qui e in nessun altro posto. Un controllo scritto
# soltanto in un workflow non è riproducibile in locale; uno scritto soltanto in
# `AGENTS.md` o nella descrizione di una pull request non è eseguibile affatto.
#
# Usa esclusivamente l'ambiente che `scripts/setup.sh` ha preparato: non
# installa niente, non usa la rete, non scrive file tracciati e non tocca
# risorse live. I collaudi sui due Spreadsheet Drive restano fuori da qui,
# perché richiedono risorse reali: vedi la §5 di `AGENTS.md`.

set -uo pipefail

radice="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)" || exit 1
cd "$radice" || exit 1

venv="$radice/.venv"
esito=0

fallito() {
    printf 'verify: FALLITO — %s\n' "$1" >&2
    esito=1
}

# Questo preflight resta prima di ogni altro controllo: senza gli strumenti
# della `.venv` i controlli successivi non sarebbero più severi, sarebbero
# soltanto assenti, e un'assenza non deve mai leggersi come un esito verde.
for comando in python pip pytest ruff; do
    if [ ! -x "$venv/bin/$comando" ]; then
        fallito "ambiente non pronto ($comando non disponibile); esegui: bash scripts/setup.sh"
    fi
done

if [ "$esito" -ne 0 ]; then
    exit "$esito"
fi

# `scripts/setup.sh` fotografa l'albero prima di poter toccare qualsiasi cosa e
# lascia la fotografia dentro `.git/`, che sta fuori dal working tree. Scattarla
# qui invece che là mancherebbe tutto ciò che ha fatto il setup. Si confronta il
# contenuto e non i soli codici di stato, perché `git status --porcelain` non
# distingue un file già modificato dallo stesso file modificato di nuovo.
# Risolto come lo risolve il setup, così un worktree collegato trova la
# fotografia che il setup ha registrato lì.
baseline_setup="$(git rev-parse --git-path reminder-tree-baseline 2>/dev/null)"
[ -n "$baseline_setup" ] || baseline_setup="$radice/.git/reminder-tree-baseline"

temporanea="$(mktemp -d "${TMPDIR:-/tmp}/reminder-verify.XXXXXX")" || {
    fallito 'impossibile creare la directory di lavoro temporanea'
    exit "$esito"
}
# La fotografia si consuma quando viene letta, ma
# `tests/test_agent_environment_setup.py` esegue `scripts/setup.sh` e ne lascia
# una nuova a metà corsa. Se restasse lì diventerebbe la baseline della
# prossima esecuzione e la farebbe fallire. Si cancella sempre all'uscita.
trap 'rm -rf "$temporanea"; rm -f "$baseline_setup"' EXIT

stato_albero() {
    git status --porcelain=v1 --untracked-files=all &&
        printf -- '--- contenuto tracciato ---\n' &&
        git diff --binary --no-ext-diff HEAD
}

baseline="$temporanea/albero-prima"
ambito='il setup e la verifica'
if [ -f "$baseline_setup" ]; then
    mv "$baseline_setup" "$baseline" || {
        fallito 'impossibile leggere la fotografia del checkout lasciata dal setup'
        exit "$esito"
    }
else
    ambito='la verifica'
    printf 'verify: nessuna fotografia dal setup; copro soltanto la verifica\n'
    if ! stato_albero > "$baseline" 2>/dev/null; then
        fallito 'impossibile registrare lo stato iniziale del checkout'
        exit "$esito"
    fi
fi

printf '\n== Ruff ==\n'
if "$venv/bin/ruff" check .; then
    printf 'verify: Ruff superato\n'
else
    fallito 'Ruff'
fi

printf '\n== Coerenza delle dipendenze ==\n'
if "$venv/bin/python" -m pip check; then
    printf 'verify: pip check superato\n'
else
    fallito 'pip check'
fi

printf '\n== Test ==\n'
if "$venv/bin/pytest"; then
    printf 'verify: pytest superato\n'
else
    fallito 'pytest'
fi

printf '\n== Whitespace e marcatori di conflitto ==\n'
albero_vuoto="$(git hash-object -t tree /dev/null 2>/dev/null)"
if [ -n "$albero_vuoto" ] \
        && git diff --check "$albero_vuoto" HEAD \
        && git diff --check \
        && git diff --cached --check; then
    printf 'verify: nessun errore di whitespace nel contenuto tracciato\n'
else
    fallito 'git diff --check'
fi

printf '\n== Checkout invariato ==\n'
albero_dopo="$temporanea/albero-dopo"
if ! stato_albero > "$albero_dopo" 2>/dev/null; then
    fallito 'impossibile rileggere lo stato del checkout'
elif diff -u "$baseline" "$albero_dopo" >&2; then
    printf 'verify: %s non hanno modificato il checkout\n' "$ambito"
else
    fallito 'il checkout è cambiato durante il setup o la verifica'
fi

printf '\n'
if [ "$esito" -eq 0 ]; then
    printf 'verify: tutti i controlli dichiarati sono superati\n'
else
    printf 'verify: uno o più controlli sono falliti\n' >&2
fi

exit "$esito"
