"""Architect seat adapter for Polyphony Dark Factory."""

import asyncio
import logging
import os
import sys

from dotenv import load_dotenv

from band import Agent, configure_logging
from band.adapters.codex import CodexAdapter, CodexAdapterConfig
from band.core.types import Emit

configure_logging(
    level=logging.INFO,
    style="json",
    root_level=logging.INFO,
    stream="stdout",
    extra_loggers={"websockets": logging.WARNING, "httpx": logging.WARNING},
)
logger = logging.getLogger("polyphony-architect")

async def main() -> None:
    load_dotenv()
    mandate_path = os.path.join(os.path.dirname(__file__), "..", "mandates", "architect.md")
    custom_section = ""
    if os.path.exists(mandate_path):
        with open(mandate_path, "r", encoding="utf-8") as f:
            custom_section = f.read()

    adapter = CodexAdapter(
        config=CodexAdapterConfig(
            transport="stdio",
            personality="none",
            custom_section=custom_section,
            include_base_instructions=True,
            fallback_send_agent_text=True,
        ),
        emit={Emit.TASK_EVENTS, Emit.THOUGHTS},
    )

    logger.info("Starting polyphony-architect agent seat...")
    async with Agent.from_config("polyphony-architect", adapter=adapter) as agent:
        await agent.run_forever()

if __name__ == "__main__":
    asyncio.run(main())
