# Piano di test

Questo documento definisce i controlli automatici e i collaudi necessari per dimostrare che il sistema è corretto, sicuro e pronto al rilascio; non registra lo stato corrente del progetto.

## Test automatici obbligatori

- finestra inclusiva, scaduti esclusi e cambi di calendario;
- nome, cognome, email, scadenza, qualifica e abilitazione letti dalla stessa riga;
- otto intestazioni effettivamente usate come requisito bloccante;
- cella vuota di `Fa attività quest'anno` interpretata come attività e annotazioni non affermative come inattività;
- esclusione di benemeriti, osservatori, fuori quadro, decaduti e non attivi;
- righe malformate, vuote e ID duplicati;
- saluto personalizzato, corpo libero, placeholder autorizzati, escaping HTML e oggetto sicuro;
- CONFIG con chiavi duplicate, sconosciute, mancanti o valori incoerenti;
- `AUTOMAZIONE_ATTIVA=false` prima della lettura e dell'invio;
- dry-run senza override o configurazione SMTP;
- override e doppia conferma obbligatori nel solo sottocomando `test-smtp`;
- `produzione` protetta da `PRODUCTION_ENABLED=true` senza conferme CLI automatiche;
- bootstrap idempotente, migrazione con backup e preflight completo;
- una sola lettura completa di `NOTIFICHE` per esecuzione;
- append e update della stessa riga con indice locale aggiornato;
- retry soltanto da `FAILED_RETRYABLE` e blocco degli esiti incerti;
- output ed errori senza email, token, notification ID o payload;
- MIME testo/HTML, Message-ID e logo CID;
- test SMTP limitato a una sola email all'override;
- dashboard aggiornata senza `clear` preventivo;
- un solo entry point CLI installato;
- workflow con WIF, Environment, lock condiviso e segreti confinati allo step SMTP;
- modello schedulato fuori da `.github/workflows` con una sola schedule giornaliera;
- documentazione senza file di stato duplicati e con fonti di verità esplicite;
- nessun upgrade dinamico di pip nei workflow.

## Contratti di sicurezza dei workflow

Il workflow manuale deve mantenere separate:

1. operazioni in sola lettura;
2. scrittura sintetica con doppio consenso;
3. test SMTP con consenso e Secrets dedicati.

Il modello produttivo deve:

1. restare non attivo sotto `docs/workflows`;
2. usare Environment `production`, WIF e lo stesso gruppo `concurrency`;
3. richiedere `PRODUCTION_ENABLED=true` sia nel gate del workflow sia nel runtime;
4. contenere una sola esecuzione applicativa tramite `reminder-certificati produzione`;
5. non contenere `ALLOW_EMAIL_DELIVERY` o `--confirm-email-delivery`;
6. avere una sola schedule giornaliera;
7. non contenere bootstrap, preflight o modalità di test;
8. esporre i Secrets SMTP soltanto nello step produttivo.

## Collaudo Google controllato

1. creare con l'account umano il foglio amministrativo vuoto;
2. condividerlo con il service account;
3. eseguire `init-admin` due volte e verificare idempotenza;
4. eseguire la migrazione in anteprima e poi con backup;
5. verificare che entrambi gli interruttori restino disattivati;
6. eseguire `preflight` e il collaudo sintetico di `NOTIFICHE`;
7. verificare append, update, deduplicazione e revoca dei permessi;
8. controllare che i log non contengano celle o identificatori personali.

## Collaudo dry-run reale

Impostare `AUTOMAZIONE_ATTIVA=true` e `INVII_REALI_ABILITATI=false`, quindi eseguire `reminder-certificati dry-run`. Verificare conteggi aggregati, applicazione delle regole di categoria, deduplicazione, limite, zero scritture nel registro e zero chiamate SMTP.

## Collaudo SMTP

1. impostare un override controllato;
2. eseguire `ALLOW_EMAIL_DELIVERY=true reminder-certificati test-smtp --confirm-email-delivery`;
3. inviare al massimo una email;
4. verificare testo, HTML, mittente, Reply-To e Message-ID;
5. simulare errori ritentabili, permanenti e incerti;
6. verificare che gli esiti incerti non siano ritentati.

## Criteri di uscita

- CI verde su `main`;
- nessun segreto o PII nei diff e nei log;
- dry-run e test SMTP validati;
- arresto tramite `AUTOMAZIONE_ATTIVA=false` provato;
- runbook provato da un responsabile non tecnico;
- seconda identità umana CIA configurata;
- firma, logo e contenuti approvati;
- autorizzazione esplicita al go-live.
