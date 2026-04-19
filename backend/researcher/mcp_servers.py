"""
Configuraciones del servidor MCP para el Alex Researcher
"""
from agents.mcp import MCPServerStdio


def create_playwright_mcp_server(timeout_seconds=60):
    """Crea una instancia de servidor MCP Playwright para navegación web.
    
    Args:
        timeout_seconds: Tiempo de espera de la sesión cliente en segundos (por defecto: 60)
        
    Returns:
        Instancia de MCPServerStdio configurada para Playwright
    """
    # Argumentos base
    args = [
        "@playwright/mcp@latest",
        "--headless",
        "--isolated", 
        "--no-sandbox",
        "--ignore-https-errors",
        "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36"
    ]
    
    # Añade la ruta del ejecutable en entorno Docker
    import os
    import glob
    if os.path.exists("/.dockerenv") or os.environ.get("AWS_EXECUTION_ENV"):
        # Busca dinámicamente el ejecutable de Chrome instalado
        chrome_paths = glob.glob("/root/.cache/ms-playwright/chromium-*/chrome-linux/chrome")
        if chrome_paths:
            # Usa la primera (debería haber solo una) instalación de Chrome encontrada
            chrome_path = chrome_paths[0]
            print(f"DEBUG: Chrome encontrado en: {chrome_path}")
            args.extend(["--executable-path", chrome_path])
        else:
            # Alternativa si glob no encuentra la ruta
            print("DEBUG: Chrome no encontrado mediante glob, usando ruta alternativa")
            args.extend(["--executable-path", "/root/.cache/ms-playwright/chromium-1187/chrome-linux/chrome"])
    
    params = {
        "command": "npx",
        "args": args
    }
    
    return MCPServerStdio(params=params, client_session_timeout_seconds=timeout_seconds)