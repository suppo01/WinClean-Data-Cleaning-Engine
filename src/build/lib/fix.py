import os
import asyncio
import subprocess
import traceback

from detect import extract_path_from_command
from typing import Any


async def run_opencode_prompt(broken_code: str, potential_bug: str) -> Any:
    """Run OpenCode via subprocess using shell."""
    if os.path.isfile(broken_code):
        with open(broken_code, "r", encoding="utf-8") as f:
            broken_code_content = f.read()
    else:
        broken_code_content = extract_path_from_command(broken_code)

    prompt = f"""Fix only the Windows path errors in this code based on this analysis. Just show the corrected code.

Analysis Results:
{potential_bug}

Code:
{broken_code_content}
"""

    print("Running OpenCode via subprocess...")

    try:
        cmd = (
            "bun x opencode-ai run --model github-copilot/gpt-4o --format json --continue "
            + '"'
            + prompt.replace('"', '\\"')
            + '"'
        )

        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=180,
        )

        if result.stdout:
            return result.stdout
        elif result.stderr:
            return f"Error: {result.stderr}"
        else:
            return "No output"

    except Exception as e:
        return f"Error: {e}\n{traceback.format_exc()}"


def run_opencode_prompt_sync(broken_code: str, potential_bug: str) -> Any:
    """Synchronous wrapper."""
    return asyncio.run(run_opencode_prompt(broken_code, potential_bug))
