# Reminder scadenza certificato

Sistema per individuare gli arbitri con certificato medico prossimo alla scadenza e inviare promemoria individuali tramite SMTP MDaemon.

## Stato del progetto

La versione di pacchetto corrente **0.11.5** contiene il codice necessario ai collaudi pre-produzione, ma non attiva risorse o invii reali.

Sono implementati:

- lettura e validazione di `Operativo`, con intestazioni in riga 2;
- nome, cognome, email, scadenza e stato letti dalla medesima riga;
- finestra configurabile e chiave anti-duplicazione;
- stati `SENDING`, `SENT`, `FAILED_RETRYABLE` e `UNKNOWN_REVIEW_REQUIRED`;
- registro persistente indicizzato in memoria dopo una sola lettura per esecuzione;
- inizializzazione non distruttiva di uno Spreadsheet vuoto creato dall'amministratore umano;
- `CONFIG` limitata ai campi realmente usati, con kill switch, limiti e modalità test;
- aggiornamento aggregato di `DASHBOARD` e anomalie persistenti deduplicate;
- orchestratore completo per dry-run, test e produzione protetta;
- comando protetto per collaudare il registro con una sola riga interamente sintetica;
- preflight Google in sola lettura per verificare file distinti, tab e sole intestazioni necessarie;
- email testo e HTML con Message-ID e logo CID facoltativo;
- trasporto SMTP con STARTTLS o SSL e fake per i test;
- autenticazione Google tramite WIF/OIDC, con blocco delle chiavi JSON permanenti;
- workflow manuale pre-produzione disabilitato per default;
- modello di workflow schedulato conservato come esempio non attivo;
- test automatici e guide operative.

Restano da creare o valorizzare esternamente il progetto Google Cloud, i permessi, lo Spreadsheet amministrativo vuoto, gli Environment GitHub, i parametri SMTP e i contenuti ufficiali.

## Avvio locale

