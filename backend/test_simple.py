#!/usr/bin/env python3
"""
Prueba todos los agentes ejecutando sus archivos test_simple.py individuales en sus propios directorios.
Esto asegura que cada agente se ejecute con sus propias dependencias y entorno.
"""

import os
import subprocess
import sys
from pathlib import Path

def run_command(cmd, cwd):
    """Ejecuta un comando y captura la salida."""
    print(f"Ejecutando en {cwd}: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    return result.returncode == 0, result.stdout, result.stderr

def test_agent(agent_name, test_file="test_simple.py"):
    """Prueba un agente individual en su directorio."""
    backend_dir = Path(__file__).parent
    agent_dir = backend_dir / agent_name
    
    if not agent_dir.exists():
        print(f"  ❌ {agent_name}: Directorio no encontrado")
        return False
    
    test_path = agent_dir / test_file
    if not test_path.exists():
        print(f"  ⚠️  {agent_name}: No se encontró {test_file}, se omite")
        return True  # No es un fallo, solo se omite
    
    # Configura el entorno para lambdas simulados
    env = os.environ.copy()
    env['MOCK_LAMBDAS'] = 'true'
    
    # Ejecuta la prueba con uv
    success, stdout, stderr = run_command(
        ['uv', 'run', test_file],
        cwd=str(agent_dir)
    )
    
    if success:
        print(f"  ✅ {agent_name}: Prueba pasada")
        if stdout and "Status Code: 200" in stdout:
            # Extraer información clave de ejecuciones exitosas
            for line in stdout.split('\n'):
                if 'Tagged:' in line or 'Success:' in line or 'Message:' in line:
                    print(f"     {line.strip()}")
    else:
        print(f"  ❌ {agent_name}: Prueba fallida")
        if stderr:
            # Muestra la primera línea de error
            error_lines = [l for l in stderr.split('\n') if l.strip()]
            if error_lines:
                print(f"     Error: {error_lines[0][:100]}")
    
    return success

def main():
    """Ejecuta todas las pruebas de los agentes."""
    print("="*60)
    print("PROBANDO TODOS LOS AGENTES")
    print("Ejecutando test_simple.py individual en cada directorio de agente")
    print("="*60)
    
    # Lista de agentes a probar
    agents = [
        'tagger',
        'reporter', 
        'charter',
        'retirement',
        'planner'
    ]
    
    results = {}
    
    for agent in agents:
        print(f"\nAgente {agent.upper()}:")
        results[agent] = test_agent(agent)
    
    # Resumen
    print("\n" + "="*60)
    print("RESUMEN DE PRUEBAS")
    print("="*60)
    
    passed = sum(1 for r in results.values() if r)
    failed = sum(1 for r in results.values() if not r)
    
    print(f"Aprobados: {passed}/{len(agents)}")
    print(f"Fallidos: {failed}/{len(agents)}")
    
    if failed > 0:
        print("\nAgentes fallidos:")
        for agent, success in results.items():
            if not success:
                print(f"  - {agent}")
    
    print("="*60)
    
    if failed > 0:
        print("\n⚠️  ALGUNAS PRUEBAS FALLARON")
        sys.exit(1)
    else:
        print("\n✅ ¡TODAS LAS PRUEBAS APROBADAS!")
        sys.exit(0)

if __name__ == "__main__":
    main()