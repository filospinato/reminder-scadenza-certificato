# Changelog

Questo documento registra soltanto i delta funzionali delle release. Evidenze di collaudo e cronache di pull request vivono rispettivamente negli artefatti di validazione e su GitHub; i valori correnti restano nelle fonti tecniche che li usano.

## [Unreleased]

### Affidabilità

- `scripts/setup.sh` ripara uno strumento di sviluppo guasto invece di fallire
  per sempre. Un eseguibile presente ma rotto lascia il requisito già
  soddisfatto, quindi `pip install --editable .[dev,google]` non ha nulla da fare
  e non riscrive il file: il gate rilevava il guasto, reinstallava a vuoto e
  usciva con errore a ogni esecuzione successiva. È lo stato che impedisce a
  un'automazione di eseguire `ruff check .` e di rimettersi in sesto da sola. La
  riparazione ora passa a `--force-reinstall`, che il file lo riscrive davvero.

- reso esplicito il set stabile di regole Ruff usato dalla CI;
- aggiunti retry automatici alle operazioni runtime idempotenti di Google Sheets,
  mantenendo gli append senza retry automatici per non duplicare scritture dall’esito
  incerto;
- rimossa dalla politica dello stato una lista di valori inattivi che non partecipava
  alla semantica documentata di `Operativo`;
- resa visibile come anomalia critica anche l’eventuale mancata registrazione di un
  esito SMTP non classificato.

### Documentazione e architettura dell’informazione

- consolidate in root le tre fonti documentali canoniche: `README.md`, `AGENTS.md` e `CHANGELOG.md`;
- spostati guide, contratti e validazioni della release in `releases/v0.14.18/`;
- sostituito il contratto Markdown dell’Environment con `config/github/environment-contract.json`;
- rimossi roadmap, checklist, handoff e documenti concorrenti sotto `docs/`;
- evitato un manifesto di stato separato, mantenendo versione, workflow e configurazioni nelle rispettive fonti autoritative;
- aggiornati i test per proteggere la nuova architettura SSoT;
- introdotto `scripts/setup.sh` come unica procedura di preparazione dell’ambiente
  per tutti gli agenti, richiamato all’avvio, alla ripresa, dopo `/clear`, dopo
  una compattazione e al fork delle
  sessioni Claude Code locali e remote e documentato per Codex in
  `config/codex/ENVIRONMENT_SETUP.md`; la configurazione Cloud va salvata solo
  quando lo script è già presente su `main`, mentre un hook Codex di progetto
  applica lo stesso gate a Local e Worktree; lo script installa gli stessi extra
  della CI in una `.venv` per-checkout senza modificare il Python globale e senza
  duplicare l’elenco, che resta in `pyproject.toml`.

## [0.14.18] - 2026-07-22

### Workflow produttivo

- reso disponibile il workflow degli invii reali come dispatch esclusivamente manuale su `main`;
- mantenuto un solo Environment condiviso con le risorse di preproduzione;
- conservati lock condiviso e limiti selezionabili di 1, 5 o 10 invii;
- mantenuta intenzionalmente assente la schedule automatica.

## [0.14.16–0.14.17] - 2026-07-22

### Configurazione SMTP

- eliminata la Variable ridondante `SMTP_FROM`;
- usato `SMTP_USERNAME` sia per autenticazione sia come mittente;
- confinata la sola password nei Secrets;
- completata la compatibilità con STARTTLS e il test controllato verso destinatario override.

## [0.14.11–0.14.15] - 2026-07-22

### Firma e schema amministrativo

- introdotta la firma istituzionale HTML con logo inline CID e fallback testuale coerente;
- generata la firma testo/HTML da un’unica sorgente versionata;
- introdotto lo schema amministrativo v4 a sei chiavi;
- rimossa `FIRMA_TESTO` dalla CONFIG e la compatibilità runtime con gli schemi precedenti;
- mantenuto il riconoscimento dei vecchi schemi soltanto nell’anteprima di migrazione.

## [0.14.5–0.14.10] - 2026-07-20/21

### Affidabilità e integrazione

- fissato nel codice il contratto di `Operativo`: tab, riga intestazioni e intervallo;
- escluse prima della validazione le categorie non tenute al certificato;
- aggiunto il supporto ai seriali data nativi di Google Sheets;
- limitate le anomalie ai record realmente candidati nella finestra di preavviso;
- rafforzata la gestione di duplicati, errori SMTP e stati del registro;
- aggiunto il rollout controllato tramite `--max-sends`;
- esplicitato il fuso `Europe/Rome`;
- aggiornate e fissate a SHA immutabili le GitHub Actions;
- resi obbligatori i collaudi sui fogli Drive per ogni modifica al codice.

## [0.14.0–0.14.4] - 2026-07-20

### Semplificazione operativa

