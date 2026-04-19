#!/usr/bin/env python3
"""
Rastrear y mostrar los logs de Tagger Lambda en tiempo real
"""

import time
import boto3
import signal
import sys
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(override=True)

class TaggerLogTracker:
    """Consultar continuamente y mostrar los logs de Tagger Lambda"""

    def __init__(self):
        self.logs_client = boto3.client('logs', region_name='us-east-1')
        self.log_group_name = '/aws/lambda/alex-tagger'
        self.running = True
        self.last_timestamp = None

        # Configurar el manejador de señales para salida limpia
        signal.signal(signal.SIGINT, self.signal_handler)

    def signal_handler(self, sig, frame):
        """Manejar Ctrl+C de forma elegante"""
        print("\n\n⏹  Deteniendo el rastreo de logs...")
        self.running = False
        sys.exit(0)

    def get_logs(self, start_time):
        """Obtener logs desde CloudWatch"""
        try:
            params = {
                'logGroupName': self.log_group_name,
                'startTime': start_time,
                'limit': 100
            }

            response = self.logs_client.filter_log_events(**params)
            return response.get('events', [])

        except Exception as e:
            if 'ResourceNotFoundException' in str(e):
                print(f"⚠️  Grupo de logs {self.log_group_name} no encontrado")
            else:
                print(f"❌ Error obteniendo logs: {e}")
            return []

    def format_log_message(self, event):
        """Formatear un evento de log para su visualización"""
        # Extraer timestamp
        timestamp = datetime.fromtimestamp(event['timestamp'] / 1000)
        time_str = timestamp.strftime('%H:%M:%S.%f')[:-3]

        # Obtener el mensaje
        message = event['message'].strip()

        # Código de color según el contenido
        if 'ERROR' in message or 'Failed' in message:
            color = '\033[91m'  # Rojo
        elif 'WARNING' in message or 'WARN' in message:
            color = '\033[93m'  # Amarillo
        elif 'LangFuse' in message or 'observability' in message:
            color = '\033[92m'  # Verde
        elif 'OpenAI Agents trace' in message:
            color = '\033[96m'  # Cian
        elif 'Successfully classified' in message:
            color = '\033[94m'  # Azul
        elif 'START RequestId' in message or 'END RequestId' in message:
            color = '\033[95m'  # Magenta
        elif 'INIT_START' in message:
            color = '\033[93m'  # Amarillo
        else:
            color = '\033[0m'   # Por defecto

        reset = '\033[0m'

        # Formatear según el tipo de mensaje
        if 'REPORT RequestId' in message:
            # Parsear reporte de Lambda
            parts = message.split('\t')
            if len(parts) >= 3:
                request_id = parts[0].split(' ')[2]
                duration = parts[1] if len(parts) > 1 else ""
                memory = parts[3] if len(parts) > 3 else ""
                return f"{time_str} 📊 {color}Reporte Lambda: {duration}, {memory}{reset}"
        elif 'START RequestId' in message:
            request_id = message.split(' ')[2]
            return f"{time_str} 🚀 {color}Inicio de Lambda: {request_id[:8]}...{reset}"
        elif 'END RequestId' in message:
            request_id = message.split(' ')[2]
            return f"{time_str} 🏁 {color}Fin de Lambda: {request_id[:8]}...{reset}"
        elif message.startswith('[INFO]') or message.startswith('[ERROR]') or message.startswith('[WARNING]'):
            # Registro estándar de Python
            parts = message.split('\t', 2)
            if len(parts) >= 3:
                level = parts[0].strip('[]')
                msg = parts[2] if len(parts) > 2 else parts[1]
                level_icon = {'INFO': 'ℹ️ ', 'ERROR': '❌', 'WARNING': '⚠️ '}.get(level, '  ')
                return f"{time_str} {level_icon} {color}{msg}{reset}"
        elif 'OpenAI Agents trace' in message:
            return f"{time_str} 🤖 {color}{message}{reset}"
        elif 'Agent run:' in message:
            return f"{time_str}    ↳ {color}{message.strip()}{reset}"
        elif 'Chat completion' in message:
            return f"{time_str}      ↳ {color}{message.strip()}{reset}"
        else:
            # Formato por defecto
            if message and not message.isspace():
                return f"{time_str}    {color}{message}{reset}"

        return None

    def track(self):
        """Bucle principal de rastreo"""
        print("=" * 60)
        print("📡 Rastreando logs de Tagger Lambda")
        print("=" * 60)
        print(f"Grupo de logs: {self.log_group_name}")
        print("Presiona Ctrl+C para detener\n")

        # Comenzar desde hace 1 minuto
        start_time = int((time.time() - 60) * 1000)
        seen_ids = set()

        while self.running:
            try:
                # Obtener logs
                events = self.get_logs(start_time)

                # Procesar eventos nuevos
                new_events = []
                for event in events:
                    event_id = event.get('eventId')
                    if event_id not in seen_ids:
                        seen_ids.add(event_id)
                        new_events.append(event)

                # Mostrar eventos nuevos
                for event in new_events:
                    formatted = self.format_log_message(event)
                    if formatted:
                        print(formatted)

                    # Actualizar start_time para la siguiente consulta
                    start_time = max(start_time, event['timestamp'] + 1)

                # Si recibimos eventos, mostrar un separador para mayor claridad
                if new_events and len(new_events) > 5:
                    print("-" * 40)

                # Esperar antes de la siguiente consulta (menos si acabamos de recibir eventos)
                sleep_time = 1 if new_events else 2
                time.sleep(sleep_time)

            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ Error en el bucle de rastreo: {e}")
                time.sleep(5)

        print("\n✅ Rastreo de logs detenido")

def main():
    """Punto de entrada principal"""
    tracker = TaggerLogTracker()

    print("\n🔍 Buscando logs recientes relacionados con Langfuse...")
    print("-" * 40)

    # Primero mostrar cualquier log reciente de Langfuse
    recent_logs = tracker.get_logs(int((time.time() - 300) * 1000))  # Últimos 5 minutos
    langfuse_found = False

    for event in recent_logs[-20:]:  # Últimos 20 eventos
        message = event['message']
        if any(term in message for term in ['LangFuse', 'langfuse', 'observability', 'OPENAI_API_KEY', 'setup_observability']):
            formatted = tracker.format_log_message(event)
            if formatted:
                print(formatted)
                langfuse_found = True

    if not langfuse_found:
        print("  No se encontraron logs recientes relacionados con Langfuse")

    print("-" * 40)
    print("\nIniciando rastreo continuo...\n")

    # Comenzar rastreo continuo
    tracker.track()

if __name__ == "__main__":
    main()