from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path
from typing import Any, Mapping

from .rules import trova_candidati
from .validation import SchemaError, valida_righe


def _parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("usa il formato YYYY-MM-DD") from exc


def _load_rows(path: Path) -> list[Mapping[str, Any]]:
    raw: Any = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError("il file di input deve contenere una lista JSON")

    rows: list[Mapping[str, Any]] = []
    for index, item in enumerate(raw, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"riga {index}: atteso un oggetto JSON")
        rows.append(item)
    return rows


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
        esito = valida_righe(_load_rows(args.input), prima_riga_dati=1)
        candidati = trova_candidati(
            esito.arbitri,
            oggi=args.today,
            giorni_preavviso=args.days,
        )
    except (OSError, ValueError, SchemaError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Errore di input: {exc}") from exc

    output = {
        "mode": "dry-run",
        "today": args.today.isoformat(),
        "days_before_expiry": args.days,
        "input_row_count": esito.righe_totali,
        "valid_record_count": len(esito.arbitri),
        "ignored_empty_row_count": esito.righe_vuote_ignorate,
        "anomaly_count": len(esito.anomalie),
        "anomalies": [
            {
                "row": item.numero_riga,
                "code": item.codice,
                "field": item.campo,
                "id_arbitro": item.id_arbitro,
                "message": item.messaggio,
            }
            for item in esito.anomalie
        ],
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
