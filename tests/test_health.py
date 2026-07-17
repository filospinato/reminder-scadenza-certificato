from datetime import datetime, timedelta, timezone

from reminder_certificati.health import LivelloSalute, valuta_salute
from reminder_certificati.monitoring import MetricheEsecuzione


def _metriche(**overrides):
    base = dict(
        stato_sistema="OK",
        ultima_esecuzione=datetime(2026, 7, 17, 10, tzinfo=timezone.utc),
        heartbeat=datetime(2026, 7, 17, 10, tzinfo=timezone.utc),
        kill_switch=False,
        versione_app="0.11.0",
    )
    base.update(overrides)
    return MetricheEsecuzione(**base)


def test_salute_ok_senza_segnali() -> None:
    esito = valuta_salute(
        _metriche(),
        ora=datetime(2026, 7, 17, 11, tzinfo=timezone.utc),
    )
    assert esito.livello is LivelloSalute.OK
    assert esito.segnali == ()


def test_heartbeat_scaduto_ed_esito_incerto_sono_critici() -> None:
    esito = valuta_salute(
        _metriche(esiti_incerti=1),
        ora=datetime(2026, 7, 19, 0, tzinfo=timezone.utc),
        massimo_silenzio=timedelta(hours=24),
    )
    assert esito.livello is LivelloSalute.CRITICAL
    assert {segnale.codice for segnale in esito.segnali} == {
        "HEARTBEAT_SCADUTO",
        "ESITI_INCERTI",
    }


def test_kill_switch_e_fallimenti_generano_warning() -> None:
    esito = valuta_salute(
        _metriche(kill_switch=True, invii_falliti=2),
        ora=datetime(2026, 7, 17, 11, tzinfo=timezone.utc),
    )
    assert esito.livello is LivelloSalute.WARNING
