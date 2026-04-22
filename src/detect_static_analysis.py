# ------ Import Block -------
import ast
import subprocess
import sys
import os
import re

from typing import Any
# ----------------------------


# ----- Symbolic Path Analysis with Z3 -----
def check_with_z3(code: str) -> list[str]:
    """Check code using Z3 symbolic path analysis - only path-related issues."""
    try:
        from z3 import Solver, String, Contains, StringVal, Or, sat

        tree = ast.parse(code)
        user_inputs = {}  # var_name -> True (tracks that this var gets user input)
        errors = []

        def get_func_name(node):
            if isinstance(node, ast.Name):
                return node.id
            if isinstance(node, ast.Attribute):
                if isinstance(node.value, ast.Name):
                    return f"{node.value.id}.{node.attr}"
                return node.attr
            return ""

        def looks_like_path(node):
            """Check if AST node involves path operations."""
            if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
                return looks_like_path(node.left) or looks_like_path(node.right)
            if isinstance(node, ast.JoinedStr):
                return any(
                    (
                        isinstance(v, ast.Constant)
                        and isinstance(v.value, str)
                        and ("/" in v.value or "\\" in v.value or ":" in v.value)
                    )
                    for v in node.values
                )
            if isinstance(node, ast.Call):
                func = get_func_name(node.func)
                return func in ("join", "path.join")
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                return "/" in node.value or "\\" in node.value or ":" in node.value
            return False

        def uses_user_input(node):
            """Check if expression uses any user input variables."""
            if isinstance(node, ast.Name):
                return node.id in user_inputs
            if isinstance(node, ast.Attribute):
                return uses_user_input(node.value)
            if isinstance(node, ast.BinOp):
                return uses_user_input(node.left) or uses_user_input(node.right)
            if isinstance(node, ast.Call):
                return any(uses_user_input(arg) for arg in node.args)
            return False

        def check_path_dangers(path_expr, lineno, desc=""):
            """Check if symbolic path could be dangerous."""
            ILLEGAL = set('<>:"|?*')
            RESERVED = {
                "CON",
                "PRN",
                "AUX",
                "NUL",
                *{f"COM{i}" for i in range(1, 10)},
                *{f"LPT{i}" for i in range(1, 10)},
            }

            for char in ILLEGAL:
                solver = Solver()
                solver.add(Contains(path_expr, StringVal(char)))
                if solver.check() == sat:
                    errors.append(f"Line {lineno}: Path MAY contain illegal '{char}'")

            for name in RESERVED:
                solver = Solver()
                solver.add(
                    Or(
                        Contains(path_expr, StringVal(f"/{name}")),
                        Contains(path_expr, StringVal(f"\\{name}")),
                        Contains(path_expr, StringVal(f":\\{name}")),
                    )
                )
                if solver.check() == sat:
                    errors.append(f"Line {lineno}: Path MAY contain reserved '{name}'")

        # Visit all nodes
        for node in ast.walk(tree):
            # Track input() assignments
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        if isinstance(node.value, ast.Call):
                            func = get_func_name(node.value.func)
                            if func == "input":
                                user_inputs[target.id] = True

            # Track sys.argv usage
            if isinstance(node, ast.Call):
                func = get_func_name(node.func)
                if func == "__getitem__" and isinstance(node.func, ast.Attribute):
                    if isinstance(node.func.value, ast.Attribute):
                        if (
                            isinstance(node.func.value.value, ast.Name)
                            and node.func.value.value.id == "sys"
                            and node.func.value.attr == "argv"
                        ):
                            # sys.argv used - check if it's in a path operation
                            parent_call = node
                            for parent in ast.walk(tree):
                                if isinstance(parent, ast.Call):
                                    for arg in parent.args:
                                        if arg == node:
                                            path_func = get_func_name(parent.func)
                                            if path_func in (
                                                "listdir",
                                                "chdir",
                                                "open",
                                                "exists",
                                                "isdir",
                                                "isfile",
                                                "walk",
                                            ):
                                                errors.append(
                                                    f"Line {parent.lineno}: sys.argv used in path operation"
                                                )

            # Check path operations that use user input
            if isinstance(node, ast.Call):
                func = get_func_name(node.func)
                if func in (
                    "listdir",
                    "chdir",
                    "open",
                    "exists",
                    "isdir",
                    "isfile",
                    "walk",
                ):
                    for arg in node.args:
                        if uses_user_input(arg):
                            check_path_dangers(arg, node.lineno)
                        elif looks_like_path(arg):
                            check_path_dangers(arg, node.lineno)

        return errors

    except ImportError:
        return ["Z3 not installed - run: pip install z3-solver"]
    except SyntaxError:
        return []


