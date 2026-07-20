# Changelog

Questo documento registra le versioni recenti e le modifiche rilasciate; lo storico fino alla 0.12.0 è conservato integralmente in `docs/CHANGELOG_ARCHIVE.md`.

## [0.14.4] - 2026-07-20

### Corretto

- il sanitizzatore dei messaggi riconosce ora qualsiasi identificativo con struttura `ID|DATA|TIPO`, senza dipendere dal vecchio formato `REMINDER_n`;
- coperti gli identificativi produttivi `CERTIFICATO_SCADENZA_V1`, quelli di prova, il formato storico e il collaudo sintetico del registro;
- gestiti anche gli identificativi seguiti da punteggiatura nei messaggi di errore.

### Sicurezza e compatibilità

- tessera, data di scadenza e tipo di notifica non vengono più lasciati nei dettagli sanitizzati quando compare il formato corrente;
- nessuna modifica a selezione dei candidati, email, SMTP, Google Sheets, registro o workflow;
- nessun aggiornamento del foglio amministrativo necessario.

## [0.14.3] - 2026-07-20

### Modificato

- estesa la normalizzazione ai placeholder `{{cognome}}` e `{{nome_completo}}`;
- nome e cognome usano la stessa logica: spazi uniformati e iniziale maiuscola per ogni parte;
- aggiunti test per cognomi semplici, composti, con apostrofo e trattino;
- verificato il nominativo completo `PIER SILVIO DE LUCA` come `Pier Silvio De Luca`.

### Compatibilità

- il foglio `Operativo` resta invariato;
- nessuna modifica a Drive, template, SMTP, registro o workflow;
- nessun backup esterno necessario.

## [0.14.2] - 2026-07-20

### Modificato

- il placeholder `{{nome}}` normalizza i nomi maiuscoli provenienti da `Operativo`;
- ogni parte di un nome composto conserva soltanto l'iniziale maiuscola;
- gli spazi interni ripetuti vengono uniformati prima della composizione della mail;
- aggiunti test espliciti per nomi singoli e composti, tra cui `PIER SILVIO`, `ALFONSO ARIO` e `NICOLA GIULIO`.

### Compatibilità

- nessuna modifica al foglio Drive, ai template, a SMTP, al registro o ai workflow;
- il valore originale in `Operativo` resta invariato e viene normalizzato soltanto durante la composizione del messaggio.

## [0.14.1] - 2026-07-20

### Modificato

- `CORPO_EMAIL` contiene ora il messaggio completo, compreso l'eventuale saluto;
- il valore predefinito usa `Ciao {{nome}},` direttamente nel template del foglio;
- il renderer non aggiunge più saluti o altre frasi implicite;
- l'operatore può sostituire, spostare o rimuovere il saluto modificando soltanto la CONFIG;
- aggiornati test e documentazione senza cambiare lo schema amministrativo v3.

### Compatibilità e sicurezza

- output predefinito testuale e HTML invariato;
- placeholder consentiti e protezioni contro template non validi invariati;
- nessuna modifica a SMTP, registro, selezione dei candidati o workflow.

## [0.14.0] - 2026-07-20

### Modificato

- introdotto lo schema amministrativo v3 con la `CONFIG` ridotta a tre colonne e sette chiavi;
- sostituiti `AUTOMAZIONE_ATTIVA`, `INVII_REALI_ABILITATI` e `PRODUCTION_ENABLED` con il solo `INVIO_AUTOMATICO_ATTIVO`;
- fissato internamente a 10 il limite per esecuzione, rimuovendolo dalle decisioni dell'operatore;
- unificati inizializzazione e migrazione nel comando `setup-admin`, con anteprima e backup automatico quando applica modifiche a un foglio esistente;
- unificati preflight, dry-run e revisione del registro nel comando `check`;
- separati i workflow manuali di uso ordinario e manutenzione;
- rimossi `PREPRODUCTION_ENABLED`, `ALLOW_EMAIL_DELIVERY`, `ALLOW_SYNTHETIC_REGISTRY_WRITE` e le conferme CLI duplicate;
- rimossa la data simulata dai workflow ordinari;
- ridotte le impostazioni SMTP esposte e tradotti gli stati nei riepiloghi e nella dashboard;
- mantenuti configurabili nome tab, riga intestazioni e intervallo di `Operativo`;
- mantenute visibili tutte le tab amministrative.

