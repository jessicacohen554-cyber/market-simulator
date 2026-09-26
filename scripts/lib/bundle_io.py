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

# Derived (not raw, not benchmark) solve inputs a bundle additionally pins via
# the shared store: the per-ISO CAMPD unit-outage extracts and the clean
# capacity-deliverability partition. These are the inputs whose bytes are NOT
# recoverable from the committed tree at an arbitrary later date (the extract
# family is re-derived and has changed content at fixed raw bytes — the
# caiso-123 basis-drift attribution; the clean partition is gitignored and
# regenerated per container, and silently degrades to "no limits" when absent —
# RESULTS-neiso65 §2), so a bundle records the exact frames it solved on
# (FINDING-caiso124 §7 recommendation).
DERIVED_INPUT_NAMES: tuple[str, ...] = (
    "unit_outages",
    "unit_outages_short",
    "unit_outages_partial",
    "unit_outages_maxgen",
    "unit_outages_e923",
    "unit_outages_layup",
    "capacity_deliverability",
    "hydro_plant_modes",
)


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


def write_derived_solve_inputs(iso: str, run_dir: Path) -> dict[str, str]:
    """Pin the ISO's derived solve inputs into the shared store; return the refs.

    Captures, at bundle-write time, the content of every derived-not-committed
    (or derived-then-mutable) input the solve read, so a later session can
    byte-compare or recover the exact state a bundle solved on:

    * the per-ISO CAMPD unit-outage extract family (main / short / partial /
      maxgen via the :mod:`market_sim.data.outages` path resolvers — which any
      probe-level pinning monkeypatch is honored through — plus the ``e923``
      and ``layup`` companions by name), and
    * the clean ``capacity-deliverability`` partition (via the same loader the
      solve uses, so the ISO alias and a silently-absent partition read
      identically to the solve's own view — an absent partition records
      nothing, exactly the state the solve degraded to).

    Files that do not exist for the ISO are skipped. Returns
    ``{name: bundle-relative ref}`` for the captured inputs, to be merged into
    the bundle's ``meta.json`` ``shared_inputs`` block (replay ignores the
    whole block by design). Never raises past a single input: one unreadable
    file is logged-and-skipped so provenance capture cannot fail a solve.
    """
    import logging

    import pandas as pd

    logger = logging.getLogger(__name__)
    out: dict[str, str] = {}

    from market_sim.data import outages

    csv_paths: dict[str, Path] = {
        "unit_outages": outages.unit_outage_csv_for_iso(iso),
        "unit_outages_short": outages.unit_outage_short_csv_for_iso(iso),
        "unit_outages_partial": outages.unit_partial_outage_csv_for_iso(iso),
        "unit_outages_maxgen": outages.unit_outage_maxgen_csv_for_iso(iso),
    }
    main_csv = csv_paths["unit_outages"]
    for tag in ("e923", "layup"):
        suffix = "" if (iso or "").upper() == "ERCOT" else f"-{iso.upper()}"
        csv_paths[f"unit_outages_{tag}"] = main_csv.with_name(
            f"campd-unit-outages-{tag}{suffix}.csv"
        )
    if (iso or "").upper() != "ERCOT":
        # SPP-85: the '-netloadmask-' companions (selected under
        # ScenarioConfig.unit_outage_netload_mask_repair), captured by name like
        # e923/layup so an armed bundle pins what it actually read.
        u = iso.upper()
        csv_paths["unit_outages_netloadmask"] = main_csv.with_name(
            f"campd-unit-outages-netloadmask-{u}.csv"
        )
        csv_paths["unit_outages_short_netloadmask"] = main_csv.with_name(
            f"campd-unit-outages-short-netloadmask-{u}.csv"
        )
        csv_paths["unit_outages_partial_netloadmask"] = main_csv.with_name(
            f"campd-partial-outages-netloadmask-{u}.csv"
        )
    for name, path in csv_paths.items():
        if not path.is_file():
            continue
        try:
            out[name] = write_shared_input(pd.read_csv(path), name, iso, run_dir)
        except Exception:
            logger.warning(
                "derived-input capture failed for %s (%s)", name, path, exc_info=True
            )

    try:
        from market_sim.data.capacity_deliverability import _read as _read_capdel

        frame = _read_capdel(iso)
        if frame is not None:
            out["capacity_deliverability"] = write_shared_input(
                frame, "capacity_deliverability", iso, run_dir
            )
    except Exception:
        logger.warning(
            "derived-input capture failed for capacity_deliverability (%s)",
            iso,
            exc_info=True,
        )

    # The clean hydro-plant-modes partition (the caiso-126 RoR-split
    # classifier): derived from committed raw (EHA/HILARRI) by
    # scripts/data/curate_hydro_plant_modes.py, but the clean tree is
    # disposable — pin the exact classification bytes the solve read. Absent
    # partition (classifier not curated / not reviewed for the ISO) records
    # nothing, exactly the state the solve degraded to.
    try:
        from market_sim.data.hydro_modes import load_hydro_shapeable

        modes = load_hydro_shapeable(iso)
        if modes is not None:
            frame = pd.DataFrame(
                {
                    "plant_id": list(modes.keys()),
                    "shapeable": list(modes.values()),
                }
            ).sort_values("plant_id")
            out["hydro_plant_modes"] = write_shared_input(
                frame, "hydro_plant_modes", iso, run_dir
            )
    except Exception:
        logger.warning(
            "derived-input capture failed for hydro_plant_modes (%s)",
            iso,
            exc_info=True,
        )
    return out


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


