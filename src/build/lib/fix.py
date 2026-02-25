import subprocess
import os
import shutil

from detect import extract_path_from_command
from typing import Any


def run_opencode_prompt(broken_code: str, potential_bug: str) -> Any:
    """Run OpenCode CLI directly with a prompt."""

    if os.path.isfile(broken_code):
        with open(broken_code, "r", encoding="utf-8") as f:
            broken_code = f.read()
    else:
        broken_code = extract_path_from_command(broken_code)

    prompt = f"""Fix the Windows Path Bug in {broken_code} with the error {potential_bug}.
Here are example inputs and outputs for this prompt to help you understand the task:
Example 1: UNC Path
Input: //server/share/folder/file.txt
Output: /server/share/folder/file.txt
        There was a UNC path in the input, which is not valid in Windows.
        Use a single slash instead of a double slash.
Example 2: Folder Doesn't Exist
Input: C:/nonexistent/folder/file.txt
Output: C:/existing/folder/file.txt
        The input had a folder that doesn't exist.
        Make sure you have the right directory and file name.
Example 3: Missing Drive Letter
Input: folder/file.txt
Output: C:/folder/file.txt
        The input was missing a drive letter.
        Add the appropriate drive letter (e.g., C:) to the beginning of the path.
Example 4: Illegal Character
Input: C:/folder/fix>
Output: C:/folder/fix
        The input contained an illegal character (">").
        Remove the illegal character from the path.
Example 5: Reserved Device Name
Input: C:/folder/COM1
Output: C:/folder/folder
        The input contained a reserved device name (COM1).
        Change the reserved device name to a valid folder name.
Example 6: Mixed Slashes
Input: C:/folder\\file.txt
Output: C:/folder/file.txt
        The input had mixed slashes ("/" and "\\").
        Use consistent forward slashes ("/") throughout the path.
Example 7: No Errors
Input: C:/folder/file.txt
Output: There were no path errors found in the input.
"""

    print("Running OpenCode prompt...")

    # Set PATH to include node and npm
    node_path = r"C:\Program Files\nodejs"
    npm_path = os.path.expandvars(r"%APPDATA%\npm")
    os.environ["PATH"] = node_path + ";" + npm_path + ";" + os.environ.get("PATH", "")

    # Try opencode with full path - use 'run' command
    opencode_cmd = os.path.join(npm_path, "opencode.CMD")
    if os.path.exists(opencode_cmd):
        result = subprocess.run(
            f'"{opencode_cmd}" run "{prompt}"',
            shell=True,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
            env=os.environ,
        )
        print(f"Result: {result.returncode}")
        if result.returncode == 0:
            return result.stdout + result.stderr
        else:
            print(f"STDOUT: {result.stdout[:500] if result.stdout else 'None'}")
            print(f"STDERR: {result.stderr[:500] if result.stderr else 'None'}")
            return result.stderr

    return "OpenCode not found"
