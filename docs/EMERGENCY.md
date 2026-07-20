# Procedure di emergenza

## Arresto immediato

1. Impostare `INVIO_AUTOMATICO_ATTIVO=false` nella tab `CONFIG`.
2. Annullare eventuali workflow produttivi già in corso.
3. Se necessario, revocare temporaneamente le credenziali SMTP o l'accesso WIF.
4. Non cancellare righe di `NOTIFICHE` finché l'esito non è stato ricostruito.

Con l'interruttore spento una nuova esecuzione produttiva non legge le righe operative e non inizializza SMTP. `check` e `test-smtp` restano intenzionalmente disponibili come operazioni manuali separate.

## Diagnosi iniziale

Eseguire:

```bash
reminder-certificati check
```

Il controllo mostra risultati aggregati, verifica anche il registro e non invia email.

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

Può indicare un'interruzione tra prenotazione e conclusione SMTP. Non renderla automaticamente ritentabile. Verificare prima server SMTP, Message-ID e cronologia; in assenza di certezza trattarla come esito incerto.

## Schema alterato

Mantenere l'invio automatico spento, creare una copia di sicurezza ed eseguire:

```bash
reminder-certificati setup-admin --spreadsheet-id ID
```

Controllare l'anteprima e applicare l'aggiornamento con `--apply` soltanto dopo aver verificato il piano. Al termine eseguire `check` prima di riattivare gli invii programmati.

## Chiavi duplicate

Il setup e il runtime rifiutano chiavi duplicate. Conservare il backup, ricostruire la cronologia e mantenere una sola riga coerente con revisione a quattro occhi. Non pubblicare tessere, Message-ID o contenuti del foglio in issue.

## Revoca Google o compromissione SMTP

Per Google rimuovere il binding WIF, disabilitare il provider o revocare le condivisioni. Per SMTP disabilitare le credenziali sul server e ruotare i Secrets. Non creare chiavi JSON permanenti come soluzione temporanea.

## Rollback

Ripristinare l'ultimo commit verde tramite PR di revert, senza forzare `main`. Se lo schema del foglio è già stato aggiornato, non ripristinare una versione applicativa incompatibile senza un piano esplicito; mantenere sempre `INVIO_AUTOMATICO_ATTIVO=false` durante il rollback.