class MissingBundleInput(FileNotFoundError):
    """A bundle's shared-store input is recorded in ``meta.json`` but absent.

    Carries the bundle, the input name and the reference ``meta.json`` records,
    so a caller (and a traceback) names the bundle and the remedy rather than
    surfacing the bare ``TypeError`` a ``None`` path raises inside pandas.
    """

    def __init__(self, run_dir: Path, name: str, ref: str | None) -> None:
        self.run_dir = Path(run_dir)
        self.name = name
        self.ref = ref
        if ref:
            where = f"recorded at meta.json shared_inputs[{name!r}] = {ref!r}, but {(self.run_dir / ref)} does not exist"
        else:
            where = (
                f"meta.json records no shared_inputs[{name!r}] and no legacy "
                f"{self.run_dir / f'{name}.parquet'} exists"
            )
        super().__init__(
            f"bundle {self.run_dir} is missing its {name!r} benchmark input: {where}.\n"
            "The shared store (results/calibration/_shared/<ISO>/) is a GITIGNORED "
            "SIBLING of the bundle dir, so a shard's `git add <its out-dir>` cannot "
            "carry it (CLAUDE.md rule 34 [R-SHARD-PROMOTABLE] (a)) and a bundle that "
            "arrives by fetch or fresh checkout has the reference without the bytes.\n"
            "These frames are pure functions of (ISO, year, reference data), so they "
            "regenerate at ZERO LP from the bundle's own meta recipe. Remedy:\n"
            f"    python3 scripts/run_calibration_full.py --restore-shared-inputs {self.run_dir}\n"
            "which rebuilds ONLY the missing entries and verifies each against the "
            "content hash meta.json already records (a mismatch is a hard error, "
            "never a silent benchmark swap)."
        )


def shared_input_ref(run_dir: Path, name: str) -> str | None:
    """Return the ``meta.json`` shared-store reference for ``name``, or ``None``.

    The reference is the bundle-relative store path recorded by
    :func:`write_shared_input` (e.g. ``../_shared/NWPP/eia923-84bb6ac40d29.parquet``);
    its ``-<hash>`` stem is the content hash of the frame the solve actually read,
    which is what makes a regenerated frame verifiable.
    """
    meta_path = Path(run_dir) / "meta.json"
    if not meta_path.exists():
        return None
    try:
        return json.loads(meta_path.read_text()).get("shared_inputs", {}).get(name)
    except (json.JSONDecodeError, OSError):
        return None


def missing_bundle_inputs(
    run_dir: Path, names: tuple[str, ...] = SHARED_INPUT_NAMES
) -> dict[str, str]:
    """Return ``{name: recorded ref}`` for each of ``names`` whose bytes are absent.

    A name is missing when :func:`bundle_input_path` cannot resolve it — i.e.
    neither the shared-store reference nor a legacy in-bundle copy exists. Names
    the bundle never recorded are skipped (they were not part of the solve), so
    an empty result means every input the bundle claims is readable.
    """
    run_dir = Path(run_dir)
    out: dict[str, str] = {}
    for name in names:
        ref = shared_input_ref(run_dir, name)
        if ref and bundle_input_path(run_dir, name) is None:
            out[name] = ref
    return out


def require_bundle_input(run_dir: Path, name: str) -> Path:
    """Resolve a bundle input parquet, raising :class:`MissingBundleInput` if absent.

    The strict counterpart of :func:`bundle_input_path`, for the call sites that
    cannot proceed without the frame (the registration payload builder, the
    calibration report, the session scorer). Use it instead of passing a possibly-
    ``None`` :func:`bundle_input_path` result straight to ``pandas.read_parquet``,
    which raises a ``TypeError`` naming neither the bundle nor the remedy.
    """
    path = bundle_input_path(run_dir, name)
    if path is None:
        raise MissingBundleInput(run_dir, name, shared_input_ref(run_dir, name))
    return path


def read_bundle_input(run_dir: Path, name: str) -> pd.DataFrame | None:
    """Read a bundle input parquet via :func:`bundle_input_path`, or ``None``."""
    import pandas as pd

    path = bundle_input_path(run_dir, name)
    return pd.read_parquet(path) if path is not None else None
