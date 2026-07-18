# Runbook operativo

## Stato di sicurezza iniziale

Il sistema nasce con:

- `SISTEMA_ATTIVO=false`;
- `INVII_REALI_ABILITATI=false`;
- `MODALITA_TEST=true`;
- `KILL_SWITCH=true`;
- `PREPRODUCTION_ENABLED` assente o diverso da `true`;
- nessun workflow di produzione attivo.

L'inserimento di ID Google o credenziali SMTP non abilita invii.

## Sequenza di preparazione

1. Creare con l'account Google umano lo Spreadsheet vuoto `Reminder certificati CIA Lazio — Gestione`, fuori da cartelle con condivisione ampia.
2. Creare il progetto Google Cloud e WIF seguendo `AUTENTICAZIONE_GOOGLE.md`.
3. Condividere `Operativo` come lettore e il file amministrativo come editor con il service account.
4. Creare l'Environment GitHub `preproduction` e impostare le Variables pubbliche.
5. Impostare `PREPRODUCTION_ENABLED=true` soltanto quando WIF e condivisioni sono pronti.
6. Eseguire `init-admin`.
7. Eseguire `google-preflight`: verifica file distinti, presenza delle tab e sole intestazioni necessarie. L'ordine visuale delle tab non è rilevante.
8. Eseguire `registry-check` con la conferma sintetica dedicata.
9. Preparare il dry-run impostando in CONFIG:
   - `SISTEMA_ATTIVO=true`;
   - `KILL_SWITCH=false`;
   - `INVII_REALI_ABILITATI=false`;
   - `MODALITA_TEST=true` o `false`, senza obbligo di override.
10. Eseguire il dry-run e verificare i conteggi aggregati. `check-headers` resta una diagnostica facoltativa della sola riga 2.
11. Prima del solo test SMTP, inserire un destinatario di prova in `DESTINATARIO_OVERRIDE` e lasciare `MODALITA_TEST=true`.
12. Inserire i parametri SMTP nei Secrets dell'Environment `preproduction`.
13. Eseguire `test-smtp` con conferma manuale: al massimo una email, sempre all'override.

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

I comandi Google richiedono l'extra `google` e credenziali temporanee WIF:

```bash
pip install -e ".[google]"
```

## Modifica di CONFIG

Un responsabile può modificare le righe marcate `modificabile=true`. Non deve:

- rinominare chiavi;
- riordinare o cancellare colonne;
- duplicare righe;
- modificare il campo `modificabile`;
- inserire password o segreti nel foglio.

La CONFIG contiene soltanto impostazioni usate dal programma. Il saluto `Ciao {{nome}},` è fisso nel codice. `DESTINATARIO_OVERRIDE` è richiesto soltanto per `TEST_SMTP`, non per il dry-run.

`INVII_REALI_ABILITATI` è modificabile esclusivamente durante il go-live controllato e non è sufficiente da solo: produzione richiede anche sistema attivo, modalità test disattivata, kill switch disattivato, Environment protetto, `PRODUCTION_ENABLED=true` e consenso dello step SMTP.

## Lettura della dashboard

- `DRY_RUN_OK`: lettura, deduplicazione e composizione completate senza invio;
- `OK`: invii confermati dal trasporto;
- `ATTENZIONE`: uno o più errori ritentabili o di composizione;
- `REVISIONE_RICHIESTA`: esito SMTP incerto o errore permanente; non ritentare automaticamente;
- `DISATTIVATO`: sistema non attivo;
- `BLOCCATO_KILL_SWITCH`: barriera di emergenza attiva;
- `ERRORE`: lettura o schema non disponibile.

La dashboard contiene solo conteggi e codici aggregati.

## Registro NOTIFICHE

Non modificare manualmente le righe salvo procedura di emergenza documentata. Una chiave duplicata blocca il sistema. `SENT`, `SENDING` e `UNKNOWN_REVIEW_REQUIRED` impediscono nuovi tentativi automatici; soltanto `FAILED_RETRYABLE` è riprenotabile.

Il registro viene letto una sola volta all'inizio dell'elaborazione e mantenuto in un indice locale aggiornato dopo append e update. Il dry-run consulta l'indice ma non scrive.

## Anomalie

La tab `ANOMALIE` non riaccoda a ogni esecuzione la stessa anomalia ancora aperta. L'ID deterministico viene letto una volta e usato per deduplicare. Una nuova riga può essere registrata dopo che la precedente è stata marcata come risolta.

## Modalità test

La modalità `TEST_SMTP`:

- richiede `MODALITA_TEST=true`;
- richiede `DESTINATARIO_OVERRIDE`;
- richiede la conferma del workflow;
- usa chiavi `TEST_REMINDER_*` separate;
- non invia ai destinatari di `Operativo`;
- invia al massimo una email per esecuzione;
- registra l'override realmente contattato, Message-ID ed esito.

## Workflow

Se `PREPRODUCTION_ENABLED` non vale `true`, nessuno step con accesso esterno viene eseguito. Pre-produzione e produzione condividono lo stesso gruppo `concurrency`. I segreti SMTP sono disponibili soltanto allo step di invio. I workflow installano il pacchetto senza eseguire upgrade dinamici di pip.

## Produzione

`docs/workflows/production.yml.example` è soltanto un modello. Prima di copiarlo in `.github/workflows` servono approvazione dei contenuti, test SMTP, WIF ristretto, Environment protetto e autorizzazione esplicita. Gli orari cron sono UTC e devono essere ricontrollati rispetto all'ora locale e all'ora legale.
