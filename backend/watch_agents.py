#!/usr/bin/env python3
"""
Ver el registro de CloudWatch de todos los agentes Alex en tiempo real.
Consulta los registros de los 5 agentes simultáneamente y muestra la salida con codificación de color.
"""

import boto3
import time
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed

# Códigos de color ANSI para la salida por terminal
COLORS = {
    'PLANNER': '\033[94m',    # Azul
    'TAGGER': '\033[93m',     # Amarillo
    'REPORTER': '\033[92m',   # Verde
    'CHARTER': '\033[96m',    # Cian
    'RETIREMENT': '\033[95m', # Magenta
    'ERROR': '\033[91m',      # Rojo
    'LANGFUSE': '\033[35m',   # Púrpura (para los logs relacionados con LangFuse)
    'RESET': '\033[0m',       # Restablecer a predeterminado
    'BOLD': '\033[1m',        # Texto en negrita
}

# Grupos de logs de los agentes
LOG_GROUPS = {
    'PLANNER': '/aws/lambda/alex-planner',
    'TAGGER': '/aws/lambda/alex-tagger',
    'REPORTER': '/aws/lambda/alex-reporter',
    'CHARTER': '/aws/lambda/alex-charter',
    'RETIREMENT': '/aws/lambda/alex-retirement',
}


class AgentLogWatcher:
    """Observa los logs de CloudWatch para todos los agentes."""

    def __init__(self, region: str = 'us-east-1', lookback_minutes: int = 5):
        """Inicializa el observador de logs."""
        self.logs_client = boto3.client('logs', region_name=region)
        self.lookback_minutes = lookback_minutes
        self.last_timestamps = {agent: 0 for agent in LOG_GROUPS}

    def get_log_events(self, agent: str, start_time: int) -> List[Dict]:
        """Obtiene los eventos del log para un agente específico."""
        log_group = LOG_GROUPS[agent]

        try:
            # Obtiene todos los flujos de logs en el grupo
            response = self.logs_client.describe_log_streams(
                logGroupName=log_group,
                orderBy='LastEventTime',
                descending=True,
                limit=5  # Obtiene los 5 flujos más recientes
            )

            if not response.get('logStreams'):
                return []

            # Recoge los eventos de todos los flujos recientes
            all_events = []
            for stream in response['logStreams']:
                stream_name = stream['logStreamName']

                # Obtiene los eventos de este flujo
                try:
                    events_response = self.logs_client.filter_log_events(
                        logGroupName=log_group,
                        logStreamNames=[stream_name],
                        startTime=start_time,
                        limit=100
                    )

                    events = events_response.get('events', [])
                    all_events.extend(events)

                except Exception as e:
                    # Es posible que el flujo haya sido eliminado o no tenga eventos
                    continue

            # Ordena los eventos por timestamp
            all_events.sort(key=lambda x: x['timestamp'])

            # Actualiza el último timestamp para este agente
            if all_events:
                self.last_timestamps[agent] = all_events[-1]['timestamp'] + 1

            return all_events

        except self.logs_client.exceptions.ResourceNotFoundException:
            print(f"{COLORS['ERROR']}Grupo de logs {log_group} no encontrado{COLORS['RESET']}")
            return []
        except Exception as e:
            print(f"{COLORS['ERROR']}Error al obtener los logs para {agent}: {e}{COLORS['RESET']}")
            return []

    def format_message(self, agent: str, event: Dict) -> str:
        """Formatea un mensaje de log con codificación de color."""
        timestamp = datetime.fromtimestamp(event['timestamp'] / 1000).strftime('%H:%M:%S.%f')[:-3]
        message = event['message'].rstrip()

        # Colorea el nombre del agente
        agent_color = COLORS[agent]
        agent_label = f"{agent_color}[{agent:10}]{COLORS['RESET']}"

        # Destaca tipos específicos de mensajes
        if 'ERROR' in message or 'Exception' in message:
            message_color = COLORS['ERROR']
        elif 'LangFuse' in message or 'Observability' in message:
            message_color = COLORS['LANGFUSE']
        else:
            message_color = ''

        if message_color:
            message = f"{message_color}{message}{COLORS['RESET']}"

        return f"{timestamp} {agent_label} {message}"

    def poll_agent(self, agent: str, start_time: int) -> List[str]:
        """Consulta un solo agente en busca de nuevos eventos de log."""
        events = self.get_log_events(agent, start_time)
        formatted_messages = []

        for event in events:
            formatted_messages.append(self.format_message(agent, event))

        return formatted_messages

    def watch(self, poll_interval: int = 2):
        """Observa continuamente los logs de todos los agentes."""
        print(f"{COLORS['BOLD']}Observando los logs de CloudWatch para todos los agentes Alex...{COLORS['RESET']}")
        print(f"Mirando hacia atrás {self.lookback_minutes} minutos inicialmente")
        print(f"Consultando cada {poll_interval} segundos")
        print(f"Presiona Ctrl+C para detener\n")

        # Tiempo de inicio inicial (periodo de retroceso)
        initial_start = int((datetime.now() - timedelta(minutes=self.lookback_minutes)).timestamp() * 1000)

        # Establece los timestamps iniciales
        for agent in LOG_GROUPS:
            self.last_timestamps[agent] = initial_start

        try:
            while True:
                # Consulta todos los agentes en paralelo
                with ThreadPoolExecutor(max_workers=5) as executor:
                    futures = {
                        executor.submit(self.poll_agent, agent, self.last_timestamps[agent]): agent
                        for agent in LOG_GROUPS
                    }

                    # Recoge y muestra los resultados
                    all_messages = []
                    for future in as_completed(futures):
                        messages = future.result()
                        all_messages.extend(messages)

                    # Ordena los mensajes por timestamp y los muestra
                    all_messages.sort()
                    for message in all_messages:
                        print(message)

                # Espera antes de la siguiente consulta
                time.sleep(poll_interval)

        except KeyboardInterrupt:
            print(f"\n{COLORS['BOLD']}Observación de logs detenida{COLORS['RESET']}")
            sys.exit(0)
        except Exception as e:
            print(f"{COLORS['ERROR']}Error: {e}{COLORS['RESET']}")
            sys.exit(1)


def main():
    """Punto de entrada principal."""
    parser = argparse.ArgumentParser(description='Ver los logs de CloudWatch de todos los agentes Alex')
    parser.add_argument(
        '--region',
        default='us-east-1',
        help='Región de AWS (por defecto: us-east-1)'
    )
    parser.add_argument(
        '--lookback',
        type=int,
        default=5,
        help='Minutos previos a consultar inicialmente (por defecto: 5)'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=2,
        help='Intervalo de consulta en segundos (por defecto: 2)'
    )

    args = parser.parse_args()

    watcher = AgentLogWatcher(region=args.region, lookback_minutes=args.lookback)
    watcher.watch(poll_interval=args.interval)


if __name__ == "__main__":
    main()