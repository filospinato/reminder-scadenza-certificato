# Schema dei fogli amministrativi

Il file separato canonico è `Reminder certificati CIA Lazio — Gestione`. Deve essere creato dall'amministratore umano, fuori dal database operativo e da cartelle con condivisione ereditata ampia.

Le tab richieste sono:

```text
CONFIG | NOTIFICHE | DASHBOARD | ANOMALIE
```

L'inizializzatore le crea in questo ordine per uniformità. Il runtime le individua per nome: un successivo riordino visuale non blocca l'automazione.

## Inizializzazione e verifica

- Richiede l'ID di uno Spreadsheet già creato e condiviso dall'identità umana.
- Se il file contiene una sola tab completamente vuota, la rinomina in `CONFIG` e aggiunge le altre tre.
- Scrive le matrici canoniche soltanto nelle tab vuote.
- Non sovrascrive mai una tab già popolata.
- Durante le normali esecuzioni verifica presenza delle tab e riga delle intestazioni.

## Tab `CONFIG`

Intestazioni:

```text
chiave | valore | tipo | descrizione | modificabile
```

| Chiave | Valore iniziale | Scopo |
|---|---:|---|
| `AUTOMAZIONE_ATTIVA` | `false` | unico interruttore operativo; `false` arresta elaborazione e invii |
| `INVII_REALI_ABILITATI` | `false` | seconda barriera attivata soltanto nel go-live controllato |
| `GIORNI_PREAVVISO` | `30` | finestra inclusiva |
| `LIMITE_INVII_PER_ESECUZIONE` | `10` | limite massimo per avvio |
| `DESTINATARIO_OVERRIDE` | vuoto | destinatario del test SMTP |
| `OGGETTO_EMAIL` | predefinito sintetico | oggetto del promemoria |
| `CORPO_EMAIL` | testo predefinito | corpo del messaggio |
| `FIRMA_TESTO` | firma provvisoria | da sostituire dopo approvazione |

La modalità non è conservata nel foglio: viene determinata dal sottocomando `dry-run`, `test-smtp` o `produzione`.

Il saluto `Ciao {{nome}},` è fisso nel codice. Il corpo è liberamente modificabile e può usare soltanto i placeholder autorizzati.

Vincoli principali:

- finestra tra 0 e 365 giorni;
- limite tra 1 e 500;
- override richiesto soltanto per `test-smtp`;
- oggetto, corpo e firma non possono essere vuoti;
- l'oggetto non può contenere ritorni a capo;
- `INVII_REALI_ABILITATI=true` richiede `AUTOMAZIONE_ATTIVA=true`.

Le colonne descrittive `tipo`, `descrizione` e `modificabile` aiutano l'operatore, ma il runtime non si blocca per una loro modifica editoriale.

## Tab `NOTIFICHE`

Intestazioni:

```text
notification_id | id_arbitro | nome | cognome | email | scadenza_certificato | tipo | stato | tentativi | creato_il | aggiornato_il | message_id | versione_app | errore
```

La chiave è:

```text
ID_ARBITRO|DATA_SCADENZA|TIPO_NOTIFICA
```

Regole:

- la prenotazione crea `SENDING` prima della chiamata SMTP;
- `SENT`, `SENDING` e `UNKNOWN_REVIEW_REQUIRED` bloccano nuovi tentativi;
- soltanto `FAILED_RETRYABLE` può tornare a `SENDING`;
- `creato_il` è immutabile e `aggiornato_il` non può regredire;
- più righe con la stessa chiave bloccano l'esecuzione.

L'adapter legge la tab una volta per esecuzione, crea un indice `notification_id → riga` e lo aggiorna localmente dopo append o update.

## Tab `DASHBOARD`

Intestazioni:

```text
metrica | valore | descrizione
```

La fotografia aggregata comprende stato, heartbeat UTC, righe lette e valide, candidati, notifiche già presenti, invii, esiti incerti, anomalie, `automazione_attiva`, versione e codice dell'eventuale errore fatale. Non contiene nominativi o email.

## Tab `ANOMALIE`

Intestazioni:

```text
anomalia_id | rilevata_il | severita | origine | codice | riga_sorgente | campo | messaggio | versione_app | risolta_il
```

`anomalia_id` è deterministico. L'adapter legge una volta gli ID ancora aperti e non accoda duplicati a ogni esecuzione. Il messaggio è limitato e sanitizzato.

## Scritture Google

Tutte le scritture usano `valueInputOption=RAW`.

- l'inizializzatore scrive soltanto in tab vuote;
- `NOTIFICHE` usa append per nuove chiavi e update per le transizioni;
- `DASHBOARD` aggiorna la fotografia in una richiesta;
- `ANOMALIE` accoda soltanto anomalie nuove.

Google Sheets non offre una transazione tra ricerca e scrittura. Le esecuzioni sono serializzate tramite il gruppo `concurrency` condiviso dai workflow.
