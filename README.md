# Reminder scadenza certificato

Sistema per individuare gli arbitri con certificato medico prossimo alla scadenza e inviare promemoria individuali tramite SMTP MDaemon.

## Uso quotidiano

L'operatore deve conoscere soltanto tre azioni:

- `INVIO_AUTOMATICO_ATTIVO` nella tab `CONFIG` accende o spegne gli invii programmati;
- **Controlla senza inviare** verifica configurazione, dati, candidati e registro;
- **Invia email di prova** manda al massimo un messaggio al `DESTINATARIO_OVERRIDE`.

Il controllo e la prova funzionano anche quando l'invio automatico è spento. Soltanto la modalità `produzione` richiede `INVIO_AUTOMATICO_ATTIVO=true`.

## Principi operativi

- `Operativo` resta in sola lettura e vengono lette soltanto le otto colonne necessarie;
- il contratto della sorgente è fisso nel codice: tab `Operativo`, intestazioni alla riga 2 e intervallo `A:AS`; l'operatore configura soltanto l'ID dello Spreadsheet;
- le categorie non tenute al certificato vengono ignorate prima dei controlli su email e scadenza; i seriali data nativi di Google Sheets vengono convertiti automaticamente;
- le righe senza data di scadenza vengono ignorate come dati storici non valutabili;
- ID, nome, cognome ed email sono obbligatori soltanto per le persone attive con certificato compreso nella finestra di preavviso; i dati incompleti fuori finestra non generano anomalie;
- `NOTIFICHE` e `ANOMALIE` restano visibili nel foglio amministrativo;
- il test SMTP mantiene il comportamento corrente: usa un candidato reale, sostituisce l'indirizzo con l'override, registra una notifica `TEST_` e invia al massimo un messaggio;
- il limite produttivo resta fissato internamente a 10 messaggi per esecuzione;
- Environment GitHub, WIF/OIDC, registro anti-duplicazione e classificazione degli errori SMTP restano invariati;
- SMTP `PLAIN` resta temporaneamente supportato e protetto da `ALLOW_PLAIN_SMTP=true`.

## Installazione

Richiede Python 3.11 o successivo.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
pytest
```

Per usare Google Sheets:

```bash
python -m pip install -e ".[google]"
```

## Comandi

```bash
reminder-certificati setup-admin --spreadsheet-id ID
reminder-certificati setup-admin --spreadsheet-id ID --apply
reminder-certificati check
reminder-certificati registry-check
reminder-certificati test-smtp
reminder-certificati produzione
```

`setup-admin` riconosce automaticamente un foglio vuoto, uno schema precedente o un foglio già aggiornato. Senza `--apply` mostra l'anteprima; con `--apply` inizializza oppure aggiorna e, quando modifica un foglio esistente, crea prima un backup JSON.

`check` unisce preflight, controllo completo senza invio e revisione aggregata del registro. Non usa SMTP e non richiede che l'invio automatico sia acceso.

## CONFIG

La tab usa tre sole colonne: `chiave`, `valore`, `descrizione`. Le chiavi sono:

- `SCHEMA_VERSION`, gestita dal programma;
- `INVIO_AUTOMATICO_ATTIVO`;
- `GIORNI_PREAVVISO`;
- `DESTINATARIO_OVERRIDE`;
- `OGGETTO_EMAIL`;
- `CORPO_EMAIL`;
- `FIRMA_TESTO`.

`CORPO_EMAIL` contiene il messaggio completo, compreso l'eventuale saluto. Il codice non aggiunge frasi implicite. I placeholder disponibili in oggetto, corpo e firma sono:

```text
{{nome}}
{{cognome}}
{{nome_completo}}
{{data_scadenza}}
{{giorni_residui}}
```

I placeholder anagrafici `{{nome}}`, `{{cognome}}` e `{{nome_completo}}` vengono normalizzati soltanto durante la composizione della mail: gli spazi ripetuti sono uniformati e ogni parte riceve l'iniziale maiuscola, senza modificare i valori nel foglio `Operativo`.

Il valore predefinito inizia con `Ciao {{nome}},`, ma può essere sostituito con qualsiasi formulazione valida direttamente dal foglio.

Durante una migrazione l'invio automatico viene sempre lasciato su `false`. Il limite di invio non è più una decisione dell'operatore.

## Registro

La chiave anti-duplicazione è:

```text
ID_ARBITRO|DATA_SCADENZA|CERTIFICATO_SCADENZA_V1
```

Il registro non conserva nome, cognome o email. Gli stati tecnici restano distinti tra invio in corso, riuscito, ritentabile, permanente e incerto; nei riepiloghi vengono mostrati con etichette comprensibili.

## Produzione

Il modello resta non attivo in `docs/workflows/production.yml.example` e non contiene ancora una schedule. Al go-live verrà aggiunta una sola esecuzione giornaliera dopo i collaudi finali.

Gli invii reali richiedono:

- Environment GitHub `production` protetto;
- `INVIO_AUTOMATICO_ATTIVO=true` nella tab `CONFIG`;
- configurazione Google e SMTP valida.

Non esistono più `PRODUCTION_ENABLED`, `PREPRODUCTION_ENABLED`, `INVII_REALI_ABILITATI`, `ALLOW_EMAIL_DELIVERY` o conferme CLI duplicate.

## Fonti di verità

Per evitare documentazione duplicata:

- `pyproject.toml` contiene la versione corrente del pacchetto;
- `CHANGELOG.md` contiene la cronologia delle versioni;
- `ROADMAP.md` contiene esclusivamente il lavoro ancora aperto;
- `docs/OPERATIONS.md` contiene le procedure ordinarie;
- `docs/DEPLOYMENT_CHECKLIST.md` contiene il percorso di go-live;
- `docs/EMERGENCY.md` contiene le procedure di arresto e incidente.

Le issue coordinano il lavoro ma non duplicano versione, stato o roadmap.

## Guide

- [`docs/OPERATIONS.md`](docs/OPERATIONS.md)
- [`docs/EMERGENCY.md`](docs/EMERGENCY.md)
- [`docs/SCHEMA_FOGLI.md`](docs/SCHEMA_FOGLI.md)
- [`docs/DEPLOYMENT_CHECKLIST.md`](docs/DEPLOYMENT_CHECKLIST.md)
- [`docs/PREFLIGHT_DIAGNOSTICA.md`](docs/PREFLIGHT_DIAGNOSTICA.md)
- [`docs/HANDOFF.md`](docs/HANDOFF.md)
