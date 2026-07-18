# Piano di test

## Test automatici obbligatori

- finestra inclusiva, scaduti esclusi e cambi di calendario;
- nome, cognome, email e scadenza letti dalla stessa riga;
- nomi composti conservati;
- sole sei intestazioni effettivamente usate come requisito bloccante;
- righe malformate, vuote e ID duplicati;
- apertura obbligatoria, escaping HTML e oggetto sicuro;
- CONFIG con chiavi duplicate, sconosciute, mancanti o valori incoerenti;
- dry-run attivo senza override o configurazione SMTP;
- override obbligatorio nella sola modalità `TEST_SMTP`;
- kill switch prima della lettura e dell'invio;
- bootstrap idempotente e tab riordinabili dopo la creazione;
- verifica runtime limitata a metadati e intestazioni;
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
- workflow con WIF, Environment, lock condiviso e segreti confinati allo step SMTP;
- modello schedulato fuori da `.github/workflows`;
- nessun upgrade dinamico di pip nei workflow.

## Contratti di sicurezza dei workflow

I test dei workflow verificano proprietà operative, non nomi italiani degli step o conteggi testuali fragili.

Il workflow manuale deve mantenere separate:

1. operazioni in sola lettura;
2. scrittura sintetica con doppio consenso;
3. test SMTP con consenso e Secrets dedicati.

Il modello produttivo deve:

1. restare non attivo sotto `docs/workflows`;
2. usare Environment `production`, WIF e lo stesso gruppo `concurrency`;
3. richiedere `PRODUCTION_ENABLED=true`;
4. contenere una sola esecuzione applicativa in modalità `PRODUZIONE`;
5. non contenere bootstrap, preflight o modalità di test;
6. esporre i Secrets SMTP soltanto nello step produttivo.

## Diagnostica preflight

I test verificano che:

- i codici siano univoci, prefissati `PREFLIGHT_` e documentati;
- l'output contenga le garanzie minime dichiarate;
- successo ed errore dichiarino zero letture di righe operative e zero scritture;
- il dettaglio sensibile originario non venga propagato.

Aggiungere un campo JSON o riordinare un enum non deve rompere la CI se il contratto di sicurezza rimane invariato.

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
3. eseguire `init-admin` due volte e verificare idempotenza;
4. riordinare visivamente le tab e verificare che il preflight resti verde;
5. alterare un'intestazione su una copia e verificare il blocco;
6. eseguire il collaudo sintetico del registro;
7. verificare append e update senza righe duplicate;
8. verificare la deduplicazione di un'anomalia aperta;
9. simulare revoca accesso e controllare l'errore aggregato;
10. verificare che i log non contengano celle o identificatori personali.

## Collaudo dry-run reale

Prima del dry-run impostare:

- `SISTEMA_ATTIVO=true`;
- `KILL_SWITCH=false`;
- `INVII_REALI_ABILITATI=false`.

Non è necessario valorizzare `DESTINATARIO_OVERRIDE` o i parametri SMTP.

Verificare conteggi aggregati, deduplicazione, applicazione del limite, zero scritture nel registro e zero chiamate SMTP.

## Collaudo SMTP

1. usare esclusivamente `TEST_SMTP`;
2. impostare un override controllato;
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
- dry-run e modalità test validati;
- runbook provato da un responsabile non tecnico;
- seconda identità umana CIA configurata;
- firma, logo e contenuti approvati;
- autorizzazione esplicita al go-live.
