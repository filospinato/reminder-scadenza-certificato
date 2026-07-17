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
| `attivo` | appartenenza alla popolazione da elaborare | valore riconosciuto dalla politica di stato configurata |

Non esiste una colonna artificiale `nome_saluto`: il saluto usa la colonna `nome` di Operativo. Un nome composto, per esempio `Anna Maria`, viene mantenuto integralmente.

## Stati riconosciuti nella simulazione

I valori predefiniti sono volutamente generici e saranno verificati sui dati reali prima del collegamento definitivo.

- attivi: `1`, `true`, `sì`, `si`, `attivo`, `operativo`;
- inattivi: `0`, `false`, `no`, `inattivo`, `non operativo`.

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
| `STATO_NON_VALIDO` | riga esclusa |
| `ID_DUPLICATO` | tutte le righe con lo stesso ID vengono escluse |

Le righe interamente vuote vengono ignorate e conteggiate separatamente.

## Regola di sicurezza

Il programma non incrocia righe diverse e non tenta di dedurre nome o cognome da un nominativo composto. Tutti i dati della notifica devono provenire dalla stessa riga valida di Operativo. Le anomalie saranno riportate nel foglio amministrativo `ANOMALIE`, mentre `Operativo` resterà in sola lettura.

## Informazioni necessarie per il collegamento reale

Prima dell'attivazione servono:

1. nome della scheda che contiene gli arbitri;
2. intestazioni effettive delle sei colonne logiche;
3. valori reali che identificano un arbitro operativo e non operativo;
4. conferma del formato effettivo della data;
5. identificativo dello Spreadsheet, conservato fuori dal codice.
