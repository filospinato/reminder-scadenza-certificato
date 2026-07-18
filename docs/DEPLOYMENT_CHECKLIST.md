# Checklist di deployment graduale

## A. Software

- [ ] CI verde sulla PR e su `main`;
- [ ] dipendenze Google installabili con l'extra `google`;
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

- [ ] foglio amministrativo vuoto creato dall'account umano fuori da cartelle troppo condivise;
- [ ] proprietà e recupero umano verificati;
- [ ] file condiviso direttamente con il service account come editor;
- [ ] bootstrap dalla singola tab vuota riuscito;
- [ ] quattro tab presenti; un eventuale riordino visuale non causa errore;
- [ ] service account lettore di `Operativo`;
- [ ] preflight riuscito con file distinti e sole intestazioni necessarie;
- [ ] collaudo sintetico del registro riuscito;
- [ ] deduplicazione delle anomalie aperte verificata;
- [ ] CONFIG ancora in stato sicuro.

## D. Dry-run

- [ ] `SISTEMA_ATTIVO=true`;
- [ ] `KILL_SWITCH=false`;
- [ ] `INVII_REALI_ABILITATI=false`;
- [ ] nessun obbligo di override o parametri SMTP;
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
- [ ] test SMTP singolo riuscito;
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
- [ ] CONFIG con sistema attivo, invii reali abilitati, modalità test false e kill switch disattivo;
- [ ] orari cron verificati rispetto a UTC e ora legale;
- [ ] monitoraggio ravvicinato delle prime esecuzioni.

## G. Handoff

- [ ] responsabile non tecnico ha superato il collaudo;
- [ ] inventario risorse completato;
- [ ] contatti, proprietà e recupero del foglio registrati;
- [ ] procedure emergenza provate;
- [ ] automazione di sviluppo disabilitata dopo la consegna definitiva.
