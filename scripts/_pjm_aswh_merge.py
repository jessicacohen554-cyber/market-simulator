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

# Year-tagged parquets that concatenate across bundles.
_CONCAT = ["system", "eia930", "eia923", "storage", "campd", "btm"]


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
    (out / "meta.json").write_text(json.dumps(meta, indent=2))
    print(f"  meta: years {meta['years']} gas {meta['gas_prices']}")

    # run_config.json: copy the first year's (records as_reserve_withholding +
    # the full keeper config), patch the year list + gas prices for provenance.
    rc_path = year_dirs[0] / "run_config.json"
    if rc_path.exists():
        rc = json.loads(rc_path.read_text())
        rc.setdefault("calibration_flags", {})["years"] = meta["years"]
        rc["calibration_flags"]["gas_prices"] = gas_prices
        rc["model_changes_note"] = (
            "pjm_27_aswh: keeper pjm_26 config + AS reserve-withholding "
            "(PJM Primary Reserve requirement), 2023-25 merged from parallel "
            "per-year solves.")
        (out / "run_config.json").write_text(json.dumps(rc, indent=2))
    print(f"merged -> {out}")


if __name__ == "__main__":
    main(Path(sys.argv[1]), [Path(p) for p in sys.argv[2:]])
