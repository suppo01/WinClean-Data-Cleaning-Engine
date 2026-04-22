"""
Z3 Symbolic Path Analyzer

Uses Z3 SMT Solver to symbolically execute path building operations
and determine if paths COULD be dangerous.
"""

import ast
import re
from typing import Any, Optional


ILLEGAL_CHARS = set('<>:"|?*')
RESERVED_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *{f"COM{i}" for i in range(1, 10)},
    *{f"LPT{i}" for i in range(1, 10)},
}


class Z3SymbolicAnalyzer:
    """
    Uses Z3 to symbolically execute path building and detect potential issues.
    """

    def __init__(self):
        self.errors = []
        self.user_input_vars = {}  # var_name -> Z3 String
        self.solver = None

    def analyze(self, code: str) -> list[str]:
        """Analyze code using Z3 symbolic execution."""
        try:
            tree = ast.parse(code)
            self.visit(tree)
        except SyntaxError:
            pass
        return self.errors

    def visit(self, node: ast.AST) -> None:
        """Visit AST nodes."""
        if isinstance(node, ast.Module):
            for child in node.body:
                self.visit(child)
        elif isinstance(node, ast.FunctionDef):
            self._visit_function(node)
        elif isinstance(node, ast.Assign):
            self._visit_assign(node)
        elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            self._visit_call(node.value)
        elif isinstance(node, ast.Call):
            self._visit_call(node)

    def _visit_function(self, node: ast.FunctionDef) -> None:
        """Visit function definition."""
        for child in node.body:
            self.visit(child)

    def _visit_assign(self, node: ast.Assign) -> None:
        """Visit assignment statement."""
        for target in node.targets:
            if isinstance(target, ast.Name):
                var_name = target.id
                value = self._expr_to_symbolic(node.value, var_name)
                if value is not None:
                    self.user_input_vars[var_name] = value

    def _visit_call(self, node: ast.Call) -> None:
        """Visit function call."""
        func_name = self._get_func_name(node.func)

        # Track input() calls
        if func_name == "input":
            var = self._get_assign_target(node)
            if var:
                self.user_input_vars[var] = self._create_symbolic_input(var)
                self.errors.append(
                    f"Line {node.lineno}: Variable '{var}' receives user input (symbolic)"
                )

        # Track sys.argv usage
        if func_name == "__getitem__" and self._is_sys_argv(node):
            self.errors.append(
                f"Line {node.lineno}: sys.argv[...] used - untrusted input (symbolic)"
            )

        # Check path operations
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
                result = self._expr_to_symbolic(arg, None)
                if result:
                    self._check_symbolic_path(result, node.lineno)

    def _expr_to_symbolic(
        self, node: ast.AST, var_name: Optional[str]
    ) -> Optional[Any]:
        """Convert AST expression to Z3 symbolic expression."""
        from z3 import String, StringVal, Concat

        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return StringVal(node.value)

        if isinstance(node, ast.Name):
            name = node.id
            if name in self.user_input_vars:
                return self.user_input_vars[name]
            # Unknown variable - create symbolic
            return String(name)

        if isinstance(node, ast.JoinedStr):
            return self._visit_joined_str(node)

        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            left = self._expr_to_symbolic(node.left, None)
            right = self._expr_to_symbolic(node.right, None)
            if left and right:
                return Concat(left, right)

        if isinstance(node, ast.Call):
            func_name = self._get_func_name(node.func)
            if func_name == "str":
                if node.args:
                    return self._expr_to_symbolic(node.args[0], None)
            if func_name in ("join", "path.join"):
                return self._visit_path_join(node)

        return None

    def _visit_joined_str(self, node: ast.JoinedStr) -> Optional[Any]:
        """Visit f-string."""
        from z3 import String, StringVal, Concat

        parts = []
        for value in node.values:
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                parts.append(StringVal(value.value))
            elif isinstance(value, ast.FormattedValue):
                expr = self._expr_to_symbolic(value.value, None)
                if expr:
                    parts.append(expr)
        if parts:
            return Concat(*parts)
        return None

    def _visit_path_join(self, node: ast.Call) -> Optional[Any]:
        """Visit os.path.join call."""
        from z3 import String, StringVal, Concat

        args = node.args
        if not args:
            return None

        result = None
        for arg in args:
            part = self._expr_to_symbolic(arg, None)
            if part:
                if result is None:
                    result = part
                else:
                    result = Concat(result, StringVal("/"), part)
        return result

    def _get_func_name(self, node: ast.AST) -> str:
        """Get function name from AST."""
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            if isinstance(node.value, ast.Name):
                return f"{node.value.id}.{node.attr}"
            return node.attr
        return ""

    def _get_assign_target(self, call_node: ast.Call) -> Optional[str]:
        """Get variable being assigned from input() call."""
        return None  # Simplified - would need parent tracking

    def _is_sys_argv(self, node: ast.Call) -> bool:
        """Check if this is sys.argv[...]."""
        if isinstance(node.func, ast.Attribute) and node.func.attr == "__getitem__":
            if isinstance(node.func.value, ast.Attribute):
                if (
                    isinstance(node.func.value.value, ast.Name)
                    and node.func.value.value.id == "sys"
                    and node.func.value.attr == "argv"
                ):
                    return True
        return False

    def _create_symbolic_input(self, var_name: str) -> Any:
        """Create a Z3 symbolic string representing user input."""
        from z3 import String

        return String(var_name)

    def _check_symbolic_path(self, path_expr, lineno: int) -> None:
        """Check if symbolic path COULD be dangerous using Z3."""
        from z3 import Solver, String, Contains, StringVal, Or, sat, unsat

        solver = Solver()

        # Check for illegal characters
        for char in ILLEGAL_CHARS:
            solver.push()
            solver.add(Contains(path_expr, StringVal(char)))
            if solver.check() == sat:
                self.errors.append(
                    f"Line {lineno}: Path MAY contain illegal character '{char}' "
                    f"(symbolic analysis)"
                )
            solver.pop()

        # Check for reserved names
        for reserved in RESERVED_NAMES:
            solver.push()
            solver.add(
                Or(
                    Contains(path_expr, StringVal(f"/{reserved}")),
                    Contains(path_expr, StringVal(f"\\{reserved}")),
                    Contains(path_expr, StringVal(f":\\{reserved}")),
                )
            )
            if solver.check() == sat:
                self.errors.append(
                    f"Line {lineno}: Path MAY contain reserved name '{reserved}' "
                    f"(symbolic analysis)"
                )
            solver.pop()


def check_with_z3(code: str) -> list[str]:
    """Check code using Z3 symbolic analysis."""
    try:
        analyzer = Z3SymbolicAnalyzer()
        return analyzer.analyze(code)
    except ImportError:
        return ["Z3 not available - install with: pip install z3-solver"]


# Export for use
__all__ = ["check_with_z3", "Z3SymbolicAnalyzer"]
