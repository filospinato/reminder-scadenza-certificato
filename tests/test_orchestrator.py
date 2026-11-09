from dataclasses import replace
from datetime import date, datetime, timedelta, timezone

from reminder_certificati.admin_store import ArchivioNotificheMemoria
from reminder_certificati.data_sources import SorgenteMemoria
from reminder_certificati.email_templates import ConfigurazioneEmail
from reminder_certificati.models import Arbitro, CandidatoNotifica
from reminder_certificati.monitoring import AnomalieMemoria, DashboardMemoria
from reminder_certificati.orchestrator import ModalitaEsecuzione, OrchestratoreReminder
from reminder_certificati.persistent_registry import RegistroPersistente
from reminder_certificati.registry import StatoNotifica
from reminder_certificati.rules import TIPO_NOTIFICA_SCADENZA
from reminder_certificati.runtime_config import (
    LIMITE_INVII_PER_ESECUZIONE,
    ConfigurazioneRuntime,
)
from reminder_certificati.smtp_transport import (
    ErroreSmtpPermanente,
    ErroreSmtpRetryable,
    TrasportoEmailMemoria,
)

VERSIONE = "0.14.0"
_INTESTAZIONI = [
    "id_arbitro",
    "nome",
    "cognome",
    "email",
    "scadenza_certificato",
    "attivo",
]


def _sorgente(*righe: list[str]) -> SorgenteMemoria:
    dati = list(righe) or [
        ["A-1", "Anna Maria", "Verdi", "anna@example.invalid", "2026-08-01", "true"]
    ]
    return SorgenteMemoria([_INTESTAZIONI, *dati])


def _config(
    *,
    attiva: bool = True,
    limite: int = LIMITE_INVII_PER_ESECUZIONE,
    override: str | None = "test@example.invalid",
) -> ConfigurazioneRuntime:
    return ConfigurazioneRuntime(
        automazione_attiva=attiva,
        giorni_preavviso=30,
        limite_invii_per_esecuzione=limite,
        destinatario_override=override,
        email=ConfigurazioneEmail(),
    )


def _candidato(
    id_arbitro: str,
    nome: str,
    email: str,
    scadenza: date,
) -> CandidatoNotifica:
    arbitro = Arbitro(
        id_arbitro=id_arbitro,
        nome=nome,
        cognome="Verdi",
        email=email,
        scadenza_certificato=scadenza,
    )
    tipo = TIPO_NOTIFICA_SCADENZA
    return CandidatoNotifica(
        arbitro=arbitro,
        tipo=tipo,
        giorni_residui=15,
        notification_id=f"{id_arbitro}|{scadenza.isoformat()}|{tipo}",
    )


def test_produzione_spenta_blocca_prima_della_lettura() -> None:
    dashboard = DashboardMemoria()
    orchestratore = OrchestratoreReminder(
        sorgente=_sorgente(),
        configurazione=_config(attiva=False),
        dashboard=dashboard,
        anomalie=AnomalieMemoria(),
        versione_app=VERSIONE,
    )
    esito = orchestratore.esegui(
        oggi=date(2026, 7, 17),
        modalita=ModalitaEsecuzione.PRODUZIONE,
    )

    assert esito.stato == "DISATTIVATO"
    assert esito.righe_lette == 0
    assert dashboard.ultima is not None
    assert dashboard.ultima.automazione_attiva is False


def test_dry_run_funziona_anche_con_invii_automatici_spenti() -> None:
    archivio = ArchivioNotificheMemoria()
    orchestratore = OrchestratoreReminder(
        sorgente=_sorgente(),
        configurazione=_config(attiva=False, override=None),
        dashboard=DashboardMemoria(),
        anomalie=AnomalieMemoria(),
        versione_app=VERSIONE,
        registro=RegistroPersistente(archivio, versione_app=VERSIONE),
    )
    esito = orchestratore.esegui(
        oggi=date(2026, 7, 17),
        modalita=ModalitaEsecuzione.DRY_RUN,
    )

    assert esito.stato == "DRY_RUN_OK"
    assert esito.candidati == 1
    assert esito.messaggi_composti == 1
    assert esito.invii_tentati == 0
    assert archivio.snapshot() == ()


