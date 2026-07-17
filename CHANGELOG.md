# Changelog

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
- campo facoltativo `nome_saluto` con fallback alla prima parola del nominativo;
- escaping HTML dei dati personalizzati;
- test dedicati a personalizzazione, fallback, placeholder e sicurezza dell'oggetto.

### Modificato

- generazione HTML esplicita per paragrafi, senza manipolazioni basate su slicing;
- fallback del nome reso sicuro anche davanti a un nominativo vuoto.

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
