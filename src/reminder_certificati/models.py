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
        Se anche il nominativo è vuoto restituisce una stringa vuota, che il
        compositore del messaggio rifiuterà con un errore di configurazione.
        """

        esplicito = (self.nome_saluto or "").strip()
        if esplicito:
            return esplicito

        parti = self.nome.strip().split()
        return parti[0] if parti else ""


@dataclass(frozen=True, slots=True)
class CandidatoNotifica:
    """Notifica che sarebbe inviata in una successiva fase SMTP."""

    arbitro: Arbitro
    tipo: str
    giorni_residui: int
    notification_id: str
