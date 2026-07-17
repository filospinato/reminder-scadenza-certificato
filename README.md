# Reminder scadenza certificato

Sistema per individuare gli arbitri con certificato medico prossimo alla scadenza e preparare promemoria individuali tramite SMTP MDaemon.

## Stato del progetto

La versione corrente **0.11.2** contiene il codice necessario ai collaudi pre-produzione, ma non attiva risorse o invii reali.

Sono implementati:

- lettura e validazione di `Operativo`, con intestazioni in riga 2;
- nome, cognome, email, scadenza e stato letti dalla medesima riga;
- finestra configurabile e chiave anti-duplicazione;
- stati `SENDING`, `SENT`, `FAILED_RETRYABLE` e `UNKNOWN_REVIEW_REQUIRED`;
- registro persistente nella tab `NOTIFICHE`;
- inizializzazione non distruttiva di uno Spreadsheet vuoto creato dall'amministratore umano;
- lettura runtime di `CONFIG` con kill switch, limiti e modalità test;
- aggiornamento aggregato di `DASHBOARD` e `ANOMALIE`;
- orchestratore completo per dry-run, test e produzione protetta;
- email testo e HTML con Message-ID e logo CID facoltativo realmente referenziato;
- trasporto SMTP con STARTTLS o SSL e fake per i test;
- autenticazione Google predisposta tramite WIF/OIDC, con blocco runtime dei file JSON `service_account` permanenti;
- workflow manuale pre-produzione disabilitato per default;
- modello di workflow schedulato conservato come esempio non attivo;
- test automatici e guide operative.

Restano da creare o valorizzare esternamente il progetto Google Cloud, i permessi, lo Spreadsheet amministrativo vuoto, gli ambienti GitHub, i parametri SMTP e i contenuti ufficiali.

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
reminder-certificati-runtime init-admin --spreadsheet-id ID
reminder-certificati-runtime check-headers
reminder-certificati-runtime run --mode DRY_RUN
reminder-certificati-runtime run --mode DRY_RUN --today 2026-07-17
```

`init-admin` non crea il file: l'amministratore umano crea uno Spreadsheet vuoto, lo condivide con il service account e fornisce l'ID. Il codice trasforma in sicurezza la singola tab vuota in `CONFIG`, `NOTIFICHE`, `DASHBOARD` e `ANOMALIE`.

`check-headers` legge soltanto la riga delle intestazioni e non legge righe dati. La CLI runtime stampa solo conteggi e stati aggregati e rimuove email, token e chiavi di notifica dagli errori.

## Flusso applicativo

L'orchestratore:

1. verifica il foglio amministrativo;
2. carica e valida `CONFIG`;
3. controlla sistema attivo e kill switch;
4. legge e valida la sorgente;
5. registra anomalie minimizzate;
6. individua tutti i candidati nella finestra;
7. consulta il registro e salta le notifiche già presenti;
8. applica il limite ai candidati ancora prenotabili;
9. compone testo e HTML;
10. applica l'override in modalità test;
11. esegue dry-run oppure SMTP;
12. aggiorna stato persistente, dashboard e heartbeat.

Il dry-run consulta il registro ma non scrive: i conteggi rappresentano quindi ciò che sarebbe davvero processabile. La modalità `TEST_SMTP` invia al massimo una sola email per esecuzione.

## Regola e registro

Un arbitro è candidato quando è operativo, ha dati validi e univoci e il certificato scade nella finestra configurata.

La chiave è:

```text
ID_ARBITRO|DATA_SCADENZA|TIPO_NOTIFICA
```

`SENT`, `SENDING` e `UNKNOWN_REVIEW_REQUIRED` bloccano altri tentativi automatici. Soltanto `FAILED_RETRYABLE` può essere riprenotato. La modalità test usa chiavi `TEST_REMINDER_*` separate e registra l'indirizzo override realmente contattato.

## Foglio amministrativo

Il file canonico è `Reminder certificati CIA Lazio — Gestione`, con le tab:

```text
CONFIG | NOTIFICHE | DASHBOARD | ANOMALIE
```

Il file nasce nell'account umano dell'amministratore. Se contiene una sola tab vuota, l'inizializzatore la rinomina, crea le altre tre e inserisce soltanto intestazioni e configurazioni sintetiche. Non sovrascrive strutture incompatibili e continua ad accettare i normali aggiornamenti runtime.

La configurazione iniziale mantiene sistema e invii disabilitati, modalità test e kill switch attivi, finestra di 30 giorni e limite di 10 messaggi per esecuzione.

## Messaggi e SMTP

Ogni comunicazione deve iniziare con:

```text
Ciao {{nome}}, ricevi questa mail...
```

Il nome proviene direttamente dalla colonna `Nome`; i nomi composti restano integri.

Il trasporto genera un messaggio individuale multipart testo/HTML, assegna un Message-ID, supporta Reply-To e logo inline facoltativo, e distingue errori ritentabili da esiti che richiedono revisione umana. Non crea copie nella Posta inviata. Nome mittente e CID sono validati contro header injection.

## Barriere di attivazione

L'inserimento dei parametri esterni non abilita automaticamente gli invii. Le modalità non dry-run richiedono più consensi separati tra foglio, comando ed environment. La produzione richiede inoltre un riconoscimento esplicito dedicato.

Il workflow manuale legge il gate dopo che l'Environment è stato dichiarato, usa una data corrente salvo override esplicito e condivide lo stesso lock del modello di produzione. I segreti SMTP esistono soltanto nello step di invio. Il workflow schedulato resta in `docs/workflows/production.yml.example` e non è eseguito da GitHub Actions.

## Google Cloud

Il collegamento usa token OIDC temporanei e un service account dedicato, senza chiavi permanenti. Prima di costruire il client Google Sheets, il runtime controlla il file indicato da `GOOGLE_APPLICATION_CREDENTIALS`: accetta soltanto una configurazione WIF `external_account` completa e rifiuta esplicitamente i file JSON `service_account`. Il contenuto delle credenziali non viene stampato né registrato.

Il service account avrà sola lettura sul file operativo e modifica sul solo foglio amministrativo già creato e condiviso dall'amministratore umano.

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
- credenziali Google permanenti bloccate anche a runtime;
- esiti incerti non ritentati automaticamente;
- nessuna schedule di produzione attiva prima dell'autorizzazione finale.

## Roadmap

La roadmap è in [`ROADMAP.md`](ROADMAP.md), lo stato sintetico in [`LATEST.md`](LATEST.md) e l'avanzamento nell'issue #1.
