# Registro delle notifiche

Il registro impedisce che la stessa notifica venga inviata più volte. La chiave stabile è:

```text
ID_ARBITRO|DATA_SCADENZA|TIPO_NOTIFICA
```

Esempio:

```text
A-123|2026-08-01|REMINDER_30
```

Il contenuto del messaggio non entra nella chiave: una modifica cosmetica al template non deve rendere nuovamente inviabile una comunicazione già spedita.

## Stati

| Stato | Significato | Nuovo invio automatico |
|---|---|---|
| `SENDING` | prenotazione scritta prima di contattare SMTP | vietato |
| `SENT` | MDaemon ha confermato l'accettazione e il `Message-ID` è stato registrato | vietato |
| `FAILED_RETRYABLE` | errore certamente precedente all'accettazione SMTP | consentito, incrementando i tentativi |
| `UNKNOWN_REVIEW_REQUIRED` | non è possibile sapere con certezza se SMTP abbia accettato il messaggio | vietato; serve controllo umano |

## Transizioni ammesse

```text
assenza → SENDING
SENDING → SENT
SENDING → FAILED_RETRYABLE
SENDING → UNKNOWN_REVIEW_REQUIRED
FAILED_RETRYABLE → SENDING
```

`SENT` e `UNKNOWN_REVIEW_REQUIRED` sono terminali per l'automazione. Non esiste un reinvio automatico da questi stati.

## Perché si registra `SENDING` prima dell'invio

La prenotazione precedente a SMTP riduce il rischio che due esecuzioni concorrenti spediscano lo stesso messaggio. L'implementazione in memoria usa un lock e i test verificano che, anche con più thread, una sola prenotazione possa riuscire.

La futura persistenza nel foglio `NOTIFICHE` dovrà offrire lo stesso comportamento logico. La concorrenza del workflow GitHub resterà inoltre limitata a una sola esecuzione del gruppo di produzione.

## Gestione degli esiti SMTP

- Se l'errore avviene certamente prima che MDaemon accetti il messaggio, lo stato diventa `FAILED_RETRYABLE`.
- Se MDaemon conferma l'accettazione, lo stato diventa `SENT` e viene salvato il `Message-ID`.
- Se la connessione si interrompe dopo un possibile invio e l'esito è ambiguo, lo stato diventa `UNKNOWN_REVIEW_REQUIRED`.

Lo stato incerto non viene mai ritentato automaticamente: il rischio di una mail mancante è preferibile a un duplicato non controllato.

## Implementazione corrente

`RegistroMemoria` è un adapter senza rete e senza dati reali, usato per:

- definire il contratto del dominio;
- provare le transizioni;
- verificare la prenotazione atomica;
- preparare il successivo adapter Google Sheets.

Non persiste dati tra due esecuzioni e non è ancora collegato alla CLI o a MDaemon. Prima della produzione verrà implementato un adapter per il foglio amministrativo e verranno eseguiti test di integrazione su uno Spreadsheet sintetico.
