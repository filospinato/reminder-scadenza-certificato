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

Il modulo `admin_initializer` usa `TrasportoStrutturaSheets` per:

- creare il file canonico con le quattro tab;
- leggere metadati e ordine delle tab;
- inizializzare esclusivamente le tab vuote;
- rileggere e verificare la scrittura;
- bloccare sovrascritture distruttive.

Sono disponibili `TrasportoStrutturaMemoria` e `TrasportoStrutturaGoogleApi`.

## `NOTIFICHE`

Componenti:

- `TrasportoNotificheSheets`;
- `TrasportoNotificheMemoria`;
- `TrasportoNotificheGoogleApi`;
- `ArchivioNotificheGoogleSheets`;
- `RegistroPersistente` per applicare il ciclo di vita sopra l'archivio.

Prima di ogni append o update vengono verificate intestazioni e unicità della chiave. Duplicati, modifica di `creato_il`, regressione di `aggiornato_il` e identità incoerente sono errori bloccanti.

## `DASHBOARD` e `ANOMALIE`

`TrasportoMonitoraggioSheets` espone sostituzione della fotografia dashboard e append delle anomalie. Sono disponibili adapter Google e fake in memoria.

La dashboard contiene solo dati aggregati. Le anomalie rimuovono indirizzi email e stringhe simili a token e non conservano righe complete.

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
3. avere modifica sul solo `Reminder certificati CIA Lazio — Gestione`;
4. non avere ruoli generali su Drive, Gmail, Calendar o dominio;
5. durante il primo collaudo, accedere soltanto a risorse sintetiche.

I permessi sui file derivano dalla condivisione diretta.

## Workflow manuale

`.github/workflows/manual-preproduction.yml` è eseguibile solo manualmente ed è disabilitato finché la variabile dell'environment non viene impostata esplicitamente. Supporta:

- controllo delle sole intestazioni;
- inizializzazione o verifica del foglio amministrativo;
- dry-run aggregato;
- test SMTP con conferma e override.

Il workflow usa WIF, permessi minimi, timeout e `concurrency` senza sovrapposizioni.

## Concorrenza ed errori

Google Sheets non offre una transazione atomica tra ricerca e scrittura. `concurrency` impedisce due workflow simultanei, ma non sostituisce i controlli di duplicazione sul foglio.

Gli errori Google vengono convertiti in errori applicativi che riportano il tipo del problema senza credenziali, payload o dati personali. Uno schema ambiguo è fatale per l'esecuzione.

## Stato operativo

Codice, fake, adapter, CLI e workflow manuale sono presenti. Restano da completare esternamente:

- progetto Google Cloud e WIF;
- environment e variabili GitHub;
- condivisione dei due file;
- creazione del foglio amministrativo;
- prova sintetica di scritture;
- controllo reale delle intestazioni;
- dry-run reale con output aggregato.
