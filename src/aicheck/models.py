from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class Severity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FindingKind(Enum):
    HALLUCINATED_IMPORT = "hallucinated_import"
    DEAD_CODE = "dead_code"
    SUSPICIOUS_API = "suspicious_api"
    UNREACHABLE_CODE = "unreachable_code"
    FAKE_STDLIB = "fake_stdlib"


@dataclass
class Finding:
    kind: FindingKind
    message: str
    line: int
    column: int
    severity: Severity
    suggestion: str = ""


@dataclass
class FileResult:
    path: Path
    findings: list[Finding] = field(default_factory=list)

    @property
    def score(self) -> float:
        if not self.findings:
            return 100.0
        penalties = {
            Severity.LOW: 2,
            Severity.MEDIUM: 5,
            Severity.HIGH: 15,
            Severity.CRITICAL: 30,
        }
        total_penalty = sum(penalties[f.severity] for f in self.findings)
        return max(0.0, 100.0 - total_penalty)

    @property
    def passed(self) -> bool:
        return self.score >= 70.0
