"""Servidor Python ligero: mapa, directorio y actualización por Excel."""

from __future__ import annotations

import json
import mimetypes
import os
import tempfile
from email.parser import BytesParser
from email.policy import default
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from cms_service import CMSValidationError, update_database

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "stores.json"
CMS_FILE = BASE_DIR / "cms" / "Mapa_CentroNorte_CMS.xlsx"
MAX_UPLOAD = 15 * 1024 * 1024


def load_database() -> dict:
    with DATA_FILE.open(encoding="utf-8") as handle:
        return json.load(handle)


def render_index(page: str) -> bytes:
    source = (BASE_DIR / "templates" / "index.html").read_text(encoding="utf-8")
    if page == "mapa":
        replacements = {"{{PAGE}}": "mapa", "{{PAGE_TITLE}}": "Mapa de tiendas", "{{CONTENT_VIEW}}": '<div id="map" aria-label="Mapa de tiendas"></div>'}
    else:
        replacements = {"{{PAGE}}": "directorio", "{{PAGE_TITLE}}": "Directorio operativo", "{{CONTENT_VIEW}}": '<div id="directory" class="directory"></div>'}
    for key, value in replacements.items():
        source = source.replace(key, value)
    return source.encode("utf-8")


def render_admin() -> bytes:
    database = load_database()
    source = (BASE_DIR / "templates" / "admin.html").read_text(encoding="utf-8")
    replacements = {
        "{{STORE_COUNT}}": str(database["metadata"]["store_count"]),
        "{{SCHEMA_VERSION}}": str(database["metadata"]["schema_version"]),
        "{{UPDATED_AT}}": str(database["metadata"]["updated_at"]),
    }
    for key, value in replacements.items():
        source = source.replace(key, value)
    return source.encode("utf-8")


def parse_multipart(content_type: str, body: bytes) -> dict[str, dict]:
    message = BytesParser(policy=default).parsebytes(
        f"Content-Type: {content_type}\r\nMIME-Version: 1.0\r\n\r\n".encode() + body
    )
    fields = {}
    if not message.is_multipart():
        return fields
    for part in message.iter_parts():
        name = part.get_param("name", header="content-disposition")
        if not name:
            continue
        fields[name] = {
            "filename": part.get_filename(),
            "content": part.get_payload(decode=True) or b"",
        }
    return fields


class AppHandler(BaseHTTPRequestHandler):
    server_version = "CentroNorteCMS/2.0"

    def log_message(self, fmt, *args):
        print(f"{self.address_string()} - {fmt % args}")

    def send_bytes(self, content: bytes, content_type: str, status: int = 200, disposition: str | None = None):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self' https://unpkg.com; style-src 'self' 'unsafe-inline' https://unpkg.com; img-src 'self' data: https://*.tile.openstreetmap.org; connect-src 'self';")
        if disposition:
            self.send_header("Content-Disposition", disposition)
        self.end_headers()
        self.wfile.write(content)

    def send_json(self, payload: dict, status: int = 200):
        self.send_bytes(json.dumps(payload, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8", status)

    def send_local_file(self, path: Path, download_name: str | None = None):
        if not path.is_file():
            self.send_error(404)
            return
        mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        disposition = f'attachment; filename="{download_name}"' if download_name else None
        self.send_bytes(path.read_bytes(), mime, disposition=disposition)

    def do_GET(self):
        route = urlparse(self.path).path
        if route == "/":
            self.send_response(302); self.send_header("Location", "/mapa"); self.end_headers(); return
        if route == "/mapa":
            self.send_bytes(render_index("mapa"), "text/html; charset=utf-8"); return
        if route == "/directorio":
            self.send_bytes(render_index("directorio"), "text/html; charset=utf-8"); return
        if route == "/administrar":
            self.send_bytes(render_admin(), "text/html; charset=utf-8"); return
        if route == "/api/stores":
            self.send_json(load_database()); return
        if route == "/descargar/cms":
            self.send_local_file(CMS_FILE, CMS_FILE.name); return
        if route == "/descargar/json":
            self.send_local_file(DATA_FILE, "stores.json"); return
        if route.startswith("/static/"):
            relative = route.removeprefix("/static/")
            candidate = (BASE_DIR / "static" / relative).resolve()
            static_root = (BASE_DIR / "static").resolve()
            if static_root not in candidate.parents:
                self.send_error(403); return
            self.send_local_file(candidate); return
        self.send_error(404)

    def do_POST(self):
        if urlparse(self.path).path != "/administrar/importar":
            self.send_error(404); return
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0 or length > MAX_UPLOAD:
            self.send_json({"ok": False, "errors": ["Archivo vacío o mayor a 15 MB."]}, 413); return
        fields = parse_multipart(self.headers.get("Content-Type", ""), self.rfile.read(length))
        token = fields.get("token", {}).get("content", b"").decode("utf-8", "replace").strip()
        expected = os.environ.get("CMS_ADMIN_TOKEN", "").strip()
        local = self.client_address[0] in {"127.0.0.1", "::1"}
        if (expected and token != expected) or (not expected and not local):
            self.send_json({"ok": False, "errors": ["Acceso no autorizado. Configura o envía CMS_ADMIN_TOKEN."]}, 403); return
        upload = fields.get("archivo", {})
        filename = upload.get("filename") or ""
        if not filename.lower().endswith(".xlsx"):
            self.send_json({"ok": False, "errors": ["El archivo debe tener extensión .xlsx."]}, 400); return
        with tempfile.NamedTemporaryFile(suffix=".xlsx") as temporary:
            temporary.write(upload.get("content", b"")); temporary.flush()
            try:
                payload = update_database(temporary.name, DATA_FILE)
            except CMSValidationError as exc:
                self.send_json({"ok": False, "errors": exc.errors}, 422); return
            except Exception:
                self.send_json({"ok": False, "errors": ["El archivo no es un Excel válido."]}, 400); return
        self.send_json({"ok": True, "message": f"Base actualizada: {len(payload['stores'])} tiendas.", "metadata": payload["metadata"]})


def create_server(host: str = "127.0.0.1", port: int = 8000) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((host, port), AppHandler)


if __name__ == "__main__":
    server = create_server()
    print("Centro Norte CMS: http://127.0.0.1:8000")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
