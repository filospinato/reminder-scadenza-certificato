# Contratto degli Environment GitHub

Questo documento è la fonte di verità per i nomi delle GitHub Actions Variables e dei Secrets usati dai workflow del progetto. Gli identificatori pubblici e le impostazioni non sensibili devono essere Variables; le credenziali SMTP devono essere Secrets. Nessun valore reale deve essere inserito nel repository.

## Environment `preproduction`

Il workflow manuale `.github/workflows/manual-preproduction.yml` usa esattamente queste Variables:

<!-- BEGIN PREPRODUCTION VARIABLES -->
```text
ADMIN_SPREADSHEET_ID
GCP_PROJECT_ID
GCP_SERVICE_ACCOUNT
GCP_WORKLOAD_IDENTITY_PROVIDER
OPERATIVO_COLUMNS_A1
OPERATIVO_HEADER_ROW
OPERATIVO_SHEET_NAME
OPERATIVO_SPREADSHEET_ID
PREPRODUCTION_ENABLED
SMTP_FROM_NAME
SMTP_REPLY_TO
```
<!-- END PREPRODUCTION VARIABLES -->

`PREPRODUCTION_ENABLED` deve restare `false` o assente finché Environment, WIF e condivisioni non sono stati verificati. `OPERATIVO_COLUMNS_A1` delimita l'intervallo di colonne letto; gli altri identificatori Google sono pubblici ma non devono essere stampati insieme a righe o dati personali.

## Environment `production`

Il modello non attivo `docs/workflows/production.yml.example` usa esattamente queste Variables:

<!-- BEGIN PRODUCTION VARIABLES -->
```text
ADMIN_SPREADSHEET_ID
GCP_PROJECT_ID
GCP_SERVICE_ACCOUNT
GCP_WORKLOAD_IDENTITY_PROVIDER
OPERATIVO_COLUMNS_A1
OPERATIVO_SPREADSHEET_ID
PRODUCTION_ENABLED
PRODUCTION_WORKFLOW_APPROVED
SMTP_FROM_NAME
SMTP_REPLY_TO
```
<!-- END PRODUCTION VARIABLES -->

Nel modello produttivo il nome tab `Operativo` e la riga intestazioni `2` sono fissati nel file, mentre gli ID e l'intervallo di colonne restano Variables. `PRODUCTION_ENABLED` e `PRODUCTION_WORKFLOW_APPROVED` sono acknowledgement distinti e non sostituiscono le protezioni dell'Environment o il consenso applicativo.

## Secrets SMTP

Entrambi i workflow fanno riferimento esattamente ai seguenti Secrets, disponibili soltanto nello step SMTP:

<!-- BEGIN SMTP SECRETS -->
```text
SMTP_FROM
SMTP_HOST
SMTP_PASSWORD
SMTP_PORT
SMTP_SECURITY
SMTP_USERNAME
```
<!-- END SMTP SECRETS -->

`SMTP_FROM_NAME` e `SMTP_REPLY_TO` non sono credenziali e restano Variables. Password, username e parametri di connessione riservati non devono essere trasformati in Variables di job, riportati nei log o documentati con valori reali.

## Regola di modifica

Ogni aggiunta, rimozione o rinomina nei workflow deve aggiornare contestualmente questo documento e il test `tests/test_github_environment_contract.py`. Un fallimento del test non va risolto aggiornando automaticamente l'elenco: occorre verificare prima che la classificazione Variable/Secret e lo scope dello step siano ancora corretti.