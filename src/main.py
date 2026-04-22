# main.py
import argparse
import os
from pathlib import Path
from detect_static import analyze_folder_access
from detect_dynamic import dynamic_analyzer
from OpenCode_runner import run_opencode_prompt_sync


def main():
    parser = argparse.ArgumentParser(
        description="WinClean - Windows Path Cleaning Engine"
    )

    parser.add_argument(
        "--mode",
        choices=["static", "dynamic"],
        required=True,
        help="Choose analysis mode: static or dynamic",
    )

    parser.add_argument("--root", help="Filesystem root path")
    parser.add_argument("--script-path", help="Python script file")
    parser.add_argument("--path-command", help="Command path for static analysis")
    parser.add_argument(
        "--venv", help="Virtual environment path (required for dynamic)"
    )

    args = parser.parse_args()

    def validate_and_normalize_path(path):
        if path:
            normalized = str(Path(path).resolve())
            if not os.path.exists(normalized):
                raise FileNotFoundError(f"Path does not exist: {normalized}")
            return normalized
        return None

    try:
        root = validate_and_normalize_path(args.root)
        script_path = validate_and_normalize_path(args.script_path)
        path_command = args.path_command  # Don't validate - it's a command string
        venv = validate_and_normalize_path(args.venv)

        input_path = (
            script_path or path_command
        )  # Use script_path if available, else path_command

        if args.mode == "static":
            if not input_path:
                raise ValueError(
                    "--script-path or --path-command required for static mode"
                )

            print("Running static analysis...")
            # Pass the original path_command string for command analysis
            if path_command and not script_path:
                analysis = analyze_folder_access(path_command, root or "")
            else:
                analysis = analyze_folder_access(input_path, root or "")

        elif args.mode == "dynamic":
            if not input_path:
                raise ValueError(
                    "--script-path or --path-command required for dynamic mode"
                )
            if not venv:
                raise ValueError("--venv is required for dynamic mode")

            print("Running dynamic analysis...")
            analysis = dynamic_analyzer(input_path, root or "", venv or "")

        print("Analysis complete.")
        print(
            run_opencode_prompt_sync(
                broken_code=input_path or "", potential_bug=analysis or ""
            )
        )

    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
