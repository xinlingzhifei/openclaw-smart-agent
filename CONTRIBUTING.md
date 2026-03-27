# Contributing

## Workflow

- Use Python 3.11+ and Node 22+.
- Prefer test-first changes for runtime behavior.
- Keep plugin changes thin and push business logic into the Python runtime.
- Preserve the current OpenClaw contract: workspace skill in `skills/`, plugin manifest in `plugin/openclaw.plugin.json`, runtime API in `src/openclaw_smart_agent/api.py`.

## Local setup

```bash
python -m pip install -e ".[dev]"
npm --prefix plugin install --no-audit --no-fund
```

## Verification

```bash
python -m pytest tests -q
npm --prefix plugin run check
python /path/to/quick_validate.py /path/to/repo/skills/openclaw-smart-agent
```

## Pull requests

- Keep each PR focused on one capability area.
- Add or update tests for runtime behavior changes.
- Update `README.md` whenever install or operator steps change.
- Follow PEP 8 for Python and the repository TypeScript settings for the plugin.

## Issues and proposals

- Use issues for bugs, routing improvements, identity template additions, and OpenClaw compatibility updates.
- If you change public payloads or routing behavior, include before and after examples in the issue or PR description.
