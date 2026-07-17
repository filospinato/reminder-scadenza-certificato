# Contratto dati

Questo documento definisce il formato logico minimo che il programma deve ricevere. I nomi reali delle colonne di `Operativo` saranno collegati tramite una mappatura configurabile: non devono essere inventati nel codice.

## Campi logici obbligatori

| Campo logico | Significato | Regola |
|---|---|---|
| `id_arbitro` | identificativo stabile e univoco | obbligatorio; i duplicati vengono esclusi integralmente |
| `nome` | nominativo usato nel messaggio | obbligatorio |
| `email` | destinatario della notifica | obbligatoria e formalmente valida |
| `scadenza_certificato` | data di scadenza | `YYYY-MM-DD`, `GG/MM/AAAA` o valore data fornito dall'adapter |
| `attivo` | appartenenza alla popolazione da elaborare | valore riconosciuto dalla politica di stato configurata |

## Stati riconosciuti nella simulazione

I valori predefiniti sono volutamente generici e saranno verificati sui dati reali prima del collegamento a `Operativo`.

- attivi: `1`, `true`, `sì`, `si`, `attivo`, `operativo`;
- inattivi: `0`, `false`, `no`, `inattivo`, `non operativo`.

Il confronto testuale non distingue maiuscole e minuscole.

## Anomalie

Le anomalie non interrompono l'intera elaborazione, salvo uno schema privo delle colonne obbligatorie.

| Codice | Comportamento |
|---|---|
| `ID_MANCANTE` | riga esclusa |
| `NOME_MANCANTE` | riga esclusa |
| `EMAIL_NON_VALIDA` | riga esclusa |
| `SCADENZA_NON_VALIDA` | riga esclusa |
| `STATO_NON_VALIDO` | riga esclusa |
| `ID_DUPLICATO` | tutte le righe con lo stesso ID vengono escluse |

Le righe interamente vuote vengono ignorate e conteggiate separatamente.

## Regola di sicurezza

Il programma non sceglie arbitrariamente tra dati ambigui e non corregge automaticamente la sorgente. Le anomalie saranno riportate nel foglio amministrativo `ANOMALIE`, mentre `Operativo` resterà in sola lettura.

## Informazioni necessarie per il collegamento reale

Prima di implementare l'adapter Google Sheets servono:

1. nome della scheda che contiene gli arbitri;
2. intestazioni reali delle cinque colonne logiche;
3. valori reali che identificano un arbitro operativo e non operativo;
4. conferma del formato effettivo della data;
5. identificativo dello Spreadsheet, da conservare fuori dal codice quando opportuno.
