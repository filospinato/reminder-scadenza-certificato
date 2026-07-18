# Changelog

## [0.11.4] - 2026-07-18

### Aggiunto

- comando separato `reminder-certificati-google-preflight` per verificare le risorse Google prima dei collaudi esterni;
- controllo che `Operativo` e il foglio amministrativo siano Spreadsheet distinti;
- verifica dell'ordine delle quattro tab amministrative e delle sole righe delle intestazioni;
- lettura limitata alla riga 2 delle intestazioni di `Operativo`;
- test sintetici per configurazione conforme, file coincidenti, tab fuori ordine e intestazioni mancanti.

### Modificato

- versione del pacchetto aggiornata a 0.11.4;
- README, stato corrente, roadmap e checklist di deployment descrivono il nuovo preflight in sola lettura.

### Sicurezza

- il preflight non legge righe operative, non scrive celle e non usa SMTP;
- l'output contiene soltanto booleani e conteggi aggregati e non espone ID degli Spreadsheet o contenuti delle celle;
- il permesso di modifica del foglio amministrativo resta esplicitamente non verificato finché non viene eseguito il collaudo sintetico separato;
- nessuna credenziale, risorsa Google reale o dato personale è stato usato durante lo sviluppo.

## [0.11.3] - 2026-07-18

### Aggiunto

- comando separato `reminder-certificati-registry-check` per collaudare la tab `NOTIFICHE` del solo Spreadsheet amministrativo;
- sequenza sintetica completa di append `SENDING`, rilettura, update a `SENT` e verifica dell'unicità della chiave;
- test applicativi e CLI con fake per consensi, persistenza, output aggregato e assenza di accessi operativi.

### Modificato

- versione del pacchetto aggiornata a 0.11.3;
- README, stato corrente e roadmap descrivono il collaudo protetto e la futura esecuzione controllata sul foglio reale.

### Sicurezza

- il comando richiede contemporaneamente `--confirm-synthetic-write` e `ALLOW_SYNTHETIC_REGISTRY_WRITE=true`;
- la prova usa una sola riga con ID, nominativo, email e Message-ID sintetici sul dominio `.invalid`;
- il comando non legge `Operativo`, non usa SMTP e non stampa ID dello Spreadsheet, chiavi del registro o contenuti delle celle;
- nessuna credenziale, risorsa Google o scrittura reale è stata attivata durante lo sviluppo.

## [0.11.2] - 2026-07-17

### Aggiunto

- barriera runtime che verifica il file indicato da `GOOGLE_APPLICATION_CREDENTIALS` prima di costruire il client Google Sheets;
- validazione del formato WIF/OIDC `external_account`, inclusi `audience`, `subject_token_type` e `credential_source`;
- test sintetici per credenziali federate valide, chiavi permanenti, file mancanti, JSON malformati e configurazioni incomplete.

### Modificato

- versione del pacchetto aggiornata a 0.11.2;
- README, stato corrente, roadmap e guida Google Cloud descrivono il controllo effettivo delle Application Default Credentials.

### Sicurezza

- i file JSON di tipo `service_account` vengono rifiutati esplicitamente prima di qualsiasi chiamata alle API Google;
- il contenuto delle credenziali non viene stampato né incluso negli errori;
- nessuna credenziale o risorsa Google reale è stata creata, letta o attivata.

## [0.11.1] - 2026-07-17

### Corretto

