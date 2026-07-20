# Passaggio di consegne

Questo documento definisce ciò che un responsabile operativo deve conoscere prima di ricevere la gestione ordinaria del sistema.

## Responsabilità da assegnare

Prima del go-live devono essere identificati il responsabile del repository, il proprietario del foglio amministrativo, il referente Google Cloud, il referente MDaemon e un contatto di recupero. I dettagli reali restano fuori dal repository.

## Conoscenze minime

Il responsabile non tecnico deve saper:

1. impostare `INVIO_AUTOMATICO_ATTIVO` su `true` o `false`;
2. usare **Controlla senza inviare** nel workflow ordinario;
3. impostare `DESTINATARIO_OVERRIDE` ed eseguire **Invia email di prova**;
4. leggere dashboard, anomalie e riepilogo del registro;
5. distinguere un errore da riprovare da un esito che richiede verifica manuale;
6. consultare `docs/EMERGENCY.md` quando il sistema segnala un problema.

Le attività tecniche su identità cloud, permessi, configurazione GitHub e codice restano affidate a un referente tecnico.

## Inventario minimo

L'inventario di consegna deve indicare:

- repository e ramo predefinito;
- foglio `Operativo` e foglio amministrativo;
- progetto e identità Google usati dal sistema;
- Environment GitHub collegati;
- casella mittente e Reply-To;
- data dell'ultima revisione degli accessi.

## Collaudo del responsabile

Il nuovo responsabile deve completare senza assistenza tecnica:

- modifica sicura di `GIORNI_PREAVVISO`;
- impostazione del destinatario di prova;
- esecuzione del controllo senza invio;
- esecuzione di una prova SMTP controllata;
- lettura di dashboard e anomalie;
- arresto e riattivazione tramite `INVIO_AUTOMATICO_ATTIVO`;
- consultazione della procedura corretta per un esito incerto.

Il limite per esecuzione non è più una decisione dell'operatore. Il collaudo non include invii reali ad arbitri.
