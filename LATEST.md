# Stato corrente

**Versione:** 0.1.0  
**Data:** 17 luglio 2026  
**Branch di sviluppo:** `agent/bootstrap-mvp`

## Funziona già

- caricamento di dati anonimi da JSON;
- calcolo dei giorni residui;
- selezione entro una finestra configurabile;
- chiave anti-duplicazione deterministica;
- output JSON in `dry-run`;
- test e CI.

## Non ancora collegato

- Google Sheets / Operativo;
- foglio `CONFIG`, dashboard e registro;
- SMTP MDaemon;
- firma HTML ufficiale;
- workflow programmato di produzione.

## Prossimo incremento

Definire il contratto dei fogli Google e il livello di validazione dei dati, mantenendo il `dry-run` come comportamento predefinito.
