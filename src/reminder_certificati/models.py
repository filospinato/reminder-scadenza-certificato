from __future__ import annotations

from dataclasses import dataclass
from datetime import date


def _normalizza_nome_proprio(valore: str) -> str:
    """Uniforma spazi e maiuscole di nomi e cognomi provenienti da Operativo."""

    return " ".join(valore.split()).title()


@dataclass(frozen=True, slots=True)
class Arbitro:
    """Dati minimi di una riga valida di Operativo."""

    id_arbitro: str
    nome: str
    cognome: str
    email: str
    scadenza_certificato: date
    attivo: bool = True
    qualifica: str = ""
    abilitazione: str = ""

    @property
    def nome_per_saluto(self) -> str:
        """Nome leggibile per i template, anche se Operativo usa il maiuscolo."""

        return _normalizza_nome_proprio(self.nome)

    @property
    def cognome_per_template(self) -> str:
        """Cognome leggibile per i template, anche se Operativo usa il maiuscolo."""

        return _normalizza_nome_proprio(self.cognome)

    @property
    def nome_completo(self) -> str:
        """Nominativo completo normalizzato dalle colonne nome e cognome."""

        return " ".join(
            parte
            for parte in (self.nome_per_saluto, self.cognome_per_template)
            if parte
        )


@dataclass(frozen=True, slots=True)
class CandidatoNotifica:
    """Notifica che sarebbe inviata in una successiva fase SMTP."""

    arbitro: Arbitro
    tipo: str
    giorni_residui: int
    notification_id: str
