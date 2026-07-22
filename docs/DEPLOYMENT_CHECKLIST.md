# Checklist di deployment graduale

Questa checklist registra soltanto attività concluse con evidenze verificabili;
va aggiornata insieme a ogni modifica che completa un passo di deployment.

## A. Software

- [x] CI verde sulla PR e su `main`;
- [x] dipendenze Google installabili con l'extra `google`;
- [x] unico entry point `reminder-certificati` verificato;
- [x] workflow ordinario e workflow di manutenzione verificati;
- [x] Environment `preproduction` e lock condiviso verificati;
- [x] modello produttivo revisionato, non attivo e senza schedule;
- [ ] nessun segreto o dato personale nel repository;
- [ ] issue #1 e documentazione allineate.

## B. Google Cloud

- [x] progetto creato;
- [x] Sheets API abilitata;
- [x] service account dedicato senza chiavi permanenti;
- [x] pool e provider WIF creati;
- [ ] trust limitata a repository, proprietario, `main` e workflow/Environment;
- [ ] binding `roles/iam.workloadIdentityUser` limitato;
- [ ] seconda identità umana CIA configurata;
- [ ] procedura di revoca provata.

## C. Spreadsheet

- [x] foglio amministrativo creato dall'account umano;
- [x] versione pre-live nominata nella cronologia del foglio;
- [ ] proprietà e recupero umano verificati;
- [x] file condiviso direttamente con il service account come editor;
- [x] `reminder-certificati setup-admin --spreadsheet-id ID` eseguito in anteprima;
- [x] `setup-admin --apply` completato con backup quando necessario;
- [ ] artifact del backup scaricato, custodito con accesso limitato e poi eliminato allo scadere della necessità;
- [x] quattro tab presenti e visibili;
- [x] service account lettore di `Operativo`;
- [x] `INVIO_AUTOMATICO_ATTIVO=false` verificato dopo il setup;
- [x] `reminder-certificati check` riuscito;
- [x] collaudo sintetico del registro riuscito.

## D. Controllo senza invio

- [x] `INVIO_AUTOMATICO_ATTIVO=false`;
- [x] nessun obbligo di override o parametri SMTP;
- [x] `reminder-certificati check` riuscito;
- [x] conteggi aggregati e categorie escluse verificati;
- [x] zero scritture in `NOTIFICHE` durante il controllo;
- [x] zero chiamate SMTP.

## E. SMTP e contenuti

- [ ] host, porta e sicurezza MDaemon verificati;
- [ ] se MDaemon richiede `PLAIN`, `ALLOW_PLAIN_SMTP=true` configurato come Environment Variable dopo aver verificato il canale di rete;
- [ ] mittente e Reply-To approvati;
- [ ] password inserita nel Secret e parametri non sensibili nelle Variables dello specifico Environment;
- [ ] corpo ufficiale approvato;
- [x] firma ufficiale approvata;
- [ ] resa HTML, logo inline e CID approvati nei client email usati;
- [x] `DESTINATARIO_OVERRIDE` configurato;
- [ ] `INVIO_AUTOMATICO_ATTIVO=false` durante la prova;
- [ ] `reminder-certificati test-smtp` riuscito;
- [ ] usato un candidato reale e inviata al massimo una email all'override;
- [ ] registro test contiene la notifica `TEST_`;
- [ ] errori ritentabili, permanenti e incerti collaudati;
- [ ] nessuna copia nella Posta inviata confermata.

## F. Attivazione graduale

- [x] setup e controllo completi;
- [x] scrittura sintetica sul foglio amministrativo;
- [ ] test SMTP con override;
- [ ] singolo invio reale autorizzato con `--max-sends 1`;
- [ ] piccolo lotto controllato con `--max-sends 5`;
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
