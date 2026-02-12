# main.py
import argparse
import sys
from detect import analyze_folder_access
from detect import dynamic_analyzer


def main():
    parser = argparse.ArgumentParser(description="WinClean - Choose Analysis Type")

    # Selects mode flag: static or dynamic
    parser.add_argument(
        "--mode",
        choices=["static", "dynamic"],
        required=True,
        help="Choose analysis mode: static or dynamic",
    )

    # Provides root for path if specified
    parser.add_argument("--root", help="Filesystem root path")

    # Provides arguments for either script path or path command
    parser.add_argument("--script-path", help="Python script file for static analysis")
    parser.add_argument("--path-command", help="Command path for static analysis")

    # Provides argument for venv path for dynamic analysis
    parser.add_argument(
        "--venv", help="Virtual environment path (required for dynamic)"
    )

    args = parser.parse_args()

    if args.mode == "static":
        # Validate static mode inputs
        if not args.script_path and not args.path_command:
            print("Error: --script-path or --path-command required for static mode")
            return

        # Set up argv for analyze_folder_access
        argv = ["main.py"]
        if args.script_path:
            argv.append(args.script_path)
        elif args.path_command:
            argv.append(args.path_command)
        if args.root:
            argv.extend(["--root", args.root])

        print("Running static analysis...")
        input_path = args.script_path or args.path_command
        analyze_folder_access(input_path, args.root)

    elif args.mode == "dynamic":
        # Validate dynamic mode inputs
        if not args.script_path and not args.path_command:
            print("Error: --script-path or --path-command required for dynamic mode")
            return
        if not args.venv:
            print("Error: --venv required for dynamic mode")
            return

        print("Running dynamic analysis...")
        input_path = args.script_path or args.path_command
        dynamic_analyzer(input_path, args.root, args.venv)


if __name__ == "__main__":
    main()
