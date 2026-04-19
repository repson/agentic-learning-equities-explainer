# \!/usr/bin/env python3
"""
Prueba el agente researcher localmente antes del despliegue
"""

import asyncio
from context import get_agent_instructions, DEFAULT_RESEARCH_PROMPT
from mcp_servers import create_playwright_mcp_server
from tools import ingest_financial_document
from agents import Agent, Runner
from dotenv import load_dotenv

load_dotenv(override=True)


async def test_local():
    """Prueba el agente researcher localmente."""
    print("Probando el agente researcher localmente...")
    print("=" * 60)

    # Prueba sin tema (el agente elige)
    query = DEFAULT_RESEARCH_PROMPT

    try:
        async with create_playwright_mcp_server() as playwright_mcp:
            agent = Agent(
                name="Alex Investment Researcher",
                instructions=get_agent_instructions(),
                model="gpt-4.1-mini",
                tools=[ingest_financial_document],
                mcp_servers=[playwright_mcp],
            )

            result = await Runner.run(agent, input=query)

        print("\nRESULTADO:")
        print("=" * 60)
        print(result.final_output)
        print("=" * 60)
        print("\n✅ ¡Prueba completada con éxito!")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_local())
