# Schema dei fogli amministrativi

Questo documento definisce lo schema logico iniziale dello Spreadsheet amministrativo. Il codice include ora un adapter Google Sheets testato con fake, ma non usa ancora credenziali né Spreadsheet reali.

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
| `versione_app` | versione del programma | utile per audit e diagnosi |
| `errore` | dettaglio tecnico sintetico | privo di segreti e dati superflui |

L'ordine delle quattordici colonne è canonico e viene verificato esattamente prima di ogni lettura o scrittura.

## Comportamento dell'adapter

`ArchivioNotificheGoogleSheets`:

1. legge intestazioni e righe della tab;
2. converte ogni riga non vuota in `RigaNotifica`;
3. cerca la `notification_id` esatta;
4. aggiunge una riga se non esiste alcuna corrispondenza;
5. aggiorna la stessa riga se esiste una sola corrispondenza;
6. blocca la scrittura se esistono due o più corrispondenze;
7. rifiuta intestazioni diverse, timestamp regressivi o modifica di `creato_il`.

Il trasporto usa `valueInputOption=RAW`, quindi date, timestamp e identificativi vengono conservati come stringhe canoniche senza interpretazioni automatiche del foglio.

## Concorrenza

Google Sheets non offre una transazione atomica che comprenda ricerca della chiave e successiva scrittura. Il controllo applicativo evita errori e duplicati già presenti, ma in produzione deve essere affiancato da un solo workflow attivo alla volta tramite `concurrency` di GitHub Actions.

Il lock del workflow non sostituisce i controlli sul foglio: se una modifica manuale crea chiavi duplicate, l'esecuzione deve comunque bloccarsi e segnalare l'anomalia.

## Preparazione del foglio sintetico

Per la prova reale sarà sufficiente uno Spreadsheet senza dati personali con una tab chiamata `NOTIFICHE`. La prima riga dovrà contenere, nell'ordine:

```text
notification_id | id_arbitro | nome | cognome | email | scadenza_certificato | tipo | stato | tentativi | creato_il | aggiornato_il | message_id | versione_app | errore
```

Il service account riceverà accesso in scrittura soltanto a questo Spreadsheet sintetico durante il collaudo.

## Tab future

- `CONFIG`: attivazione, finestra temporale, limiti, modalità test, override destinatario, oggetto, corpo, firma e contatti.
- `DASHBOARD`: heartbeat, ultima esecuzione, conteggi, stato generale e kill switch.
- `ANOMALIE`: problemi di qualità dati e tecnici, senza modificare Operativo.

## Stato attuale

Sono implementati e testati `RigaNotifica`, `ArchivioNotificheMemoria`, `ArchivioNotificheGoogleSheets`, `TrasportoNotificheMemoria` e `TrasportoNotificheGoogleApi`. Mancano ancora la costruzione delle credenziali, la prova su uno Spreadsheet sintetico, l'integrazione nel flusso completo e il workflow `concurrency` di produzione.
