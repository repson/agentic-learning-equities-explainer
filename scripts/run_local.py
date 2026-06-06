#!/usr/bin/env python3
"""
Run both frontend and backend locally for development.
This script starts the NextJS frontend and the FastAPI backend in parallel.
"""

import you
import sys
import subprocess
import signal
import time
from pathlib import Path

# Track threads for cleanup
processes = []

def cleanup(signum=None, frame=None):
    """Clear all threads on exit"""
    print("\n🛑 Shutting down services...")
    for proc in processes:
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except:
            proc.kill()
    sys.exit(0)

# Register cleanup handlers
signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

def check_requirements():
    """Check if the required tools are installed"""
    checks = []

    # Check Node.js
    try:
        result = subprocess.run(["node", "--version"], capture_output=True, text=True)
        node_version = result.stdout.strip()
        checks.append(f"✅ Node.js: {node_version}")
    except FileNotFoundError:
        checks.append("❌ Node.js not found - please install Node.js")

    # Check npm
    try:
        result = subprocess.run(["npm", "--version"], capture_output=True, text=True)
        npm_version = result.stdout.strip()
        checks.append(f"✅ npm: {npm_version}")
    except FileNotFoundError:
        checks.append("❌ npm not found - please install npm")

    # Check uv (which Python manages for us)
    try:
        result = subprocess.run(["uv", "--version"], capture_output=True, text=True)
        uv_version = result.stdout.strip()
        checks.append(f"✅ uv: {uv_version}")
    except FileNotFoundError:
        checks.append("❌ uv not found - please install uv")

    print("\n📋 Prerequisite check:")
    for check in checks:
        print(f" {check}")

    # Exit if any critical requirement is missing
    if any("❌" in check for check in checks):
        print("\n⚠️ Please install the missing dependencies and try again.")
        sys.exit(1)

def check_env_files():
    """Check if the environment files exist"""
    project_root = Path(__file__).parent.parent

    root_env = project_root / ".env"
    frontend_env = project_root / "frontend" / ".env.local"

    missing = []

    if not root_env.exists():
        missing.append(".env (base project file)")
    if not frontend_env.exists():
        missing.append("frontend/.env.local")

    if missing:
        print("\n⚠️ Missing environment files:")
        for file in missing:
            print(f" - {file}")
        print("\nPlease create these files with the required configuration.")
        print("The .env file in the root must have all the backend variables from Parts 1-7.")
        print("The frontend/.env.local file must have the Clerk keys.")
        sys.exit(1)

    print("✅ Environment files found")

def start_backend():
    "Start the FastAPI backend"
    backend_dir = Path(__file__).parent.parent / "backend" / "api"

    print("\n🚀 Starting FastAPI backend...")

    # Check if dependencies are installed
    if not (backend_dir / ".venv").exists() and not (backend_dir / "uv.lock").exists():
        print("Installing backend dependencies...")
        subprocess.run(["uv", "sync"], cwd=backend_dir, check=True)

    # Start the backend
    proc = subprocess.Popen(
        ["uv", "run", "main.py"],
        cwd=backend_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    processes.append(proc)

    # Wait for the backend to start
    print("Waiting for backend to start...")
    for _ in range(30): # 30 seconds maximum wait
        try:
            import httpx
            response = httpx.get("http://localhost:8000/health")
            if response.status_code == 200:
                print(" ✅ Backend running on http://localhost:8000")
                print("API Documentation: http://localhost:8000/docs")
                return proc
        except:
            time.sleep(1)

    print(" ❌ The backend could not be started")
    cleanup()

def start_frontend():
    """Start the NextJS frontend"""
    frontend_dir = Path(__file__).parent.parent / "frontend"

    print("\n🚀 Starting NextJS frontend...")

    # Check if dependencies are installed
    if not (frontend_dir / "node_modules").exists():
        print("Installing frontend dependencies...")
        subprocess.run(["npm", "install"], cwd=frontend_dir, check=True)

    # Start the frontend
    proc = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=frontend_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, # Combine stderr with stdout
        text=True,
        bufsize=1
    )
    processes.append(proc)

    # Wait for the frontend to start
    print("Waiting for frontend to start...")
    import httpx
    import select

    started = False
    for i in range(30): # 30 seconds maximum wait
        # Check the process exit in a non-blocking manner
        if proc.stdout:
            ready, _, _ = select.select([proc.stdout], [], [], 0)
            if ready:
                line = proc.stdout.readline()
                if line:
                    print(f" Frontend: {line.strip()}")
                    # NextJS dev server prints "Ready" when ready
                    if "ready" in line.lower() or "compiled" in line.lower() or "started server" in line.lower():
                        started = True

        # Also try to connect
        if started or i > 5: # Start checking after 5 seconds or when it sees "ready"
            try:
                response = httpx.get("http://localhost:3000", timeout=1)
                print(" ✅ Frontend running on http://localhost:3000")
                return proc
            except httpx.ConnectError:
                pass # The server is not ready yet
            except:
                # Any other response means the server is up
                print(" ✅ Frontend running on http://localhost:3000")
                return proc

        time.sleep(1)

    print(" ❌ The frontend could not be started")
    cleanup()

def monitor_processes():
    """Monitors running processes and displays their output"""
    print("\n" + "="*60)
    print("🎯 Alex Financial Advisor - Local Development")
    print("="*60)
    print("\n📍Services:")
    print("Frontend: http://localhost:3000")
    print("Backend: http://localhost:8000")
    print("API Documentation: http://localhost:8000/docs")
    print("\n📝 The logs will appear below. Press Ctrl+C to stop.\n")
    print("="*60 + "\n")

    # Monitor processes
    while True:
        for proc in processes:
            # Check if the process is still running
            if proc.poll() is not None:
                print(f"\n⚠️ A process has stopped unexpectedly!")
                cleanup()

            # Read any available output
            try:
                line = proc.stdout.readline()
                if line:
                    print(f"[LOG] {line.strip()}")
            except:
                pass

        time.sleep(0.1)

def main():
    "Main entry point"
    print("\n🔧 Alex Financial Advisor - Local Development Configuration")
    print("="*50)

    # Check prerequisites
    check_requirements()
    check_env_files()

    # Install httpx if necessary
    try:
        import httpx
    exceptImportError:
        print("\n📦 Installing httpx for health checks...")
        subprocess.run(["uv", "add", "httpx"], check=True)

    # Start services
    backend_proc = start_backend()
    frontend_proc = start_frontend()

    # Monitor processes
    try:
        monitor_processes()
    exceptKeyboardInterrupt:
        cleanup()

if __name__ == "__main__":
    main()
