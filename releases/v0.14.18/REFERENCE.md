# Riferimento tecnico — release 0.14.18

Questo documento fotografa i contratti applicativi della release 0.14.18.

## Architettura

Il dominio è indipendente dai trasporti esterni. Le componenti principali sono:

- lettura e validazione di `Operativo`;
- selezione dei candidati;
- configurazione amministrativa;
- composizione del messaggio testo/HTML;
- registro persistente anti-duplicazione;
- trasporto SMTP MDaemon;
- dashboard e anomalie aggregate;
- adapter Google Sheets autenticato tramite WIF/OIDC.

## Contratto della sorgente `Operativo`

Il contratto strutturale è incorporato nel codice:

- tab: `Operativo`;
- intestazioni: riga 2;
- intervallo: `A:AS`;
- il foglio è sempre in sola lettura.

Campi logici utilizzati:

| Campo | Intestazione reale | Regola |
|---|---|---|
| `id_arbitro` | `Tessera` | obbligatorio e univoco per i record rilevanti |
| `nome` | `Nome` | obbligatorio per i candidati |
| `cognome` | `Cognome` | obbligatorio per i candidati |
| `email` | `e-Mail` | formalmente valida |
| `scadenza_certificato` | `Data Scadenza Certificato` | data riconoscibile |
| `attivo` | `Fa attività quest'anno` | vuoto o valore affermativo = attivo |
| `qualifica` | `Qualifica` | usata per le esclusioni |
| `abilitazione` | `Abilitazione` | usata per le esclusioni |

Nome, cognome, email, scadenza e stato devono provenire dalla stessa riga. Il programma non ricompone dati provenienti da righe diverse e non deduce il nome da un nominativo completo.

Le righe vuote, prive di scadenza o appartenenti a categorie non tenute al certificato vengono ignorate. ID, nome, cognome, email e duplicati vengono validati soltanto per persone attive con scadenza compresa nella finestra di preavviso.

Categorie escluse:

- Benemeriti;
- Osservatori;
- Fuori Quadro;
- Decaduti;
- Non Attivi.

Formati data accettati:

- `YYYY-MM-DD`;
- `GG/MM/AAAA`;
- valori data nativi o seriali Google Sheets compatibili con l’epoca `1899-12-30`.

## Anomalie dati

| Codice | Comportamento |
|---|---|
| `ID_MANCANTE` | riga esclusa |
| `NOME_MANCANTE` | riga esclusa |
| `COGNOME_MANCANTE` | riga esclusa |
| `EMAIL_NON_VALIDA` | riga esclusa |
| `SCADENZA_NON_VALIDA` | riga esclusa |
| `ID_DUPLICATO` | tutte le righe rilevanti con lo stesso ID vengono escluse |

Le anomalie persistite sono minimizzate e sanitizzate; non contengono email complete, token, payload Google o chiavi di notifica.

## Foglio amministrativo

La versione dello schema è `4`. Le tab canoniche sono:

- `CONFIG`;
- `NOTIFICHE`;
- `DASHBOARD`;
- `ANOMALIE`.

L’ordine visuale non è significativo e nessuna tab viene nascosta.

### CONFIG

Intestazioni:

```text
chiave | valore | descrizione
```

Chiavi canoniche:

| Chiave | Valore iniziale | Scopo |
|---|---:|---|
| `SCHEMA_VERSION` | `4` | versione del contratto amministrativo |
| `INVIO_AUTOMATICO_ATTIVO` | `false` | unico interruttore degli invii reali |
| `GIORNI_PREAVVISO` | `30` | finestra inclusiva |
| `DESTINATARIO_OVERRIDE` | vuoto | destinatario del test SMTP |
| `OGGETTO_EMAIL` | predefinito | oggetto del promemoria |
| `CORPO_EMAIL` | predefinito | messaggio completo |

Il limite ordinario di 10 invii per esecuzione è interno al programma. Il parametro produttivo può soltanto ridurlo a 1, 5 o 10.

Il runtime accetta esclusivamente una CONFIG v4 completa. `setup-preview` può leggere uno schema precedente soltanto per descriverne la migrazione. Ogni migrazione lascia gli invii spenti, preserva i valori funzionali e crea un backup prima di modificare un foglio esistente.

### NOTIFICHE

Intestazioni:

```text
notification_id | id_arbitro | scadenza_certificato | tipo | stato | tentativi | creato_il | aggiornato_il | message_id | versione_app | errore
```

Nome, cognome ed email non vengono persistiti.

Chiave stabile:

```text
ID_ARBITRO|DATA_SCADENZA|CERTIFICATO_SCADENZA_V1
```

La chiave del test SMTP usa il tipo distinto `TEST_CERTIFICATO_SCADENZA_V1`.

### DASHBOARD e ANOMALIE

La dashboard contiene soltanto conteggi aggregati e viene aggiornata con una singola operazione, evitando uno stato intermedio vuoto. `ANOMALIE` conserva codice, origine, riga, campo e messaggio sanitizzato.

## Registro anti-duplicazione

Stati:

