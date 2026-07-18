# Roadmap

Il progetto segue il contratto funzionale concordato. Il codice pre-produzione è implementato e rafforzato, ma l'attivazione reale richiede ancora risorse, permessi, contenuti e collaudi esterni.

1. [x] Repository Python, test, CI e documentazione di base.
2. [ ] GitHub Actions programmata una o due volte al giorno, oltre all'avvio manuale.
   - [x] workflow manuale pre-produzione con WIF, environment e permessi minimi;
   - [x] gate dell'Environment verificato dentro il job, prima dell'autenticazione;
   - [x] data corrente predefinita, con override manuale opzionale;
   - [x] `concurrency` condivisa tra pre-produzione e modello di produzione;
   - [x] segreti SMTP limitati al solo step di invio;
   - [x] modello di produzione schedulato conservato come `.example` non attivo;
   - [ ] creazione degli environment e valorizzazione di Variables/Secrets;
   - [ ] attivazione del workflow di produzione dopo autorizzazione finale.
3. [ ] Lettura di `Operativo` tramite Google Sheets API e service account a privilegi minimi.
   - [x] protocollo, adapter, conversione e validazione strutturale;
   - [x] supporto alle intestazioni di `Operativo` in riga 2;
   - [x] mappatura delle intestazioni reali;
   - [x] comando `check-headers` limitato alla sola riga delle intestazioni;
   - [x] preflight Google in sola lettura per file distinti, metadati delle tab e sole righe delle intestazioni;
   - [x] codici diagnostici stabili, output JSON aggregato e azioni di runbook senza payload Google;
   - [x] factory Google basata su ADC temporanee prodotte da WIF;
   - [x] verifica runtime del file ADC, con accettazione dei soli `external_account` completi e rifiuto dei JSON `service_account` permanenti;
   - [x] runbook di provisioning, trust policy e privilegi minimi;
   - [ ] provisioning reale di progetto, pool, provider e service account;
   - [ ] condivisione diretta in sola lettura;
   - [ ] esecuzione reale del preflight con zero righe dati lette e zero scritture;
   - [ ] verifica pratica della diagnostica su errori controllati;
   - [ ] dry-run controllato su righe reali con output aggregato.
4. [x] Validazione di ID, nome, cognome, email, scadenza e stato; anomalie e duplicati esclusi in sicurezza.
5. [ ] Controllo della finestra di scadenza e del registro anti-duplicazione.
   - [x] finestra configurabile, estremi inclusi, con scaduti esclusi;
   - [x] chiave deterministica `ID_ARBITRO|DATA_SCADENZA|TIPO_NOTIFICA`;
   - [x] prenotazione preventiva `SENDING`;
   - [x] registro persistente sopra `NOTIFICHE`;
   - [x] dry-run che consulta il registro senza scrivere;
   - [x] limite applicato dopo la deduplicazione;
   - [x] retry soltanto da `FAILED_RETRYABLE`;
   - [x] blocco automatico di `SENT`, `SENDING` e `UNKNOWN_REVIEW_REQUIRED`;
   - [x] serializzazione prevista nei workflow;
   - [x] collaudo automatizzato del ciclo persistente con fake;
   - [x] comando protetto per ripetere append, rilettura e update sul foglio amministrativo con una sola riga sintetica;
   - [ ] esecuzione controllata del comando sullo Spreadsheet amministrativo reale;
   - [ ] prova di concorrenza tra workflow sul foglio reale.
