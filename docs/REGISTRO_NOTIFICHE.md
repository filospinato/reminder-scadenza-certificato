# Registro delle notifiche

Il registro impedisce che la stessa notifica venga inviata più volte. La chiave stabile è:

```text
ID_ARBITRO|DATA_SCADENZA|TIPO_NOTIFICA
```

Il contenuto del messaggio non entra nella chiave: una modifica al template non rende nuovamente inviabile una comunicazione già spedita.

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

`SENT` e `UNKNOWN_REVIEW_REQUIRED` sono terminali per l'automazione.

## Persistenza e concorrenza

`RegistroPersistente` è l'unica macchina a stati applicativa. Usa la tab `NOTIFICHE` tramite un archivio iniettato; i test usano un archivio in memoria, mentre il runtime usa Google Sheets.

L'adapter Google:

1. legge `NOTIFICHE` una sola volta per esecuzione;
2. rifiuta immediatamente chiavi duplicate;
3. crea un indice locale `notification_id → numero riga`;
4. aggiorna l'indice dopo ogni append o update;
5. evita di rileggere l'intero foglio a ogni transizione.

Google Sheets non offre una transazione tra ricerca e scrittura. I workflow che accedono al registro condividono quindi lo stesso gruppo `concurrency` e non vengono eseguiti in parallelo.

## Perché si registra `SENDING` prima dell'invio

La prenotazione precedente a SMTP impedisce che una ripartenza o una seconda esecuzione tratti la notifica come mai tentata. Se l'esecuzione si interrompe dopo `SENDING`, la riga resta bloccata fino alla revisione umana.

## Gestione degli esiti SMTP

- errore certamente precedente alla consegna: `FAILED_RETRYABLE`;
- accettazione confermata: `SENT` con `Message-ID`;
- esito ambiguo dopo un possibile invio: `UNKNOWN_REVIEW_REQUIRED`.

Lo stato incerto non viene ritentato automaticamente: evitare duplicati ha priorità rispetto a un reinvio non verificato.
