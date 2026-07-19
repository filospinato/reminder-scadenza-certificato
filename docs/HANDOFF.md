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

## Conoscenze minime del responsabile operativo

Il responsabile non tecnico deve saper:

1. impostare `AUTOMAZIONE_ATTIVA=true` o `false`;
2. eseguire `reminder-certificati preflight`;
3. eseguire `reminder-certificati dry-run`;
4. impostare un destinatario di test;
5. interpretare dashboard e anomalie;
6. distinguere `FAILED_RETRYABLE` da `UNKNOWN_REVIEW_REQUIRED`;
7. applicare le procedure di `EMERGENCY.md`.

Le attività tecniche su WIF, GitHub Secrets, IAM, codice e pull request restano responsabilità di un referente tecnico e non fanno parte della gestione ordinaria.

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
- arresto e riattivazione tramite `AUTOMAZIONE_ATTIVA`;
- simulazione di un esito incerto seguendo il runbook.

Il collaudo non include invii reali ad arbitri.
