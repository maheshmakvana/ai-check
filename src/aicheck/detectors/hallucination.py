import ast

from aicheck.models import Finding, FindingKind, Severity


class HallucinationDetector:
    FAKE_STDLIB_MODULES: set[str] = {
        "utils", "helpers", "common", "tools", "misc",
        "extras", "general", "core", "base", "utilities",
        "datatools", "fileutils", "strutils", "validators",
    }

    def check(self, tree: ast.AST, source: str) -> list[Finding]:
        findings: list[Finding] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top = alias.name.split(".")[0]
                    if top in self.FAKE_STDLIB_MODULES:
                        findings.append(Finding(
                            kind=FindingKind.HALLUCINATED_IMPORT,
                            message=f"Potentially hallucinated module: '{alias.name}' — "
                                    f"'{top}' is a common LLM-invented name",
                            line=node.lineno or 0,
                            column=node.col_offset or 0,
                            severity=Severity.HIGH,
                            suggestion=(
                                f"Verify '{alias.name}' exists; "
                                "check PyPI or project dependencies"
                            ),
                        ))
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    top = node.module.split(".")[0]
                    if top in self.FAKE_STDLIB_MODULES and node.level is None:
                        findings.append(Finding(
                            kind=FindingKind.FAKE_STDLIB,
                            message=f"Import from potentially fake module: '{node.module}'",
                            line=node.lineno or 0,
                            column=node.col_offset or 0,
                            severity=Severity.HIGH,
                            suggestion=f"Ensure '{node.module}' is a real package",
                        ))
        return findings
