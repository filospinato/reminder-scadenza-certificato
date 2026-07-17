# Reminder scadenza certificato

Sistema automatico per individuare gli arbitri con certificato medico prossimo alla scadenza e, nelle fasi successive, inviare promemoria individuali tramite SMTP MDaemon.

## Stato del progetto

La versione corrente è un **MVP esclusivamente in dry-run**:

- legge dati anonimi da un file JSON;
- seleziona i certificati in scadenza entro una finestra configurabile;
- genera una chiave deterministica anti-duplicazione;
- non accede ancora a Google Sheets;
- non contiene credenziali;
- non invia alcuna email.

## Avvio locale

Richiede Python 3.11 o successivo.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
pytest
reminder-certificati --today 2026-07-17 --days 30
```

Il comando usa per impostazione predefinita `examples/arbitri.json` e stampa un riepilogo JSON in modalità `dry-run`.

## Regola iniziale

Un arbitro è candidato quando:

- è attivo;
- possiede un indirizzo email formalmente valido;
- il certificato scade tra oggi e il limite configurato, estremi inclusi.

I certificati già scaduti saranno gestiti in futuro da un promemoria separato.

## Sicurezza

- Nessun dato personale reale deve essere versionato.
- Nessun segreto deve essere salvato nei file del repository.
- L'invio reale resterà disabilitato fino alla validazione esplicita di Google Sheets, registro notifiche, modalità test e SMTP MDaemon.

## Roadmap

La roadmap operativa è tracciata nell'issue #1. Il progetto avanzerà per incrementi piccoli, testati e revisionabili tramite pull request.
