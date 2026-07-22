# Deployment — release 0.14.18

Questa guida descrive il provisioning e il rollout della release 0.14.18. La versione è autoritativa in `../../pyproject.toml`; i nomi esatti di Variables, Secrets ed Environment sono in `../../config/github/environment-contract.json`; trigger e limiti effettivi sono nei workflow GitHub.

## Prerequisiti

- Python 3.11 o successivo;
- repository GitHub con Actions abilitate;
- progetto Google Cloud con Google Sheets API;
- service account dedicato senza chiavi permanenti;
- Workload Identity Federation e provider OIDC per GitHub Actions;
- Spreadsheet `Operativo` condiviso in sola lettura;
- Spreadsheet amministrativo creato da un’identità umana e condiviso in modifica;
- account SMTP MDaemon approvato.

Installazione locale:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev,google]"
pytest
```

## Modello di autenticazione Google

GitHub Actions accede a Google Sheets tramite WIF/OIDC. Sono vietati file JSON di service account, password, token utente e Domain-Wide Delegation.

Per questa release la trust policy deve limitare almeno:

- repository GitHub ID `1303804647`;
- proprietario GitHub ID `265553127`;
- branch `main`;
- workflow o Environment autorizzato prima dell’attivazione continuativa.

Attribute mapping minimo:

```text
google.subject=assertion.sub
attribute.repository_id=assertion.repository_id
attribute.repository_owner_id=assertion.repository_owner_id
attribute.ref=assertion.ref
attribute.workflow_ref=assertion.workflow_ref
```

Il service account deve avere soltanto:

- lettura diretta sullo Spreadsheet `Operativo`;
- modifica diretta sullo Spreadsheet amministrativo;
- nessun ruolo generale su Drive, Gmail, Calendar o dominio Workspace.

Il runtime accetta soltanto credenziali temporanee `external_account` prodotte dall’azione WIF e rifiuta configurazioni permanenti come `GOOGLE_SERVICE_ACCOUNT_JSON`, `GOOGLE_APPLICATION_CREDENTIALS_JSON` o `GCP_SERVICE_ACCOUNT_KEY`.

## Preparazione dello Spreadsheet amministrativo

1. Creare un file vuoto con l’account umano che ne conserverà proprietà e recupero.
2. Collocarlo fuori da cartelle con condivisioni ereditate non necessarie.
3. Condividerlo direttamente con il service account come editor.
4. Valorizzare `ADMIN_SPREADSHEET_ID` nell’Environment GitHub.
5. Eseguire l’anteprima:

```bash
reminder-certificati setup-admin --spreadsheet-id ID
```

6. Revisionare il piano.
7. Applicare soltanto se il piano è atteso:

```bash
reminder-certificati setup-admin --spreadsheet-id ID --apply
```

8. Conservare il backup con accesso limitato per il tempo necessario.
9. Verificare che `INVIO_AUTOMATICO_ATTIVO=false`.
10. Eseguire `check` e, quando richiesto, `registry-check`.

## Configurazione GitHub

Tutti i workflow usano l’Environment dichiarato in `../../config/github/environment-contract.json`. Lo stesso file è autoritativo per i nomi consentiti di Variables e Secrets; i workflow restano autoritativi per il loro effettivo utilizzo.

Regole:

- soltanto `SMTP_PASSWORD` è un Secret;
- host, porta, sicurezza, Reply-To e username SMTP sono Variables dello specifico Environment;
- `SMTP_USERNAME` viene usato anche come mittente;
- `ALLOW_PLAIN_SMTP=true` è ammesso soltanto quando MDaemon richiede esplicitamente trasporto senza TLS su rete approvata;
- nessun valore SMTP deve comparire nei log.

## Sequenza di collaudo

Con `INVIO_AUTOMATICO_ATTIVO=false`:

1. eseguire `setup-preview`;
2. eseguire `check`;
3. verificare zero tentativi SMTP e zero scritture operative;
4. per schema, migrazioni o persistenza eseguire `registry-check`;
5. con autorizzazione distinta, configurare `DESTINATARIO_OVERRIDE` ed eseguire un solo `test-smtp`;
6. verificare la notifica di test e la resa del messaggio.

## Rollout produttivo

La release espone un workflow produttivo soltanto manuale e senza schedule.

1. autorizzare formalmente un singolo invio reale;
2. impostare temporaneamente `INVIO_AUTOMATICO_ATTIVO=true`;
3. avviare il workflow con limite 1;
4. verificare registro, dashboard, anomalie e deduplicazione;
5. autorizzare un lotto da 5 e verificarlo;
6. passare al limite 10 soltanto dopo esito positivo;
7. aggiungere una schedule giornaliera solo con decisione separata, verificando UTC e ora legale di `Europe/Rome`;
8. monitorare ravvicinatamente le prime esecuzioni.

## Criteri di uscita

- CI completa verde;
- nessun segreto o dato personale nei diff e nei log;
- schema e migrazioni verificati;
- controllo senza invio riuscito sui fogli reali;
- registro sintetico verificato quando applicabile;
- prova SMTP autorizzata riuscita;
- errori ritentabili, permanenti e incerti collaudati prima del funzionamento continuativo;
- procedure di arresto provate;
- responsabile operativo formato;
- autorizzazione esplicita al go-live.

## Rollback

Disattivare prima gli invii tramite `INVIO_AUTOMATICO_ATTIVO=false`. Ripristinare il codice con una PR di revert. Non ripristinare una versione incompatibile con lo schema amministrativo corrente senza un piano di migrazione inversa. Revocare WIF o SMTP quando l’incidente riguarda le credenziali.
