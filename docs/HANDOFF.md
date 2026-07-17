# Passaggio di consegne

## Identità e proprietà da registrare

Prima della produzione compilare, fuori dal repository pubblico ai collaboratori non autorizzati:

- proprietario principale del progetto Google Cloud;
- seconda identità umana CIA di recupero;
- responsabile GitHub del repository;
- responsabile del foglio amministrativo;
- referente MDaemon;
- contatto di emergenza;
- data dell'ultima revisione accessi.

Non usare account condivisi o password comuni.

## Conoscenze minime del nuovo responsabile

Il responsabile deve saper:

1. attivare e disattivare il kill switch;
2. eseguire `check-headers`;
3. eseguire un dry-run manuale;
4. impostare un destinatario di test;
5. interpretare gli stati della dashboard;
6. distinguere `FAILED_RETRYABLE` da `UNKNOWN_REVIEW_REQUIRED`;
7. revocare l'accesso WIF;
8. aggiornare o rimuovere un GitHub Secret SMTP;
9. aprire una PR senza scrivere direttamente su `main`;
10. applicare le procedure di `EMERGENCY.md`.

## Inventario delle risorse

- repository: `filospinato/reminder-scadenza-certificato`;
- sorgente: `CIA Lazio 25/26 - Automatico`, tab `Operativo`, sola lettura;
- amministrazione: `Reminder certificati CIA Lazio — Gestione`;
- progetto Google Cloud: da inserire;
- service account: da inserire;
- Workload Identity Pool/provider: da inserire;
- environment GitHub `preproduction`: da creare;
- environment GitHub `production`: da creare prima del go-live;
- casella mittente MDaemon: da inserire;
- Reply-To: da inserire;
- logo approvato: da inserire senza versionare font o materiali riservati.

## Rotazione e revoca

Al cambio di responsabile:

1. aggiungere il nuovo account individuale;
2. verificare accesso e recupero;
3. rimuovere il precedente account;
4. rivedere condivisioni dei due Spreadsheet;
5. rivedere amministratori Google Cloud;
6. rivedere accessi GitHub ed environment approvers;
7. ruotare credenziali SMTP se il precedente responsabile ne aveva conoscenza;
8. aggiornare la data di revisione accessi.

## Collaudo del passaggio

Il nuovo responsabile deve completare senza assistenza tecnica:

- modifica sicura di `GIORNI_PREAVVISO`;
- modifica del limite per esecuzione;
- impostazione dell'override test;
- esecuzione di un dry-run;
- lettura di dashboard e anomalie;
- attivazione e rimozione del kill switch;
- simulazione di un esito incerto seguendo il runbook.

Il collaudo non include invii reali ad arbitri.
