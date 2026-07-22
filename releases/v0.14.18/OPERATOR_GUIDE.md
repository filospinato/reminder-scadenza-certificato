# Guida operativa — release 0.14.18

Questa guida descrive le operazioni disponibili per il responsabile del reminder dei certificati medici.

## Stato sicuro

Lo stato sicuro è `INVIO_AUTOMATICO_ATTIVO=false` nella tab `CONFIG`. In questo stato:

- gli invii reali sono bloccati prima della lettura completa di `Operativo` e prima dell’inizializzazione SMTP;
- il controllo senza invio resta disponibile;
- il test SMTP verso il destinatario override resta disponibile come operazione manuale separata.

## Uso ordinario

Il workflow **Reminder certificati — controllo e prova** offre due operazioni.

### Controlla senza inviare

Esegue:

```bash
reminder-certificati check
```

Il comando verifica configurazione, intestazioni, dati rilevanti, candidati, dashboard e registro. Non usa SMTP e non scrive notifiche operative. Un risultato con anomalie o stati da revisionare termina con exit code non-zero.

### Invia email di prova

Esegue:

```bash
reminder-certificati test-smtp
```

La prova:

- usa un candidato reale già valido;
- sostituisce il destinatario con `DESTINATARIO_OVERRIDE`;
- invia al massimo un messaggio;
- registra una notifica distinta di tipo `TEST_CERTIFICATO_SCADENZA_V1`;
- è disponibile anche con l’invio automatico spento.

Non usare il test SMTP come sostituto del controllo senza invio.

## Manutenzione del foglio amministrativo

Il workflow **Reminder certificati — manutenzione** offre:

- `setup-preview`: descrive l’inizializzazione o la migrazione necessaria senza modificare il foglio;
- `setup-apply`: applica il piano previsto e crea un backup JSON quando modifica un foglio esistente;
- `registry-check`: collauda append, rilettura e aggiornamento di una sola notifica sintetica.

Comandi equivalenti:

```bash
reminder-certificati setup-admin --spreadsheet-id ID
reminder-certificati setup-admin --spreadsheet-id ID --apply
reminder-certificati registry-check
```

Usare `setup-apply` soltanto dopo aver revisionato l’anteprima. Ogni migrazione lascia `INVIO_AUTOMATICO_ATTIVO=false`.

## Invii reali controllati

Il workflow **Reminder certificati — invii reali** è disponibile manualmente sul branch `main`, usa l’Environment `preproduction` e consente un limite di 1, 5 o 10 messaggi.

La sequenza di rollout è:

1. impostare `INVIO_AUTOMATICO_ATTIVO=true` soltanto dopo autorizzazione esplicita;
2. eseguire un singolo invio con limite 1;
3. verificare notifica, dashboard, anomalie e deduplicazione;
4. eseguire un piccolo lotto con limite 5;
5. passare a 10 soltanto dopo la verifica del lotto precedente;
6. riportare l’interruttore su `false` al termine di ogni collaudo controllato, salvo autorizzazione al funzionamento continuativo.

La release non contiene una schedule automatica.

## Lettura degli esiti

Gli stati principali del registro sono:

- `SENDING`: invio prenotato, esito non concluso;
- `SENT`: accettazione SMTP confermata;
- `FAILED_RETRYABLE`: errore certamente precedente all’accettazione, ritentabile entro il limite;
- `FAILED_PERMANENT`: rifiuto definitivo o configurazione non recuperabile automaticamente;
- `UNKNOWN_REVIEW_REQUIRED`: non è possibile stabilire se il messaggio sia stato accettato.

`SENT`, `FAILED_PERMANENT` e `UNKNOWN_REVIEW_REQUIRED` bloccano nuovi tentativi automatici.

## Arresto immediato

1. Impostare `INVIO_AUTOMATICO_ATTIVO=false`.
2. Annullare eventuali workflow produttivi già in corso.
3. Se necessario, revocare temporaneamente credenziali SMTP o accesso WIF.
4. Non cancellare righe di `NOTIFICHE` finché l’esito non è stato ricostruito.
5. Eseguire `reminder-certificati check` per una diagnosi aggregata senza invio.

## Gestione degli incidenti

### Esito incerto

Per `UNKNOWN_REVIEW_REQUIRED` o una riga `SENDING` rimasta aperta, non ritentare automaticamente. Verificare sul server SMTP tramite `Message-ID` e orario:

- consegna confermata: correggere a `SENT` con procedura controllata;
- mancata consegna certa e temporanea: correggere a `FAILED_RETRYABLE` soltanto se restano tentativi;
- dubbio residuo: lasciare lo stato incerto.

### Errore permanente

Correggere la causa e decidere manualmente se una nuova notifica sia legittima. Non trasformare automaticamente lo stato in ritentabile.

### Retry esauriti

Dopo tre tentativi un errore ritentabile non viene più prenotato. Non azzerare il contatore senza aver ricostruito la causa.

### Schema alterato

Mantenere gli invii spenti, creare una copia di sicurezza, eseguire `setup-admin` in anteprima e applicare soltanto un piano atteso. Concludere con `check`.

### Compromissione Google o SMTP

Per Google rimuovere il binding WIF, disabilitare il provider o revocare la condivisione dei file. Per SMTP disabilitare le credenziali e ruotare il Secret. Non creare chiavi JSON permanenti come soluzione temporanea.

## Consegna a un responsabile

Prima del passaggio di gestione devono essere assegnati:

- responsabile del repository;
- proprietario del foglio amministrativo;
- referente Google Cloud;
- referente MDaemon;
- contatto umano di recupero.

I dettagli personali e le credenziali restano fuori dal repository.

Il responsabile non tecnico deve saper:

1. accendere e spegnere `INVIO_AUTOMATICO_ATTIVO`;
2. eseguire il controllo senza invio;
3. configurare l’override ed eseguire una prova SMTP;
4. leggere dashboard, anomalie e registro;
5. riconoscere un errore ritentabile, permanente o incerto;
6. applicare la procedura di arresto.

## Rollback applicativo

Ripristinare l’ultimo commit verde tramite pull request di revert, senza forzare `main`. Se lo schema del foglio è già stato aggiornato, non ripristinare una versione incompatibile senza un piano esplicito. Mantenere gli invii spenti durante tutto il rollback.
