# Schema dei fogli amministrativi

Il file separato canonico è `Reminder certificati CIA Lazio — Gestione`. Deve essere creato dall'amministratore umano, fuori dal database operativo e da cartelle con condivisione ereditata ampia.

Le tab devono esistere una sola volta e nell'ordine:

```text
CONFIG | NOTIFICHE | DASHBOARD | ANOMALIE
```

## Inizializzazione e verifica

`InizializzatoreFoglioAmministrativo` opera tramite un protocollo iniettato, con fake in memoria e ponte Google Sheets.

- Richiede l'ID di uno Spreadsheet già creato e condiviso dall'identità umana.
- Se il file contiene una sola tab completamente vuota, la rinomina in `CONFIG` e aggiunge le altre tre tab nell'ordine canonico.
- Se le quattro tab esistono già, ne verifica l'ordine.
- Scrive le matrici canoniche soltanto nelle tab vuote.
- Rilegge i valori dopo ogni inizializzazione.
- Non sovrascrive mai una tab già popolata.
- Verifica ordine delle tab, intestazioni, larghezza delle righe e chiavi strutturali.
- Accetta i normali aggiornamenti runtime di CONFIG e DASHBOARD e le righe aggiunte a NOTIFICHE e ANOMALIE.
- Blocca file con più tab non canoniche, singola tab non vuota, intestazioni alterate, chiavi duplicate o strutture incomplete.

L'operazione è idempotente: una seconda esecuzione su un foglio conforme non aggiunge tab o righe. Il service account non crea e non possiede il file.

## Tab `CONFIG`

Intestazioni:

```text
chiave | valore | tipo | descrizione | modificabile
```

I tipi previsti sono `BOOLEANO`, `INTERO`, `TESTO`, `EMAIL_OPZIONALE` e `TEMPLATE`.

| Chiave | Valore iniziale | Modificabile | Scopo |
|---|---:|---:|---|
| `SISTEMA_ATTIVO` | `false` | sì | abilita l'elaborazione dopo il collaudo |
| `INVII_REALI_ABILITATI` | `false` | no | barriera separata per SMTP reale |
| `MODALITA_TEST` | `true` | sì | usa il destinatario sostitutivo |
| `KILL_SWITCH` | `true` | sì | blocco operativo immediato |
| `GIORNI_PREAVVISO` | `30` | sì | finestra inclusiva |
| `LIMITE_INVII_PER_ESECUZIONE` | `10` | sì | limite massimo per avvio |
| `DESTINATARIO_OVERRIDE` | vuoto | sì | destinatario dei test SMTP |
| `OGGETTO_EMAIL` | predefinito sintetico | sì | oggetto del promemoria |
| `SALUTO_EMAIL` | `Ciao {{nome}},` | no | saluto fisso dalla colonna Nome |
| `CORPO_EMAIL` | inizia con `ricevi questa mail` | sì | corpo del messaggio |
| `FIRMA_TESTO` | firma provvisoria | sì | da sostituire dopo approvazione |
| `CONTATTO_SUPPORTO` | vuoto | sì | contatto organizzativo |

`runtime_config.carica_configurazione` richiede tutte e sole le chiavi canoniche, verifica tipo, descrizione e attributo `modificabile`, rifiuta duplicati e interpreta i valori.

Vincoli principali:

- finestra tra 0 e 365 giorni;
- limite tra 1 e 500;
- modalità test attiva con sistema attivo richiede un override valido;
- `SALUTO_EMAIL` non può cambiare;
- il corpo deve iniziare con `ricevi questa mail`;
- l'oggetto non può contenere ritorni a capo;
- una configurazione dichiarata reale deve avere sistema attivo, modalità test e kill switch disattivati.

La configurazione del foglio non basta da sola per inviare: servono anche il consenso del comando e dell'Environment.

## Tab `NOTIFICHE`

Intestazioni, nell'ordine:

```text
notification_id | id_arbitro | nome | cognome | email | scadenza_certificato | tipo | stato | tentativi | creato_il | aggiornato_il | message_id | versione_app | errore
```

Una riga rappresenta lo stato corrente di una sola chiave:

```text
ID_ARBITRO|DATA_SCADENZA|TIPO_NOTIFICA
```

Regole:

- la prenotazione crea `SENDING` prima della chiamata SMTP;
- `SENT`, `SENDING` e `UNKNOWN_REVIEW_REQUIRED` bloccano nuovi tentativi;
- soltanto `FAILED_RETRYABLE` può tornare a `SENDING`;
- `creato_il` è immutabile e `aggiornato_il` non può regredire;
- nome, cognome, email, scadenza e tipo devono coincidere con la notifica persistita;
- più righe con la stessa chiave bloccano l'esecuzione;
- testo tecnico e Message-ID vengono limitati a lunghezze controllate.

Il dry-run consulta la tab per saltare le chiavi già presenti ma non scrive. Il limite viene applicato dopo questa deduplicazione.

La modalità test usa un tipo `TEST_REMINDER_*`, separato dalle chiavi reali. Nel campo `email` viene salvato il destinatario override realmente contattato e ogni esecuzione tenta al massimo un messaggio.

## Tab `DASHBOARD`

Intestazioni:

```text
metrica | valore | descrizione
```

All'inizio la tab contiene stato disattivato, heartbeat vuoto, conteggi a zero e kill switch attivo. Durante l'esecuzione viene aggiornata con una fotografia aggregata che comprende:

- stato del sistema;
- ultima esecuzione e heartbeat UTC;
- righe lette e valide;
- candidati;
- notifiche già presenti;
- invii tentati, riusciti e falliti;
- esiti incerti;
- anomalie;
- stato del kill switch;
- versione applicativa;
- codice sintetico dell'eventuale errore fatale.

La dashboard non contiene nominativi, email o contenuti delle righe. L'adapter usa un singolo `values.update`: non esegue prima un `clear` che potrebbe lasciare la tab vuota in caso di errore intermedio.

## Tab `ANOMALIE`

Intestazioni:

```text
anomalia_id | rilevata_il | severita | origine | codice | riga_sorgente | campo | messaggio | versione_app | risolta_il
```

`anomalia_id` è deterministico per origine, codice, riga, campo e messaggio sintetico. Il fake in memoria evita la duplicazione indefinita della stessa anomalia aperta.

Il messaggio:

- è limitato a 500 caratteri;
- non contiene intere righe o certificati;
- rimuove indirizzi email, stringhe simili a token e chiavi `notification_id`;
- usa codici stabili per distinguere dati, registro, template, Google e SMTP.

## Scritture Google

Tutte le scritture usano `valueInputOption=RAW`.

- L'inizializzatore scrive una matrice soltanto in tab vuote.
- `NOTIFICHE` usa append per nuove chiavi e update della stessa riga per le transizioni.
- `DASHBOARD` aggiorna la fotografia aggregata in un'unica richiesta.
- `ANOMALIE` accoda righe minimizzate.

Google Sheets non offre una transazione tra ricerca e scrittura. I controlli sul foglio sono quindi affiancati da un gruppo `concurrency` condiviso dai workflow, senza annullare le verifiche di chiavi duplicate.

## Stato operativo

Codice, fake, adapter e test sono presenti. Restano da eseguire esternamente:

- creazione umana e condivisione del foglio reale vuoto;
- prova idempotente dell'inizializzatore;
- append, update e duplicati su un foglio sintetico;
- aggiornamento reale di dashboard e anomalie;
- collaudo con un responsabile non tecnico.
