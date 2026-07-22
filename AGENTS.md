# Regole operative del repository

Questo file è l’unica fonte delle regole per agenti e persone che modificano il repository. Le istruzioni sono ordinate per priorità: in caso di conflitto prevale la sezione precedente.

## 1. Sicurezza e invarianti non negoziabili

- Non inserire nel repository, nei diff, nei log, nelle issue o nelle pull request credenziali, token, password, chiavi private, contenuti completi dei fogli o dati personali degli arbitri.
- Il foglio `Operativo` è sempre in sola lettura. Il sistema può scrivere soltanto nel foglio amministrativo previsto dal contratto applicativo.
- L’accesso Google deve usare WIF/OIDC e credenziali temporanee `external_account`. Le chiavi JSON permanenti di service account sono vietate.
- Nessuna modifica al codice o alla documentazione deve attivare autonomamente invii reali, schedule produttive, nuovi permessi cloud o altre risorse live.
- Gli invii reali richiedono un’autorizzazione esplicita separata e l’interruttore esterno `INVIO_AUTOMATICO_ATTIVO=true`.
- Un esito SMTP incerto non deve essere ritentato automaticamente. Evitare duplicati ha priorità rispetto al reinvio.
- La chiave anti-duplicazione, la macchina a stati del registro, il limite massimo interno e la separazione tra test e produzione non possono essere indeboliti senza una decisione architetturale esplicita e test dedicati.

## 2. Fonti di verità

Leggere nell’ordine:

1. `README.md`: scopo, architettura e stato semantico di alto livello;
2. `AGENTS.md`: regole operative per le modifiche;
3. `CHANGELOG.md`: delta funzionali delle release;
4. `pyproject.toml`: versione, dipendenze, compatibilità Python ed entry point;
5. `config/github/environment-contract.json`: nomi canonici di Variables, Secrets ed Environment;
6. `.github/workflows/`: trigger, branch, limiti, permessi e concorrenza effettivamente eseguiti;
7. `releases/vX.Y.Z/`: documentazione immutabile della release interessata;
8. codice e test come contratto eseguibile.

Le GitHub Issues e i milestone contengono esclusivamente lavoro aperto. Non creare `LATEST.md`, `CURRENT_STATE.md`, `CURRENT_STATE.json`, `ROADMAP.md`, `PROJECT_RULES.md`, `PROJECT_INSTRUCTION.md`, handoff temporanei o altre fonti concorrenti.

Un file di stato separato è ammesso soltanto se viene letto o aggiornato automaticamente dal sistema e costituisce davvero un input operativo. Non va creato per ricopiare valori già autoritativi in package, workflow, configurazioni o GitHub.

## 3. Metodo di modifica

- Usare `main` come baseline canonica, ma non modificarla direttamente.
- Verificare prima branch, pull request aperte, issue rilevanti e stato della CI.
- Lavorare su un branch `agent/<descrizione>` dedicato a un intervento coerente.
- Evitare refactoring estranei, dipendenze non necessarie, duplicazioni e overengineering.
- Aggiornare nella stessa modifica codice, test, documentazione e contratti di configurazione quando sono realmente coinvolti.
- Non copiare nei documenti di release dati mutevoli già autoritativi altrove, salvo quelli necessari a riprodurre quella specifica release.
- I testi destinati alla configurazione manuale di agenti esterni devono stare sotto `config/<prodotto>/`, mai in questo file.

## 4. Verifica automatica obbligatoria

Eseguire almeno:

```bash
python -m pip install -e ".[dev,google]"
ruff check .
python -m compileall -q src
python -m pip check
pytest
```

I test devono coprire il comportamento modificato e, quando applicabile, proteggere:

- validazione e provenienza dei dati dalla stessa riga;
- esclusione delle categorie non soggette al certificato;
- schema amministrativo e migrazioni conservative;
- deduplicazione e transizioni del registro;
- composizione testo/HTML e sicurezza MIME;
- classificazione degli esiti SMTP;
- isolamento dei Secrets negli step di invio;
- coerenza tra workflow e contratto JSON dell’Environment;
- struttura documentale SSoT.

## 5. Collaudi esterni

Ogni modifica al codice deve essere collaudata anche sui due Spreadsheet Drive collegati prima di essere dichiarata pronta per la produzione. Con `INVIO_AUTOMATICO_ATTIVO=false` eseguire:

1. `setup-preview`, verificando che non proponga modifiche inattese;
2. `check`, verificando preflight, dati e registro senza scritture operative e senza SMTP;
3. `registry-check` anche sul foglio reale per modifiche a schema, migrazioni, adapter o persistenza.

`setup-apply` si usa soltanto dopo revisione dell’anteprima e con backup. `test-smtp` richiede autorizzazione distinta e non sostituisce i controlli Drive senza invio.

Quando le risorse live non sono disponibili, dichiarare chiaramente il limite: la modifica può essere corretta in CI, ma non è verificata per la produzione.

## 6. Versioni e artefatti di release

- La versione applicativa vive in `pyproject.toml` e deve avere una voce nel `CHANGELOG.md`.
- Ogni release documentata deve avere una directory `releases/vX.Y.Z/` coerente con la versione.
- I documenti sotto `releases/` sono fotografie immutabili: non vanno riscritti per descrivere release successive.
- `CHANGELOG.md` contiene solo delta funzionali; evidenze di collaudo, cronache di PR e log di run appartengono alla PR o al file `VALIDATION.md` della release.
- I valori esatti devono vivere nella fonte che li usa: package, workflow, contratto di configurazione, codice o piattaforma GitHub.

## 7. Pull request e revisione finale

- Aprire una pull request in bozza verso `main`.
- Dopo la pubblicazione, revisionare immediatamente il diff effettivo su GitHub: base corretta, file modificati, test, regressioni, riferimenti residui, segreti e coerenza complessiva.
- Correggere eventuali problemi sullo stesso branch e ripetere la revisione.
- Non iniziare modifiche dipendenti finché la pull request corrente non è verificata e pronta.
- Non effettuare il merge finale né attivare risorse live senza autorizzazione esplicita dell’utente.
