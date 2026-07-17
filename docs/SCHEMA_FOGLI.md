# Schema dei fogli amministrativi

Questo documento definisce lo schema logico iniziale del futuro Spreadsheet amministrativo. In questa fase non viene effettuata alcuna scrittura su Google Sheets reale.

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

La futura implementazione Google Sheets dovrà aggiornare la riga già associata alla chiave, non aggiungerne una nuova a ogni transizione. Chiavi duplicate nella tab sono un'anomalia bloccante.

## Tab future

- `CONFIG`: attivazione, finestra temporale, limiti, modalità test, override destinatario, oggetto, corpo, firma e contatti.
- `DASHBOARD`: heartbeat, ultima esecuzione, conteggi, stato generale e kill switch.
- `ANOMALIE`: problemi di qualità dati e tecnici, senza modificare Operativo.

## Stato attuale

Il modulo `admin_store` implementa lo schema di `NOTIFICHE`, conversione tipizzata e archivio in memoria thread-safe. Serve come fake e contratto per i test. Non sono ancora presenti autenticazione Google, ricerca della riga reale, controllo di concorrenza distribuito o scritture sullo Spreadsheet amministrativo.
