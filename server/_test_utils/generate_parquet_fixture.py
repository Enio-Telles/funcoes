"""Generate a small deterministic Parquet fixture used by integration tests.

This script is intentionally dependency-light and uses Polars (already required by the API).
"""

from __future__ import annotations

import sys
from pathlib import Path

import polars as pl


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python generate_parquet_fixture.py <output_parquet_path>")
        return 2

    output = Path(sys.argv[1]).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    # Must match expectations in server/python-api.test.ts
    df = pl.DataFrame(
        {
            "nfe_numero": ["1", "2", "3", "4", "5"],
            "cnpj_emitente": ["12345678000190"] * 5,
            "valor_total": [10.5, 20.0, 30.25, 40.0, 50.75],
        }
    )

    df.write_parquet(str(output))
    print(f"Fixture written: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
