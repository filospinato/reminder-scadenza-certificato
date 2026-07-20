# Runbook operativo

## Stato sicuro

Lo stato iniziale e quello successivo a ogni migrazione sono:

- `AUTOMAZIONE_ATTIVA=false`;
- `INVII_REALI_ABILITATI=false`;
- nessun workflow di produzione attivo.

Con l'automazione spenta il runtime non legge le righe di `Operativo` e non inizializza SMTP.

## Preparazione o aggiornamento

1. Predisporre WIF, Environment e condivisioni Google.
2. Per un file vuoto eseguire `reminder-certificati init-admin --spreadsheet-id ID`.
3. Per un file esistente eseguire l'anteprima:

```bash
reminder-certificati migrate-admin --spreadsheet-id ID
```

4. Controllare le modifiche aggregate e applicare con backup:

```bash
reminder-certificati migrate-admin --spreadsheet-id ID \
  --apply --confirm-migration \
  --backup-path admin-migration-backup.json
```

5. Eseguire `reminder-certificati preflight`.
6. Eseguire il collaudo sintetico di NOTIFICHE.
7. Impostare `AUTOMAZIONE_ATTIVA=true`, lasciando gli invii reali spenti.
8. Eseguire il dry-run.
9. Configurare override e SMTP soltanto per il test controllato.

## Comandi

```bash
reminder-certificati preflight
ALLOW_SYNTHETIC_REGISTRY_WRITE=true reminder-certificati registry-check --confirm-synthetic-write
reminder-certificati review-registry
reminder-certificati dry-run
reminder-certificati test-smtp --confirm-email-delivery
reminder-certificati produzione --confirm-email-delivery
```

## Preflight

Controlla file distinti, tab, intestazioni, chiavi funzionali e `SCHEMA_VERSION` della CONFIG. Legge la sola riga delle intestazioni di `Operativo`, non le righe anagrafiche.

## Registro

`review-registry` mostra soltanto conteggi aggregati di:

- stati presenti;
- `SENDING` più vecchi della soglia, 24 ore per default;
- `FAILED_RETRYABLE` che hanno raggiunto tre tentativi;
- `FAILED_PERMANENT`;
- `UNKNOWN_REVIEW_REQUIRED`.

Non corregge automaticamente alcuna riga.

## Stati e codici di uscita

| Stato | Significato | Exit code |
|---|---|---:|
| `DISATTIVATO` | interruttore spento | 0 |
| `DRY_RUN_OK` / `OK` | esecuzione regolare | 0 |
| `ATTENZIONE` | errori ritentabili, permanenti o di composizione | 3 |
| `REVISIONE_RICHIESTA` | esito incerto | 4 |
| `ERRORE` | errore fatale | 2 |

Un workflow con `ATTENZIONE` non deve apparire verde.

## Modifica di CONFIG

L'operatore modifica normalmente soltanto la colonna `valore`. Non deve modificare `SCHEMA_VERSION`, rinominare chiavi, duplicare righe o inserire segreti. `AUTOMAZIONE_ATTIVA` resta l'unico comando ordinario e di emergenza; `INVII_REALI_ABILITATI` è solo una barriera aggiuntiva per la produzione.

## Modalità test

Il test SMTP mantiene il flusso corrente: usa `DESTINATARIO_OVERRIDE`, invia al massimo un messaggio e richiede doppio consenso. La modifica che lo renderebbe interamente sintetico non fa parte della versione 0.13.0.

## Produzione

Il modello schedulato resta fuori da `.github/workflows`. Prima dell'attivazione servono collaudi reali, contenuti approvati, Environment protetto e autorizzazione esplicita.
