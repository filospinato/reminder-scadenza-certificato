# Reminder scadenza certificato

Sistema per individuare gli arbitri con certificato medico prossimo alla scadenza e preparare promemoria individuali tramite SMTP MDaemon.

## Stato del progetto

La versione corrente **0.11.0** contiene il codice necessario ai collaudi pre-produzione, ma non attiva risorse o invii reali.

Sono implementati:

- lettura e validazione di `Operativo`, con intestazioni in riga 2;
- nome, cognome, email, scadenza e stato letti dalla medesima riga;
- finestra configurabile e chiave anti-duplicazione;
- stati `SENDING`, `SENT`, `FAILED_RETRYABLE` e `UNKNOWN_REVIEW_REQUIRED`;
- registro persistente nella tab `NOTIFICHE`;
- inizializzazione e verifica non distruttiva del foglio amministrativo;
- lettura runtime di `CONFIG` con kill switch, limiti e modalità test;
- aggiornamento aggregato di `DASHBOARD` e `ANOMALIE`;
- orchestratore completo per dry-run, test e produzione protetta;
- email testo e HTML con Message-ID e logo CID facoltativo;
- trasporto SMTP con STARTTLS o SSL e fake per i test;
- autenticazione Google predisposta tramite WIF/OIDC;
- workflow manuale pre-produzione disabilitato per default;
- modello di workflow schedulato conservato come esempio non attivo;
- test automatici e guide operative.

Restano da creare o valorizzare esternamente il progetto Google Cloud, i permessi, il foglio amministrativo reale, gli ambienti GitHub, i parametri SMTP e i contenuti ufficiali.

## Avvio locale

Richiede Python 3.11 o successivo.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
pytest
reminder-certificati --today 2026-07-17 --days 30
```

Il comando storico usa soltanto i dati anonimi in `examples/arbitri.json`.

Per i comandi Google installare l'extra opzionale:

```bash
python -m pip install -e ".[google]"
```

Comandi pre-produzione:

```bash
reminder-certificati-runtime init-admin
reminder-certificati-runtime init-admin --spreadsheet-id ID
reminder-certificati-runtime check-headers
reminder-certificati-runtime run --mode DRY_RUN --today 2026-07-17
```

`check-headers` legge soltanto la riga delle intestazioni e non legge righe dati. La CLI runtime stampa solo conteggi e stati aggregati.

## Flusso applicativo

L'orchestratore:

1. verifica il foglio amministrativo;
2. carica e valida `CONFIG`;
3. controlla sistema attivo e kill switch;
4. legge e valida la sorgente;
5. registra anomalie minimizzate;
6. seleziona i candidati entro finestra e limite;
7. verifica il registro e prenota `SENDING`;
8. compone testo e HTML;
9. applica l'override in modalità test;
10. esegue dry-run oppure SMTP;
11. aggiorna lo stato persistente;
12. aggiorna dashboard e heartbeat.

## Regola e registro

Un arbitro è candidato quando è operativo, ha dati validi e univoci e il certificato scade nella finestra configurata.

La chiave è:

```text
ID_ARBITRO|DATA_SCADENZA|TIPO_NOTIFICA
```

`SENT`, `SENDING` e `UNKNOWN_REVIEW_REQUIRED` bloccano altri tentativi automatici. Soltanto `FAILED_RETRYABLE` può essere riprenotato. La modalità test usa chiavi `TEST_REMINDER_*` separate.

## Foglio amministrativo

Il file canonico è `Reminder certificati CIA Lazio — Gestione`, con le tab:

```text
CONFIG | NOTIFICHE | DASHBOARD | ANOMALIE
```

L'inizializzatore crea le tab vuote o verifica un file esistente. Non sovrascrive strutture incompatibili e continua ad accettare i normali aggiornamenti runtime.

La configurazione iniziale mantiene sistema e invii disabilitati, modalità test e kill switch attivi, finestra di 30 giorni e limite di 10 messaggi per esecuzione.

Il contratto completo è in [`docs/SCHEMA_FOGLI.md`](docs/SCHEMA_FOGLI.md).

## Messaggi e SMTP

Ogni comunicazione deve iniziare con:

```text
Ciao {{nome}}, ricevi questa mail...
```

Il nome proviene direttamente dalla colonna `Nome`; i nomi composti restano integri.

Il trasporto genera un messaggio individuale multipart testo/HTML, assegna un Message-ID, supporta Reply-To e logo inline facoltativo, e distingue errori ritentabili da esiti che richiedono revisione umana. Non crea copie nella Posta inviata.

## Barriere di attivazione

L'inserimento dei parametri esterni non abilita automaticamente gli invii. Le modalità non dry-run richiedono più consensi separati tra foglio, comando ed environment. La produzione richiede inoltre un riconoscimento esplicito dedicato.

Il workflow manuale non accede alle risorse finché l'environment di pre-produzione non viene abilitato. Il workflow schedulato resta in `docs/workflows/production.yml.example` e non è eseguito da GitHub Actions.

## Google Cloud

Il collegamento userà token OIDC temporanei e un service account dedicato, senza chiavi permanenti. Il service account avrà sola lettura sul file operativo e modifica sul solo foglio amministrativo.

Il runbook è in [`docs/AUTENTICAZIONE_GOOGLE.md`](docs/AUTENTICAZIONE_GOOGLE.md).

## Guide

- [`docs/OPERATIONS.md`](docs/OPERATIONS.md)
- [`docs/EMERGENCY.md`](docs/EMERGENCY.md)
- [`docs/HANDOFF.md`](docs/HANDOFF.md)
- [`docs/TEST_PLAN.md`](docs/TEST_PLAN.md)
- [`docs/DEPLOYMENT_CHECKLIST.md`](docs/DEPLOYMENT_CHECKLIST.md)

## Sicurezza

- nessun dato personale o parametro riservato nel repository;
- `Operativo` sempre di sola lettura;
- output dei workflow aggregati;
- chiavi duplicate o schema inatteso bloccano l'esecuzione;
- esiti incerti non ritentati automaticamente;
- nessuna schedule di produzione attiva prima dell'autorizzazione finale.

## Roadmap

La roadmap è in [`ROADMAP.md`](ROADMAP.md), lo stato sintetico in [`LATEST.md`](LATEST.md) e l'avanzamento nell'issue #1.
