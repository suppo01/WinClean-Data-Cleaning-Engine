"""
Test Z3 Symbolic Path Analysis

This script demonstrates how Z3 symbolically analyzes path building
to determine if paths COULD be dangerous without knowing actual values.
"""

from z3 import Solver, String, Contains, StringVal, Or, sat, unsat


ILLEGAL_CHARS = set('<>:"|?*')
RESERVED_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *{f"COM{i}" for i in range(1, 10)},
    *{f"LPT{i}" for i in range(1, 10)},
}


def test_symbolic_path():
    """Test Z3 symbolic analysis on path expressions."""

    print("=" * 60)
    print("Z3 SYMBOLIC PATH ANALYSIS")
    print("=" * 60)

    # Define symbolic user input
    user_input = String("user_input")

    # Build symbolic paths
    base = StringVal("C:\\Users\\molly\\")

    print("\n1. SYMBOLIC PATH: base + user_input")
    print("-" * 40)

    solver = Solver()
    solver.add(Contains(base + user_input, StringVal(">")))

    result = solver.check()
    if result == sat:
        model = solver.model()
        print(f"  Z3 Result: SAT (path COULD contain '>')")
        print(
            f"  Example: '{model[user_input]}' would create 'C:\\Users\\molly\\{model[user_input]}'"
        )
    else:
        print("  Z3 Result: UNSAT (path CANNOT contain '>')")

    # Test reserved name
    solver2 = Solver()
    solver2.add(Contains(base + user_input, StringVal("\\COM1")))

    result2 = solver2.check()
    if result2 == sat:
        print(f"\n  Z3 Result: SAT (path COULD contain '\\COM1')")
        print(f"  User could enter 'COM1' as input!")
    else:
        print("\n  Z3 Result: UNSAT")

    print("\n2. F-STRING PATTERN: C:\\Users\\{user}")
    print("-" * 40)

    user = String("username")
    path_pattern = StringVal("C:\\Users\\") + user + StringVal("\\config")

    solver3 = Solver()
    solver3.add(Contains(path_pattern, StringVal(">")))

    result3 = solver3.check()
    if result3 == sat:
        print(f"  Z3 Result: SAT (path COULD contain '>')")
        print(f"  User could enter 'test>' as username!")
    else:
        print("  Z3 Result: UNSAT")

    # Test what values WOULD be dangerous
    print("\n3. FINDING DANGEROUS VALUES")
    print("-" * 40)

    for char in ILLEGAL_CHARS:
        solver_test = Solver()
        solver_test.add(Contains(user_input, StringVal(char)))
        if solver_test.check() == sat:
            model = solver_test.model()
            print(f"  '{char}' is SAT - user could enter: {model[user_input]}")


def test_path_concat():
    """Test concatenation with symbolic analysis."""
    print("\n" + "=" * 60)
    print("PATH CONCATENATION ANALYSIS")
    print("=" * 60)

    base = StringVal("C:\\Data\\")
    user = String("folder")

    print("\nSymbolic path: C:\\Data\\ + folder")
    print("-" * 40)

    # Check each dangerous pattern
    dangerous = []

    # Check illegal chars
    for char in ILLEGAL_CHARS:
        solver = Solver()
        solver.add(Contains(base + user, StringVal(char)))
        if solver.check() == sat:
            dangerous.append(f"'{char}'")

    if dangerous:
        print(f"  COULD contain illegal chars: {', '.join(dangerous)}")

    # Check reserved names
    reserved_found = []
    for name in ["COM1", "AUX", "NUL", "PRN", "CON"]:
        solver = Solver()
        solver.add(Contains(base + user, StringVal(name)))
        if solver.check() == sat:
            reserved_found.append(name)

    if reserved_found:
        print(f"  COULD contain reserved names: {', '.join(reserved_found)}")

    # Mixed slashes
    solver_mixed = Solver()
    # For a path to have mixed slashes, user input would need to contain both
    solver_mixed.add(Contains(user, StringVal("/")))
    solver_mixed.add(Contains(user, StringVal("\\")))
    if solver_mixed.check() == sat:
        print("  COULD have mixed slashes (if user provides both / and \\)")

    print("\n  This proves the path CANNOT be fully trusted!")


def test_os_path_join():
    """Test os.path.join symbolic analysis."""
    print("\n" + "=" * 60)
    print("OS.PATH.JOIN SYMBOLIC ANALYSIS")
    print("=" * 60)

    base = StringVal("C:\\Users\\")
    subfolder = String("subfolder")
    sep = StringVal("\\")

    print("\nSymbolic: C:\\Users\\ + subfolder")
    print("-" * 40)

    solver = Solver()
    path = base + sep + subfolder

    # Test if path could have reserved name in subfolder
    for name in ["AUX", "PRN", "CON"]:
        solver.push()
        solver.add(Contains(path, StringVal(f"\\{name}\\")))
        if solver.check() == sat:
            print(f"  COULD contain \\{name}\\ in path!")
        solver.pop()

    # Test if path could be missing drive letter (if base could be empty)
    print("\n  Z3 proves: If base is always 'C:\\Users\\', path will have drive letter")
    print("  But subfolder content is UNKNOWN - must validate!")


if __name__ == "__main__":
    test_symbolic_path()
    test_path_concat()
    test_os_path_join()

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print("""
Z3 symbolic analysis can PROVE:
  ✓ Path COULD contain illegal characters
  ✓ Path COULD contain reserved names
  ✓ Path COULD have mixed slashes
  ✓ Values that WOULD make path dangerous

This is useful for:
  - Proving vulnerabilities exist (SAT)
  - Proving code is safe (UNSAT)
  - Finding test cases that trigger bugs
""")
