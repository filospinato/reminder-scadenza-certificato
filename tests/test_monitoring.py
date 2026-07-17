from datetime import datetime, timezone

from reminder_certificati.monitoring import (
    AnomaliaRuntime,
    AnomalieMemoria,
    DashboardMemoria,
    MetricheEsecuzione,
    SeveritaAnomalia,
    TrasportoMonitoraggioGoogleApi,
    sanitizza_messaggio,
)


def test_sanitizza_email_token_notification_id_e_riduce_righe() -> None:
    risultato = sanitizza_messaggio(
        "Errore per mario@example.it\nAuthorization: sk-test-segreto "
        "A-123|2026-08-01|REMINDER_30"
    )

    assert "mario@example.it" not in risultato
    assert "sk-test-segreto" not in risultato
    assert "A-123" not in risultato
    assert "notification-id-rimosso" in risultato
    assert "\n" not in risultato


def test_anomalia_id_e_stabile_e_i_duplicati_aperti_non_si_accodano() -> None:
    ora = datetime(2026, 7, 17, 10, tzinfo=timezone.utc)
    prima = AnomaliaRuntime.crea(
        severita=SeveritaAnomalia.WARNING,
        origine="OPERATIVO",
        codice="EMAIL_NON_VALIDA",
        messaggio="anomalia dati nel campo email",
        versione_app="0.11.1",
        riga_sorgente=7,
        campo="e-Mail",
        rilevata_il=ora,
    )
    seconda = AnomaliaRuntime.crea(
        severita=SeveritaAnomalia.WARNING,
        origine="OPERATIVO",
        codice="EMAIL_NON_VALIDA",
        messaggio="anomalia dati nel campo email",
        versione_app="0.11.1",
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
        versione_app="0.11.1",
    )
    dashboard = DashboardMemoria()
    dashboard.aggiorna(metriche)

    assert dashboard.ultima == metriche
    valori = {riga[0]: riga[1] for riga in metriche.come_righe()}
    assert valori["righe_lette"] == "5"
    assert valori["kill_switch"] == "DISATTIVO"
    assert "email" not in valori


class _Richiesta:
    def execute(self):
        return {}


class _ValoriApi:
    def __init__(self) -> None:
        self.update_calls: list[dict[str, object]] = []

    def clear(self, **kwargs):
        raise AssertionError("la dashboard non deve essere svuotata prima dell'update")

    def update(self, **kwargs):
        self.update_calls.append(kwargs)
        return _Richiesta()


class _SpreadsheetsApi:
    def __init__(self, valori: _ValoriApi) -> None:
        self._valori = valori

    def values(self) -> _ValoriApi:
        return self._valori


class _ServizioApi:
    def __init__(self) -> None:
        self.valori = _ValoriApi()
        self._spreadsheets = _SpreadsheetsApi(self.valori)

    def spreadsheets(self) -> _SpreadsheetsApi:
        return self._spreadsheets


def test_dashboard_google_usa_un_solo_update_senza_clear() -> None:
    servizio = _ServizioApi()
    trasporto = TrasportoMonitoraggioGoogleApi(servizio)

    trasporto.sostituisci_valori(
        spreadsheet_id="synthetic-sheet",
        intervallo_a1="'DASHBOARD'!A1:C",
        valori=[["metrica", "valore", "descrizione"]],
    )

    assert len(servizio.valori.update_calls) == 1
    assert servizio.valori.update_calls[0]["valueInputOption"] == "RAW"
