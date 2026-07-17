# Sorgenti dati e Google Sheets

Il dominio non dipende direttamente dalla Google Sheets API. Lettura, struttura e persistenza usano protocolli iniettati, così test e dry-run non richiedono rete o risorse reali.

## `Operativo`

Componenti:

- `SorgenteDati` e `SorgenteMemoria`;
- `AdapterGoogleSheets` e `LettoreValoriSheets`;
- `LettoreGoogleApi` per un servizio già autenticato;
- `leggi_e_valida` per collegare sorgente e dominio;
- `google_runtime.MAPPATURA_OPERATIVO_REALE` per le intestazioni verificate.

Mappatura reale:

| Campo logico | Intestazione |
|---|---|
| ID | `Tessera` |
| nome | `Nome` |
| cognome | `Cognome` |
| email | `e-Mail` |
| scadenza | `Data Scadenza Certificato` |
| attività | `Fa attività quest'anno` |

Le intestazioni sono in riga 2 e i dati iniziano dalla riga 3. L'adapter conserva il numero originale per le anomalie.

L'adapter rifiuta matrici vuote, intestazioni vuote o duplicate, righe non tabellari e celle non vuote oltre le intestazioni. Le righe corte vengono completate con celle vuote.

## Verifica preliminare delle intestazioni

Il comando:

```bash
reminder-certificati-runtime check-headers
```

legge esclusivamente la riga delle intestazioni e verifica la presenza delle colonne già identificate. L'output contiene conteggi e `data_rows_read=0`; non espone valori di arbitri.

Questo controllo deve precedere ogni lettura reale delle righe.

## Foglio amministrativo

Il file viene creato vuoto dall'amministratore umano, che ne conserva proprietà e recupero. Dopo la condivisione diretta con il service account come editor, il comando:

```bash
reminder-certificati-runtime init-admin --spreadsheet-id ID
```

usa `TrasportoStrutturaSheets` per:

- verificare che il file contenga una singola tab completamente vuota oppure le quattro tab canoniche già ordinate;
- rinominare la tab vuota in `CONFIG` e aggiungere `NOTIFICHE`, `DASHBOARD` e `ANOMALIE`;
- inizializzare esclusivamente le tab vuote;
- rileggere e verificare ogni scrittura;
- bloccare sovrascritture distruttive.

Il service account non crea e non possiede file. Sono disponibili `TrasportoStrutturaMemoria` e `TrasportoStrutturaGoogleApi`.

## `NOTIFICHE`

Componenti:

- `TrasportoNotificheSheets`;
- `TrasportoNotificheMemoria`;
- `TrasportoNotificheGoogleApi`;
- `ArchivioNotificheGoogleSheets`;
- `RegistroPersistente` per applicare il ciclo di vita sopra l'archivio.

Prima di ogni append o update vengono verificate intestazioni e unicità della chiave. Duplicati, modifica di `creato_il`, regressione di `aggiornato_il` e identità incoerente sono errori bloccanti.

Il dry-run costruisce il registro in sola lettura, salta le chiavi già presenti e non salva transizioni. Il limite si applica ai candidati ancora prenotabili.

## `DASHBOARD` e `ANOMALIE`

`TrasportoMonitoraggioSheets` espone aggiornamento della fotografia dashboard e append delle anomalie. Sono disponibili adapter Google e fake in memoria.

La dashboard contiene solo dati aggregati e viene riscritta con un unico `values.update`, senza un `clear` preventivo che potrebbe lasciarla vuota in caso di errore intermedio. Le anomalie rimuovono indirizzi email, stringhe simili a token e chiavi `notification_id` dai messaggi tecnici.

## Client Google runtime

`google_runtime.costruisci_servizio_sheets` importa il client Google soltanto quando serve e usa Application Default Credentials temporanee. Nei test e nel dry-run anonimo non è necessario installare dipendenze Google.

Installazione opzionale:

```bash
pip install -e ".[google]"
```

La factory costruisce:

- sorgente di sola lettura per `Operativo`;
- archivio `NOTIFICHE`;
- writer di dashboard e anomalie;
- trasporto strutturale dell'inizializzatore.

La CI installa anche l'extra `google`, così dipendenze e import del percorso pre-produzione vengono verificati prima del merge.

## Variabili pubbliche previste

```text
GCP_PROJECT_ID
GCP_WORKLOAD_IDENTITY_PROVIDER
GCP_SERVICE_ACCOUNT
OPERATIVO_SPREADSHEET_ID
OPERATIVO_SHEET_NAME
OPERATIVO_HEADER_ROW
OPERATIVO_COLUMNS_A1
ADMIN_SPREADSHEET_ID
```

I parametri WIF e gli ID dei file sono identificatori, non chiavi private. Le condizioni di trust sono in [`AUTENTICAZIONE_GOOGLE.md`](AUTENTICAZIONE_GOOGLE.md).

Sono vietate configurazioni con chiavi permanenti come:

```text
GOOGLE_SERVICE_ACCOUNT_JSON
GOOGLE_APPLICATION_CREDENTIALS_JSON
GCP_SERVICE_ACCOUNT_KEY
```

Il file effimero prodotto dall'azione WIF sul runner non è una chiave privata permanente e viene escluso da Git.

## Privilegi minimi

Il service account dovrà:

1. essere impersonabile soltanto dal repository e dal workflow/environment autorizzato;
2. avere sola lettura su `CIA Lazio 25/26 - Automatico`;
3. avere modifica sul solo `Reminder certificati CIA Lazio — Gestione` già creato dall'utente;
4. non avere ruoli generali su Drive, Gmail, Calendar o dominio;
5. durante il primo collaudo, accedere soltanto a risorse sintetiche.

I permessi sui file derivano dalla condivisione diretta.

## Workflow manuale

`.github/workflows/manual-preproduction.yml` è eseguibile solo manualmente. Il job dichiara l'Environment e poi verifica `PREPRODUCTION_ENABLED` prima di checkout e autenticazione. Supporta:

- controllo delle sole intestazioni;
- inizializzazione o verifica del foglio amministrativo esistente;
- dry-run aggregato con data corrente o opzionale;
- un singolo test SMTP con conferma e override.

Il workflow usa WIF, permessi minimi, timeout e un gruppo `concurrency` condiviso con il futuro workflow di produzione. I segreti SMTP sono disponibili soltanto allo step di test.

## Concorrenza ed errori

Google Sheets non offre una transazione atomica tra ricerca e scrittura. `concurrency` impedisce due workflow simultanei, ma non sostituisce i controlli di duplicazione sul foglio.

Gli errori Google vengono convertiti in errori applicativi che riportano il tipo del problema senza credenziali, payload o dati personali. Uno schema ambiguo è fatale per l'esecuzione.

## Stato operativo

Codice, fake, adapter, CLI e workflow manuale sono presenti. Restano da completare esternamente:

- creazione umana del file amministrativo vuoto;
- progetto Google Cloud e WIF;
- environment e variabili GitHub;
- condivisione dei due file;
- prova sintetica di scritture;
- controllo reale delle intestazioni;
- dry-run reale con output aggregato.
