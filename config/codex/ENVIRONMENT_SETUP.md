# Setup dell'ambiente Codex

Questo file descrive il setup condiviso tra Codex Cloud, Local e Worktree. Lo
script eseguibile è `scripts/setup.sh` e resta la fonte di ciò che viene
realmente installato.

Non inserire mai valori segreti in file, issue, pull request o log.

## Perché serve

Gli ambienti cloud di Codex lavorano in due fasi: la fase di **setup** dispone della rete, la fase **agente** gira isolata salvo abilitazione esplicita. Le dipendenze non installate durante il setup non sono più installabili dopo: senza questo passaggio l'agente si trova senza `pytest` né `ruff` e non può eseguire la verifica automatica obbligatoria della sezione 4 di `AGENTS.md`.

## Quando salvare la configurazione

Salvare il valore indicato sotto soltanto dopo che `scripts/setup.sh` è presente su
`main`, il branch predefinito del repository. Non salvarlo mentre lo script esiste
soltanto in una pull request: il setup partirebbe dal branch predefinito e fallirebbe
perché il file non è ancora disponibile.

## Percorso nell'interfaccia

Aprire l'ambiente Codex associato a questo repository e cercare il campo dello **script di setup**.

## Valore da inserire

```bash
bash scripts/setup.sh
```

Nient'altro. Lo script crea o riusa `.venv`, vi installa il pacchetto in
modalità editabile con gli extra `dev` e `google` dichiarati in
`pyproject.toml` — gli stessi della CI — riprova fino a tre volte se il mirror
dei pacchetti non risponde ed è idempotente.

## Codex Desktop: Local e Worktree

Per un checkout Local già esistente, eseguire una volta `bash scripts/setup.sh`
da terminale con rete prima della prima sessione nel sandbox. Per i Worktree,
creare una **Local Environment** con lo stesso script di setup e selezionarla
quando si crea l’attività: un worktree nuovo non contiene ancora `.venv`, quindi
il bootstrap automatico deve avvenire durante la creazione, prima del sandbox
di lavoro.

`.codex/hooks.json` esegue poi lo stesso setup al `SessionStart`, prima della
prima richiesta al modello. Se ambiente, dipendenze e politica di setup sono già
coerenti, lo stamp nella `.venv` attiva un fast path senza rete e senza
richiamare `pip`. L’hook resta fail-closed, ma non sostituisce il bootstrap:
un checkout pulito avviato direttamente nel sandbox senza rete deve fermarsi.
Il progetto deve essere attendibile e l’hook va approvato quando Codex lo
presenta per la prima volta o dopo una modifica.

Se l’hook è disabilitato o saltato, `AGENTS.md` rende obbligatorio lo stesso
comando come primo gate manuale. Un fallimento blocca il lavoro.

### Comportamento verificato (codex-cli 0.144.1)

Gli hook di progetto richiedono **due condizioni indipendenti**: il progetto
deve avere `trust_level = "trusted"` in `~/.codex/config.toml` e la definizione
esatta dell'hook deve essere approvata a parte con `/hooks`. Se ne manca una,
il gate non viene eseguito: in `codex exec` l’omissione può avvenire senza un
avviso osservabile, mentre la TUI presenta la revisione degli hook all’avvio.
La funzionalità `hooks` è invece attiva di default — `codex features list` la
riporta come `stable` — quindi non serve aggiungere alcuna voce `[features]`.

Quando il setup fallisce, `continue: false` ferma davvero il turno prima della
richiesta al modello. In `codex exec`, però, `stopReason` e `systemMessage` non
vengono mostrati e l'uscita resta `0`: si legge soltanto
`hook: SessionStart Stopped`. Uno script che invoca Codex non deve quindi
dedurre l'esito del gate dal codice di uscita.

## Verifica

Prima della riga finale compare uno dei seguenti esiti:

```
setup: dipendenze installate da pyproject.toml in .venv (extra dev, google)
```

oppure, se lo stamp e l’ambiente sono già coerenti:

```
setup: dipendenze e configurazione già aggiornate
```

oppure, dopo il recupero di un ambiente corrotto:

```
setup: ambiente riparato con una reinstallazione forzata
```

Ogni esito positivo deve essere seguito da:

```
setup: ambiente pronto (Python 3.x.y)
```

Se compare invece una riga `setup: ...non riuscita`, l'ambiente è incompleto: la verifica automatica obbligatoria non è eseguibile e va ripetuto il setup prima di lavorare.

## Rete e credenziali durante la fase agente

Non sono richieste dopo un bootstrap riuscito e con stamp valido. Un checkout
pulito o una modifica a `pyproject.toml` richiedono invece un nuovo bootstrap
con rete. I test non contattano Google né SMTP: usano sostituti locali, e le
credenziali reali vivono soltanto negli Environment di GitHub Actions.

L'extra `google` serve a rendere importabili le librerie client, non a raggiungere un foglio vero. Restano valide senza eccezioni le regole della sezione 1 di `AGENTS.md`: nessun invio reale e nessun accesso ai dati di produzione da un ambiente di sviluppo.

## Rapporto con Claude Code

Claude Code richiama lo stesso `scripts/setup.sh` tramite
`.claude/hooks/session-start.sh`, sia sul web sia in locale. Non esistono due
procedure di preparazione: modificare lo script vale per entrambi gli agenti.
`SessionStart` non può impedire tecnicamente l’avvio di Claude Code; in caso di
errore l’hook restituisce codice `0` e scrive diagnosi e `GATE BLOCCANTE` su
`stdout`, l’unico canale aggiunto al contesto del modello. Il blocco operativo
resta imposto da `AGENTS.md`.
