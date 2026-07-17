# Stato corrente

**Versione:** 0.9.0  
**Data:** 17 luglio 2026  
**Stato di pubblicazione:** incremento WIF in verifica tramite pull request  
**Baseline di partenza:** `0dfe8f951fb6ad4445f96b265cea30d8bae64643`

## Funziona già

- MVP completo in `dry-run` con validazione, selezione, template e registro;
- adapter Google Sheets testati con fake per lettura di `Operativo` e persistenza di `NOTIFICHE`;
- intestazioni di `Operativo` configurabili in riga 2 e numeri di riga originali preservati;
- configurazione tipizzata per Workload Identity Federation tramite variabili pubbliche;
- rifiuto esplicito di chiavi JSON permanenti e formati non canonici;
- runbook Google Cloud con trust OIDC limitata al repository, privilegi minimi e recupero umano;
- test automatici e CI.

## Sicurezza mantenuta

- nessuna credenziale, password o chiave permanente nel repository;
- nessuna configurazione IAM/OIDC reale applicata;
- nessun accesso reale a `Operativo`;
- nessun dato personale reale nei test o nella documentazione;
- nessuna scrittura su Spreadsheet reali;
- nessun workflow programmato o invio SMTP.

## Non ancora collegato

- provisioning effettivo di progetto, pool, provider e service account Google Cloud;
- prova manuale su Spreadsheet sintetico;
- creazione controllata di `Reminder certificati CIA Lazio — Gestione`;
- collegamento reale in sola lettura a `Operativo`;
- persistenza reale del registro nel foglio amministrativo;
- `CONFIG`, `DASHBOARD` e `ANOMALIE`;
- SMTP MDaemon, firma ufficiale e logo CID;
- workflow programmato di produzione.

## Prossimo incremento

Definire e testare lo schema iniziale del nuovo Spreadsheet amministrativo separato (`CONFIG`, `NOTIFICHE`, `DASHBOARD`, `ANOMALIE`) usando esclusivamente dati sintetici, senza ancora creare o collegare risorse operative.
