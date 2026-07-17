# Stato corrente

**Versione:** 0.5.0  
**Data:** 17 luglio 2026  
**Branch di sviluppo:** `agent/bootstrap-mvp`  
**Pull request:** #2, bozza

## Funziona già

- caricamento di righe anonime da JSON o da sorgente tabellare simulata;
- protocollo indipendente `SorgenteDati`;
- adapter Google Sheets con trasporto iniettato e ponte verso un servizio Google già autenticato;
- conversione sicura di matrici con controlli su intestazioni, righe e celle eccedenti;
- contratto dati con mappatura configurabile delle colonne;
- lettura separata di nome, cognome ed email dalla stessa riga;
- validazione di ID, nome, cognome, email, data e stato;
- raccolta strutturata delle anomalie senza bloccare le righe sane;
- esclusione sicura di tutte le occorrenze degli ID duplicati;
- calcolo dei giorni residui e selezione entro una finestra configurabile;
- chiave anti-duplicazione deterministica;
- registro in memoria con stati `SENDING`, `SENT`, `FAILED_RETRYABLE`, `UNKNOWN_REVIEW_REQUIRED`;
- prenotazione atomica e blocco dei duplicati concorrenti;
- retry consentito soltanto dopo un errore esplicitamente retryable;
- output JSON completo in `dry-run`;
- composizione sicura in memoria di email testo e HTML;
- apertura personalizzata `Ciao {{nome}}, ricevi questa mail...` usando direttamente la colonna `nome`;
- disponibilità di `{{cognome}}` e `{{nome_completo}}` nei template;
- validazione dei placeholder, escaping HTML e protezione dell'oggetto da header injection;
- 44 test automatici previsti e CI.

## Non ancora collegato

- credenziali Google e accesso reale al database `Operativo`;
- intestazioni effettive e valori reali dello stato operativo;
- persistenza del registro nel foglio `NOTIFICHE`;
- foglio amministrativo con `CONFIG`, `DASHBOARD` e `ANOMALIE`;
- SMTP MDaemon;
- firma HTML ufficiale e logo CID;
- workflow programmato di produzione.

## Informazioni esterne ancora necessarie

Per il collegamento reale a `Operativo` servono il nome della scheda, le intestazioni effettive delle colonne, i valori reali dello stato operativo e il formato effettivo della data. È confermato che ogni arbitro occupa una riga e che nome, cognome ed email sono in colonne separate.

Per il messaggio definitivo serviranno inoltre firma ufficiale, eventuale logo e testo approvato; nel frattempo il compositore resta disaccoppiato dall'invio e usa dati sintetici nei test.

## Prossimo incremento

Definire lo schema del foglio amministrativo e un adapter fake/testabile per persistere `NOTIFICHE` e le transizioni del registro, senza credenziali o scritture su Spreadsheet reali.
