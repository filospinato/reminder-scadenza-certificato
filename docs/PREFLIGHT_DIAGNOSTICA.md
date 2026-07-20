# Diagnostica del preflight Google

Il sottocomando `reminder-certificati preflight` restituisce JSON aggregato. In caso di errore applicativo usa un codice stabile, un messaggio breve e un'azione operativa. Non include ID degli Spreadsheet, contenuti delle righe operative, email, token o payload Google.

Il preflight verifica:

- presenza delle quattro tab amministrative per nome;
- intestazioni canoniche delle tab amministrative;
- chiavi, valori funzionali e `SCHEMA_VERSION` della tab `CONFIG`;
- presenza in `Operativo` delle sole sei colonne effettivamente usate.

Legge il contenuto della sola tab `CONFIG`, ma non legge righe anagrafiche di `Operativo`, non scrive celle e non usa SMTP.

## Codici

| Codice | Significato | Azione |
|---|---|---|
| `PREFLIGHT_RESOURCE_IDS_EQUAL` | `Operativo` e amministrazione indicano lo stesso file | Correggere le Variables dei due Spreadsheet |
| `PREFLIGHT_ADMIN_UNREACHABLE` | Il file amministrativo non è leggibile | Verificare ID, condivisione e identità WIF |
| `PREFLIGHT_ADMIN_TABS_INVALID` | Tab mancanti o duplicate | Verificare o ripetere `reminder-certificati init-admin` sul solo file amministrativo |
| `PREFLIGHT_ADMIN_HEADERS_UNREADABLE` | Le intestazioni amministrative non sono leggibili | Verificare permessi e integrità delle quattro tab |
| `PREFLIGHT_ADMIN_HEADERS_INVALID` | La riga 1 non rispetta lo schema | Eseguire `migrate-admin` in anteprima e confrontare con `docs/SCHEMA_FOGLI.md` |
| `PREFLIGHT_ADMIN_CONFIG_INVALID` | Le chiavi o i valori della CONFIG non sono compatibili con il runtime | Eseguire `migrate-admin` in anteprima e correggere la CONFIG mantenendo il sistema disattivato |
| `PREFLIGHT_OPERATIVO_UNREACHABLE` | La riga delle intestazioni di `Operativo` non è leggibile | Verificare condivisione in sola lettura, nome tab e riga |
| `PREFLIGHT_OPERATIVO_HEADERS_MISSING` | Manca una colonna usata dal reminder | Controllare la sola riga delle intestazioni prima di modificare la mappatura |
| `PREFLIGHT_UNEXPECTED_ERROR` | Errore non classificato prima o durante il preflight | Verificare WIF e log sanitizzati, poi ripetere |

## Contratto di sicurezza

Anche in caso di errore il risultato dichiara zero righe operative lette, zero scritture e SMTP non controllato. Le eccezioni tecniche originali restano collegate internamente per il debug, ma non vengono riportate nell'output pubblico.
