import pytest

from reminder_certificati.google_auth import (
    ConfigurazioneGoogleWif,
    ErroreConfigurazioneGoogle,
)


AMBIENTE_VALIDO = {
    "GCP_WORKLOAD_IDENTITY_PROVIDER": (
        "projects/123456789/locations/global/"
        "workloadIdentityPools/github-cia/providers/github-actions"
    ),
    "GCP_SERVICE_ACCOUNT": (
        "reminder-certificati@cia-lazio-reminder.iam.gserviceaccount.com"
    ),
}


def test_accetta_configurazione_wif_canonica() -> None:
    configurazione = ConfigurazioneGoogleWif.da_ambiente(AMBIENTE_VALIDO)

    assert configurazione.workload_identity_provider.endswith("github-actions")
    assert configurazione.service_account.startswith("reminder-certificati@")


@pytest.mark.parametrize(
    ("nome", "valore"),
    [
        ("GCP_WORKLOAD_IDENTITY_PROVIDER", ""),
        ("GCP_SERVICE_ACCOUNT", ""),
        ("GCP_WORKLOAD_IDENTITY_PROVIDER", "projects/demo/provider"),
        ("GCP_SERVICE_ACCOUNT", "utente@example.com"),
    ],
)
def test_rifiuta_configurazione_mancante_o_malformata(
    nome: str, valore: str
) -> None:
    ambiente = dict(AMBIENTE_VALIDO)
    ambiente[nome] = valore

    with pytest.raises(ErroreConfigurazioneGoogle):
        ConfigurazioneGoogleWif.da_ambiente(ambiente)


@pytest.mark.parametrize(
    "provider",
    [
        (
            "projects/123456789/locations/global/"
            "workloadIdentityPools/gcp-pool/providers/github-actions"
        ),
        (
            "projects/123456789/locations/global/"
            "workloadIdentityPools/github-cia/providers/gcp-provider"
        ),
    ],
)
def test_rifiuta_prefisso_wif_riservato(provider: str) -> None:
    ambiente = dict(AMBIENTE_VALIDO)
    ambiente["GCP_WORKLOAD_IDENTITY_PROVIDER"] = provider

    with pytest.raises(ErroreConfigurazioneGoogle, match="prefisso riservato"):
        ConfigurazioneGoogleWif.da_ambiente(ambiente)


@pytest.mark.parametrize(
    "nome_chiave",
    [
        "GOOGLE_SERVICE_ACCOUNT_JSON",
        "GOOGLE_APPLICATION_CREDENTIALS_JSON",
        "GCP_SERVICE_ACCOUNT_KEY",
    ],
)
def test_rifiuta_chiavi_json_permanenti(nome_chiave: str) -> None:
    ambiente = dict(AMBIENTE_VALIDO)
    ambiente[nome_chiave] = "{\"type\": \"service_account\"}"

    with pytest.raises(ErroreConfigurazioneGoogle, match="non consentite"):
        ConfigurazioneGoogleWif.da_ambiente(ambiente)


def test_segnala_la_chiave_permanente_anche_se_manca_la_configurazione_wif() -> None:
    with pytest.raises(ErroreConfigurazioneGoogle, match="non consentite"):
        ConfigurazioneGoogleWif.da_ambiente(
            {"GOOGLE_SERVICE_ACCOUNT_JSON": "{\"type\": \"service_account\"}"}
        )
