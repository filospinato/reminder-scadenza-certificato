# Autenticazione Google Cloud senza chiavi permanenti

## Obiettivo

GitHub Actions accederà a Google Sheets tramite Workload Identity Federation (WIF) e OIDC. Il repository non usa file JSON di service account, password, token utente o credenziali ChatGPT.

Il provisioning resta un passaggio controllato. Nessun accesso reale, workflow programmato, lettura di dati personali o invio viene attivato dal solo merge del codice.

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

## Proprietà del foglio amministrativo

Il file amministrativo deve essere creato vuoto dall'amministratore umano. I service account non hanno una normale quota Drive personale e non devono essere usati come proprietari del file. Dopo la creazione:

1. il file resta di proprietà dell'identità umana;
2. viene collocato fuori da cartelle con condivisione ereditata ampia;
3. viene condiviso direttamente con il service account come editor;
4. l'ID viene salvato in `ADMIN_SPREADSHEET_ID`;
5. `reminder-certificati setup-admin --spreadsheet-id ID --apply` trasforma la singola tab vuota nelle quattro tab canoniche.

Non sono richiesti accesso interattivo, Domain-Wide Delegation o chiavi permanenti.

## Variabili GitHub previste

Sono identificatori pubblici da conservare come GitHub Actions Variables, non come segreti:

```text
GCP_PROJECT_ID=<project-id>
GCP_WORKLOAD_IDENTITY_PROVIDER=projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/github-cia/providers/github-actions
GCP_SERVICE_ACCOUNT=reminder-certificati@PROJECT_ID.iam.gserviceaccount.com
OPERATIVO_SPREADSHEET_ID=15_TOwRL3Rk-Df7t-29D0OHa2BNtBx3tBxkZSMbeXA2E
ADMIN_SPREADSHEET_ID=<id del file vuoto creato dall'amministratore>
```

`GOOGLE_SERVICE_ACCOUNT_JSON`, `GOOGLE_APPLICATION_CREDENTIALS_JSON`, `GCP_SERVICE_ACCOUNT_KEY` e variabili equivalenti sono vietate. `GOOGLE_APPLICATION_CREDENTIALS` non viene invece vietata: l'azione WIF la valorizza temporaneamente con il percorso del file effimero generato per quella sola esecuzione.

## Verifica runtime del file ADC

Prima di costruire il client Google Sheets, il runtime legge soltanto la struttura del file indicato da `GOOGLE_APPLICATION_CREDENTIALS` e applica una barriera bloccante:

- il percorso deve essere presente e puntare a un file JSON leggibile;
- il documento deve avere `type: external_account`;
- devono essere presenti `audience`, `subject_token_type` e `credential_source`;
- un documento con `type: service_account` viene rifiutato esplicitamente;
- tipi diversi, file vuoti, troppo grandi, malformati o incompleti vengono rifiutati;
- il contenuto del file, i token e gli identificatori interni non vengono stampati né inseriti nei log.

Questa barriera impedisce che una chiave privata permanente venga accettata accidentalmente attraverso il normale meccanismo Application Default Credentials. Non sostituisce la trust policy IAM/OIDC: aggiunge un controllo locale ulteriore prima di qualsiasi chiamata a Google Sheets.

## Provisioning controllato

1. Creare con l'account umano lo Spreadsheet amministrativo vuoto.
2. Creare il progetto Google Cloud con l'account personale dell'amministratore iniziale, senza attivare servizi a pagamento non necessari.
3. Abilitare Google Sheets API. Drive API non è necessaria al normale runtime basato su condivisione diretta.
4. Creare il service account dedicato senza generare chiavi.
5. Creare un Workload Identity Pool e un provider OIDC con issuer `https://token.actions.githubusercontent.com` e audience predefinita.
6. Non usare il prefisso riservato `gcp-` negli ID di pool o provider.
7. Configurare almeno questo attribute mapping:

```text
google.subject=assertion.sub
attribute.repository_id=assertion.repository_id
attribute.repository_owner_id=assertion.repository_owner_id
attribute.ref=assertion.ref
attribute.workflow_ref=assertion.workflow_ref
```

8. Applicare una attribute condition equivalente a:

```text
assertion.repository_id == '1303804647' &&
assertion.repository_owner_id == '265553127' &&
assertion.ref == 'refs/heads/main'
```

9. Concedere `roles/iam.workloadIdentityUser` sul solo service account al seguente insieme di principal:

```text
principalSet://iam.googleapis.com/projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/POOL_ID/attribute.repository_id/1303804647
```

10. Prima della produzione, restringere ulteriormente il workflow autorizzato tramite `workflow_ref` oppure un GitHub Environment protetto, mantenendo comunque i vincoli su repository, proprietario e branch.
11. Condividere direttamente lo Spreadsheet operativo con l'email del service account come lettore.
12. Condividere direttamente lo Spreadsheet amministrativo con l'email del service account come editor.
13. Non assegnare al service account ruoli generali su Drive: i permessi sui due file derivano dalla loro condivisione diretta.
14. Eseguire la prima prova mediante i workflow manuali su `main`: prima `setup-preview` e `setup-apply`, poi `check`.
15. Prima della produzione aggiungere una seconda identità umana CIA per recupero e documentare trasferimento e revoca degli accessi.

## Esempio di autenticazione

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

Il file temporaneo `gha-creds-*.json` prodotto sul runner è escluso da Git tramite `.gitignore` e viene eliminato con il workspace del job. Non è una chiave privata permanente del service account e supera la verifica runtime perché usa il formato federato `external_account`.

## Environment GitHub

Il job dichiara esplicitamente l'Environment `preproduction`; variabili e segreti SMTP vengono letti dal relativo scope. Non esiste un gate applicativo duplicato: eventuali approvazioni e restrizioni devono essere configurate nelle regole dell'Environment e nella trust policy WIF.

## Verifiche di sicurezza

- il codice valida il formato canonico di provider e service account;
- il codice rifiuta il prefisso WIF riservato `gcp-`;
- la presenza di variabili riconducibili a chiavi JSON permanenti causa un errore bloccante;
- il file ADC viene validato come configurazione federata temporanea prima della costruzione del client Google;
- la trust policy usa gli ID numerici immutabili di repository e proprietario;
- il token è limitato almeno al branch `main` e dovrà essere vincolato al workflow o Environment autorizzato;
- gli identificatori dei fogli non devono essere stampati insieme a righe o dati personali;
- i test automatici usano soltanto identificatori sintetici;
- la lettura iniziale di `Operativo` deve limitarsi a intestazioni e struttura;
- nessun payload reale deve comparire in log, issue o pull request.

## Attivazione reale

Il provisioning IAM/OIDC, la condivisione dei fogli e la valorizzazione dell'Environment richiedono un passaggio controllato e una verifica esplicita. Il workflow di produzione resta un file `.example` non attivo.
