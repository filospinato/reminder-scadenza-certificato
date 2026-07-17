# Checklist di deployment graduale

## A. Software

- [ ] CI verde sulla PR e su `main`;
- [ ] dipendenze Google installabili e verificate con l'extra `google`;
- [ ] workflow manuale pre-produzione verificato;
- [ ] gate Environment, data opzionale e lock condiviso verificati;
- [ ] modello produzione revisionato ma non ancora attivato;
- [ ] nessun segreto o PII nel repository;
- [ ] issue #1 e documentazione allineate.

## B. Google Cloud

- [ ] progetto creato;
- [ ] Sheets API abilitata;
- [ ] service account dedicato senza chiavi;
- [ ] pool e provider WIF creati;
- [ ] trust limitata a repository, proprietario, `main` e workflow/environment;
- [ ] binding `roles/iam.workloadIdentityUser` limitato;
- [ ] seconda identità umana CIA configurata;
- [ ] procedura di revoca provata.

## C. Spreadsheet

- [ ] foglio amministrativo vuoto creato dall'account umano fuori da cartelle troppo condivise;
- [ ] proprietà e recupero umano verificati;
- [ ] file condiviso direttamente con il service account come editor;
- [ ] bootstrap dalla singola tab vuota riuscito;
- [ ] quattro tab verificate e inizializzatore idempotente;
- [ ] service account lettore di `Operativo`;
- [ ] `check-headers` riuscito con zero righe dati lette;
- [ ] scrittura sintetica, update e duplicati collaudati;
- [ ] dry-run confermato senza scritture nel registro;
- [ ] CONFIG ancora in stato sicuro.

## D. SMTP e contenuti

- [ ] host, porta e sicurezza MDaemon verificati;
- [ ] mittente e Reply-To approvati;
- [ ] credenziali inserite solo nei GitHub Secrets dello specifico Environment;
- [ ] corpo e firma ufficiali approvati;
- [ ] logo e CID approvati, se utilizzati;
- [ ] logo visibile nel corpo HTML e allegato inline;
- [ ] test SMTP singolo all'override riuscito;
- [ ] registro test contiene l'override effettivo;
- [ ] errori retryable, permanenti, incerti e non classificati collaudati;
- [ ] nessuna copia nella Posta inviata confermata.

## E. Attivazione a livelli

- [ ] dry-run sintetico;
- [ ] scrittura sintetica sul foglio amministrativo;
- [ ] dry-run su `Operativo` con output aggregato e deduplicazione verificata;
- [ ] test SMTP con override;
- [ ] singolo invio autorizzato;
- [ ] piccolo lotto controllato;
- [ ] workflow schedulato con invii ancora bloccati;
- [ ] autorizzazione esplicita finale;
- [ ] `PRODUCTION_ENABLED=true`;
- [ ] CONFIG coerente con produzione e kill switch disattivo;
- [ ] orari cron verificati rispetto a UTC e ora legale;
- [ ] monitoraggio ravvicinato delle prime esecuzioni.

## F. Handoff

- [ ] responsabile non tecnico ha superato il collaudo;
- [ ] inventario risorse completato;
- [ ] contatti, proprietà e recupero del foglio registrati;
- [ ] procedure emergenza provate;
- [ ] automazione di sviluppo disabilitata dopo la consegna definitiva.
