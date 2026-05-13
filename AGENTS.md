# aicheck — dev workflow notes

## Test
```bash
pytest tests/ -v
pytest tests/ -v --tb=short
```

## Lint
```bash
ruff check src/
ruff check src/ --fix
```

## Type check
```bash
mypy src/
```

## Build
```bash
python -m build
```

## Release (dry run)
```bash
twine check dist/*
```