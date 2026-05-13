"""Valid Python — should pass with high score."""

import os
import sys
import json
from pathlib import Path
from typing import Optional


def greet(name: str) -> str:
    return f"Hello, {name}!"


def load_config(path: Path) -> Optional[dict]:
    if path.exists():
        with path.open() as f:
            return json.load(f)
    return None


def main() -> None:
    cfg = load_config(Path("config.json"))
    if cfg:
        print(greet(cfg.get("name", "world")))


if __name__ == "__main__":
    main()