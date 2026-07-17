# Schema dei fogli amministrativi

Questo documento definisce il contratto logico dello Spreadsheet separato `Reminder certificati CIA Lazio — Gestione`. Il codice produce esclusivamente una struttura iniziale sintetica: non crea ancora lo Spreadsheet, non legge dati personali e non attiva invii.

Le tab devono esistere una sola volta e nell'ordine canonico:

```text
CONFIG | NOTIFICHE | DASHBOARD | ANOMALIE
```

Il modulo `admin_schema` valida nome del file, nomi e ordine delle tab, intestazioni, duplicati e larghezza delle righe iniziali.

## Tab `CONFIG`

Intestazioni:

```text
chiave | valore | tipo | descrizione | modificabile
```

Ogni riga rappresenta una singola impostazione. I tipi previsti sono `BOOLEANO`, `INTERO`, `TESTO`, `EMAIL_OPZIONALE` e `TEMPLATE`.

La configurazione iniziale è deliberatamente bloccata:

| Chiave | Valore iniziale | Modificabile | Scopo |
|---|---:|---:|---|
| `SISTEMA_ATTIVO` | `false` | sì | abilita l'elaborazione soltanto dopo collaudo |
| `INVII_REALI_ABILITATI` | `false` | no | barriera separata contro invii SMTP accidentali |
| `MODALITA_TEST` | `true` | sì | forza l'uso del destinatario sostitutivo |
| `KILL_SWITCH` | `true` | sì | blocco operativo immediato |
| `GIORNI_PREAVVISO` | `30` | sì | finestra inclusiva dei certificati in scadenza |
| `LIMITE_INVII_PER_ESECUZIONE` | `10` | sì | limite massimo per singolo avvio |
| `DESTINATARIO_OVERRIDE` | vuoto | sì | deve essere valorizzato prima di prove di invio |
| `OGGETTO_EMAIL` | valore sintetico predefinito | sì | oggetto del promemoria |
| `SALUTO_EMAIL` | `Ciao {{nome}},` | no | saluto fisso dalla colonna `nome` della stessa riga |
| `CORPO_EMAIL` | inizia con `ricevi questa mail` | sì | corpo del messaggio |
| `FIRMA_TESTO` | firma testuale provvisoria | sì | firma ufficiale e logo richiedono approvazione separata |
| `CONTATTO_SUPPORTO` | vuoto | sì | contatto da definire prima della produzione |

`SALUTO_EMAIL` e `CORPO_EMAIL` preservano insieme l'apertura obbligatoria `Ciao {{nome}}, ricevi questa mail...`. Lo schema non introduce `nome_saluto` e non deduce il nome da un nominativo completo.

## Tab `NOTIFICHE`

Una riga rappresenta lo stato corrente di una sola notifica, identificata in modo univoco da `notification_id`.

| Colonna | Contenuto | Regola |
|---|---|---|
| `notification_id` | `ID_ARBITRO|DATA_SCADENZA|TIPO_NOTIFICA` | chiave univoca e immutabile |
| `id_arbitro` | identificativo stabile dell'arbitro | proviene da Operativo |
| `nome` | nome dell'arbitro | stessa riga di Operativo |
| `cognome` | cognome dell'arbitro | stessa riga di Operativo |
| `email` | indirizzo destinatario | stessa riga di Operativo |
| `scadenza_certificato` | data ISO `YYYY-MM-DD` | immutabile per la chiave |
| `tipo` | tipo di promemoria | per esempio `REMINDER_30` |
| `stato` | stato del ciclo di vita | `SENDING`, `SENT`, `FAILED_RETRYABLE`, `UNKNOWN_REVIEW_REQUIRED` |
| `tentativi` | numero progressivo dei tentativi | intero maggiore o uguale a 1 |
| `creato_il` | primo inserimento UTC | immutabile |
| `aggiornato_il` | ultima transizione UTC | non può regredire |
| `message_id` | identificativo SMTP | valorizzato dopo invio accettato |
| `versione_app` | versione del programma | audit e diagnosi |
| `errore` | dettaglio tecnico sintetico | privo di segreti e dati superflui |

L'ordine delle quattordici colonne è canonico e viene riusato direttamente dal contratto già implementato in `admin_store`.

Lo schema iniziale contiene soltanto le intestazioni: nessuna notifica o dato personale viene precompilato.

## Tab `DASHBOARD`

Intestazioni:

```text
metrica | valore | descrizione
```

La dashboard iniziale contiene metriche sintetiche e sicure:

- `stato_sistema = DISATTIVATO`;
- `ultima_esecuzione` e `heartbeat` vuoti;
- `righe_lette`, `candidati`, `invii_tentati`, `invii_riusciti` e `anomalie` uguali a `0`;
- `kill_switch = ATTIVO`.

Questi valori non dichiarano un'esecuzione reale e non devono essere confusi con dati operativi.

## Tab `ANOMALIE`

Intestazioni:

```text
anomalia_id | rilevata_il | severita | origine | codice | riga_sorgente | campo | messaggio | versione_app | risolta_il
```

La tab nasce vuota. In futuro conterrà problemi di qualità dati o tecnici senza modificare `Operativo`. `messaggio` deve restare sintetico e non deve includere intere righe, certificati, credenziali o dati personali non necessari.

## Comportamento dell'adapter `NOTIFICHE`

`ArchivioNotificheGoogleSheets`:

1. legge intestazioni e righe della tab;
2. converte ogni riga non vuota in `RigaNotifica`;
3. cerca la `notification_id` esatta;
4. aggiunge una riga se non esiste alcuna corrispondenza;
5. aggiorna la stessa riga se esiste una sola corrispondenza;
6. blocca la scrittura se esistono due o più corrispondenze;
7. rifiuta intestazioni diverse, timestamp regressivi o modifica di `creato_il`.

Il trasporto usa `valueInputOption=RAW`, quindi date, timestamp e identificativi vengono conservati come stringhe canoniche.

## Concorrenza

Google Sheets non offre una transazione atomica che comprenda ricerca della chiave e successiva scrittura. In produzione il controllo applicativo dovrà essere affiancato da un solo workflow attivo alla volta tramite `concurrency` di GitHub Actions.

Il lock del workflow non sostituisce i controlli sul foglio: una chiave duplicata creata manualmente deve comunque bloccare l'esecuzione.

## Stato attuale

Sono implementati e testati:

- il contratto completo delle quattro tab;
- i valori iniziali sicuri di `CONFIG` e `DASHBOARD`;
- l'assenza di righe iniziali in `NOTIFICHE` e `ANOMALIE`;
- i controlli su nome del file, ordine delle tab, intestazioni duplicate e larghezza delle righe;
- il riuso dello schema `NOTIFICHE` già esistente.

Non sono ancora stati creati Spreadsheet reali, configurati permessi Google, copiati dati da `Operativo` o attivati workflow e invii SMTP.
