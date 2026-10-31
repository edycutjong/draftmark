# Contributing

```bash
npm install && pip install -r requirements.txt -r requirements-dev.txt ruff
python3 -m pytest -q
ruff check . && npm run typecheck && npm run build
```

Keep pull requests small, add a test for behaviour changes, and never commit keys (`.env*` is ignored). Numbers in the README must trace to a record in `evidence/`.
