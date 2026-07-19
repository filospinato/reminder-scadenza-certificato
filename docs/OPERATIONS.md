# Runbook operativo

## Stato di sicurezza iniziale

Il sistema nasce con:

- `AUTOMAZIONE_ATTIVA=false`;
- `INVII_REALI_ABILITATI=false`;
- `PREPRODUCTION_ENABLED` assente o diverso da `true`;
- nessun workflow di produzione attivo.

L'inserimento di ID Google o credenziali SMTP non abilita invii.

## Sequenza di preparazione

1. Creare con l'account Google umano lo Spreadsheet vuoto `Reminder certificati CIA Lazio — Gestione`.
2. Creare il progetto Google Cloud e WIF seguendo `AUTENTICAZIONE_GOOGLE.md`.
3. Condividere `Operativo` come lettore e il file amministrativo come editor con il service account.
4. Creare l'Environment GitHub `preproduction` e impostare le Variables pubbliche.
5. Impostare `PREPRODUCTION_ENABLED=true` soltanto quando WIF e condivisioni sono pronti.
6. Eseguire `reminder-certificati init-admin --spreadsheet-id ID`.
7. Eseguire `reminder-certificati preflight`.
8. Eseguire `reminder-certificati registry-check --confirm-synthetic-write` con la variabile dedicata.
9. Impostare `AUTOMAZIONE_ATTIVA=true` e lasciare `INVII_REALI_ABILITATI=false`.
10. Eseguire `reminder-certificati dry-run` e verificare i conteggi aggregati.
11. Prima del test SMTP inserire `DESTINATARIO_OVERRIDE`.
12. Inserire i parametri SMTP nei Secrets dell'Environment `preproduction`.
13. Eseguire `reminder-certificati test-smtp --confirm-email-delivery`.

## Comando unico

```bash
reminder-certificati init-admin --spreadsheet-id ID
reminder-certificati preflight
ALLOW_SYNTHETIC_REGISTRY_WRITE=true reminder-certificati registry-check --confirm-synthetic-write
reminder-certificati dry-run
reminder-certificati dry-run --today 2026-07-17
reminder-certificati test-smtp --today 2026-07-17 --confirm-email-delivery
reminder-certificati produzione --confirm-email-delivery
```

## Modifica di CONFIG

Un responsabile modifica normalmente soltanto la colonna `valore`. Non deve:

- rinominare chiavi;
- riordinare o cancellare colonne;
- duplicare righe;
- inserire password o segreti nel foglio.

Le colonne `tipo`, `descrizione` e `modificabile` sono informative: una modifica editoriale non blocca il runtime.

### Unico interruttore operativo

- `AUTOMAZIONE_ATTIVA=true`: consente lettura, dry-run, test o produzione secondo il sottocomando eseguito;
- `AUTOMAZIONE_ATTIVA=false`: arresta immediatamente elaborazione e invii.

Non esiste un secondo kill switch. Lo stesso campo viene usato sia per la gestione ordinaria sia per l'emergenza.

`INVII_REALI_ABILITATI` resta una barriera separata per il solo go-live e non attiva nulla senza Environment e consenso SMTP.

## Lettura della dashboard

- `DRY_RUN_OK`: lettura, deduplicazione e composizione completate senza invio;
- `OK`: invii confermati dal trasporto;
- `ATTENZIONE`: uno o più errori ritentabili o di composizione;
- `REVISIONE_RICHIESTA`: esito SMTP incerto o errore permanente;
- `DISATTIVATO`: `AUTOMAZIONE_ATTIVA=false`;
- `ERRORE`: lettura o schema non disponibile.

La dashboard contiene solo conteggi e codici aggregati e mostra il valore corrente di `automazione_attiva`.

## Registro NOTIFICHE

Non modificare manualmente le righe salvo procedura di emergenza documentata. Una chiave duplicata blocca il sistema. `SENT`, `SENDING` e `UNKNOWN_REVIEW_REQUIRED` impediscono nuovi tentativi automatici; soltanto `FAILED_RETRYABLE` è riprenotabile.

## Modalità test

La modalità è determinata dal sottocomando `test-smtp`, non da un campo della CONFIG. Richiede:

- `AUTOMAZIONE_ATTIVA=true`;
- `DESTINATARIO_OVERRIDE`;
- conferma del workflow;
- al massimo una email per esecuzione.

## Workflow

Se `PREPRODUCTION_ENABLED` non vale `true`, nessuno step con accesso esterno viene eseguito. Pre-produzione e produzione condividono lo stesso gruppo `concurrency`. I segreti SMTP sono disponibili soltanto allo step di invio.

## Produzione

`docs/workflows/production.yml.example` è soltanto un modello. Prevede una sola esecuzione giornaliera. Prima di copiarlo in `.github/workflows` servono approvazione dei contenuti, test SMTP, WIF ristretto, Environment protetto e autorizzazione esplicita.
