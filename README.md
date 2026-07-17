# Reminder scadenza certificato

Sistema automatico per individuare gli arbitri con certificato medico prossimo alla scadenza e, nelle fasi successive, inviare promemoria individuali tramite SMTP MDaemon.

## Stato del progetto

La versione corrente **0.10.0** resta esclusivamente in `dry-run` e definisce anche il contratto completo dello Spreadsheet amministrativo separato:

- legge dati anonimi da un file JSON o da una sorgente tabellare simulata;
- legge `nome`, `cognome` ed `email` da colonne separate della stessa riga;
- valida ID, nome, cognome, email, scadenza e stato operativo;
- raccoglie anomalie senza interrompere le altre righe valide;
- esclude integralmente gli ID duplicati;
- seleziona i certificati in scadenza entro una finestra configurabile;
- genera una chiave deterministica anti-duplicazione;
- modella il registro con stati `SENDING`, `SENT`, `FAILED_RETRYABLE` e `UNKNOWN_REVIEW_REQUIRED`;
- impedisce prenotazioni concorrenti duplicate nel registro in memoria;
- include adapter Google Sheets testati con fake per lettura, append e update;
- supporta la struttura verificata di `Operativo`, con intestazioni in riga 2;
- definisce le tab `CONFIG`, `NOTIFICHE`, `DASHBOARD` e `ANOMALIE`;
- inizializza configurazione e dashboard in stato disattivato e senza dati personali;
- compone in memoria versioni testo e HTML del promemoria, senza inviarle;
- valida gli identificatori pubblici di Workload Identity Federation;
- rifiuta variabili riconducibili a chiavi JSON permanenti;
- non accede ancora al database reale `Operativo` e non crea o modifica Spreadsheet reali.

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

## Registro anti-duplicazione

Il modulo `registry` definisce il ciclo di vita della notifica usando la chiave:

```text
ID_ARBITRO|DATA_SCADENZA|TIPO_NOTIFICA
```

La prenotazione crea `SENDING` prima del futuro contatto SMTP. `SENT`, `SENDING` e `UNKNOWN_REVIEW_REQUIRED` bloccano ulteriori tentativi automatici; soltanto `FAILED_RETRYABLE` può tornare a `SENDING`. `RegistroMemoria` rende atomica la prenotazione all'interno del singolo processo.

Il modulo `admin_store` converte candidato e stato in una `RigaNotifica` completa. `ArchivioNotificheMemoria` simula il registro tabellare, mentre `ArchivioNotificheGoogleSheets` usa un trasporto iniettato per:

1. leggere intestazioni e righe della tab `NOTIFICHE`;
2. cercare la chiave esatta;
3. aggiungere una nuova riga soltanto se la chiave è assente;
4. aggiornare la riga esistente soltanto se la chiave è presente una volta;
5. bloccare ogni scrittura quando il foglio è ambiguo o non conforme allo schema.

Il ponte `TrasportoNotificheGoogleApi` è pronto per un servizio Google già autenticato, ma non costruisce credenziali e non viene ancora usato contro Spreadsheet reali. La ricerca seguita da scrittura non è una transazione atomica di Google Sheets: in produzione le esecuzioni saranno anche serializzate tramite `concurrency` di GitHub Actions.

## Foglio amministrativo

Il modulo `admin_schema` definisce lo Spreadsheet canonico `Reminder certificati CIA Lazio — Gestione` e le quattro tab, nell'ordine:

```text
CONFIG | NOTIFICHE | DASHBOARD | ANOMALIE
```

La configurazione iniziale mantiene `SISTEMA_ATTIVO=false`, `INVII_REALI_ABILITATI=false`, `MODALITA_TEST=true` e `KILL_SWITCH=true`. `NOTIFICHE` e `ANOMALIE` nascono senza righe dati; `DASHBOARD` contiene soltanto metriche sintetiche a zero.

Il codice valida nome del file, ordine delle tab, intestazioni duplicate e larghezza delle righe. Non crea ancora il file su Google Drive. Il contratto completo è in [`docs/SCHEMA_FOGLI.md`](docs/SCHEMA_FOGLI.md).

## Composizione del messaggio

Il modulo `email_templates` produce una versione testo e una HTML senza effettuare connessioni SMTP. L'apertura è vincolata alla forma:

```text
Ciao {{nome}}, ricevi questa mail...
```

`{{nome}}` viene letto direttamente dalla colonna `nome` della stessa riga di `Operativo` che contiene anche `cognome`, `email`, scadenza e stato. Non vengono usati fallback basati sulla prima parola di un nominativo composto.

I placeholder consentiti sono `{{nome}}`, `{{cognome}}`, `{{nome_completo}}`, `{{data_scadenza}}` e `{{giorni_residui}}`.

Placeholder sconosciuti, oggetti con ritorni a capo, valori HTML non sottoposti a escaping e corpi che non rispettano l'apertura concordata vengono rifiutati. Il contratto completo è in [`docs/CONTRATTO_MESSAGGIO.md`](docs/CONTRATTO_MESSAGGIO.md).

## Sorgenti dati

La logica applicativa dipende da protocolli, non direttamente dalla libreria Google. Sono disponibili:

- `SorgenteMemoria`, per test e simulazioni;
- `AdapterGoogleSheets`, per la lettura di `Operativo` tramite un lettore iniettato;
- `LettoreGoogleApi`, ponte di sola lettura verso un servizio Google già autenticato;
- `ArchivioNotificheGoogleSheets`, per il registro amministrativo;
- `TrasportoNotificheMemoria`, fake di lettura, append e update;
- `TrasportoNotificheGoogleApi`, ponte di lettura e scrittura verso un servizio Google già autenticato;
- `leggi_e_valida`, che collega qualsiasi sorgente degli arbitri alla validazione esistente.

La riga delle intestazioni è configurabile. Per `Operativo` è fissata a 2 e le anomalie mantengono il numero di riga originale del foglio.

## Autenticazione Google

Il modulo `google_auth` valida soltanto gli identificatori pubblici necessari a Workload Identity Federation. Il repository non accetta chiavi JSON permanenti.

Il futuro collegamento GitHub–Google userà token OIDC temporanei, un service account dedicato e una trust policy limitata al repository, al proprietario e al branch autorizzato. Il provisioning non è ancora stato applicato.

Il runbook completo è in [`docs/AUTENTICAZIONE_GOOGLE.md`](docs/AUTENTICAZIONE_GOOGLE.md).

## Contratto dati

Il formato logico e le anomalie previste sono documentati in [`docs/CONTRATTO_DATI.md`](docs/CONTRATTO_DATI.md). Le intestazioni reali vengono collegate tramite configurazione e non tramite valori personali versionati.

## Sicurezza

- Nessun dato personale reale deve essere versionato.
- Nessun segreto o chiave permanente deve essere salvato nel repository.
- `Operativo` sarà accessibile in sola lettura.
- Il foglio amministrativo riceverà accesso in scrittura separato e limitato.
- Il foglio iniziale mantiene invii reali disabilitati e kill switch attivo.
- Nome, cognome, email e scadenza devono provenire dalla stessa riga validata.
- Gli esiti incerti non vengono ritentati automaticamente.
- Chiavi duplicate o schema errato in `NOTIFICHE` bloccano la scrittura.
- L'invio reale resterà disabilitato fino alla validazione esplicita di Google Sheets, modalità test e SMTP MDaemon.

## Roadmap

La roadmap canonica in dieci passi è in [`ROADMAP.md`](ROADMAP.md); l'avanzamento operativo è tracciato anche nell'issue #1. Il progetto procede per incrementi piccoli, testati e revisionabili tramite pull request.