- ridotta la CONFIG a tre colonne e a un unico interruttore `INVIO_AUTOMATICO_ATTIVO`;
- unificati inizializzazione e migrazione nel comando `setup-admin`;
- unificati preflight, controllo e revisione del registro nel comando `check`;
- separati workflow ordinario, manutenzione e produzione;
- reso configurabile il messaggio completo senza frasi implicite;
- normalizzati nome, cognome e nominativo completo durante la composizione;
- estesa la sanitizzazione agli identificatori di notifica correnti.

## [0.13.0–0.13.5] - 2026-07-20

### Registro e popolazione

- introdotto lo schema amministrativo v2 con migrazione controllata e backup;
- minimizzato il registro eliminando nome, cognome ed email persistiti;
- aggiunto `FAILED_PERMANENT` e limitati i retry a tre tentativi;
- completata la migrazione della dashboard;
- esclusi Benemeriti, Osservatori, Fuori Quadro, Decaduti e Non Attivi;
- interpretato lo stato vuoto come attività secondo il contratto di `Operativo`;
- eliminato il precedente file `LATEST.md` e separata la storia funzionale dallo stato corrente.

## [0.12.0] - 2026-07-19

### CLI e modello operativo

- riunite tutte le operazioni sotto il comando `reminder-certificati`;
- rimossi entry point storici e comandi duplicati;
- sostituiti i precedenti interruttori con un unico controllo operativo;
- mantenuti WIF/OIDC, registro conservativo e consenso esplicito per gli invii.

## [0.11.0–0.11.5] - 2026-07-17/18

### Stack di preproduzione

- implementati inizializzazione del foglio amministrativo, CONFIG runtime, dashboard e anomalie;
- implementati registro persistente, orchestratore end-to-end e trasporto SMTP MDaemon;
- aggiunti factory Google Sheets e workflow manuale protetto;
- introdotta la barriera che rifiuta chiavi permanenti e accetta soltanto credenziali WIF `external_account`;
- aggiunti collaudo sintetico del registro e preflight Google in sola lettura;
- introdotti codici diagnostici stabili senza esposizione di dati personali.

## [0.10.0] - 2026-07-17

### Schema amministrativo

- definito lo Spreadsheet amministrativo separato con `CONFIG`, `NOTIFICHE`, `DASHBOARD` e `ANOMALIE`;
- aggiunti valori iniziali sicuri, registro vuoto e dashboard aggregata.

## [0.9.0] - 2026-07-17

### Autenticazione cloud

- introdotto il contratto tipizzato per WIF/OIDC;
- limitata la trust tramite identificatori numerici di repository e proprietario;
- vietate configurazioni con chiavi permanenti.

## [0.8.0] - 2026-07-17

### Adapter `Operativo`

- supportate intestazioni in riga configurabile;
- costruiti intervalli A1 coerenti con la riga reale;
- preservato il numero di riga originario nelle anomalie.

## [0.7.0] - 2026-07-17

### Persistenza Google Sheets

- implementati lettura, append e update della tab `NOTIFICHE`;
- aggiunti indice locale, controlli di unicità e adapter Google/fake;
- bloccate regressioni temporali e intestazioni non conformi.

## [0.6.0] - 2026-07-17

### Schema delle notifiche

- introdotto lo schema tipizzato della tab `NOTIFICHE`;
- aggiunta conversione sicura tra record applicativi e righe;
- implementato un archivio in memoria thread-safe.

## [0.5.0] - 2026-07-17

### Macchina a stati

- introdotti registro in memoria, prenotazione preventiva `SENDING` e stati di esito;
- consentito il retry soltanto da `FAILED_RETRYABLE`;
- bloccati i reinvii per stati conclusi o incerti.

## [0.4.0–0.4.1] - 2026-07-17

### Sorgenti dati

- separato il dominio dalla tecnologia di origine tramite protocolli e adapter;
- aggiunto l’adapter Google Sheets testabile con fake;
- allineato il modello a colonne distinte per nome, cognome ed email;
- vietata la ricostruzione di dati anagrafici da righe o campi differenti.

## [0.3.0] - 2026-07-17

### Composizione email

- aggiunto un compositore puro testo/HTML senza invio;
- introdotti placeholder autorizzati ed escaping HTML;
- bloccati header injection e placeholder malformati.

## [0.2.0] - 2026-07-17

### Contratto dati

- introdotte mappatura delle colonne e validazione strutturata;
- aggiunti formati data, anomalie stabili ed esclusione degli ID duplicati;
- resa non bloccante una singola riga invalida.

## [0.1.0] - 2026-07-17

### Prima versione

- creato il package Python con layout `src`;
- implementati modelli, selezione delle scadenze, chiave anti-duplicazione e dry-run;
- aggiunti dati anonimi di esempio, test automatici e CI.
