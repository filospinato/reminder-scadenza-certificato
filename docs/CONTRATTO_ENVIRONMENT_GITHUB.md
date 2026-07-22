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
SMTP_FROM
SMTP_HOST
SMTP_PORT
SMTP_REPLY_TO
SMTP_SECURITY
SMTP_USERNAME
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
SMTP_FROM
SMTP_HOST
SMTP_PORT
SMTP_REPLY_TO
SMTP_SECURITY
SMTP_USERNAME
```
<!-- END PRODUCTION VARIABLES -->

La produzione usa l'Environment protetto e l'unico interruttore `INVIO_AUTOMATICO_ATTIVO` nella tab `CONFIG`. Non richiede ulteriori acknowledgement o interruttori duplicati.

## Secrets SMTP

Il workflow ordinario di prova e il modello produttivo usano questi Secrets, disponibili soltanto nello step SMTP:

<!-- BEGIN SMTP SECRETS -->
```text
SMTP_PASSWORD
```
<!-- END SMTP SECRETS -->

Soltanto `SMTP_PASSWORD` è una credenziale e resta un Secret. Host, porta,
sicurezza, mittente, Reply-To e username sono impostazioni non sensibili e
restano Variables limitate allo specifico Environment; il workflow le espone
soltanto nello step SMTP. `ALLOW_PLAIN_SMTP` deve valere `true` esclusivamente
se MDaemon richiede il trasporto senza TLS e il canale di rete è stato
approvato. Il nome del mittente e il timeout usano default applicativi stabili;
logo e CID della firma sono inclusi nel codice. Nessun valore SMTP deve essere
riportato nei log.

## Regola di modifica

Quando un workflow introduce un nuovo nome, questo documento deve essere aggiornato dopo aver verificato la classificazione Variable/Secret e lo scope dello step.
