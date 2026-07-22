# Validazione — release 0.14.18

Questo documento registra la fotografia delle verifiche associate alla release 0.14.18. Non è uno stato corrente e non deve essere aggiornato per release successive.

## Verificato

- suite CI eseguita sulle versioni Python supportate dal workflow;
- installazione degli extra `dev` e `google`;
- Ruff, compilazione del package e controllo delle dipendenze;
- workflow ordinario e workflow di manutenzione disponibili;
- autenticazione Google tramite WIF/OIDC senza chiavi permanenti;
- `setup-preview` eseguito sul foglio amministrativo;
- `setup-apply` completato con backup quando necessario;
- quattro tab amministrative presenti e visibili;
- service account in sola lettura su `Operativo` e in modifica sul foglio amministrativo;
- `INVIO_AUTOMATICO_ATTIVO=false` verificato dopo il setup;
- `check` completato senza tentativi SMTP e senza scritture operative;
- collaudo sintetico del registro completato;
- configurazione SMTP STARTTLS verificata sulla porta approvata;
- un singolo test SMTP inviato al destinatario override;
- ricezione e resa HTML del messaggio verificate nel client di collaudo;
- notifica di test registrata in stato `SENT`, con un tentativo e senza errore;
- workflow produttivo pubblicato come dispatch manuale, limitato a `main` e privo di schedule;
- unico Environment `preproduction` mantenuto per test e produzione sulle stesse risorse.

## Non ancora verificato per il funzionamento continuativo

- trust WIF limitata anche al workflow o Environment definitivo;
- seconda identità umana di recupero e procedura di revoca completa;
- errori SMTP ritentabili, permanenti e incerti sul sistema reale;
- comportamento del registro dopo ogni classe di esito reale;
- singolo invio reale a un arbitro;
- lotto controllato da 5 e successivo limite ordinario;
- schedule giornaliera e comportamento rispetto a UTC e ora legale;
- monitoraggio delle prime esecuzioni programmate;
- prova completa delle procedure di arresto ed emergenza;
- consegna e collaudo autonomo da parte di un responsabile non tecnico.

## Condizione di go-live

La presenza del workflow produttivo non costituisce autorizzazione al go-live. Gli invii reali richiedono autorizzazione esplicita, `INVIO_AUTOMATICO_ATTIVO=true`, verifica del lotto precedente e monitoraggio degli esiti.

## Tracciabilità

Le evidenze dettagliate dei run, gli URL dei workflow e le discussioni di revisione restano nella cronologia GitHub delle pull request e delle Actions. Non vengono duplicate in questo documento.
