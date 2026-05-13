# aicheck

**Catch AI-generated code issues before they catch you.**

`aicheck` is a static analysis toolkit that detects common failure patterns in AI-generated Python code:

- **Hallucinated imports** — modules LLMs frequently invent (e.g. `utils`, `helpers`, `misc`)
- **Dead code** — unused variables, unreachable branches, code after `return`/`raise`
- **Suspicious API usage** — wrong method names for stdlib modules, `open().read()` patterns
- **Confidence scoring** — each file gets a 0–100 score based on findings severity

## Installation

```bash
pip install aicheck
```

## Quick Start

```bash
# Check a single file
aicheck check my_file.py

# Check an entire project
aicheck check src/

# JSON output for CI integration
aicheck check src/ --format json
```

## Sample Output

```
[FAIL] src/suspicious.py  (score: 62.0)
    high  L1:0  [hallucinated_import] Potentially hallucinated module: 'utils'
           ↳ Verify 'utils' exists; check PyPI or project dependencies
  medium  L14:4  [unreachable_code] Unreachable branch: condition is always False
     low  L11:4  [dead_code] Possibly unused variable: 'unused_var'

Files: 1  Passed: 0  Failed: 1
Average confidence score: 62.0/100
```

## CLI Reference

| Command | Description |
|---|---|
| `aicheck check <path>` | Analyze a file or directory |
| `aicheck check <path> --format json` | Output as JSON |
| `aicheck version` | Show version |

## Score Interpretation

| Score | Meaning |
|---|---|
| 100–90 | Clean |
| 89–70 | Minor issues |
| 69–50 | Moderate issues — review recommended |
| <50 | Critical — do not commit without review |

## Development

```bash
git clone https://github.com/maheshmakvana/ai-check.git
cd ai-check
python -m venv venv && source venv/bin/activate
pip install -e ".[test]"
pytest tests/ -v
ruff check src/
mypy src/
```

## License

MIT