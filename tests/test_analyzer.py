import ast
import json
from pathlib import Path

import pytest

from aicheck.analyzer import Analyzer

SAMPLES = Path(__file__).parent / "samples"


@pytest.fixture
def analyzer() -> Analyzer:
    return Analyzer()


def test_check_good_code(analyzer: Analyzer) -> None:
    result = analyzer.check_file(SAMPLES / "good_code.py")
    assert result.score == 100.0
    assert len(result.findings) == 0
    assert result.passed


def test_check_suspicious_code(analyzer: Analyzer) -> None:
    result = analyzer.check_file(SAMPLES / "suspicious_code.py")
    assert len(result.findings) >= 3
    assert not result.passed
    assert result.score < 100.0


def test_check_directory(analyzer: Analyzer) -> None:
    results = analyzer.check_path(SAMPLES)
    assert len(results) == 2


def test_unreachable_code_detection(analyzer: Analyzer) -> None:
    source = """
if False:
    print("never")
"""
    tree = ast.parse(source)
    all_findings = []
    for d in analyzer._detectors:
        all_findings.extend(d.check(tree, source))
    unreachable = [f for f in all_findings if f.kind.name == "UNREACHABLE_CODE"]
    assert len(unreachable) >= 1


def test_unused_var_detection(analyzer: Analyzer) -> None:
    source = """
x = 42
y = 10
print(y)
"""
    tree = ast.parse(source)
    all_findings = []
    for d in analyzer._detectors:
        all_findings.extend(d.check(tree, source))
    unused = [f for f in all_findings
              if f.kind.name == "DEAD_CODE" and "unused" in f.message.lower()]
    assert len(unused) >= 1


def test_json_output_format(analyzer: Analyzer) -> None:
    from aicheck.reporters.console import JsonReporter
    results = analyzer.check_path(SAMPLES)
    reporter = JsonReporter()
    output = reporter.report(results)
    parsed = json.loads(output)
    assert "files" in parsed
    assert len(parsed["files"]) == 2


def test_pass_threshold(analyzer: Analyzer) -> None:
    result = analyzer.check_file(SAMPLES / "good_code.py")
    assert result.passed


def test_fail_threshold(analyzer: Analyzer) -> None:
    result = analyzer.check_file(SAMPLES / "suspicious_code.py")
    assert not result.passed


def test_dead_after_return(analyzer: Analyzer) -> None:
    source = """
def foo():
    return 1
    x = 2
"""
    tree = ast.parse(source)
    all_findings = []
    for d in analyzer._detectors:
        all_findings.extend(d.check(tree, source))
    dead_after = [f for f in all_findings
                  if f.kind.name == "DEAD_CODE" and "Dead code after" in f.message]
    assert len(dead_after) >= 1


def test_cli_check_file(capsys: pytest.CaptureFixture) -> None:
    from aicheck.cli import main
    rc = main(["check", str(SAMPLES / "good_code.py")])
    captured = capsys.readouterr()
    assert rc == 0
    assert "PASS" in captured.out


def test_cli_check_suspicious(capsys: pytest.CaptureFixture) -> None:
    from aicheck.cli import main
    rc = main(["check", str(SAMPLES / "suspicious_code.py")])
    captured = capsys.readouterr()
    assert rc == 1
    assert "FAIL" in captured.out


def test_cli_json_format(capsys: pytest.CaptureFixture) -> None:
    from aicheck.cli import main
    rc = main(["check", str(SAMPLES / "good_code.py"), "--format", "json"])
    captured = capsys.readouterr()
    assert rc == 0
    parsed = json.loads(captured.out)
    assert parsed["files"][0]["score"] == 100.0


def test_cli_version(capsys: pytest.CaptureFixture) -> None:
    from aicheck.cli import main
    rc = main(["version"])
    captured = capsys.readouterr()
    assert rc == 0
    assert "aicheck" in captured.out


def test_hallucinated_import_detection(analyzer: Analyzer) -> None:
    source = "import utils\nimport helpers\n"
    tree = ast.parse(source)
    all_findings = []
    for d in analyzer._detectors:
        all_findings.extend(d.check(tree, source))
    hallucinated = [f for f in all_findings
                    if f.kind.name in ("HALLUCINATED_IMPORT", "FAKE_STDLIB")]
    assert len(hallucinated) >= 2


def test_score_penalties() -> None:
    from aicheck.models import FileResult, Finding, FindingKind, Severity
    path = Path("dummy.py")
    r = FileResult(path=path)
    r.findings.append(Finding(
        kind=FindingKind.DEAD_CODE, message="", line=1, column=0,
        severity=Severity.CRITICAL,
    ))
    assert r.score == 70.0
    assert r.passed

    r.findings.append(Finding(
        kind=FindingKind.DEAD_CODE, message="", line=2, column=0,
        severity=Severity.CRITICAL,
    ))
    assert r.score == 40.0
    assert not r.passed