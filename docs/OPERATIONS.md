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

1. Creare il progetto Google Cloud e WIF seguendo `AUTENTICAZIONE_GOOGLE.md`.
2. Impostare le GitHub Variables pubbliche del solo environment `preproduction`.
3. Impostare `PREPRODUCTION_ENABLED=true` soltanto quando WIF è pronto.
4. Eseguire manualmente `check-headers`: legge esclusivamente la riga 2 di `Operativo`.
5. Eseguire `init-admin`: crea o verifica lo Spreadsheet amministrativo senza PII.
6. Salvare l'ID restituito come `ADMIN_SPREADSHEET_ID`.
7. Eseguire un `dry-run` con data nota e controllare soltanto i conteggi aggregati.
8. Inserire un destinatario sintetico in `DESTINATARIO_OVERRIDE`.
9. Inserire i parametri SMTP nei GitHub Secrets dell'environment `preproduction`.
10. Eseguire `test-smtp` con conferma manuale. Tutti i destinatari sono sostituiti dall'override.

## Comandi locali

```bash
reminder-certificati-runtime init-admin
reminder-certificati-runtime init-admin --spreadsheet-id ID
reminder-certificati-runtime check-headers
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

- `DRY_RUN_OK`: lettura e composizione completate senza invio;
- `OK`: invii confermati dal trasporto;
- `ATTENZIONE`: uno o più errori ritentabili o di composizione;
- `REVISIONE_RICHIESTA`: esito SMTP incerto o errore permanente; non ritentare automaticamente;
- `DISATTIVATO`: sistema non attivo;
- `BLOCCATO_KILL_SWITCH`: barriera di emergenza attiva;
- `ERRORE`: lettura o schema non disponibile.

La dashboard contiene solo conteggi e codici aggregati, non nominativi o email.

## Registro NOTIFICHE

Non modificare manualmente le righe salvo procedura di emergenza documentata. Una chiave duplicata blocca il sistema. Gli stati `SENT`, `SENDING` e `UNKNOWN_REVIEW_REQUIRED` impediscono nuovi tentativi automatici; soltanto `FAILED_RETRYABLE` è riprenotabile.

## Modalità test

La modalità `TEST_SMTP`:

- richiede `MODALITA_TEST=true`;
- richiede `DESTINATARIO_OVERRIDE`;
- richiede la conferma del workflow;
- usa chiavi `TEST_REMINDER_*`, separate dalle notifiche reali;
- non invia ai destinatari di `Operativo`;
- continua a registrare Message-ID ed esiti per verificare il ciclo completo.

## Produzione

Il file `docs/workflows/production.yml.example` è soltanto un modello. Prima di copiarlo in `.github/workflows` devono essere completati tutti i punti della checklist di deployment, inclusi approvazione dei contenuti, test SMTP, WIF ristretto al workflow ed environment protetto.