- il service account non tenta più di creare o possedere lo Spreadsheet amministrativo: inizializza un file vuoto creato e condiviso dall'amministratore umano;
- il bootstrap trasforma in sicurezza una singola tab vuota nelle quattro tab canoniche e rifiuta file non vuoti o ambigui;
- il gate dei workflow viene valutato dopo la dichiarazione dell'Environment, rendendo utilizzabili le variabili definite a quel livello;
- il workflow manuale non usa più una data predefinita fissa;
- pre-produzione e produzione condividono lo stesso gruppo `concurrency`;
- i segreti SMTP del modello di produzione sono disponibili soltanto allo step di invio;
- il dry-run consulta il registro senza scrivere e il limite viene applicato dopo la deduplicazione;
- il test SMTP registra l'indirizzo override realmente contattato ed è limitato a una sola email per esecuzione;
- la dashboard viene aggiornata con un singolo `values.update`, senza `clear` preventivo;
- le chiavi `notification_id` vengono rimosse dai messaggi CLI e di monitoraggio;
- il logo CID viene sia allegato sia referenziato nel corpo HTML;
- nome mittente e CID vengono validati contro header injection;
- gli errori SMTP non classificati dopo `SENDING` vengono conservativamente trasformati in `UNKNOWN_REVIEW_REQUIRED`.

### Modificato

- versione del pacchetto aggiornata a 0.11.1;
- la CI installa anche l'extra `google`;
- README, stato corrente, roadmap e runbook descrivono il flusso corretto di creazione umana e inizializzazione applicativa;
- aggiunti test di regressione per workflow, CLI, deduplicazione, limite, dashboard, MIME e bootstrap.

### Sicurezza

- nessuna risorsa Google, credenziale, email reale, firma, logo o invio operativo è stato creato o attivato;
- il file amministrativo resta di proprietà dell'identità umana e il service account riceve soltanto modifica tramite condivisione diretta;
- i log non espongono chiavi contenenti l'ID dell'arbitro;
- un test SMTP non può inviare accidentalmente un intero lotto all'override.

## [0.11.0] - 2026-07-17

### Aggiunto

- inizializzatore idempotente e non distruttivo dello Spreadsheet amministrativo, con fake e ponte Google Sheets;
- parser runtime tipizzato della tab `CONFIG`, con validazione di chiavi, tipi, limiti, override e template;
- registro persistente sopra `NOTIFICHE`, con prenotazione preventiva `SENDING` e transizioni conservative;
- aggiornamento aggregato di `DASHBOARD`, persistenza minimizzata delle anomalie e valutazione dello stato di salute;
- orchestratore end-to-end per `DRY_RUN`, `TEST_SMTP` e `PRODUZIONE` protetta;
- trasporto SMTP MDaemon testo/HTML con `Message-ID`, STARTTLS/SSL, Reply-To, fake e logo CID facoltativo;
- classificazione degli errori SMTP in ritentabili, permanenti ed esiti incerti;
- factory Google Sheets tramite Application Default Credentials temporanee prodotte da WIF/OIDC;
- mappatura delle intestazioni reali di `Operativo` e comando `check-headers` limitato alla sola riga 2;
- CLI pre-produzione per inizializzare/verificare il foglio, controllare le intestazioni ed eseguire il flusso con output aggregato;
- workflow manuale pre-produzione con environment, WIF, permessi minimi e `concurrency`, disabilitato per default;
- modello non attivo del workflow schedulato di produzione;
- runbook operativo, emergenze, handoff, test e checklist di deployment graduale;
- test sintetici per inizializzazione, CONFIG, monitoraggio, registro persistente, SMTP, orchestrazione, Google runtime e salute.

### Modificato

- versione del pacchetto aggiornata a 0.11.0 e aggiunto il comando `reminder-certificati-runtime`;
- aggiunto l'extra opzionale `google` per installare il client Google soltanto negli ambienti che ne hanno bisogno;
- l'inizializzatore verifica intestazioni e vincoli strutturali senza pretendere che `CONFIG` e `DASHBOARD` conservino per sempre i valori sintetici iniziali;
- `LATEST.md` e `ROADMAP.md` distinguono ora il codice già pronto dalle risorse e dai collaudi che devono essere completati esternamente.

### Sicurezza

