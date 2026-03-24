import os
import asyncio

from detect import extract_path_from_command
from typing import Any


async def run_opencode_prompt_async(
    broken_code: str, potential_bug: str, analysis_results: str = ""
) -> Any:
    """Run OpenCode via ACP."""
    if os.path.isfile(broken_code):
        with open(broken_code, "r", encoding="utf-8") as f:
            broken_code_content = f.read()
    else:
        broken_code_content = extract_path_from_command(broken_code)

    analysis_section = ""
    if analysis_results:
        analysis_section = f"""ANALYSIS RESULTS:
{analysis_results}

"""

    prompt = f"""Fix Windows path bugs in this code using the provided analysis results. Return ONLY the corrected code.

{analysis_section}CODE:
{broken_code_content}"""

    print("Running OpenCode via ACP...")

    try:
        from acp import Client, text_block, connect_to_agent
        from acp.transports import spawn_stdio_transport

        class OpenCodeClient(Client):
            def __init__(self):
                super().__init__()
                self.messages = []
                self.done = asyncio.Event()

            async def request_permission(
                self, options, session_id, tool_call, **kwargs
            ):
                return {"outcome": {"outcome": "ALLOW"}}

            async def session_update(self, session_id, update, **kwargs) -> None:
                content = getattr(update, "content", None)
                if content and hasattr(content, "text") and content.text:
                    self.messages.append(content.text)
                    print(f"OpenCode: {content.text[:100]}...")
                if content and getattr(content, "is_final", False):
                    self.done.set()

        client = OpenCodeClient()

        async with spawn_stdio_transport("opencode.cmd", "acp", "--port", "8080") as (
            reader,
            writer,
            proc,
        ):
            conn = connect_to_agent(client, writer, reader)
            await conn.initialize(protocol_version=1)

            session = await conn.new_session(cwd=os.getcwd())
            await conn.prompt(
                session_id=session.session_id,
                prompt=[text_block(prompt)],
            )

            try:
                await asyncio.wait_for(client.done.wait(), timeout=120)
            except asyncio.TimeoutError:
                print("Timeout waiting for response")

        return "\n".join(client.messages) if client.messages else "No response"

    except Exception as e:
        import traceback

        return f"Error: {e}\n{traceback.format_exc()}"


def run_opencode_prompt(
    broken_code: str, potential_bug: str, analysis_results: str = ""
) -> Any:
    """Synchronous wrapper."""
    return asyncio.run(
        run_opencode_prompt_async(broken_code, potential_bug, analysis_results)
    )


def run_opencode_prompt_sync(
    broken_code: str, potential_bug: str, analysis_results: str = ""
) -> Any:
    """Synchronous wrapper."""
    return asyncio.run(
        run_opencode_prompt_async(broken_code, potential_bug, analysis_results)
    )
