"""SOCO-60 phase 0 — the SOCO benchmark's plant boundary, measured (ZERO LP).

The model's SOCO fleet census is EIA-860 ``Balancing Authority Code == "SOCO"``
at the current vintage (soco-data-audit §1 row 1). The benchmark's EIA-923 frame
is restricted by ``run_calibration_full._iso_plant_ids`` → ``build_zone_lookup``,
whose base is eGRID 2023 ``BACODE``. eGRID 2023 still codes the former Gulf Power
plants (Lansing Smith 643, Gulf Clean Energy Center 641, Pea Ridge 7715, …) to
SOCO; EIA-860 recodes them to FPL from vintage 2024; EIA-930's SOCO series
excludes them in every year 2019–2024 (mode ``ba``). The benchmark therefore
scores plants neither the model nor the SOCO BA contains, and its combined
fossil reconcile then removes that energy by scaling EVERY fossil class down.

Modes
-----
``ba``     -- EIA-930 SOCO gas+coal vs SOCO EIA-923 fossil with / without the
              plants EIA-860 (current) recodes to another BA, per year.
``bench``  -- rebuild one year's benchmark from a per-year leg bundle, in THIS
              process, with ``--drop-recoded`` optionally applied to
              ``_iso_plant_ids``; print classFull and every scored C1 row.
              Run each side in its OWN process (SOCO-59 P14: several helpers
              are ``@lru_cache``'d).
"""

from __future__ import annotations

import argparse
import glob
import json
import shutil
import sys
from pathlib import Path

import pandas as pd

_ROOT = Path(__file__).resolve().parents[2]
for _p in (str(_ROOT), str(_ROOT / "src"), str(_ROOT / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)


def recoded_plants(iso: str = "SOCO") -> frozenset[int]:
    """Plants in the benchmark base whose CURRENT EIA-860 BA code is another BA."""
    from market_sim.data.zone_assignment import build_zone_lookup

    base = set(build_zone_lookup(iso))
    p = pd.read_parquet(_ROOT / "data/raw/eia-860/eia860_plant.parquet")
    code = p.drop_duplicates("Plant Code").set_index("Plant Code")[
        "Balancing Authority Code"
    ]
    code = code.astype(str).str.strip()
    return frozenset(
        int(x)
        for x in base
        if x in code.index and code[x] not in ("", "nan", "None", iso)
    )


def ba_check() -> None:
    """EIA-930 SOCO gas+coal against 923 fossil with and without the recoded plants."""
    sys.path.insert(0, str(_ROOT / "scripts/probes"))
    from _soco54_phase0 import _actuals

    drop = recoded_plants()
    print("recoded plants:", sorted(drop))
    for y in range(2019, 2025):
        fs = glob.glob(str(_ROOT / f"data/raw/eia-930/EIA930_BALANCE_{y}_*.parquet"))
        cols = [
            "Balancing Authority",
            "Net Generation (MW) from Coal",
            "Net Generation (MW) from Natural Gas",
        ]
        d = pd.concat([pd.read_parquet(f, columns=cols) for f in fs])
        s = d[d["Balancing Authority"] == "SOCO"]
        num = lambda c: (
            pd.to_numeric(s[c].astype(str).str.replace(",", ""), errors="coerce").sum()
            / 1e6
        )
        e930 = num(cols[1]) + num(cols[2])
        a = _actuals(y).reset_index()
        fos = a[a.klass.str.match("^(CC_|CT_|ST_|COAL)")]
        tot = fos.annual_mwh.sum()
        out = fos[fos.plant_id.isin(drop)].annual_mwh.sum()
        print(
            f"{y}  930 {e930:7.2f} | 923 all {tot:7.2f} (930/923 {e930 / tot:.3f}) | "
            f"923 ex-recoded {tot - out:7.2f} ({e930 / (tot - out):.3f}) | recoded {out:5.2f}"
        )


def bench(
    leg: Path, year: int, drop_recoded: bool, scratch: Path, no_fold: bool = False
) -> None:
    """Rebuild ``year``'s benchmark off ``leg`` and score C1 against it."""
    import calibration_verdict as cv
    import render_calibration_html as rch
    import run_calibration_full as rcf

    if no_fold:
        _orig_fold = rch._gas_foldin_deflation
        rch._gas_foldin_deflation = lambda cf, e930, iso: (
            0.0 if iso == "SOCO" else _orig_fold(cf, e930, iso)
        )

    if drop_recoded:
        drop = recoded_plants()
        orig = rcf._iso_plant_ids

        def patched(iso, yr=None, vintage_union=False):
            base = orig(iso, yr, vintage_union)
            return base - drop if iso == "SOCO" else base

        rcf._iso_plant_ids = patched
    work = (
        scratch
        / (("drop" if drop_recoded else "ctrl") + ("_nofold" if no_fold else ""))
        / "results/calibration"
        / leg.name
    )
    if work.exists():
        shutil.rmtree(work)
    shutil.copytree(leg, work, ignore=shutil.ignore_patterns("dispatch", "floors"))
    (work / "dispatch").mkdir()
    for f in (leg / "dispatch").glob(f"{year}_P1*.parquet"):
        (work / "dispatch" / f.name).symlink_to(f)
    iso, frames = rcf.build_benchmark_frames(work)
    meta = json.loads((work / "meta.json").read_text())
    si = dict(meta.get("shared_inputs", {}))
    for name, frame in frames.items():
        si[name] = rcf.write_shared_input(frame, name, iso, work)
    meta["shared_inputs"] = si
    (work / "meta.json").write_text(json.dumps(meta, indent=2) + "\n")
    pay = rch.build_payload([("x", work)], {year})
    yb = pay["bench"][year]
    ypay = pay["model"][0]["years"][year]
    cf = yb["classFull"]
    print("classFull", {k: round(v, 3) for k, v in sorted(cf.items())})
    for r in cv.score_fuelmix(year, ypay, yb, iso):
        if str(r.get("status")).upper() in ("SKIPPED", "SKIP"):
            continue
        print(
            f"  {r['key']:<11} {r['status']:<5} model {r.get('model')!s:>8} actual {r.get('actual')!s:>8} "
            f"{r.get('magnitude', '')}  tol {r.get('tol', '')[-24:]}"
        )


def main() -> None:
    """CLI entry."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("mode", choices=("ba", "bench"))
    ap.add_argument("--leg")
    ap.add_argument("--year", type=int)
    ap.add_argument("--drop-recoded", action="store_true")
    ap.add_argument(
        "--no-fold", action="store_true", help="SOCO gas_foldin_deflation -> 0"
    )
    ap.add_argument("--scratch", default="/tmp/soco60_bench")
    a = ap.parse_args()
    if a.mode == "ba":
        ba_check()
    else:
        bench(Path(a.leg).resolve(), a.year, a.drop_recoded, Path(a.scratch), a.no_fold)


if __name__ == "__main__":
    main()
