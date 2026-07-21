import pytest

from reminder_certificati.admin_schema import crea_schema_amministrativo
from reminder_certificati.runtime_config import (
    LIMITE_INVII_PER_ESECUZIONE,
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
    assert config.limite_invii_per_esecuzione == 10
    assert config.invio_reale_consentito(consenso_esterno=True) is False


def test_controllo_puo_funzionare_con_invii_automatici_spenti() -> None:
    config = carica_configurazione(_matrice_config())

    assert config.elaborazione_consentita is False
    assert config.destinatario_override is None


def test_test_smtp_accetta_override_anche_con_automazione_spenta() -> None:
    matrice = _matrice_config()
    _imposta(matrice, "DESTINATARIO_OVERRIDE", "test@example.invalid")

    config = carica_configurazione(matrice)

    assert config.automazione_attiva is False
    assert config.destinatario_override == "test@example.invalid"


def test_produzione_richiede_il_solo_interruttore_del_foglio() -> None:
    matrice = _matrice_config()
    _imposta(matrice, "INVIO_AUTOMATICO_ATTIVO", "true")

    config = carica_configurazione(matrice)

    assert config.invio_reale_consentito(consenso_esterno=False) is False
    assert config.invio_reale_consentito(consenso_esterno=True) is True


def test_limite_interno_non_e_una_chiave_configurabile() -> None:
    matrice = _matrice_config()
    chiavi = {riga[0] for riga in matrice[1:]}

    assert "LIMITE_INVII_PER_ESECUZIONE" not in chiavi
    assert LIMITE_INVII_PER_ESECUZIONE == 10


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
    matrice[1][2] = "Descrizione modificata dall'amministratore"
    _imposta(matrice, "CORPO_EMAIL", "Il certificato scade il {{data_scadenza}}.")

    config = carica_configurazione(matrice)

    assert config.email.corpo.startswith("Il certificato")


def test_rifiuta_corpo_vuoto_e_giorni_fuori_intervallo() -> None:
    matrice = _matrice_config()
    _imposta(matrice, "CORPO_EMAIL", "")
    with pytest.raises(ErroreConfigurazioneRuntime, match="CORPO_EMAIL"):
        carica_configurazione(matrice)

    matrice = _matrice_config()
    _imposta(matrice, "GIORNI_PREAVVISO", "10000")
    with pytest.raises(ErroreConfigurazioneRuntime, match="compreso"):
        carica_configurazione(matrice)


@pytest.mark.parametrize(
    ("chiave", "valore"),
    [
        ("OGGETTO_EMAIL", "Promemoria {{campo_sconosciuto}}"),
        ("CORPO_EMAIL", "Certificato in scadenza {{data_scadenza"),
        ("FIRMA_TESTO", "Firma }} non valida"),
    ],
)
def test_rifiuta_template_non_validi_prima_di_leggere_i_candidati(
    chiave: str,
    valore: str,
) -> None:
    matrice = _matrice_config()
    _imposta(matrice, chiave, valore)

    with pytest.raises(ErroreConfigurazioneRuntime, match="template email non valido"):
        carica_configurazione(matrice)
