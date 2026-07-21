import json
import stat
from pathlib import Path

import pytest

from reminder_certificati.admin_migration import (
    COLONNE_CONFIG_V2,
    COLONNE_NOTIFICHE_LEGACY,
    ErroreMigrazioneAmministrativa,
    prepara_piano,
)
from reminder_certificati.admin_schema import (
    COLONNE_DASHBOARD,
    VERSIONE_SCHEMA_AMMINISTRATIVO,
    crea_schema_amministrativo,
)
from reminder_certificati.admin_store import COLONNE_NOTIFICHE
from reminder_certificati.rules import TIPO_NOTIFICA_SCADENZA


def _config_v2() -> list[list[str]]:
    return [
        list(COLONNE_CONFIG_V2),
        ["SCHEMA_VERSION", "2", "INTERO", "vecchio", "false"],
        ["AUTOMAZIONE_ATTIVA", "true", "BOOLEANO", "vecchio", "true"],
        ["INVII_REALI_ABILITATI", "true", "BOOLEANO", "vecchio", "true"],
        ["GIORNI_PREAVVISO", "45", "INTERO", "vecchio", "true"],
        ["LIMITE_INVII_PER_ESECUZIONE", "8", "INTERO", "vecchio", "true"],
        [
            "DESTINATARIO_OVERRIDE",
            "test@example.invalid",
            "EMAIL_OPZIONALE",
            "vecchio",
            "true",
        ],
        ["OGGETTO_EMAIL", "Oggetto", "TEMPLATE", "vecchio", "true"],
        ["CORPO_EMAIL", "Corpo {{data_scadenza}}", "TEMPLATE", "vecchio", "true"],
        ["FIRMA_TESTO", "Firma", "TEMPLATE", "vecchio", "true"],
    ]


def _dashboard_legacy() -> list[list[str]]:
    return [
        list(COLONNE_DASHBOARD),
        ["stato_sistema", "DISATTIVATO", "Stato operativo complessivo."],
        ["righe_lette", "0", "Righe lette."],
        ["kill_switch", "ATTIVO", "Vecchia barriera operativa."],
    ]


def _dashboard_corrente() -> list[list[str]]:
    schema = crea_schema_amministrativo()
    return [list(riga) for riga in schema.ottieni_tab("DASHBOARD").matrice()]


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


def test_migra_config_v2_con_un_solo_interruttore_spento() -> None:
    piano = prepara_piano(
        _config_v2(),
        _notifiche_legacy(),
        _dashboard_legacy(),
    )
    valori = {riga[0]: riga[1] for riga in piano.config_dopo[1:]}

    assert valori["SCHEMA_VERSION"] == str(VERSIONE_SCHEMA_AMMINISTRATIVO)
    assert valori["INVIO_AUTOMATICO_ATTIVO"] == "false"
    assert valori["GIORNI_PREAVVISO"] == "45"
    assert valori["DESTINATARIO_OVERRIDE"] == "test@example.invalid"
    assert valori["OGGETTO_EMAIL"] == "Oggetto"
    for chiave in (
        "AUTOMAZIONE_ATTIVA",
        "INVII_REALI_ABILITATI",
        "LIMITE_INVII_PER_ESECUZIONE",
    ):
        assert chiave not in valori
    assert piano.config_dopo[0] == ("chiave", "valore", "descrizione")
    assert piano.necessaria is True


def test_migra_dashboard_legacy_senza_perdere_le_altre_metriche() -> None:
    piano = prepara_piano(
        _config_v2(),
        _notifiche_legacy(),
        _dashboard_legacy(),
    )
    metriche = {riga[0]: riga[1:] for riga in piano.dashboard_dopo[1:]}

    assert "kill_switch" not in metriche
    assert metriche["automazione_attiva"][0] == "NO"
    assert metriche["righe_lette"][0] == "0"
    assert "DASHBOARD_SCHEMA_V3" in piano.modifiche


