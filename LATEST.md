# Stato corrente

**Versione:** 0.11.5  
**Data:** 18 luglio 2026  
**Stato:** codice pre-produzione rafforzato e disattivato; risorse e collaudi esterni ancora mancanti  
**Baseline di partenza:** `29aa14504f652c0547a893f5799763641c4d65ed`

## Funziona già

- dominio completo di validazione, selezione, template e stati notifiche;
- lettura di `Operativo` e persistenza `NOTIFICHE` tramite adapter Google testati con fake;
- inizializzazione idempotente di un file vuoto creato dall'amministratore umano;
- bootstrap sicuro dalla singola tab vuota alle quattro tab canoniche;
- parser tipizzato di `CONFIG` con kill switch, limiti, override e barriere multiple;
- registro persistente con `SENDING`, `SENT`, `FAILED_RETRYABLE` e `UNKNOWN_REVIEW_REQUIRED`;
- dry-run consapevole delle notifiche già registrate, senza scritture;
- limite applicato dopo la deduplicazione;
- comando protetto per collaudare append, rilettura e update della tab `NOTIFICHE` con una sola riga sintetica;
- preflight Google in sola lettura che verifica file distinti, ordine delle tab e sole righe delle intestazioni;
- codici diagnostici stabili del preflight, con messaggio pubblico, azione di runbook e JSON aggregato anche in errore;
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
- il preflight legge soltanto metadati e intestazioni, non legge righe operative, non scrive e non usa SMTP;
- il preflight rifiuta configurazioni nelle quali `Operativo` e amministrazione indicano lo stesso Spreadsheet;
- gli errori del preflight usano codici stabili e non riportano ID, email, celle, token o payload Google;
- il collaudo del registro richiede `--confirm-synthetic-write` e `ALLOW_SYNTHETIC_REGISTRY_WRITE=true`;
- il collaudo usa soltanto dati `.invalid`, non legge `Operativo` e non abilita email;
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
- preflight Google reale con zero righe operative lette e zero scritture;
- verifica pratica dei codici diagnostici e delle azioni del runbook su errori controllati;
- esecuzione controllata del comando sintetico sulla tab `NOTIFICHE` reale;
- dry-run aggregato su `Operativo`;
- test SMTP esclusivamente all'override;
- errori retryable, permanenti e incerti;
- concorrenza reale tra workflow e revoca dei permessi;
- prova dei runbook con un responsabile non tecnico.

## Prossimo passo

Creare con l'account umano lo Spreadsheet amministrativo vuoto, quindi predisporre progetto Google Cloud ed environment `preproduction`. Dopo la condivisione con il service account, eseguire nell'ordine `init-admin --spreadsheet-id ID`, `reminder-certificati-google-preflight`, `reminder-certificati-registry-check --confirm-synthetic-write`, dry-run e test SMTP con override. Nessun invio reale ad arbitri è necessario per questi collaudi.
