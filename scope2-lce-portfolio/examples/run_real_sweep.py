#!/usr/bin/env python
"""Real-data entry point: reference load x real per-ISO CF shapes x BAU LMP.

Run from inside ``scope2-lce-portfolio/``::

    ../.venv/bin/python examples/run_real_sweep.py --iso ERCOT
    ../.venv/bin/python examples/run_real_sweep.py --iso PJM --lmp path/to/bau_lmp.csv

Wires together the pieces the other waves built: the stylized 100 MW
reference load (``scripts/make_reference_load.py``), the real per-ISO CF
profiles built by ``scripts/build_profiles.py`` (pinned to the 2024
measured-shape vintage via ``PortfolioConfig.profile_shape_year`` — a missing
profile file is a hard error here, never a silent synthetic swap), and a BAU
LMP file.

**LMP resolution (see :func:`resolve_lmp_path`):** explicit ``--lmp`` wins;
otherwise the newest real (non-``_dummy``) ``bau_lmp_*.csv`` in
``data/inputs/`` is preferred; otherwise the newest existing ``*_dummy.csv``;
otherwise one is generated on the spot via the market-sim side's
``scripts/export_lce_lmp.py --dummy`` (subprocess — this tool never imports
``market_sim``). The market simulator's BAU **forecast** is on hold by
stakeholder decision (``PLAN.md`` Sec.10) — real LMPs never come from a
solve triggered here, only from a file that already exists. Any synthetic
result prints a loud banner and is recorded in the run-metadata JSON's
``lmp_source`` block, so a synthetic run can never be mistaken for a priced
premium result.

Reuses :func:`lce_portfolio.cli.run_one_iso` for the actual pipeline
(intake -> resources -> profiles -> LP -> sweep -> outputs); this script only
adds LMP/load resolution and the synthetic-data labeling on top.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]  # scope2-lce-portfolio/
_MARKET_SIM_ROOT = _ROOT.parent  # market-simulator/
sys.path.insert(0, str(_ROOT / "src"))
sys.path.insert(0, str(_ROOT / "scripts"))

from lce_portfolio.cli import run_one_iso  # noqa: E402
from lce_portfolio.config import PortfolioConfig  # noqa: E402
from make_reference_load import build_reference_load  # noqa: E402

DEFAULT_INPUTS_DIR = _ROOT / "data" / "inputs"
DEFAULT_OUT_DIR = _ROOT / "data" / "outputs"
DEFAULT_REFERENCE_LOAD = _ROOT / "data" / "reference" / "reference_load_100mw.csv"
EXPORTER = _MARKET_SIM_ROOT / "scripts" / "export_lce_lmp.py"

# The measured-shape vintage scripts/build_profiles.py builds by default —
# independent of the modeled `year` (a 2030 study year still prices against
# 2024's real hourly wind/solar shapes; see PortfolioConfig.profile_shape_year).
PROFILE_SHAPE_YEAR = 2024

SYNTHETIC_BANNER = (
    "\n"
    + "=" * 78
    + "\nSYNTHETIC LMP — wiring validation only, NOT a real premium result\n"
    + "=" * 78
)


def resolve_lmp_path(
    iso: str,
    explicit: str | Path | None,
    inputs_dir: str | Path,
    year: int,
) -> tuple[Path | None, dict]:
    """Resolve which LMP file to price ``iso`` against, ADR-0011 precedence.

    Order: explicit ``--lmp`` path (any filename) > newest real (i.e. not
    ``*_dummy.csv``) ``bau_lmp_*.csv`` under ``inputs_dir`` > newest existing
    dummy that covers ``iso`` (``bau_lmp_{iso}_*_dummy.csv``, or a legacy
    un-keyed ``bau_lmp_*_dummy.csv`` whose ``iso`` column contains it) >
    nothing found (``path`` is ``None``; the caller generates a dummy file).
    Dummy files are ISO-keyed (audit finding CL-12): the documented
    run-ERCOT-then-PJM workflow used to reuse ERCOT's un-keyed dummy for PJM
    and crash in intake.

    Returns ``(path, info)``. ``info`` always carries ``source`` (one of
    ``explicit`` / ``real`` / ``dummy_existing`` / ``none``) and
    ``is_synthetic`` (bool) for the run-metadata sidecar and banner decision.
    A ``path`` returned here is not read or validated — that happens in the
    normal intake pipeline (:func:`lce_portfolio.intake.prepare_lmp`).
    """
    if explicit is not None:
        path = Path(explicit)
        if not path.exists():
            raise FileNotFoundError(f"--lmp file not found: {path}")
        is_dummy = path.stem.endswith("_dummy")
        return path, {"source": "explicit", "is_synthetic": is_dummy, "path": str(path)}

    inputs_dir = Path(inputs_dir)
    candidates = sorted(inputs_dir.glob("bau_lmp_*.csv")) if inputs_dir.exists() else []
    real = [p for p in candidates if not p.stem.endswith("_dummy")]
    if real:
        newest = max(real, key=lambda p: p.stat().st_mtime)
        return newest, {"source": "real", "is_synthetic": False, "path": str(newest)}

    dummy = [
        p for p in candidates if p.stem.endswith("_dummy") and _dummy_covers_iso(p, iso)
    ]
    if dummy:
        newest = max(dummy, key=lambda p: p.stat().st_mtime)
        return newest, {
            "source": "dummy_existing",
            "is_synthetic": True,
            "path": str(newest),
        }

    return None, {"source": "none", "is_synthetic": True, "path": None}


def _dummy_covers_iso(path: Path, iso: str) -> bool:
    """True if a dummy LMP file is keyed to (or actually contains) ``iso``.

    ISO-keyed filenames (``bau_lmp_{iso}_...``) are matched by name; legacy
    un-keyed files are peeked (header + iso column) so another ISO's dummy is
    never silently reused (audit finding CL-12).
    """
    if f"_{iso}_".lower() in path.stem.lower():
        return True
    try:
        import pandas as pd

        isos = pd.read_csv(path, usecols=["iso"])["iso"].unique()
        return iso in set(isos)
    except Exception:
        return False


def generate_dummy_lmp(iso: str, year: int, out_dir: Path) -> Path:
    """Invoke the market-sim exporter's ``--dummy`` stub for one ISO.

    Runs ``scripts/export_lce_lmp.py`` (market-sim side) as a subprocess —
    this tool stays free of any ``import market_sim``. Returns the written
    CSV path.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"bau_lmp_{iso}_{year}_dummy.csv"
    cmd = [
        sys.executable,
        str(EXPORTER),
        "--dummy",
        "--iso",
        iso,
        "--year",
        str(year),
        "--out",
        str(out_path),
    ]
    print(f"no LMP file found for {iso}; generating synthetic stub:\n  {' '.join(cmd)}")
    subprocess.run(cmd, check=True, cwd=_MARKET_SIM_ROOT)
    return out_path


