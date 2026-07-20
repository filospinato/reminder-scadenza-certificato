# Procedure di emergenza

## Arresto immediato

1. Impostare `AUTOMAZIONE_ATTIVA=false` in CONFIG.
2. Impostare `PREPRODUCTION_ENABLED=false` o `PRODUCTION_ENABLED=false` nell'Environment interessato.
3. Annullare eventuali workflow in corso.
4. Non cancellare righe di NOTIFICHE finché l'esito non è stato ricostruito.

Con l'interruttore spento il runtime non legge le righe operative e non inizializza SMTP.

## Diagnosi iniziale

Eseguire:

```bash
reminder-certificati review-registry
```

Il comando mostra soltanto conteggi aggregati e non modifica il registro.

## `UNKNOWN_REVIEW_REQUIRED`

Non ritentare automaticamente. Verificare sul server SMTP tramite Message-ID e orario:

- consegna confermata: correggere a `SENT` con procedura controllata;
- mancata consegna certa e temporanea: correggere a `FAILED_RETRYABLE` soltanto se restano tentativi;
- dubbio residuo: lasciare `UNKNOWN_REVIEW_REQUIRED`.

## `FAILED_PERMANENT`

Indica un rifiuto certo o una configurazione non recuperabile automaticamente. Correggere la causa e decidere manualmente se creare una nuova notifica; non trasformare automaticamente lo stato in ritentabile.

## Retry esauriti

Dopo tre tentativi un `FAILED_RETRYABLE` non viene più prenotato. Verificare la causa e intervenire manualmente, senza azzerare il contatore alla cieca.

## Riga `SENDING` vecchia

Può indicare un crash tra prenotazione e conclusione SMTP. Non renderla automaticamente ritentabile. Verificare prima server SMTP, Message-ID e cronologia; in assenza di certezza trattarla come esito incerto.

## Schema alterato

Mantenere l'automazione spenta, creare una copia di sicurezza ed eseguire:

```bash
reminder-certificati migrate-admin --spreadsheet-id ID
```

Applicare la migrazione soltanto dopo aver controllato l'anteprima. `preflight` deve risultare verde prima della riattivazione.

## Chiavi duplicate

La migrazione e il runtime rifiutano chiavi duplicate. Conservare il backup, ricostruire la cronologia e mantenere una sola riga coerente con revisione a quattro occhi. Non pubblicare tessere, Message-ID o contenuti del foglio in issue.

## Revoca Google o compromissione SMTP

Per Google rimuovere il binding WIF, disabilitare il provider o revocare le condivisioni. Per SMTP disabilitare le credenziali sul server e ruotare i Secrets. Non creare chiavi JSON permanenti come soluzione temporanea.

## Rollback

Ripristinare l'ultimo commit verde tramite PR di revert, senza forzare `main`. Se lo schema del foglio è già stato migrato, non ripristinare una versione applicativa incompatibile senza un piano esplicito; mantenere sempre `AUTOMAZIONE_ATTIVA=false` durante il rollback.
