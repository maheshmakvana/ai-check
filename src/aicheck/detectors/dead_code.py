import ast

from aicheck.models import Finding, FindingKind, Severity


class DeadCodeDetector:
    def check(self, tree: ast.AST, source: str) -> list[Finding]:
        findings: list[Finding] = []
        self._check_unreachable(tree, findings)
        self._check_unused_vars(tree, findings)
        self._check_dead_after_return(tree, findings)
        return findings

    @staticmethod
    def _check_unreachable(tree: ast.AST, findings: list[Finding]) -> None:
        for node in ast.walk(tree):
            if isinstance(node, ast.If):
                if isinstance(node.test, ast.Constant) and node.test.value is False:
                    findings.append(Finding(
                        kind=FindingKind.UNREACHABLE_CODE,
                        message="Unreachable branch: condition is always False",
                        line=node.lineno or 0,
                        column=node.col_offset or 0,
                        severity=Severity.MEDIUM,
                        suggestion="Remove dead branch or update condition",
                    ))

    @staticmethod
    def _check_unused_vars(tree: ast.AST, findings: list[Finding]) -> None:
        assigns: dict[str, ast.Name] = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for t in node.targets:
                    if isinstance(t, ast.Name) and not t.id.startswith("_"):
                        assigns[t.id] = t
        for var, node in assigns.items():
            count = sum(1 for n in ast.walk(tree)
                        if isinstance(n, ast.Name) and n.id == var)
            if count <= 1:
                findings.append(Finding(
                    kind=FindingKind.DEAD_CODE,
                    message=f"Possibly unused variable: '{var}' (assigned but never read)",
                    line=node.lineno or 0,
                    column=node.col_offset or 0,
                    severity=Severity.LOW,
                    suggestion=f"Remove '{var}' or use it elsewhere",
                ))

    @staticmethod
    def _check_dead_after_return(tree: ast.AST, findings: list[Finding]) -> None:
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                stmts = node.body
                for i, stmt in enumerate(stmts[:-1]):
                    if isinstance(stmt, (ast.Return, ast.Raise)):
                        next_stmt = stmts[i + 1]
                        findings.append(Finding(
                            kind=FindingKind.DEAD_CODE,
                            message=f"Dead code after {type(stmt).__name__.lower()} "
                                    f"on line {next_stmt.lineno}",
                            line=next_stmt.lineno or 0,
                            column=next_stmt.col_offset or 0,
                            severity=Severity.MEDIUM,
                            suggestion="Remove unreachable statement or reorder logic",
                        ))