def test_migra_versione_schema_errata_e_spegne_invii() -> None:
    schema = crea_schema_amministrativo()
    config = [list(riga) for riga in schema.ottieni_tab("CONFIG").matrice()]
    for riga in config:
        if riga and riga[0] == "SCHEMA_VERSION":
            riga[1] = "2"
        if riga and riga[0] == "INVIO_AUTOMATICO_ATTIVO":
            riga[1] = "true"

    piano = prepara_piano(
        config,
        [list(COLONNE_NOTIFICHE)],
        _dashboard_corrente(),
    )
    valori = {riga[0]: riga[1] for riga in piano.config_dopo[1:]}
    dashboard = {riga[0]: riga[1] for riga in piano.dashboard_dopo[1:]}

    assert valori["SCHEMA_VERSION"] == "3"
    assert valori["INVIO_AUTOMATICO_ATTIVO"] == "false"
    assert dashboard["automazione_attiva"] == "NO"
    assert piano.necessaria is True


def test_migra_notifiche_rimuovendo_pii_e_stabilizzando_la_chiave() -> None:
    piano = prepara_piano(
        _config_v2(),
        _notifiche_legacy(_riga_legacy()),
        _dashboard_legacy(),
    )
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
    dashboard = _dashboard_corrente()
    piano = prepara_piano(config, notifiche, dashboard)

    assert piano.necessaria is False
    assert piano.modifiche == ()
    assert piano.dashboard_dopo == tuple(tuple(riga) for riga in dashboard)


def test_config_corrente_preserva_descrizioni_personalizzate_senza_migrare() -> None:
    schema = crea_schema_amministrativo()
    config = [list(riga) for riga in schema.ottieni_tab("CONFIG").matrice()]
    note = {
        "CORPO_EMAIL": "Promemoria personale sul corpo HTML.",
        "FIRMA_TESTO": "In futuro implementare la firma tramite HTML.",
    }
    for riga in config[1:]:
        if riga[0] in note:
            riga[2] = note[riga[0]]

    piano = prepara_piano(
        config,
        [list(COLONNE_NOTIFICHE)],
        _dashboard_corrente(),
    )
    descrizioni = {riga[0]: riga[2] for riga in piano.config_dopo[1:]}

    assert piano.necessaria is False
    assert piano.modifiche == ()
    assert descrizioni["CORPO_EMAIL"] == note["CORPO_EMAIL"]
    assert descrizioni["FIRMA_TESTO"] == note["FIRMA_TESTO"]


def test_migrazione_reale_preserva_le_note_delle_chiavi_esistenti() -> None:
    config = _config_v2()
    nota = "Promemoria personale: implementare la firma tramite HTML."
    for riga in config[1:]:
        if riga[0] == "FIRMA_TESTO":
            riga[3] = nota

    piano = prepara_piano(
        config,
        _notifiche_legacy(),
        _dashboard_legacy(),
    )
    descrizioni = {riga[0]: riga[2] for riga in piano.config_dopo[1:]}

    assert piano.necessaria is True
    assert descrizioni["FIRMA_TESTO"] == nota


def test_rifiuta_collisioni_prodotte_dalla_chiave_stabile() -> None:
    with pytest.raises(ErroreMigrazioneAmministrativa, match="chiavi duplicate"):
        prepara_piano(
            _config_v2(),
            _notifiche_legacy(
                _riga_legacy("REMINDER_30"),
                _riga_legacy("REMINDER_45"),
            ),
            _dashboard_legacy(),
        )


def test_backup_conserva_esattamente_lo_stato_precedente(tmp_path: Path) -> None:
    config = _config_v2()
    notifiche = _notifiche_legacy(_riga_legacy())
    dashboard = _dashboard_legacy()
    piano = prepara_piano(config, notifiche, dashboard)
    path = tmp_path / "backup.json"
    piano.salva_backup(path)
    payload = json.loads(path.read_text(encoding="utf-8"))

    assert payload["config"] == config
    assert payload["notifiche"] == notifiche
    assert payload["dashboard"] == dashboard
    assert stat.S_IMODE(path.stat().st_mode) == 0o600


def test_rifiuta_intestazioni_config_sconosciute() -> None:
    with pytest.raises(ErroreMigrazioneAmministrativa, match="intestazioni"):
        prepara_piano(
            [["a", "b"], ["x", "y"]],
            [list(COLONNE_NOTIFICHE)],
            _dashboard_corrente(),
        )
