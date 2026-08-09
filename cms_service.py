"""Importa el Excel CMS, valida y actualiza atómicamente la base JSON."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from openpyxl import load_workbook

from schema import (
    LOCATION_HEADERS, LOCATION_MAP, METRIC_HEADERS, METRIC_MAP,
    NUMBER_FIELDS, PERCENT_FIELDS,
)


class CMSValidationError(ValueError):
    def __init__(self, errors: list[str]):
        super().__init__("; ".join(errors))
        self.errors = errors


def _clean(value: Any) -> Any:
    if isinstance(value, str):
        value = value.strip()
        return value if value else None
    return value


def _serialize(value: Any) -> Any:
    value = _clean(value)
    if isinstance(value, (date, datetime)):
        return value.date().isoformat() if isinstance(value, datetime) else value.isoformat()
    return value


def _read_sheet(ws, expected_headers: list[str]) -> list[dict[str, Any]]:
    headers = [_clean(cell.value) for cell in ws[1]]
    missing = [header for header in expected_headers if header not in headers]
    if missing:
        raise CMSValidationError([f"{ws.title}: faltan columnas: {', '.join(missing)}"])
    positions = {header: headers.index(header) for header in expected_headers}
    rows = []
    for row_number, cells in enumerate(ws.iter_rows(min_row=2, values_only=True), 2):
        record = {header: _serialize(cells[index] if index < len(cells) else None) for header, index in positions.items()}
        if any(value is not None for value in record.values()):
            record["_row"] = row_number
            rows.append(record)
    return rows


def _to_float(value: Any, label: str, errors: list[str], allow_none: bool = True) -> float | None:
    value = _clean(value)
    if value is None and allow_none:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        errors.append(f"{label}: debe ser numérico")
        return None


def workbook_to_payload(path: str | Path) -> dict[str, Any]:
    wb = load_workbook(path, data_only=True, read_only=True)
    errors: list[str] = []
    required_sheets = {"Ubicaciones", "Indicadores"}
    if not required_sheets.issubset(wb.sheetnames):
        missing = sorted(required_sheets.difference(wb.sheetnames))
        raise CMSValidationError([f"Faltan pestañas: {', '.join(missing)}"])

    locations = _read_sheet(wb["Ubicaciones"], LOCATION_HEADERS)
    metrics = _read_sheet(wb["Indicadores"], METRIC_HEADERS)

    location_by_cc: dict[str, dict[str, Any]] = {}
    for row in locations:
        cc = str(row.get("CC") or "").strip()
        label = f"Ubicaciones fila {row['_row']}"
        if not cc:
            errors.append(f"{label}: CC es obligatorio")
            continue
        if cc in location_by_cc:
            errors.append(f"{label}: CC duplicado {cc}")
            continue
        if not row.get("Nombre Tienda"):
            errors.append(f"{label}: Nombre Tienda es obligatorio")
        lat = _to_float(row.get("Latitud"), f"{label} Latitud", errors, False)
        lng = _to_float(row.get("Longitud"), f"{label} Longitud", errors, False)
        if lat is not None and not (-90 <= lat <= 90):
            errors.append(f"{label}: Latitud fuera de rango")
        if lng is not None and not (-180 <= lng <= 180):
            errors.append(f"{label}: Longitud fuera de rango")
        row["Latitud"], row["Longitud"] = lat, lng
        location_by_cc[cc] = row

    metric_by_cc: dict[str, dict[str, Any]] = {}
    for row in metrics:
        cc = str(row.get("CC") or "").strip()
        label = f"Indicadores fila {row['_row']}"
        if not cc:
            errors.append(f"{label}: CC es obligatorio")
            continue
        if cc in metric_by_cc:
            errors.append(f"{label}: CC duplicado {cc}")
            continue
        metric_by_cc[cc] = row

    missing_metrics = sorted(set(location_by_cc).difference(metric_by_cc))
    orphan_metrics = sorted(set(metric_by_cc).difference(location_by_cc))
    if missing_metrics:
        errors.append("CC sin indicadores: " + ", ".join(missing_metrics[:12]))
    if orphan_metrics:
        errors.append("Indicadores sin ubicación: " + ", ".join(orphan_metrics[:12]))

    stores = []
    for cc, location in location_by_cc.items():
        merged: dict[str, Any] = {}
        for header, field in LOCATION_MAP.items():
            merged[field] = location.get(header)
        metric = metric_by_cc.get(cc, {})
        for header, field in METRIC_MAP.items():
            if field != "cc":
                merged[field] = metric.get(header)
        merged["cc"] = cc
        active = merged.get("active")
        merged["active"] = str(active).strip().lower() not in {"no", "false", "0", "inactiva"}
        for field in NUMBER_FIELDS | PERCENT_FIELDS:
            if field in {"latitude", "longitude"}:
                continue
            merged[field] = _to_float(merged.get(field), f"CC {cc} {field}", errors)
        stores.append(merged)

    if errors:
        raise CMSValidationError(errors)

    stores.sort(key=lambda item: (str(item.get("dm") or ""), str(item.get("store_name") or "")))
    return {
        "metadata": {
            "schema_version": 2,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "source": "Excel CMS",
            "store_count": len(stores),
        },
        "stores": stores,
    }


def update_database(workbook_path: str | Path, database_path: str | Path) -> dict[str, Any]:
    payload = workbook_to_payload(workbook_path)
    database_path = Path(database_path)
    database_path.parent.mkdir(parents=True, exist_ok=True)
    if database_path.exists():
        backup_dir = database_path.parent / "backups"
        backup_dir.mkdir(exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        shutil.copy2(database_path, backup_dir / f"stores_{stamp}.json")
    fd, temporary = tempfile.mkstemp(prefix="stores_", suffix=".json", dir=database_path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
        os.replace(temporary, database_path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return payload
