# Changelog

Questo documento registra le versioni più recenti. Lo stato completo precedente alla 0.14.3 è conservato in [`docs/CHANGELOG_SNAPSHOT_0.14.2.md`](docs/CHANGELOG_SNAPSHOT_0.14.2.md); lo storico fino alla 0.12.0 resta in [`docs/CHANGELOG_ARCHIVE.md`](docs/CHANGELOG_ARCHIVE.md).

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

- normalizzazione di `{{nome}}` per nomi singoli e composti provenienti da `Operativo`;
- nessuna modifica ai dati sorgente o alle risorse esterne.

## [0.14.1] - 2026-07-20

- `CORPO_EMAIL` contiene il messaggio completo, compreso il saluto configurabile;
- il renderer non aggiunge frasi implicite.

## [0.14.0] - 2026-07-20

- schema amministrativo v3 e configurazione semplificata;
- un solo interruttore operativo;
- comandi e workflow manuali razionalizzati;
- protezioni interne, registro e credenziali temporanee invariati.

## Versioni precedenti

Per il dettaglio completo delle versioni 0.14.2–0.13.0 consultare [`docs/CHANGELOG_SNAPSHOT_0.14.2.md`](docs/CHANGELOG_SNAPSHOT_0.14.2.md).
