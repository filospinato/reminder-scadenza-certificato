import json
from pathlib import Path

import pytest

from reminder_certificati.admin_migration import (
    COLONNE_NOTIFICHE_LEGACY,
    ErroreMigrazioneAmministrativa,
    prepara_piano,
)
from reminder_certificati.admin_schema import (
    COLONNE_CONFIG,
    VERSIONE_SCHEMA_AMMINISTRATIVO,
    crea_schema_amministrativo,
)
from reminder_certificati.admin_store import COLONNE_NOTIFICHE
from reminder_certificati.rules import TIPO_NOTIFICA_SCADENZA


def _config_legacy() -> list[list[str]]:
    return [
        list(COLONNE_CONFIG),
        ["SISTEMA_ATTIVO", "false", "BOOLEANO", "vecchio", "true"],
        ["INVII_REALI_ABILITATI", "false", "BOOLEANO", "vecchio", "true"],
        ["MODALITA_TEST", "true", "BOOLEANO", "vecchio", "true"],
        ["KILL_SWITCH", "true", "BOOLEANO", "vecchio", "true"],
        ["GIORNI_PREAVVISO", "45", "INTERO", "vecchio", "true"],
        ["LIMITE_INVII_PER_ESECUZIONE", "8", "INTERO", "vecchio", "true"],
        ["DESTINATARIO_OVERRIDE", "", "EMAIL_OPZIONALE", "vecchio", "true"],
        ["OGGETTO_EMAIL", "Oggetto", "TEMPLATE", "vecchio", "true"],
        ["CORPO_EMAIL", "Corpo {{data_scadenza}}", "TEMPLATE", "vecchio", "true"],
        ["FIRMA_TESTO", "Firma", "TEMPLATE", "vecchio", "true"],
    ]


def _notifiche_legacy(*righe: list[str]) -> list[list[str]]:
    return [list(COLONNE_NOTIFICHE_LEGACY), *righe]


def _riga_legacy(tipo: str = "REMINDER_30", id_arbitro: str = "A-1") -> list[str]:
    return [
        f"{id_arbitro}|2026-08-01|{tipo}",
        id_arbitro,
        "Anna",
        "Verdi",
        "anna@example.it",
        "2026-08-01",
        tipo,
        "SENT",
        "1",
        "2026-07-01T10:00:00+00:00",
        "2026-07-01T10:01:00+00:00",
        "<m@example.it>",
        "0.12.0",
        "",
    ]


def test_migra_config_legacy_e_lascia_tutto_disattivato() -> None:
    piano = prepara_piano(_config_legacy(), _notifiche_legacy())
    valori = {riga[0]: riga[1] for riga in piano.config_dopo[1:]}
    assert valori["SCHEMA_VERSION"] == str(VERSIONE_SCHEMA_AMMINISTRATIVO)
    assert valori["AUTOMAZIONE_ATTIVA"] == "false"
    assert valori["INVII_REALI_ABILITATI"] == "false"
    assert valori["GIORNI_PREAVVISO"] == "45"
    assert "SISTEMA_ATTIVO" not in valori
    assert "MODALITA_TEST" not in valori
    assert "KILL_SWITCH" not in valori
    assert piano.necessaria is True


def test_migra_notifiche_rimuovendo_pii_e_stabilizzando_la_chiave() -> None:
    piano = prepara_piano(_config_legacy(), _notifiche_legacy(_riga_legacy()))
    assert piano.notifiche_dopo[0] == COLONNE_NOTIFICHE
    assert len(piano.notifiche_dopo[1]) == 11
    riga = dict(zip(COLONNE_NOTIFICHE, piano.notifiche_dopo[1], strict=True))
    assert riga["tipo"] == TIPO_NOTIFICA_SCADENZA
    assert riga["notification_id"] == f"A-1|2026-08-01|{TIPO_NOTIFICA_SCADENZA}"
    assert "Anna" not in piano.notifiche_dopo[1]
    assert "Verdi" not in piano.notifiche_dopo[1]
    assert "anna@example.it" not in piano.notifiche_dopo[1]


def test_migrazione_corrente_e_idempotente() -> None:
    schema = crea_schema_amministrativo()
    config = [list(riga) for riga in schema.ottieni_tab("CONFIG").matrice()]
    notifiche = [list(COLONNE_NOTIFICHE)]
    piano = prepara_piano(config, notifiche)
    assert piano.necessaria is False
    assert piano.modifiche == ()


def test_rifiuta_collisioni_prodotte_dalla_chiave_stabile() -> None:
    with pytest.raises(ErroreMigrazioneAmministrativa, match="chiavi duplicate"):
        prepara_piano(
            _config_legacy(),
            _notifiche_legacy(
                _riga_legacy("REMINDER_30"),
                _riga_legacy("REMINDER_45"),
            ),
        )


def test_backup_conserva_esattamente_lo_stato_precedente(tmp_path: Path) -> None:
    config = _config_legacy()
    notifiche = _notifiche_legacy(_riga_legacy())
    piano = prepara_piano(config, notifiche)
    path = tmp_path / "backup.json"
    piano.salva_backup(path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["config"] == config
    assert payload["notifiche"] == notifiche
