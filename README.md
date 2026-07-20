# Reminder scadenza certificato

Sistema per individuare gli arbitri con certificato medico prossimo alla scadenza e inviare promemoria individuali tramite SMTP MDaemon.

## Principi operativi

- `Operativo` è sempre letto in sola lettura e soltanto nelle colonne necessarie;
- il foglio amministrativo contiene CONFIG, registro, dashboard e anomalie;
- `AUTOMAZIONE_ATTIVA` abilita l'elaborazione;
- `INVII_REALI_ABILITATI` abilita separatamente gli invii agli indirizzi reali;
- il test SMTP usa esclusivamente `DESTINATARIO_OVERRIDE` e richiede doppia conferma;
- la produzione richiede Environment protetto e `PRODUCTION_ENABLED=true`;
- credenziali Google permanenti e dati personali nei log sono rifiutati.

## Installazione

Richiede Python 3.11 o successivo.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
pytest
```

Per i comandi Google:

```bash
python -m pip install -e ".[google]"
```

## Comando unico

```bash
reminder-certificati init-admin --spreadsheet-id ID
reminder-certificati migrate-admin --spreadsheet-id ID
reminder-certificati migrate-admin --spreadsheet-id ID --apply --confirm-migration
reminder-certificati preflight
ALLOW_SYNTHETIC_REGISTRY_WRITE=true reminder-certificati registry-check --confirm-synthetic-write
reminder-certificati review-registry
reminder-certificati dry-run
ALLOW_EMAIL_DELIVERY=true reminder-certificati test-smtp --confirm-email-delivery
PRODUCTION_ENABLED=true reminder-certificati produzione
```

`migrate-admin` opera in anteprima senza `--apply`. L'applicazione richiede anche `--confirm-migration`, salva un backup JSON e lascia disattivati sia `AUTOMAZIONE_ATTIVA` sia `INVII_REALI_ABILITATI`.

`preflight` verifica risorse, tab, intestazioni, versione dello schema e valori funzionali della CONFIG senza leggere righe anagrafiche di `Operativo`, scrivere celle o usare SMTP.

`review-registry` restituisce soltanto conteggi aggregati degli stati che richiedono attenzione.

## CONFIG

Le chiavi funzionali sono:

- `SCHEMA_VERSION`, gestita dal programma;
- `AUTOMAZIONE_ATTIVA`;
- `INVII_REALI_ABILITATI`;
- `GIORNI_PREAVVISO`;
- `LIMITE_INVII_PER_ESECUZIONE`;
- `DESTINATARIO_OVERRIDE`;
- `OGGETTO_EMAIL`;
- `CORPO_EMAIL`;
- `FIRMA_TESTO`.

Con `AUTOMAZIONE_ATTIVA=false`, il runtime termina prima di leggere le righe operative e prima di inizializzare SMTP.

## Registro e codici di uscita

La chiave anti-duplicazione è:

```text
ID_ARBITRO|DATA_SCADENZA|CERTIFICATO_SCADENZA_V1
```

Il registro non conserva nome, cognome o email. Gli stati distinguono invii in corso, riusciti, ritentabili, permanenti ed esiti incerti da revisionare.

- `0`: esecuzione regolare o sistema disattivato;
- `2`: errore operativo o registro da revisionare;
- `3`: stato `ATTENZIONE`;
- `4`: stato `REVISIONE_RICHIESTA`.

## Produzione

Il modello schedulato resta in `docs/workflows/production.yml.example` finché il go-live non è autorizzato. Gli invii reali richiedono contemporaneamente:

- Environment GitHub `production` protetto;
- `PRODUCTION_ENABLED=true`;
- `AUTOMAZIONE_ATTIVA=true`;
- `INVII_REALI_ABILITATI=true`;
- configurazione Google e SMTP valida.

`ALLOW_EMAIL_DELIVERY` e `--confirm-email-delivery` appartengono soltanto al test SMTP manuale e non al workflow schedulato.

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