- l'inserimento di ID Google o credenziali SMTP non abilita automaticamente elaborazione o invii;
- gli invii fuori dal dry-run richiedono contemporaneamente configurazione coerente, consenso CLI e `ALLOW_EMAIL_DELIVERY=true`;
- la produzione richiede anche il riconoscimento esatto `PRODUCTION_ACTIVATION_ACK`;
- la modalità test sostituisce tutti i destinatari con l'override e usa chiavi `TEST_REMINDER_*` separate;
- il workflow manuale non accede a Google finché `PREPRODUCTION_ENABLED` non viene impostato esplicitamente a `true` in un environment protetto;
- il workflow schedulato è conservato come file `.example` non eseguibile;
- `check-headers` non legge righe dati e la CLI runtime non stampa nominativi, email o contenuti delle righe;
- anomalie e messaggi tecnici vengono sanitizzati per rimuovere email e token;
- nessun progetto Google Cloud, permesso, Spreadsheet, credenziale SMTP, firma, logo o invio reale è stato creato o attivato.

## [0.10.0] - 2026-07-17

### Aggiunto

- contratto tipizzato dello Spreadsheet amministrativo separato `Reminder certificati CIA Lazio — Gestione`;
- definizioni canoniche e ordinate delle tab `CONFIG`, `NOTIFICHE`, `DASHBOARD` e `ANOMALIE`;
- configurazione iniziale con sistema e invii reali disabilitati, modalità test e kill switch attivi;
- limite iniziale di 10 invii per esecuzione e finestra predefinita di 30 giorni;
- saluto fisso `Ciao {{nome}},` e corpo configurabile vincolato all'apertura `ricevi questa mail`;
- dashboard sintetica disattivata con conteggi a zero;
- schema delle anomalie senza righe iniziali o payload personali;
- test per ordine delle tab, intestazioni, larghezza delle righe, valori di sicurezza e apertura del messaggio.

### Modificato

- lo schema `NOTIFICHE` esistente viene riusato come unica fonte delle quattordici colonne canoniche;
- `README.md`, `LATEST.md`, `ROADMAP.md` e `docs/SCHEMA_FOGLI.md` descrivono ora tutte le quattro tab;
- versione del pacchetto aggiornata a 0.10.0.

### Sicurezza

- `INVII_REALI_ABILITATI` parte da `false` e non è modificabile nel foglio iniziale;
- `DESTINATARIO_OVERRIDE` e `CONTATTO_SUPPORTO` restano vuoti, senza email inventate;
- `NOTIFICHE` e `ANOMALIE` non contengono dati precompilati;
- nessuno Spreadsheet reale, permesso Google, dato personale, workflow autenticato o invio SMTP è stato creato o attivato.

## [0.9.0] - 2026-07-17

### Aggiunto

- configurazione tipizzata degli identificatori pubblici per Workload Identity Federation;
- validazione del formato canonico di provider e service account;
- runbook di provisioning Google Cloud e GitHub OIDC;
- trust policy basata sugli ID numerici immutabili di repository e proprietario;
- indicazioni per limitare l'accesso al branch `main` e, prima della produzione, al workflow o environment autorizzato;
- test sintetici per configurazioni mancanti, malformate e non sicure;
- esclusione Git dei file temporanei `gha-creds-*.json` generati dal runner.

### Modificato

- la documentazione usa `google-github-actions/auth@v3`;
- `README.md`, `ROADMAP.md` e la documentazione delle sorgenti sono allineati al modello WIF/OIDC;
- gli identificatori Google non sensibili sono trattati come GitHub Actions Variables, non come chiavi permanenti.

### Sicurezza

- `GOOGLE_SERVICE_ACCOUNT_JSON`, `GOOGLE_APPLICATION_CREDENTIALS_JSON` e `GCP_SERVICE_ACCOUNT_KEY` vengono rifiutate;
- gli ID di pool e provider con prefisso riservato `gcp-` vengono rifiutati;
- nessuna configurazione IAM reale, credenziale, dato personale, risorsa Google operativa o funzione SMTP è stata attivata.

