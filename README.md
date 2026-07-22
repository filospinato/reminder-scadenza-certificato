# Reminder scadenza certificato

Sistema che legge in sola lettura il foglio `Operativo`, individua gli arbitri con certificato medico prossimo alla scadenza e invia promemoria individuali tramite SMTP MDaemon, mantenendo un registro persistente anti-duplicazione.

## Obiettivo

Il progetto automatizza un’attività amministrativa ripetitiva senza trasformare il foglio operativo in un database scrivibile e senza affidare la sicurezza a un singolo interruttore tecnico.

Il sistema deve:

- elaborare soltanto le persone attive e soggette all’obbligo del certificato;
- usare nome, cognome, email e scadenza provenienti dalla stessa riga;
- inviare un solo messaggio per destinatario;
- impedire duplicazioni anche dopo errori o interruzioni;
- produrre dashboard e anomalie aggregate senza esporre dati personali nei log;
- consentire controllo, prova SMTP, rollout e arresto con procedure separate.

## Architettura

```text
Google Sheets Operativo (read-only)
              |
              v
      lettura e validazione
              |
              v
      selezione candidati
              |
              +--------------------+
              |                    |
              v                    v
  composizione testo/HTML     anomalie aggregate
              |
              v
   registro amministrativo
   SENDING prima di SMTP
              |
              v
        MDaemon SMTP
              |
              v
  SENT / errore / revisione
```

Componenti principali:

- package Python installabile con entry point `reminder-certificati`;
- adapter Google Sheets autenticato tramite WIF/OIDC;
- foglio amministrativo separato con CONFIG, registro, dashboard e anomalie;
- compositore MIME testo/HTML con firma istituzionale versionata;
- trasporto SMTP MDaemon;
- GitHub Actions per controllo, manutenzione e invii reali controllati.

## Modello di sicurezza

- `Operativo` è sempre in sola lettura.
- Google usa credenziali temporanee WIF/OIDC; le chiavi permanenti sono vietate.
- Il controllo senza invio non inizializza SMTP e non crea notifiche operative.
- Il test SMTP sostituisce il destinatario con un override e invia al massimo un messaggio.
- Gli invii reali richiedono autorizzazione esplicita e l’interruttore esterno `INVIO_AUTOMATICO_ATTIVO=true`.
- La prenotazione `SENDING` viene persistita prima del contatto SMTP.
- Gli esiti incerti non vengono ritentati automaticamente.
- Tutti i workflow che accedono al registro condividono un lock di concorrenza.

## Stato semantico

| Area | Stato |
|---|---|
| Lettura e validazione di `Operativo` | disponibile |
| Foglio amministrativo e migrazioni | disponibili |
| Registro anti-duplicazione | disponibile |
| Composizione testo/HTML e firma istituzionale | disponibile |
| Integrazione Google tramite WIF/OIDC | disponibile |
| Controllo senza invio | validato |
| Prova SMTP verso override | validata |
| Workflow produttivo manuale | disponibile |
| Schedule automatica | non attiva |
| Rollout reale continuativo | richiede autorizzazione e collaudi finali |
| Consegna a responsabile non tecnico | da completare |

I valori esatti correnti sono in [`CURRENT_STATE.json`](CURRENT_STATE.json). Le evidenze della release corrente sono nel relativo file `VALIDATION.md` sotto `releases/`.

## Comandi pubblici

```bash
reminder-certificati setup-admin --spreadsheet-id ID
reminder-certificati setup-admin --spreadsheet-id ID --apply
reminder-certificati check
reminder-certificati registry-check
reminder-certificati test-smtp
reminder-certificati produzione
reminder-certificati produzione --max-sends 1
```

`setup-admin` mostra per default un’anteprima. L’opzione `--apply` inizializza o migra il foglio amministrativo con backup quando necessario.

`check` unisce preflight, controllo dei candidati e revisione del registro senza invio.

`test-smtp` esegue una sola prova controllata al destinatario override.

`produzione` è riservato agli invii reali autorizzati.

## Installazione per lo sviluppo

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev,google]"
ruff check .
python -m compileall -q src
python -m pip check
pytest
```

## Fonti di verità

- [`README.md`](README.md): overview, architettura e stato semantico;
- [`AGENTS.md`](AGENTS.md): unica fonte delle regole operative per le modifiche;
- [`CURRENT_STATE.json`](CURRENT_STATE.json): stato esatto corrente;
- [`CHANGELOG.md`](CHANGELOG.md): storia semantica delle release;
- [`config/github/environment-contract.json`](config/github/environment-contract.json): contratto macchina di Variables e Secrets;
- [`releases/`](releases/): guide e riferimenti immutabili delle singole release;
- GitHub Issues e milestone: lavoro ancora aperto.

Non devono essere introdotte roadmap, file `LATEST`, handoff temporanei o altre fonti concorrenti.

## Documentazione della release corrente

La directory indicata da `CURRENT_STATE.json` contiene:

- guida operativa;
- deployment e rollout;
- riferimento tecnico;
- validazione della release.

## Contribuire

Prima di modificare il repository leggere [`AGENTS.md`](AGENTS.md). Le modifiche passano sempre da branch dedicato, test completi e pull request con revisione del diff pubblicato. Nessuna modifica documentale o applicativa abilita automaticamente risorse live o invii reali.
