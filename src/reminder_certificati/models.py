from __future__ import annotations

from dataclasses import dataclass
from datetime import date


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
        """Nome, letto direttamente dalla relativa colonna di Operativo."""

        return self.nome.strip()

    @property
    def nome_completo(self) -> str:
        """Nominativo completo ricomposto dalle colonne nome e cognome."""

        return " ".join(parte for parte in (self.nome.strip(), self.cognome.strip()) if parte)


@dataclass(frozen=True, slots=True)
class CandidatoNotifica:
    """Notifica che sarebbe inviata in una successiva fase SMTP."""

    arbitro: Arbitro
    tipo: str
    giorni_residui: int
    notification_id: str
