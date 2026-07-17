# Contratto del messaggio email

Il programma compone sempre una versione testuale e una versione HTML dello stesso messaggio. La composizione è separata dall'invio SMTP: può quindi essere provata in `dry-run` senza contattare MDaemon.

## Apertura obbligatoria

Ogni comunicazione destinata all'arbitro deve iniziare con:

```text
Ciao {{nome}}, ricevi questa mail...
```

Il saluto non è affidato liberamente al template. Il programma aggiunge `Ciao {{nome}}, ` e accetta il corpo solo quando inizia con `ricevi questa mail`.

## Scelta del nome

1. se la mappatura di `Operativo` indica una colonna facoltativa `nome_saluto`, viene usato quel valore;
2. altrimenti viene usata la prima parola del nominativo completo;
3. per nomi composti, soprannomi istituzionali o sorgenti ordinate `Cognome Nome`, è consigliato configurare esplicitamente `nome_saluto`.

Esempio:

```text
nome = Anna Maria Verdi
nome_saluto = Anna Maria
```

produce:

```text
Ciao Anna Maria, ricevi questa mail...
```

## Placeholder consentiti

| Placeholder | Valore |
|---|---|
| `{{nome}}` | nome usato nel saluto |
| `{{nome_completo}}` | nominativo completo presente nella sorgente |
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

- valori personalizzati sottoposti a escaping nella versione HTML;
- ritorni a capo vietati nell'oggetto per prevenire header injection;
- testo e HTML generati dalla stessa configurazione;
- nessun invio viene effettuato dal modulo di composizione;
- i template non possono accedere a campi arbitrari della sorgente.