### Compatibilità e sicurezza

- il test SMTP conserva intenzionalmente il comportamento precedente: candidato reale, destinatario override, massimo un messaggio e registrazione `TEST_`;
- SMTP `PLAIN` resta temporaneamente supportato e protetto da consenso esplicito;
- registro anti-duplicazione, stati SMTP, retry conservativi, WIF/OIDC ed Environment protetti restano invariati;
- il modello produttivo resta non attivo e senza schedule fino al go-live autorizzato;
- la migrazione allo schema v3 lascia sempre `INVIO_AUTOMATICO_ATTIVO=false`.

## [0.13.5] - 2026-07-20

### Modificato

- la doppia conferma `ALLOW_EMAIL_DELIVERY=true` più `--confirm-email-delivery` resta esclusivamente nel test SMTP manuale;
- il comando `produzione` non accetta più il flag di conferma e verifica direttamente `PRODUCTION_ENABLED=true` nel runtime;
- il modello schedulato non imposta conferme automatiche e invoca soltanto `reminder-certificati produzione`;
- README, roadmap, runbook, piano di test e changelog hanno responsabilità distinte e dichiarate;
- eliminato `LATEST.md`, che duplicava versione, stato e prossimi passi;
- la roadmap contiene soltanto lavoro ancora aperto;
- aggiunti test di contratto per impedire il ritorno di pseudo-conferme produttive e documentazione duplicata.

### Sicurezza

- restano obbligatori Environment `production` protetto, `PRODUCTION_ENABLED=true`, `AUTOMAZIONE_ATTIVA=true` e `INVII_REALI_ABILITATI=true`;
- i Secrets SMTP restano confinati al solo step produttivo;
- il workflow schedulato resta un modello non attivo sotto `docs/workflows`.

## [0.13.4] - 2026-07-20

### Modificato

- escluse dai reminder anche le categorie `Decaduto` e `Non Attivo`, quando presenti in `Qualifica` o `Abilitazione`;
- aggiornati test, README e versione senza attivare risorse o invii.

## [0.13.3] - 2026-07-20

### Modificato

- esclusi esplicitamente anche i `Fuori Quadro` dai reminder per il certificato medico;
- aggiornata la copertura di test della regola per qualifica e abilitazione.

## [0.13.2] - 2026-07-20

### Modificato

- la cella vuota di `Fa attività quest'anno` viene interpretata come persona attiva;
- `No` e qualsiasi annotazione non affermativa vengono interpretati come inattività;
- eliminate le anomalie per annotazioni di stato non affermative.

## [0.13.1] - 2026-07-20

### Aggiunto

- lettura di `Qualifica` e `Abilitazione` dalla tab `Operativo`;
- esclusione di benemeriti e osservatori dai candidati al reminder.

## [0.13.0] - 2026-07-20

### Aggiunto

- schema amministrativo v2 e migrazione controllata con anteprima e backup di CONFIG, NOTIFICHE e DASHBOARD;
- lettura delle sole colonne necessarie di `Operativo`;
- registro minimizzato senza nome, cognome o email;
- stato `FAILED_PERMANENT`, massimo tre tentativi e revisione aggregata del registro;
- comando `review-registry` ed exit code non-zero per stati di attenzione o revisione.

### Modificato

- stabilizzata la chiave anti-duplicazione rispetto a `GIORNI_PREAVVISO`;
- esteso il preflight al contenuto reale della CONFIG;
- l'arresto operativo evita anche l'inizializzazione SMTP;
- completata la migrazione della dashboard dal vecchio `kill_switch` a `automazione_attiva`.

## Versioni precedenti

Lo storico completo dalla versione 0.12.0 alla 0.1.0 è disponibile in [`docs/CHANGELOG_ARCHIVE.md`](docs/CHANGELOG_ARCHIVE.md).
