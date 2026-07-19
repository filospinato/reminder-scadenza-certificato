# Roadmap

Il codice pre-produzione è implementato e semplificato. L'attivazione reale richiede ancora risorse, permessi, contenuti e collaudi esterni.

1. [x] Repository Python, test, CI e documentazione di base.
2. [ ] GitHub Actions programmata una volta al giorno, oltre all'avvio manuale.
   - [x] workflow manuale pre-produzione con WIF, Environment e permessi minimi;
   - [x] `concurrency` condivisa;
   - [x] segreti SMTP limitati al solo step di invio;
   - [x] modello di produzione conservato come `.example` non attivo;
   - [x] una sola schedule giornaliera prevista;
   - [ ] creazione degli Environment e valorizzazione di Variables/Secrets;
   - [ ] attivazione del workflow di produzione dopo autorizzazione finale.
3. [ ] Lettura di `Operativo` tramite Google Sheets API e service account a privilegi minimi.
   - [x] adapter, conversione e validazione strutturale;
   - [x] intestazioni in riga 2;
   - [x] unica mappatura canonica delle sei colonne usate;
   - [x] preflight unico limitato a file, tab e intestazioni;
   - [x] WIF/OIDC e blocco delle chiavi permanenti;
   - [ ] provisioning reale, condivisione e dry-run controllato.
4. [x] Validazione di ID, nome, cognome, email, scadenza e stato; anomalie e duplicati esclusi.
5. [ ] Finestra di scadenza e registro anti-duplicazione.
   - [x] finestra configurabile e chiave deterministica;
   - [x] stati e transizioni conservative;
   - [x] registro persistente indicizzato dopo una sola lettura per esecuzione;
   - [x] limite applicato dopo la deduplicazione;
   - [x] collaudo sintetico protetto;
   - [ ] prova sul foglio reale e concorrenza tra workflow.
6. [x] Stati `SENDING`, `SENT`, `FAILED_RETRYABLE` e `UNKNOWN_REVIEW_REQUIRED`.
7. [ ] Invio individuale SMTP MDaemon.
   - [x] testo/HTML, escaping e Message-ID;
   - [x] STARTTLS/SSL, Reply-To e logo CID facoltativo;
   - [x] classificazione retryable, permanente e incerta;
   - [x] test limitato a una email all'override;
   - [ ] Secrets reali, contenuti approvati e collaudo MDaemon.
8. [ ] Registro amministrativo completo.
   - [x] schema, fake e adapter Google;
   - [x] bootstrap idempotente;
   - [x] append/update e indice locale;
   - [x] preflight e collaudo sintetico;
   - [ ] creazione e collaudo del foglio reale.
9. [ ] `CONFIG` modificabile da un responsabile non tecnico.
   - [x] un solo interruttore `AUTOMAZIONE_ATTIVA`;
   - [x] modalità determinata dal sottocomando, senza duplicazioni nel foglio;
   - [x] validazione concentrata sui valori funzionali;
   - [x] corpo email liberamente modificabile con placeholder autorizzati;
   - [ ] prova con responsabile non tecnico.
10. [ ] `DASHBOARD`, anomalie, arresto operativo, runbook e handoff.
    - [x] dashboard aggregata con un solo update;
    - [x] anomalie sanitizzate e deduplicate per ID aperto;
    - [x] `AUTOMAZIONE_ATTIVA=false` blocca prima della lettura e degli invii;
    - [x] runbook, emergenze, handoff e checklist;
    - [ ] prova reale delle scritture e passaggio di consegne.

## Flusso applicativo

1. verifica leggera di tab e intestazioni amministrative;
2. lettura e validazione di `CONFIG`;
3. controllo di `AUTOMAZIONE_ATTIVA`;
4. lettura e validazione di `Operativo`;
5. deduplicazione delle anomalie aperte;
6. selezione dei candidati;
7. singola lettura e indicizzazione di `NOTIFICHE`;
8. limite, composizione, dry-run o SMTP;
9. transizione persistente e aggiornamento dashboard.

## Vincoli permanenti

- nessun segreto o dato personale nel repository;
- nessuna chiave JSON permanente;
- `Operativo` sempre in sola lettura;
- dry-run senza configurazione SMTP;
- nessun invio reale senza Environment, CONFIG coerente e consenso esplicito;
- collaudi di scrittura limitati a dati sintetici;
- nessun workflow schedulato attivo prima del go-live;
- semplicità operativa e manutentiva.
