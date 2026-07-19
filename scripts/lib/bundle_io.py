"""Content-addressed shared-input store for calibration bundles.

The deterministic input/benchmark parquets a bundle carries — ``campd``,
``eia930`` and ``eia923`` — depend only on the ISO / year / benchmark config,
not on the LP solve, so they are byte-identical across most runs of an ISO.
Writing a copy into every bundle duplicated ~6 MB/bundle (gigabytes across the
run archive, and the bulk of the working-tree checkout that fills the disk on a
fresh clone). Instead they are written **once** to a content-addressed shared
store next to the bundles::

    <bundles_root>/_shared/<ISO>/<name>-<sha8>.parquet

and each bundle's ``meta.json`` records the reference under ``shared_inputs``
(a bundle-relative path, e.g. ``../_shared/CAISO/campd-1a2b3c4d5e6f.parquet``).
Identical content collapses to one file; a genuinely different variant (e.g. an
``eia923`` built with a different backfill flag) hashes differently and is kept
separately. Run-specific outputs (``dispatch/``, ``system``, ``storage``) stay
in the bundle.

The store is content-addressed so it needs no cache invalidation: the same data
always maps to the same path, and a never-before-seen variant simply adds a new
file. ``write_shared_input`` returns the reference to record; ``bundle_input_path``
resolves it back (falling back to a legacy in-bundle file when a bundle predates
the store, so existing tooling keeps working).
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pandas is imported lazily so stdlib-only tools can import
    import pandas as pd  # this module (calibration_verdict, audit_keepers, deploy).

# Repo root (scripts/lib/bundle_io.py -> parents[2]) and the bundle / registry
# roots derived from it, so the path-resolution helpers below stay stdlib-only
# (no ``market_sim`` / pandas import) and are usable by the no-numpy governance
# scorers and the bare-python deploy toolchain.
REPO_ROOT: Path = Path(__file__).resolve().parents[2]
BUNDLES_ROOT: Path = REPO_ROOT / "results" / "calibration"
REGISTRY_DIR: Path = REPO_ROOT / "frontend" / "data" / "backcast" / "registry"

# The deterministic input/benchmark frames eligible for the shared store. The
# solve outputs (dispatch/system/storage/btm) are per-run and never shared.
SHARED_INPUT_NAMES: tuple[str, ...] = ("campd", "eia930", "eia923")


def bundles_root() -> Path:
    """Return the calibration bundles root (``results/calibration`` under repo)."""
    return BUNDLES_ROOT


def resolve_bundle(name_or_path: str | Path) -> Path:
    """Resolve a bundle spec to its on-disk run directory.

    Accepts any of the spellings the standing tools take on the command line:

    * an existing path (absolute or relative) to a bundle dir — returned as-is;
    * a registry run id (``<id>`` with a ``registry/<id>.json`` sidecar) — the
      sidecar's ``bundle`` field, resolved under the repo root;
    * a bare bundle name — resolved under :func:`bundles_root`.

    The returned path is not required to exist (callers decide), except the
    registry-sidecar branch, which reads the sidecar to find the bundle.

    Raises:
        FileNotFoundError: if ``name_or_path`` is neither an existing path, a
            known run id, nor a name under the bundles root.
    """
    p = Path(name_or_path)
    # An explicit path (has a separator, or already exists) is taken literally.
    if p.exists():
        return p
    text = str(name_or_path)
    if os.sep in text or (os.altsep and os.altsep in text):
        return p
    sidecar = REGISTRY_DIR / f"{text}.json"
    if sidecar.exists():
        bundle = json.loads(sidecar.read_text()).get("bundle")
        if bundle:
            return REPO_ROOT / bundle
    candidate = BUNDLES_ROOT / text
    if candidate.exists():
        return candidate
    raise FileNotFoundError(
        f"cannot resolve bundle {name_or_path!r}: not an existing path, a "
        f"registry run id ({sidecar}), or a name under {BUNDLES_ROOT}"
    )


def bundle_meta(run_dir: Path) -> dict:
    """Return a bundle's parsed ``meta.json``, or an empty dict if absent."""
    meta_path = Path(run_dir) / "meta.json"
    if not meta_path.exists():
        return {}
    return json.loads(meta_path.read_text())


def dispatch_path(run_dir: Path, year: int, pass_label: str = "P1") -> Path:
    """Return the dispatch parquet path for ``year``/``pass_label`` in a bundle.

    The bundle stores one dispatch parquet per solved year and pass under
    ``dispatch/<year>_<pass_label>.parquet`` (e.g. ``dispatch/2024_P1.parquet``).
    """
    return Path(run_dir) / "dispatch" / f"{year}_{pass_label}.parquet"


def content_hash(df: pd.DataFrame) -> str:
    """Return a stable 12-hex content hash of ``df`` (column-order sensitive).

    Hashes the row content via :func:`pandas.util.hash_pandas_object` plus the
    column names, so it is independent of parquet encoding/metadata (two writes
    of the same data map to the same hash and dedupe). It is stable within a
    pandas version; a version bump may shift the hash, which only adds a new
    (still-correct) store entry.
    """
    import pandas as pd

    h = hashlib.sha256()
    h.update("\x00".join(map(str, df.columns)).encode("utf-8"))
    h.update(pd.util.hash_pandas_object(df, index=True).values.tobytes())
    return h.hexdigest()[:12]


def write_shared_input(df: pd.DataFrame, name: str, iso: str, run_dir: Path) -> str:
    """Write ``df`` to the content-addressed shared store; return its reference.

    The reference is the store path **relative to** ``run_dir`` (so the bundle
    stays portable as long as it and the ``_shared`` sibling move together), to
    be stored in the bundle's ``meta.json`` ``shared_inputs[name]``. A file with
    the same content hash is written only once.
    """
    run_dir = Path(run_dir)
    shared = run_dir.parent / "_shared" / iso
    shared.mkdir(parents=True, exist_ok=True)
    target = shared / f"{name}-{content_hash(df)}.parquet"
    if not target.exists():
        df.to_parquet(target, index=False)
    return os.path.relpath(target, run_dir)


def bundle_input_path(run_dir: Path, name: str) -> Path | None:
    """Resolve a bundle's input parquet ``name`` to an existing file, or ``None``.

    Prefers the shared-store reference in ``meta.json`` (new bundles); falls back
    to a legacy in-bundle ``<name>.parquet`` so tooling still reads older bundles.
    Returns ``None`` when neither exists.
    """
    run_dir = Path(run_dir)
    meta_path = run_dir / "meta.json"
    if meta_path.exists():
        try:
            ref = json.loads(meta_path.read_text()).get("shared_inputs", {}).get(name)
        except (json.JSONDecodeError, OSError):
            ref = None
        if ref:
            shared = (run_dir / ref).resolve()
            if shared.exists():
                return shared
    legacy = run_dir / f"{name}.parquet"
    return legacy if legacy.exists() else None


def read_bundle_input(run_dir: Path, name: str) -> pd.DataFrame | None:
    """Read a bundle input parquet via :func:`bundle_input_path`, or ``None``."""
    import pandas as pd

    path = bundle_input_path(run_dir, name)
    return pd.read_parquet(path) if path is not None else None
