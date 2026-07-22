# Changelog

Questo documento registra le versioni recenti e le modifiche rilasciate; lo storico fino alla 0.12.0 è conservato integralmente in `docs/CHANGELOG_ARCHIVE.md`.

## [0.14.16] - 2026-07-22

### Configurazione SMTP

- rimossa la Variable ridondante `SMTP_FROM`;
- il workflow usa `SMTP_USERNAME` sia per l'autenticazione sia come mittente,
  riducendo il futuro cambio di casella a una Variable e un Secret.

## [0.14.15] - 2026-07-22

### Configurazione SMTP

- classificati host, porta, sicurezza, mittente, Reply-To e username come
  Variables non sensibili dello specifico Environment;
- mantenuta soltanto `SMTP_PASSWORD` nei Secrets;
- reso possibile sostituire l'account tecnico di invio senza modificare codice,
  workflow o fogli Drive.

## [0.14.14] - 2026-07-22

### Processo di rilascio

- resa esplicita nel README la regola di aggiornare checklist e roadmap insieme
  a ogni passo completato;
- aggiunta una regressione documentale che protegge questa definizione di
  completamento;
- riallineate checklist e roadmap alle verifiche effettivamente concluse,
  lasciando aperte le attività prive di evidenza;
- registrate le evidenze già disponibili per backup, accesso in scrittura del
  service account e collaudo sintetico del registro;
- registrata la versione pre-live nominata nella cronologia del foglio, evitando
  una copia Drive separata non necessaria;
- esclusi dal versionamento gli artefatti standard prodotti dalla build locale.

## [0.14.13] - 2026-07-22

### Schema amministrativo

- il runtime accetta esclusivamente la CONFIG v4 e rifiuta ogni versione
  precedente, anche se formalmente completa;
- rimossa la compatibilità transitoria con la CONFIG v3 per mantenere un solo
  contratto operativo;
- `setup-preview` continua a riconoscere i vecchi schemi unicamente per
  descrivere la migrazione, senza usarli nelle operazioni ordinarie.

## [0.14.12] - 2026-07-22

### Firma email

- la firma HTML e quella `text/plain` vengono ora generate da un'unica sorgente
  dati versionata nel codice;
- aggiunta una regressione che confronta i dati visibili delle due
  rappresentazioni e impedisce che divergano;
- rimossa `FIRMA_TESTO` dalle impostazioni del foglio, perché non deve più
  produrre varianti indipendenti della firma istituzionale.

### Migrazione sicura

- introdotto lo schema amministrativo v4 a sei chiavi;
- la migrazione elimina la riga legacy preservando valori e descrizioni delle
  altre chiavi e lasciando gli invii automatici spenti;
- il runtime accetta temporaneamente una CONFIG v3 completa, ignorandone la
  firma, così codice e foglio possono essere aggiornati senza interruzioni;
- gli stati parziali o ambigui tra v3 e v4 vengono rifiutati.

## [0.14.11] - 2026-07-22

### Firma email

- aggiunta la firma HTML istituzionale CIA Lazio in Tahoma 10 pt, con il solo
  nome `CIA Lazio` in grassetto e la riga email in peso normale;
- incorporato tramite CID lo stesso PNG FIP Lazio usato dal generatore di bozze
  MDaemon, senza dipendenze da file del server o immagini remote;
- mantenuta `FIRMA_TESTO` come fallback configurabile per i client che non
  visualizzano HTML, con contatti completi come valore predefinito;
- indirizzo, telefono, email e sito sono collegamenti utilizzabili conservando
  la resa visiva richiesta.

### Sicurezza e verifica

- le risorse inline sono validate per CID, tipo, nome e riferimento nel corpo;
- rimossa la configurazione esterna facoltativa del logo, che poteva produrre
  firme diverse tra ambienti;
- aggiunte regressioni per struttura, stile, assenza di evidenziazione, hash del
  logo e composizione MIME.

## [0.14.10] - 2026-07-21

### Corretto

- `setup-preview` non segnala più una migrazione quando una CONFIG corrente ha
  descrizioni personalizzate;
- le migrazioni reali preservano le note delle chiavi CONFIG esistenti, compresi
  i promemoria operativi non usati dal runtime.

### Verifica e manutenzione

- README e piano di test richiedono per ogni modifica al codice anche il
  collaudo sui fogli Drive collegati, in sola lettura e senza invii SMTP;
- un test di contratto impedisce di rimuovere accidentalmente questa regola;
- nessuna modifica allo schema, ai valori CONFIG, a SMTP o all'attivazione della
  produzione.

## [0.14.9] - 2026-07-21

### Infrastruttura

- aggiornate le Actions ufficiali alle release Node 24 correnti per eliminare gli avvisi di deprecazione Node 20;
- tutti i riferimenti alle Actions sono fissati a commit SHA immutabili, mantenendo accanto la versione leggibile;
- aggiunto Dependabot settimanale per proporre automaticamente gli aggiornamenti delle GitHub Actions fissate.

### Compatibilità e sicurezza

