# Diagnostica del controllo Google

Il comando `reminder-certificati check` include il preflight Google e restituisce risultati aggregati. In caso di errore applicativo usa un codice stabile, un messaggio breve e un'azione operativa. Non include ID degli Spreadsheet, contenuti delle righe operative, email, token o payload Google.

Il preflight verifica:

- presenza delle quattro tab amministrative per nome;
- intestazioni canoniche delle tab amministrative;
- chiavi, valori funzionali e `SCHEMA_VERSION` della tab `CONFIG`;
- presenza in `Operativo` delle otto colonne effettivamente usate.

La fase preflight legge il contenuto della sola tab `CONFIG`, ma non legge righe anagrafiche di `Operativo`, non scrive celle e non usa SMTP. Le fasi successive di `check` validano le righe operative e revisionano il registro senza inviare.

## Codici

| Codice | Significato | Azione |
|---|---|---|
| `PREFLIGHT_RESOURCE_IDS_EQUAL` | `Operativo` e amministrazione indicano lo stesso file | Correggere le Variables dei due Spreadsheet |
| `PREFLIGHT_ADMIN_UNREACHABLE` | Il file amministrativo non è leggibile | Verificare ID, condivisione e identità WIF |
| `PREFLIGHT_ADMIN_TABS_INVALID` | Tab mancanti o duplicate | Eseguire `setup-admin` sul file amministrativo |
| `PREFLIGHT_ADMIN_HEADERS_UNREADABLE` | Le intestazioni amministrative non sono leggibili | Verificare permessi e integrità delle quattro tab |
| `PREFLIGHT_ADMIN_HEADERS_INVALID` | La riga 1 non rispetta lo schema | Eseguire `setup-admin` in anteprima e confrontare con `docs/SCHEMA_FOGLI.md` |
| `PREFLIGHT_ADMIN_CONFIG_INVALID` | Le chiavi o i valori della CONFIG non sono compatibili | Eseguire `setup-admin` in anteprima mantenendo l'invio automatico spento |
| `PREFLIGHT_OPERATIVO_UNREACHABLE` | Le intestazioni canoniche di `Operativo` non sono leggibili | Verificare condivisione in sola lettura e contratto tab `Operativo`, riga 2 |
| `PREFLIGHT_OPERATIVO_HEADERS_MISSING` | Manca una colonna usata dal reminder | Controllare la riga 2 del foglio sorgente e aggiornare il codice se il contratto è cambiato |
| `PREFLIGHT_UNEXPECTED_ERROR` | Errore non classificato | Verificare WIF e log sanitizzati, poi ripetere |

## Contratto di sicurezza

Anche in caso di errore il risultato preflight dichiara zero righe operative lette, zero scritture e SMTP non controllato. Le eccezioni tecniche originali restano collegate internamente per il debug, ma non vengono riportate nell'output pubblico.
