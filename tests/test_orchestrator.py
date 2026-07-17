from datetime import date, datetime, timezone

from reminder_certificati.admin_store import ArchivioNotificheMemoria
from reminder_certificati.data_sources import SorgenteMemoria
from reminder_certificati.email_templates import ConfigurazioneEmail
from reminder_certificati.monitoring import AnomalieMemoria, DashboardMemoria
from reminder_certificati.orchestrator import ModalitaEsecuzione, OrchestratoreReminder
from reminder_certificati.persistent_registry import RegistroPersistente
from reminder_certificati.registry import StatoNotifica
from reminder_certificati.runtime_config import ConfigurazioneRuntime
from reminder_certificati.smtp_transport import TrasportoEmailMemoria


def _sorgente() -> SorgenteMemoria:
    return SorgenteMemoria(
        [
            [
                "id_arbitro",
                "nome",
                "cognome",
                "email",
                "scadenza_certificato",
                "attivo",
            ],
            ["A-1", "Anna Maria", "Verdi", "anna@example.invalid", "2026-08-01", "true"],
        ]
    )


def _config(*, attivo: bool = True, test: bool = True, kill: bool = False) -> ConfigurazioneRuntime:
    return ConfigurazioneRuntime(
        sistema_attivo=attivo,
        invii_reali_abilitati=False,
        modalita_test=test,
        kill_switch=kill,
        giorni_preavviso=30,
        limite_invii_per_esecuzione=10,
        destinatario_override="test@example.invalid" if test else None,
        email=ConfigurazioneEmail(),
        contatto_supporto=None,
    )


def test_kill_switch_blocca_prima_della_lettura() -> None:
    dashboard = DashboardMemoria()
    orchestratore = OrchestratoreReminder(
        sorgente=_sorgente(),
        configurazione=_config(kill=True),
        dashboard=dashboard,
        anomalie=AnomalieMemoria(),
        versione_app="0.11.0",
    )

    esito = orchestratore.esegui(oggi=date(2026, 7, 17))

    assert esito.stato == "BLOCCATO_KILL_SWITCH"
    assert esito.righe_lette == 0
    assert dashboard.ultima is not None
    assert dashboard.ultima.kill_switch is True


def test_dry_run_compone_senza_registro_o_smtp() -> None:
    dashboard = DashboardMemoria()
    anomalie = AnomalieMemoria()
    orchestratore = OrchestratoreReminder(
        sorgente=_sorgente(),
        configurazione=_config(),
        dashboard=dashboard,
        anomalie=anomalie,
        versione_app="0.11.0",
    )

    esito = orchestratore.esegui(
        oggi=date(2026, 7, 17),
        modalita=ModalitaEsecuzione.DRY_RUN,
    )

    assert esito.stato == "DRY_RUN_OK"
    assert esito.candidati == 1
    assert esito.messaggi_composti == 1
    assert esito.invii_tentati == 0
    assert anomalie.snapshot() == ()


def test_modalita_test_invia_solo_all_override_e_persistente_test_id() -> None:
    archivio = ArchivioNotificheMemoria()
    registro = RegistroPersistente(archivio, versione_app="0.11.0")
    smtp = TrasportoEmailMemoria()
    orchestratore = OrchestratoreReminder(
        sorgente=_sorgente(),
        configurazione=_config(),
        dashboard=DashboardMemoria(),
        anomalie=AnomalieMemoria(),
        versione_app="0.11.0",
        registro=registro,
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
    assert righe[0].tipo == "TEST_REMINDER_30"
    assert righe[0].stato is StatoNotifica.SENT
    assert righe[0].nome == "Anna Maria"


def test_seconda_esecuzione_test_non_duplica() -> None:
    archivio = ArchivioNotificheMemoria()
    registro = RegistroPersistente(archivio, versione_app="0.11.0")
    smtp = TrasportoEmailMemoria()
    orchestratore = OrchestratoreReminder(
        sorgente=_sorgente(),
        configurazione=_config(),
        dashboard=DashboardMemoria(),
        anomalie=AnomalieMemoria(),
        versione_app="0.11.0",
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
    assert len(smtp.inviati) == 1