6. [x] Stati `SENDING`, `SENT`, `FAILED_RETRYABLE`, `UNKNOWN_REVIEW_REQUIRED` e transizioni sicure nel dominio e nel registro persistente.
7. [ ] Invio individuale SMTP MDaemon, testo + HTML, firma ufficiale e logo CID facoltativo.
   - [x] composizione testo/HTML con apertura obbligatoria ed escaping;
   - [x] trasporto SMTP con STARTTLS, SSL e PLAIN esplicitamente autorizzato;
   - [x] Message-ID, mittente, Reply-To e MIME multipart;
   - [x] logo CID opzionale allegato e referenziato nel corpo HTML;
   - [x] validazione contro header injection;
   - [x] classificazione retryable, permanente e incerta;
   - [x] test SMTP limitato a una email e audit dell'override effettivo;
   - [x] nessuna copia nella Posta inviata;
   - [ ] inserimento dei parametri MDaemon nei Secrets;
   - [ ] approvazione di mittente, Reply-To, firma e logo;
   - [ ] collaudo su MDaemon con destinatario override.
8. [ ] Registro amministrativo completo.
   - [x] schema, archivio fake e adapter Google Sheets;
   - [x] bootstrap idempotente di un file vuoto creato dall'identità umana;
   - [x] registro persistente integrato nell'orchestratore;
   - [x] gestione Message-ID, versione, tentativi ed errori;
   - [x] collaudo sintetico automatizzato di append, rerun e update;
   - [x] comando dedicato con doppio consenso, dati `.invalid` e output aggregato;
   - [x] preflight non distruttivo di tab e intestazioni amministrative;
   - [x] diagnostica stabile del preflight documentata per il runbook;
   - [ ] creazione umana e condivisione dello Spreadsheet amministrativo;
   - [ ] esecuzione del preflight e del collaudo sul foglio reale.
9. [ ] Foglio `CONFIG` modificabile da un responsabile non tecnico.
   - [x] schema di chiave, valore, tipo, descrizione e modificabilità;
   - [x] lettura, validazione e applicazione runtime;
   - [x] limiti numerici, override test e template validati;
   - [x] barriere separate tra foglio, CLI, environment e consenso produzione;
   - [ ] collaudo con responsabile non tecnico.
10. [ ] `DASHBOARD`, heartbeat, anomalie, kill switch, runbook e handoff.
   - [x] aggiornamento runtime aggregato di dashboard e heartbeat;
   - [x] scrittura dashboard con un solo update, senza finestra vuota intermedia;
   - [x] registro anomalie con sanitizzazione di email, token e notification ID;
   - [x] valutazione salute per heartbeat, fallimenti ed esiti incerti;
   - [x] kill switch verificato prima della lettura e degli invii;
   - [x] runbook operativo, emergenze, handoff, deployment, test e diagnostica preflight;
   - [ ] prova reale delle scritture dashboard/anomalie;
   - [ ] collaudo dei runbook e passaggio di consegne.

## Orchestrazione

È implementato il flusso completo:

1. verifica strutturale del foglio amministrativo;
2. lettura e validazione di `CONFIG`;
3. controllo kill switch e modalità;
4. lettura e validazione della sorgente;
5. registrazione minimizzata delle anomalie;
6. selezione dei candidati nella finestra;
7. deduplicazione rispetto al registro;
8. applicazione del limite ai soli candidati prenotabili;
9. composizione testo/HTML;
10. override e limite unitario in modalità test;
11. invio SMTP o dry-run;
12. transizione dello stato persistente;
13. aggiornamento dashboard e riepilogo aggregato.

## Vincoli permanenti

- costo zero con runner GitHub standard;
- nessun segreto o dato personale nel repository;
- nessuna chiave JSON permanente per Google Cloud, bloccata anche dalla verifica runtime delle ADC;
- `dry-run` predefinito;
- nessun invio reale senza autorizzazione esplicita e barriere multiple;
- preflight esterni limitati a metadati e intestazioni, senza letture di righe operative o scritture;
- diagnostica pubblica del preflight limitata a codici stabili, messaggi brevi e azioni senza identificatori sensibili;
- collaudi di scrittura limitati al foglio amministrativo e a dati sintetici esplicitamente riconoscibili;
- nessun workflow schedulato attivo prima del go-live;
- semplicità operativa per un futuro responsabile poco tecnico.