def test_dry_run_salta_registrate_e_applica_limite_dopo_deduplicazione() -> None:
    archivio = ArchivioNotificheMemoria()
    registro = RegistroPersistente(archivio, versione_app=VERSIONE)
    ora = datetime(2026, 7, 17, 10, tzinfo=timezone.utc)
    primo = _candidato("A-1", "Anna", "anna@example.invalid", date(2026, 8, 1))
    registro.prenota(primo, ora=ora)
    registro.segna_inviata(
        primo,
        message_id="<sent@example.invalid>",
        ora=ora + timedelta(seconds=1),
    )
    orchestratore = OrchestratoreReminder(
        sorgente=_sorgente(
            ["A-1", "Anna", "Verdi", "anna@example.invalid", "2026-08-01", "true"],
            ["A-2", "Luca", "Verdi", "luca@example.invalid", "2026-08-02", "true"],
        ),
        configurazione=_config(limite=1),
        dashboard=DashboardMemoria(),
        anomalie=AnomalieMemoria(),
        versione_app=VERSIONE,
        registro=registro,
    )
    esito = orchestratore.esegui(
        oggi=date(2026, 7, 17),
        modalita=ModalitaEsecuzione.DRY_RUN,
    )

    assert esito.candidati == 2
    assert esito.notifiche_gia_presenti == 1
    assert esito.messaggi_composti == 1
    assert len(archivio.snapshot()) == 1


def test_test_smtp_invia_solo_all_override_e_lo_registra_anche_se_spento() -> None:
    archivio = ArchivioNotificheMemoria()
    smtp = TrasportoEmailMemoria()
    orchestratore = OrchestratoreReminder(
        sorgente=_sorgente(),
        configurazione=_config(attiva=False),
        dashboard=DashboardMemoria(),
        anomalie=AnomalieMemoria(),
        versione_app=VERSIONE,
        registro=RegistroPersistente(archivio, versione_app=VERSIONE),
        trasporto_email=smtp,
    )
    esito = orchestratore.esegui(
        oggi=date(2026, 7, 17),
        modalita=ModalitaEsecuzione.TEST_SMTP,
        consenso_esterno_invio=True,
        ora=datetime(2026, 7, 17, 10, tzinfo=timezone.utc),
    )

    assert esito.invii_riusciti == 1
    assert smtp.inviati[0].destinatario == "test@example.invalid"
    righe = archivio.snapshot()
    assert len(righe) == 1
    assert righe[0].tipo == f"TEST_{TIPO_NOTIFICA_SCADENZA}"
    assert righe[0].stato is StatoNotifica.SENT
    assert righe[0].id_arbitro == "A-1"


def test_test_smtp_invia_al_massimo_un_messaggio() -> None:
    smtp = TrasportoEmailMemoria()
    orchestratore = OrchestratoreReminder(
        sorgente=_sorgente(
            ["A-1", "Anna", "Verdi", "anna@example.invalid", "2026-08-01", "true"],
            ["A-2", "Luca", "Verdi", "luca@example.invalid", "2026-08-02", "true"],
        ),
        configurazione=_config(),
        dashboard=DashboardMemoria(),
        anomalie=AnomalieMemoria(),
        versione_app=VERSIONE,
        registro=RegistroPersistente(ArchivioNotificheMemoria(), versione_app=VERSIONE),
        trasporto_email=smtp,
    )
    esito = orchestratore.esegui(
        oggi=date(2026, 7, 17),
        modalita=ModalitaEsecuzione.TEST_SMTP,
        consenso_esterno_invio=True,
        ora=datetime(2026, 7, 17, 10, tzinfo=timezone.utc),
    )

    assert esito.candidati == 2
    assert esito.invii_tentati == 1
    assert len(smtp.inviati) == 1


def test_seconda_esecuzione_test_non_duplica() -> None:
    archivio = ArchivioNotificheMemoria()
    registro = RegistroPersistente(archivio, versione_app=VERSIONE)
    smtp = TrasportoEmailMemoria()
    orchestratore = OrchestratoreReminder(
        sorgente=_sorgente(),
        configurazione=_config(),
        dashboard=DashboardMemoria(),
        anomalie=AnomalieMemoria(),
        versione_app=VERSIONE,
        registro=registro,
        trasporto_email=smtp,
    )
    kwargs = dict(
        oggi=date(2026, 7, 17),
        modalita=ModalitaEsecuzione.TEST_SMTP,
        consenso_esterno_invio=True,
        ora=datetime(2026, 7, 17, 10, tzinfo=timezone.utc),
    )
    orchestratore.esegui(**kwargs)
    seconda = orchestratore.esegui(**kwargs)

    assert seconda.notifiche_gia_presenti == 1
    assert seconda.invii_tentati == 0
    assert seconda.stato == "ATTENZIONE"
    assert len(smtp.inviati) == 1


