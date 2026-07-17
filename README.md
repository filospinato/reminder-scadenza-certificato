# Reminder scadenza certificato

Sistema automatico per individuare gli arbitri con certificato medico prossimo alla scadenza e, nelle fasi successive, inviare promemoria individuali tramite SMTP MDaemon.

## Stato del progetto

La versione corrente è un **MVP esclusivamente in dry-run**:

- legge dati anonimi da un file JSON o da una sorgente tabellare simulata;
- legge `nome`, `cognome` ed `email` da colonne separate della stessa riga;
- valida ID, nome, cognome, email, scadenza e stato operativo;
- raccoglie anomalie senza interrompere le altre righe valide;
- esclude integralmente gli ID duplicati;
- seleziona i certificati in scadenza entro una finestra configurabile;
- genera una chiave deterministica anti-duplicazione;
- compone in memoria versioni testo e HTML del promemoria, senza inviarle;
- include un adapter Google Sheets testabile con fake, senza credenziali reali;
- non accede ancora al database reale `Operativo`;
- non contiene credenziali e non invia email.

## Avvio locale

Richiede Python 3.11 o successivo.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
pytest
reminder-certificati --today 2026-07-17 --days 30
```

Il comando usa per impostazione predefinita `examples/arbitri.json` e stampa un riepilogo JSON con righe lette, anomalie, candidati e identificativi deterministici delle notifiche.

## Regola iniziale

Un arbitro è candidato quando:

- è operativo;
- possiede un identificativo univoco;
- possiede nome e cognome;
- possiede un indirizzo email formalmente valido;
- il certificato scade tra oggi e il limite configurato, estremi inclusi;
- non presenta anomalie che rendano ambiguo l'invio.

I certificati già scaduti saranno gestiti in futuro da un promemoria separato.

## Composizione del messaggio

Il modulo `email_templates` produce una versione testo e una HTML senza effettuare connessioni SMTP. L'apertura è vincolata alla forma:

```text
Ciao {{nome}}, ricevi questa mail...
```

`{{nome}}` viene letto direttamente dalla colonna `nome` della stessa riga di `Operativo` che contiene anche `cognome`, `email`, scadenza e stato. Non vengono usati fallback basati sulla prima parola di un nominativo composto.

I placeholder consentiti sono `{{nome}}`, `{{cognome}}`, `{{nome_completo}}`, `{{data_scadenza}}` e `{{giorni_residui}}`.

Placeholder sconosciuti, oggetti con ritorni a capo, valori HTML non sottoposti a escaping e corpi che non rispettano l'apertura concordata vengono rifiutati. Il contratto completo è in [`docs/CONTRATTO_MESSAGGIO.md`](docs/CONTRATTO_MESSAGGIO.md).

## Sorgenti dati

La logica applicativa dipende dal protocollo `SorgenteDati`, non dalla libreria Google. Sono disponibili:

- `SorgenteMemoria`, per test e simulazioni;
- `AdapterGoogleSheets`, che costruisce l'intervallo A1 e usa un lettore iniettato;
- `LettoreGoogleApi`, ponte verso un servizio Google già autenticato;
- `leggi_e_valida`, che collega qualsiasi sorgente alla validazione esistente.

Credenziali, Spreadsheet ID e nome reale della scheda restano fuori dal repository. Architettura, controlli tabellari e privilegi minimi sono descritti in [`docs/SORGENTI_DATI.md`](docs/SORGENTI_DATI.md).

## Contratto dati

Il formato logico e le anomalie previste sono documentati in [`docs/CONTRATTO_DATI.md`](docs/CONTRATTO_DATI.md). Le intestazioni effettive di `Operativo` saranno collegate tramite configurazione.

## Sicurezza

- Nessun dato personale reale deve essere versionato.
- Nessun segreto deve essere salvato nei file del repository.
- `Operativo` sarà accessibile in sola lettura.
- Nome, cognome, email e scadenza devono provenire dalla stessa riga validata.
- L'invio reale resterà disabilitato fino alla validazione esplicita di Google Sheets, registro notifiche, modalità test e SMTP MDaemon.

## Roadmap

La roadmap canonica in dieci passi è in [`ROADMAP.md`](ROADMAP.md); l'avanzamento operativo è tracciato anche nell'issue #1. Il progetto procede per incrementi piccoli, testati e revisionabili tramite pull request draft.
