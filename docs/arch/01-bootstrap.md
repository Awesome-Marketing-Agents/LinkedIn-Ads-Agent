# Module: Bootstrap (Path Helper)

## Overview

`bootstrap.py` is a small utility that ensures the `src/` directory is on Python's import path. This lets `main.py` and `cli.py` import `linkedin_action_center` without installing the package or manually adjusting `sys.path`.

---

## File Path

`bootstrap.py`

---

## Components & Explanation

- **Module-level code**
  - **Purpose**: Add `src/` to `sys.path` so `linkedin_action_center` can be imported.
  - **Inputs**: None (uses `__file__` to find the project root).
  - **Outputs**: Side effect on `sys.path`.
  - **Dependencies**: `os`, `sys`.

---

## Relationships

- Imported by `main.py` and `cli.py` before any `linkedin_action_center` imports.
- No other modules depend on it.

---

## Example Code Snippets

```python
# In main.py or cli.py (first line)
import bootstrap  # noqa: F401  — adds src/ to sys.path

from linkedin_action_center.auth.manager import AuthManager
```

```python
# Equivalent manual setup (if bootstrap were not used)
import os
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.join(current_dir, 'src')
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
```

---

## Edge Cases & Tips

- **Import order**: `bootstrap` must be imported before any `linkedin_action_center` imports.
- **`noqa: F401`**: Used because `bootstrap` is imported only for its side effect; linters may flag it as unused.
- **Alternative**: Running `uv run python main.py` from the project root uses `pyproject.toml` and `uv`'s environment, which also makes the package importable; `bootstrap` is a fallback for direct execution.

---

## Architecture / Flow

```
main.py / cli.py
    |
    └── import bootstrap
            └── sys.path.insert(0, project_root/src)
                    └── linkedin_action_center importable
```

---

## Advanced Notes

- `BASE_DIR` in `core/config.py` is computed from `__file__` in `config.py`, not from `bootstrap`.
- With `uv run`, the project is typically run in editable mode, so `bootstrap` may be redundant in some setups.
