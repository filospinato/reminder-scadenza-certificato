# Contratto dati

Questo documento definisce il formato logico minimo ricevuto da `Operativo`. Ogni arbitro occupa una riga; nome, cognome, email, scadenza e stato sono letti dalle rispettive colonne della stessa riga.

## Campi logici obbligatori

| Campo logico | Significato | Regola |
|---|---|---|
| `id_arbitro` | identificativo stabile e univoco | obbligatorio; i duplicati vengono esclusi integralmente |
| `nome` | nome della persona | obbligatorio; usato direttamente dopo `Ciao` |
| `cognome` | cognome della persona | obbligatorio; unito a `nome` quando serve il nominativo completo |
| `email` | destinatario della notifica | obbligatoria e formalmente valida |
| `scadenza_certificato` | data di scadenza | `YYYY-MM-DD`, `GG/MM/AAAA` o valore data fornito dall'adapter |
| `attivo` | appartenenza alla popolazione da elaborare | vuoto o valore affermativo = attivo; ogni annotazione non affermativa = inattivo |

Non esiste una colonna artificiale `nome_saluto`: il saluto usa la colonna `nome` di Operativo. Un nome composto, per esempio `Anna Maria`, viene mantenuto integralmente.

## Stati riconosciuti

- attivi: `1`, `true`, `sì`, `si`, `attivo`, `operativo`;
- inattivi espliciti: `0`, `false`, `no`, `inattivo`, `non operativo`;
- la cella vuota è attiva per convenzione di `Operativo`;
- qualsiasi altro testo non affermativo è inattivo.

Il confronto testuale non distingue maiuscole e minuscole.

## Anomalie

Le anomalie non interrompono l'intera elaborazione, salvo uno schema privo delle colonne obbligatorie.

| Codice | Comportamento |
|---|---|
| `ID_MANCANTE` | riga esclusa |
| `NOME_MANCANTE` | riga esclusa |
| `COGNOME_MANCANTE` | riga esclusa |
| `EMAIL_NON_VALIDA` | riga esclusa |
| `SCADENZA_NON_VALIDA` | riga esclusa |
| `ID_DUPLICATO` | tutte le righe con lo stesso ID vengono escluse |

Le righe interamente vuote, le righe senza scadenza e le categorie non tenute al certificato vengono ignorate. ID, nome, cognome, email e duplicati vengono controllati soltanto per scadenze attive nella finestra di preavviso; un duplicato resta bloccante anche se una delle occorrenze ha altri dati non validi.

## Regola di sicurezza

Il programma non incrocia righe diverse e non tenta di dedurre nome o cognome da un nominativo composto. Tutti i dati della notifica devono provenire dalla stessa riga valida di Operativo. Le anomalie saranno riportate nel foglio amministrativo `ANOMALIE`, mentre `Operativo` resterà in sola lettura.

## Collegamento reale

Il contratto canonico è fissato nel codice: tab `Operativo`, intestazioni alla riga 2, intervallo `A:AS` e otto colonne comprendenti anche `Qualifica` e `Abilitazione`. Fuori dal codice viene configurato soltanto `OPERATIVO_SPREADSHEET_ID`.
