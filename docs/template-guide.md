# Template Guide

The identity enhancer reads role templates from `src/openclaw_smart_agent/templates/`.

Each template file should be YAML and include:

```yaml
role: python-developer
keywords:
  - python
  - Python开发
skills:
  - python
  - testing
tools:
  - shell
system_prompt: You are a Python implementation specialist.
resource_weight: 0.8
```

## Required fields

- `role`: stable role identifier
- `keywords`: phrases matched against the incoming identity text
- `skills`: routing capabilities attached to the role
- `tools`: tools exposed to the generated profile
- `system_prompt`: prompt text carried with the profile
- `resource_weight`: scheduling weight used by the router

## Matching behavior

The enhancer performs a case-insensitive substring match across `keywords`. The first matching template wins.

## Adding a new template

1. Create a new `.yaml` file in `src/openclaw_smart_agent/templates/`
2. Add realistic `keywords`
3. Add skills that the router can use in `required_skills`
4. Run:

```bash
python -m pytest tests/test_identity.py -q
```

## Recommended conventions

- Keep `role` short and stable
- Keep `keywords` broad enough for user phrasing, but not so broad that unrelated roles collide
- Use `skills` names that you expect to reference in `smart_agent_publish_task`
- Keep `resource_weight` between `0.1` and `1.0`
