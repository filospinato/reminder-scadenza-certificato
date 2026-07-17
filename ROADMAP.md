# Roadmap

Il progetto segue il contratto funzionale concordato. Ogni fase deve essere implementata, testata e documentata prima dell'attivazione reale.

1. [x] Repository Python, test, CI e documentazione di base.
2. [ ] GitHub Actions programmata una o due volte al giorno, oltre all'avvio manuale.
3. [ ] Lettura di `Operativo` tramite Google Sheets API e service account a privilegi minimi.
   - [x] protocollo indipendente per le sorgenti dati;
   - [x] adapter Google Sheets con lettore iniettato;
   - [x] conversione e validazione strutturale delle matrici;
   - [x] test con fake del trasporto Google API;
   - [ ] autenticazione reale con service account in sola lettura;
   - [ ] prova su Spreadsheet sintetico e successivo collegamento a `Operativo`.
4. [x] Validazione di ID, nominativo, email, scadenza e stato; anomalie e duplicati esclusi in sicurezza.
5. [ ] Controllo della finestra di scadenza e del registro anti-duplicazione.
6. [ ] Stati `SENDING`, `SENT`, `FAILED_RETRYABLE`, `UNKNOWN_REVIEW_REQUIRED`.
7. [ ] Invio individuale SMTP MDaemon, testo + HTML, firma ufficiale e logo CID facoltativo.
   - [x] composizione pura e testata delle versioni testo e HTML;
   - [x] apertura personalizzata `Ciao {{nome}}, ricevi questa mail...`;
   - [x] escaping HTML e validazione sicura dei template;
   - [ ] firma ufficiale, logo CID, trasporto SMTP e test MDaemon.
8. [ ] Registro amministrativo completo con Message-ID, versione ed errori.
9. [ ] Foglio `CONFIG` modificabile da un responsabile non tecnico.
10. [ ] `DASHBOARD`, heartbeat, anomalie, kill switch, runbook e handoff.

## Ordine di sviluppo

- fondazioni e regole pure;
- contratto dati e adapter Google Sheets;
- registro, configurazione e dashboard;
- composizione messaggi e firma;
- SMTP MDaemon;
- workflow schedulato e monitoraggio;
- hardening, validazione finale e passaggio di consegne.

## Vincoli permanenti

- costo zero con runner GitHub standard;
- nessun segreto o dato personale nel repository;
- `dry-run` predefinito;
- nessun invio reale senza autorizzazione esplicita;
- semplicità operativa per un futuro responsabile poco tecnico.
