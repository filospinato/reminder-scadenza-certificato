# Reminder scadenza certificato

Sistema per individuare gli arbitri con certificato medico prossimo alla scadenza e inviare promemoria individuali tramite SMTP MDaemon.

## Stato del progetto

La versione **0.13.3** interpreta correttamente la convenzione reale della colonna `Fa attività quest'anno`: cella vuota significa che la persona fa attività; una annotazione non affermativa significa che non fa attività. Benemeriti, osservatori e fuori quadro sono esclusi dai reminder, senza attivare risorse, schedule o invii reali.

Sono implementati:

- lettura e validazione di `Operativo`, con intestazioni in riga 2;
- lettura delle sole otto colonne necessarie tramite `batchGet`, incluse `Qualifica` e `Abilitazione`;
- interpretazione di `Fa attività quest'anno`: vuoto = attivo, annotazione non affermativa = inattivo;
- esclusione esplicita di benemeriti, osservatori e fuori quadro dai candidati al reminder;
- chiave anti-duplicazione stabile anche se cambia `GIORNI_PREAVVISO`;
- stati `SENDING`, `SENT`, `FAILED_RETRYABLE`, `FAILED_PERMANENT` e `UNKNOWN_REVIEW_REQUIRED`;
- massimo tre tentativi automatici per gli errori ritentabili;
- registro persistente minimizzato, senza nome, cognome o email;
- schema amministrativo versionato con `SCHEMA_VERSION=2`;
- migrazione amministrativa con anteprima, conferma e backup;
- preflight che valida tab, intestazioni e contenuto della CONFIG;
- un solo interruttore operativo, `AUTOMAZIONE_ATTIVA`;
- arresto senza lettura completa di `Operativo` e senza inizializzazione SMTP;
- output aggregato e codici di uscita non-zero per attenzione o revisione;
- workflow manuale protetto e modello schedulato non attivo.

## Avvio locale

Richiede Python 3.11 o successivo.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
pytest
```

Per i comandi Google:

```bash
python -m pip install -e ".[google]"
```

## Comando unico

```bash
reminder-certificati init-admin --spreadsheet-id ID
reminder-certificati migrate-admin --spreadsheet-id ID
reminder-certificati migrate-admin --spreadsheet-id ID --apply --confirm-migration
reminder-certificati preflight
ALLOW_SYNTHETIC_REGISTRY_WRITE=true reminder-certificati registry-check --confirm-synthetic-write
reminder-certificati review-registry
reminder-certificati dry-run
reminder-certificati test-smtp --confirm-email-delivery
reminder-certificati produzione --confirm-email-delivery
```

`migrate-admin` opera in anteprima se non riceve `--apply`. L'applicazione richiede anche `--confirm-migration`, salva prima un backup JSON e lascia sempre `AUTOMAZIONE_ATTIVA=false` e `INVII_REALI_ABILITATI=false` quando effettua una migrazione.

`preflight` controlla anche chiavi, valori funzionali e versione della CONFIG. Non legge righe anagrafiche di `Operativo`, non scrive e non usa SMTP.

`review-registry` restituisce solo conteggi aggregati di righe `SENDING` vecchie, retry esauriti, errori permanenti ed esiti incerti.

## CONFIG

Le chiavi funzionali sono:

- `SCHEMA_VERSION`, gestita dal programma;
- `AUTOMAZIONE_ATTIVA`;
- `INVII_REALI_ABILITATI`;
- `GIORNI_PREAVVISO`;
- `LIMITE_INVII_PER_ESECUZIONE`;
- `DESTINATARIO_OVERRIDE`;
- `OGGETTO_EMAIL`;
- `CORPO_EMAIL`;
- `FIRMA_TESTO`.

Con `AUTOMAZIONE_ATTIVA=false`, il comando termina come `DISATTIVATO` prima di leggere le righe operative e prima di validare o costruire SMTP.

## Registro

La chiave è:

```text
ID_ARBITRO|DATA_SCADENZA|CERTIFICATO_SCADENZA_V1
```

Il registro conserva soltanto identificativo, scadenza, tipo, stato, tentativi, timestamp, Message-ID, versione ed errore sintetico. Nome, cognome ed email non vengono persistiti.

- `FAILED_RETRYABLE` è riprenotabile fino a tre tentativi complessivi;
- `FAILED_PERMANENT` non viene ritentato;
- `UNKNOWN_REVIEW_REQUIRED` richiede verifica umana;
- `SENDING` vecchi sono segnalati da `review-registry`.

Il test SMTP mantiene il comportamento attuale richiesto: usa l'override come destinatario e invia al massimo un messaggio.

## Codici di uscita

- `0`: esecuzione regolare o sistema disattivato;
- `2`: errore operativo o registro da revisionare;
- `3`: stato `ATTENZIONE`;
- `4`: stato `REVISIONE_RICHIESTA`.

## Barriere di produzione

Gli invii reali richiedono contemporaneamente Environment protetto, `PRODUCTION_ENABLED=true`, `AUTOMAZIONE_ATTIVA=true`, `INVII_REALI_ABILITATI=true`, `ALLOW_EMAIL_DELIVERY=true` e conferma CLI. Il workflow di produzione resta soltanto in `docs/workflows/production.yml.example`.

## Guide

- [`docs/OPERATIONS.md`](docs/OPERATIONS.md)
- [`docs/EMERGENCY.md`](docs/EMERGENCY.md)
- [`docs/SCHEMA_FOGLI.md`](docs/SCHEMA_FOGLI.md)
- [`docs/DEPLOYMENT_CHECKLIST.md`](docs/DEPLOYMENT_CHECKLIST.md)
- [`docs/PREFLIGHT_DIAGNOSTICA.md`](docs/PREFLIGHT_DIAGNOSTICA.md)
