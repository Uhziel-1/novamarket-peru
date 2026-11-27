"""
Lanzador local con 1 clic para NovaMarket Perú.
Usa el puerto poco común 38420 (o el siguiente libre) en 127.0.0.1 para no chocar con puertos ocupados como 8000,
y sirve tanto la interfaz web como la API REST desde el mismo puerto.
"""

import os
import socket
import sys
import threading
import webbrowser
import uvicorn


def _find_free_port(host: str, preferred: int, span: int = 20) -> int:
    for candidate in range(preferred, preferred + span):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            if sock.connect_ex((host, candidate)) != 0:
                return candidate
    return preferred


def main() -> None:
    host = "127.0.0.1"
    preferred = int(os.environ.get("PORT", "38420"))
    port = _find_free_port(host, preferred)
    url = f"http://{host}:{port}"
    if "--no-browser" not in sys.argv:
        threading.Timer(1.4, lambda: webbrowser.open(url)).start()
    print(f"\n[NovaMarket Perú] Web App + Backend FastAPI activos en: {url}")
    print(f"[NovaMarket Perú] Documentación API (Swagger): {url}/docs")
    print("[NovaMarket Perú] Pulsa Ctrl + C en esta ventana para detener.\n")
    uvicorn.run("app.main:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    main()
