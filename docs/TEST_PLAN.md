# Piano di test

## Test automatici obbligatori

- finestra inclusiva, scaduti esclusi e cambi di calendario;
- nome, cognome, email e scadenza letti dalla stessa riga;
- nomi composti conservati;
- sole sei intestazioni effettivamente usate come requisito bloccante;
- righe malformate, vuote e ID duplicati;
- saluto personalizzato, corpo libero, placeholder autorizzati, escaping HTML e oggetto sicuro;
- CONFIG con chiavi duplicate, sconosciute, mancanti o valori incoerenti;
- modifiche editoriali a descrizione e metadati CONFIG non bloccanti;
- `AUTOMAZIONE_ATTIVA=false` prima della lettura e dell'invio;
- dry-run senza override o configurazione SMTP;
- override obbligatorio nel solo sottocomando `test-smtp`;
- bootstrap idempotente e tab riordinabili dopo la creazione;
- preflight unico limitato a file, tab e intestazioni;
- una sola lettura completa di `NOTIFICHE` per esecuzione;
- append e update della stessa riga con indice locale aggiornato;
- unica macchina a stati persistente;
- retry soltanto da `FAILED_RETRYABLE`;
- `SENT`, `SENDING` e `UNKNOWN_REVIEW_REQUIRED` bloccanti;
- anomalie aperte deduplicate anche nell'adapter Google;
- output ed errori senza email, token, notification ID o payload;
- MIME testo/HTML, Message-ID e logo CID;
- test SMTP limitato a una sola email all'override;
- dashboard aggiornata senza `clear` preventivo;
- un solo entry point CLI installato;
- workflow con WIF, Environment, lock condiviso e segreti confinati allo step SMTP;
- modello schedulato fuori da `.github/workflows` con una sola schedule giornaliera;
- nessun upgrade dinamico di pip nei workflow.

## Contratti di sicurezza dei workflow

Il workflow manuale deve mantenere separate:

1. operazioni in sola lettura;
2. scrittura sintetica con doppio consenso;
3. test SMTP con consenso e Secrets dedicati.

Tutte le operazioni devono usare il comando `reminder-certificati`.

Il modello produttivo deve:

1. restare non attivo sotto `docs/workflows`;
2. usare Environment `production`, WIF e lo stesso gruppo `concurrency`;
3. richiedere `PRODUCTION_ENABLED=true`;
4. contenere una sola esecuzione applicativa tramite `reminder-certificati produzione`;
5. avere una sola schedule giornaliera;
6. non contenere bootstrap, preflight o modalità di test;
7. esporre i Secrets SMTP soltanto nello step produttivo.

## Diagnostica preflight

I test verificano che:

- i codici siano univoci, prefissati `PREFLIGHT_` e documentati;
- l'output contenga le garanzie minime dichiarate;
- successo ed errore dichiarino zero letture di righe operative e zero scritture;
- il dettaglio sensibile originario non venga propagato.

## Collaudo persistente sintetico

Il fake tabellare deve dimostrare:

1. append di una riga `SENDING`;
2. rilettura della stessa chiave;
3. update a `SENT` sulla medesima riga;
4. retry da `FAILED_RETRYABLE` con incremento dei tentativi;
5. blocco dei duplicati;
6. una sola lettura completa del registro durante un ciclo applicativo.

## Collaudo Google controllato

1. creare con l'account umano il foglio amministrativo vuoto;
2. condividerlo con il service account;
3. eseguire `reminder-certificati init-admin` due volte e verificare idempotenza;
4. riordinare visivamente le tab e verificare che `reminder-certificati preflight` resti verde;
5. alterare un'intestazione su una copia e verificare il blocco;
6. eseguire `reminder-certificati registry-check`;
7. verificare append e update senza righe duplicate;
8. verificare la deduplicazione di un'anomalia aperta;
9. simulare revoca accesso e controllare l'errore aggregato;
10. verificare che i log non contengano celle o identificatori personali.

## Collaudo dry-run reale

Prima del dry-run impostare:

- `AUTOMAZIONE_ATTIVA=true`;
- `INVII_REALI_ABILITATI=false`.

Non è necessario valorizzare `DESTINATARIO_OVERRIDE` o i parametri SMTP.

Eseguire `reminder-certificati dry-run` e verificare conteggi aggregati, deduplicazione, applicazione del limite, zero scritture nel registro e zero chiamate SMTP.

## Collaudo SMTP

1. impostare un override controllato;
2. eseguire `reminder-certificati test-smtp --confirm-email-delivery`;
3. inviare al massimo una email;
4. verificare testo, HTML, mittente, Reply-To e Message-ID;
5. verificare che il registro conservi l'override;
6. simulare errori retryable, permanenti e incerti;
7. verificare che gli esiti incerti non siano ritentati.

## Concorrenza e crash

- due workflow devono condividere il lock;
- un'interruzione dopo `SENDING` non deve causare retry automatici;
- le notifiche `SENT` devono essere saltate;
- le eccedenti il limite devono restare non prenotate.

## Criteri di uscita

- CI verde su `main`;
- nessun segreto o PII nei diff e nei log;
- dry-run e test SMTP validati;
- arresto tramite `AUTOMAZIONE_ATTIVA=false` provato;
- runbook provato da un responsabile non tecnico;
- seconda identità umana CIA configurata;
- firma, logo e contenuti approvati;
- autorizzazione esplicita al go-live.
