# Roadmap

Questo file contiene esclusivamente lavoro ancora aperto. Le funzionalità già rilasciate sono descritte in `CHANGELOG.md`; le procedure operative sono in `docs/`.

## 1. Provisioning esterno

- [ ] creare gli Environment GitHub `preproduction` e `production`;
- [ ] configurare Variables e Secrets con ambito minimo;
- [ ] creare progetto Google Cloud, service account e Workload Identity Federation;
- [ ] limitare il trust a repository, branch e workflow autorizzati;
- [ ] condividere `Operativo` in sola lettura e il foglio amministrativo in modifica;
- [ ] configurare una seconda identità umana di recupero.

## 2. Migrazione e collaudi Google

- [ ] creare una copia di sicurezza del foglio amministrativo reale;
- [ ] eseguire `migrate-admin` in anteprima e applicare la migrazione con backup;
- [ ] verificare che `AUTOMAZIONE_ATTIVA=false` e `INVII_REALI_ABILITATI=false`;
- [ ] completare il preflight reale;
- [ ] collaudare la scrittura sintetica del registro;
- [ ] eseguire un dry-run controllato su `Operativo`;
- [ ] verificare concorrenza, lock e revoca dei permessi.

## 3. SMTP e contenuti

- [ ] approvare mittente, Reply-To, oggetto, corpo, firma e logo;
- [ ] configurare i Secrets MDaemon nell'Environment corretto;
- [ ] eseguire il test SMTP esclusivamente sul destinatario override;
- [ ] collaudare errori ritentabili, permanenti ed esiti incerti;
- [ ] verificare il comportamento del registro dopo ogni classe di esito.

## 4. Go-live controllato

- [ ] eseguire un singolo invio reale autorizzato;
- [ ] eseguire un piccolo lotto controllato;
- [ ] verificare dashboard, anomalie e deduplicazione;
- [ ] autorizzare formalmente il go-live;
- [ ] attivare il workflow di produzione partendo dal modello revisionato;
- [ ] impostare `PRODUCTION_ENABLED=true` soltanto al termine dei collaudi;
- [ ] verificare la schedule giornaliera rispetto a UTC e ora legale;
- [ ] monitorare ravvicinatamente le prime esecuzioni.

## 5. Consegna operativa

- [ ] completare inventario, proprietari e contatti di recupero;
- [ ] provare le procedure di arresto ed emergenza;
- [ ] far eseguire il runbook a un responsabile non tecnico;
- [ ] completare il passaggio di consegne;
- [ ] disabilitare l'automazione di sviluppo dopo la consegna definitiva.
