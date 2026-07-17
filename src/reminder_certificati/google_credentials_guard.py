"""Barriera contro chiavi JSON permanenti per l'accesso Google.

Il runtime accetta Application Default Credentials temporanee prodotte da
Workload Identity Federation. Una credenziale di tipo ``service_account`` è
invece una chiave privata permanente e viene rifiutata prima di costruire il
client Google.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping


class ErroreCredenzialiGoogle(RuntimeError):
    """Credenziali Google assenti, illeggibili o non conformi alla policy."""


def verifica_credenziali_google_temporanee(ambiente: Mapping[str, str]) -> None:
    """Verifica il file ADC indicato dall'ambiente senza esporne il contenuto.

    In GitHub Actions l'azione WIF crea un file JSON temporaneo di tipo
    ``external_account`` e valorizza ``GOOGLE_APPLICATION_CREDENTIALS``.
    Vengono rifiutate esplicitamente le chiavi ``service_account``.
    """

    percorso_raw = ambiente.get("GOOGLE_APPLICATION_CREDENTIALS", "").strip()
    if not percorso_raw:
        raise ErroreCredenzialiGoogle(
            "GOOGLE_APPLICATION_CREDENTIALS mancante: usa WIF/OIDC con credenziali temporanee"
        )

    percorso = Path(percorso_raw)
    try:
        dimensione = percorso.stat().st_size
    except OSError as exc:
        raise ErroreCredenzialiGoogle(
            "file ADC non disponibile; verifica l'autenticazione WIF/OIDC"
        ) from exc
    if dimensione <= 0 or dimensione > 128 * 1024:
        raise ErroreCredenzialiGoogle("file ADC vuoto o di dimensione non valida")

    try:
        payload = json.loads(percorso.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ErroreCredenzialiGoogle("file ADC illeggibile o non valido") from exc
    if not isinstance(payload, dict):
        raise ErroreCredenzialiGoogle("formato ADC non valido")

    tipo = str(payload.get("type", "")).strip()
    if tipo == "service_account":
        raise ErroreCredenzialiGoogle(
            "chiave JSON service account permanente vietata: configura WIF/OIDC"
        )
    if tipo != "external_account":
        raise ErroreCredenzialiGoogle(
            "tipo ADC non ammesso: sono consentite soltanto credenziali WIF/OIDC external_account"
        )

    audience = payload.get("audience")
    subject_token_type = payload.get("subject_token_type")
    credential_source = payload.get("credential_source")
    if not isinstance(audience, str) or not audience.strip():
        raise ErroreCredenzialiGoogle("credenziale WIF priva di audience")
    if not isinstance(subject_token_type, str) or not subject_token_type.strip():
        raise ErroreCredenzialiGoogle("credenziale WIF priva di subject_token_type")
    if not isinstance(credential_source, dict):
        raise ErroreCredenzialiGoogle("credenziale WIF priva di credential_source")
