# ------ Import Block -------
import argparse
import ast
import os

from typing import Any
# ----------------------------


# ----- Static Analysis ------
class FileSystem_Analyzer(ast.NodeVisitor):
    """Analyzes Python code for filesystem directory usage."""

    def __init__(self, root: Any = None):
        """Creates an instance of the class."""
        self.root = root if root else os.getcwd()
        self.errors = []

    def visit_Call(self, node) -> None:
        """Visits a node in the code passed in for ast."""
        # Detects os.listdir("folder")
        if isinstance(node.func, ast.Attribute) and node.func.attr == "listdir":
            folder = self._extract_string(node.args[0])
            if folder:
                self._check(folder, node.lineno)

        # Detects Path("folder").iterdir()
        if isinstance(node.func, ast.Attribute) and node.func.attr == "iterdir":
            if isinstance(node.func.value, ast.Call):
                if (
                    isinstance(node.func.value.func, ast.Name)
                    and node.func.value.func.id == "Path"
                ):
                    folder = self._extract_string(node.func.value.args[0])
                    if folder:
                        self._check(folder, node.lineno)

        self.generic_visit(node)

    def _extract_string(self, node) -> str | None:
        """Extracts a string value from and ast node."""
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        return None

    def _check(self, folder: str, lineno: int) -> None:
        """Checks for inconsistencies with Windows path commands."""
        # Puts the original folder value into a variable for printing error messages
        raw = folder
        # Cleans up folder value to fit expected conditions for checking paths
        folder = folder.strip()

        # Detects UNC path using a string function and the pattern used to find UNC paths
        if folder.startswith("\\\\"):
            # This is used for path commands being checked as the fake line number being employed is 0
            if lineno == 0:
                self.errors.append(
                    f"UNC path '{raw}' cannot be used as a current directory in Windows CMD"
                )
            else:
                self.errors.append(
                    f"Line {lineno}: UNC path '{raw}' cannot be used as a current directory in Windows CMD"
                )
            return

        # Detects illegal characters using a set containing all illegal characters
        illegal_chars = set('<>:"|?*')
        if any(c in illegal_chars for c in folder):
            # This is used for path commands being checked as the fake line number being employed is 0
            if lineno == 0:
                self.errors.append(f"Path '{raw}' contains illegal Windows characters")
            else:
                self.errors.append(
                    f"Line {lineno}: Path '{raw}' contains illegal Windows characters"
                )
            return

        # Detects mixed slashes using a functionality of strings
        if "/" in folder and "\\" in folder:
            # This is used for path commands being checked as the fake line number being employed is 0
            if lineno == 0:
                self.errors.append(f"Path '{raw}' mixes slash styles")
            else:
                self.errors.append(f"Line {lineno}: Path '{raw}' mixes slash styles")
            return

        # Detects missing drive letter using a string function
        # For Python file analysis (lineno > 0), always require drive letters
        # For command line analysis (lineno == 0), allow relative paths if root is provided
        if (
            not folder.startswith("\\")
            and ":" not in folder
            and (lineno > 0 or (lineno == 0 and not self.root))
            and not folder.startswith("/")
        ):
            # This is used for path commands being checked as the fake line number being employed is 0
            if lineno == 0:
                self.errors.append(f"Path '{raw}' is missing a drive letter")
            else:
                self.errors.append(
                    f"Line {lineno}: Path '{raw}' is missing a drive letter"
                )
            return

        # Detects reserved names using a dictionary containing all reserved device names
        reserved = {
            "CON",
            "PRN",
            "AUX",
            "NUL",
            *(f"COM{i}" for i in range(1, 10)),
            *(f"LPT{i}" for i in range(1, 10)),
        }
        base = os.path.basename(folder).upper()
        if base in reserved:
            # This is used for path commands being checked as the fake line number being employed is 0
            if lineno == 0:
                self.errors.append(
                    f"Path '{raw}' uses reserved Windows device name '{base}'"
                )
            else:
                self.errors.append(
                    f"Line {lineno}: Path '{raw}' uses reserved Windows device name '{base}'"
                )
            return

        # Resolves the path using os package
        full = os.path.abspath(os.path.join(self.root, folder))

        # Does an existence check using os
        if not os.path.isdir(full):
            # This is used for path commands being checked as the fake line number being employed is 0
            if lineno == 0:
                self.errors.append(f"Folder does not exist -> {full}")
            else:
                self.errors.append(f"Line {lineno}: Folder does not exist -> {full}")


def extract_path_from_command(cmd: str) -> str:
    """Extracts a path from a Windows command."""
    parts = cmd.strip().split()

    # Used when a path is given with a command like cd
    if len(parts) >= 2:
        return parts[1]
    # Used when just a path is given
    if len(parts) == 1:
        return parts[0]
    # Used for the empty case
    return ""


def validate_windows_path(path: str, root: Any = None) -> list[str]:
    """Validates a raw Windows path command."""
    # Creates an instance of the FileSystem_Analyzer class
    analyzer = FileSystem_Analyzer(root)
    # Calls FileSystem_Analyzer._check to check for any potential errors
    analyzer._check(path, lineno=0)
    # Returns the list of errors found
    return analyzer.errors


def analyze_folder_access():
    """Runs static analysis on either Python code or a path command for possible Windows pathing errors."""
    # Sets up a parser for CLI use
    parser = argparse.ArgumentParser(
        description="Analyze Python code OR a Windows path command."
    )
    # Adds an input argument that has a help flag for what the input should be
    parser.add_argument("input", help="Python file OR a path command")
    # Adds an optional root argument for setting the filesystem root with a default of None
    parser.add_argument(
        "--root", help="Filesystem root for Python code analysis", default=None
    )

    # Collects arguments given to the parser through CLI
    args = parser.parse_args()
    # Transfers the input arguments to user_input for easier access
    user_input = args.input

    # 1. If input is a file → it is treated as Python code and uses AST
    # If input is a file, it is open and read using utf-8 encoding
    if os.path.isfile(user_input):
        with open(user_input, "r", encoding="utf-8") as f:
            code = f.read()

        # Creates an instance of the FileSystem_Analyzer class and visits the AST of the code
        analyzer = FileSystem_Analyzer(args.root)

        # Try to parse as AST first, if fails fall back to string analysis
        try:
            analyzer.visit(ast.parse(code))
        except SyntaxError:
            # Fall back to line-by-line string analysis for path extraction
            import re

            lines = code.split("\n")
            for line_num, line in enumerate(lines, 1):
                # Find all string literals in this line
                strings = re.findall(r'"([^"]*)"', line) + re.findall(
                    r"'([^']*)'", line
                )
                for string_literal in strings:
                    if string_literal:  # Only check non-empty strings
                        analyzer._check(string_literal, lineno=line_num)

        # If the analyzer, an instance of the FileSystem_Analyzer class, has any errors, they are printed out
        if analyzer.errors:
            print("\nIssues found:")
            for err in analyzer.errors:
                print(" -", err)
        else:
            print("No folder path issues detected.")
        return

    # 2. Otherwise → treats input as a path command and focuses on validating the path
    # The path is extracted from the command input
    path = extract_path_from_command(user_input)
    # The path is validated using the validate_windows_path function and errors are collected in the errors variable
    errors = validate_windows_path(path, args.root)

    # If any errors were found during validation, they are printed out
    if errors:
        print("\nIssues found:")
        for err in errors:
            print(" -", err)
    else:
        print("No path issues detected.")


# ----------------------------


# ----- Dynamic Analysis -----

if __name__ == "__main__":
    analyze_folder_access()
