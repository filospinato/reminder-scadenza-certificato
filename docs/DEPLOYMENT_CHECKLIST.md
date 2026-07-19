# Checklist di deployment graduale

## A. Software

- [ ] CI verde sulla PR e su `main`;
- [ ] dipendenze Google installabili con l'extra `google`;
- [ ] unico comando `reminder-certificati` verificato;
- [ ] workflow manuale pre-produzione verificato;
- [ ] Environment, data opzionale e lock condiviso verificati;
- [ ] modello produzione revisionato ma non attivato;
- [ ] nessun segreto o PII nel repository;
- [ ] issue #1 e documentazione allineate.

## B. Google Cloud

- [ ] progetto creato;
- [ ] Sheets API abilitata;
- [ ] service account dedicato senza chiavi;
- [ ] pool e provider WIF creati;
- [ ] trust limitata a repository, proprietario, `main` e workflow/Environment;
- [ ] binding `roles/iam.workloadIdentityUser` limitato;
- [ ] seconda identità umana CIA configurata;
- [ ] procedura di revoca provata.

## C. Spreadsheet

- [ ] foglio amministrativo vuoto creato dall'account umano;
- [ ] proprietà e recupero umano verificati;
- [ ] file condiviso direttamente con il service account come editor;
- [ ] `reminder-certificati init-admin` riuscito;
- [ ] quattro tab presenti;
- [ ] service account lettore di `Operativo`;
- [ ] `reminder-certificati preflight` riuscito;
- [ ] collaudo sintetico del registro riuscito;
- [ ] deduplicazione delle anomalie aperte verificata;
- [ ] CONFIG ancora in stato sicuro.

## D. Dry-run

- [ ] `AUTOMAZIONE_ATTIVA=true`;
- [ ] `INVII_REALI_ABILITATI=false`;
- [ ] nessun obbligo di override o parametri SMTP;
- [ ] `reminder-certificati dry-run` riuscito;
- [ ] conteggi aggregati verificati;
- [ ] zero scritture in `NOTIFICHE`;
- [ ] zero chiamate SMTP.

## E. SMTP e contenuti

- [ ] host, porta e sicurezza MDaemon verificati;
- [ ] mittente e Reply-To approvati;
- [ ] credenziali inserite solo nei Secrets dello specifico Environment;
- [ ] corpo e firma ufficiali approvati;
- [ ] logo e CID approvati, se utilizzati;
- [ ] override configurato per il solo test SMTP;
- [ ] `reminder-certificati test-smtp` riuscito;
- [ ] registro test contiene l'override effettivo;
- [ ] errori retryable, permanenti e incerti collaudati;
- [ ] nessuna copia nella Posta inviata confermata.

## F. Attivazione a livelli

- [ ] preflight in sola lettura;
- [ ] scrittura sintetica sul foglio amministrativo;
- [ ] dry-run su `Operativo`;
- [ ] test SMTP con override;
- [ ] singolo invio autorizzato;
- [ ] piccolo lotto controllato;
- [ ] autorizzazione esplicita finale;
- [ ] Environment `production` protetto;
- [ ] `PRODUCTION_ENABLED=true`;
- [ ] `AUTOMAZIONE_ATTIVA=true`;
- [ ] `INVII_REALI_ABILITATI=true`;
- [ ] una sola schedule giornaliera verificata rispetto a UTC e ora legale;
- [ ] monitoraggio ravvicinato delle prime esecuzioni.

## G. Arresto e handoff

- [ ] `AUTOMAZIONE_ATTIVA=false` provato come arresto immediato;
- [ ] responsabile non tecnico ha superato il collaudo;
- [ ] inventario risorse completato;
- [ ] contatti, proprietà e recupero del foglio registrati;
- [ ] procedure emergenza provate;
- [ ] automazione di sviluppo disabilitata dopo la consegna definitiva.
