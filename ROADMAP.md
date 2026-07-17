# Roadmap

Il progetto segue il contratto funzionale concordato. Il codice pre-produzione è implementato, ma l'attivazione reale richiede ancora risorse, permessi, contenuti e collaudi esterni.

1. [x] Repository Python, test, CI e documentazione di base.
2. [ ] GitHub Actions programmata una o due volte al giorno, oltre all'avvio manuale.
   - [x] workflow manuale pre-produzione con WIF, environment e permessi minimi;
   - [x] workflow disabilitato per default tramite `PREPRODUCTION_ENABLED`;
   - [x] `concurrency` senza sovrapposizioni;
   - [x] modello di produzione schedulato conservato come `.example` non attivo;
   - [ ] creazione degli environment e valorizzazione di Variables/Secrets;
   - [ ] attivazione del workflow di produzione dopo autorizzazione finale.
3. [ ] Lettura di `Operativo` tramite Google Sheets API e service account a privilegi minimi.
   - [x] protocollo, adapter, conversione e validazione strutturale;
   - [x] supporto alle intestazioni di `Operativo` in riga 2;
   - [x] mappatura delle intestazioni reali;
   - [x] comando `check-headers` limitato alla sola riga delle intestazioni;
   - [x] factory Google basata su ADC temporanee prodotte da WIF;
   - [x] runbook di provisioning, trust policy e privilegi minimi;
   - [ ] provisioning reale di progetto, pool, provider e service account;
   - [ ] condivisione diretta in sola lettura;
   - [ ] esecuzione reale di `check-headers`;
   - [ ] dry-run controllato su righe reali con output aggregato.
4. [x] Validazione di ID, nome, cognome, email, scadenza e stato; anomalie e duplicati esclusi in sicurezza.
5. [ ] Controllo della finestra di scadenza e del registro anti-duplicazione.
   - [x] finestra configurabile, estremi inclusi, con scaduti esclusi;
   - [x] chiave deterministica `ID_ARBITRO|DATA_SCADENZA|TIPO_NOTIFICA`;
   - [x] prenotazione preventiva `SENDING`;
   - [x] registro persistente sopra `NOTIFICHE`;
   - [x] retry soltanto da `FAILED_RETRYABLE`;
   - [x] blocco automatico di `SENT`, `SENDING` e `UNKNOWN_REVIEW_REQUIRED`;
   - [x] serializzazione prevista nei workflow;
   - [ ] prova di persistenza e concorrenza su Spreadsheet sintetico.
6. [x] Stati `SENDING`, `SENT`, `FAILED_RETRYABLE`, `UNKNOWN_REVIEW_REQUIRED` e transizioni sicure nel dominio e nel registro persistente.
7. [ ] Invio individuale SMTP MDaemon, testo + HTML, firma ufficiale e logo CID facoltativo.
   - [x] composizione testo/HTML con apertura obbligatoria ed escaping;
   - [x] trasporto SMTP con STARTTLS, SSL e PLAIN esplicitamente autorizzato;
   - [x] Message-ID, mittente, Reply-To e MIME multipart;
   - [x] logo CID opzionale e fake SMTP;
   - [x] classificazione retryable, permanente e incerta;
   - [x] nessuna copia nella Posta inviata;
   - [ ] inserimento dei parametri MDaemon nei Secrets;
   - [ ] approvazione di mittente, Reply-To, firma e logo;
   - [ ] collaudo su MDaemon con destinatario override.
8. [ ] Registro amministrativo completo.
   - [x] schema, archivio fake e adapter Google Sheets;
   - [x] inizializzatore idempotente e non distruttivo delle quattro tab;
   - [x] registro persistente integrato nell'orchestratore;
   - [x] gestione Message-ID, versione, tentativi ed errori;
   - [ ] creazione controllata dello Spreadsheet amministrativo;
   - [ ] prova di append, update e blocco duplicati su foglio sintetico.
9. [ ] Foglio `CONFIG` modificabile da un responsabile non tecnico.
   - [x] schema di chiave, valore, tipo, descrizione e modificabilità;
   - [x] lettura, validazione e applicazione runtime;
   - [x] limiti numerici, override test e template validati;
   - [x] barriere separate tra foglio, CLI, environment e consenso produzione;
   - [ ] collaudo con responsabile non tecnico.
10. [ ] `DASHBOARD`, heartbeat, anomalie, kill switch, runbook e handoff.
   - [x] aggiornamento runtime aggregato di dashboard e heartbeat;
   - [x] registro anomalie con sanitizzazione e deduplicazione in memoria;
   - [x] valutazione salute per heartbeat, fallimenti ed esiti incerti;
   - [x] kill switch verificato prima della lettura e degli invii;
   - [x] runbook operativo, emergenze, handoff, deployment e test;
   - [ ] prova reale delle scritture dashboard/anomalie;
   - [ ] collaudo dei runbook e passaggio di consegne.

## Orchestrazione

È implementato il flusso completo:

1. verifica strutturale del foglio amministrativo;
2. lettura e validazione di `CONFIG`;
3. controllo kill switch e modalità;
4. lettura e validazione della sorgente;
5. registrazione minimizzata delle anomalie;
6. selezione e limite dei candidati;
7. deduplicazione e prenotazione `SENDING`;
8. composizione testo/HTML;
9. override in modalità test;
10. invio SMTP o dry-run;
11. transizione dello stato persistente;
12. aggiornamento dashboard e riepilogo aggregato.

## Vincoli permanenti

- costo zero con runner GitHub standard;
- nessun segreto o dato personale nel repository;
- nessuna chiave JSON permanente per Google Cloud;
- `dry-run` predefinito;
- nessun invio reale senza autorizzazione esplicita e barriere multiple;
- nessun workflow schedulato attivo prima del go-live;
- semplicità operativa per un futuro responsabile poco tecnico.
