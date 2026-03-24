"""
Test file for Z3 Symbolic Path Analysis

This file contains various patterns that test WinClean's Z3-based
symbolic path analysis for detecting dynamically built paths.
"""

import os
import sys


# ============================================================
# TEST 1: Direct concatenation with input()
# ============================================================
def test_input_concatenation():
    """User input concatenated with base path."""
    base = "C:\\Users\\molly\\"
    user_input = input("Enter folder name: ")
    full_path = base + user_input  # DANGEROUS: user input in path
    os.listdir(full_path)


# ============================================================
# TEST 2: f-string with input
# ============================================================
def test_fstring_input():
    """f-string building path from user input."""
    username = input("Enter username: ")
    config_path = f"C:\\Users\\{username}\\config"  # DANGEROUS
    os.chdir(config_path)


# ============================================================
# TEST 3: Multiple concatenations
# ============================================================
def test_multiple_concat():
    """Path built through multiple string operations."""
    drive = "C:"
    sep = "\\"
    folder = input("Folder: ")
    subfolder = input("Subfolder: ")
    path = drive + sep + folder + sep + subfolder  # DANGEROUS
    os.listdir(path)


# ============================================================
# TEST 4: os.path.join with user input
# ============================================================
def test_path_join_input():
    """os.path.join with variable components."""
    base_path = "C:\\Data"
    user_folder = input("Folder name: ")
    full = os.path.join(base_path, user_folder)  # DANGEROUS
    os.listdir(full)


# ============================================================
# TEST 5: sys.argv usage
# ============================================================
def test_sysargv():
    """Path built from command line argument."""
    if len(sys.argv) > 1:
        target = sys.argv[1]  # DANGEROUS: untrusted
        os.chdir(target)


# ============================================================
# TEST 6: Environment variable + user input
# ============================================================
def test_env_concat():
    """Path using environment variable with user input."""
    home = os.environ.get("USERPROFILE", "C:\\Users\\default")
    folder = input("Folder: ")
    path = os.path.join(home, folder)  # DANGEROUS
    os.listdir(path)


# ============================================================
# TEST 7: Safe static path (should NOT trigger)
# ============================================================
def test_static_path():
    """Static path that should be safe."""
    static = "C:\\Users\\molly\\Documents"
    os.listdir(static)  # SAFE: no user input


# ============================================================
# TEST 8: Conditional path building
# ============================================================
def test_conditional():
    """Path built based on condition."""
    mode = input("Enter mode (admin/user): ")
    if mode == "admin":
        base = "C:\\Admin"
    else:
        base = "C:\\Users"
    os.chdir(base)  # DANGEROUS: user input affects path


# ============================================================
# TEST 9: List comprehension with paths
# ============================================================
def test_list_comprehension():
    """Building multiple paths from user input."""
    folders = input("Enter folders (comma sep): ").split(",")
    paths = [f"C:\\Data\\{f.strip()}" for f in folders]  # DANGEROUS
    for p in paths:
        print(os.listdir(p))


# ============================================================
# TEST 10: Path with reserved name potential
# ============================================================
def test_reserved_potential():
    """User might enter reserved name."""
    filename = input("Enter filename: ")
    full = f"C:\\Users\\molly\\{filename}"  # DANGEROUS
    with open(full, "r") as f:
        f.read()


# ============================================================
# TEST 11: Format string attack
# ============================================================
def test_format_attack():
    """Path built with format()."""
    template = "C:\\Users\\{}\\{}"
    user = input("Username: ")
    subdir = input("Subdirectory: ")
    path = template.format(user, subdir)  # DANGEROUS
    os.listdir(path)


# ============================================================
# TEST 12: Safe - pure calculation
# ============================================================
def test_safe_calculation():
    """Path calculation that's safe."""
    base = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base, "data")  # SAFE
    os.listdir(data_dir)


# ============================================================
# TEST 13: Unsafe - string replace
# ============================================================
def test_replace_danger():
    """Path modified with replace()."""
    user_input = input("Enter path modifier: ")
    base = "C:\\Users\\molly\\docs"
    modified = base.replace("docs", user_input)  # DANGEROUS
    os.listdir(modified)


# ============================================================
# TEST 14: Path with strip/sanitize attempt
# ============================================================
def test_sanitize_attempt():
    """User sanitizes but may miss some cases."""
    raw = input("Enter path: ")
    cleaned = raw.strip().replace("..", "")  # DANGEROUS
    os.chdir(cleaned)


# ============================================================
# TEST 15: Combined - environment + input
# ============================================================
def test_combined():
    """Complex path building with multiple sources."""
    user = input("User: ")
    app = input("App: ")
    base = os.environ.get("PROGRAMFILES", "C:\\Program Files")
    path = os.path.join(base, user, app, "config")  # DANGEROUS
    os.listdir(path)


if __name__ == "__main__":
    print("This file tests WinClean's Z3 symbolic path analysis.")
    print("Run WinClean on this file to see detection results.")
    print()
    print("Expected flags:")
    print("  DANGEROUS: Tests 1-6, 8-11, 13-15 (use user input in paths)")
    print("  SAFE:      Tests 7, 12 (static paths only)")
    print()
    print("Run: winclean --mode static --script-path test_suite/test_z3_paths.py")
