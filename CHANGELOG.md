# Changelog

Questo documento registra le versioni recenti e le modifiche rilasciate. Lo storico precedente alla 0.13.0 è disponibile in `docs/CHANGELOG_ARCHIVE.md`.

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
- aggiunti test per nomi singoli e composti.

## [0.14.1] - 2026-07-20

### Modificato

- `CORPO_EMAIL` contiene il messaggio completo, compreso l'eventuale saluto;
- il valore predefinito usa `Ciao {{nome}},` direttamente nel template;
- il renderer non aggiunge più frasi implicite;
- il saluto può essere sostituito, spostato o rimosso dal foglio.

## [0.14.0] - 2026-07-20

### Modificato

- introdotto lo schema amministrativo v3 con una configurazione più semplice;
- mantenuto un solo interruttore per gli invii programmati;
- fissato internamente il limite per esecuzione;
- unificati inizializzazione, aggiornamento e controlli principali;
- separati i workflow manuali ordinari da quelli di manutenzione;
- mantenute configurabili le coordinate di `Operativo` e visibili tutte le tab amministrative.

## [0.13.5] - 2026-07-20

### Modificato

- consolidati i contratti della modalità produttiva e del test manuale;
- semplificate le fonti di verità documentali;
- aggiunti test contro configurazioni duplicate o incoerenti.

## [0.13.4] - 2026-07-20

### Modificato

- escluse dai reminder anche le categorie `Decaduto` e `Non Attivo`.

## [0.13.3] - 2026-07-20

### Modificato

- esclusi esplicitamente anche i `Fuori Quadro`.

## [0.13.2] - 2026-07-20

### Modificato

- la cella vuota di `Fa attività quest'anno` viene interpretata come persona attiva;
- le annotazioni non affermative vengono interpretate come inattività.

## [0.13.1] - 2026-07-20

### Aggiunto

- lettura di `Qualifica` e `Abilitazione` dalla tab `Operativo`;
- esclusione di benemeriti e osservatori dai candidati.

## [0.13.0] - 2026-07-20

### Aggiunto

- schema amministrativo v2 e migrazione controllata;
- lettura delle sole colonne necessarie di `Operativo`;
- registro minimizzato senza nome, cognome o email;
- gestione più rigorosa degli stati di invio e dei tentativi.

## Versioni precedenti

Lo storico completo dalla versione 0.12.0 alla 0.1.0 è disponibile in [`docs/CHANGELOG_ARCHIVE.md`](docs/CHANGELOG_ARCHIVE.md).
