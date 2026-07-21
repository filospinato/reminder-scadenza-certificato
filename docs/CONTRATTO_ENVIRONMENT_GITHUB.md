# Contratto degli Environment GitHub

Questo documento elenca i nomi pubblici usati dai workflow. Gli identificatori e le impostazioni non sensibili sono Variables; le credenziali SMTP sono Secrets. Nessun valore reale deve essere inserito nel repository.

## Environment `preproduction`

Variables usate dai workflow manuali ordinario e di manutenzione:

<!-- BEGIN PREPRODUCTION VARIABLES -->
```text
ALLOW_PLAIN_SMTP
ADMIN_SPREADSHEET_ID
GCP_PROJECT_ID
GCP_SERVICE_ACCOUNT
GCP_WORKLOAD_IDENTITY_PROVIDER
OPERATIVO_SPREADSHEET_ID
SMTP_REPLY_TO
```
<!-- END PREPRODUCTION VARIABLES -->

Il foglio `Operativo` segue il contratto canonico incorporato nel programma: tab `Operativo`, intestazioni alla riga 2 e intervallo `A:AS`. Questi dettagli non sono Variables operative e non richiedono configurazione manuale.

L'avvio manuale e l'Environment `preproduction` sono l'unica autorizzazione richiesta. Non esistono ulteriori interruttori GitHub per preflight, setup o collaudi sintetici.

## Environment `production`

Variables usate dal modello non attivo:

<!-- BEGIN PRODUCTION VARIABLES -->
```text
ALLOW_PLAIN_SMTP
ADMIN_SPREADSHEET_ID
GCP_PROJECT_ID
GCP_SERVICE_ACCOUNT
GCP_WORKLOAD_IDENTITY_PROVIDER
OPERATIVO_SPREADSHEET_ID
SMTP_REPLY_TO
```
<!-- END PRODUCTION VARIABLES -->

La produzione usa l'Environment protetto e l'unico interruttore `INVIO_AUTOMATICO_ATTIVO` nella tab `CONFIG`. Non richiede ulteriori acknowledgement o interruttori duplicati.

## Secrets SMTP

Il workflow ordinario di prova e il modello produttivo usano questi Secrets, disponibili soltanto nello step SMTP:

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

`SMTP_REPLY_TO` non è una credenziale e resta una Variable. Anche `ALLOW_PLAIN_SMTP` è una Variable: deve valere `true` soltanto se MDaemon richiede esplicitamente il trasporto senza TLS e il canale di rete è stato approvato. Il nome del mittente, il timeout e il CID del logo usano default applicativi stabili. Username e password non devono essere trasformati in Variables di job né riportati nei log.

## Regola di modifica

Quando un workflow introduce un nuovo nome, questo documento deve essere aggiornato dopo aver verificato la classificazione Variable/Secret e lo scope dello step.
