"""Configurazione sicura per l'autenticazione Google tramite WIF/OIDC.

Il modulo valida esclusivamente identificatori pubblici. Non crea credenziali,
non contatta Google Cloud e non accetta chiavi JSON permanenti.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Mapping


class ErroreConfigurazioneGoogle(ValueError):
    """Configurazione Google assente, ambigua o non sicura."""


_PROVIDER_RE = re.compile(
    r"^projects/(?P<project_number>[1-9][0-9]*)/locations/global/"
    r"workloadIdentityPools/(?P<pool>[a-z0-9-]{4,32})/providers/"
    r"(?P<provider>[a-z0-9-]{4,32})$"
)
_SERVICE_ACCOUNT_RE = re.compile(
    r"^[a-z][a-z0-9-]{4,28}[a-z0-9]@[a-z][a-z0-9-]{4,28}[a-z0-9]"
    r"\.iam\.gserviceaccount\.com$"
)


@dataclass(frozen=True, slots=True)
class ConfigurazioneGoogleWif:
    workload_identity_provider: str
    service_account: str

    @classmethod
    def da_ambiente(cls, ambiente: Mapping[str, str]) -> "ConfigurazioneGoogleWif":
        provider = ambiente.get("GCP_WORKLOAD_IDENTITY_PROVIDER", "").strip()
        service_account = ambiente.get("GCP_SERVICE_ACCOUNT", "").strip()

        if not provider:
            raise ErroreConfigurazioneGoogle(
                "GCP_WORKLOAD_IDENTITY_PROVIDER mancante"
            )
        if not service_account:
            raise ErroreConfigurazioneGoogle("GCP_SERVICE_ACCOUNT mancante")
        if not _PROVIDER_RE.fullmatch(provider):
            raise ErroreConfigurazioneGoogle(
                "GCP_WORKLOAD_IDENTITY_PROVIDER non ha il formato canonico"
            )
        if not _SERVICE_ACCOUNT_RE.fullmatch(service_account):
            raise ErroreConfigurazioneGoogle(
                "GCP_SERVICE_ACCOUNT non ha il formato canonico"
            )

        vietate = {
            "GOOGLE_SERVICE_ACCOUNT_JSON",
            "GOOGLE_APPLICATION_CREDENTIALS_JSON",
            "GCP_SERVICE_ACCOUNT_KEY",
        }
        presenti = sorted(nome for nome in vietate if ambiente.get(nome, "").strip())
        if presenti:
            raise ErroreConfigurazioneGoogle(
                "chiavi JSON permanenti non consentite: " + ", ".join(presenti)
            )

        return cls(
            workload_identity_provider=provider,
            service_account=service_account,
        )
