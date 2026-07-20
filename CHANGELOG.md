# Changelog

## [0.13.1] - 2026-07-20

### Modificato

- separata l'autorizzazione del test SMTP dal gate di produzione;
- `test-smtp` continua a richiedere `ALLOW_EMAIL_DELIVERY=true` e `--confirm-email-delivery`;
- `produzione` richiede direttamente `PRODUCTION_ENABLED=true` e non accetta più conferme CLI automatiche;
- il modello schedulato non imposta più `ALLOW_EMAIL_DELIVERY` e invoca `reminder-certificati produzione` senza flag cerimoniali;
- il README è diventato una guida stabile, mentre la roadmap contiene soltanto lavoro ancora aperto;
- eliminato `LATEST.md` e ridotta l'issue principale a indice delle fonti di verità;
- aggiunti test di contratto contro la reintroduzione di pseudo-conferme e documentazione duplicata.

### Sicurezza

- restano obbligatori Environment protetto, `PRODUCTION_ENABLED=true`, `AUTOMAZIONE_ATTIVA=true` e `INVII_REALI_ABILITATI=true`;
- la doppia conferma resta confinata al test SMTP manuale;
- i Secrets SMTP restano disponibili soltanto nello step produttivo che li usa.

## [0.13.0] - 2026-07-20

### Aggiunto

- schema amministrativo v2 e migrazione controllata con anteprima e backup di CONFIG, NOTIFICHE e DASHBOARD;
- lettura delle sole colonne necessarie di `Operativo`;
- registro minimizzato senza nome, cognome o email;
- stato `FAILED_PERMANENT`, massimo tre tentativi e revisione aggregata del registro;
- comando `review-registry` ed exit code non-zero per stati di attenzione o revisione.

### Modificato

- stabilizzata la chiave anti-duplicazione rispetto a `GIORNI_PREAVVISO`;
- esteso il preflight al contenuto reale della CONFIG;
- l'arresto operativo evita anche l'inizializzazione SMTP;
- completata la migrazione della dashboard dal vecchio `kill_switch` a `automazione_attiva`.

## [0.12.0] - 2026-07-19

### Modificato

- unificate tutte le operazioni sotto il solo comando `reminder-certificati`, con sottocomandi per inizializzazione, preflight, collaudo registro, dry-run, test SMTP e produzione;
- rimossi la CLI storica, gli entry point separati e il comando duplicato `check-headers`;
- sostituiti `SISTEMA_ATTIVO`, `KILL_SWITCH` e `MODALITA_TEST` con il solo interruttore operativo `AUTOMAZIONE_ATTIVA`;
- la modalità di esecuzione è ora determinata esclusivamente dal sottocomando;
- alleggerita la validazione della CONFIG: restano bloccanti chiavi e valori funzionali, non i metadati descrittivi;
- il corpo email può usare qualsiasi formulazione non vuota con placeholder autorizzati;
- il modello produttivo prevede una sola esecuzione giornaliera;
- documentazione, runbook, handoff, checklist e test riallineati.

### Sicurezza

- mantenuti WIF/OIDC, `Operativo` in sola lettura, Environment protetti, `INVII_REALI_ABILITATI`, consenso SMTP esplicito e doppio consenso per le scritture sintetiche;
- `AUTOMAZIONE_ATTIVA=false` arresta elaborazione e invii prima della lettura completa della sorgente;
- i segreti SMTP restano confinati al solo step di invio;
- gli esiti incerti continuano a non essere ritentati automaticamente.

## [0.11.5] - 2026-07-18

### Aggiunto

- codici diagnostici stabili per gli errori prevedibili del preflight Google;
- struttura tipizzata con codice, messaggio pubblico e azione operativa di runbook;
- documento `docs/PREFLIGHT_DIAGNOSTICA.md` con significato e gestione dei codici;
- test applicativi e CLI contro la propagazione di ID, email e dettagli tecnici.

### Modificato

- versione del pacchetto aggiornata a 0.11.5;
- il comando `reminder-certificati-google-preflight` restituisce JSON aggregato anche in caso di errore;
- README, stato corrente e roadmap descrivono il contratto diagnostico stabile.

### Sicurezza

- le eccezioni del trasporto Google restano collegate internamente ma non vengono riportate nell'output pubblico;
- gli errori inattesi espongono soltanto il nome della classe, non il messaggio originale;
- messaggi e azioni non includono ID degli Spreadsheet, celle, email, token o payload Google;
- il preflight mantiene zero righe operative lette, zero scritture e SMTP disabilitato.

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
