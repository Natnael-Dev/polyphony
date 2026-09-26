"""Developer seat adapter for Polyphony Dark Factory."""

from __future__ import annotations

import asyncio
import logging
import os
import pathlib
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
    extra_loggers={
        "websockets": logging.WARNING,
        "httpx": logging.WARNING,
    },
)
logger = logging.getLogger("polyphony-developer")

WORKSPACE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MANDATE_PATH = os.path.join(WORKSPACE_DIR, "mandates", "developer.md")
CONFIG_PATH = os.path.join(WORKSPACE_DIR, "agent_config.yaml")

async def main() -> None:
    load_dotenv()
    custom_section = ""
    if os.path.exists(MANDATE_PATH):
        with open(MANDATE_PATH, "r", encoding="utf-8") as f:
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

    logger.info("Starting polyphony-developer agent seat...")
    async with Agent.from_config(
        "polyphony-developer",
        adapter=adapter,
        config_path=CONFIG_PATH,
    ) as agent:
        await agent.run_forever()

if __name__ == "__main__":
    asyncio.run(main())
