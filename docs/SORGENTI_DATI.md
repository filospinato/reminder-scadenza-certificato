# Sorgenti dati e Google Sheets

Il dominio non dipende direttamente dalla Google Sheets API. La lettura di `Operativo` e la persistenza amministrativa usano contratti separati, così quasi tutta la logica può essere verificata senza rete, credenziali o Spreadsheet reali.

## Lettura di `Operativo`

Componenti:

- `SorgenteDati`: protocollo minimo con il metodo `leggi()`;
- `SorgenteMemoria`: sorgente usata nei test e nelle simulazioni;
- `AdapterGoogleSheets`: costruisce l'intervallo A1 e usa un lettore iniettato;
- `LettoreValoriSheets`: protocollo del trasporto di sola lettura;
- `LettoreGoogleApi`: ponte verso un servizio Google API già autenticato;
- `leggi_e_valida`: collega qualsiasi sorgente alla validazione del dominio.

La prima riga della matrice contiene le intestazioni. Le righe successive contengono i dati. Ogni arbitro occupa una sola riga e le colonne logiche obbligatorie comprendono `id_arbitro`, `nome`, `cognome`, `email`, `scadenza_certificato` e `attivo`.

L'adapter:

- rifiuta una matrice vuota;
- rifiuta intestazioni mancanti, vuote o duplicate;
- completa con stringhe vuote le righe più corte;
- rifiuta celle non vuote oltre il numero delle intestazioni;
- rifiuta righe che non siano sequenze di celle;
- conserva il numero di riga coerente con Google Sheets, partendo da 2 per i dati.

Le regole logiche dei campi sono in [`CONTRATTO_DATI.md`](CONTRATTO_DATI.md).

## Persistenza di `NOTIFICHE`

Componenti:

- `TrasportoNotificheSheets`: protocollo per lettura, append e update;
- `TrasportoNotificheMemoria`: fake tabellare usato nei test;
- `TrasportoNotificheGoogleApi`: ponte verso un servizio Sheets già autenticato;
- `ArchivioNotificheGoogleSheets`: ricerca la chiave, decide tra append e update e applica i controlli di coerenza.

Il registro amministrativo non modifica mai `Operativo`. Prima di scrivere verifica lo schema canonico delle quattordici colonne e richiede che la `notification_id` sia assente o presente una sola volta. Duplicati, timestamp regressivi e modifica di `creato_il` sono errori bloccanti.

Append e update usano `valueInputOption=RAW`. Il nome della scheda viene racchiuso tra apici e gli apostrofi interni vengono raddoppiati.

## Configurazione prevista

I valori reali non devono essere scritti nel repository. Saranno forniti tramite GitHub Actions Secrets o Variables:

```text
GOOGLE_SERVICE_ACCOUNT_JSON
OPERATIVO_SPREADSHEET_ID
OPERATIVO_SHEET_NAME
OPERATIVO_COLUMNS_A1
ADMIN_SPREADSHEET_ID
NOTIFICHE_SHEET_NAME
```

`OPERATIVO_COLUMNS_A1` potrà avere un valore come `A:Z` o un intervallo più ristretto dopo aver verificato le colonne effettive. `NOTIFICHE_SHEET_NAME` avrà come default `NOTIFICHE`.

## Privilegi minimi

Il service account dovrà:

1. avere accesso soltanto agli Spreadsheet necessari;
2. essere lettore del database `Operativo`;
3. non possedere ruoli amministrativi sul progetto o sul dominio;
4. usare accesso in sola lettura per `Operativo`;
5. ottenere accesso in scrittura soltanto allo Spreadsheet amministrativo;
6. durante il collaudo, essere condiviso esclusivamente con uno Spreadsheet sintetico senza dati reali.

La costruzione concreta delle credenziali verrà aggiunta soltanto dopo una prova controllata sul foglio sintetico.

## Concorrenza

Una sequenza “leggi, cerca, scrivi” su Google Sheets non è una transazione atomica. Per evitare che due esecuzioni leggano contemporaneamente la stessa assenza e aggiungano entrambe una riga, il workflow di produzione dovrà usare un gruppo `concurrency` senza sovrapposizioni.

I controlli sul foglio restano comunque obbligatori: una chiave duplicata già presente, anche per modifica manuale, blocca la scrittura.

## Gestione degli errori

Gli errori tecnici della libreria Google vengono convertiti in errori applicativi stabili. I messaggi conservano il tipo dell'errore, ma non includono credenziali, payload completi o dati personali superflui.

Un errore di lettura, schema o ambiguità è fatale per quella esecuzione: il sistema non procede con una tabella parziale e non tenta di scegliere arbitrariamente una riga. Nome, cognome, email e scadenza non vengono mai ricombinati tra righe diverse.

## Stato attuale

Sono implementati e testati con fake:

- lettura e validazione tabellare di `Operativo`;
- ponte di sola lettura verso un servizio Google già autenticato;
- schema della tab `NOTIFICHE`;
- ricerca univoca della chiave;
- append e update controllato;
- ponte di scrittura verso un servizio Google già autenticato.

Non sono ancora presenti credenziali, dipendenze Google installate in produzione, Spreadsheet ID reali, accesso a `Operativo` o scritture su un foglio amministrativo reale.
