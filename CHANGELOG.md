# Changelog

Questo documento registra soltanto i delta funzionali delle release. Evidenze di collaudo e cronache di pull request vivono rispettivamente negli artefatti di validazione e su GitHub; i valori correnti restano nelle fonti tecniche che li usano.

## [Unreleased]

### Affidabilità e configurazione

- Estesa la ricerca delle intestazioni di Operativo fino a ZZ, mantenendo la
  lettura batch delle sole otto colonne richieste: la colonna di attività
  corrente può trovarsi oltre AS senza essere confusa con quella storica.
- La password SMTP dei workflow proviene dal repository secret
  `REMINDER_SMTP_PASSWORD`, configurabile da un collaboratore con il proprio
  account. Le Variables restano nell'Environment; il precedente Secret
  `SMTP_PASSWORD` non viene più usato dai workflow.
- Limitati a `main` anche controllo e manutenzione. Nei repository pubblici
  sono bloccati applicazione e caricamento dei backup amministrativi.
- Esclusa la password dalla rappresentazione diagnostica della configurazione SMTP.
- Aggiunti retry alle operazioni Google Sheets idempotenti, lasciando gli append
  senza retry per evitare scritture duplicate dall'esito incerto.
- Rimossa una lista di stati inattivi inutilizzata e resa esplicita l'anomalia
  critica in caso di mancata registrazione di un esito SMTP non classificato.

### Manutenzione

- README essenziale e terminologia generica, con costi, configurazione a distanza
  e distinzione tra invii manuali e programmazione giornaliera ancora assente.
- Rimossi integrazioni e hook per strumenti non più utilizzati, inclusi i relativi test.
- Regole operative in `AGENTS.md`, contratto GitHub in JSON e guide storiche in
  `releases/`; rimossi documenti di stato e wrapper duplicati.
- Preparazione dell'ambiente con `scripts/setup.sh`: extra da `pyproject.toml`,
  ambiente per checkout, verifica offline quando coerente, riparazione degli
  strumenti guasti e normalizzazione dei flag macOS tramite Python.
- Verifica unica con `scripts/verify.sh`: controlli automatici, coerenza delle
  dipendenze, whitespace e checkout invariato. Rimosso `compileall` ridondante.
- CI sul runtime Python 3.12, con regole Ruff esplicite; rimossa la matrice
  settimanale. I collaudi Drive restano obbligatori prima del deployment solo
  per le modifiche che possono influire sulle risorse live.

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
