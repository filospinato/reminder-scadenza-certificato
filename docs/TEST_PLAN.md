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
- inizializzatore idempotente e non distruttivo;
- registro con `SENDING` preventivo;
- retry soltanto da `FAILED_RETRYABLE`;
- esiti incerti non ritentati;
- doppia esecuzione bloccata tramite `concurrency`;
- messaggi di errore senza email, token o payload completi;
- MIME testo/HTML, Message-ID e logo CID opzionale;
- assenza di copie nella Posta inviata.

## Collaudo Google sintetico

1. creare il foglio amministrativo vuoto;
2. rieseguire l'inizializzatore e verificare idempotenza;
3. alterare una intestazione su una copia e verificare il blocco;
4. aggiungere una notifica sintetica;
5. aggiornare la stessa notifica;
6. creare un duplicato su una copia e verificare il blocco;
7. simulare revoca accesso e verificare errore aggregato;
8. verificare che i log non contengano celle o righe.

## Collaudo intestazioni Operativo

Il primo accesso deve eseguire soltanto `check-headers`. Il risultato deve contenere numero di intestazioni e conferma delle colonne obbligatorie, con `data_rows_read=0`.

## Collaudo dry-run reale

- usare una data controllata;
- confrontare conteggi aggregati con una verifica manuale ristretta;
- controllare anomalie senza pubblicare contenuti delle righe;
- verificare zero righe aggiunte a `NOTIFICHE`;
- verificare zero chiamate SMTP.

## Collaudo SMTP

1. usare esclusivamente `TEST_SMTP`;
2. impostare un override controllato;
3. verificare testo, HTML, mittente, Reply-To e Message-ID;
4. verificare il logo solo dopo approvazione;
5. simulare errore di connessione prima della consegna;
6. simulare disconnessione durante la consegna;
7. simulare destinatario rifiutato;
8. verificare rispettivamente `FAILED_RETRYABLE` e `UNKNOWN_REVIEW_REQUIRED`;
9. rieseguire la stessa notifica test e verificare deduplicazione.

## Prove di concorrenza e crash

- avviare due workflow manuali: il secondo deve restare in attesa;
- interrompere dopo `SENDING`: la riga non deve essere ritentata automaticamente;
- rilanciare un job GitHub: le notifiche già `SENT` devono essere saltate;
- raggiungere il limite massimo: le eccedenti restano non prenotate.

## Criteri di uscita

- CI verde su `main`;
- nessun segreto o PII nei diff e nei log;
- zero criticità alte o medie aperte;
- dry-run e modalità test validati;
- runbook provato da un responsabile non tecnico;
- seconda identità umana CIA configurata;
- firma, logo e contenuti approvati;
- autorizzazione esplicita al go-live.
