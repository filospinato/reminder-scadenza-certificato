# Piano di test e hardening

## Test automatici obbligatori

- finestra inclusiva a 0 e 30 giorni;
- esclusione dei certificati scaduti;
- cambio mese, anno e anno bisestile;
- nomi composti conservati integralmente;
- nome, cognome, email e scadenza dalla stessa riga;
- intestazioni mancanti, duplicate o spostate;
- righe corte, celle eccedenti e righe vuote;
- ID duplicati esclusi integralmente;
- apertura obbligatoria ed escaping HTML;
- oggetto con ritorni a capo rifiutato;
- CONFIG con chiavi duplicate, sconosciute o mancanti;
- limiti numerici fuori intervallo;
- modalità test senza override rifiutata;
- kill switch prima della lettura e dell'invio;
- bootstrap di una singola tab vuota, idempotenza e blocco dei file già usati;
- registro con `SENDING` preventivo;
- persistenza del ciclo `SENDING` → `SENT` attraverso la ricreazione dell'adapter;
- percorso `FAILED_RETRYABLE` → nuova prenotazione sulla stessa riga con incremento dei tentativi;
- dry-run che consulta il registro senza scrivere;
- limite applicato dopo la deduplicazione;
- retry soltanto da `FAILED_RETRYABLE`;
- esiti incerti e imprevisti non ritentati;
- doppia esecuzione bloccata tramite `concurrency` condivisa;
- messaggi di errore senza email, token, notification ID o payload completi;
- contratto dei codici diagnostici del preflight e dello schema JSON pubblico;
- corrispondenza esatta tra codici nel sorgente e guida diagnostica;
- MIME testo/HTML, Message-ID e logo CID referenziato;
- nome mittente e CID protetti da header injection;
- test SMTP limitato a una sola email all'override;
- dashboard aggiornata senza `clear` preventivo;
- workflow senza data fissa e senza gate basato prematuramente su variabili Environment;
- preflight e collaudo sintetico esposti come operazioni manuali distinte;
- doppio consenso richiesto per la scrittura sintetica del registro;
- preflight privo di flag di scrittura, consenso email e segreti SMTP;
- modello schedulato mantenuto fuori da `.github/workflows`;
- secondo acknowledgement esterno richiesto prima di autenticazione e produzione schedulata;
- assenza di comandi di bootstrap, preflight, collaudo o modalità non produttive nel modello schedulato;
- segreti SMTP limitati allo step di invio;
- assenza di copie nella Posta inviata.

## Contratto del workflow manuale

`tests/test_manual_preproduction_workflow_contract.py` rende non regressiva la separazione delle operazioni nel workflow `.github/workflows/manual-preproduction.yml`. Il test deve dimostrare che:

1. `google-preflight` e `registry-check` sono operazioni selezionabili e distinte;
2. il preflight richiama soltanto `reminder-certificati-google-preflight`, senza consensi di scrittura o email e senza segreti SMTP;
3. il collaudo del registro richiede sia la conferma nell'input del workflow sia `ALLOW_SYNTHETIC_REGISTRY_WRITE=true` nello step dedicato;
4. i segreti SMTP e `ALLOW_EMAIL_DELIVERY=true` compaiono esclusivamente nello step `test-smtp`;
5. il gate dell'Environment e il gruppo `concurrency` condiviso restano presenti.

Le modifiche future al workflow devono mantenere separate le operazioni di sola lettura, scrittura sintetica e invio SMTP. Un nuovo consenso non può essere riutilizzato implicitamente per un'operazione diversa.

## Contratto del modello schedulato

`tests/test_production_workflow_contract.py` rende non regressivo il modello `docs/workflows/production.yml.example`. Il test deve dimostrare che:

1. il file resta sotto `docs/workflows` e non esiste un workflow attivo `.github/workflows/production.yml`;
2. il modello dichiara esplicitamente di non essere attivo, usa l'Environment `production`, WIF temporaneo e lo stesso gruppo `concurrency` del workflow manuale;
3. il gate richiede contemporaneamente `PRODUCTION_ENABLED=true` e l'acknowledgement esterno `PRODUCTION_WORKFLOW_APPROVED=REMINDER_CERTIFICATI_SCHEDULE_V1` prima del checkout e dell'autenticazione;
4. il modello non contiene `init-admin`, `check-headers`, preflight, collaudo del registro, `DRY_RUN` o `TEST_SMTP`;
5. esiste una sola esecuzione applicativa, in modalità `PRODUZIONE`, con conferma email e acknowledgement applicativo dedicato;
6. tutti i Secrets SMTP, `ALLOW_EMAIL_DELIVERY` e `PRODUCTION_ACTIVATION_ACK` restano limitati allo step produttivo;
7. schedule, vincolo WIF e checklist pre-go-live restano documentati.

La copia futura del modello in `.github/workflows` dovrà essere una modifica esplicita e revisionata. Il semplice spostamento del file non deve bastare ad avviare il sistema: il gate esterno, l'Environment, WIF, CONFIG e gli acknowledgement applicativi devono essere configurati separatamente.

## Contratto della diagnostica preflight

