# Stato corrente

**Versione di pacchetto:** 0.11.5  
**Data:** 18 luglio 2026  
**Stato:** codice pre-produzione semplificato e disattivato; risorse e collaudi esterni ancora mancanti

## Funziona già

- validazione e selezione lineari dei record di `Operativo`;
- una sola fonte di verità per le sei colonne effettivamente utilizzate;
- preflight in sola lettura che non dipende dall'ordine visuale delle tab o da colonne estranee al reminder;
- inizializzazione sicura del foglio amministrativo e verifica runtime limitata a metadati e intestazioni;
- `CONFIG` ridotta ai campi realmente usati;
- dry-run eseguibile senza destinatario override o configurazione SMTP;
- registro persistente con una sola lettura completa per esecuzione e indice locale aggiornato dopo le scritture;
- stati `SENDING`, `SENT`, `FAILED_RETRYABLE` e `UNKNOWN_REVIEW_REQUIRED` gestiti da una sola macchina a stati;
- anomalie persistenti deduplicate per ID aperto;
- test SMTP limitato a un messaggio all'override;
- dashboard aggregata, SMTP MDaemon, WIF/OIDC e workflow manuale protetto;
- modello schedulato conservato come esempio non attivo;
- test automatici concentrati sulle proprietà di sicurezza e sul comportamento, non sulla forma testuale dei file.

## Semplificazioni applicate

- rimossa la CLI storica che elaborava e stampava record completi; il vecchio comando mostra soltanto un avviso;
- eliminata la versione duplicata da `__init__.py`;
- eliminati `SALUTO_EMAIL` e `CONTATTO_SUPPORTO` dalla CONFIG perché non influenzavano il runtime;
- reso modificabile `INVII_REALI_ABILITATI`, mantenendo le altre barriere di go-live;
- rimosso il modulo di salute non collegato a CLI o workflow;
- rimossa la macchina a stati in memoria duplicata;
- eliminati gli acknowledgement produttivi statici ridondanti;
- eliminato l'upgrade dinamico di pip dai workflow.

## Barriere di sicurezza

- nessuna credenziale, email reale o PII nel repository;
- `Operativo` sempre in sola lettura;
- credenziali Google permanenti rifiutate a runtime;
- preflight e check delle intestazioni senza lettura di righe operative;
- collaudo del registro protetto da flag e variabile dedicata;
- segreti SMTP disponibili soltanto nello step di invio;
- produzione subordinata a Environment, `PRODUCTION_ENABLED`, CONFIG coerente, kill switch disattivato e consenso esplicito dello step;
- esiti SMTP incerti non ritentati automaticamente;
- workflow schedulato assente da `.github/workflows`.

## Da creare o valorizzare esternamente

- progetto Google Cloud, API, service account, pool e provider WIF;
- GitHub Environments, Variables e binding IAM;
- Spreadsheet amministrativo vuoto creato dall'account umano;
- condivisione diretta dei due Spreadsheet;
- parametri e credenziali MDaemon;
- mittente, Reply-To, firma ufficiale e logo approvato;
- seconda identità umana CIA di recupero.

## Collaudi ancora necessari

- inizializzazione reale del file amministrativo vuoto;
- preflight Google reale;
- collaudo sintetico di `NOTIFICHE`;
- dry-run aggregato su `Operativo`;
- test SMTP esclusivamente all'override;
- errori retryable, permanenti e incerti;
- concorrenza reale tra workflow e revoca dei permessi;
- prova dei runbook con un responsabile non tecnico.

## Prossimo passo

Creare con l'account umano lo Spreadsheet amministrativo vuoto, predisporre Google Cloud e l'Environment `preproduction`, quindi eseguire `init-admin`, preflight, collaudo sintetico, dry-run e test SMTP all'override. Nessun invio reale agli arbitri è necessario durante questi collaudi.
