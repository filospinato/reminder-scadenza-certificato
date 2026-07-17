# Stato corrente

**Versione:** 0.8.0  
**Data:** 17 luglio 2026  
**Stato di pubblicazione:** incremento in verifica tramite pull request  
**Baseline di partenza:** `bdb5c2e0d1a926c4bc2e1fac1dd9a2b9aba2cd13`

## Funziona già

- caricamento di righe anonime da JSON o da sorgente tabellare simulata;
- protocollo indipendente `SorgenteDati`;
- adapter Google Sheets di lettura con trasporto iniettato;
- riga delle intestazioni configurabile, inclusa la struttura reale di `Operativo` con intestazioni in riga 2;
- intervallo A1 costruito in modo sicuro dalla riga configurata;
- numeri di riga delle anomalie coerenti con il foglio originale;
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
- schema tipizzato completo della tab `NOTIFICHE`;
- archivio fake thread-safe con insert/update per chiave e controlli temporali;
- adapter `ArchivioNotificheGoogleSheets` con ricerca univoca, append e update controllato;
- fake `TrasportoNotificheMemoria` e ponte `TrasportoNotificheGoogleApi`;
- composizione sicura in memoria di email testo e HTML;
- apertura personalizzata `Ciao {{nome}}, ricevi questa mail...` usando direttamente la colonna `nome`;
- test automatici e CI.

## Sicurezza mantenuta

- nessuna credenziale o chiave permanente nel repository;
- nessun accesso reale a `Operativo`;
- nessun dato personale reale nei test o nella documentazione;
- nessuna scrittura su Spreadsheet reali;
- nessun invio SMTP;
- intervalli A1 ambigui rifiutati invece di essere interpretati implicitamente.

## Non ancora collegato

- autenticazione Google tramite Workload Identity Federation;
- prova su Spreadsheet sintetico;
- collegamento reale in sola lettura a `Operativo`;
- persistenza reale del registro nel foglio amministrativo;
- `CONFIG`, `DASHBOARD` e `ANOMALIE`;
- SMTP MDaemon, firma ufficiale e logo CID;
- workflow programmato di produzione.

## Prossimo incremento

Preparare la configurazione Workload Identity Federation per GitHub Actions e il runbook di provisioning Google Cloud, senza creare chiavi JSON permanenti e senza collegare ancora risorse operative.
