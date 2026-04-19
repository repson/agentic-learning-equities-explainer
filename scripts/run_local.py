#!/usr/bin/env python3
"""
Ejecuta tanto el frontend como el backend localmente para desarrollo.
Este script inicia el frontend de NextJS y el backend de FastAPI en paralelo.
"""

import os
import sys
import subprocess
import signal
import time
from pathlib import Path

# Seguimiento de los subprocesos para limpieza
processes = []

def cleanup(signum=None, frame=None):
    """Limpia todos los subprocesos al salir"""
    print("\n🛑 Apagando servicios...")
    for proc in processes:
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except:
            proc.kill()
    sys.exit(0)

# Registrar manejadores de limpieza
signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

def check_requirements():
    """Verifica si las herramientas requeridas están instaladas"""
    checks = []

    # Verificar Node.js
    try:
        result = subprocess.run(["node", "--version"], capture_output=True, text=True)
        node_version = result.stdout.strip()
        checks.append(f"✅ Node.js: {node_version}")
    except FileNotFoundError:
        checks.append("❌ Node.js no encontrado - por favor instala Node.js")

    # Verificar npm
    try:
        result = subprocess.run(["npm", "--version"], capture_output=True, text=True)
        npm_version = result.stdout.strip()
        checks.append(f"✅ npm: {npm_version}")
    except FileNotFoundError:
        checks.append("❌ npm no encontrado - por favor instala npm")

    # Verificar uv (que gestiona Python por nosotros)
    try:
        result = subprocess.run(["uv", "--version"], capture_output=True, text=True)
        uv_version = result.stdout.strip()
        checks.append(f"✅ uv: {uv_version}")
    except FileNotFoundError:
        checks.append("❌ uv no encontrado - por favor instala uv")

    print("\n📋 Verificación de prerrequisitos:")
    for check in checks:
        print(f"  {check}")

    # Salir si algún requisito crítico falta
    if any("❌" in check for check in checks):
        print("\n⚠️  Por favor instala las dependencias que faltan e intenta de nuevo.")
        sys.exit(1)

def check_env_files():
    """Verifica si existen los archivos de entorno"""
    project_root = Path(__file__).parent.parent

    root_env = project_root / ".env"
    frontend_env = project_root / "frontend" / ".env.local"

    missing = []

    if not root_env.exists():
        missing.append(".env (archivo base del proyecto)")
    if not frontend_env.exists():
        missing.append("frontend/.env.local")

    if missing:
        print("\n⚠️  Archivos de entorno faltantes:")
        for file in missing:
            print(f"  - {file}")
        print("\nPor favor crea estos archivos con la configuración requerida.")
        print("El archivo .env en la raíz debe tener todas las variables del backend de las Partes 1-7.")
        print("El archivo frontend/.env.local debe tener las claves de Clerk.")
        sys.exit(1)

    print("✅ Archivos de entorno encontrados")

def start_backend():
    """Inicia el backend FastAPI"""
    backend_dir = Path(__file__).parent.parent / "backend" / "api"

    print("\n🚀 Iniciando backend FastAPI...")

    # Verificar si las dependencias están instaladas
    if not (backend_dir / ".venv").exists() and not (backend_dir / "uv.lock").exists():
        print("  Instalando dependencias del backend...")
        subprocess.run(["uv", "sync"], cwd=backend_dir, check=True)

    # Iniciar el backend
    proc = subprocess.Popen(
        ["uv", "run", "main.py"],
        cwd=backend_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    processes.append(proc)

    # Esperar a que el backend se inicie
    print("  Esperando que el backend inicie...")
    for _ in range(30):  # 30 segundos de espera máxima
        try:
            import httpx
            response = httpx.get("http://localhost:8000/health")
            if response.status_code == 200:
                print("  ✅ Backend en ejecución en http://localhost:8000")
                print("     Documentación API: http://localhost:8000/docs")
                return proc
        except:
            time.sleep(1)

    print("  ❌ El backend no se pudo iniciar")
    cleanup()

def start_frontend():
    """Inicia el frontend NextJS"""
    frontend_dir = Path(__file__).parent.parent / "frontend"

    print("\n🚀 Iniciando frontend NextJS...")

    # Verificar si las dependencias están instaladas
    if not (frontend_dir / "node_modules").exists():
        print("  Instalando dependencias del frontend...")
        subprocess.run(["npm", "install"], cwd=frontend_dir, check=True)

    # Iniciar el frontend
    proc = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=frontend_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,  # Combina stderr con stdout
        text=True,
        bufsize=1
    )
    processes.append(proc)

    # Esperar a que el frontend se inicie
    print("  Esperando que el frontend inicie...")
    import httpx
    import select

    started = False
    for i in range(30):  # 30 segundos de espera máxima
        # Verifica la salida del proceso de forma no bloqueante
        if proc.stdout:
            ready, _, _ = select.select([proc.stdout], [], [], 0)
            if ready:
                line = proc.stdout.readline()
                if line:
                    print(f"    Frontend: {line.strip()}")
                    # El servidor de dev de NextJS imprime "Ready" cuando está listo
                    if "ready" in line.lower() or "compiled" in line.lower() or "started server" in line.lower():
                        started = True

        # También intentar conectar
        if started or i > 5:  # Empieza a comprobar luego de 5 segundos o cuando ve "ready"
            try:
                response = httpx.get("http://localhost:3000", timeout=1)
                print("  ✅ Frontend en ejecución en http://localhost:3000")
                return proc
            except httpx.ConnectError:
                pass  # El servidor no está listo aún
            except:
                # Cualquier otra respuesta significa que el servidor está arriba
                print("  ✅ Frontend en ejecución en http://localhost:3000")
                return proc

        time.sleep(1)

    print("  ❌ El frontend no se pudo iniciar")
    cleanup()

def monitor_processes():
    """Monitorea los procesos en ejecución y muestra su salida"""
    print("\n" + "="*60)
    print("🎯 Alex Asesor Financiero - Desarrollo Local")
    print("="*60)
    print("\n📍 Servicios:")
    print("  Frontend: http://localhost:3000")
    print("  Backend:  http://localhost:8000")
    print("  Documentación API: http://localhost:8000/docs")
    print("\n📝 Los logs aparecerán abajo. Pulsa Ctrl+C para detener.\n")
    print("="*60 + "\n")

    # Monitorea los procesos
    while True:
        for proc in processes:
            # Verifica si el proceso sigue corriendo
            if proc.poll() is not None:
                print(f"\n⚠️  ¡Un proceso se ha detenido inesperadamente!")
                cleanup()

            # Lee cualquier salida disponible
            try:
                line = proc.stdout.readline()
                if line:
                    print(f"[LOG] {line.strip()}")
            except:
                pass

        time.sleep(0.1)

def main():
    """Punto de entrada principal"""
    print("\n🔧 Alex Asesor Financiero - Configuración de desarrollo local")
    print("="*50)

    # Verifica requisitos previos
    check_requirements()
    check_env_files()

    # Instala httpx si es necesario
    try:
        import httpx
    except ImportError:
        print("\n📦 Instalando httpx para comprobaciones de salud...")
        subprocess.run(["uv", "add", "httpx"], check=True)

    # Iniciar servicios
    backend_proc = start_backend()
    frontend_proc = start_frontend()

    # Monitorea procesos
    try:
        monitor_processes()
    except KeyboardInterrupt:
        cleanup()

if __name__ == "__main__":
    main()