- nessuna modifica alla logica dei reminder, ai fogli, a SMTP o allo schema amministrativo;
- produzione e schedule restano non attive.

## [0.14.8] - 2026-07-21

### Corretto

- gli ID duplicati bloccano tutte le righe rilevanti anche quando una delle occorrenze ha email o dati obbligatori non validi;
- le risposte SMTP temporanee `4xx` di autenticazione, mittente, destinatario e contenuto vengono classificate come ritentabili, mentre le `5xx` restano permanenti;
- un errore del registro durante la classificazione SMTP produce `REVISIONE_RICHIESTA` senza interrompere il riepilogo e senza lasciare un falso esito certo;
- `check` restituisce attenzione in presenza di anomalie dati, `test-smtp` non restituisce più `OK` quando non tenta alcun invio e la revisione del registro segnala anche `FAILED_PERMANENT`;
- la configurazione rifiuta template malformati o placeholder sconosciuti prima di leggere i candidati;
- il collaudo sintetico invalida la cache e rilegge realmente Google Sheets dopo append e update.

### Operatività e manutenzione

- `produzione --max-sends 1..10` consente il rollout controllato da uno, cinque e dieci invii senza modificare lo schema del foglio;
- la data operativa usa esplicitamente `Europe/Rome`, compresi i cambi di ora legale;
- i backup di migrazione locali sono ignorati da Git, creati con permessi `0600` e caricati dal workflow anche se l'applicazione fallisce dopo la loro creazione;
- la CI copre Python 3.11, 3.12 e 3.13 ed esegue Ruff, compilazione e controllo delle dipendenze installate.
- pytest è aggiornato alla serie 9 corretta, eliminando l'advisory noto presente nella precedente serie di sviluppo.

### Sicurezza

- nessuna attivazione della produzione, nessuna schedule e nessun invio reale;
- il limite interno resta 10 e il nuovo argomento può soltanto ridurlo;
- nessuna modifica allo schema amministrativo o ai permessi Google.

## [0.14.7] - 2026-07-21

### Modificato

- le righe di `Operativo` prive di una data di scadenza vengono ignorate senza generare anomalie;
- ID, nome, cognome ed email vengono validati soltanto per persone attive con certificato compreso nella finestra `0..GIORNI_PREAVVISO`;
- i record incompleti con scadenza futura oltre la finestra o già trascorsa non producono anomalie operative;
- il cognome resta obbligatorio insieme a ID, nome ed email per ogni candidato al reminder;
- gli ID duplicati vengono considerati bloccanti soltanto quando più righe con lo stesso ID sono contemporaneamente rilevanti per l'invio.

### Compatibilità e sicurezza

- nessun hardcoding delle righe 3 e 4 o di specifici numeri di tessera;
- nessuna modifica al foglio `Operativo`, ai permessi Google, a SMTP, al registro o ai workflow;
- le date presenti ma malformate continuano a essere segnalate;
- `INVIO_AUTOMATICO_ATTIVO` resta spento e non è stata attivata alcuna schedule produttiva.

## [0.14.6] - 2026-07-21

### Corretto

- le categorie non tenute al certificato vengono escluse prima di validare email e data di scadenza, evitando anomalie inutili per Benemeriti, Osservatori, Fuori Quadro, Decaduti e Non Attivi;
- le date di Google Sheets espresse come seriali numerici, compreso il valore reale `46261`, vengono convertite con l'epoca compatibile `1899-12-30`;
- la politica sulle categorie escluse è ora condivisa tra validazione e selezione, senza logica duplicata;
- aggiunte regressioni per seriali interi, frazionari e testuali e per tutte le categorie escluse.

### Compatibilità e sicurezza

- nessuna modifica ai fogli, alle intestazioni, ai permessi, a SMTP o al registro;
- gli arbitri ordinari continuano a produrre anomalie quando email o scadenza sono realmente mancanti o non valide;
- `INVIO_AUTOMATICO_ATTIVO` resta spento e non è stata attivata alcuna schedule produttiva.

## [0.14.5] - 2026-07-20

### Modificato

- rimosse dalle Environment Variables `OPERATIVO_SHEET_NAME`, `OPERATIVO_HEADER_ROW` e `OPERATIVO_COLUMNS_A1`;
- fissato nel codice il contratto canonico della sorgente: tab `Operativo`, intestazioni alla riga 2 e intervallo `A:AS`;
- l'operatore configura ora soltanto `OPERATIVO_SPREADSHEET_ID` per il foglio sorgente;
- allineati workflow manuale, modello produttivo, documentazione e test di contratto.

### Compatibilità e sicurezza

- nessuna modifica ai dati, alle formule o ai permessi del foglio `Operativo`;
- nessuna modifica a selezione candidati, email, SMTP, registro o schema amministrativo;
- eventuali vecchie Variables strutturali vengono ignorate e possono essere eliminate da GitHub;
- `INVIO_AUTOMATICO_ATTIVO` resta spento e il modello produttivo resta non attivo.

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
