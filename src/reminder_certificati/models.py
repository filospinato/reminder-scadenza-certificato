from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class Arbitro:
    """Dati minimi necessari per valutare una scadenza."""

    id_arbitro: str
    nome: str
    email: str
    scadenza_certificato: date
    attivo: bool = True
    nome_saluto: str | None = None

    @property
    def nome_per_saluto(self) -> str:
        """Nome da usare nell'apertura della mail.

        Quando la sorgente espone un nome breve esplicito viene preferito.
        In assenza di quel dato, usa la prima parola del nominativo completo.
        """

        esplicito = (self.nome_saluto or "").strip()
        if esplicito:
            return esplicito
        return self.nome.strip().split(maxsplit=1)[0]


@dataclass(frozen=True, slots=True)
class CandidatoNotifica:
    """Notifica che sarebbe inviata in una successiva fase SMTP."""

    arbitro: Arbitro
    tipo: str
    giorni_residui: int
    notification_id: str
