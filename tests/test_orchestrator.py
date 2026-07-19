from datetime import date, datetime, timedelta, timezone

from reminder_certificati.admin_store import ArchivioNotificheMemoria
from reminder_certificati.data_sources import SorgenteMemoria
from reminder_certificati.email_templates import ConfigurazioneEmail
from reminder_certificati.models import Arbitro, CandidatoNotifica
from reminder_certificati.monitoring import AnomalieMemoria, DashboardMemoria
from reminder_certificati.orchestrator import ModalitaEsecuzione, OrchestratoreReminder
from reminder_certificati.persistent_registry import RegistroPersistente
from reminder_certificati.registry import StatoNotifica
from reminder_certificati.runtime_config import ConfigurazioneRuntime
from reminder_certificati.smtp_transport import TrasportoEmailMemoria

VERSIONE = "0.12.0"
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
    invii_reali: bool = False,
    limite: int = 10,
    override: str | None = "test@example.invalid",
) -> ConfigurazioneRuntime:
    return ConfigurazioneRuntime(
        automazione_attiva=attiva,
        invii_reali_abilitati=invii_reali,
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
    tipo = "REMINDER_30"
    return CandidatoNotifica(
        arbitro=arbitro,
        tipo=tipo,
        giorni_residui=15,
        notification_id=f"{id_arbitro}|{scadenza.isoformat()}|{tipo}",
    )


def test_automazione_disattivata_blocca_prima_della_lettura() -> None:
    dashboard = DashboardMemoria()
    orchestratore = OrchestratoreReminder(
        sorgente=_sorgente(),
        configurazione=_config(attiva=False),
        dashboard=dashboard,
        anomalie=AnomalieMemoria(),
        versione_app=VERSIONE,
    )

    esito = orchestratore.esegui(oggi=date(2026, 7, 17))

    assert esito.stato == "DISATTIVATO"
    assert esito.righe_lette == 0
    assert dashboard.ultima is not None
    assert dashboard.ultima.automazione_attiva is False


def test_dry_run_compone_senza_override_scritture_o_invio() -> None:
    dashboard = DashboardMemoria()
    anomalie = AnomalieMemoria()
    archivio = ArchivioNotificheMemoria()
    orchestratore = OrchestratoreReminder(
        sorgente=_sorgente(),
        configurazione=_config(override=None),
        dashboard=dashboard,
        anomalie=anomalie,
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
    assert anomalie.snapshot() == ()


def test_dry_run_salta_registrate_e_applica_limite_dopo_deduplicazione() -> None:
    archivio = ArchivioNotificheMemoria()
    registro = RegistroPersistente(archivio, versione_app=VERSIONE)
    ora = datetime(2026, 7, 17, 10, tzinfo=timezone.utc)
    primo = _candidato(
        "A-1", "Anna", "anna@example.invalid", date(2026, 8, 1)
    )
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


def test_test_smtp_invia_solo_all_override_e_lo_registra() -> None:
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
    assert righe[0].email == "test@example.invalid"


def test_test_smtp_invia_al_massimo_un_messaggio() -> None:
    smtp = TrasportoEmailMemoria()
    orchestratore = OrchestratoreReminder(
        sorgente=_sorgente(
            ["A-1", "Anna", "Verdi", "anna@example.invalid", "2026-08-01", "true"],
            ["A-2", "Luca", "Verdi", "luca@example.invalid", "2026-08-02", "true"],
        ),
        configurazione=_config(limite=10),
        dashboard=DashboardMemoria(),
        anomalie=AnomalieMemoria(),
        versione_app=VERSIONE,
        registro=RegistroPersistente(
            ArchivioNotificheMemoria(), versione_app=VERSIONE
        ),
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
    assert len(smtp.inviati) == 1


def test_produzione_richiede_invii_reali_abilitati() -> None:
    orchestratore = OrchestratoreReminder(
        sorgente=_sorgente(),
        configurazione=_config(invii_reali=False),
        dashboard=DashboardMemoria(),
        anomalie=AnomalieMemoria(),
        versione_app=VERSIONE,
        registro=RegistroPersistente(
            ArchivioNotificheMemoria(), versione_app=VERSIONE
        ),
        trasporto_email=TrasportoEmailMemoria(),
    )

    try:
        orchestratore.esegui(
            oggi=date(2026, 7, 17),
            modalita=ModalitaEsecuzione.PRODUZIONE,
            consenso_esterno_invio=True,
        )
    except Exception as exc:
        assert "barriere" in str(exc)
    else:
        raise AssertionError("produzione accettata senza INVII_REALI_ABILITATI")


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
