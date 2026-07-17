# Stato corrente

**Versione:** 0.11.0  
**Data:** 17 luglio 2026  
**Stato:** codice pre-produzione completo e disattivato; configurazioni e collaudi esterni ancora mancanti  
**Baseline di partenza:** `d3aaffe2cbe76da21fd24e9c98c7518e8c8cda4b`

## Funziona già

- dominio completo di validazione, selezione, template e stati notifiche;
- lettura di `Operativo` e persistenza `NOTIFICHE` tramite adapter Google testati con fake;
- inizializzatore idempotente e non distruttivo del foglio amministrativo;
- verifica di CONFIG, DASHBOARD, NOTIFICHE e ANOMALIE anche dopo aggiornamenti runtime;
- parser tipizzato di `CONFIG` con kill switch, limiti, override e barriere multiple;
- registro persistente con `SENDING`, `SENT`, `FAILED_RETRYABLE` e `UNKNOWN_REVIEW_REQUIRED`;
- dashboard aggregata, registro anomalie minimizzato e valutazione salute;
- orchestratore end-to-end per `DRY_RUN`, `TEST_SMTP` e `PRODUZIONE` protetta;
- SMTP MDaemon testo/HTML, Message-ID, STARTTLS/SSL, fake e logo CID opzionale;
- factory Google basata su ADC temporanee prodotte da WIF;
- comando `check-headers` che legge soltanto la riga 2 di `Operativo`;
- CLI per inizializzare il foglio, controllare le intestazioni ed eseguire il flusso;
- workflow manuale pre-produzione disabilitato per default e con `concurrency`;
- modello di workflow produzione non attivo;
- runbook operativo, emergenze, handoff, test e deployment;
- test automatici e CI.

## Barriere di sicurezza

- nessuna chiave JSON permanente;
- nessuna credenziale, email reale o PII nel repository;
- nessun accesso Google finché l'environment non abilita esplicitamente la pre-produzione;
- nessun invio fuori dal dry-run senza conferma CLI e `ALLOW_EMAIL_DELIVERY=true`;
- produzione subordinata anche a `PRODUCTION_ACTIVATION_ACK`;
- `CONFIG` deve essere coerente con modalità ed environment;
- workflow schedulato presente soltanto come file `.example` non eseguibile;
- output CLI esclusivamente aggregato;
- esiti SMTP incerti non vengono ritentati automaticamente.

## Da creare o valorizzare esternamente

- progetto Google Cloud, API, service account, pool e provider WIF;
- GitHub Environments, Variables e binding IAM;
- condivisione diretta dei due Spreadsheet;
- creazione controllata del foglio amministrativo tramite workflow manuale;
- parametri e credenziali MDaemon;
- mittente, Reply-To, firma ufficiale e logo approvato;
- seconda identità umana CIA di recupero.

## Collaudi ancora necessari

- inizializzazione reale su Spreadsheet sintetico;
- `check-headers` reale con zero righe dati lette;
- dry-run aggregato su `Operativo`;
- append, update e duplicati sul registro sintetico;
- test SMTP esclusivamente all'override;
- errori retryable, permanenti e incerti;
- concorrenza, crash dopo `SENDING` e rerun;
- prova dei runbook con un responsabile non tecnico.

## Prossimo passo

Creare il progetto Google Cloud e l'environment `preproduction`, inserire gli identificatori pubblici e avviare nell'ordine `check-headers`, `init-admin`, dry-run e test SMTP con override. Nessun invio reale ad arbitri è necessario per questi collaudi.
