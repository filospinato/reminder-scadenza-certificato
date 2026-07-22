# Runbook operativo

Questo documento descrive le operazioni disponibili e il loro significato; i dettagli di attivazione esterna restano nella checklist di deployment.

## Stato sicuro

`INVIO_AUTOMATICO_ATTIVO=false` è lo stato iniziale e quello ripristinato dopo ogni aggiornamento del foglio amministrativo.

Il controllo senza invio e la prova sul destinatario override restano disponibili anche quando l'invio automatico è spento.

## Uso ordinario

Il workflow ordinario presenta due sole scelte:

- `check`, che verifica configurazione, dati, candidati e registro senza inviare;
- `test-smtp`, che mantiene il comportamento corrente e invia al massimo un messaggio al `DESTINATARIO_OVERRIDE`.

## Manutenzione

Il workflow di manutenzione presenta tre scelte:

- `setup-preview`, per vedere se il foglio richiede preparazione o aggiornamento;
- `setup-apply`, per applicare l'operazione prevista con backup quando necessario;
- `registry-check`, per collaudare una sola riga sintetica nella tab `NOTIFICHE`.

## CONFIG

La tab contiene soltanto `chiave`, `valore` e `descrizione`. Le impostazioni modificabili sono:

- `INVIO_AUTOMATICO_ATTIVO`;
- `GIORNI_PREAVVISO`;
- `DESTINATARIO_OVERRIDE`;
- `OGGETTO_EMAIL`;
- `CORPO_EMAIL`.

`SCHEMA_VERSION` è gestita dal programma. Il limite di 10 messaggi per esecuzione è interno e non richiede decisioni dell'operatore.

La firma HTML e quella `text/plain` sono gestite insieme nel codice e non si modificano dal foglio.

Per il rollout produttivo il comando accetta `--max-sends 1..10`: il valore può soltanto ridurre il limite interno. Usare prima 1, poi 5 e infine 10 dopo aver verificato gli esiti del lotto precedente.

## Stati leggibili

I riepiloghi traducono gli stati tecnici in etichette come “Controllo completato”, “Attenzione richiesta”, “Errore definitivo” e “Verifica manuale necessaria”. Un controllo con anomalie o una prova SMTP senza alcun tentativo restituiscono un exit code non-zero. Gli stati originali restano conservati internamente per non alterare la macchina a stati.

## File collegati

- `docs/DEPLOYMENT_CHECKLIST.md` descrive i passaggi esterni ancora necessari;
- `docs/EMERGENCY.md` descrive l'arresto e la gestione degli incidenti;
- `docs/SCHEMA_FOGLI.md` documenta le tab e le colonne;
- `docs/TEST_PLAN.md` definisce i collaudi richiesti.
