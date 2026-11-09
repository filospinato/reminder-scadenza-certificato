# Reminder scadenza certificato

## Obiettivo

Promemoria email per i tesserati con certificato medico in scadenza. Il programma legge un foglio Google, seleziona le persone attive e mantiene un registro per evitare invii duplicati.

## Architettura

Il programma Python gira sui runner Linux di **GitHub Actions**, soltanto durante le esecuzioni: non richiede un computer acceso né un server dedicato. Usa due Google Sheets separati, uno come sorgente e uno per configurazione, registro e monitoraggio; invia tramite il server SMTP della casella configurata.

Con una **repository pubblica**, i runner standard di GitHub Actions sono gratuiti e non consumano la quota inclusa per le repository private. Runner maggiorati e servizi esterni seguono le proprie condizioni: [fatturazione GitHub Actions](https://docs.github.com/en/billing/concepts/product-billing/github-actions). Il programma non usa API di intelligenza artificiale.

## Modello di sicurezza

- Il foglio sorgente `Operativo` resta in sola lettura; Google usa credenziali temporanee WIF/OIDC.
- Il controllo `check` non invia email; `test-smtp` invia al massimo una prova al destinatario override.
- Gli invii reali richiedono `INVIO_AUTOMATICO_ATTIVO=true` nella CONFIG.
- Il registro prenota ogni invio prima del contatto SMTP; gli esiti incerti richiedono revisione e non vengono ritentati automaticamente.
- I workflow operativi usano `main` e lo stesso lock. Password e dati dei tesserati restano fuori dal codice e dai log.

## Configurazione

Nomi e ambiti delle impostazioni sono nel [contratto GitHub](config/github/environment-contract.json). Le Variables restano nell'Environment `preproduction`; `SMTP_USERNAME` identifica anche il mittente.

La password va nel **repository secret** `REMINDER_SMTP_PASSWORD`, passato al programma soltanto negli step SMTP dei workflow attuali. Un collaboratore può inserirla **dal proprio account e dal proprio dispositivo**, senza comunicarla al proprietario:

1. Il proprietario invita il collaboratore in **Settings → Collaborators**.
2. Il collaboratore accetta e apre **Settings → Secrets and variables → Actions → New repository secret**.
3. Inserisce `REMINDER_SMTP_PASSWORD`, la password SMTP, quindi **Add secret**.

Non creare questo segreto nell'Environment: nelle repository personali quella configurazione richiede il proprietario. La collaborazione funziona anche con una repository privata; renderla pubblica non concede accesso alle impostazioni. La password salvata non è rileggibile dall'interfaccia, ma il codice autorizzato può utilizzarla: chi può modificare i workflow deve essere fidato. [Guida GitHub ai Secrets](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets).

Il vecchio Secret `SMTP_PASSWORD` non è più usato dai workflow aggiornati. Non creare un Environment secret con lo stesso nome del nuovo repository secret, perché avrebbe precedenza.

## Attivare e fermare gli invii dal foglio

Nel **foglio di gestione**, aprire la scheda **CONFIG** e cercare la riga **INVIO_AUTOMATICO_ATTIVO**. Modificare soltanto la colonna **valore** (cella **B3** nello schema iniziale):

- **`true` — attivare o riattivare:** consente gli invii reali dalla successiva esecuzione GitHub, programmata ogni giorno alle **09:15, ora italiana**, con un massimo di **50 email per esecuzione**. Cambiare la cella non avvia immediatamente un invio.
- **`false` — disattivare:** blocca gli invii reali delle esecuzioni successive. Il valore viene letto all'avvio: per fermare un'esecuzione già partita, aprire **GitHub → Actions**, selezionare il run produttivo e premere **Cancel workflow**. Le email già inviate non possono essere annullate.

La scheda **DASHBOARD** mostra l'ultima esecuzione, non lo stato in tempo reale dell'interruttore. `check` resta disponibile senza invii; `test-smtp` può inviare una prova manuale anche con l'interruttore su `false`. Conservare il registro **NOTIFICHE**, che evita i duplicati; la password resta nei Secrets GitHub.

## Stato semantico

Il workflow **Reminder certificati — invii reali** viene eseguito una volta al giorno alle **09:15** nel fuso **Europe/Rome**, anche nei festivi; l'orario segue automaticamente ora legale e solare. Il limite è **50 invii per esecuzione**. Il registro evita di reinviare il promemoria per la stessa scadenza; eventuali candidati oltre il limite vengono rivalutati nelle esecuzioni successive, finché rientrano nella finestra di preavviso.

Per un avvio manuale: **Actions → Reminder certificati — invii reali → Run workflow**, branch `main`, limite 1, 5, 10 o 50. Il valore predefinito è 50; il foglio deve essere su `true`. `DESTINATARIO_OVERRIDE` serve soltanto alla prova SMTP: gli invii reali usano gli indirizzi del foglio sorgente.

Controllare periodicamente **DASHBOARD → ultima_esecuzione** e gli esiti in Actions. GitHub può avviare il job in ritardo; nelle repository pubbliche disabilita la programmazione dopo 60 giorni senza attività sul repository. Se disabilitata, riattivarla da **Actions → Reminder certificati — invii reali → Enable workflow**, verificando prima CONFIG e registro ([limiti della programmazione](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule)).

In caso di `UNKNOWN_REVIEW_REQUIRED` o `SENDING` rimasto sospeso, mettere `false` e confrontare il registro con i log del server SMTP prima di decidere se ritentare. Non cancellare le righe per forzare un nuovo invio. Gli errori temporanei consentono al massimo tre tentativi; gli errori permanenti e gli esiti incerti bloccano i retry automatici. Per modifiche al programma seguire i collaudi di [AGENTS.md](AGENTS.md).

In una repository pubblica, `setup-apply` da Actions è bloccato per non pubblicare backup amministrativi. Eventuali migrazioni vanno eseguite in un ambiente riservato, con WIF e backup protetto. Prima di cambiare visibilità controllare anche cronologia, vecchi log e artifact: la pulizia del README non li modifica.

## Sviluppo

```bash
bash scripts/setup.sh
bash scripts/verify.sh
```

Il primo comando prepara la `.venv`; il secondo esegue tutti i controlli del progetto senza rete né invii. Il primo bootstrap richiede accesso alle dipendenze.

## Fonti di verità

- [AGENTS.md](AGENTS.md): regole per contribuire e collaudi prima del deployment.
- [CHANGELOG.md](CHANGELOG.md): modifiche funzionali.
- [pyproject.toml](pyproject.toml): versione, dipendenze ed entry point.
- [Workflow](.github/workflows/) e [contratto](config/github/environment-contract.json): configurazione effettiva.
- [releases/](releases/): fotografie storiche delle release; per il codice corrente valgono questo `README.md`, i workflow e il contratto.
