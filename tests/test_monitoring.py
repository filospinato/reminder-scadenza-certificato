from datetime import datetime, timezone

from reminder_certificati.monitoring import (
    AnomaliaRuntime,
    AnomalieGoogleSheets,
    AnomalieMemoria,
    DashboardMemoria,
    MetricheEsecuzione,
    SeveritaAnomalia,
    TrasportoMonitoraggioGoogleApi,
    sanitizza_messaggio,
)


def _anomalia() -> AnomaliaRuntime:
    return AnomaliaRuntime.crea(
        severita=SeveritaAnomalia.WARNING,
        origine="OPERATIVO",
        codice="EMAIL_NON_VALIDA",
        messaggio="anomalia dati nel campo email",
        versione_app="0.12.0",
        riga_sorgente=7,
        campo="e-Mail",
        rilevata_il=datetime(2026, 7, 17, 10, tzinfo=timezone.utc),
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
    prima = _anomalia()
    seconda = _anomalia()
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
        automazione_attiva=True,
        versione_app="0.12.0",
    )
    dashboard = DashboardMemoria()
    dashboard.aggiorna(metriche)

    assert dashboard.ultima == metriche
    valori = {riga[0]: riga[1] for riga in metriche.come_righe()}
    assert valori["righe_lette"] == "5"
    assert valori["automazione_attiva"] == "SI"
    assert "email" not in valori


class _TrasportoAnomalie:
    def __init__(self, righe=()) -> None:
        self.righe = [list(riga) for riga in righe]
        self.letture = 0
        self.append = 0

    def leggi_valori(self, **kwargs):
        self.letture += 1
        return [list(riga) for riga in self.righe]

    def aggiungi_riga(self, *, valori, **kwargs):
        self.append += 1
        self.righe.append(list(valori))

    def sostituisci_valori(self, **kwargs):
        raise AssertionError("non usato in questo test")


def test_anomalie_google_non_riaccoda_un_id_gia_aperto() -> None:
    anomalia = _anomalia()
    trasporto = _TrasportoAnomalie([anomalia.come_riga()])
    archivio = AnomalieGoogleSheets(
        trasporto=trasporto,
        spreadsheet_id="synthetic-sheet",
    )

    archivio.registra(anomalia)
    archivio.registra(anomalia)

    assert trasporto.letture == 1
    assert trasporto.append == 0


def test_anomalie_google_accoda_una_sola_volta_un_nuovo_id() -> None:
    anomalia = _anomalia()
    trasporto = _TrasportoAnomalie()
    archivio = AnomalieGoogleSheets(
        trasporto=trasporto,
        spreadsheet_id="synthetic-sheet",
    )

    archivio.registra(anomalia)
    archivio.registra(anomalia)

    assert trasporto.letture == 1
    assert trasporto.append == 1


class _Richiesta:
    def __init__(self, payload=None):
        self.payload = {} if payload is None else payload

    def execute(self):
        return self.payload


class _ValoriApi:
    def __init__(self) -> None:
        self.update_calls: list[dict[str, object]] = []

    def clear(self, **kwargs):
        raise AssertionError("la dashboard non deve essere svuotata prima dell'update")

    def get(self, **kwargs):
        return _Richiesta({"values": []})

    def update(self, **kwargs):
        self.update_calls.append(kwargs)
        return _Richiesta()

    def append(self, **kwargs):
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
