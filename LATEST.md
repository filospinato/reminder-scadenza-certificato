# Stato corrente

**Versione:** 0.7.0  
**Data:** 17 luglio 2026  
**Stato di pubblicazione:** baseline disponibile su `main`  
**Commit baseline:** `eff46227970c5730b66f1cc91e65570988e27508`  
**Pull request baseline:** #2, mergiata con squash

## Funziona già

- caricamento di righe anonime da JSON o da sorgente tabellare simulata;
- protocollo indipendente `SorgenteDati`;
- adapter Google Sheets di lettura con trasporto iniettato;
- conversione sicura di matrici con controlli su intestazioni, righe e celle eccedenti;
- contratto dati con mappatura configurabile delle colonne;
- lettura separata di nome, cognome ed email dalla stessa riga;
- validazione di ID, nome, cognome, email, data e stato;
- raccolta strutturata delle anomalie senza bloccare le righe sane;
- esclusione sicura di tutte le occorrenze degli ID duplicati;
- calcolo dei giorni residui e selezione entro una finestra configurabile;
- chiave anti-duplicazione deterministica;
- registro in memoria con stati `SENDING`, `SENT`, `FAILED_RETRYABLE`, `UNKNOWN_REVIEW_REQUIRED`;
- prenotazione atomica e blocco dei duplicati concorrenti nel singolo processo;
- retry consentito soltanto dopo un errore esplicitamente retryable;
- schema tipizzato completo della tab `NOTIFICHE`;
- archivio fake thread-safe con insert/update per chiave e controlli temporali;
- adapter `ArchivioNotificheGoogleSheets` con ricerca univoca, append e update controllato;
- fake `TrasportoNotificheMemoria` e ponte `TrasportoNotificheGoogleApi`;
- rifiuto di intestazioni errate, chiavi duplicate e regressioni temporali prima della scrittura;
- escaping corretto dei nomi delle schede negli intervalli A1;
- output JSON completo in `dry-run`;
- composizione sicura in memoria di email testo e HTML;
- apertura personalizzata `Ciao {{nome}}, ricevi questa mail...` usando direttamente la colonna `nome`;
- disponibilità di `{{cognome}}` e `{{nome_completo}}` nei template;
- validazione dei placeholder, escaping HTML e protezione dell'oggetto da header injection;
- test automatici e CI.

## Politica di sviluppo

- `main` remoto è la fonte di verità;
- ogni incremento completo viene sviluppato su un branch breve `agent/<slug>`;
- ogni incremento usa una PR dedicata verso `main`;
- quando test e CI sono verdi e non esistono conflitti o criticità alte/medie, la PR viene mergiata con squash;
- collegamenti reali, credenziali, invii e risorse operative richiedono sempre autorizzazione esplicita.

## Non ancora collegato

- credenziali Google e accesso reale al database `Operativo`;
- intestazioni effettive e valori reali dello stato operativo;
- prova di lettura/scrittura su Spreadsheet sintetico;
- persistenza reale del registro nel foglio `NOTIFICHE`;
- serializzazione del workflow di produzione tramite `concurrency`;
- foglio amministrativo con `CONFIG`, `DASHBOARD` e `ANOMALIE`;
- SMTP MDaemon;
- firma HTML ufficiale e logo CID;
- workflow programmato di produzione.

## Informazioni esterne ancora necessarie

Per il collegamento reale a `Operativo` servono il nome della scheda, le intestazioni effettive delle colonne, i valori reali dello stato operativo e il formato effettivo della data. È confermato che ogni arbitro occupa una riga e che nome, cognome ed email sono in colonne separate.

Per la prova del registro serve uno Spreadsheet sintetico con una tab `NOTIFICHE` e le quattordici intestazioni canoniche. Non deve contenere dati reali. Per il messaggio definitivo serviranno inoltre firma ufficiale, eventuale logo e testo approvato.

## Prossimo incremento

Eseguire una prova controllata su uno Spreadsheet sintetico, costruire l'autenticazione del service account con privilegi minimi e verificare append, update e blocco dei duplicati senza collegare ancora `Operativo` o MDaemon.