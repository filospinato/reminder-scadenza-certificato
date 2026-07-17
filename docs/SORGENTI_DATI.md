# Sorgenti dati e Google Sheets

Il dominio non dipende direttamente dalla Google Sheets API. Le sorgenti restituiscono una `TabellaDati`; validazione, selezione delle scadenze e composizione dei messaggi lavorano sul formato normalizzato.

## Componenti

- `SorgenteDati`: protocollo minimo con il metodo `leggi()`;
- `SorgenteMemoria`: sorgente usata nei test e nelle simulazioni;
- `AdapterGoogleSheets`: costruisce l'intervallo A1 e usa un lettore iniettato;
- `LettoreValoriSheets`: protocollo del trasporto Google;
- `LettoreGoogleApi`: ponte verso un servizio Google API già autenticato;
- `leggi_e_valida`: collega qualsiasi sorgente alla validazione del dominio.

Questa separazione consente di testare quasi tutto senza rete, credenziali o Spreadsheet reali.

## Struttura attesa

La prima riga della matrice contiene le intestazioni. Le righe successive contengono i dati. Ogni arbitro occupa una sola riga e le colonne logiche obbligatorie comprendono `id_arbitro`, `nome`, `cognome`, `email`, `scadenza_certificato` e `attivo`.

L'adapter:

- rifiuta una matrice vuota;
- rifiuta intestazioni mancanti, vuote o duplicate;
- completa con stringhe vuote le righe più corte;
- rifiuta celle non vuote oltre il numero delle intestazioni;
- rifiuta righe che non siano sequenze di celle;
- conserva il numero di riga coerente con Google Sheets, partendo da 2 per i dati.

Le regole logiche dei campi sono in [`CONTRATTO_DATI.md`](CONTRATTO_DATI.md).

## Configurazione prevista

I valori reali non devono essere scritti nel repository. Saranno forniti tramite GitHub Actions Secrets o Variables:

```text
GOOGLE_SERVICE_ACCOUNT_JSON
OPERATIVO_SPREADSHEET_ID
OPERATIVO_SHEET_NAME
OPERATIVO_COLUMNS_A1
```

`OPERATIVO_COLUMNS_A1` potrà avere un valore come `A:Z` o un intervallo più ristretto dopo aver verificato le colonne effettive.

## Privilegi minimi

Il service account dovrà:

1. avere accesso soltanto agli Spreadsheet necessari;
2. essere lettore del database `Operativo`;
3. non possedere ruoli amministrativi sul progetto o sul dominio;
4. usare per la lettura lo scope Google Sheets in sola lettura;
5. ottenere accesso in scrittura soltanto al futuro foglio amministrativo.

La costruzione concreta delle credenziali verrà aggiunta soltanto quando saranno disponibili gli identificativi reali e dopo una prova con un foglio sintetico.

## Intervallo A1

Il nome della scheda viene racchiuso tra apici e gli apostrofi interni vengono raddoppiati. Per esempio:

```text
Arbitri d'Italia
```

diventa:

```text
'Arbitri d''Italia'!A:Z
```

## Gestione degli errori

Gli errori tecnici della libreria Google vengono convertiti in `ErroreSorgenteDati`. Il messaggio conserva il tipo dell'errore, ma non include credenziali, payload completi o dati personali.

Un errore di lettura o di schema è fatale per quella esecuzione: il sistema non deve procedere con una tabella parziale o ambigua. Nome, cognome, email e scadenza non vengono mai ricombinati tra righe diverse.

## Stato attuale

L'interfaccia, l'adapter e il ponte verso un servizio Google già autenticato sono implementati e testati con fake. Non sono ancora presenti:

- dipendenze Google installate in produzione;
- credenziali;
- Spreadsheet ID reali;
- accesso al database `Operativo`;
- scrittura nel foglio amministrativo.
