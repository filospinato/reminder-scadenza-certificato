# Contratto del messaggio email

Il programma compone sempre una versione testuale e una versione HTML dello stesso messaggio. La composizione è separata dall'invio SMTP e può essere provata in `dry-run` senza contattare MDaemon.

## Apertura obbligatoria

Ogni comunicazione destinata all'arbitro deve iniziare con:

```text
Ciao {{nome}}, ricevi questa mail...
```

Il saluto non è affidato liberamente al template. Il programma aggiunge `Ciao {{nome}}, ` e accetta il corpo solo quando inizia con `ricevi questa mail`.

## Provenienza del nome

`{{nome}}` è letto direttamente dalla colonna del nome presente sulla stessa riga di `Operativo` che contiene anche cognome, email, scadenza e stato dell'arbitro.

Esempio:

```text
nome = Anna Maria
cognome = Verdi
email = anna@example.it
```

produce:

```text
Ciao Anna Maria, ricevi questa mail...
```

Il programma non prende la prima parola di un nominativo completo e non tenta di dedurre il nome dal cognome.

## Placeholder consentiti

| Placeholder | Valore |
|---|---|
| `{{nome}}` | colonna `nome` di Operativo |
| `{{cognome}}` | colonna `cognome` di Operativo |
| `{{nome_completo}}` | `nome` e `cognome` ricomposti |
| `{{data_scadenza}}` | data in formato `GG/MM/AAAA` |
| `{{giorni_residui}}` | giorni mancanti alla scadenza |

Placeholder sconosciuti, incompleti o privi di valore causano un errore di configurazione e impediscono la preparazione del messaggio.

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

Oggetto, corpo e firma saranno caricati dal foglio `CONFIG`. La firma ufficiale potrà includere successivamente contatti e logo inline CID.

## Sicurezza

- nome, cognome, email e scadenza provengono dalla medesima riga validata;
- valori personalizzati sottoposti a escaping nella versione HTML;
- ritorni a capo vietati nell'oggetto per prevenire header injection;
- testo e HTML generati dalla stessa configurazione;
- nessun invio viene effettuato dal modulo di composizione;
- i template non possono accedere a campi arbitrari della sorgente.
