"""Merge the per-year PJM withholding bundles into one multi-year bundle.

The three withholding years were solved to separate out-dirs (parallel jobs,
claude.md #45). The overlay deriver and LMP-residual analyzer expect a single
bundle with all years, so this concatenates the year-tagged parquets, copies
the per-year dispatch files, and merges meta.json / run_config.json.

Usage: python scripts/_pjm_aswh_merge.py <out_bundle> <year_dir> [<year_dir> ...]
"""
import json
import shutil
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _bundle_io import (  # noqa: E402
    SHARED_INPUT_NAMES,
    bundle_input_path,
    write_shared_input,
)

# Year-tagged parquets that concatenate across bundles. The benchmark/input
# frames (eia930/eia923/campd) now live in the content-addressed shared store
# referenced from meta.json, not in-bundle, so they are reconciled separately
# (see below) rather than concatenated as loose files here.
_CONCAT = ["system", "storage", "btm"]


def main(out: Path, year_dirs: list[Path]) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "dispatch").mkdir(exist_ok=True)

    for name in _CONCAT:
        frames = []
        for d in year_dirs:
            p = d / f"{name}.parquet"
            if p.exists():
                frames.append(pd.read_parquet(p))
        if frames:
            df = pd.concat(frames, ignore_index=True)
            df = df.sort_values("year").reset_index(drop=True)
            df.to_parquet(out / f"{name}.parquet", index=False)
            print(f"  {name}: {df.shape} years {sorted(df['year'].unique())}")

    # Per-year dispatch parquets: copy each verbatim.
    for d in year_dirs:
        for f in (d / "dispatch").glob("*.parquet"):
            shutil.copy2(f, out / "dispatch" / f.name)
    print(f"  dispatch: {[f.name for f in sorted((out/'dispatch').glob('*.parquet'))]}")

    # meta.json: take the first, merge years + gas_prices across all.
    metas = [json.loads((d / "meta.json").read_text()) for d in year_dirs]
    meta = dict(metas[0])
    years, gas_prices = [], {}
    for m in metas:
        years += list(m["years"])
        gas_prices.update(m["gas_prices"])
    meta["years"] = sorted(set(years))
    meta["gas_prices"] = gas_prices

    # Reconcile the content-addressed shared inputs: each per-year bundle
    # references a single-year eia930/eia923/campd in the shared store, so the
    # merged bundle must concatenate all years and re-reference the combined
    # frame (otherwise the dashboard/scorer only sees the first year's bench).
    iso = meta.get("iso", "PJM")
    shared_refs: dict[str, str] = {}
    for name in SHARED_INPUT_NAMES:
        frames = []
        for d in year_dirs:
            p = bundle_input_path(d, name)
            if p is not None:
                frames.append(pd.read_parquet(p))
        if frames:
            df = pd.concat(frames, ignore_index=True)
            if "year" in df.columns:
                df = df.sort_values("year").reset_index(drop=True)
            shared_refs[name] = write_shared_input(df, name, iso, out)
            yrs = sorted(df["year"].unique()) if "year" in df.columns else "n/a"
            print(f"  {name}: {df.shape} years {yrs}")
    if shared_refs:
        meta["shared_inputs"] = shared_refs

    (out / "meta.json").write_text(json.dumps(meta, indent=2))
    print(f"  meta: years {meta['years']} gas {meta['gas_prices']}")

    # run_config.json: copy the first year's (records as_reserve_withholding +
    # the full keeper config), patch the year list + gas prices for provenance.
    rc_path = year_dirs[0] / "run_config.json"
    if rc_path.exists():
        rc = json.loads(rc_path.read_text())
        rc.setdefault("calibration_flags", {})["years"] = meta["years"]
        rc["calibration_flags"]["gas_prices"] = gas_prices
        # Preserve the per-year solve's own note (set via the runner's --note),
        # appending the merge provenance rather than overwriting with a
        # run-specific string.
        base_note = rc.get("model_changes_note", "")
        rc["model_changes_note"] = (
            f"{base_note} [merged 2023-25 from parallel per-year solves]"
        ).strip()
        (out / "run_config.json").write_text(json.dumps(rc, indent=2))
    print(f"merged -> {out}")


if __name__ == "__main__":
    main(Path(sys.argv[1]), [Path(p) for p in sys.argv[2:]])
