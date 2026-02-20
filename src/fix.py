# ------ Import Block -------
import requests
import time
import subprocess
import os

from detect import extract_path_from_command
from typing import Any
# ----------------------------


# --- Opencode Server Call ---
def run_opencode_prompt(broken_code: str, potential_bug: str) -> Any:
    # Starts the server
    server = subprocess.Popen(
        ["opencode", "serve", "--port", "4096"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    time.sleep(2)

    if os.path.isfile(broken_code):
        with open(broken_code, "r", encoding="utf-8") as f:
            broken_code = f.read()
        
    else:
        broken_code = extract_path_from_command(broken_code)

    try:
        # Builds a dynamic prompt with passed in variables for broken code and analysis of the code
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
            Input: C:/folder\file.txt
            Output: C:/folder/file.txt
                    The input had mixed slashes ("/" and "\").
                    Use consistent forward slashes ("/") throughout the path.
            Example 7: No Errors
            Input: C:/folder/file.txt
            Output: There were no path errors found in the input.
            """
        
        # Collects the response from the server and returns it as JSON
        response = requests.post(
            "http://127.0.0.1:4096/prompt",
            json={"prompt": prompt}
        )
        return response.json()
    # Stops the server
    finally:
        server.terminate()