| Stato | Significato | Nuovo invio automatico |
|---|---|---|
| `SENDING` | prenotazione scritta prima di SMTP | vietato |
| `SENT` | accettazione confermata | vietato |
| `FAILED_RETRYABLE` | errore certamente precedente all’accettazione | consentito entro tre tentativi |
| `FAILED_PERMANENT` | rifiuto definitivo | vietato |
| `UNKNOWN_REVIEW_REQUIRED` | esito incerto | vietato |

Transizioni ammesse:

```text
assenza -> SENDING
SENDING -> SENT
SENDING -> FAILED_RETRYABLE
SENDING -> FAILED_PERMANENT
SENDING -> UNKNOWN_REVIEW_REQUIRED
FAILED_RETRYABLE -> SENDING
```

`SENDING` viene registrato prima del contatto SMTP per impedire che un’interruzione faccia apparire la notifica come mai tentata. Tutti i workflow canonici condividono il gruppo di concorrenza `reminder-certificati-runtime`, definito direttamente nei file sotto `.github/workflows/`.

## Contratto del messaggio

`CORPO_EMAIL` contiene il messaggio completo, compreso l’eventuale saluto. Il codice non aggiunge frasi implicite.

Placeholder consentiti:

| Placeholder | Valore |
|---|---|
| `{{nome}}` | colonna Nome normalizzata in composizione |
| `{{cognome}}` | colonna Cognome normalizzata in composizione |
| `{{nome_completo}}` | nome e cognome ricomposti |
| `{{data_scadenza}}` | data in formato `GG/MM/AAAA` |
| `{{giorni_residui}}` | giorni mancanti |

Placeholder sconosciuti, incompleti o privi di valore bloccano la preparazione. I ritorni a capo nell’oggetto sono vietati e i valori dinamici vengono sottoposti a escaping HTML.

La firma istituzionale testo/HTML deriva da un’unica sorgente versionata nel codice. Il logo è incorporato tramite CID; non vengono usate immagini remote.

## MIME e SMTP

Ogni messaggio contiene:

- `Subject`, `From`, `To`, `Date` e `Message-ID`;
- `Reply-To` opzionale;
- parte `text/plain`;
- parte `text/html`;
- logo inline CID;
- un solo destinatario.

Trasporti supportati:

- STARTTLS;
- SSL;
- PLAIN soltanto con consenso esplicito `ALLOW_PLAIN_SMTP=true`.

Classificazione:

- errore di connessione certamente precedente alla consegna: `FAILED_RETRYABLE`;
- risposta SMTP `4xx`: `FAILED_RETRYABLE`;
- risposta SMTP `5xx`: `FAILED_PERMANENT`;
- disconnessione o risposta dubbia durante la consegna: `UNKNOWN_REVIEW_REQUIRED`;
- accettazione confermata: `SENT` con `Message-ID`.

La consegna diretta al server SMTP non crea una copia nella Posta inviata.

## Diagnostica preflight

Il preflight legge struttura e CONFIG, non legge righe anagrafiche di `Operativo`, non scrive e non usa SMTP.

| Codice | Significato | Azione |
|---|---|---|
| `PREFLIGHT_RESOURCE_IDS_EQUAL` | i due ID indicano lo stesso file | correggere le Variables |
| `PREFLIGHT_ADMIN_UNREACHABLE` | amministrazione non leggibile | verificare ID, condivisione e WIF |
| `PREFLIGHT_ADMIN_TABS_INVALID` | tab mancanti o duplicate | eseguire `setup-admin` |
| `PREFLIGHT_ADMIN_HEADERS_UNREADABLE` | intestazioni non leggibili | verificare permessi e integrità |
| `PREFLIGHT_ADMIN_HEADERS_INVALID` | schema intestazioni non conforme | eseguire anteprima e migrazione controllata |
| `PREFLIGHT_ADMIN_CONFIG_INVALID` | CONFIG incompatibile | eseguire anteprima e correggere le chiavi |
| `PREFLIGHT_OPERATIVO_UNREACHABLE` | intestazioni di Operativo non leggibili | verificare condivisione, tab e riga 2 |
| `PREFLIGHT_OPERATIVO_HEADERS_MISSING` | manca una colonna usata dal reminder | aggiornare sorgente o contratto applicativo |
| `PREFLIGHT_UNEXPECTED_ERROR` | errore non classificato | verificare WIF e log sanitizzati |

L’output pubblico non contiene ID degli Spreadsheet, righe operative, email, token o payload Google.

## Contratto GitHub Environment

Il file autoritativo per i nomi è `../../config/github/environment-contract.json`.

Regole:

- tutti i workflow usano un solo Environment;
- `SMTP_PASSWORD` è l’unico Secret SMTP;
- gli altri parametri SMTP sono Variables;
- `SMTP_USERNAME` viene usato anche come mittente;
- la struttura di `Operativo` non è configurabile tramite Variables;
- non esistono gate ridondanti come `PREPRODUCTION_ENABLED`, `PRODUCTION_ENABLED`, `ALLOW_EMAIL_DELIVERY` o `ALLOW_SYNTHETIC_REGISTRY_WRITE`.

## Comandi pubblici

```bash
reminder-certificati setup-admin --spreadsheet-id ID
reminder-certificati setup-admin --spreadsheet-id ID --apply
reminder-certificati check
reminder-certificati registry-check
reminder-certificati test-smtp
reminder-certificati produzione
reminder-certificati produzione --max-sends 1
```
