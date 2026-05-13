import json

from aicheck.models import FileResult


class ConsoleReporter:
    def report(self, results: list[FileResult]) -> str:
        lines: list[str] = []
        passed = 0
        failed = 0
        for r in results:
            status = "PASS" if r.passed else "FAIL"
            if r.passed:
                passed += 1
            else:
                failed += 1
            lines.append(f"[{status}] {r.path}  (score: {r.score:.1f})")
            for f in r.findings:
                lines.append(
                    f"  {f.severity.value:>8}  L{f.line}:{f.column}  "
                    f"[{f.kind.value}] {f.message}"
                )
                if f.suggestion:
                    lines.append(f"           \u21b3 {f.suggestion}")
        if not results:
            lines.append("No Python files found.")
        lines.append("")
        total = len(results)
        lines.append(f"Files: {total}  Passed: {passed}  Failed: {failed}")
        if total:
            avg = sum(r.score for r in results) / total
            lines.append(f"Average confidence score: {avg:.1f}/100")
        return "\n".join(lines)


class JsonReporter:
    def report(self, results: list[FileResult]) -> str:
        data = []
        for r in results:
            data.append({
                "path": str(r.path),
                "score": r.score,
                "passed": r.passed,
                "findings": [
                    {
                        "kind": f.kind.value,
                        "severity": f.severity.value,
                        "line": f.line,
                        "column": f.column,
                        "message": f.message,
                        "suggestion": f.suggestion,
                    }
                    for f in r.findings
                ],
            })
        return json.dumps({"files": data}, indent=2)


def get_reporter(format: str) -> ConsoleReporter | JsonReporter:
    reporters: dict[str, type[ConsoleReporter] | type[JsonReporter]] = {
        "console": ConsoleReporter,
        "json": JsonReporter,
    }
    cls = reporters.get(format, ConsoleReporter)
    return cls()
