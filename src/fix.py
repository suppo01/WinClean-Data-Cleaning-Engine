import subprocess
import os

from detect import extract_path_from_command
from typing import Any


def run_opencode_prompt(broken_code: str, potential_bug: str) -> Any:
    """Run OpenCode via server mode."""

    if os.path.isfile(broken_code):
        with open(broken_code, "r", encoding="utf-8") as f:
            broken_code = f.read()
    else:
        broken_code = extract_path_from_command(broken_code)

    prompt = f"""Fix Windows path errors in this code: {broken_code}

Errors to fix: {potential_bug}

Examples:
- UNC path //server/share -> /server/share  
- Missing drive letter folder/file -> C:/folder/file
- Illegal char C:/folder> -> C:/folder
- Reserved name C:/COM1 -> C:/folder
- Mixed slashes C:/folder\\file -> C:/folder/file
"""

    print("Running OpenCode via server...")

    # Start server and get response using Python's requests to localhost
    import socket
    import time

    # Check if server is already running
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_running = sock.connect_ex(("127.0.0.1", 4096)) == 0
    sock.close()

    if not server_running:
        # Try to start server in background
        npm_path = os.path.expandvars(r"%APPDATA%\npm")
        server_cmd = os.path.join(npm_path, "opencode.CMD")

        # Try to start server using bunx
        bun_path = r"C:\Users\molly\.bun\bin\bun.EXE"

        if os.path.exists(bun_path):
            subprocess.Popen(
                f'"{bun_path}" x opencode-ai serve',
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            time.sleep(10)  # Wait for server to start

    # Now try to get response via HTTP
    try:
        import requests

        response = requests.post(
            "http://127.0.0.1:4096/prompt",
            json={"prompt": prompt},
            stream=True,
            timeout=60,
        )

        # Handle SSE streaming
        result = []
        for line in response.iter_lines():
            if line:
                decoded = line.decode("utf-8")
                if decoded.startswith("data: "):
                    data = decoded[6:]
                    if data and data != "[DONE]":
                        print(data, end="", flush=True)
                        result.append(data)

        return "\n".join(result)
    except Exception as e:
        return f"Server error: {e}"
