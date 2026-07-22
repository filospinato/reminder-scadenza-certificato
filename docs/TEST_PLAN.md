# Piano di test

Questo documento definisce i controlli automatici e i collaudi necessari per dimostrare correttezza, sicurezza e semplicità operativa del sistema.

## Dati e regole

La suite verifica intestazioni, righe vuote o malformate, identificativi duplicati, date, email, stato di attività e categorie escluse. Nome, cognome, email, scadenza, qualifica e abilitazione devono provenire dalla stessa riga.

Le righe senza data di scadenza devono essere ignorate senza anomalie. ID, nome, cognome ed email devono essere validati soltanto per persone attive con scadenza compresa tra oggi e `GIORNI_PREAVVISO`; dati incompleti fuori finestra non devono produrre anomalie. I duplicati sono bloccanti soltanto quando coinvolgono più righe contemporaneamente rilevanti.

## CONFIG e migrazione

La suite verifica lo schema v4 a tre colonne, le sei chiavi canoniche, l'unico interruttore `INVIO_AUTOMATICO_ATTIVO`, il limite interno non configurabile e la migrazione conservativa dallo schema precedente. Verifica inoltre che la firma HTML e quella `text/plain` derivino dagli stessi dati visibili. Ogni aggiornamento deve lasciare gli invii automatici spenti e preservare destinatario di prova, oggetto e corpo.

## Modalità operative

Il controllo deve funzionare anche con l'invio automatico spento e non deve usare SMTP. La produzione spenta deve fermarsi prima della lettura di `Operativo` e prima dell'inizializzazione SMTP.

Il test SMTP mantiene il comportamento esistente: seleziona un candidato reale, usa `DESTINATARIO_OVERRIDE`, invia al massimo un messaggio e registra una notifica distinta con prefisso `TEST_`.

## Registro e monitoraggio

La suite verifica prenotazione preventiva, deduplicazione, massimo tre tentativi, errori ritentabili e permanenti, esiti incerti non ritentabili e assenza di dati personali nel registro. Dashboard e riepiloghi devono mostrare etichette comprensibili senza cambiare gli stati tecnici persistiti.

## Workflow

Il workflow ordinario deve mostrare soltanto controllo e prova email. Il workflow di manutenzione deve contenere anteprima setup, applicazione setup e collaudo sintetico. Non devono esistere gate, date simulate o conferme duplicate.

Il modello produttivo deve restare non attivo e senza pianificazione automatica fino al go-live, mantenendo Environment protetto, WIF, lock condiviso, i soli ID dei due Spreadsheet e Secrets limitati allo step SMTP. Tab `Operativo`, riga 2 e intervallo `A:AS` sono un contratto applicativo, non Variables GitHub.

## Verifica obbligatoria sui fogli Drive

Ogni modifica al codice, indipendentemente dall'area interessata, deve essere
collaudata sui due Spreadsheet Drive collegati prima di essere considerata
completata o pronta per la produzione. La suite automatica e i trasporti fake
sono necessari, ma non sostituiscono la verifica dell'integrazione reale.

Il collaudo si svolge con `INVIO_AUTOMATICO_ATTIVO=false` e comprende:

1. il workflow di manutenzione con `setup-preview`, controllando che non proponga
   modifiche inattese al foglio amministrativo;
2. il workflow manuale di preproduzione con `check`, verificando preflight Google,
   lettura e validazione aggregate di `Operativo`, CONFIG, dashboard e registro;
3. zero tentativi SMTP e nessun invio durante entrambi i controlli;
4. per modifiche a schema, migrazioni, adapter o persistenza, anche
   `registry-check`, che usa esclusivamente una chiave sintetica;
5. conservazione degli URL dei run e dei risultati aggregati nella PR, nelle note
   di rilascio o nell'handoff della modifica.

`setup-apply` non fa parte del controllo ordinario in sola lettura: si esegue
soltanto quando l'anteprima mostra una modifica attesa, dopo revisione esplicita
e con backup. `test-smtp` richiede un'autorizzazione distinta e non può essere
usato come sostituto del controllo Drive senza invii.

Se WIF, permessi o fogli reali non sono disponibili, il limite deve essere
dichiarato esplicitamente. In quel caso il cambiamento non soddisfa questo
criterio di uscita e non deve essere attivato in produzione.

## Criteri di uscita

- CI completa verde;
- nessun segreto o dato personale nei diff e nei log;
- schema, controllo, test SMTP e registro validati;
- arresto tramite l'unico interruttore provato;
- documentazione coerente con i comandi pubblici;
- collaudi Drive obbligatori completati per ogni modifica al codice, con evidenze
  conservate e nessun invio SMTP implicito;
- altri collaudi esterni completati prima del go-live.
