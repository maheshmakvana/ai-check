import ast
import importlib
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Protocol

import requests

from aicheck.detectors.api_usage import ApiUsageDetector
from aicheck.detectors.dead_code import DeadCodeDetector
from aicheck.detectors.hallucination import HallucinationDetector
from aicheck.models import FileResult, Finding


class DetectorProtocol(Protocol):
    def check(self, tree: ast.AST, source: str) -> list[Finding]:
        ...


class Analyzer:
    def __init__(self, timeout: int = 5):
        self.timeout = timeout
        self._detectors: list[DetectorProtocol] = [
            HallucinationDetector(),
            DeadCodeDetector(),
            ApiUsageDetector(),
        ]

    def check_file(self, path: Path) -> FileResult:
        with path.open(encoding="utf-8", errors="replace") as f:
            source = f.read()
        try:
            tree = ast.parse(source, filename=str(path))
        except SyntaxError:
            return FileResult(path=path)
        result = FileResult(path=path)
        for detector in self._detectors:
            result.findings.extend(detector.check(tree, source))
        return result

    def check_path(self, path: Path) -> list[FileResult]:
        if path.is_file() and path.suffix == ".py":
            return [self.check_file(path)]
        results: list[FileResult] = []
        files = list(path.rglob("*.py"))
        with ThreadPoolExecutor(max_workers=8) as pool:
            for r in pool.map(self.check_file, files):
                results.append(r)
        return results

    @staticmethod
    def known_modules() -> set[str]:
        known = set(sys.builtin_module_names)
        for m in list(sys.modules.keys()):
            parts = m.split(".")
            for i in range(len(parts)):
                known.add(".".join(parts[: i + 1]))
        known.update({
            "os", "sys", "re", "json", "math", "datetime", "pathlib",
            "collections", "functools", "itertools", "typing", "abc",
            "dataclasses", "enum", "hashlib", "random", "statistics",
            "uuid", "inspect", "textwrap", "string", "decimal", "fractions",
            "io", "base64", "binascii", "pickle", "shelve", "sqlite3",
            "csv", "configparser", "logging", "argparse", "subprocess",
            "shutil", "tempfile", "glob", "fnmatch", "linecache",
            "asyncio", "threading", "multiprocessing", "concurrent",
            "http", "urllib", "socket", "ssl", "email", "xml", "html",
            "unittest", "doctest", "pdb", "profile", "timeit",
            "warnings", "contextlib", "atexit", "weakref", "copy",
            "pprint", "reprlib", "enum", "numbers", "stat",
            "calendar", "locale", "gettext", "platform",
        })
        return known


def verify_import(name: str, timeout: int = 3) -> bool:
    top = name.split(".")[0]
    try:
        importlib.import_module(top)
        return True
    except ImportError:
        pass
    try:
        resp = requests.get(
            f"https://pypi.org/pypi/{top}/json",
            timeout=timeout,
        )
        return bool(resp.status_code == 200)
    except requests.RequestException:
        return False
