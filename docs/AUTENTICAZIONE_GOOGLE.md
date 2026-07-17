# Autenticazione Google Cloud senza chiavi permanenti

## Obiettivo

GitHub Actions accederà in futuro a Google Sheets tramite Workload Identity Federation (WIF) e OIDC. Il repository non usa file JSON di service account, password, token utente o credenziali ChatGPT.

Questa fase prepara soltanto contratto e provisioning. Non abilita accesso reale, workflow programmati, letture di dati personali o scritture su Spreadsheet.

## Identità e risorse

- repository autorizzato: `filospinato/reminder-scadenza-certificato`;
- service account dedicato consigliato: `reminder-certificati`;
- progetto Google Cloud con nome riconducibile al sistema CIA Lazio;
- sorgente operativa: Spreadsheet `CIA Lazio 25/26 - Automatico`, tab `Operativo`, sola lettura;
- registro separato: `Reminder certificati CIA Lazio — Gestione`, modifica limitata;
- nessun ruolo generale su Drive, Gmail, Calendar o dominio Google Workspace.

## Variabili GitHub previste

Sono identificatori pubblici, non segreti:

```text
GCP_WORKLOAD_IDENTITY_PROVIDER=projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/github-cia/providers/github-actions
GCP_SERVICE_ACCOUNT=reminder-certificati@PROJECT_ID.iam.gserviceaccount.com
OPERATIVO_SPREADSHEET_ID=15_TOwRL3Rk-Df7t-29D0OHa2BNtBx3tBxkZSMbeXA2E
OPERATIVO_SHEET_NAME=Operativo
OPERATIVO_HEADER_ROW=2
ADMIN_SPREADSHEET_ID=<da valorizzare dopo la creazione controllata>
```

`GOOGLE_SERVICE_ACCOUNT_JSON`, `GCP_SERVICE_ACCOUNT_KEY` e variabili equivalenti sono vietate.

## Provisioning controllato

1. Creare il progetto Google Cloud con fatturazione non necessaria per l'uso previsto delle API entro le quote gratuite.
2. Abilitare esclusivamente Google Sheets API e, se necessario alla creazione iniziale, Google Drive API.
3. Creare il service account dedicato senza generare chiavi.
4. Creare un Workload Identity Pool e un provider OIDC con issuer `https://token.actions.githubusercontent.com`.
5. Configurare l'attribute mapping almeno per `google.subject`, `attribute.repository`, `attribute.ref` e `attribute.workflow`.
6. Limitare l'attribute condition a `attribute.repository == 'filospinato/reminder-scadenza-certificato'`.
7. Concedere `roles/iam.workloadIdentityUser` sul solo service account al principalSet del repository. Prima della produzione restringere ulteriormente a branch, environment o workflow autorizzato.
8. Condividere direttamente lo Spreadsheet operativo con l'email del service account come lettore.
9. Condividere direttamente lo Spreadsheet amministrativo separato con l'email del service account come editor.
10. Non collocare il foglio amministrativo in cartelle con condivisione ereditata ampia.
11. Eseguire una prima prova soltanto su Spreadsheet sintetico e con workflow manuale.
12. Prima della produzione aggiungere una seconda identità umana CIA per recupero e documentare revoca e trasferimento.

## Esempio di autenticazione futura

Da inserire in un workflow solo dopo verifica esplicita della configurazione IAM:

```yaml
permissions:
  contents: read
  id-token: write

steps:
  - uses: actions/checkout@v4
  - uses: google-github-actions/auth@v2
    with:
      workload_identity_provider: ${{ vars.GCP_WORKLOAD_IDENTITY_PROVIDER }}
      service_account: ${{ vars.GCP_SERVICE_ACCOUNT }}
```

L'esempio non viene aggiunto come workflow attivo in questa fase, così nessuna federazione o risorsa reale può essere utilizzata accidentalmente.

## Verifiche di sicurezza

- il codice valida il formato canonico di provider e service account;
- la presenza di variabili riconducibili a chiavi JSON permanenti causa un errore bloccante;
- gli identificatori dei fogli non devono essere stampati insieme a righe o dati personali;
- i test automatici usano soltanto identificatori sintetici;
- la lettura iniziale di `Operativo` deve limitarsi a intestazioni e struttura;
- nessun payload reale deve comparire in log, issue o pull request.
