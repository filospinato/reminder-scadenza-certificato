# Reminder scadenza certificato

Sistema automatico per individuare gli arbitri con certificato medico prossimo alla scadenza e, nelle fasi successive, inviare promemoria individuali tramite SMTP MDaemon.

## Stato del progetto

La versione corrente è un **MVP esclusivamente in dry-run**:

- legge dati anonimi da un file JSON;
- valida ID, nominativo, email, scadenza e stato operativo;
- raccoglie anomalie senza interrompere le altre righe valide;
- esclude integralmente gli ID duplicati;
- seleziona i certificati in scadenza entro una finestra configurabile;
- genera una chiave deterministica anti-duplicazione;
- non accede ancora a Google Sheets;
- non contiene credenziali e non invia email.

## Avvio locale

Richiede Python 3.11 o successivo.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e "[dev]"
pytest
reminder-certificati --today 2026-07-17 --days 30
```

Il comando usa per impostazione predefinita `examples/arbitri.json` e stampa un riepilogo JSON con:

- righe lette e record validi;
- righe vuote ignorate;
- anomalie con numero di riga, codice, campo e messaggio;
- candidati che riceverebbero la notifica;
- identificativo deterministico della notifica.

## Regola iniziale

Un arbitro è candidato quando:

- è operativo;
- possiede un identificativo univoco;
- possiede un indirizzo email formalmente valido;
- il certificato scade tra oggi e il limite configurato, estremi inclusi;
- non presenta anomalie che rendano ambiguo l'invio.

I certificati già scaduti saranno gestiti in futuro da un promemoria separato.

## Contratto dati

Il formato logico e le anomalie previste sono documentati in [`docs/CONTRATTO_DATI.md`](docs/CONTRATTO_DATI.md). Le intestazioni reali di `Operativo` saranno collegate tramite configurazione e non verranno inventate nel codice.

## Sicurezza

- Nessun dato personale reale deve essere versionato.
- Nessun segreto deve essere salvato nei file del repository.
- `Operativo` sarà accessibile in sola lettura.
- L'invio reale resterà disabilitato fino alla validazione esplicita di Google Sheets, registro notifiche, modalità test e SMTP MDaemon.

## Roadmap

La roadmap canonica in dieci passi è in [`ROADMAP.md`](ROADMAP.md); l'avanzamento operativo è tracciato anche nell'issue #1. Il progetto procede per incrementi piccoli, testati e revisionabili tramite pull request draft.
