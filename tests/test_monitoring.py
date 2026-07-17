from datetime import datetime, timezone

from reminder_certificati.monitoring import (
    AnomaliaRuntime,
    AnomalieMemoria,
    DashboardMemoria,
    MetricheEsecuzione,
    SeveritaAnomalia,
    sanitizza_messaggio,
)


def test_sanitizza_email_token_e_riduce_righe() -> None:
    risultato = sanitizza_messaggio(
        "Errore per mario@example.it\nAuthorization: sk-test-segreto"
    )

    assert "mario@example.it" not in risultato
    assert "sk-test-segreto" not in risultato
    assert "\n" not in risultato


def test_anomalia_id_e_stabile_e_i_duplicati_aperti_non_si_accodano() -> None:
    ora = datetime(2026, 7, 17, 10, tzinfo=timezone.utc)
    prima = AnomaliaRuntime.crea(
        severita=SeveritaAnomalia.WARNING,
        origine="OPERATIVO",
        codice="EMAIL_NON_VALIDA",
        messaggio="anomalia dati nel campo email",
        versione_app="0.11.0",
        riga_sorgente=7,
        campo="e-Mail",
        rilevata_il=ora,
    )
    seconda = AnomaliaRuntime.crea(
        severita=SeveritaAnomalia.WARNING,
        origine="OPERATIVO",
        codice="EMAIL_NON_VALIDA",
        messaggio="anomalia dati nel campo email",
        versione_app="0.11.0",
        riga_sorgente=7,
        campo="e-Mail",
        rilevata_il=ora,
    )
    archivio = AnomalieMemoria()
    archivio.registra(prima)
    archivio.registra(seconda)

    assert prima.anomalia_id == seconda.anomalia_id
    assert len(archivio.snapshot()) == 1
    assert len(prima.come_riga()) == 10


def test_dashboard_espone_solo_conteggi_e_stato() -> None:
    ora = datetime(2026, 7, 17, 10, tzinfo=timezone.utc)
    metriche = MetricheEsecuzione(
        stato_sistema="DRY_RUN_OK",
        ultima_esecuzione=ora,
        heartbeat=ora,
        righe_lette=5,
        righe_valide=4,
        candidati=2,
        anomalie=1,
        kill_switch=False,
        versione_app="0.11.0",
    )
    dashboard = DashboardMemoria()
    dashboard.aggiorna(metriche)

    assert dashboard.ultima == metriche
    valori = {riga[0]: riga[1] for riga in metriche.come_righe()}
    assert valori["righe_lette"] == "5"
    assert valori["kill_switch"] == "DISATTIVO"
    assert "email" not in valori
