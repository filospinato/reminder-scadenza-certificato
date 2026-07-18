# Runbook operativo

## Stato di sicurezza iniziale

Il sistema deve restare con:

- `SISTEMA_ATTIVO=false`;
- `INVII_REALI_ABILITATI=false`;
- `MODALITA_TEST=true`;
- `KILL_SWITCH=true`;
- `PREPRODUCTION_ENABLED` assente o diverso da `true`;
- nessun workflow di produzione attivo.

L'inserimento di ID Google o credenziali SMTP non modifica automaticamente questi valori e non abilita invii.

## Sequenza di preparazione

1. Creare con l'account Google umano lo Spreadsheet vuoto `Reminder certificati CIA Lazio — Gestione`, fuori da cartelle con condivisione ampia.
2. Creare il progetto Google Cloud e WIF seguendo `AUTENTICAZIONE_GOOGLE.md`.
3. Condividere il file operativo con il service account come lettore e il file amministrativo vuoto come editor.
4. Creare l'Environment GitHub `preproduction` e impostare gli identificatori pubblici.
5. Salvare l'ID del file vuoto come `ADMIN_SPREADSHEET_ID`.
6. Impostare `PREPRODUCTION_ENABLED=true` soltanto quando WIF e condivisioni sono pronti.
7. Eseguire `init-admin`: rinomina la singola tab vuota, crea le altre tre e inserisce solo struttura sintetica.
8. Eseguire `google-preflight`: verifica file distinti, ordine delle tab e sole righe delle intestazioni, senza leggere righe operative o scrivere celle.
9. Eseguire `registry-check` con la conferma sintetica dedicata: scrive e aggiorna una sola riga `.invalid` nella tab `NOTIFICHE`, senza leggere `Operativo` o usare SMTP.
10. Eseguire un `dry-run` con data corrente o una data controllata e verificare i conteggi aggregati. `check-headers` resta disponibile come diagnostica mirata della sola riga 2 di `Operativo`.
11. Inserire un destinatario sintetico in `DESTINATARIO_OVERRIDE`.
12. Inserire i parametri SMTP nei GitHub Secrets dell'Environment `preproduction`.
13. Eseguire `test-smtp` con conferma manuale: viene inviata al massimo una email, sempre all'override.

Un service account non viene usato per creare o possedere il file. La proprietà resta all'identità umana e l'accesso applicativo deriva dalla condivisione diretta.

## Comandi locali

```bash
reminder-certificati-runtime init-admin --spreadsheet-id ID
reminder-certificati-google-preflight
ALLOW_SYNTHETIC_REGISTRY_WRITE=true reminder-certificati-registry-check --confirm-synthetic-write
reminder-certificati-runtime check-headers
reminder-certificati-runtime run --mode DRY_RUN
reminder-certificati-runtime run --mode DRY_RUN --today 2026-07-17
reminder-certificati-runtime run --mode TEST_SMTP --today 2026-07-17 --confirm-email-delivery
```

I comandi Google richiedono l'extra `google` e Application Default Credentials temporanee:

```bash
pip install -e ".[google]"
```

## Modifica di CONFIG

Un responsabile può modificare soltanto le righe marcate `modificabile=true`. Non deve:

- rinominare chiavi;
- riordinare o cancellare colonne;
- duplicare righe;
- modificare `SALUTO_EMAIL`;
- modificare il campo `modificabile`;
- inserire password o segreti nel foglio.

La modalità test attiva richiede un `DESTINATARIO_OVERRIDE` formalmente valido. Il corpo deve iniziare con `ricevi questa mail`; l'oggetto non può contenere ritorni a capo.

## Lettura della dashboard

- `DRY_RUN_OK`: lettura, deduplicazione e composizione completate senza scritture nel registro e senza invio;
- `OK`: invii confermati dal trasporto;
- `ATTENZIONE`: uno o più errori ritentabili o di composizione;
- `REVISIONE_RICHIESTA`: esito SMTP incerto o errore permanente; non ritentare automaticamente;
- `DISATTIVATO`: sistema non attivo;
- `BLOCCATO_KILL_SWITCH`: barriera di emergenza attiva;
- `ERRORE`: lettura o schema non disponibile.

La dashboard contiene solo conteggi e codici aggregati, non nominativi o email. Viene aggiornata con una sola richiesta, senza essere prima svuotata.

## Registro NOTIFICHE

Non modificare manualmente le righe salvo procedura di emergenza documentata. Una chiave duplicata blocca il sistema. Gli stati `SENT`, `SENDING` e `UNKNOWN_REVIEW_REQUIRED` impediscono nuovi tentativi automatici; soltanto `FAILED_RETRYABLE` è riprenotabile.

Il dry-run consulta il registro per mostrare quanti candidati sono già presenti, ma non aggiunge o aggiorna righe. Il limite viene applicato dopo la deduplicazione.

## Modalità test

La modalità `TEST_SMTP`:

- richiede `MODALITA_TEST=true`;
- richiede `DESTINATARIO_OVERRIDE`;
- richiede la conferma del workflow;
- usa chiavi `TEST_REMINDER_*`, separate dalle notifiche reali;
- non invia ai destinatari di `Operativo`;
- invia al massimo una email per esecuzione;
- registra nel campo email l'override realmente contattato;
- continua a registrare Message-ID ed esiti per verificare il ciclo completo.

## Workflow

Il gate `PREPRODUCTION_ENABLED` viene letto dentro il job dopo la dichiarazione dell'Environment. Se non vale `true`, nessuno step di checkout, autenticazione, installazione o accesso esterno viene eseguito.

Il campo data del workflow manuale è facoltativo: se vuoto viene usata la data corrente del runner. Pre-produzione e produzione condividono lo stesso gruppo `concurrency`, perché scrivono sulle stesse tab. I segreti SMTP sono disponibili soltanto allo step di invio.

## Produzione

Il file `docs/workflows/production.yml.example` è soltanto un modello. Prima di copiarlo in `.github/workflows` devono essere completati tutti i punti della checklist di deployment, inclusi approvazione dei contenuti, test SMTP, WIF ristretto al workflow ed Environment protetto. Gli orari cron sono UTC e devono essere ricontrollati rispetto all'ora locale e all'ora legale.