`tests/test_preflight_diagnostics_contract.py` rende non regressiva l'interfaccia pubblica del comando `reminder-certificati-google-preflight`. Il test deve dimostrare che:

1. i sette codici applicativi restano esattamente quelli pubblicati e mantengono il prefisso `PREFLIGHT_`;
2. non esistono codici duplicati;
3. `docs/PREFLIGHT_DIAGNOSTICA.md` elenca una sola volta tutti i codici applicativi e `PREFLIGHT_UNEXPECTED_ERROR`, senza codici aggiuntivi non implementati;
4. l'output JSON di successo mantiene le chiavi pubbliche previste;
5. l'output JSON per errore inatteso mantiene le chiavi pubbliche previste, dichiara zero righe operative e zero scritture e non propaga il dettaglio sensibile originario.

Ogni modifica futura a un codice o allo schema JSON deve quindi essere intenzionale, accompagnata dall'aggiornamento della guida e trattata come cambiamento del contratto operativo.

## Collaudo persistente sintetico automatizzato

`tests/test_notifications_sheets_lifecycle.py` usa esclusivamente `TrasportoNotificheMemoria` e dati sintetici con dominio `.invalid`. Il test deve dimostrare che:

1. la prima prenotazione aggiunge una sola riga `SENDING`;
2. un nuovo adapter, equivalente a un nuovo processo dopo un crash, rilegge la prenotazione persistita;
3. la transizione finale a `SENT` aggiorna la medesima riga e conserva il `Message-ID`;
4. una riga `FAILED_RETRYABLE` può tornare a `SENDING` con `tentativi=2`;
5. nessuno dei passaggi crea righe duplicate.

Questo collaudo non sostituisce la successiva prova controllata sullo Spreadsheet amministrativo reale: verifica in CI il contratto applicativo e il comportamento del fake tabellare senza rete, credenziali o PII.

## Collaudo Google sintetico

1. creare con l'account umano il foglio amministrativo vuoto;
2. condividerlo con il service account e valorizzare `ADMIN_SPREADSHEET_ID`;
3. eseguire l'inizializzatore e verificare la creazione delle quattro tab;
4. rieseguire l'inizializzatore e verificare idempotenza;
5. alterare una intestazione su una copia e verificare il blocco;
6. verificare che una singola tab non vuota non venga rinominata o sovrascritta;
7. ripetere sul foglio la prenotazione sintetica `SENDING` già coperta dal test automatico;
8. simulare un nuovo processo e verificare che la stessa chiave venga riletta senza append;
9. aggiornare la stessa notifica a `SENT` e verificare che rimanga una sola riga;
10. provare il percorso `FAILED_RETRYABLE` e il secondo tentativo sulla stessa riga;
11. creare un duplicato su una copia e verificare il blocco;
12. simulare revoca accesso e verificare errore aggregato;
13. verificare che i log non contengano celle, righe o notification ID.

## Collaudo intestazioni Operativo

Il primo accesso deve eseguire soltanto `check-headers`. Il risultato deve contenere numero di intestazioni e conferma delle colonne obbligatorie, con `data_rows_read=0`.

## Collaudo dry-run reale

- usare la data corrente oppure una data controllata esplicitamente;
- confrontare conteggi aggregati con una verifica manuale ristretta;
- controllare anomalie senza pubblicare contenuti delle righe;
- verificare il conteggio delle notifiche già registrate;
- verificare che i record già presenti non consumino il limite utile;
- verificare zero righe aggiunte o aggiornate in `NOTIFICHE`;
- verificare zero chiamate SMTP.

## Collaudo SMTP

1. usare esclusivamente `TEST_SMTP`;
2. impostare un override controllato;
3. verificare che venga inviata una sola email anche se esistono più candidati;
4. verificare testo, HTML, mittente, Reply-To e Message-ID;
5. verificare che il registro conservi l'override realmente contattato;
6. verificare il logo solo dopo approvazione e controllare il riferimento `cid:` nel corpo HTML;
7. simulare errore di connessione prima della consegna;
8. simulare disconnessione durante la consegna;
9. simulare destinatario rifiutato e un errore non classificato;
10. verificare rispettivamente `FAILED_RETRYABLE` e `UNKNOWN_REVIEW_REQUIRED`;
11. rieseguire la stessa notifica test e verificare deduplicazione.

## Prove di concorrenza e crash

- avviare due workflow manuali: il secondo deve restare in attesa;
- verificare che anche un futuro workflow di produzione usi lo stesso lock;
- interrompere dopo `SENDING`: la riga non deve essere ritentata automaticamente;
- rilanciare un job GitHub: le notifiche già `SENT` devono essere saltate;
- raggiungere il limite massimo: le eccedenti restano non prenotate.

## Criteri di uscita

- CI verde su `main`, compresa installazione dell'extra Google;
- nessun segreto o PII nei diff e nei log;
- zero criticità alte o medie aperte;
- dry-run e modalità test validati;
- runbook provato da un responsabile non tecnico;
- seconda identità umana CIA configurata;
- firma, logo e contenuti approvati;
- autorizzazione esplicita al go-live.
