import pytest

from reminder_certificati.admin_schema import crea_schema_amministrativo
from reminder_certificati.runtime_config import (
    ErroreConfigurazioneRuntime,
    carica_configurazione,
)


def _matrice_config() -> list[list[str]]:
    matrice = crea_schema_amministrativo().ottieni_tab("CONFIG").matrice()
    return [list(riga) for riga in matrice]


def _imposta(matrice: list[list[str]], chiave: str, valore: str) -> None:
    for riga in matrice[1:]:
        if riga[0] == chiave:
            riga[1] = valore
            return
    raise AssertionError(chiave)


def test_configurazione_iniziale_e_disattivata() -> None:
    config = carica_configurazione(_matrice_config())

    assert config.sistema_attivo is False
    assert config.kill_switch is True
    assert config.modalita_test is True
    assert config.invio_reale_consentito(consenso_esterno=True) is False


def test_modalita_test_attiva_richiede_override() -> None:
    matrice = _matrice_config()
    _imposta(matrice, "SISTEMA_ATTIVO", "true")
    _imposta(matrice, "KILL_SWITCH", "false")

    with pytest.raises(ErroreConfigurazioneRuntime, match="DESTINATARIO_OVERRIDE"):
        carica_configurazione(matrice)


def test_modalita_test_attiva_accetta_override_sintetico() -> None:
    matrice = _matrice_config()
    _imposta(matrice, "SISTEMA_ATTIVO", "true")
    _imposta(matrice, "KILL_SWITCH", "false")
    _imposta(matrice, "DESTINATARIO_OVERRIDE", "test@example.invalid")

    config = carica_configurazione(matrice)

    assert config.elaborazione_consentita is True
    assert config.destinatario_override == "test@example.invalid"
    assert config.invio_reale_consentito(consenso_esterno=True) is False


def test_invii_reali_richiedono_configurazione_coerente_e_consenso_esterno() -> None:
    matrice = _matrice_config()
    _imposta(matrice, "SISTEMA_ATTIVO", "true")
    _imposta(matrice, "KILL_SWITCH", "false")
    _imposta(matrice, "MODALITA_TEST", "false")
    _imposta(matrice, "INVII_REALI_ABILITATI", "true")

    config = carica_configurazione(matrice)

    assert config.invio_reale_consentito(consenso_esterno=False) is False
    assert config.invio_reale_consentito(consenso_esterno=True) is True


def test_rifiuta_chiavi_duplicate_sconosciute_e_saluto_alterato() -> None:
    matrice = _matrice_config()
    matrice.append(list(matrice[1]))
    with pytest.raises(ErroreConfigurazioneRuntime, match="duplicata"):
        carica_configurazione(matrice)

    matrice = _matrice_config()
    matrice[1][0] = "SCONOSCIUTA"
    with pytest.raises(ErroreConfigurazioneRuntime, match="mancanti"):
        carica_configurazione(matrice)

    matrice = _matrice_config()
    _imposta(matrice, "SALUTO_EMAIL", "Salve {{nome}}")
    with pytest.raises(ErroreConfigurazioneRuntime, match="SALUTO_EMAIL"):
        carica_configurazione(matrice)


def test_rifiuta_limiti_fuori_intervallo() -> None:
    matrice = _matrice_config()
    _imposta(matrice, "LIMITE_INVII_PER_ESECUZIONE", "10000")
    with pytest.raises(ErroreConfigurazioneRuntime, match="compreso"):
        carica_configurazione(matrice)
