# Stato corrente

**Versione:** 0.10.0  
**Data:** 17 luglio 2026  
**Stato:** contratto sintetico dello Spreadsheet amministrativo completato; nessuna risorsa reale creata  
**Baseline di partenza:** `7efee42e60201f76675e0de73416ee3b38818246`

## Funziona già

- MVP completo in `dry-run` con validazione, selezione, template e registro;
- adapter Google Sheets testati con fake per lettura di `Operativo` e persistenza di `NOTIFICHE`;
- intestazioni di `Operativo` configurabili in riga 2 e numeri di riga originali preservati;
- configurazione tipizzata per Workload Identity Federation senza chiavi permanenti;
- runbook Google Cloud con trust OIDC basata sugli ID numerici immutabili;
- contratto tipizzato dello Spreadsheet `Reminder certificati CIA Lazio — Gestione`;
- tab canoniche `CONFIG`, `NOTIFICHE`, `DASHBOARD` e `ANOMALIE` nell'ordine previsto;
- `CONFIG` inizializzata con sistema e invii reali disabilitati, modalità test e kill switch attivi;
- apertura email preservata tramite `SALUTO_EMAIL = Ciao {{nome}},` e corpo che inizia con `ricevi questa mail`;
- `DASHBOARD` inizializzata in stato disattivato con conteggi a zero;
- `NOTIFICHE` e `ANOMALIE` inizializzate senza righe dati;
- controlli su nome del file, tab mancanti o fuori ordine, intestazioni duplicate e righe malformate;
- test automatici e CI.

## Sicurezza mantenuta

- nessuna credenziale, password o chiave permanente nel repository;
- nessuna configurazione IAM/OIDC reale applicata;
- nessun accesso reale a `Operativo`;
- nessun dato personale reale nei test o nella documentazione;
- nessuna scrittura su Spreadsheet reali;
- invii reali disabilitati e non modificabili nello schema iniziale;
- modalità test e kill switch attivi;
- nessun workflow autenticato o programmato;
- nessun invio SMTP.

## Non ancora collegato

- provisioning effettivo di progetto, pool, provider e service account Google Cloud;
- adapter per creare e inizializzare fisicamente le quattro tab;
- creazione controllata dello Spreadsheet amministrativo separato;
- prova manuale su Spreadsheet sintetico;
- collegamento reale in sola lettura a `Operativo`;
- persistenza reale del registro nel foglio amministrativo;
- lettura e applicazione runtime di `CONFIG`, `DASHBOARD` e `ANOMALIE`;
- SMTP MDaemon, firma ufficiale e logo CID;
- workflow programmato di produzione.

## Prossimo incremento

Implementare un inizializzatore strutturale Google Sheets dietro un protocollo testabile con fake, capace di creare e verificare le quattro tab senza dati personali. Solo dopo test e CI verdi potrà essere usato per la creazione controllata dello Spreadsheet amministrativo separato già autorizzata.
