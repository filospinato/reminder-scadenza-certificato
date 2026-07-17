# Autenticazione Google Cloud senza chiavi permanenti

## Obiettivo

GitHub Actions accederà in futuro a Google Sheets tramite Workload Identity Federation (WIF) e OIDC. Il repository non usa file JSON di service account, password, token utente o credenziali ChatGPT.

Questa fase prepara soltanto il contratto software e il runbook. Non abilita accesso reale, workflow programmati, letture di dati personali o scritture su Spreadsheet.

## Identità e risorse

- repository autorizzato: `filospinato/reminder-scadenza-certificato`;
- ID numerico immutabile del repository: `1303804647`;
- ID numerico immutabile del proprietario GitHub: `265553127`;
- branch previsto per le future esecuzioni autorizzate: `main`;
- service account dedicato consigliato: `reminder-certificati`;
- progetto Google Cloud con nome riconducibile al sistema CIA Lazio;
- sorgente operativa: Spreadsheet `CIA Lazio 25/26 - Automatico`, tab `Operativo`, sola lettura;
- registro separato: `Reminder certificati CIA Lazio — Gestione`, modifica limitata;
- nessun ruolo generale su Drive, Gmail, Calendar o dominio Google Workspace.

Gli ID numerici GitHub sono preferiti nelle condizioni di trust perché non possono essere riutilizzati in seguito a rinomina o cancellazione dell'account o del repository.

## Variabili GitHub previste

Sono identificatori pubblici da conservare come GitHub Actions Variables, non come segreti:

```text
GCP_PROJECT_ID=<project-id>
GCP_WORKLOAD_IDENTITY_PROVIDER=projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/github-cia/providers/github-actions
GCP_SERVICE_ACCOUNT=reminder-certificati@PROJECT_ID.iam.gserviceaccount.com
OPERATIVO_SPREADSHEET_ID=15_TOwRL3Rk-Df7t-29D0OHa2BNtBx3tBxkZSMbeXA2E
OPERATIVO_SHEET_NAME=Operativo
OPERATIVO_HEADER_ROW=2
ADMIN_SPREADSHEET_ID=<da valorizzare dopo la creazione controllata>
```

`GOOGLE_SERVICE_ACCOUNT_JSON`, `GOOGLE_APPLICATION_CREDENTIALS_JSON`, `GCP_SERVICE_ACCOUNT_KEY` e variabili equivalenti sono vietate. `GOOGLE_APPLICATION_CREDENTIALS` non viene invece vietata: l'azione WIF può valorizzarla temporaneamente nel runner indicando il file effimero generato per quella sola esecuzione.

## Provisioning controllato

1. Creare il progetto Google Cloud con l'account personale dell'amministratore iniziale, senza attivare servizi a pagamento non necessari.
2. Abilitare Google Sheets API e usare Google Drive API soltanto se necessaria alla creazione o gestione iniziale del foglio amministrativo.
3. Creare il service account dedicato senza generare chiavi.
4. Creare un Workload Identity Pool e un provider OIDC con issuer `https://token.actions.githubusercontent.com` e audience predefinita.
5. Non usare il prefisso riservato `gcp-` negli ID di pool o provider.
6. Configurare almeno questo attribute mapping:

```text
google.subject=assertion.sub
attribute.repository_id=assertion.repository_id
attribute.repository_owner_id=assertion.repository_owner_id
attribute.ref=assertion.ref
attribute.workflow_ref=assertion.workflow_ref
```

7. Applicare una attribute condition equivalente a:

```text
assertion.repository_id == '1303804647' &&
assertion.repository_owner_id == '265553127' &&
assertion.ref == 'refs/heads/main'
```

8. Concedere `roles/iam.workloadIdentityUser` sul solo service account al seguente insieme di principal:

```text
principalSet://iam.googleapis.com/projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/POOL_ID/attribute.repository_id/1303804647
```

9. Prima della produzione, restringere ulteriormente il workflow autorizzato tramite `workflow_ref` oppure un GitHub Environment protetto, mantenendo comunque i vincoli su repository, proprietario e branch.
10. Condividere direttamente lo Spreadsheet operativo con l'email del service account come lettore.
11. Condividere direttamente lo Spreadsheet amministrativo separato con l'email del service account come editor.
12. Non assegnare al service account ruoli generali su Drive: i permessi sui due file derivano dalla loro condivisione diretta.
13. Non collocare il foglio amministrativo in cartelle con condivisione ereditata ampia.
14. Eseguire la prima prova soltanto su uno Spreadsheet sintetico e mediante un workflow manuale su `main`.
15. Prima della produzione aggiungere una seconda identità umana CIA per recupero e documentare trasferimento e revoca degli accessi.

## Esempio di autenticazione futura

Da inserire in un workflow soltanto dopo verifica esplicita della configurazione IAM:

```yaml
permissions:
  contents: read
  id-token: write

steps:
  - uses: actions/checkout@v4

  - id: auth
    uses: google-github-actions/auth@v3
    with:
      project_id: ${{ vars.GCP_PROJECT_ID }}
      workload_identity_provider: ${{ vars.GCP_WORKLOAD_IDENTITY_PROVIDER }}
      service_account: ${{ vars.GCP_SERVICE_ACCOUNT }}
      create_credentials_file: true
```

Il file temporaneo `gha-creds-*.json` prodotto sul runner è escluso da Git tramite `.gitignore` e deve essere eliminato automaticamente con il workspace del job. Non è una chiave privata permanente del service account.

L'esempio non viene aggiunto come workflow attivo in questa fase, così nessuna federazione o risorsa reale può essere utilizzata accidentalmente.

## Verifiche di sicurezza

- il codice valida il formato canonico di provider e service account;
- il codice rifiuta il prefisso WIF riservato `gcp-`;
- la presenza di variabili riconducibili a chiavi JSON permanenti causa un errore bloccante;
- la trust policy usa gli ID numerici immutabili di repository e proprietario;
- il token è limitato almeno al branch `main` e dovrà essere vincolato al workflow o environment autorizzato;
- gli identificatori dei fogli non devono essere stampati insieme a righe o dati personali;
- i test automatici usano soltanto identificatori sintetici;
- la lettura iniziale di `Operativo` deve limitarsi a intestazioni e struttura;
- nessun payload reale deve comparire in log, issue o pull request.

## Attivazione reale

Il provisioning IAM/OIDC, la condivisione dei fogli e l'aggiunta del workflow autenticato richiedono un passaggio controllato e una verifica esplicita. Il merge di questo documento non autorizza né esegue tali operazioni.
