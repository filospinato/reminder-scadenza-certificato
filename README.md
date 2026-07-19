# Reminder scadenza certificato

Sistema per individuare gli arbitri con certificato medico prossimo alla scadenza e inviare promemoria individuali tramite SMTP MDaemon.

## Stato del progetto

La versione **0.12.0** contiene il codice necessario ai collaudi pre-produzione, ma non attiva risorse o invii reali.

Sono implementati:

- lettura e validazione di `Operativo`, con intestazioni in riga 2;
- finestra configurabile e chiave anti-duplicazione;
- stati persistenti `SENDING`, `SENT`, `FAILED_RETRYABLE` e `UNKNOWN_REVIEW_REQUIRED`;
- registro indicizzato in memoria dopo una sola lettura per esecuzione;
- Spreadsheet amministrativo con `CONFIG`, `NOTIFICHE`, `DASHBOARD` e `ANOMALIE`;
- un solo interruttore operativo, `AUTOMAZIONE_ATTIVA`;
- un solo comando installato, `reminder-certificati`, con sottocomandi;
- preflight Google in sola lettura;
- dry-run, collaudo sintetico del registro e test SMTP all'override;
- email testo/HTML con Message-ID e logo CID facoltativo;
- autenticazione Google tramite WIF/OIDC, senza chiavi permanenti;
- workflow manuale protetto e modello schedulato non attivo;
- una sola esecuzione giornaliera prevista per la produzione;
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

Per i comandi Google installare l'extra opzionale:

```bash
python -m pip install -e ".[google]"
```

## Comando unico

Tutte le operazioni usano lo stesso eseguibile:

```bash
reminder-certificati init-admin --spreadsheet-id ID
reminder-certificati preflight
ALLOW_SYNTHETIC_REGISTRY_WRITE=true reminder-certificati registry-check --confirm-synthetic-write
reminder-certificati dry-run
reminder-certificati dry-run --today 2026-07-17
reminder-certificati test-smtp --confirm-email-delivery
reminder-certificati produzione --confirm-email-delivery
```

`init-admin` non crea il file: l'amministratore umano crea uno Spreadsheet vuoto, lo condivide con il service account e fornisce l'ID. Il codice configura le quattro tab senza sovrascrivere strutture già popolate.

`preflight` verifica che `Operativo` e il foglio amministrativo siano file distinti, controlla tab e intestazioni e non legge righe operative, non scrive celle e non usa SMTP. Sostituisce il precedente comando separato `check-headers`.

`registry-check` richiede sia il flag CLI sia la variabile ambiente dedicata. Scrive una sola riga sintetica `.invalid`, la rilegge e la aggiorna da `SENDING` a `SENT`.

## Flusso applicativo

1. verifica leggera di tab e intestazioni amministrative;
2. carica e valida `CONFIG`;
3. controlla `AUTOMAZIONE_ATTIVA`;
4. legge e valida `Operativo`;
5. registra soltanto anomalie nuove;
6. individua i candidati nella finestra;
7. carica una volta il registro e salta le notifiche già presenti;
8. applica il limite ai candidati ancora prenotabili;
9. compone testo e HTML;
10. esegue dry-run oppure SMTP;
11. aggiorna stato persistente, dashboard e heartbeat.

Il dry-run consulta il registro ma non scrive e non richiede configurazione SMTP o destinatario override. Il test SMTP invia al massimo una sola email per esecuzione e usa sempre l'override.

## CONFIG

La tab contiene soltanto le impostazioni usate dal runtime:

- `AUTOMAZIONE_ATTIVA`: unico interruttore ordinario e di emergenza;
- `INVII_REALI_ABILITATI`: seconda barriera per il go-live;
- `GIORNI_PREAVVISO`;
- `LIMITE_INVII_PER_ESECUZIONE`;
- `DESTINATARIO_OVERRIDE`;
- `OGGETTO_EMAIL`;
- `CORPO_EMAIL`;
- `FIRMA_TESTO`.

Per arrestare immediatamente il sistema impostare `AUTOMAZIONE_ATTIVA=false`. Il controllo avviene prima della lettura completa di `Operativo` e prima di qualsiasi invio.

La modalità non è duplicata nella CONFIG: è determinata dal sottocomando `dry-run`, `test-smtp` o `produzione`.

Il corpo della mail è liberamente modificabile e può usare soltanto i placeholder autorizzati. Il codice aggiunge automaticamente `Ciao {{nome}},`.

## Registro

La chiave è:

```text
ID_ARBITRO|DATA_SCADENZA|TIPO_NOTIFICA
```

`SENT`, `SENDING` e `UNKNOWN_REVIEW_REQUIRED` bloccano altri tentativi automatici. Soltanto `FAILED_RETRYABLE` può essere riprenotato. La modalità test usa chiavi `TEST_REMINDER_*` separate.

## Barriere di produzione

Gli invii reali richiedono contemporaneamente:

- Environment `production` protetto;
- `PRODUCTION_ENABLED=true`;
- `AUTOMAZIONE_ATTIVA=true`;
- `INVII_REALI_ABILITATI=true`;
- `ALLOW_EMAIL_DELIVERY=true` e flag CLI nello step SMTP.

I segreti SMTP sono disponibili soltanto allo step di invio. Il workflow schedulato resta in `docs/workflows/production.yml.example` e non è ancora eseguito da GitHub Actions.

## Google Cloud

Il collegamento usa token OIDC temporanei e un service account dedicato. Il service account avrà sola lettura sul file operativo e modifica sul solo foglio amministrativo già creato dall'amministratore umano.

## Guide

- [`docs/OPERATIONS.md`](docs/OPERATIONS.md)
- [`docs/EMERGENCY.md`](docs/EMERGENCY.md)
- [`docs/HANDOFF.md`](docs/HANDOFF.md)
- [`docs/TEST_PLAN.md`](docs/TEST_PLAN.md)
- [`docs/DEPLOYMENT_CHECKLIST.md`](docs/DEPLOYMENT_CHECKLIST.md)
- [`docs/PREFLIGHT_DIAGNOSTICA.md`](docs/PREFLIGHT_DIAGNOSTICA.md)

## Sicurezza

- nessun dato personale o parametro riservato nel repository;
- `Operativo` sempre in sola lettura;
- output dei workflow aggregati;
- credenziali Google permanenti bloccate a runtime;
- collaudo del registro limitato a una riga sintetica;
- esiti incerti non ritentati automaticamente;
- nessuna schedule di produzione attiva prima dell'autorizzazione finale.
