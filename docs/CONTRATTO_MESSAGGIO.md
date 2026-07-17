# Contratto del messaggio email

Il programma genera sempre una versione testuale e una HTML dello stesso messaggio. La composizione resta separata dal trasporto e può essere verificata in dry-run.

## Apertura obbligatoria

Ogni comunicazione deve iniziare con:

```text
Ciao {{nome}}, ricevi questa mail...
```

Il saluto non è affidato liberamente al template. Il programma aggiunge `Ciao {{nome}}, ` e accetta il corpo solo quando inizia con `ricevi questa mail`.

## Provenienza del nome

`{{nome}}` è letto direttamente dalla colonna `Nome` della stessa riga di `Operativo` che contiene cognome, email, scadenza e stato.

Esempio sintetico:

```text
nome = Anna Maria
cognome = Verdi
```

produce:

```text
Ciao Anna Maria, ricevi questa mail...
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
ricevi questa mail perché il certificato medico presente nei nostri archivi risulta in scadenza il {{data_scadenza}}.

Ti invitiamo a provvedere al rinnovo e alla trasmissione della nuova documentazione secondo le modalità previste.

Firma:
Cordiali saluti,
CIA Lazio
```

Oggetto, corpo e firma vengono caricati da `CONFIG`. Il testo attuale è provvisorio: contenuto, contatti, firma ufficiale e logo devono essere approvati prima della produzione.

## MIME e trasporto

`TrasportoSmtpMdaemon` costruisce un messaggio individuale con:

- intestazioni Subject, From, To, Date e Message-ID;
- Reply-To opzionale;
- parte `text/plain`;
- parte `text/html`;
- immagine inline CID facoltativa;
- un solo destinatario per chiamata SMTP.

Il trasporto supporta STARTTLS e SSL. SMTP non cifrato è rifiutato salvo una seconda autorizzazione esplicita. Username e password devono essere entrambi presenti o entrambi assenti.

La consegna avviene direttamente al server SMTP e non crea una copia nella Posta inviata.

## Classificazione degli esiti

- connessione non disponibile prima della consegna: `FAILED_RETRYABLE`;
- autenticazione, mittente o destinatario rifiutati: errore permanente e revisione umana;
- disconnessione o risposta dubbia durante la consegna: `UNKNOWN_REVIEW_REQUIRED`;
- consegna confermata: `SENT` con Message-ID.

Un esito incerto non viene ritentato automaticamente.

## Modalità test

`TEST_SMTP` richiede:

- sistema attivo;
- kill switch disattivato;
- modalità test attiva;
- destinatario override valido;
- consenso esplicito del comando e dell'environment.

Il destinatario originale viene sostituito prima della chiamata SMTP. Il registro usa tipi `TEST_REMINDER_*`, separati dalle notifiche reali.

## Sicurezza

- nome, cognome, email e scadenza provengono dalla medesima riga validata;
- valori personalizzati sottoposti a escaping HTML;
- ritorni a capo vietati nell'oggetto;
- testo e HTML prodotti dalla stessa configurazione;
- i template non accedono a campi arbitrari;
- i parametri SMTP vengono letti dall'ambiente e non sono versionati;
- nessun invio reale è possibile con il solo inserimento dei parametri esterni.