def test_produzione_attiva_usa_il_solo_interruttore() -> None:
    smtp = TrasportoEmailMemoria()
    orchestratore = OrchestratoreReminder(
        sorgente=_sorgente(),
        configurazione=_config(attiva=True),
        dashboard=DashboardMemoria(),
        anomalie=AnomalieMemoria(),
        versione_app=VERSIONE,
        registro=RegistroPersistente(ArchivioNotificheMemoria(), versione_app=VERSIONE),
        trasporto_email=smtp,
    )
    esito = orchestratore.esegui(
        oggi=date(2026, 7, 17),
        modalita=ModalitaEsecuzione.PRODUZIONE,
        consenso_esterno_invio=True,
    )

    assert esito.invii_riusciti == 1
    assert smtp.inviati[0].destinatario == "anna@example.invalid"


def test_limite_cinquanta_arresto_ripresa_e_deduplicazione() -> None:
    archivio = ArchivioNotificheMemoria()
    smtp = TrasportoEmailMemoria()
    orchestratore = OrchestratoreReminder(
        sorgente=_sorgente(*[
            [f"A-{i:03}", "Persona", "Test", f"test{i}@example.invalid", "2026-08-01", "true"]
            for i in range(51)
        ]),
        configurazione=_config(),
        dashboard=DashboardMemoria(),
        anomalie=AnomalieMemoria(),
        versione_app=VERSIONE,
        registro=RegistroPersistente(archivio, versione_app=VERSIONE),
        trasporto_email=smtp,
    )
    kwargs = dict(
        oggi=date(2026, 7, 17),
        modalita=ModalitaEsecuzione.PRODUZIONE,
        consenso_esterno_invio=True,
    )

    prima = orchestratore.esegui(**kwargs)
    assert prima.candidati == 51
    assert prima.invii_tentati == prima.invii_riusciti == 50
    assert len(archivio.snapshot()) == len(smtp.inviati) == 50

    spento = replace(
        orchestratore,
        configurazione=replace(orchestratore.configurazione, automazione_attiva=False),
    ).esegui(**kwargs)
    assert spento.stato == "DISATTIVATO"
    assert spento.invii_tentati == 0
    assert len(archivio.snapshot()) == len(smtp.inviati) == 50

    ripresa = orchestratore.esegui(**kwargs)
    assert ripresa.notifiche_gia_presenti == 50
    assert ripresa.invii_tentati == ripresa.invii_riusciti == 1

    ripetizione = orchestratore.esegui(**kwargs)
    assert ripetizione.notifiche_gia_presenti == 51
    assert ripetizione.invii_tentati == 0
    assert len(archivio.snapshot()) == len(smtp.inviati) == 51
    assert len({messaggio.destinatario for messaggio in smtp.inviati}) == 51
    assert all(riga.stato is StatoNotifica.SENT and riga.tentativi == 1
               for riga in archivio.snapshot())


def test_errore_smtp_non_classificato_diventa_esito_incerto() -> None:
    archivio = ArchivioNotificheMemoria()
    smtp = TrasportoEmailMemoria(errore=RuntimeError("errore inatteso"))
    orchestratore = OrchestratoreReminder(
        sorgente=_sorgente(),
        configurazione=_config(),
        dashboard=DashboardMemoria(),
        anomalie=AnomalieMemoria(),
        versione_app=VERSIONE,
        registro=RegistroPersistente(archivio, versione_app=VERSIONE),
        trasporto_email=smtp,
    )
    esito = orchestratore.esegui(
        oggi=date(2026, 7, 17),
        modalita=ModalitaEsecuzione.TEST_SMTP,
        consenso_esterno_invio=True,
        ora=datetime(2026, 7, 17, 10, tzinfo=timezone.utc),
    )

    assert esito.stato == "REVISIONE_RICHIESTA"
    assert archivio.snapshot()[0].stato is StatoNotifica.UNKNOWN_REVIEW_REQUIRED


def test_fallimento_del_fallback_sul_registro_viene_segnalato() -> None:
    class RegistroConFallbackNonDisponibile:
        def puo_prenotare(self, notification_id: str) -> bool:
            return True

        def prenota(self, candidato, *, ora=None) -> None:
            pass

        def segna_esito_incerto(self, candidato, *, errore, ora=None) -> None:
            raise RuntimeError("registro non disponibile")

    anomalie = AnomalieMemoria()
    orchestratore = OrchestratoreReminder(
        sorgente=_sorgente(),
        configurazione=_config(),
        dashboard=DashboardMemoria(),
        anomalie=anomalie,
        versione_app=VERSIONE,
        registro=RegistroConFallbackNonDisponibile(),
        trasporto_email=TrasportoEmailMemoria(errore=RuntimeError("errore inatteso")),
    )

    esito = orchestratore.esegui(
        oggi=date(2026, 7, 17),
        modalita=ModalitaEsecuzione.TEST_SMTP,
        consenso_esterno_invio=True,
    )

    assert esito.stato == "REVISIONE_RICHIESTA"
    assert esito.esiti_incerti == 1
    assert {item.codice for item in anomalie.snapshot()} == {
        "ERRORE_NON_CLASSIFICATO",
        "REGISTRO_INCOERENTE",
    }


