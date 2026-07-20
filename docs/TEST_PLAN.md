# Piano di test

Questo documento definisce i controlli automatici e i collaudi necessari per dimostrare correttezza, sicurezza e semplicità operativa del sistema.

## Dati e regole

La suite verifica intestazioni, righe vuote o malformate, identificativi duplicati, date, email, stato di attività e categorie escluse. Nome, cognome, email, scadenza, qualifica e abilitazione devono provenire dalla stessa riga.

## CONFIG e migrazione

La suite verifica lo schema v3 a tre colonne, le sette chiavi canoniche, l'unico interruttore `INVIO_AUTOMATICO_ATTIVO`, il limite interno non configurabile e la migrazione conservativa dallo schema precedente. Ogni aggiornamento deve lasciare gli invii automatici spenti e preservare destinatario di prova e template.

## Modalità operative

Il controllo deve funzionare anche con l'invio automatico spento e non deve usare SMTP. La produzione spenta deve fermarsi prima della lettura di `Operativo` e prima dell'inizializzazione SMTP.

Il test SMTP mantiene il comportamento esistente: seleziona un candidato reale, usa `DESTINATARIO_OVERRIDE`, invia al massimo un messaggio e registra una notifica distinta con prefisso `TEST_`.

## Registro e monitoraggio

La suite verifica prenotazione preventiva, deduplicazione, massimo tre tentativi, errori ritentabili e permanenti, esiti incerti non ritentabili e assenza di dati personali nel registro. Dashboard e riepiloghi devono mostrare etichette comprensibili senza cambiare gli stati tecnici persistiti.

## Workflow

Il workflow ordinario deve mostrare soltanto controllo e prova email. Il workflow di manutenzione deve contenere anteprima setup, applicazione setup e collaudo sintetico. Non devono esistere gate, date simulate o conferme duplicate.

Il modello produttivo deve restare non attivo e senza pianificazione automatica fino al go-live, mantenendo Environment protetto, WIF, lock condiviso, configurazione di `Operativo` e Secrets limitati allo step SMTP.

## Criteri di uscita

- CI completa verde;
- nessun segreto o dato personale nei diff e nei log;
- schema, controllo, test SMTP e registro validati;
- arresto tramite l'unico interruttore provato;
- documentazione coerente con i comandi pubblici;
- collaudi esterni completati prima del go-live.
