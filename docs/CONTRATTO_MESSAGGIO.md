# Contratto del messaggio email

Il programma genera sempre una versione testuale e una HTML dello stesso messaggio. La composizione resta separata dal trasporto e può essere verificata in dry-run.

## Apertura

Il programma non aggiunge automaticamente un saluto. `CORPO_EMAIL` contiene il messaggio completo; il valore iniziale include `Ciao {{nome}},` ma l'operatore può modificarlo o rimuoverlo. Il corpo deve essere non vuoto e può usare soltanto i placeholder autorizzati.

## Provenienza del nome

`{{nome}}` è letto direttamente dalla colonna `Nome` della stessa riga di `Operativo` che contiene cognome, email, scadenza e stato.

Esempio sintetico:

```text
nome = Anna Maria
cognome = Verdi
```

può produrre:

```text
Ciao Anna Maria, il tuo certificato medico scade il 01/08/2026.
```

Il programma non prende la prima parola di un nominativo completo e non deduce il nome dal cognome.

## Placeholder consentiti

| Placeholder | Valore |
|---|---|
| `{{nome}}` | colonna Nome |
| `{{cognome}}` | colonna Cognome |
| `{{nome_completo}}` | nome e cognome ricomposti |
| `{{data_scadenza}}` | data `GG/MM/AAAA` |
| `{{giorni_residui}}` | giorni mancanti |

Placeholder sconosciuti, incompleti o privi di valore impediscono la preparazione del messaggio.

## Configurazione iniziale

```text
Oggetto: Certificato medico in scadenza

Corpo:
Ciao {{nome}}, ricevi questa mail perché il certificato medico presente nei nostri archivi risulta in scadenza il {{data_scadenza}}.

Ti invitiamo a provvedere al rinnovo e alla trasmissione della nuova documentazione secondo le modalità previste.

Firma:
Cordiali saluti,
CIA Lazio
```

Il testo iniziale resta quello concordato, ma può essere modificato senza cambiare il codice. Oggetto, corpo e firma vengono caricati da `CONFIG`; contenuto, contatti, firma ufficiale e logo devono essere approvati prima della produzione.

## MIME e trasporto

`TrasportoSmtpMdaemon` costruisce un messaggio individuale con:

- intestazioni Subject, From, To, Date e Message-ID;
- Reply-To opzionale;
- parte `text/plain`;
- parte `text/html`;
- immagine inline CID facoltativa;
- un solo destinatario per chiamata SMTP.

Il trasporto supporta STARTTLS e SSL. La consegna avviene direttamente al server SMTP e non crea una copia nella Posta inviata.

## Classificazione degli esiti

- connessione non disponibile prima della consegna: `FAILED_RETRYABLE`;
- risposta SMTP temporanea `4xx`: `FAILED_RETRYABLE`;
- risposta SMTP permanente `5xx`: `FAILED_PERMANENT` e revisione umana;
- disconnessione o risposta dubbia durante la consegna: `UNKNOWN_REVIEW_REQUIRED`;
- consegna confermata: `SENT` con Message-ID.

Un esito incerto non viene ritentato automaticamente.

## Test SMTP

Il sottocomando `reminder-certificati test-smtp` richiede:

- destinatario override valido;
- configurazione SMTP valida nello specifico Environment.

Il test resta disponibile con `INVIO_AUTOMATICO_ATTIVO=false`. Non esiste una seconda modalità test nella CONFIG. Il destinatario originale viene sostituito prima della chiamata SMTP. Il registro usa un tipo `TEST_`, separato dalle notifiche reali, e un'esecuzione che non tenta alcun invio termina con attenzione.

## Sicurezza

- nome, cognome, email e scadenza provengono dalla medesima riga validata;
- valori personalizzati sottoposti a escaping HTML;
- ritorni a capo vietati nell'oggetto;
- oggetto, corpo e firma non possono essere vuoti;
- testo e HTML prodotti dalla stessa configurazione;
- i template non accedono a campi arbitrari;
- i parametri SMTP vengono letti dall'ambiente e non sono versionati;
- nessun invio reale è possibile con il solo inserimento dei parametri esterni.
