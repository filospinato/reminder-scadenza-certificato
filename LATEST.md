# Stato corrente

**Versione di pacchetto:** 0.12.0  
**Data:** 19 luglio 2026  
**Stato:** codice pre-produzione semplificato e disattivato; risorse e collaudi esterni ancora mancanti

## Funziona già

- validazione e selezione dei record di `Operativo`;
- preflight in sola lettura su file, tab e intestazioni;
- inizializzazione sicura del foglio amministrativo;
- un solo comando installato: `reminder-certificati`;
- sottocomandi `init-admin`, `preflight`, `registry-check`, `dry-run`, `test-smtp` e `produzione`;
- un solo interruttore operativo: `AUTOMAZIONE_ATTIVA`;
- modalità determinata dal sottocomando, senza `MODALITA_TEST` in CONFIG;
- registro persistente con una sola lettura completa per esecuzione;
- anomalie persistenti deduplicate;
- corpo email liberamente modificabile con placeholder autorizzati;
- dashboard aggregata, SMTP MDaemon, WIF/OIDC e workflow manuale protetto;
- modello schedulato conservato come esempio non attivo, con una sola esecuzione giornaliera.

## Semplificazioni applicate

- rimossa la CLI storica;
- rimossi gli entry point separati per preflight e collaudo registro;
- eliminato il comando duplicato `check-headers`;
- sostituiti `SISTEMA_ATTIVO` e `KILL_SWITCH` con `AUTOMAZIONE_ATTIVA`;
- eliminato `MODALITA_TEST` dalla CONFIG;
- alleggerita la validazione dei metadati descrittivi della CONFIG;
- rimosso il vincolo testuale che imponeva al corpo di iniziare con “ricevi questa mail”;
- ridotta la schedule prevista da due esecuzioni a una al giorno.

## Barriere di sicurezza mantenute

- `Operativo` sempre in sola lettura;
- credenziali Google permanenti rifiutate a runtime;
- preflight senza lettura di righe operative;
- collaudo del registro protetto da flag e variabile dedicata;
- segreti SMTP disponibili soltanto nello step di invio;
- produzione subordinata a Environment, `PRODUCTION_ENABLED`, CONFIG coerente e consenso dello step;
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

## Prossimo passo

Creare lo Spreadsheet amministrativo vuoto, predisporre Google Cloud e l'Environment `preproduction`, quindi eseguire nell'ordine:

```text
reminder-certificati init-admin
reminder-certificati preflight
reminder-certificati registry-check
reminder-certificati dry-run
reminder-certificati test-smtp
```
