"""Esquema canónico del CMS Centro Norte."""

LOCATION_HEADERS = [
    "CC", "Nombre Tienda", "DM", "Fecha Apertura", "Municipio", "Cobertura",
    "Formato", "Formato Comercial", "Tier", "Latitud", "Longitud", "Activa",
]

METRIC_HEADERS = [
    "CC", "Corte YTD", "Rolling", "TPLH", "IPLH", "Labor", "Dif Labor",
    "Ventas MXN", "Dif Ppto", "OMT", "NPS", "Conexión", "Bebida", "CTC",
    "Costo", "Dif Costo", "EBITDA", "Dif EBITDA", "DT Time", "Tiempo DT AA",
]

LOCATION_MAP = {
    "CC": "cc",
    "Nombre Tienda": "store_name",
    "DM": "dm",
    "Fecha Apertura": "opening_date",
    "Municipio": "municipality",
    "Cobertura": "coverage",
    "Formato": "format",
    "Formato Comercial": "commercial_format",
    "Tier": "tier",
    "Latitud": "latitude",
    "Longitud": "longitude",
    "Activa": "active",
}

METRIC_MAP = {
    "CC": "cc",
    "Corte YTD": "cutoff_ytd",
    "Rolling": "rolling_pct",
    "TPLH": "tplh",
    "IPLH": "iplh",
    "Labor": "labor_pct",
    "Dif Labor": "labor_variance_pct",
    "Ventas MXN": "sales_mxn",
    "Dif Ppto": "budget_variance_pct",
    "OMT": "omt",
    "NPS": "nps",
    "Conexión": "connection_pct",
    "Bebida": "beverage_pct",
    "CTC": "ctc_pct",
    "Costo": "cost_pct",
    "Dif Costo": "cost_variance_pct",
    "EBITDA": "ebitda_pct",
    "Dif EBITDA": "ebitda_variance_pct",
    "DT Time": "dt_time",
    "Tiempo DT AA": "dt_time_aa",
}

PERCENT_FIELDS = {
    "rolling_pct", "labor_pct", "labor_variance_pct", "budget_variance_pct",
    "connection_pct", "beverage_pct", "ctc_pct", "cost_pct",
    "cost_variance_pct", "ebitda_pct", "ebitda_variance_pct",
}

NUMBER_FIELDS = {"tplh", "iplh", "sales_mxn", "omt", "nps", "latitude", "longitude"}

