from datetime import date

from reminder_certificati.data_sources import SorgenteMemoria
from reminder_certificati.email_templates import ConfigurazioneEmail
from reminder_certificati.monitoring import AnomalieMemoria, DashboardMemoria
from reminder_certificati.orchestrator import ModalitaEsecuzione, OrchestratoreReminder
from reminder_certificati.runtime_config import ConfigurazioneRuntime


INTESTAZIONI = [
    "id_arbitro",
    "nome",
    "cognome",
    "email",
    "scadenza_certificato",
    "attivo",
]


def configurazione() -> ConfigurazioneRuntime:
    return ConfigurazioneRuntime(
        automazione_attiva=False,
        giorni_preavviso=30,
        destinatario_override=None,
        email=ConfigurazioneEmail(),
    )


def test_dry_run_ignora_le_righe_fol_con_sola_tessera() -> None:
    anomalie = AnomalieMemoria()
    sorgente = SorgenteMemoria(
        [
            INTESTAZIONI,
            ["100001", "", "", "", "", ""],
            ["100002", "", "", "", "", ""],
            [
                "A-1",
                "Mario",
                "Rossi",
                "mario@example.invalid",
                "2026-08-01",
                "true",
            ],
        ]
    )
    orchestratore = OrchestratoreReminder(
        sorgente=sorgente,
        configurazione=configurazione(),
        dashboard=DashboardMemoria(),
        anomalie=anomalie,
        versione_app="0.14.7",
    )

    esito = orchestratore.esegui(
        oggi=date(2026, 7, 17),
        modalita=ModalitaEsecuzione.DRY_RUN,
    )

    assert esito.candidati == 1
    assert esito.anomalie == 0
    assert anomalie.snapshot() == ()


def test_dry_run_segnala_nome_cognome_ed_email_solo_se_imminenti() -> None:
    anomalie = AnomalieMemoria()
    sorgente = SorgenteMemoria(
        [
            INTESTAZIONI,
            ["A-1", "", "", "", "2026-08-01", "true"],
            ["A-2", "", "", "", "2026-12-31", "true"],
        ]
    )
    orchestratore = OrchestratoreReminder(
        sorgente=sorgente,
        configurazione=configurazione(),
        dashboard=DashboardMemoria(),
        anomalie=anomalie,
        versione_app="0.14.7",
    )

    esito = orchestratore.esegui(
        oggi=date(2026, 7, 17),
        modalita=ModalitaEsecuzione.DRY_RUN,
    )

    assert esito.candidati == 0
    assert esito.anomalie == 3
    assert esito.stato == "ATTENZIONE"
    assert {item.codice for item in anomalie.snapshot()} == {
        "NOME_MANCANTE",
        "COGNOME_MANCANTE",
        "EMAIL_NON_VALIDA",
    }
