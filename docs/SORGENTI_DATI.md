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

La prima riga della matrice restituita dall'adapter contiene le intestazioni. La posizione originale nel foglio è configurabile: nella struttura verificata di `Operativo` le intestazioni sono in riga 2 e la prima riga dati è quindi la 3.

Ogni arbitro occupa una sola riga e le colonne logiche obbligatorie comprendono `id_arbitro`, `nome`, `cognome`, `email`, `scadenza_certificato` e `attivo`.

L'adapter:

- rifiuta una matrice vuota;
- rifiuta intestazioni mancanti, vuote o duplicate;
- completa con stringhe vuote le righe più corte;
- rifiuta celle non vuote oltre il numero delle intestazioni;
- rifiuta righe che non siano sequenze di celle;
- costruisce l'intervallo A1 dalla riga configurata;
- conserva il numero di riga originale per le anomalie.

Le regole logiche dei campi sono in [`CONTRATTO_DATI.md`](CONTRATTO_DATI.md).

## Persistenza di `NOTIFICHE`

Componenti:

- `TrasportoNotificheSheets`: protocollo per lettura, append e update;
- `TrasportoNotificheMemoria`: fake tabellare usato nei test;
- `TrasportoNotificheGoogleApi`: ponte verso un servizio Sheets già autenticato;
- `ArchivioNotificheGoogleSheets`: ricerca la chiave, decide tra append e update e applica i controlli di coerenza.

Il registro amministrativo non modifica mai `Operativo`. Prima di scrivere verifica lo schema canonico delle quattordici colonne e richiede che la `notification_id` sia assente o presente una sola volta. Duplicati, timestamp regressivi e modifica di `creato_il` sono errori bloccanti.

Append e update usano `valueInputOption=RAW`. Il nome della scheda viene racchiuso tra apici e gli apostrofi interni vengono raddoppiati.

## Autenticazione prevista

GitHub Actions userà Workload Identity Federation e OIDC. Non verranno salvate chiavi JSON permanenti nel repository o nei GitHub Secrets.

Identificatori pubblici previsti come GitHub Actions Variables:

```text
GCP_PROJECT_ID
GCP_WORKLOAD_IDENTITY_PROVIDER
GCP_SERVICE_ACCOUNT
OPERATIVO_SPREADSHEET_ID
OPERATIVO_SHEET_NAME
OPERATIVO_HEADER_ROW
OPERATIVO_COLUMNS_A1
ADMIN_SPREADSHEET_ID
NOTIFICHE_SHEET_NAME
```

`OPERATIVO_COLUMNS_A1` potrà avere un valore come `A:Z` o un intervallo più ristretto dopo aver verificato le colonne effettive. `NOTIFICHE_SHEET_NAME` avrà come default `NOTIFICHE`.

Sono vietate variabili che contengano chiavi permanenti, tra cui:

```text
GOOGLE_SERVICE_ACCOUNT_JSON
GOOGLE_APPLICATION_CREDENTIALS_JSON
GCP_SERVICE_ACCOUNT_KEY
```

Il contratto di configurazione è validato da `ConfigurazioneGoogleWif`. Il provisioning completo e le condizioni di trust sono documentati in [`AUTENTICAZIONE_GOOGLE.md`](AUTENTICAZIONE_GOOGLE.md).

## Privilegi minimi

Il service account dovrà:

1. essere impersonabile soltanto dal repository GitHub autorizzato tramite WIF/OIDC;
2. avere accesso soltanto agli Spreadsheet necessari;
3. essere lettore del database `Operativo`;
4. non possedere ruoli amministrativi sul progetto, su Drive o sul dominio;
5. ottenere accesso in scrittura soltanto allo Spreadsheet amministrativo;
6. durante il collaudo, essere condiviso esclusivamente con uno Spreadsheet sintetico senza dati reali.

I permessi sui singoli Spreadsheet saranno concessi tramite condivisione diretta con l'email del service account. Non è necessario assegnare un ruolo generale su Google Drive.

## Concorrenza

Una sequenza “leggi, cerca, scrivi” su Google Sheets non è una transazione atomica. Per evitare che due esecuzioni leggano contemporaneamente la stessa assenza e aggiungano entrambe una riga, il workflow di produzione dovrà usare un gruppo `concurrency` senza sovrapposizioni.

I controlli sul foglio restano comunque obbligatori: una chiave duplicata già presente, anche per modifica manuale, blocca la scrittura.

## Gestione degli errori

Gli errori tecnici della libreria Google vengono convertiti in errori applicativi stabili. I messaggi conservano il tipo dell'errore, ma non includono credenziali, payload completi o dati personali superflui.

Un errore di lettura, schema o ambiguità è fatale per quella esecuzione: il sistema non procede con una tabella parziale e non tenta di scegliere arbitrariamente una riga. Nome, cognome, email e scadenza non vengono mai ricombinati tra righe diverse.

## Stato attuale

Sono implementati e testati con fake:

- lettura e validazione tabellare di `Operativo`;
- supporto alle intestazioni reali in riga 2;
- ponte di sola lettura verso un servizio Google già autenticato;
- schema della tab `NOTIFICHE`;
- ricerca univoca della chiave;
- append e update controllato;
- ponte di scrittura verso un servizio Google già autenticato;
- validazione degli identificatori WIF e rifiuto delle chiavi permanenti.

Sono documentati, ma non ancora applicati, il provisioning WIF/OIDC e i privilegi minimi. Non sono ancora presenti configurazione IAM reale, accesso a `Operativo`, scritture su un foglio amministrativo reale o workflow autenticati.
