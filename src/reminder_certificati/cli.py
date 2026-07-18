"""Compatibilità per il vecchio comando, senza elaborare o stampare record."""

from __future__ import annotations


def main() -> int:
    print(
        "Il comando storico non elabora più file con record. "
        "Usare reminder-certificati-runtime per dry-run e operazioni controllate."
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
