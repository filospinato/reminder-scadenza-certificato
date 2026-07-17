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
- MIME testo/HTML, Message-ID e logo CID referenziato;
- nome mittente e CID protetti da header injection;
- test SMTP limitato a una sola email all'override;
- dashboard aggiornata senza `clear` preventivo;
- workflow senza data fissa e senza gate basato prematuramente su variabili Environment;
- segreti SMTP limitati allo step di invio;
- assenza di copie nella Posta inviata.

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
