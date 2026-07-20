from __future__ import annotations

_CATEGORIE_ESCLUSE_CERTIFICATO = (
    "benemerito",
    "osservatore",
    "fuori quadro",
    "decaduto",
    "non attivo",
)


def richiede_certificato_medico_per_categoria(
    *,
    qualifica: str,
    abilitazione: str,
) -> bool:
    """Indica se qualifica e abilitazione richiedono il certificato medico."""

    categoria = " ".join(
        parte.strip().casefold()
        for parte in (qualifica, abilitazione)
        if parte.strip()
    )
    return not any(
        categoria_esclusa in categoria
        for categoria_esclusa in _CATEGORIE_ESCLUSE_CERTIFICATO
    )