def ensure_reference_load(path: Path) -> Path:
    """Return ``path``, generating the deterministic reference load if absent.

    ``data/reference/`` is gitignored (the CSV is ~2 MB; see ``.gitignore``),
    so a fresh checkout regenerates it on first use from
    :func:`make_reference_load.build_reference_load` (byte-identical to
    running ``scripts/make_reference_load.py`` directly).
    """
    if path.exists():
        return path
    print(f"reference load not found at {path}; generating it")
    df = build_reference_load()
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, float_format="%.3f")
    return path


def main(argv: list[str] | None = None) -> int:
    """Parse args, resolve LMP/load, run the sweep, print the frontier."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iso", required=True, help="ISO to run, e.g. ERCOT")
    parser.add_argument("--lmp", default=None, help="explicit BAU LMP CSV/Parquet path")
    parser.add_argument("--year", type=int, default=2030, help="modeled study year")
    parser.add_argument(
        "--load", default=str(DEFAULT_REFERENCE_LOAD), help="load-intake file"
    )
    parser.add_argument(
        "--inputs-dir",
        default=str(DEFAULT_INPUTS_DIR),
        help="directory searched for existing bau_lmp_*.csv files",
    )
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    args = parser.parse_args(argv)

    iso = args.iso.upper()
    inputs_dir = Path(args.inputs_dir)
    try:
        return _run(args, iso, inputs_dir)
    except (ValueError, KeyError, OSError, subprocess.CalledProcessError) as exc:
        # Same clean-error contract as lce_portfolio.cli (audit CL-12): a bad
        # ISO/LMP pairing is a one-line message, not a traceback.
        msg = exc.args[0] if isinstance(exc, KeyError) and exc.args else exc
        print(f"error: {msg}", file=sys.stderr)
        return 1


def _run(args: argparse.Namespace, iso: str, inputs_dir: Path) -> int:
    """Resolve inputs and run the sweep (split from main for clean errors)."""
    load_path = ensure_reference_load(Path(args.load))

    lmp_path, lmp_info = resolve_lmp_path(iso, args.lmp, inputs_dir, args.year)
    if lmp_path is None:
        lmp_path = generate_dummy_lmp(iso, args.year, inputs_dir)
        lmp_info = {"source": "generated", "is_synthetic": True, "path": str(lmp_path)}

    if lmp_info["is_synthetic"]:
        print(SYNTHETIC_BANNER)
    print(f"LMP source: {lmp_info['source']} ({lmp_path})")

    config = PortfolioConfig(
        iso=iso,
        year=args.year,
        profile_shape_year=PROFILE_SHAPE_YEAR,
        load_file=str(load_path),
        lmp_file=str(lmp_path),
    )

    out_dir = Path(args.out_dir)
    run_one_iso(config, load_path, lmp_path, out_dir)

    # Post-process the run-metadata JSON that write_outputs() just wrote:
    # append the LMP provenance/synthetic label (cli.run_one_iso has no seam
    # for extra metadata, and this tool never touches that pipeline beyond
    # this documented seam-through-the-file step).
    meta_path = out_dir / f"{iso}_run_metadata.json"
    if meta_path.exists():
        meta = json.loads(meta_path.read_text())
        meta["lmp_source"] = lmp_info
        meta_path.write_text(json.dumps(meta, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
