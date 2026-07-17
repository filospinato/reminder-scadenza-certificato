# Procedure di emergenza

## Arresto immediato

Eseguire nell'ordine:

1. impostare `KILL_SWITCH=true` nella tab `CONFIG`;
2. impostare `PREPRODUCTION_ENABLED=false` o `PRODUCTION_ENABLED=false` nell'environment GitHub interessato;
3. annullare eventuali workflow in corso;
4. non cancellare righe di `NOTIFICHE` finché l'esito non è stato ricostruito;
5. annotare nella tab `ANOMALIE` un codice sintetico, senza copiare payload o dati personali.

Il kill switch viene verificato prima della lettura completa della sorgente e prima di qualsiasi invio.

## Esito `UNKNOWN_REVIEW_REQUIRED`

Non ritentare automaticamente. Verificare sul server SMTP, usando Message-ID e orario, se la consegna è stata accettata. Dopo la verifica:

- se consegnata, correggere lo stato a `SENT` con procedura controllata;
- se certamente non consegnata, correggere a `FAILED_RETRYABLE`;
- se resta dubbia, lasciare `UNKNOWN_REVIEW_REQUIRED` e contattare il destinatario con un canale separato solo se autorizzato.

## Riga bloccata in `SENDING`

Una riga `SENDING` può indicare un crash tra prenotazione e conclusione SMTP. Non trasformarla automaticamente in errore ritentabile. Verificare prima i log aggregati e il server SMTP. In assenza di prova certa, trattarla come esito incerto.

## Chiave duplicata in NOTIFICHE

1. attivare il kill switch;
2. esportare una copia amministrativa ristretta del solo foglio;
3. confrontare le due righe senza pubblicarne i dati in issue o log;
4. mantenere la riga con cronologia coerente e archiviare manualmente l'altra fuori dal foglio operativo;
5. rieseguire il controllo strutturale;
6. riattivare soltanto dopo revisione a quattro occhi.

## Schema alterato

Non tentare di adattare automaticamente le colonne. Ripristinare intestazioni e ordine dal contratto in `SCHEMA_FOGLI.md`. L'inizializzatore rifiuta contenuti esistenti incompatibili e non li sovrascrive.

## Revoca Google

Per bloccare immediatamente Google:

- rimuovere dal service account il binding `roles/iam.workloadIdentityUser`;
- oppure disabilitare il provider WIF;
- oppure rimuovere la condivisione diretta dai due Spreadsheet.

Non creare una chiave JSON come soluzione temporanea.

## Compromissione SMTP

1. disabilitare le credenziali sul server MDaemon;
2. rimuovere o ruotare i GitHub Secrets;
3. attivare kill switch e disabilitare l'environment;
4. controllare i Message-ID e i log del server;
5. non inserire credenziali o log completi in GitHub issue.

## Rollback applicativo

Ripristinare il precedente commit verde di `main` tramite una PR di revert. Non forzare `main` e non cancellare la cronologia. Mantenere il foglio amministrativo in kill switch durante il rollback.
