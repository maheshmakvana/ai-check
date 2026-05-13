import ast
import sys

from aicheck.models import Finding, FindingKind, Severity


class ApiUsageDetector:
    FAKE_FUNCTIONS: dict[str, set[str]] = {
        "os": {"path.join"},
        "sys": {"argv"},
        "re": {"search", "match", "findall", "sub", "split"},
        "json": {"dumps", "loads", "dump", "load"},
        "typing": {"List", "Dict", "Optional", "Tuple", "Union", "Any"},
    }

    REAL_STDLIB_FUNCTIONS: set[str] = set()

    def __init__(self) -> None:
        if not self.REAL_STDLIB_FUNCTIONS:
            self._build_stdlib_index()

    @staticmethod
    def _build_stdlib_index() -> None:
        known: set[str] = set()
        for mod_name in sys.stdlib_module_names:
            try:
                mod = __import__(mod_name)
                for attr in dir(mod):
                    known.add(f"{mod_name}.{attr}")
            except (ImportError, AttributeError):
                pass
        ApiUsageDetector.REAL_STDLIB_FUNCTIONS = known

    def check(self, tree: ast.AST, source: str) -> list[Finding]:
        findings: list[Finding] = []
        self._check_wrong_stdlib_methods(tree, findings)
        self._check_common_mistakes(tree, findings)
        return findings

    @staticmethod
    def _check_wrong_stdlib_methods(tree: ast.AST, findings: list[Finding]) -> None:
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if isinstance(node.func.value, ast.Name):
                    mod = node.func.value.id
                    func = f"{mod}.{node.func.attr}"
                    if mod in ("os", "sys", "json", "re", "typing"):
                        expected = ApiUsageDetector.FAKE_FUNCTIONS.get(mod, set())
                        if node.func.attr not in expected:
                            findings.append(Finding(
                                kind=FindingKind.SUSPICIOUS_API,
                                message=f"Suspicious API call: '{func}' — "
                                        f"uncommon for module '{mod}'",
                                line=node.lineno or 0,
                                column=node.col_offset or 0,
                                severity=Severity.MEDIUM,
                                suggestion=f"Verify '{func}' is a valid {mod} function",
                            ))

    @staticmethod
    def _check_common_mistakes(tree: ast.AST, findings: list[Finding]) -> None:
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if isinstance(node.func.value, ast.Name):
                    if node.func.value.id == "open" and node.func.attr == "read":
                        findings.append(Finding(
                            kind=FindingKind.SUSPICIOUS_API,
                            message=(
                                "Suspicious: 'open(...).read()' — "
                                "use 'pathlib.Path.read_text()' instead"
                            ),
                            line=node.lineno or 0,
                            column=node.col_offset or 0,
                            severity=Severity.LOW,
                            suggestion="Replace with Path.read_text()",
                        ))
