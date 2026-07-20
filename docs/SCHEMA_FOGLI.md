# Schema dei fogli amministrativi

Il file separato canonico è `Reminder certificati CIA Lazio — Gestione`. Le tab richieste sono `CONFIG`, `NOTIFICHE`, `DASHBOARD` e `ANOMALIE`; il loro ordine visuale non è significativo.

## Versione dello schema

La versione corrente è **2** ed è registrata in CONFIG come:

```text
SCHEMA_VERSION | 2
```

`SCHEMA_VERSION` è gestita dal programma. Un foglio precedente deve essere aggiornato con `reminder-certificati migrate-admin`, prima in anteprima e poi con conferma e backup.

## CONFIG

Intestazioni:

```text
chiave | valore | tipo | descrizione | modificabile
```

| Chiave | Valore iniziale | Scopo |
|---|---:|---|
| `SCHEMA_VERSION` | `2` | versione del contratto amministrativo |
| `AUTOMAZIONE_ATTIVA` | `false` | unico interruttore operativo |
| `INVII_REALI_ABILITATI` | `false` | barriera separata per il go-live |
| `GIORNI_PREAVVISO` | `30` | finestra inclusiva |
| `LIMITE_INVII_PER_ESECUZIONE` | `10` | massimo per esecuzione |
| `DESTINATARIO_OVERRIDE` | vuoto | destinatario del test SMTP |
| `OGGETTO_EMAIL` | predefinito | oggetto del promemoria |
| `CORPO_EMAIL` | predefinito | testo dopo il saluto automatico |
| `FIRMA_TESTO` | provvisoria | firma testuale |

Il preflight valida intestazioni, presenza delle chiavi, valori funzionali e versione. Le colonne `tipo`, `descrizione` e `modificabile` restano informative.

## NOTIFICHE

Intestazioni dello schema v2:

```text
notification_id | id_arbitro | scadenza_certificato | tipo | stato | tentativi | creato_il | aggiornato_il | message_id | versione_app | errore
```

Nome, cognome ed email non vengono persistiti.

La chiave è stabile rispetto alla finestra di preavviso:

```text
ID_ARBITRO|DATA_SCADENZA|CERTIFICATO_SCADENZA_V1
```

Stati:

- `SENDING`: prenotazione avvenuta, esito non ancora concluso;
- `SENT`: invio confermato;
- `FAILED_RETRYABLE`: errore ritentabile, fino a tre tentativi complessivi;
- `FAILED_PERMANENT`: errore certo e non ritentabile;
- `UNKNOWN_REVIEW_REQUIRED`: esito incerto da verificare manualmente.

`SENT`, `SENDING`, `FAILED_PERMANENT` e `UNKNOWN_REVIEW_REQUIRED` bloccano nuovi tentativi. Le chiavi duplicate bloccano l'esecuzione.

## Migrazione dallo schema precedente

La migrazione:

1. legge CONFIG e NOTIFICHE;
2. produce un'anteprima aggregata;
3. salva un backup JSON prima dell'applicazione;
4. sostituisce le vecchie chiavi con lo schema v2;
5. converte `REMINDER_n` nel tipo stabile;
6. elimina nome, cognome ed email dal registro;
7. rifiuta collisioni tra chiavi convertite;
8. lascia automazione e invii reali disattivati.

## DASHBOARD e ANOMALIE

La dashboard contiene solo metriche aggregate. ANOMALIE conserva codice, origine, riga e campo, con messaggio limitato e sanitizzato. Non devono esservi copiati payload Google, credenziali o contenuti completi delle righe.

## Concorrenza

Google Sheets non offre una transazione completa tra ricerca e scrittura. Tutti i workflow canonici condividono il gruppo `reminder-certificati-runtime`; gli invii non devono essere lanciati contemporaneamente da percorsi esterni non coordinati.