def check_path_concatenation(code: str) -> list[str]:
    """Quick regex-based check for path concatenation patterns - path-related only."""
    errors = []

    lines = code.split("\n")
    for lineno, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("#"):
            continue

        # Check for input() + path operations in same line
        if "input(" in line:
            if any(
                x in line
                for x in [
                    "+",
                    "os.path",
                    "os.listdir",
                    "os.chdir",
                    "os.open",
                    "os.sep",
                    "\\\\",
                ]
            ):
                errors.append(f"Line {lineno}: input() with path concatenation")

        # Check for f-strings building paths with variables
        if ('f"' in line or "f'" in line) and "{" in line:
            if any(x in line for x in ["\\\\", "os.path", ":\\\\", ":///"]):
                errors.append(f"Line {lineno}: f-string builds path with variable")

        # Check for os.path.join with user input
        if "os.path.join" in line and any(x in line for x in ["input(", "argv"]):
            errors.append(f"Line {lineno}: os.path.join with user input")

    return errors


class DynamicPathAnalyzer(ast.NodeVisitor):
    """Detects dynamically built paths using AST analysis."""

    def __init__(self):
        self.errors = []
        self.user_input_vars = set()

    def visit_Assign(self, node) -> None:
        if isinstance(node.value, ast.Call):
            func_name = self._get_func_name(node.value.func)
            if func_name == "input":
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        self.user_input_vars.add(target.id)
                        self.errors.append(
                            f"Line {node.lineno}: Variable '{target.id}' receives user input"
                        )

        if isinstance(node.value, ast.BinOp) and isinstance(node.value.op, ast.Add):
            if self._contains_user_input(node.value):
                self.errors.append(
                    f"Line {node.lineno}: Path built from concatenation with user input"
                )

        if isinstance(node.value, ast.JoinedStr):
            has_path = any(
                self._looks_like_path(v.value)
                for v in node.value.values
                if isinstance(v, ast.Constant) and isinstance(v.value, str)
            )
            has_var = any(
                isinstance(v, ast.FormattedValue) and self._is_user_input(v.value)
                for v in node.value.values
            )
            if has_path and has_var:
                self.errors.append(
                    f"Line {node.lineno}: f-string builds path with user input"
                )

        self.generic_visit(node)

    def visit_Call(self, node) -> None:
        func_name = self._get_func_name(node.func)

        if func_name in (
            "listdir",
            "chdir",
            "open",
            "exists",
            "isdir",
            "isfile",
            "walk",
        ):
            for arg in node.args:
                if self._uses_user_input(arg):
                    self.errors.append(
                        f"Line {node.lineno}: Path operation uses user input"
                    )
                    break

        if func_name in ("join", "path.join"):
            for arg in node.args:
                if self._uses_user_input(arg):
                    self.errors.append(
                        f"Line {node.lineno}: os.path.join uses user input"
                    )
                    break

        self.generic_visit(node)

    def _get_func_name(self, node) -> str:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            if isinstance(node.value, ast.Name):
                return f"{node.value.id}.{node.attr}"
            return node.attr
        if isinstance(node, ast.Call):
            return self._get_func_name(node.func)
        return ""

    def _uses_user_input(self, node) -> bool:
        if isinstance(node, ast.Name):
            return node.id in self.user_input_vars
        if isinstance(node, ast.Attribute):
            return self._uses_user_input(node.value)
        return False

    def _is_user_input(self, node) -> bool:
        return self._uses_user_input(node)

    def _contains_user_input(self, node) -> bool:
        if isinstance(node, ast.Name):
            return node.id in self.user_input_vars
        if isinstance(node, ast.BinOp):
            return self._contains_user_input(node.left) or self._contains_user_input(
                node.right
            )
        return False

    def _looks_like_path(self, s: str) -> bool:
        if not s or not isinstance(s, str):
            return False
        import re

        return bool(
            re.search(r"^[A-Za-z]:[/\\]", s)
            or s.startswith("/")
            or s.startswith("\\")
            or re.search(r"[/\\]{2,}", s)
        )


