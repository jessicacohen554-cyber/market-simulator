"""Root conftest: put the repo root and ``src/`` on ``sys.path``.

Makes the ``scripts.*``-importing test files (and ``market_sim.*`` imports)
resolve no matter how pytest is invoked — from the repo root, a subdir, or an
editor runner — without relying on the editable install being present.
"""

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
for _p in (_ROOT, _ROOT / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))
