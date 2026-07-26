"""Orchestrazione completa, aggregata e sicura del ciclo reminder."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date, datetime, timezone
from enum import StrEnum
from typing import Callable, Protocol

from .candidate_selection import seleziona_candidati
from .data_sources import SorgenteDati, leggi_e_valida
from .email_templates import ErroreTemplate, componi_email
from .models import CandidatoNotifica
from .monitoring import (
    AnomaliaRuntime,
    ArchivioAnomalie,
    ArchivioDashboard,
    MetricheEsecuzione,
    SeveritaAnomalia,
)
from .persistent_registry import ErroreRegistroPersistente
from .runtime_config import ConfigurazioneRuntime
from .smtp_transport import (
    ErroreSmtpPermanente,
    ErroreSmtpRetryable,
    EsitoSmtpIncerto,
    TrasportoEmail,
)
from .validation import MappaturaColonne, PoliticaStato


class ModalitaEsecuzione(StrEnum):
    DRY_RUN = "DRY_RUN"
    TEST_SMTP = "TEST_SMTP"
    PRODUZIONE = "PRODUZIONE"


class ErroreOrchestrazione(RuntimeError):
    """L'esecuzione non può proseguire senza rischi."""


@dataclass(frozen=True, slots=True)
class EsitoEsecuzione:
    modalita: ModalitaEsecuzione
    stato: str
    righe_lette: int
    righe_valide: int
    anomalie: int
    candidati: int
    notifiche_gia_presenti: int
    messaggi_composti: int
    invii_tentati: int
    invii_riusciti: int
    invii_falliti: int
    esiti_incerti: int


class RegistroNotifichePersistente(Protocol):
    def puo_prenotare(self, notification_id: str) -> bool: ...
    def prenota(self, candidato: CandidatoNotifica, *, ora: datetime | None = None): ...
    def segna_inviata(
        self,
        candidato: CandidatoNotifica,
        *,
        message_id: str,
        ora: datetime | None = None,
    ): ...
    def segna_errore_retryable(
        self, candidato: CandidatoNotifica, *, errore: str, ora: datetime | None = None
    ): ...
    def segna_errore_permanente(
        self, candidato: CandidatoNotifica, *, errore: str, ora: datetime | None = None
    ): ...
    def segna_esito_incerto(
        self, candidato: CandidatoNotifica, *, errore: str, ora: datetime | None = None
    ): ...


