import os
import asyncio
import re
import ast
from detect import extract_path_from_command
from typing import Any


FEW_SHOT_EXAMPLES = """
Here are some examples of Windows path bug fixes:

Example 1:
BUGGY CODE:
import os
path = "C:\\\\Users\\\\molly\\\\COM1"
os.listdir(path)

FIX:
import os
path = "C:\\\\Users\\\\molly\\\\data"
os.listdir(path)

Example 2:
BUGGY CODE:
import os
user_input = input("Enter name: ")
path = "C:\\\\Users\\\\molly\\\\" + user_input

FIX:
import os
user_input = input("Enter name: ")
if user_input:
    path = r"C:\\\\Users\\\\molly\\\\" + user_input
    if os.path.exists(path):
        os.listdir(path)

Example 3:
BUGGY CODE:
print("C:\\\\Users\\\\test\\\\>")

FIX:
print(r"C:\\\\Users\\\\test\\\\>")
"""


def extract_code(response: str) -> str:
    """Extract Python code from response, handling markdown blocks."""
    code_blocks = re.findall(r"```python\n(.*?)```", response, re.DOTALL)
    if code_blocks:
        return code_blocks[0]
    code_blocks = re.findall(r"```\n(.*?)```", response, re.DOTALL)
    if code_blocks:
        return code_blocks[0]
    return response.strip()


def validate_python_syntax(code: str) -> bool:
    """Check if the code has valid Python syntax."""
    try:
        ast.parse(code)
        return True
    except SyntaxError:
        return False


class OpenCodeClient:
    """ACP client for OpenCode."""

    def __init__(self):
        self.messages = []
        self.done = asyncio.Event()

    async def request_permission(self, options, session_id, tool_call, **kwargs):
        return {"outcome": {"outcome": "ALLOW"}}

    async def session_update(self, session_id, update, **kwargs):
        content = getattr(update, "content", None)
        if content and hasattr(content, "text") and content.text:
            self.messages.append(content.text)
        if content and getattr(content, "is_final", False):
            self.done.set()


async def run_opencode_acp(
    prompt: str, model: str = "opencode/minimax-m2.5-free"
) -> str:
    """Run OpenCode via ACP with iterative querying handled by the server."""
    try:
        from acp import text_block, connect_to_agent
        from acp.transports import spawn_stdio_transport

        client = OpenCodeClient()

        async with spawn_stdio_transport("opencode.cmd", "acp") as (
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

            # Wait for completion with extended timeout for iterative querying
            try:
                await asyncio.wait_for(client.done.wait(), timeout=300)
            except asyncio.TimeoutError:
                pass

            return "\n".join(client.messages)

    except Exception as e:
        return f"Error: {e}"


def run_opencode_prompt_sync(
    broken_code: str,
    potential_bug: str,
    analysis_results: str = "",
    model: str = "opencode/minimax-m2.5-free",
) -> Any:
    """Run OpenCode via ACP with iterative querying and few-shot approach."""
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

    # Prompt that instructs OpenCode to do iterative refinement internally
    prompt = f"""Fix Windows path bugs in this code. Use iterative refinement to improve the fix.

{analysis_section}{FEW_SHOT_EXAMPLES}

CODE TO FIX:
{broken_code_content}

TASK:
1. First, identify all Windows path bugs in the code
2. Generate an initial fix
3. Review the fix and refine it if needed (up to 3 refinement iterations)
4. Return the FINAL corrected code and an explanation of the changes made

REQUIREMENTS:
- Return the final corrected Python code and an explanation of the changes made
- Use raw strings (r"...") for paths with backslashes
- Avoid reserved Windows names: COM1, COM2, LPT1, LPT2, LPT3, PRN, AUX, CON, NUL
- Paths must start with drive letter (C:) and not be UNC paths

FINAL CODE:
"""

    print(f"Running OpenCode via ACP with iterative querying...")

    response = asyncio.run(run_opencode_acp(prompt, model))

    extracted = extract_code(response)
    is_valid = validate_python_syntax(extracted)

    print(f"Response length: {len(extracted)} chars")
    print(f"Valid syntax: {is_valid}")

    if is_valid:
        print("✓ Valid response received")
        return extracted
    else:
        print("✗ Invalid syntax, returning response for review")
        return extracted


def run_opencode_prompt(
    broken_code: str,
    potential_bug: str,
    analysis_results: str = "",
    model: str = "opencode/minimax-m2.5-free",
) -> Any:
    """Synchronous wrapper."""
    return run_opencode_prompt_sync(broken_code, potential_bug, analysis_results, model)
