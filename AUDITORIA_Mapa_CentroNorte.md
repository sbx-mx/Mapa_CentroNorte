# Auditoría y mejora — Mapa Centro Norte

## Resultado ejecutivo

La fuente contenía 72 tiendas, 30 columnas, 0 CC duplicados y 0 coordenadas inválidas. La visualización cumplía su función básica, pero el diseño monolítico y el CSV directo impedían administrar, validar y versionar las actualizaciones con seguridad.

## Hallazgos corregidos

| Prioridad | Hallazgo original | Mejora v2 |
|---|---|---|
| Alta | Datos del CSV insertados como HTML sin escape | Escape explícito antes de construir popups y filas |
| Alta | No había backend ni validación | API Python y validador de Excel con errores por fila |
| Alta | Actualizar el CSV podía dejar la base inconsistente | JSON tipado, respaldo y reemplazo atómico |
| Media | HTML, CSS y JavaScript en un solo archivo | Separación por plantillas y archivos estáticos |
| Media | Dependencia de PapaParse y CSV con BOM/espacios | JSON consolidado y normalización durante la migración |
| Media | Colores dependían de nombres exactos | Paleta dinámica por DM |
| Media | Sin navegación ni directorio | Rutas Mapa, Directorio y Administrar |
| Media | Sin control de carga | Token configurable; sin token solo localhost |
| Media | Sin pruebas ni control de calidad en repositorio | Pruebas de rutas/carga y workflow de GitHub Actions |
| Baja | Leaflet sin versión fija | Leaflet 1.9.4 con integridad SRI |

## Decisiones de arquitectura

- `data/stores.json` es la única base consumida por el mapa.
- El Excel separa información estable (`Ubicaciones`) de indicadores de corte (`Indicadores`) y las junta por CC.
- La aplicación no escribe parcialmente: primero valida todo, luego respalda y finalmente reemplaza.
- La versión original se conserva; v2 es un paquete independiente y reversible.

## Recomendaciones siguientes

- Desplegar detrás de HTTPS con un servidor WSGI y `CMS_ADMIN_TOKEN`.
- Definir retención y cifrado de respaldos si el proyecto incorpora datos sensibles.
- Agregar autenticación corporativa si habrá varios editores.
- Automatizar pruebas y revisión de dependencias en GitHub Actions antes de publicar.
