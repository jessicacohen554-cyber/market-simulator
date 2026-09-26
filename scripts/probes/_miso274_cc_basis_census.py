#!/usr/bin/env python3
"""miso-274 phase 0 (zero LP): the CC outage numerator-basis census (charter candidate 1).

Under the keeper's ``unit_outage_dispatched_bin_denominator`` every CC_REGULAR
row removes ``unit_capacity_mw / cap_LP`` of its bin, where the numerator is on
the CAMPD extract's basis (steam-augmented CT nameplate or observed gross peak)
and ``cap_LP`` is the dispatched bin's net pmax. At a block plant whose extract
basis exceeds ``cap_LP`` a one-train outage then removes more than one train's
share. The alternative is the extract's OWN fraction
(``unit_outage_extract_basis_share``, nyiso-196): ``ucap / basis`` with basis
from :func:`market_sim.data.outages._extract_basis_index`, applied to the same
``cap_LP``.

This re-runs the shared accumulator
(:func:`market_sim.data.outages._unit_outage_factors_from_events`) on the
keeper's own flags and LP roster for the >= 5-day unitroute and < 5-day
short-gas CC_REGULAR rows, once as the keeper does it and once with each row's
``unit_capacity_mw`` rescaled by ``cap_LP / basis`` — which makes the keeper's
own divide yield exactly ``ucap / basis`` (the per-unit clip scales with it).
It reports, per bin and in total, the CC_REGULAR available TWh the keeper's
construction removes beyond the extract-own-basis one.

It needs the keeper fleet frames written by ``_miso271_cc_decomp.py``
(``<frames>/<Y>_B.parquet``) for the LP roster.

Usage::

    uv run python scripts/probes/_miso274_cc_basis_census.py --frames <dir> \
        --out results/calibration/_miso274_cc_basis_census.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
for p in (str(REPO), str(REPO / "src")):
    if p not in sys.path:
        sys.path.insert(0, p)

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from market_sim.config.plant_taxonomy import artifact_class  # noqa: E402
from market_sim.data import outages as O  # noqa: E402

RAW = REPO / "data/raw"
FILES = {
    "ge5d": RAW / "campd-unit-outages-unitroute-MISO.csv",
    "shortgas": RAW / "campd-unit-outages-shortgas-MISO.csv",
}
CC = "CC_REGULAR"


def _factors(df: pd.DataFrame, year: int, roster: tuple) -> dict:
    """The keeper's accumulator call (its own outage flags)."""
    return O._unit_outage_factors_from_events(
        df,
        year,
        8760,
        O.BINS_CSV_DEFAULT,
        "MISO",
        fleet_status_scope=True,
        st_capacity_basis=True,
        per_unit_clip=True,
        mid_vintage_exit_carry=True,
        lp_bin_capacity=roster,
    )


def main() -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--frames", required=True)
    ap.add_argument("--years", nargs="+", type=int, default=list(range(2019, 2026)))
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    res: dict[str, dict] = {}
    for y in args.years:
        b = pd.read_parquet(Path(args.frames) / f"{y}_B.parquet")
        b["ag"] = [artifact_class(g) for g in b.group]
        cap = b.groupby([b.plant_code.astype(int), "ag"]).pmax.sum()
        roster = tuple(
            sorted(((int(k[0]), k[1]), float(v)) for k, v in cap.items() if v > 0)
        )
        per_bin: dict[int, dict] = {}
        tot = {"keeper_removed_twh": 0.0, "extract_basis_removed_twh": 0.0}
        for name, path in FILES.items():
            raw = pd.read_csv(path)
            basis = O._extract_basis_index(raw)
            df = raw[raw.plant_group == CC].copy()
            if name == "ge5d":
                df = df[df["duration_days"] >= O.UNIT_OUTAGE_MIN_DAYS]
            else:
                df = df[df["duration_days"] < O.UNIT_OUTAGE_MIN_DAYS]
            alt = df.copy()
            scale = []
            for r in alt.itertuples(index=False):
                clp = cap.get((int(r.facility_id), CC))
                eb = basis.get((int(r.facility_id), CC))
                den = None
                if eb is not None:
                    single, gb = eb
                    pc = r.plant_capacity_mw
                    den = (
                        float(pc)
                        if (single and pd.notna(pc) and pc > 0)
                        else (gb if gb > 0 else None)
                    )
                scale.append(clp / den if (clp and den) else 1.0)
            alt["unit_capacity_mw"] = alt["unit_capacity_mw"] * np.asarray(scale)
            fk, fa = _factors(df, y, roster), _factors(alt, y, roster)
            for key in set(fk) | set(fa):
                if key[1] != CC:
                    continue
                clp = float(cap.get(key, 0.0))
                rk = float((1.0 - fk.get(key, np.ones(8760))).sum()) * clp / 1e6
                ra = float((1.0 - fa.get(key, np.ones(8760))).sum()) * clp / 1e6
                d = per_bin.setdefault(
                    key[0], {"cap_lp": round(clp, 1), "keeper": 0.0, "extract": 0.0}
                )
                d["keeper"] += rk
                d["extract"] += ra
                tot["keeper_removed_twh"] += rk
                tot["extract_basis_removed_twh"] += ra
        rows = {
            k: {
                "cap_lp": v["cap_lp"],
                "keeper_twh": round(v["keeper"], 3),
                "extract_twh": round(v["extract"], 3),
                "excess_twh": round(v["keeper"] - v["extract"], 3),
            }
            for k, v in sorted(
                per_bin.items(), key=lambda kv: kv[1]["extract"] - kv[1]["keeper"]
            )
        }
        res[str(y)] = {
            **{k: round(v, 3) for k, v in tot.items()},
            "excess_twh": round(
                tot["keeper_removed_twh"] - tot["extract_basis_removed_twh"], 3
            ),
            "per_bin": rows,
        }
        print(
            json.dumps({y: {k: v for k, v in res[str(y)].items() if k != "per_bin"}}),
            flush=True,
        )
    Path(args.out).write_text(json.dumps(res, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
