"""nyiso-111 pre-check: does the keeper's own dispatch cross NYISO's measured ramp envelope? (no LP)

The cross-ISO transfer under test is ``ScenarioConfig.ramp_limits``
(matrix row ``ramp_envelopes``, NYISO cell ``U``; PJM keeper since pjm-140).
With the flag off the LP asserts every thermal plant can move from ANY output
to ANY other in one hour; NYISO's own CAMPD conduct says otherwise
(``derive_campd_ramp_envelopes.py --iso NYISO``: 77 rows / 48 well-observed
plants, CC up-envelope median 0.49 x pmax, ST 0.42, CT 0.92).

**pjm-140's all-ISO lesson is binding here** (matrix ``ramp_envelopes`` note):
a MAX-based envelope cannot be pre-checked with a p99-based excess statistic —
*pre-check a bound against the bound*.  So this probe measures the ONE
statistic that is a bound-against-the-bound test and is also the statistic
pjm-140's rule-1/rule-14 promotion rested on:

    over ALL (plant, ramp-family) group transitions the keeper actually
    solved, how many cross the group's own measured envelope, and how many
    MWh of infeasible ramping do they carry?

Construction
------------
* Groups and envelopes come from the LIVE loader
  (:func:`market_sim.data.fleet.build_ramp_groups`) on the fleet rebuilt at
  the keeper's exact settings, so the MW compared against are exactly the
  rows the LP would impose — including the gross->net parasitic rebasis and
  the loader's own pruning of groups whose envelope cannot bind.
* Dispatch comes from the control bundle's per-plant ``dispatch/<year>_P1``
  frame, summed to the same (plant, family) grouping.
* Reported both ways (crossing COUNT and crossing MWh) and as a share of the
  group-transition population, per year.

This is a one-sided test: crossings PROVE the rows would bind; the absence of
crossings does not prove inertness (a bound can reshape a solution without the
unconstrained solution having crossed it).  Reported, never gated.

Usage::

    PYTHONPATH=.:src python scripts/probes/_nyiso111_ramp_envelope_precheck.py \
        --bundle results/calibration/nyiso109_zonalanchor_B \
        --dispatch-from results/calibration/nyiso111_control_A_y2023 \
        --years 2023 \
        --out results/calibration/_nyiso111_ramp_precheck.json
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]


class _FleetCaptured(Exception):
    """Control-flow sentinel: stop the replay once the fleet arrays exist."""


def _keeper_fleet(bundle: Path, year: int) -> dict:
    """Rebuild the EXACT fleet arrays the keeper solved against — no LP.

    Verbatim reuse of ``_nyiso110_peak_half_decomposition._keeper_fleet``.
    """
    spec = importlib.util.spec_from_file_location(
        "_replay_keeper", REPO / "scripts" / "replay_keeper.py"
    )
    rk = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(rk)

    from scripts import run_calibration
    from scripts import run_calibration_full as rcf

    meta = json.loads((bundle / "meta.json").read_text())
    kwargs = rk.build_kwargs(meta)
    kwargs["years"] = [year]
    kwargs["iso"] = meta["iso"]
    kwargs["hours"] = int(meta.get("hours", 8760))
    kwargs["reference"] = rcf._load_reference()
    kwargs["run_dir"] = bundle

    captured: dict = {}
    real_run_year = run_calibration.run_year

    def _intercept(*args, **kw):
        kw["fleet_only"] = True
        captured["state"] = real_run_year(*args, **kw)
        raise _FleetCaptured

    run_calibration.run_year = _intercept
    rcf.run_year = _intercept
    try:
        rcf.solve_and_persist(**kwargs)
    except _FleetCaptured:
        pass
    finally:
        run_calibration.run_year = real_run_year
        rcf.run_year = real_run_year
    if "state" not in captured:
        raise SystemExit("fleet reconstruction did not reach run_year")
    return captured["state"]


def measure(bundle: Path, dispatch_dir: Path, year: int) -> dict:
    """Crossing census for one year."""
    from market_sim.data.fleet import build_ramp_groups

    state = _keeper_fleet(bundle, year)
    fa = state["fleet_arrays"]
    groups = build_ramp_groups(fa, "NYISO")
    if groups is None:
        return {"year": year, "error": "build_ramp_groups returned None"}
    gen_idx, group_col, ramp_up, ramp_dn = groups

    unit_ids = np.asarray(fa.unit_ids, dtype=object)
    pmax = np.asarray(fa.pmax, dtype=float)
    member_unit = {str(unit_ids[int(g)]): int(grp) for g, grp in zip(gen_idx, group_col)}
    n_groups = int(len(ramp_up))
    group_cap = np.zeros(n_groups, dtype=float)
    for g, grp in zip(gen_idx, group_col):
        group_cap[int(grp)] += float(pmax[int(g)])

    disp = pd.read_parquet(dispatch_dir / "dispatch" / f"{year}_P1.parquet")
    disp = disp[disp["unit_id"].astype(str).isin(member_unit)].copy()
    disp["grp"] = disp["unit_id"].astype(str).map(member_unit)
    wide = disp.pivot_table(index="hour", columns="grp", values="mw", aggfunc="sum").sort_index()
    cols = list(wide.columns)
    arr = wide.to_numpy(dtype=float)
    dv = np.diff(arr, axis=0)  # (T-1, n_group)

    ru = np.array([ramp_up[c] for c in cols], dtype=float)
    rd = np.array([ramp_dn[c] for c in cols], dtype=float)
    cap = np.array([group_cap[c] for c in cols], dtype=float)

    tol = 1e-6
    up_x = np.maximum(dv - ru[None, :], 0.0)
    dn_x = np.maximum(-dv - rd[None, :], 0.0)
    n_trans = int(dv.size)
    n_up = int((up_x > tol).sum())
    n_dn = int((dn_x > tol).sum())
    mwh_up = float(up_x.sum())
    mwh_dn = float(dn_x.sum())

    # per-family split
    fam: dict[str, dict] = {}
    fam_of = {}
    for g, grp in zip(gen_idx, group_col):
        fam_of[int(grp)] = str(np.asarray(fa.plant_group, dtype=object)[int(g)])
    for i, c in enumerate(cols):
        f = fam_of.get(int(c), "?")
        d = fam.setdefault(f, {"groups": 0, "cap_mw": 0.0, "cross": 0, "mwh": 0.0, "trans": 0})
        d["groups"] += 1
        d["cap_mw"] += float(cap[i])
        d["cross"] += int((up_x[:, i] > tol).sum() + (dn_x[:, i] > tol).sum())
        d["mwh"] += float(up_x[:, i].sum() + dn_x[:, i].sum())
        d["trans"] += int(dv.shape[0])

    return {
        "year": year,
        "n_groups_with_rows": n_groups,
        "enveloped_capacity_mw": round(float(group_cap.sum()), 1),
        "group_transitions": n_trans,
        "crossings_up": n_up,
        "crossings_dn": n_dn,
        "crossing_share_pct": round(100.0 * (n_up + n_dn) / max(n_trans, 1), 4),
        "infeasible_ramp_mwh_up": round(mwh_up, 1),
        "infeasible_ramp_mwh_dn": round(mwh_dn, 1),
        "infeasible_ramp_mwh_total": round(mwh_up + mwh_dn, 1),
        "by_family": {
            k: {
                "groups": v["groups"],
                "cap_mw": round(v["cap_mw"], 1),
                "crossings": v["cross"],
                "crossing_share_pct": round(100.0 * v["cross"] / max(2 * v["trans"], 1), 4),
                "infeasible_mwh": round(v["mwh"], 1),
            }
            for k, v in sorted(fam.items())
        },
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", default="results/calibration/nyiso109_zonalanchor_B")
    ap.add_argument("--dispatch-from", default="results/calibration/nyiso111_control_A_y2023")
    ap.add_argument("--years", nargs="+", type=int, default=[2023])
    ap.add_argument("--out", default="results/calibration/_nyiso111_ramp_precheck.json")
    args = ap.parse_args(argv)

    bundle = Path(args.bundle)
    if not bundle.is_absolute():
        bundle = REPO / bundle
    ddir = Path(args.dispatch_from)
    if not ddir.is_absolute():
        ddir = REPO / ddir

    rows = [measure(bundle, ddir, y) for y in args.years]
    out = Path(args.out)
    if not out.is_absolute():
        out = REPO / out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"probe": "nyiso-111 ramp-envelope pre-check", "years": rows}, indent=1))

    for r in rows:
        if "error" in r:
            print(r)
            continue
        print(f"=== {r['year']} ===")
        print(
            f"  {r['n_groups_with_rows']} enveloped groups, {r['enveloped_capacity_mw']:,.1f} MW; "
            f"{r['group_transitions']:,} group-transitions"
        )
        print(
            f"  crossings: up {r['crossings_up']:,} / dn {r['crossings_dn']:,} "
            f"= {r['crossing_share_pct']} % of transitions"
        )
        print(
            f"  infeasible ramping: {r['infeasible_ramp_mwh_total']:,.1f} MWh "
            f"(up {r['infeasible_ramp_mwh_up']:,.1f} / dn {r['infeasible_ramp_mwh_dn']:,.1f})"
        )
        for f, v in r["by_family"].items():
            print(
                f"    {f:14s} groups={v['groups']:3d} cap={v['cap_mw']:9.1f} MW "
                f"crossings={v['crossings']:7,d} ({v['crossing_share_pct']:6.3f} %) "
                f"infeasible={v['infeasible_mwh']:12,.1f} MWh"
            )
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
