"""Assertions over curated ``data/clean`` outputs.

Curation tests all end the same way: resolve the clean partition path, run the
embedded-schema round-trip validation, and read the frame back. These two
helpers wrap that so a test asserts on the DataFrame directly.

They sit on top of ``scripts.lib.clean_io`` (the single write/read seam) and
respect whatever ``paths.CLEAN_DIR`` currently points at — so under
:class:`tests.helpers.base.CleanDirTestCase` they read the redirected tempdir.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from market_sim.config import paths
from scripts.lib import clean_io


def assert_clean_valid(
    datatype: str,
    iso: str | None = None,
    year: int | None = None,
    market: str | None = None,
) -> Path:
    """Assert a clean partition exists and passes schema round-trip validation.

    Resolves the canonical path via ``paths.clean_path`` and runs
    ``clean_io.validate_clean`` on it (the same read-back + re-validate the
    model's consumption seam does). Returns the validated path so a caller can
    chain further inspection.

    Raises ``AssertionError`` if the partition is missing; propagates
    ``clean_io``'s ``SchemaError`` if a present file no longer conforms.
    """
    path = paths.clean_path(datatype, iso=iso, year=year, market=market)
    assert path.is_file(), f"expected clean {datatype} partition at {path}"
    clean_io.validate_clean(path)
    return path


def read_clean_or_fail(
    datatype: str,
    iso: str | None = None,
    year: int | None = None,
    market: str | None = None,
    *,
    columns: list[str] | None = None,
) -> pd.DataFrame:
    """Read a clean partition, validating it, or fail the test with the path.

    Thin wrapper over ``clean_io.read_clean`` that converts the
    ``FileNotFoundError`` (partition absent) into an ``AssertionError`` naming
    the resolved path, which reads better in a test failure than the loader's
    regenerate hint. Schema violations still surface as ``SchemaError``.
    """
    try:
        return clean_io.read_clean(
            datatype, iso=iso, year=year, market=market, columns=columns
        )
    except FileNotFoundError as exc:
        path = paths.clean_path(datatype, iso=iso, year=year, market=market)
        raise AssertionError(f"no clean {datatype} partition at {path}") from exc
