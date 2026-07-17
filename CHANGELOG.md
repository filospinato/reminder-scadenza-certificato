# Changelog

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
