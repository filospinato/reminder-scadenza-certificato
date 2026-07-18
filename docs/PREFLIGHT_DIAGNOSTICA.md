# Diagnostica del preflight Google

Il comando `reminder-certificati-google-preflight` restituisce sempre JSON aggregato. In caso di errore applicativo usa un codice stabile, un messaggio breve e un'azione operativa. Non include ID degli Spreadsheet, contenuti delle celle, email, token o payload Google.

## Codici

| Codice | Significato | Azione |
|---|---|---|
| `PREFLIGHT_RESOURCE_IDS_EQUAL` | `Operativo` e amministrazione indicano lo stesso file | Correggere le Variables pubbliche dei due Spreadsheet |
| `PREFLIGHT_ADMIN_UNREACHABLE` | Il file amministrativo non è leggibile | Verificare ID, condivisione e identità WIF |
| `PREFLIGHT_ADMIN_TABS_INVALID` | Tab mancanti, duplicate o fuori ordine | Verificare o ripetere `init-admin` sul solo file amministrativo |
| `PREFLIGHT_ADMIN_HEADERS_UNREADABLE` | Le intestazioni amministrative non sono leggibili | Verificare permessi e integrità delle quattro tab |
| `PREFLIGHT_ADMIN_HEADERS_INVALID` | La riga 1 non rispetta lo schema | Confrontare con `docs/SCHEMA_FOGLI.md` |
| `PREFLIGHT_OPERATIVO_UNREACHABLE` | La riga 2 di `Operativo` non è leggibile | Verificare condivisione in sola lettura, nome tab e riga |
| `PREFLIGHT_OPERATIVO_HEADERS_MISSING` | Mancano intestazioni obbligatorie | Controllare la sola riga 2 prima di modificare la mappatura |
| `PREFLIGHT_UNEXPECTED_ERROR` | Errore non classificato prima o durante il preflight | Verificare WIF e log sanitizzati, poi ripetere |

## Contratto di sicurezza

Anche in caso di errore il risultato dichiara zero righe operative lette, zero scritture e SMTP non controllato. Le eccezioni tecniche originali restano collegate internamente per il debug, ma non vengono riportate nell'output pubblico.
