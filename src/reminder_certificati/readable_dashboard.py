"""Adatta le metriche tecniche a etichette comprensibili nel foglio."""

from __future__ import annotations

from dataclasses import dataclass, replace

from .monitoring import ArchivioDashboard, MetricheEsecuzione

_ETICHETTE_STATO = {
    "DISATTIVATO": "Invio automatico spento",
    "DRY_RUN_OK": "Controllo completato",
    "OK": "Esecuzione completata",
    "ATTENZIONE": "Attenzione richiesta",
    "REVISIONE_RICHIESTA": "Verifica manuale necessaria",
    "ERRORE": "Errore",
}


@dataclass(frozen=True, slots=True)
class DashboardLeggibile:
    archivio: ArchivioDashboard

    def aggiorna(self, metriche: MetricheEsecuzione) -> None:
        self.archivio.aggiorna(
            replace(
                metriche,
                stato_sistema=_ETICHETTE_STATO.get(
                    metriche.stato_sistema,
                    metriche.stato_sistema,
                ),
            )
        )
