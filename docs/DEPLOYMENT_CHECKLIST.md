# Checklist di deployment graduale

## A. Software

- [ ] CI verde sulla PR e su `main`;
- [ ] dipendenze Google installabili con l'extra `google`;
- [ ] unico entry point `reminder-certificati` verificato;
- [ ] workflow ordinario e workflow di manutenzione verificati;
- [ ] Environment e lock condiviso verificati;
- [ ] modello produttivo revisionato, non attivo e senza schedule;
- [ ] nessun segreto o dato personale nel repository;
- [ ] issue #1 e documentazione allineate.

## B. Google Cloud

- [ ] progetto creato;
- [ ] Sheets API abilitata;
- [ ] service account dedicato senza chiavi permanenti;
- [ ] pool e provider WIF creati;
- [ ] trust limitata a repository, proprietario, `main` e workflow/Environment;
- [ ] binding `roles/iam.workloadIdentityUser` limitato;
- [ ] seconda identità umana CIA configurata;
- [ ] procedura di revoca provata.

## C. Spreadsheet

- [ ] foglio amministrativo creato dall'account umano;
- [ ] proprietà e recupero umano verificati;
- [ ] file condiviso direttamente con il service account come editor;
- [ ] `reminder-certificati setup-admin --spreadsheet-id ID` eseguito in anteprima;
- [ ] `setup-admin --apply` completato con backup quando necessario;
- [ ] quattro tab presenti e visibili;
- [ ] service account lettore di `Operativo`;
- [ ] `INVIO_AUTOMATICO_ATTIVO=false` verificato dopo il setup;
- [ ] `reminder-certificati check` riuscito;
- [ ] collaudo sintetico del registro riuscito.

## D. Controllo senza invio

- [ ] `INVIO_AUTOMATICO_ATTIVO=false`;
- [ ] nessun obbligo di override o parametri SMTP;
- [ ] `reminder-certificati check` riuscito;
- [ ] conteggi aggregati e categorie escluse verificati;
- [ ] zero scritture in `NOTIFICHE` durante il controllo;
- [ ] zero chiamate SMTP.

## E. SMTP e contenuti

- [ ] host, porta e sicurezza MDaemon verificati;
- [ ] mittente e Reply-To approvati;
- [ ] credenziali inserite solo nei Secrets dello specifico Environment;
- [ ] corpo e firma ufficiali approvati;
- [ ] logo e CID approvati, se utilizzati;
- [ ] `DESTINATARIO_OVERRIDE` configurato;
- [ ] `INVIO_AUTOMATICO_ATTIVO=false` durante la prova;
- [ ] `reminder-certificati test-smtp` riuscito;
- [ ] usato un candidato reale e inviata al massimo una email all'override;
- [ ] registro test contiene la notifica `TEST_`;
- [ ] errori ritentabili, permanenti e incerti collaudati;
- [ ] nessuna copia nella Posta inviata confermata.

## F. Attivazione graduale

- [ ] setup e controllo completi;
- [ ] scrittura sintetica sul foglio amministrativo;
- [ ] test SMTP con override;
- [ ] singolo invio reale autorizzato;
- [ ] piccolo lotto controllato;
- [ ] autorizzazione esplicita finale;
- [ ] Environment `production` protetto;
- [ ] una sola schedule giornaliera aggiunta e verificata rispetto a UTC e ora legale;
- [ ] workflow produttivo spostato in `.github/workflows`;
- [ ] `INVIO_AUTOMATICO_ATTIVO=true` impostato soltanto al go-live;
- [ ] monitoraggio ravvicinato delle prime esecuzioni.

## G. Arresto e handoff

- [ ] `INVIO_AUTOMATICO_ATTIVO=false` provato come arresto degli invii programmati;
- [ ] responsabile non tecnico ha superato il collaudo;
- [ ] inventario risorse completato;
- [ ] contatti, proprietà e recupero del foglio registrati;
- [ ] procedure di emergenza provate;
- [ ] automazione di sviluppo disabilitata dopo la consegna definitiva.
