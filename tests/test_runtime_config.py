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

    assert config.automazione_attiva is False
    assert config.destinatario_override is None
    assert config.invio_reale_consentito(consenso_esterno=True) is False


def test_dry_run_puo_essere_preparato_senza_override_smtp() -> None:
    matrice = _matrice_config()
    _imposta(matrice, "AUTOMAZIONE_ATTIVA", "true")

    config = carica_configurazione(matrice)

    assert config.elaborazione_consentita is True
    assert config.destinatario_override is None
    assert config.invio_reale_consentito(consenso_esterno=True) is False


def test_test_smtp_accetta_override_quando_configurato() -> None:
    matrice = _matrice_config()
    _imposta(matrice, "AUTOMAZIONE_ATTIVA", "true")
    _imposta(matrice, "DESTINATARIO_OVERRIDE", "test@example.invalid")

    config = carica_configurazione(matrice)

    assert config.elaborazione_consentita is True
    assert config.destinatario_override == "test@example.invalid"
    assert config.invio_reale_consentito(consenso_esterno=True) is False


def test_invii_reali_richiedono_configurazione_coerente_e_consenso_esterno() -> None:
    matrice = _matrice_config()
    _imposta(matrice, "AUTOMAZIONE_ATTIVA", "true")
    _imposta(matrice, "INVII_REALI_ABILITATI", "true")

    config = carica_configurazione(matrice)

    assert config.invio_reale_consentito(consenso_esterno=False) is False
    assert config.invio_reale_consentito(consenso_esterno=True) is True


def test_rifiuta_invii_reali_con_automazione_disattivata() -> None:
    matrice = _matrice_config()
    _imposta(matrice, "INVII_REALI_ABILITATI", "true")

    with pytest.raises(ErroreConfigurazioneRuntime, match="AUTOMAZIONE_ATTIVA"):
        carica_configurazione(matrice)


def test_rifiuta_chiavi_duplicate_e_sconosciute() -> None:
    matrice = _matrice_config()
    matrice.append(list(matrice[1]))
    with pytest.raises(ErroreConfigurazioneRuntime, match="duplicata"):
        carica_configurazione(matrice)

    matrice = _matrice_config()
    matrice[1][0] = "SCONOSCIUTA"
    with pytest.raises(ErroreConfigurazioneRuntime, match="mancanti"):
        carica_configurazione(matrice)


def test_accetta_descrizioni_modificate_e_corpo_libero() -> None:
    matrice = _matrice_config()
    matrice[1][3] = "Descrizione modificata dall'amministratore"
    matrice[1][4] = "testo libero non funzionale"
    _imposta(matrice, "CORPO_EMAIL", "Il certificato scade il {{data_scadenza}}.")

    config = carica_configurazione(matrice)

    assert config.email.corpo.startswith("Il certificato")


def test_rifiuta_corpo_vuoto_e_limiti_fuori_intervallo() -> None:
    matrice = _matrice_config()
    _imposta(matrice, "CORPO_EMAIL", "")
    with pytest.raises(ErroreConfigurazioneRuntime, match="CORPO_EMAIL"):
        carica_configurazione(matrice)

    matrice = _matrice_config()
    _imposta(matrice, "LIMITE_INVII_PER_ESECUZIONE", "10000")
    with pytest.raises(ErroreConfigurazioneRuntime, match="compreso"):
        carica_configurazione(matrice)
