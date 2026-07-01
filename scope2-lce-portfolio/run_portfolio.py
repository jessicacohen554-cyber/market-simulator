#!/usr/bin/env python
"""Convenience entry point — run the CLI without installing the package.

Puts ``src/`` on the path and delegates to :func:`lce_portfolio.cli.main`, so the
tool runs straight from a clone::

    ../.venv/bin/python run_portfolio.py --load ... --lmp ... --iso ERCOT

Equivalent to ``pip install -e .`` then the ``lce-portfolio`` console script, or
``PYTHONPATH=src python -m lce_portfolio``.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from lce_portfolio.cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
