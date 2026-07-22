# Schema dei fogli amministrativi

Il file separato canonico è `Reminder certificati CIA Lazio — Gestione`. Le tab richieste sono `CONFIG`, `NOTIFICHE`, `DASHBOARD` e `ANOMALIE`; il loro ordine visuale non è significativo e nessuna tab viene nascosta.

## Versione dello schema

La versione corrente è **4** ed è registrata in CONFIG come:

```text
SCHEMA_VERSION | 4
```

`SCHEMA_VERSION` è gestita dal programma. `setup-admin` riconosce automaticamente un file vuoto, uno schema precedente oppure un file già aggiornato.

## CONFIG

Intestazioni:

```text
chiave | valore | descrizione
```

| Chiave | Valore iniziale | Scopo |
|---|---:|---|
| `SCHEMA_VERSION` | `4` | versione del contratto amministrativo |
| `INVIO_AUTOMATICO_ATTIVO` | `false` | unico interruttore degli invii programmati |
| `GIORNI_PREAVVISO` | `30` | finestra inclusiva |
| `DESTINATARIO_OVERRIDE` | vuoto | destinatario del test SMTP |
| `OGGETTO_EMAIL` | predefinito | oggetto del promemoria |
| `CORPO_EMAIL` | predefinito | messaggio completo, compreso l'eventuale saluto |

Il codice non aggiunge saluti o altre frasi implicite. `CORPO_EMAIL` può usare `{{nome}}`, `{{cognome}}`, `{{nome_completo}}`, `{{data_scadenza}}` e `{{giorni_residui}}`. Il valore iniziale comincia con `Ciao {{nome}},`, ma l'operatore può modificare liberamente la formulazione dal foglio.

La firma istituzionale non è configurabile dal foglio. Il codice genera sia la parte HTML con logo inline sia la parte `text/plain` dagli stessi dati, con una regressione automatica che ne verifica l'allineamento.

Il limite di 10 invii per esecuzione è una costante interna e non compare nel foglio. Non esistono più chiavi separate per produzione, preproduzione o invii reali.

## NOTIFICHE

Intestazioni:

```text
notification_id | id_arbitro | scadenza_certificato | tipo | stato | tentativi | creato_il | aggiornato_il | message_id | versione_app | errore
```

Nome, cognome ed email non vengono persistiti. La chiave è stabile rispetto alla finestra di preavviso:

```text
ID_ARBITRO|DATA_SCADENZA|CERTIFICATO_SCADENZA_V1
```

Stati:

- `SENDING`: prenotazione avvenuta, esito non ancora concluso;
- `SENT`: invio confermato;
- `FAILED_RETRYABLE`: errore ritentabile, fino a tre tentativi complessivi;
- `FAILED_PERMANENT`: errore certo e non ritentabile;
- `UNKNOWN_REVIEW_REQUIRED`: esito incerto da verificare manualmente.

Il test SMTP continua a creare una chiave distinta con tipo `TEST_CERTIFICATO_SCADENZA_V1`.

## Aggiornamento dallo schema precedente

L'aggiornamento:

1. legge CONFIG, NOTIFICHE e DASHBOARD;
2. produce un'anteprima aggregata;
3. salva un backup JSON prima di modificare un foglio esistente;
4. converte la CONFIG dalle cinque colonne precedenti alle tre colonne correnti;
5. sostituisce i vecchi interruttori con `INVIO_AUTOMATICO_ATTIVO=false`;
6. preserva giorni, destinatario override, oggetto, corpo e relative descrizioni;
7. elimina la vecchia chiave `FIRMA_TESTO`, ora gestita unicamente dal codice;
8. minimizza il registro e stabilizza le chiavi legacy;
9. rifiuta collisioni tra chiavi convertite.

Durante il passaggio il runtime accetta ancora una CONFIG v3 completa, ma ignora il valore di `FIRMA_TESTO`. Gli stati misti v3/v4 vengono rifiutati per evitare configurazioni ambigue.

## DASHBOARD e ANOMALIE

La dashboard contiene metriche aggregate e mostra etichette comprensibili per lo stato complessivo. Gli identificatori tecnici delle metriche restano stabili per compatibilità.

ANOMALIE conserva codice, origine, riga e campo, con messaggio limitato e sanitizzato. Non devono esservi copiati payload Google, credenziali o contenuti completi delle righe.

## Concorrenza

Google Sheets non offre una transazione completa tra ricerca e scrittura. Tutti i workflow canonici condividono il gruppo `reminder-certificati-runtime`; gli invii non devono essere lanciati contemporaneamente da percorsi esterni non coordinati.