## [0.8.0] - 2026-07-17

### Aggiunto

- configurazione `riga_intestazioni` nell'adapter Google Sheets;
- costruzione sicura dell'intervallo A1 a partire dalla riga effettiva delle intestazioni;
- conservazione del numero della prima riga dati nella tabella normalizzata;
- test specifici per la struttura reale di `Operativo`, che usa le intestazioni in riga 2.

### Corretto

- le anomalie riportano ora il numero di riga originale del foglio anche quando le intestazioni non sono in riga 1;
- l'adapter non legge più accidentalmente eventuali righe informative poste sopra le intestazioni.

### Sicurezza

- nessun dato personale reale, credenziale o collegamento operativo è stato introdotto;
- gli intervalli di colonna ambigui o già contenenti numeri di riga vengono rifiutati.

## [0.7.0] - 2026-07-17

### Aggiunto

- protocollo `TrasportoNotificheSheets` per leggere, aggiungere e aggiornare righe della tab `NOTIFICHE`;
- adapter `ArchivioNotificheGoogleSheets` indipendente dalle credenziali;
- ricerca esatta e univoca della `notification_id` prima di ogni scrittura;
- append quando la chiave è assente e update della stessa riga quando è già presente;
- fake `TrasportoNotificheMemoria` per testare il comportamento tabellare senza rete;
- ponte `TrasportoNotificheGoogleApi` verso un servizio Sheets già autenticato;
- test per append, update, duplicati, intestazioni, regressioni temporali, configurazione ed escaping A1.

### Sicurezza

- chiavi duplicate o intestazioni diverse dallo schema canonico bloccano ogni scrittura;
- `creato_il` non può cambiare e `aggiornato_il` non può regredire;
- gli errori tecnici di lettura e scrittura vengono convertiti in errori applicativi senza esporre payload o credenziali;
- documentato che ricerca e scrittura Google Sheets non sono una transazione atomica e richiedono anche `concurrency` nel workflow;
- nessuna credenziale, dipendenza Google, risorsa reale o invio SMTP è stato attivato.

## [0.6.0] - 2026-07-17

### Aggiunto

- schema tipizzato della futura tab amministrativa `NOTIFICHE`;
- campi per destinatario, nome, cognome, scadenza, tipo, stato, tentativi, timestamp, `Message-ID`, versione ed errore;
- conversione sicura tra record applicativi e righe tabellari;
- archivio in memoria thread-safe che inserisce o aggiorna una sola riga per `notification_id`;
- documento `docs/SCHEMA_FOGLI.md` con schema e vincoli delle tab amministrative;
- test di round-trip, aggiornamento, duplicati, regressioni temporali e disallineamento delle chiavi.

### Sicurezza

- le chiavi duplicate nella sorgente amministrativa vengono rifiutate;
- `creato_il` non può cambiare e `aggiornato_il` non può regredire;
- candidato e record devono condividere la stessa `notification_id`;
- nessuna scrittura Google o persistenza reale è stata attivata.

## [0.5.0] - 2026-07-17

### Aggiunto

- registro notifiche in memoria con record immutabili e accesso protetto da lock;
- stati `SENDING`, `SENT`, `FAILED_RETRYABLE` e `UNKNOWN_REVIEW_REQUIRED`;
- prenotazione atomica precedente al futuro contatto SMTP;
- retry automatico consentito soltanto da `FAILED_RETRYABLE`;
- registrazione del `Message-ID`, del numero di tentativi e dell'eventuale errore;
- documento `docs/REGISTRO_NOTIFICHE.md` con transizioni e comportamento atteso;
- test di concorrenza e regressione sul ciclo di vita.

### Sicurezza

- `SENT`, `SENDING` e `UNKNOWN_REVIEW_REQUIRED` bloccano nuove prenotazioni automatiche;
- gli esiti SMTP incerti richiedono revisione umana e non vengono reinviati;
- identificativi vuoti, timestamp senza fuso orario e dettagli mancanti vengono rifiutati;
- nessuna persistenza o risorsa reale è stata collegata.

