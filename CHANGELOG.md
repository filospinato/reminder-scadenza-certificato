# Changelog

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
- rifiuto di celle non vuote oltre le intestazioni;
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
