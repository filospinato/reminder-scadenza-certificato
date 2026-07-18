# Schema dei fogli amministrativi

Il file separato canonico è `Reminder certificati CIA Lazio — Gestione`. Deve essere creato dall'amministratore umano, fuori dal database operativo e da cartelle con condivisione ereditata ampia.

Le tab richieste sono:

```text
CONFIG | NOTIFICHE | DASHBOARD | ANOMALIE
```

L'inizializzatore le crea in questo ordine per uniformità. Il runtime le individua per nome: un successivo riordino visuale non blocca l'automazione.

## Inizializzazione e verifica

`InizializzatoreFoglioAmministrativo` opera tramite un protocollo iniettato, con fake in memoria e ponte Google Sheets.

- Richiede l'ID di uno Spreadsheet già creato e condiviso dall'identità umana.
- Se il file contiene una sola tab completamente vuota, la rinomina in `CONFIG` e aggiunge le altre tre.
- Scrive le matrici canoniche soltanto nelle tab vuote.
- Rilegge i valori dopo ogni inizializzazione.
- Non sovrascrive mai una tab già popolata.
- Durante `init-admin` verifica struttura, larghezza e chiavi.
- Durante le normali esecuzioni verifica soltanto presenza delle tab e riga delle intestazioni, senza rileggere interamente `NOTIFICHE` e `ANOMALIE`.

## Tab `CONFIG`

Intestazioni:

```text
chiave | valore | tipo | descrizione | modificabile
```

| Chiave | Valore iniziale | Modificabile | Scopo |
|---|---:|---:|---|
| `SISTEMA_ATTIVO` | `false` | sì | abilita l'elaborazione dopo il collaudo |
| `INVII_REALI_ABILITATI` | `false` | sì | barriera attivata soltanto nel go-live controllato |
| `MODALITA_TEST` | `true` | sì | usa l'override nei soli test SMTP |
| `KILL_SWITCH` | `true` | sì | blocco operativo immediato |
| `GIORNI_PREAVVISO` | `30` | sì | finestra inclusiva |
| `LIMITE_INVII_PER_ESECUZIONE` | `10` | sì | limite massimo per avvio |
| `DESTINATARIO_OVERRIDE` | vuoto | sì | destinatario del test SMTP |
| `OGGETTO_EMAIL` | predefinito sintetico | sì | oggetto del promemoria |
| `CORPO_EMAIL` | inizia con `ricevi questa mail` | sì | corpo del messaggio |
| `FIRMA_TESTO` | firma provvisoria | sì | da sostituire dopo approvazione |

Il saluto `Ciao {{nome}},` è fisso nel codice e non è duplicato nella CONFIG. Sono stati rimossi i campi che non influenzavano il comportamento applicativo.

Vincoli principali:

- finestra tra 0 e 365 giorni;
- limite tra 1 e 500;
- override richiesto soltanto per `TEST_SMTP`;
- il corpo deve iniziare con `ricevi questa mail`;
- l'oggetto non può contenere ritorni a capo;
- una configurazione dichiarata reale deve avere sistema attivo, modalità test e kill switch disattivati.

Per un dry-run controllato sono sufficienti `SISTEMA_ATTIVO=true`, `KILL_SWITCH=false` e `INVII_REALI_ABILITATI=false`; non servono parametri SMTP.

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
- nome, cognome, email, scadenza e tipo devono coincidere con la notifica persistita;
- più righe con la stessa chiave bloccano l'esecuzione.

L'adapter legge la tab una volta per esecuzione, crea un indice `notification_id → riga` e lo aggiorna localmente dopo append o update. Non rilegge l'intero foglio a ogni transizione.

Il dry-run consulta il registro ma non scrive. La modalità test usa un tipo `TEST_REMINDER_*` separato e registra l'override realmente contattato.

## Tab `DASHBOARD`

Intestazioni:

```text
metrica | valore | descrizione
```

La fotografia aggregata comprende stato, heartbeat UTC, righe lette e valide, candidati, notifiche già presenti, invii, esiti incerti, anomalie, kill switch, versione e codice dell'eventuale errore fatale. Non contiene nominativi o email.

L'adapter usa un singolo `values.update`, senza `clear` preventivo.

## Tab `ANOMALIE`

Intestazioni:

```text
anomalia_id | rilevata_il | severita | origine | codice | riga_sorgente | campo | messaggio | versione_app | risolta_il
```

`anomalia_id` è deterministico per origine, codice, riga, campo e messaggio sintetico. L'adapter legge una volta gli ID ancora aperti e non accoda duplicati a ogni esecuzione. Se una precedente occorrenza viene marcata come risolta, una nuova rilevazione può essere registrata.

Il messaggio è limitato e sanitizzato per rimuovere email, token e chiavi `notification_id`.

## Scritture Google

Tutte le scritture usano `valueInputOption=RAW`.

- l'inizializzatore scrive soltanto in tab vuote;
- `NOTIFICHE` usa append per nuove chiavi e update per le transizioni;
- `DASHBOARD` aggiorna la fotografia in una richiesta;
- `ANOMALIE` accoda soltanto anomalie nuove.

Google Sheets non offre una transazione tra ricerca e scrittura. Le esecuzioni sono quindi serializzate tramite il gruppo `concurrency` condiviso dai workflow.

## Stato operativo

Codice, fake, adapter e test sono presenti. Restano da eseguire esternamente inizializzazione reale, collaudo sintetico del registro, aggiornamento di dashboard/anomalie e prova con un responsabile non tecnico.
