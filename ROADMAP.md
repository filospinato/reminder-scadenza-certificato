# Roadmap

Il progetto segue il contratto funzionale concordato. Ogni fase deve essere implementata, testata e documentata prima dell'attivazione reale.

1. [x] Repository Python, test, CI e documentazione di base.
2. [ ] GitHub Actions programmata una o due volte al giorno, oltre all'avvio manuale.
3. [ ] Lettura di `Operativo` tramite Google Sheets API e service account a privilegi minimi.
   - [x] protocollo indipendente per le sorgenti dati;
   - [x] adapter Google Sheets con lettore iniettato;
   - [x] conversione e validazione strutturale delle matrici;
   - [x] test con fake del trasporto Google API;
   - [x] supporto alle intestazioni di `Operativo` in riga 2;
   - [x] contratto software WIF/OIDC senza chiavi permanenti;
   - [x] runbook di provisioning, trust policy e privilegi minimi;
   - [ ] provisioning reale di progetto, pool, provider e service account;
   - [ ] prova su Spreadsheet sintetico;
   - [ ] successivo collegamento controllato a `Operativo` in sola lettura.
4. [x] Validazione di ID, nome, cognome, email, scadenza e stato; anomalie e duplicati esclusi in sicurezza.
5. [ ] Controllo della finestra di scadenza e del registro anti-duplicazione.
   - [x] finestra configurabile, estremi inclusi, con scaduti esclusi;
   - [x] chiave deterministica `ID_ARBITRO|DATA_SCADENZA|TIPO_NOTIFICA`;
   - [x] prenotazione atomica e blocco dei duplicati nel registro in memoria;
   - [x] schema e archivio fake della tab `NOTIFICHE`;
   - [x] adapter Sheets con ricerca univoca, append e update controllato;
   - [ ] persistenza e confronto su Spreadsheet sintetico;
   - [ ] serializzazione delle esecuzioni di produzione tramite `concurrency`.
6. [x] Stati `SENDING`, `SENT`, `FAILED_RETRYABLE`, `UNKNOWN_REVIEW_REQUIRED` e transizioni sicure nel dominio.
7. [ ] Invio individuale SMTP MDaemon, testo + HTML, firma ufficiale e logo CID facoltativo.
   - [x] composizione pura e testata delle versioni testo e HTML;
   - [x] apertura personalizzata `Ciao {{nome}}, ricevi questa mail...` usando la colonna `nome` della stessa riga;
   - [x] supporto a `{{cognome}}` e `{{nome_completo}}`;
   - [x] escaping HTML e validazione sicura dei template;
   - [ ] firma ufficiale, logo CID, trasporto SMTP e test MDaemon.
8. [ ] Registro amministrativo completo con destinatario, nome, cognome, scadenza, tipo, Message-ID, versione ed errori.
   - [x] contratto del ciclo di vita e record minimo in memoria;
   - [x] schema tipizzato della tab `NOTIFICHE`;
   - [x] archivio fake con insert/update per chiave e controlli di coerenza;
   - [x] adapter Google Sheets e ponte verso un servizio già autenticato;
   - [ ] schema completo del nuovo Spreadsheet amministrativo separato;
   - [ ] prova controllata di scrittura su Spreadsheet sintetico;
   - [ ] integrazione nel flusso applicativo completo.
9. [ ] Foglio `CONFIG` modificabile da un responsabile non tecnico.
10. [ ] `DASHBOARD`, heartbeat, anomalie, kill switch, runbook e handoff.

## Ordine di sviluppo

- fondazioni e regole pure;
- contratto dati e adapter Google Sheets;
- autenticazione WIF/OIDC e collaudo sintetico;
- registro, configurazione e dashboard;
- composizione messaggi e firma;
- SMTP MDaemon;
- workflow schedulato e monitoraggio;
- hardening, validazione finale e passaggio di consegne.

## Vincoli permanenti

- costo zero con runner GitHub standard;
- nessun segreto o dato personale nel repository;
- nessuna chiave JSON permanente per Google Cloud;
- `dry-run` predefinito;
- nessun invio reale senza autorizzazione esplicita;
- semplicità operativa per un futuro responsabile poco tecnico.
