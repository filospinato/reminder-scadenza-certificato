import json
from pathlib import Path

import pytest

from reminder_certificati.google_credentials_guard import (
    ErroreCredenzialiGoogle,
    verifica_credenziali_google_temporanee,
)


def _scrivi(tmp_path: Path, payload: object) -> str:
    percorso = tmp_path / "adc.json"
    percorso.write_text(json.dumps(payload), encoding="utf-8")
    return str(percorso)


def test_accetta_credenziale_wif_external_account(tmp_path: Path) -> None:
    percorso = _scrivi(
        tmp_path,
        {
            "type": "external_account",
            "audience": "//iam.googleapis.com/projects/123/locations/global/workloadIdentityPools/pool/providers/provider",
            "subject_token_type": "urn:ietf:params:oauth:token-type:jwt",
            "credential_source": {"url": "https://example.invalid/token"},
        },
    )

    verifica_credenziali_google_temporanee(
        {"GOOGLE_APPLICATION_CREDENTIALS": percorso}
    )


def test_rifiuta_chiave_service_account_permanente(tmp_path: Path) -> None:
    percorso = _scrivi(
        tmp_path,
        {
            "type": "service_account",
            "private_key": "-----BEGIN PRIVATE KEY-----\nsynthetic\n-----END PRIVATE KEY-----\n",
            "client_email": "synthetic@example.invalid",
        },
    )

    with pytest.raises(ErroreCredenzialiGoogle, match="permanente vietata"):
        verifica_credenziali_google_temporanee(
            {"GOOGLE_APPLICATION_CREDENTIALS": percorso}
        )


def test_rifiuta_adc_assenti_o_malformate(tmp_path: Path) -> None:
    with pytest.raises(ErroreCredenzialiGoogle, match="mancante"):
        verifica_credenziali_google_temporanee({})

    percorso = tmp_path / "adc.json"
    percorso.write_text("non-json", encoding="utf-8")
    with pytest.raises(ErroreCredenzialiGoogle, match="illeggibile"):
        verifica_credenziali_google_temporanee(
            {"GOOGLE_APPLICATION_CREDENTIALS": str(percorso)}
        )


def test_rifiuta_external_account_incompleto(tmp_path: Path) -> None:
    percorso = _scrivi(tmp_path, {"type": "external_account"})

    with pytest.raises(ErroreCredenzialiGoogle, match="audience"):
        verifica_credenziali_google_temporanee(
            {"GOOGLE_APPLICATION_CREDENTIALS": percorso}
        )
