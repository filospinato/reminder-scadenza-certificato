# Contratto degli Environment GitHub

Questo documento elenca i nomi pubblici usati dai workflow. Gli identificatori e le impostazioni non sensibili sono Variables; le credenziali SMTP sono Secrets. Nessun valore reale deve essere inserito nel repository.

## Environment `preproduction`

Variables usate dal workflow manuale:

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

`PREPRODUCTION_ENABLED` deve restare `false` o assente finché Environment, WIF e condivisioni non sono stati verificati.

## Environment `production`

Variables usate dal modello non attivo:

<!-- BEGIN PRODUCTION VARIABLES -->
```text
ADMIN_SPREADSHEET_ID
GCP_PROJECT_ID
GCP_SERVICE_ACCOUNT
GCP_WORKLOAD_IDENTITY_PROVIDER
OPERATIVO_COLUMNS_A1
OPERATIVO_SPREADSHEET_ID
PRODUCTION_ENABLED
SMTP_FROM_NAME
SMTP_REPLY_TO
```
<!-- END PRODUCTION VARIABLES -->

Nel modello produttivo il nome tab `Operativo` e la riga intestazioni `2` sono fissati nel file. `PRODUCTION_ENABLED` è l'unico acknowledgement statico del workflow; le protezioni vive restano Environment, CONFIG, kill switch e consenso all'invio.

## Secrets SMTP

Entrambi i workflow usano questi Secrets, disponibili soltanto nello step SMTP:

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

`SMTP_FROM_NAME` e `SMTP_REPLY_TO` non sono credenziali e restano Variables. Username e password non devono essere trasformati in Variables di job né riportati nei log.

## Regola di modifica

Quando un workflow introduce un nuovo nome, questo documento deve essere aggiornato dopo aver verificato che la classificazione Variable/Secret e lo scope dello step siano corretti.
