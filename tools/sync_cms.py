"""Sincroniza el Excel CMS con JSON y CSV; útil localmente y en GitHub Actions."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from cms_service import CMSValidationError, synchronize_outputs  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Sincroniza CMS→stores.json/data.csv")
    parser.add_argument("--check", action="store_true", help="No escribe; falla si hay archivos desactualizados")
    args = parser.parse_args()
    try:
        payload, changed = synchronize_outputs(
            ROOT / "cms" / "Mapa_CentroNorte_CMS.xlsx",
            ROOT / "data" / "stores.json",
            ROOT / "data.csv",
            dry_run=args.check,
        )
    except CMSValidationError as exc:
        print("CMS inválido:")
        for error in exc.errors:
            print(f"- {error}")
        return 2
    if changed:
        action = "Desactualizados" if args.check else "Actualizados"
        print(f"{action}: {', '.join(Path(item).name for item in changed)}")
        return 1 if args.check else 0
    print(f"CMS sincronizado: {len(payload['stores'])} tiendas; sin cambios pendientes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

