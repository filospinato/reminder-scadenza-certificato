# Stato corrente

**Versione di pacchetto:** 0.13.3  
**Data:** 20 luglio 2026  
**Stato:** codice pre-produzione rafforzato e disattivato; produzione e schedule non attive

## Funziona già

- schema amministrativo v2 con `SCHEMA_VERSION`;
- migrazione con anteprima, conferma e backup;
- preflight su tab, intestazioni e CONFIG reale;
- lettura delle sole otto colonne necessarie di `Operativo`, incluse `Qualifica` e `Abilitazione`;
- interpretazione di `Fa attività quest'anno`: cella vuota = attivo, annotazione non affermativa = inattivo;
- esclusione esplicita di benemeriti, osservatori e fuori quadro dai reminder per il certificato medico;
- chiave di notifica stabile rispetto a `GIORNI_PREAVVISO`;
- registro senza nome, cognome o email;
- stati distinti per errore ritentabile, permanente e incerto;
- massimo tre tentativi automatici;
- diagnosi aggregata di righe bloccate ed esiti da revisionare;
- arresto che non inizializza SMTP;
- exit code non-zero per `ATTENZIONE` e `REVISIONE_RICHIESTA`;
- WIF/OIDC, Environment protetti e workflow manuale;
- modello produttivo non attivo.

## Regola attività

La colonna `Fa attività quest'anno` usa la convenzione del foglio reale: una cella vuota identifica chi fa attività. `No`, indipendentemente dalle maiuscole, e qualsiasi altra annotazione non affermativa identificano chi non fa attività. I valori affermativi espliciti già supportati, come `Sì`, `true`, `attivo` e `operativo`, restano compatibili.

## Regola categorie

Una riga non diventa candidata al reminder quando `Qualifica` o `Abilitazione` contiene `Benemerito`, `Osservatore` oppure `Fuori Quadro`, senza distinzione tra maiuscole e minuscole.

## Migrazione necessaria

Il foglio amministrativo precedente deve essere portato allo schema v2 prima dei collaudi. La migrazione lascia obbligatoriamente:

```text
AUTOMAZIONE_ATTIVA=false
INVII_REALI_ABILITATI=false
```

## Esclusione intenzionale

Il test SMTP non è stato trasformato in un test interamente sintetico, secondo la richiesta. Continua a usare il destinatario override e al massimo un messaggio.

## Prossimo passo

Dopo il merge della versione 0.13.3:

1. creare una copia di sicurezza del foglio reale;
2. migrare CONFIG e NOTIFICHE;
3. verificare nuovamente che entrambi gli interruttori siano `false`;
4. eseguire il preflight;
5. proseguire con i collaudi esterni soltanto quando WIF e Environment saranno pronti.