Richiede Python 3.11 o successivo.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
pytest
```

Il vecchio comando `reminder-certificati` è mantenuto soltanto come avviso di compatibilità e non elabora né stampa record. L'interfaccia applicativa è `reminder-certificati-runtime`.

Per i comandi Google installare l'extra opzionale:

```bash
python -m pip install -e ".[google]"
```

Comandi pre-produzione:

```bash
reminder-certificati-runtime init-admin --spreadsheet-id ID
reminder-certificati-google-preflight
reminder-certificati-runtime check-headers
ALLOW_SYNTHETIC_REGISTRY_WRITE=true reminder-certificati-registry-check --confirm-synthetic-write
reminder-certificati-runtime run --mode DRY_RUN
reminder-certificati-runtime run --mode DRY_RUN --today 2026-07-17
```

`init-admin` non crea il file: l'amministratore umano crea uno Spreadsheet vuoto, lo condivide con il service account e fornisce l'ID. Il codice trasforma la singola tab vuota in `CONFIG`, `NOTIFICHE`, `DASHBOARD` e `ANOMALIE`.

`reminder-certificati-google-preflight` verifica che `Operativo` e il foglio amministrativo siano file distinti, controlla la presenza delle quattro tab e legge soltanto le righe delle intestazioni. L'ordine visuale delle tab non è significativo. In `Operativo` sono bloccanti soltanto le sei colonne realmente usate dal reminder. Il preflight non legge righe operative, non scrive celle e non usa SMTP.

I codici e le azioni del preflight sono documentati in [`docs/PREFLIGHT_DIAGNOSTICA.md`](docs/PREFLIGHT_DIAGNOSTICA.md).

`check-headers` legge soltanto la riga delle intestazioni e usa la stessa lista canonica del runtime. La CLI stampa solo conteggi e stati aggregati e rimuove email, token e chiavi di notifica dagli errori.

`reminder-certificati-registry-check` richiede sia il flag CLI sia la variabile ambiente dedicata. Scrive una sola riga sintetica `.invalid`, la rilegge e la aggiorna da `SENDING` a `SENT`. Non legge `Operativo` e non invia email.

## Flusso applicativo

L'orchestratore:

1. verifica presenza e intestazioni del foglio amministrativo senza leggere interamente registro e anomalie;
2. carica e valida `CONFIG`;
3. controlla sistema attivo e kill switch;
4. legge e valida la sorgente;
5. registra soltanto anomalie nuove;
6. individua i candidati nella finestra;
7. carica una volta il registro e salta le notifiche già presenti;
8. applica il limite ai candidati ancora prenotabili;
9. compone testo e HTML;
10. applica l'override nella sola modalità test;
11. esegue dry-run oppure SMTP;
12. aggiorna stato persistente, dashboard e heartbeat.

Il dry-run consulta il registro ma non scrive e non richiede configurazione SMTP o destinatario override. La modalità `TEST_SMTP` invia al massimo una sola email per esecuzione.

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

L'inizializzatore le crea in questo ordine, ma dopo la creazione possono essere riordinate senza bloccare il programma. Il file nasce nell'account umano dell'amministratore. Non vengono sovrascritte strutture incompatibili.

La configurazione iniziale mantiene sistema e invii disabilitati, modalità test e kill switch attivi, finestra di 30 giorni e limite di 10 messaggi. Per un dry-run controllato si impostano `SISTEMA_ATTIVO=true` e `KILL_SWITCH=false`, lasciando `INVII_REALI_ABILITATI=false`. L'override è richiesto soltanto prima del test SMTP.

## Messaggi e SMTP

Ogni comunicazione inizia nel codice con:

```text
Ciao {{nome}}, ricevi questa mail...
```

Il nome proviene direttamente dalla colonna `Nome`; i nomi composti restano integri. Il saluto non è una configurazione duplicata nel foglio.

Il trasporto genera un messaggio individuale multipart testo/HTML, assegna un Message-ID, supporta Reply-To e logo inline facoltativo, e distingue errori ritentabili da esiti che richiedono revisione umana. Non crea copie nella Posta inviata.

## Barriere di attivazione

L'inserimento dei parametri esterni non abilita automaticamente gli invii. La produzione richiede contemporaneamente:

- Environment `production` protetto;
- `PRODUCTION_ENABLED=true`;
- `SISTEMA_ATTIVO=true`;
- `INVII_REALI_ABILITATI=true`;
- `MODALITA_TEST=false`;
- `KILL_SWITCH=false`;
- `ALLOW_EMAIL_DELIVERY=true` e flag CLI nello step SMTP.

Non sono presenti acknowledgement statici duplicati. I segreti SMTP esistono soltanto nello step di invio. Il workflow schedulato resta in `docs/workflows/production.yml.example` e non è eseguito da GitHub Actions.

## Google Cloud

Il collegamento usa token OIDC temporanei e un service account dedicato, senza chiavi permanenti. Il runtime accetta soltanto credenziali WIF `external_account` e rifiuta i file JSON `service_account`.

Il service account avrà sola lettura sul file operativo e modifica sul solo foglio amministrativo già creato e condiviso dall'amministratore umano.

## Guide

- [`docs/OPERATIONS.md`](docs/OPERATIONS.md)
- [`docs/EMERGENCY.md`](docs/EMERGENCY.md)
- [`docs/HANDOFF.md`](docs/HANDOFF.md)
- [`docs/TEST_PLAN.md`](docs/TEST_PLAN.md)
- [`docs/DEPLOYMENT_CHECKLIST.md`](docs/DEPLOYMENT_CHECKLIST.md)
- [`docs/PREFLIGHT_DIAGNOSTICA.md`](docs/PREFLIGHT_DIAGNOSTICA.md)

## Sicurezza

- nessun dato personale o parametro riservato nel repository;
- `Operativo` sempre di sola lettura;
- output dei workflow aggregati;
- chiavi duplicate o schema inatteso bloccano l'esecuzione;
- credenziali Google permanenti bloccate a runtime;
- preflight limitato a metadati e intestazioni, senza scritture;
- collaudo del registro limitato a una riga sintetica e protetto da doppio consenso;
- esiti incerti non ritentati automaticamente;
- nessuna schedule di produzione attiva prima dell'autorizzazione finale.

## Roadmap

La roadmap è in [`ROADMAP.md`](ROADMAP.md), lo stato sintetico in [`LATEST.md`](LATEST.md) e l'avanzamento nell'issue #1.
