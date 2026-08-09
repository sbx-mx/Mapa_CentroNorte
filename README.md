# Centro Norte CMS v2

Versión optimizada del mapa ejecutivo. La base canónica es `data/stores.json`; el Excel CMS permite actualizarla sin editar código.

## Inicio rápido

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
python app.py
```

Abre `http://127.0.0.1:8000`. Navegación: **Mapa**, **Directorio** y **Administrar**.

## Actualizar la base

1. En Administrar, descarga `Mapa_CentroNorte_CMS.xlsx`.
2. Edita `Ubicaciones` e `Indicadores`; conserva el CC como llave única en ambas.
3. Carga el Excel. Python valida hojas, encabezados, CC duplicados, relación entre tablas y coordenadas.
4. Si todo es correcto, guarda un respaldo en `data/backups/` y reemplaza `stores.json` de forma atómica.

En un servidor configura `CMS_ADMIN_TOKEN` y escríbelo al cargar el archivo. Sin token, la actualización solo está permitida desde localhost.

## Despliegue

El servidor web usa la biblioteca estándar de Python; la única dependencia externa es `openpyxl` para leer Excel. El mapa usa teselas de OpenStreetMap y Leaflet 1.9.4, por lo que requiere conexión a internet. Para producción colócalo detrás de HTTPS/reverse proxy, usa un supervisor de procesos, define un token fuerte y establece una política de respaldo/retención.
