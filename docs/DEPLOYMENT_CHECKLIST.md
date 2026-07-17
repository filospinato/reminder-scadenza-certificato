# Checklist di deployment graduale

## A. Software

- [ ] CI verde sulla PR e su `main`;
- [ ] dipendenze Google installabili con l'extra `google`;
- [ ] workflow manuale pre-produzione verificato;
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

- [ ] foglio amministrativo creato fuori da cartelle troppo condivise;
- [ ] quattro tab verificate e inizializzatore idempotente;
- [ ] service account lettore di `Operativo`;
- [ ] service account editor del solo foglio amministrativo;
- [ ] `check-headers` riuscito con zero righe dati lette;
- [ ] scrittura sintetica, update e duplicati collaudati;
- [ ] CONFIG ancora in stato sicuro.

## D. SMTP e contenuti

- [ ] host, porta e sicurezza MDaemon verificati;
- [ ] mittente e Reply-To approvati;
- [ ] credenziali inserite solo nei GitHub Secrets;
- [ ] corpo e firma ufficiali approvati;
- [ ] logo e CID approvati, se utilizzati;
- [ ] test SMTP all'override riuscito;
- [ ] errori retryable, permanenti e incerti collaudati;
- [ ] nessuna copia nella Posta inviata confermata.

## E. Attivazione a livelli

- [ ] dry-run sintetico;
- [ ] scrittura sintetica sul foglio amministrativo;
- [ ] dry-run su `Operativo` con output aggregato;
- [ ] test SMTP con override;
- [ ] singolo invio autorizzato;
- [ ] piccolo lotto controllato;
- [ ] workflow schedulato con invii ancora bloccati;
- [ ] autorizzazione esplicita finale;
- [ ] `PRODUCTION_ENABLED=true`;
- [ ] CONFIG coerente con produzione e kill switch disattivo;
- [ ] monitoraggio ravvicinato delle prime esecuzioni.

## F. Handoff

- [ ] responsabile non tecnico ha superato il collaudo;
- [ ] inventario risorse completato;
- [ ] contatti e proprietà registrati;
- [ ] procedure emergenza provate;
- [ ] automazione di sviluppo disabilitata dopo la consegna definitiva.
