"""Conversión única del CSV original al JSON tipado v2."""

import argparse
import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

MAP = {
    "CC Nombre":"store_name","CC":"cc","DM":"dm","Fecha de Apertura":"opening_date","Rolling":"rolling_pct","TPLH":"tplh","IPLH":"iplh","Labor":"labor_pct","Dif Labor%":"labor_variance_pct","Ventas":"sales_mxn","Dif ppto%":"budget_variance_pct","OMT #":"omt","NPS":"nps","Conexión":"connection_pct","Bebida":"beverage_pct","CTC":"ctc_pct","Costo":"cost_pct","Dif costo%":"cost_variance_pct","EBITDA":"ebitda_pct","Dif EBITDA %":"ebitda_variance_pct","DT Time":"dt_time","Tiempo DT AA":"dt_time_aa","Municipio o Delegación":"municipality","Cobertura":"coverage","Formato":"format","Formato - Comercial":"commercial_format","TIER":"tier","Corte YTD":"cutoff_ytd","Latitud":"latitude","Longitud":"longitude"
}
PCTS={"Rolling","Labor","Dif Labor%","Dif ppto%","Conexión","Bebida","CTC","Costo","Dif costo%","EBITDA","Dif EBITDA %"}
NUMS={"TPLH","IPLH","OMT #","NPS","Latitud","Longitud"}

def value(header, raw):
    raw=(raw or '').strip()
    if not raw or raw.lower().startswith('no hay'): return None
    if header in PCTS: return float(raw.replace('%','').replace(',',''))/100
    if header in NUMS: return float(raw.replace(',',''))
    if header=='Ventas':
        match=re.fullmatch(r'\$?([\d.]+)M',raw,re.I)
        return float(match.group(1))*1_000_000 if match else float(raw.replace('$','').replace(',',''))
    if header in {'Fecha de Apertura','Corte YTD'}:
        return datetime.strptime(raw,'%d/%m/%Y').date().isoformat()
    return raw

def main():
    parser = argparse.ArgumentParser(description="Migra el data.csv legado al JSON v2")
    parser.add_argument("source", type=Path, help="Ruta al data.csv original")
    parser.add_argument("--output", type=Path, default=ROOT / "data" / "stores.json")
    args = parser.parse_args()
    with args.source.open(encoding='utf-8-sig',newline='') as handle:
        rows=list(csv.DictReader(handle))
    stores=[]
    for row in rows:
        store={MAP[h]:value(h,row.get(h)) for h in MAP}
        store['cc']=str(row['CC']).strip()
        store['active']=True
        stores.append(store)
    stores.sort(key=lambda item:(item['dm'],item['store_name']))
    payload={'metadata':{'schema_version':2,'updated_at':datetime.now(timezone.utc).isoformat(),'source':'data.csv migrado','store_count':len(stores)},'stores':stores}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'{len(stores)} tiendas -> {args.output}')

if __name__ == '__main__':
    main()
