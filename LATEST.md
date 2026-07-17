# Stato corrente

**Versione:** 0.11.2  
**Data:** 17 luglio 2026  
**Stato:** codice pre-produzione rafforzato e disattivato; risorse e collaudi esterni ancora mancanti  
**Baseline di partenza:** `42b849cf68404f3b4472b9e3bab33ac191dd1ef2`

## Funziona già

- dominio completo di validazione, selezione, template e stati notifiche;
- lettura di `Operativo` e persistenza `NOTIFICHE` tramite adapter Google testati con fake;
- inizializzazione idempotente di un file vuoto creato dall'amministratore umano;
- bootstrap sicuro dalla singola tab vuota alle quattro tab canoniche;
- parser tipizzato di `CONFIG` con kill switch, limiti, override e barriere multiple;
- registro persistente con `SENDING`, `SENT`, `FAILED_RETRYABLE` e `UNKNOWN_REVIEW_REQUIRED`;
- dry-run consapevole delle notifiche già registrate, senza scritture;
- limite applicato dopo la deduplicazione;
- test SMTP limitato a un messaggio e audit dell'override effettivo;
- dashboard aggregata aggiornata con una singola scrittura, senza clear preventivo;
- anomalie e errori CLI con rimozione di email, token e chiavi di notifica;
- SMTP MDaemon testo/HTML, Message-ID, STARTTLS/SSL e logo CID visibile;
- workflow manuale con gate Environment corretto, data corrente predefinita e lock condiviso;
- segreti SMTP limitati allo step di invio;
- barriera runtime che accetta soltanto credenziali Google WIF `external_account` complete e rifiuta file JSON `service_account` permanenti;
- CI che installa e verifica anche l'extra Google;
- test automatici e runbook.

## Barriere di sicurezza

- nessuna chiave JSON permanente: le configurazioni note sono vietate e il file ADC viene verificato prima di costruire il client Google;
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
- Spreadsheet amministrativo vuoto creato dall'account umano;
- condivisione diretta dei due Spreadsheet;
- parametri e credenziali MDaemon;
- mittente, Reply-To, firma ufficiale e logo approvato;
- seconda identità umana CIA di recupero.

## Collaudi ancora necessari

- inizializzazione reale del file amministrativo vuoto;
- `check-headers` reale con zero righe dati lette;
- dry-run aggregato su `Operativo`;
- append, update e duplicati sul registro sintetico;
- test SMTP esclusivamente all'override;
- errori retryable, permanenti e incerti;
- concorrenza, crash dopo `SENDING` e rerun;
- prova dei runbook con un responsabile non tecnico.

## Prossimo passo

Creare con l'account umano lo Spreadsheet amministrativo vuoto, quindi predisporre progetto Google Cloud ed environment `preproduction`. Dopo la condivisione con il service account, eseguire nell'ordine `check-headers`, `init-admin --spreadsheet-id ID`, dry-run e test SMTP con override. Nessun invio reale ad arbitri è necessario per questi collaudi.
