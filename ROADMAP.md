# Roadmap

Questo file contiene esclusivamente lavoro ancora aperto. Le funzionalità già rilasciate sono descritte in `CHANGELOG.md`; le procedure operative sono in `docs/`.

## 1. Provisioning esterno

- [ ] creare e proteggere l'Environment GitHub `production`;
- [ ] spostare Variables e futuri Secrets nello scope minimo necessario;
- [ ] limitare il trust a repository, branch e workflow autorizzati;
- [ ] configurare una seconda identità umana di recupero.

## 2. Aggiornamento e collaudi Google

- [ ] creare una copia di sicurezza del foglio amministrativo reale;
- [ ] collaudare la scrittura sintetica del registro;
- [ ] verificare concorrenza, lock e revoca dei permessi.

## 3. SMTP e contenuti

- [ ] approvare mittente, Reply-To, oggetto, corpo, firma e logo;
- [ ] configurare i Secrets MDaemon nell'Environment corretto;
- [ ] eseguire il test SMTP sul `DESTINATARIO_OVERRIDE` usando un candidato reale;
- [ ] verificare se MDaemon consente di eliminare in futuro il supporto SMTP `PLAIN`;
- [ ] collaudare errori ritentabili, permanenti ed esiti incerti;
- [ ] verificare il comportamento del registro dopo ogni classe di esito.

## 4. Go-live controllato

- [ ] eseguire un singolo invio reale autorizzato;
- [ ] eseguire un piccolo lotto controllato;
- [ ] verificare dashboard, anomalie e deduplicazione;
- [ ] autorizzare formalmente il go-live;
- [ ] aggiungere una sola schedule giornaliera al modello revisionato;
- [ ] spostare il workflow produttivo in `.github/workflows`;
- [ ] impostare `INVIO_AUTOMATICO_ATTIVO=true` soltanto al termine dei collaudi;
- [ ] verificare la schedule rispetto a UTC e ora legale;
- [ ] monitorare ravvicinatamente le prime esecuzioni.

## 5. Consegna operativa

- [ ] completare inventario, proprietari e contatti di recupero;
- [ ] provare le procedure di arresto ed emergenza;
- [ ] far eseguire i due workflow manuali a un responsabile non tecnico;
- [ ] completare il passaggio di consegne;
- [ ] disabilitare l'automazione di sviluppo dopo la consegna definitiva.