@dataclass(frozen=True, slots=True)
class OrchestratoreReminder:
    sorgente: SorgenteDati
    configurazione: ConfigurazioneRuntime
    dashboard: ArchivioDashboard
    anomalie: ArchivioAnomalie
    versione_app: str
    registro: RegistroNotifichePersistente | None = None
    trasporto_email: TrasportoEmail | None = None
    mappatura: MappaturaColonne = MappaturaColonne()
    politica_stato: PoliticaStato = PoliticaStato()

    def esegui(
        self,
        *,
        oggi: date,
        modalita: ModalitaEsecuzione = ModalitaEsecuzione.DRY_RUN,
        consenso_esterno_invio: bool = False,
        ora: datetime | None = None,
    ) -> EsitoEsecuzione:
        istante = _utc(ora or datetime.now(timezone.utc))
        if not self.versione_app.strip():
            raise ErroreOrchestrazione("versione_app mancante")

        if (
            modalita is ModalitaEsecuzione.PRODUZIONE
            and not self.configurazione.automazione_attiva
        ):
            esito = _esito_vuoto(modalita, "DISATTIVATO")
            self._aggiorna_dashboard(esito, istante, codice_errore="")
            return esito

        self._valida_modalita(modalita, consenso_esterno_invio)
        if modalita is not ModalitaEsecuzione.DRY_RUN and (
            self.registro is None or self.trasporto_email is None
        ):
            raise ErroreOrchestrazione(
                "registro e trasporto email obbligatori fuori dal dry-run"
            )

        try:
            validazione = leggi_e_valida(
                self.sorgente,
                mappatura=self.mappatura,
                politica_stato=self.politica_stato,
            )
        except Exception as exc:
            self._registra_anomalia(
                severita=SeveritaAnomalia.CRITICAL,
                origine="SORGENTE",
                codice="LETTURA_FATALE",
                messaggio=f"lettura o schema non disponibile: {type(exc).__name__}",
                istante=istante,
            )
            esito = _esito_vuoto(modalita, "ERRORE", anomalie=1)
            self._aggiorna_dashboard(esito, istante, codice_errore="LETTURA_FATALE")
            raise ErroreOrchestrazione("lettura della sorgente non riuscita") from exc

        selezione = seleziona_candidati(
            validazione.arbitri,
            oggi=oggi,
            giorni_preavviso=self.configurazione.giorni_preavviso,
            mappatura=self.mappatura,
        )
        anomalie_dati = (*validazione.anomalie, *selezione.anomalie)
        for anomalia in anomalie_dati:
            self._registra_anomalia(
                severita=SeveritaAnomalia.WARNING,
                origine="OPERATIVO",
                codice=str(anomalia.codice),
                messaggio=f"anomalia dati nel campo {anomalia.campo}",
                istante=istante,
                riga_sorgente=anomalia.numero_riga,
                campo=anomalia.campo,
            )

        candidati = selezione.candidati
        limite = (
            1
            if modalita is ModalitaEsecuzione.TEST_SMTP
            else self.configurazione.limite_invii_per_esecuzione
        )

        gia_presenti = 0
        selezionati = 0
        composti = 0
        tentati = 0
        riusciti = 0
        falliti = 0
        incerti = 0

        for candidato_originale in candidati:
            candidato = candidato_originale
            if modalita is ModalitaEsecuzione.TEST_SMTP:
                override = self.configurazione.destinatario_override
                if override is None:
                    raise ErroreOrchestrazione(
                        "destinatario override mancante in modalità test"
                    )
                candidato = _candidato_test(candidato_originale, override)

            if self.registro is not None:
                try:
                    prenotabile = self.registro.puo_prenotare(candidato.notification_id)
                except Exception as exc:
                    self._registra_anomalia(
                        severita=SeveritaAnomalia.CRITICAL,
                        origine="REGISTRO",
                        codice="REGISTRO_NON_LEGGIBILE",
                        messaggio=type(exc).__name__,
                        istante=istante,
                    )
                    raise ErroreOrchestrazione(
                        "verifica del registro non riuscita"
                    ) from exc
                if not prenotabile:
                    gia_presenti += 1
                    continue

            if selezionati >= limite:
                break
            selezionati += 1

            try:
                messaggio = componi_email(candidato, self.configurazione.email)
                composti += 1
            except ErroreTemplate as exc:
                falliti += 1
                self._registra_anomalia(
                    severita=SeveritaAnomalia.ERROR,
                    origine="TEMPLATE",
                    codice="MESSAGGIO_NON_COMPONIBILE",
                    messaggio=type(exc).__name__,
                    istante=istante,
                )
                continue

            if modalita is ModalitaEsecuzione.DRY_RUN:
                continue

            assert self.registro is not None
            assert self.trasporto_email is not None
            try:
                self.registro.prenota(candidato, ora=istante)
                tentati += 1
                esito_smtp = self.trasporto_email.invia(messaggio)
                self.registro.segna_inviata(
                    candidato,
                    message_id=esito_smtp.message_id,
                    ora=istante,
                )
                riusciti += 1
            except ErroreSmtpRetryable as exc:
                nome_errore = type(exc).__name__
                if self._aggiorna_registro_dopo_smtp(
                    lambda: self.registro.segna_errore_retryable(
                        candidato,
                        errore=nome_errore,
                        ora=istante,
                    ),
                    errore_smtp=exc,
                    istante=istante,
                ):
                    falliti += 1
                    self._registra_anomalia(
                        severita=SeveritaAnomalia.ERROR,
                        origine="SMTP",
                        codice="SMTP_RETRYABLE",
                        messaggio=nome_errore,
                        istante=istante,
                    )
                else:
                    incerti += 1
            except ErroreSmtpPermanente as exc:
                nome_errore = type(exc).__name__
                if self._aggiorna_registro_dopo_smtp(
                    lambda: self.registro.segna_errore_permanente(
                        candidato,
                        errore=nome_errore,
                        ora=istante,
                    ),
                    errore_smtp=exc,
                    istante=istante,
                ):
                    falliti += 1
                    self._registra_anomalia(
                        severita=SeveritaAnomalia.ERROR,
                        origine="SMTP",
                        codice="SMTP_PERMANENTE",
                        messaggio=nome_errore,
                        istante=istante,
                    )
                else:
                    incerti += 1
            except EsitoSmtpIncerto as exc:
                incerti += 1
                nome_errore = type(exc).__name__
                if self._aggiorna_registro_dopo_smtp(
                    lambda: self.registro.segna_esito_incerto(
                        candidato,
                        errore=nome_errore,
                        ora=istante,
                    ),
                    errore_smtp=exc,
                    istante=istante,
                ):
                    self._registra_anomalia(
                        severita=SeveritaAnomalia.CRITICAL,
                        origine="SMTP",
                        codice="SMTP_ESITO_INCERTO",
                        messaggio="la consegna richiede revisione umana",
                        istante=istante,
                    )
            except ErroreRegistroPersistente as exc:
                incerti += 1
                self._registra_anomalia(
                    severita=SeveritaAnomalia.CRITICAL,
                    origine="REGISTRO",
                    codice="REGISTRO_INCOERENTE",
                    messaggio=type(exc).__name__,
                    istante=istante,
                )
            except Exception as exc:
                incerti += 1
                try:
                    self.registro.segna_esito_incerto(
                        candidato,
                        errore=type(exc).__name__,
                        ora=istante,
                    )
                except Exception as errore_registro:
                    self._registra_anomalia(
                        severita=SeveritaAnomalia.CRITICAL,
                        origine="REGISTRO",
                        codice="REGISTRO_INCOERENTE",
                        messaggio=(
                            "aggiornamento dopo "
                            f"{type(exc).__name__} non riuscito: "
                            f"{type(errore_registro).__name__}"
                        ),
                        istante=istante,
                    )
                self._registra_anomalia(
                    severita=SeveritaAnomalia.CRITICAL,
                    origine="SMTP",
                    codice="ERRORE_NON_CLASSIFICATO",
                    messaggio=type(exc).__name__,
                    istante=istante,
                )

        test_non_eseguito = (
            modalita is ModalitaEsecuzione.TEST_SMTP
            and tentati == 0
            and not falliti
            and not incerti
        )
        if test_non_eseguito:
            self._registra_anomalia(
                severita=SeveritaAnomalia.WARNING,
                origine="SMTP",
                codice="TEST_SMTP_NON_ESEGUITO",
                messaggio="nessun candidato prenotabile per il test SMTP",
                istante=istante,
            )

        stato = "DRY_RUN_OK" if modalita is ModalitaEsecuzione.DRY_RUN else "OK"
        if incerti:
            stato = "REVISIONE_RICHIESTA"
        elif falliti or anomalie_dati or test_non_eseguito:
            stato = "ATTENZIONE"

        esito = EsitoEsecuzione(
            modalita=modalita,
            stato=stato,
            righe_lette=validazione.righe_totali,
            righe_valide=len(validazione.arbitri),
            anomalie=(len(anomalie_dati) + falliti + incerti + int(test_non_eseguito)),
            candidati=len(candidati),
            notifiche_gia_presenti=gia_presenti,
            messaggi_composti=composti,
            invii_tentati=tentati,
            invii_riusciti=riusciti,
            invii_falliti=falliti,
            esiti_incerti=incerti,
        )
        self._aggiorna_dashboard(esito, istante, codice_errore="")
        return esito

    def _aggiorna_registro_dopo_smtp(
        self,
        azione: Callable[[], object],
        *,
        errore_smtp: Exception,
        istante: datetime,
    ) -> bool:
        try:
            azione()
            return True
        except Exception as exc:
            self._registra_anomalia(
                severita=SeveritaAnomalia.CRITICAL,
                origine="REGISTRO",
                codice="REGISTRO_INCOERENTE",
                messaggio=(
                    "aggiornamento dopo "
                    f"{type(errore_smtp).__name__} non riuscito: {type(exc).__name__}"
                ),
                istante=istante,
            )
            return False

    def _valida_modalita(
        self,
        modalita: ModalitaEsecuzione,
        consenso_esterno: bool,
    ) -> None:
        if modalita is ModalitaEsecuzione.DRY_RUN:
            return
        if not consenso_esterno:
            raise ErroreOrchestrazione(
                "il comando deve autorizzare esplicitamente la modalità di invio"
            )
        if modalita is ModalitaEsecuzione.TEST_SMTP:
            if self.configurazione.destinatario_override is None:
                raise ErroreOrchestrazione("DESTINATARIO_OVERRIDE mancante")
            return
        if not self.configurazione.invio_reale_consentito(
            consenso_esterno=consenso_esterno
        ):
            raise ErroreOrchestrazione(
                "INVIO_AUTOMATICO_ATTIVO deve essere true per la produzione"
            )

    def _registra_anomalia(
        self,
        *,
        severita: SeveritaAnomalia,
        origine: str,
        codice: str,
        messaggio: str,
        istante: datetime,
        riga_sorgente: int | None = None,
        campo: str | None = None,
    ) -> None:
        self.anomalie.registra(
            AnomaliaRuntime.crea(
                severita=severita,
                origine=origine,
                codice=codice,
                messaggio=messaggio,
                versione_app=self.versione_app,
                riga_sorgente=riga_sorgente,
                campo=campo,
                rilevata_il=istante,
            )
        )

    def _aggiorna_dashboard(
        self,
        esito: EsitoEsecuzione,
        istante: datetime,
        *,
        codice_errore: str,
    ) -> None:
        self.dashboard.aggiorna(
            MetricheEsecuzione(
                stato_sistema=esito.stato,
                ultima_esecuzione=istante,
                heartbeat=istante,
                righe_lette=esito.righe_lette,
                righe_valide=esito.righe_valide,
                candidati=esito.candidati,
                notifiche_gia_presenti=esito.notifiche_gia_presenti,
                invii_tentati=esito.invii_tentati,
                invii_riusciti=esito.invii_riusciti,
                invii_falliti=esito.invii_falliti,
                esiti_incerti=esito.esiti_incerti,
                anomalie=esito.anomalie,
                automazione_attiva=self.configurazione.automazione_attiva,
                versione_app=self.versione_app,
                codice_errore=codice_errore,
            )
        )


def _esito_vuoto(
    modalita: ModalitaEsecuzione,
    stato: str,
    *,
    anomalie: int = 0,
) -> EsitoEsecuzione:
    return EsitoEsecuzione(
        modalita=modalita,
        stato=stato,
        righe_lette=0,
        righe_valide=0,
        anomalie=anomalie,
        candidati=0,
        notifiche_gia_presenti=0,
        messaggi_composti=0,
        invii_tentati=0,
        invii_riusciti=0,
        invii_falliti=0,
        esiti_incerti=0,
    )


def _candidato_test(
    candidato: CandidatoNotifica,
    destinatario_override: str,
) -> CandidatoNotifica:
    tipo = f"TEST_{candidato.tipo}"
    arbitro_test = replace(
        candidato.arbitro,
        email=destinatario_override.strip(),
    )
    return replace(
        candidato,
        arbitro=arbitro_test,
        tipo=tipo,
        notification_id="|".join(
            (
                candidato.arbitro.id_arbitro.strip(),
                candidato.arbitro.scadenza_certificato.isoformat(),
                tipo,
            )
        ),
    )


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("ora deve includere il fuso orario")
    return value.astimezone(timezone.utc)