def test_errore_smtp_permanente_diventa_failed_permanent() -> None:
    archivio = ArchivioNotificheMemoria()
    smtp = TrasportoEmailMemoria(errore=ErroreSmtpPermanente("rifiutata"))
    orchestratore = OrchestratoreReminder(
        sorgente=_sorgente(),
        configurazione=_config(),
        dashboard=DashboardMemoria(),
        anomalie=AnomalieMemoria(),
        versione_app=VERSIONE,
        registro=RegistroPersistente(archivio, versione_app=VERSIONE),
        trasporto_email=smtp,
    )
    esito = orchestratore.esegui(
        oggi=date(2026, 7, 17),
        modalita=ModalitaEsecuzione.TEST_SMTP,
        consenso_esterno_invio=True,
        ora=datetime(2026, 7, 17, 10, tzinfo=timezone.utc),
    )

    assert esito.stato == "ATTENZIONE"
    assert archivio.snapshot()[0].stato is StatoNotifica.FAILED_PERMANENT


def test_dry_run_con_anomalie_non_restituisce_un_falso_verde() -> None:
    orchestratore = OrchestratoreReminder(
        sorgente=_sorgente(
            ["A-1", "", "Verdi", "", "2026-08-01", "true"],
        ),
        configurazione=_config(attiva=False, override=None),
        dashboard=DashboardMemoria(),
        anomalie=AnomalieMemoria(),
        versione_app=VERSIONE,
    )

    esito = orchestratore.esegui(
        oggi=date(2026, 7, 17),
        modalita=ModalitaEsecuzione.DRY_RUN,
    )

    assert esito.stato == "ATTENZIONE"
    assert esito.anomalie == 2


def test_test_smtp_senza_candidati_non_restituisce_ok() -> None:
    anomalie = AnomalieMemoria()
    orchestratore = OrchestratoreReminder(
        sorgente=_sorgente(
            ["A-1", "Anna", "Verdi", "anna@example.invalid", "2027-08-01", "true"],
        ),
        configurazione=_config(attiva=False),
        dashboard=DashboardMemoria(),
        anomalie=anomalie,
        versione_app=VERSIONE,
        registro=RegistroPersistente(ArchivioNotificheMemoria(), versione_app=VERSIONE),
        trasporto_email=TrasportoEmailMemoria(),
    )

    esito = orchestratore.esegui(
        oggi=date(2026, 7, 17),
        modalita=ModalitaEsecuzione.TEST_SMTP,
        consenso_esterno_invio=True,
    )

    assert esito.stato == "ATTENZIONE"
    assert esito.invii_tentati == 0
    assert esito.anomalie == 1
    assert {item.codice for item in anomalie.snapshot()} == {"TEST_SMTP_NON_ESEGUITO"}


def test_errore_nel_registro_dopo_smtp_retryable_richiede_revisione() -> None:
    class RegistroConErrore:
        def puo_prenotare(self, notification_id: str) -> bool:
            return True

        def prenota(self, candidato, *, ora=None) -> None:
            pass

        def segna_errore_retryable(self, candidato, *, errore, ora=None) -> None:
            raise RuntimeError("registro non disponibile")

    anomalie = AnomalieMemoria()
    orchestratore = OrchestratoreReminder(
        sorgente=_sorgente(),
        configurazione=_config(),
        dashboard=DashboardMemoria(),
        anomalie=anomalie,
        versione_app=VERSIONE,
        registro=RegistroConErrore(),
        trasporto_email=TrasportoEmailMemoria(errore=ErroreSmtpRetryable("temporaneo")),
    )

    esito = orchestratore.esegui(
        oggi=date(2026, 7, 17),
        modalita=ModalitaEsecuzione.TEST_SMTP,
        consenso_esterno_invio=True,
    )

    assert esito.stato == "REVISIONE_RICHIESTA"
    assert esito.invii_falliti == 0
    assert esito.esiti_incerti == 1
    assert {item.codice for item in anomalie.snapshot()} == {"REGISTRO_INCOERENTE"}
