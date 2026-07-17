from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path
from typing import Any

from .models import Arbitro
from .rules import trova_candidati


def _parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("usa il formato YYYY-MM-DD") from exc


def _load_arbitri(path: Path) -> list[Arbitro]:
    raw: Any = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError("il file di input deve contenere una lista JSON")

    records: list[Arbitro] = []
    for index, item in enumerate(raw, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"riga {index}: atteso un oggetto JSON")
        try:
            records.append(
                Arbitro(
                    id_arbitro=str(item["id_arbitro"]),
                    nome=str(item["nome"]),
                    email=str(item["email"]),
                    scadenza_certificato=date.fromisoformat(
                        str(item["scadenza_certificato"])
                    ),
                    attivo=bool(item.get("attivo", True)),
                )
            )
        except (KeyError, ValueError) as exc:
            raise ValueError(f"riga {index}: dati mancanti o non validi") from exc
    return records


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Individua in modalità dry-run i certificati in scadenza."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("examples/arbitri.json"),
        help="file JSON anonimo da elaborare",
    )
    parser.add_argument(
        "--today",
        type=_parse_date,
        default=date.today(),
        help="data di riferimento YYYY-MM-DD",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="giorni di preavviso inclusivi",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        candidati = trova_candidati(
            _load_arbitri(args.input),
            oggi=args.today,
            giorni_preavviso=args.days,
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Errore di input: {exc}") from exc

    output = {
        "mode": "dry-run",
        "today": args.today.isoformat(),
        "days_before_expiry": args.days,
        "candidate_count": len(candidati),
        "candidates": [
            {
                "notification_id": item.notification_id,
                "id_arbitro": item.arbitro.id_arbitro,
                "nome": item.arbitro.nome,
                "email": item.arbitro.email,
                "scadenza_certificato": item.arbitro.scadenza_certificato.isoformat(),
                "giorni_residui": item.giorni_residui,
            }
            for item in candidati
        ],
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