## [0.4.1] - 2026-07-17

### Corretto

- il modello dati ora rispecchia `Operativo`: `nome`, `cognome` ed `email` sono colonne distinte della stessa riga;
- il saluto usa direttamente la colonna `nome`, senza dedurre la prima parola da un nominativo completo;
- i nomi composti vengono mantenuti integralmente;
- `{{cognome}}` e `{{nome_completo}}` sono disponibili nei template;
- aggiunta l'anomalia `COGNOME_MANCANTE` e aggiornati fake, esempi e output `dry-run`.

### Sicurezza

- nome, cognome, email e scadenza devono provenire dalla medesima riga validata;
- eliminato il fallback ambiguo basato sull'ordine del nominativo.

## [0.4.0] - 2026-07-17

### Aggiunto

- protocollo `SorgenteDati` indipendente dalla tecnologia di origine;
- sorgente in memoria per test e simulazioni;
- adapter Google Sheets con lettore di valori iniettato;
- ponte minimale verso un servizio Google API già autenticato;
- conversione delle matrici in record mappati;
- collegamento riutilizzabile tra sorgente e validazione;
- documentazione di configurazione, privilegi minimi e segreti previsti;
- test con fake per adapter e trasporto Google API.

### Sicurezza

- rifiuto di matrici vuote, intestazioni vuote o duplicate e righe non tabellari;
- rifiuto di celle non vuote oltre il numero delle intestazioni;
- conversione degli errori Google in errori applicativi senza esporre payload o credenziali;
- nessuna credenziale, dipendenza Google o risorsa reale aggiunta al repository.

## [0.3.0] - 2026-07-17

### Aggiunto

- compositore puro di messaggi email in versione testo e HTML, senza invio;
- configurazione tipizzata di oggetto, corpo e firma;
- placeholder consentiti per nome, nominativo completo, data di scadenza e giorni residui;
- escaping HTML dei dati personalizzati;
- test dedicati a personalizzazione, placeholder e sicurezza dell'oggetto.

### Modificato

- generazione HTML esplicita per paragrafi, senza manipolazioni basate su slicing.

### Sicurezza

- rifiuto dei placeholder sconosciuti, malformati o privi di valore;
- divieto di ritorni a capo nell'oggetto per prevenire header injection;
- rifiuto esplicito di messaggi privi del nome da inserire nel saluto;
- vincolo esplicito sull'apertura `Ciao {{nome}}, ricevi questa mail...`.

## [0.2.0] - 2026-07-17

### Aggiunto

- contratto dati indipendente dalle intestazioni reali di `Operativo`;
- mappatura configurabile delle colonne;
- validazione strutturata di identificativo, nominativo, email, data e stato;
- supporto iniziale alle date `YYYY-MM-DD` e `GG/MM/AAAA`;
- anomalie con codici stabili, numero di riga e campo interessato;
- esclusione integrale degli ID duplicati;
- conteggi di qualità dei dati nell'output `dry-run`;
- documentazione del contratto dati e roadmap canonica in dieci passi;
- test dedicati alla validazione e ai casi ambigui.

### Modificato

- la CLI non interrompe più l'intera elaborazione per una singola riga non valida;
- la validazione email è condivisa tra ingestione e regole di selezione.

## [0.1.0] - 2026-07-17

### Aggiunto

- struttura Python installabile con layout `src`;
- modelli dati tipizzati per arbitri e candidati alla notifica;
- selezione dei certificati in scadenza entro una finestra inclusiva;
- chiave deterministica anti-duplicazione;
- CLI esclusivamente in modalità `dry-run`;
- dati anonimi di esempio;
- test automatici e workflow CI;
- documentazione iniziale e vincoli di sicurezza.
