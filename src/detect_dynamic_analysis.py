# ------ Import Block -------
import ast
import subprocess
import sys
import os
import re

from typing import Any
from detect_static import extract_path_from_command, FileSystem_Analyzer
# ----------------------------


# ----- Dynamic Analysis -----
def dynamic_analyzer(
    input_path: str, root: str = None, venv_path: str = None, *script_args: list[Any]
) -> None:
    """Sets up a virtual environment and runs the specified script or command within it."""

    # Checks if input is a path command (like "cd C:\path") or a script file
    path_commands = ["cd ", "dir ", "ls ", "mkdir "]
    is_path_command = any(input_path.lower().startswith(cmd) for cmd in path_commands)

    if is_path_command:
        # Handles path commands - extracts path and validate it using venv
        print(f"Analyzing path command: {input_path}")

        # Extracts the path from the command (e.g., "cd C:\path" -> "C:\path")
        path = extract_path_from_command(input_path)

        # Determines python executable in the venv
        if not os.path.exists(venv_path):
            print(f"Creating virtual environment at {venv_path}...")
            result = subprocess.run(
                [sys.executable, "-m", "venv", venv_path],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                print(f"Failed to create venv: {result.stderr}")
                return

        if os.name == "nt":
            python_executable = os.path.join(venv_path, "Scripts", "python.exe")
        else:
            python_executable = os.path.join(venv_path, "bin", "python")

        # Creates a test script that tries to use the path
        test_code = f'''
import os
target_path = r"{path}"
try:
    os.listdir(target_path)
    print("SUCCESS: Path is accessible")
except FileNotFoundError as e:
    print(f"FileNotFoundError: {{e}}")
except NotADirectoryError as e:
    print(f"NotADirectoryError: {{e}}")
except PermissionError as e:
    print(f"PermissionError: {{e}}")
except OSError as e:
    print(f"OSError: {{e}}")
except Exception as e:
    print(f"Exception: {{type(e).__name__}}: {{e}}")
'''

        result = subprocess.run(
            [python_executable, "-c", test_code],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0 or "Error" in result.stdout:
            print("Path validation errors:")
            print(f" - {result.stdout.strip()}")
        else:
            print(f" - {result.stdout.strip()}")
        return

    # Otherwise, treats as Python script file
    script_path = input_path

    # Creates virtual environment if it doesn't exist
    if not os.path.exists(venv_path):
        print(f"Creating virtual environment at {venv_path}...")
        try:
            result = subprocess.run(
                [sys.executable, "-m", "venv", venv_path],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                print(f"Failed to create venv: {result.stderr}")
                return
            print(f"Successfully created virtual environment at {venv_path}")
        except Exception as e:
            print(f"Error creating venv: {e}")
            return
    else:
        print(f"Using existing virtual environment at {venv_path}")

    # Determines the correct Python executable path based on the operating system
    # Checks for Windows first
    if os.name == "nt":
        python_executable = os.path.join(venv_path, "Scripts", "python.exe")
    # Unix, Linux, and Mac case
    else:
        python_executable = os.path.join(venv_path, "bin", "python")

    # Ensures the executable exists
    if not os.path.exists(python_executable):
        print(f"Error: Python executable not found at {python_executable}")
        return

    # Checks if script_path is a directory
    if os.path.isdir(script_path):
        print(f"Error: {script_path} is a directory, not a Python file")
        return

    # Determines if we should run as module or script
    script_dir, script_name = os.path.split(script_path)
    module_name = script_name.replace(".py", "")

    # Builds the command list for subprocess.run()
    # Uses -m to run as module if it has main() function
    # Builds the command list for subprocess.run()
    # Runs the Python file directly - it will execute main() if __name__ == "__main__"
    path_command = [python_executable, script_path] + list(script_args)

    # Separates out the script name for error messages
    directory_name, script_name = os.path.split(script_path)

    print(f"Running command: {path_command}")

    try:
        # Uses subprocess.run to execute the command and captures the output and errors
        # capture_output=True captures stdout and stderr. text=True decodes bytes to strings.
        # This is the base case without exceptions thrown
        result = subprocess.run(
            path_command, capture_output=True, text=True, check=True
        )
        print("STANDARD OUTPUT:", result.stdout)
        print("STANDARD ERRORS:", result.stderr)
    # This is the case for when a non-zero exit code is returned by subprocess
    except subprocess.CalledProcessError as e:
        print(f"Process failed with return code {e.returncode}")
        print("STANDARD OUTPUT:", e.stdout)
        print("STANDARD ERRORS:", e.stderr)

        # Runs script in venv and catch all runtime exceptions
        print("Analyzing script in real-time...")

        # Creates a wrapper that catches all exceptions
        wrapper_code = f'''
import sys
sys.path.insert(0, "{os.path.dirname(script_path)}")
try:
    with open("{script_path.replace("\\", "\\\\")}", "r") as f:
        code = f.read()
    exec(compile(code, "{script_path.replace("\\", "\\\\")}", "exec"))
except FileNotFoundError as e:
    print(f"FileNotFoundError: {{e}}")
except NotADirectoryError as e:
    print(f"NotADirectoryError: {{e}}")
except PermissionError as e:
    print(f"PermissionError: {{e}}")
except OSError as e:
    print(f"OSError: {{e}}")
except ValueError as e:
    print(f"ValueError: {{e}}")
except Exception as e:
    print(f"Exception: {{type(e).__name__}}: {{e}}")
'''

        result = subprocess.run(
            [python_executable, "-c", wrapper_code], capture_output=True, text=True
        )

        if result.stdout:
            print("Runtime errors found:")
            for line in result.stdout.strip().split("\n"):
                print(f" - {line}")
        else:
            print("No runtime errors detected.")
    # This is the case for when the file or path specified could not be found
    # This handles missing drive letter, device names, and a file that doesn't exist at the path specified
    except FileNotFoundError:
        if script_path == None:
            print(f"Error: The path {path_command} was not found.")
        else:
            print(f"Error: The script {script_name} was not found.")
    # This is the case for when the file or path specified contains a syntax error
    # This handles illegal characters, mixed slashes, and UNC paths within the working directory
    except SyntaxError as e:
        if script_path == None:
            print(f"Error: The path {path_command} contains a syntax error.")
        else:
            print(f"Error: The script {script_name} contains a syntax error.")
            # Falls back to path analysis for Unicode escape errors
            if "unicodeescape" in str(e):
                print("Analyzing paths in file despite Unicode escape errors...")
                try:
                    with open(script_path, "r", encoding="utf-8") as f:
                        code = f.read()

                    # Reuses static analyzer for path validation
                    analyzer = FileSystem_Analyzer(root)
                    lines = code.split("\n")
                    for line_num, line in enumerate(lines, 1):
                        import re

                        strings = re.findall(r'"([^"]*)"', line) + re.findall(
                            r"'([^']*)'", line
                        )
                        for string_literal in strings:
                            if string_literal:
                                analyzer._check(string_literal, lineno=line_num)

                    if analyzer.errors:
                        print("Path issues found in file:")
                        for err in analyzer.errors:
                            print(" -", err)
                    else:
                        print("No path issues detected despite syntax error.")
                except Exception as path_err:
                    print(f"Could not analyze paths: {path_err}")
    # This is the case for when the file of path specified is not able to perform the operation requested
    # This handles illegal characters, mixed slashes, UNC paths in the working directory, and reserved device names
    except ValueError:
        if script_path == None:
            print(f"Error: A value error occurred with path {path_command}.")
        else:
            print(f"Error: A value error occurred with script {script_name}.")
    # This is the case for when there is an operating system related error when trying to access the file or path specified
    except OSError:
        if script_path == None:
            print(f"Error: An OS error occurred while trying to access {path_command}.")
        else:
            print(f"Error: An OS error occurred while trying to access {script_name}.")
    # This is the case for when there is a permission error when trying to access the file or path specified
    except PermissionError:
        if script_path == None:
            print(f"Error: Permission denied when trying to access {path_command}.")
        else:
            print(f"Error: Permission denied when trying to access {script_name}.")
