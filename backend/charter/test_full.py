#!/usr/bin/env python3
"""
Prueba completa para el agente Charter vía Lambda
"""

import json
import boto3
import time
from dotenv import load_dotenv

from src import Database
from src.schemas import JobCreate

load_dotenv(override=True)


def test_charter_lambda():
    """Probar el agente Charter vía invocación Lambda"""

    db = Database()
    lambda_client = boto3.client("lambda")

    # Crear trabajo de prueba
    test_user_id = "test_user_001"

    job_create = JobCreate(
        clerk_user_id=test_user_id,
        job_type="portfolio_analysis",
        request_payload={"analysis_type": "test", "test": True},
    )
    job_id = db.jobs.create(job_create.model_dump())

    # Cargar datos de portfolio para la prueba
    user = db.users.find_by_clerk_id(test_user_id)
    accounts = db.accounts.find_by_user(test_user_id)

    portfolio_data = {
        "user_id": test_user_id,
        "job_id": job_id,
        "years_until_retirement": user.get("years_until_retirement", 30),
        "accounts": [],
    }

    for account in accounts:
        positions = db.positions.find_by_account(account["id"])
        account_data = {
            "id": account["id"],
            "name": account["account_name"],
            "cash_balance": float(account.get("cash_balance", 0)),
            "positions": [],
        }

        for position in positions:
            instrument = db.instruments.find_by_symbol(position["symbol"])
            if instrument:
                account_data["positions"].append(
                    {
                        "symbol": position["symbol"],
                        "quantity": float(position["quantity"]),
                        "instrument": instrument,
                    }
                )

        portfolio_data["accounts"].append(account_data)

    print(f"Probando Charter Lambda con el trabajo {job_id}")
    print("=" * 60)

    # Invocar Lambda
    try:
        response = lambda_client.invoke(
            FunctionName="alex-charter",
            InvocationType="RequestResponse",
            Payload=json.dumps({"job_id": job_id, "portfolio_data": portfolio_data}),
        )

        result = json.loads(response["Payload"].read())
        print(f"Respuesta de Lambda: {json.dumps(result, indent=2)}")

        # Consultar la base de datos por resultados
        time.sleep(2)  # Dale un momento
        job = db.jobs.find_by_id(job_id)

        if job and job.get("charts_payload"):
            print(f"\n📊 Gráficas creadas ({len(job['charts_payload'])} en total):")
            print("=" * 50)
            for chart_key, chart_data in job["charts_payload"].items():
                print(f"\n🎯 Gráfica: {chart_key}")
                print(f"   Título: {chart_data.get('title', 'N/A')}")
                print(f"   Tipo: {chart_data.get('type', 'N/A')}")
                print(f"   Descripción: {chart_data.get('description', 'N/A')}")

                data_points = chart_data.get("data", [])
                print(f"   Puntos de datos ({len(data_points)}):")
                for i, point in enumerate(data_points):
                    name = point.get("name", "N/A")
                    value = point.get("value", 0)
                    color = point.get("color", "N/A")
                    print(f"     {i+1}. {name}: ${value:,.2f} {color}")

        else:
            print("\n❌ No se encontraron gráficas en la base de datos")

    except Exception as e:
        print(f"Error al invocar Lambda: {e}")

    print("=" * 60)


if __name__ == "__main__":
    test_charter_lambda()