def check_dynamic_path(code: str) -> list[str]:
    """Check code for dynamically built paths."""
    try:
        tree = ast.parse(code)
        analyzer = DynamicPathAnalyzer()
        analyzer.visit(tree)
        return analyzer.errors
    except SyntaxError:
        return []


def analyze_dynamic_paths(code: str) -> list[str]:
    """Analyze code for dynamically built paths using Z3 symbolic analysis."""
    errors = []
    errors.extend(check_path_concatenation(code))
    errors.extend(check_with_z3(code))  # Z3 symbolic analysis
    return errors


# --------------------------------


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

        # Detects print("path") - extracts any string arguments that look like paths
        if isinstance(node.func, ast.Name) and node.func.id == "print":
            for arg in node.args:
                folder = self._extract_string(arg)
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
        if not any(c in folder for c in "/\\:"):
            return

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
        illegal_chars = set('<>"|?*')
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
            not folder.startswith("\\\\")
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


def validate_windows_path(path: str, root: str = "") -> list[str]:
    """Validates a raw Windows path command."""
    # Creates an instance of the FileSystem_Analyzer class
    analyzer = FileSystem_Analyzer(root)
    # Calls FileSystem_Analyzer._check to check for any potential errors
    analyzer._check(path, lineno=0)
    # Returns the list of errors found
    return analyzer.errors


def analyze_folder_access(input_path: str, root: str = "") -> None:
    """Runs static analysis on either Python code or a path command for possible Windows pathing errors."""
    # Assigns input_path to a function specific variable user_input
    user_input = input_path

    # 1. If input is a file → it is treated as Python code and uses AST
    # If input is a file, it is open and read using utf-8 encoding
    if os.path.isfile(user_input):
        with open(user_input, "r", encoding="utf-8") as f:
            code = f.read()

        # Creates an instance of the FileSystem_Analyzer class and visits the AST of the code
        analyzer = FileSystem_Analyzer(root)

        # Trys to parse as AST first, if fails fall back to string analysis
        try:
            analyzer.visit(ast.parse(code))
        except SyntaxError:
            # Falls back to line-by-line string analysis for path extraction
            lines = code.split("\n")
            for line_num, line in enumerate(lines, 1):
                # Finds all string literals in this line
                strings = re.findall(r'"([^"]*)"', line) + re.findall(
                    r"'([^']*)'", line
                )
                for string_literal in strings:
                    if string_literal:  # Only check non-empty strings
                        analyzer._check(string_literal, lineno=line_num)

        # Run symbolic/dynamic path analysis
        print("\nRunning dynamic path analysis...")
        dynamic_errors = analyze_dynamic_paths(code)
        all_errors = analyzer.errors + dynamic_errors

        # If the analyzer, an instance of the FileSystem_Analyzer class, has any errors, they are printed out
        if all_errors:
            print("\nIssues found:")
            for err in all_errors:
                print(" -", err)
        else:
            print("No folder path issues detected.")
        return

    # 2. Otherwise → treats input as a path command and focuses on validating the path
    # The path is extracted from the command input
    path = extract_path_from_command(user_input)
    # The path is validated using the validate_windows_path function and errors are collected in the errors variable
    errors = validate_windows_path(path, root)

    # If any errors were found during validation, they are printed out
    if errors:
        print("\nIssues found:")
        for err in errors:
            print(" -", err)
    else:
        print("No path issues detected.")


# ----------------------------