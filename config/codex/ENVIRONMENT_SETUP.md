# Setup dell'ambiente Codex

Questo file contiene esclusivamente le istruzioni da applicare nell'interfaccia di Codex. Lo script eseguibile è `scripts/setup.sh` e resta la fonte di ciò che viene realmente installato.

Non inserire mai valori segreti in file, issue, pull request o log.

## Perché serve

Gli ambienti cloud di Codex lavorano in due fasi: la fase di **setup** dispone della rete, la fase **agente** gira isolata salvo abilitazione esplicita. Le dipendenze non installate durante il setup non sono più installabili dopo: senza questo passaggio l'agente si trova senza `pytest` né `ruff` e non può eseguire la verifica automatica obbligatoria della sezione 4 di `AGENTS.md`.

## Percorso nell'interfaccia

Aprire l'ambiente Codex associato a questo repository e cercare il campo dello **script di setup**.

## Valore da inserire

```bash
bash scripts/setup.sh
```

Nient'altro. Lo script installa il pacchetto in modalità editabile con gli extra `dev` e `google` dichiarati in `pyproject.toml` — gli stessi della CI — riprova fino a tre volte se il mirror dei pacchetti non risponde ed è idempotente.

## Verifica

Al termine del setup l'output deve contenere:

```
setup: dipendenze installate da pyproject.toml (extra dev, google)
setup: ambiente pronto (Python 3.x.y)
```

Se compare invece una riga `setup: ...non riuscita`, l'ambiente è incompleto: la verifica automatica obbligatoria non è eseguibile e va ripetuto il setup prima di lavorare.

## Rete e credenziali durante la fase agente

Non sono richieste. I test non contattano Google né SMTP: usano sostituti locali, e le credenziali reali vivono soltanto negli Environment di GitHub Actions.

L'extra `google` serve a rendere importabili le librerie client, non a raggiungere un foglio vero. Restano valide senza eccezioni le regole della sezione 1 di `AGENTS.md`: nessun invio reale e nessun accesso ai dati di produzione da un ambiente di sviluppo.

## Rapporto con Claude Code

Claude Code richiama lo stesso `scripts/setup.sh` tramite `.claude/hooks/session-start.sh`. Non esistono due procedure di preparazione: modificare lo script vale per entrambi gli agenti.
