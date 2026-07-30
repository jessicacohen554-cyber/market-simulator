"""pjm-140 STEP 1 — coverage disclosure for the measured PJM ramp envelope.

`PREREG-pjm140-ramp-envelopes-2026-07-30.md` §7.3 requires the derive's own
coverage be reported BEFORE any verdict (the pjm-137 disclosure pattern), and
§6 kill **K7** rejects the delta outright if the loader's pruning leaves fewer
than half the ISO's thermal capacity carrying a live envelope.

This probe answers exactly that, with **no LP**. It rebuilds the keeper's own
fleet arrays through ``replay_keeper.build_kwargs`` -> ``run_year`` with
``fleet_only=True`` (the `_pjm138_marginal_ownership::_keeper_fleet` pattern),
then calls the production loader
:func:`market_sim.data.fleet.campd_bins.build_ramp_groups` and re-derives its
per-group accounting so the reported numbers are the loader's, not a
re-implementation of it.

Reported, per year:

- artifact rows by (bucket, basis): plants ENVELOPED (``basis == "plant"``),
  plants on the SPARSE row (below ``MIN_OBS_HOURS = 4000`` observed online
  hours, informational only — the loader never reads them), and the
  ``class_fraction`` fallback rows;
- for every (plant, CC/CT/ST) group in the model fleet: which resolution path
  it took (measured MW / class fraction / no row), its envelope after the
  gross->net rebasis, its group pmax, and whether the loader PRUNED it as
  non-binding (``RU >= cap`` AND ``RD >= cap``);
- the gross->net rebasis factors actually applied (measured per-plant
  EIA-923-net / CAMPD-gross vs the cited class default), min/median/max;
- **the K7 statistic**: live-envelope capacity as a share of the ISO's total
  thermal (ramp-bucket-eligible) capacity, and of ALL generator capacity.

Usage::

    PYTHONPATH=. .venv/bin/python scripts/probes/_pjm140_ramp_coverage.py \
        --bundle results/calibration/pjm137_ctheatrate_B --years 2023 2024 2025
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
import sys  # noqa: E402

sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

HOURS = 8760


class _FleetCaptured(Exception):
    """Control-flow signal: the fleet arrays are built, unwind the solve."""


def _keeper_fleet(bundle: Path, year: int) -> dict:
    """Rebuild the EXACT fleet arrays the keeper solved against — no LP.

    Identical interception to ``_pjm138_marginal_ownership::_keeper_fleet``:
    ``run_year`` is wrapped to force ``fleet_only=True`` (which returns the
    built arrays instead of constructing the LP), the state is stashed and the
    solve unwinds before any output stage.
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
    kwargs["hours"] = int(meta.get("hours", HOURS))
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


def _group_audit(fleet, iso: str) -> pd.DataFrame:
    """Per (plant, bucket) group audit mirroring ``build_ramp_groups`` exactly.

    Re-walks the loader's own resolution order — measured MW row (rebased
    gross->net by that plant's factor), else the CC/ST class fraction x group
    pmax, else no row — and records the prune decision (``RU >= cap`` AND
    ``RD >= cap``) without duplicating any of its arithmetic: the module's own
    helpers supply the bucket map, the parasitic map and the rebasis factor.
    """
    from market_sim.data.fleet.campd_bins import (
        _RAMP_BUCKET_BY_GROUP,
        _ramp_parasitic_factor_map,
        load_campd_ramp_envelopes,
    )

    env = load_campd_ramp_envelopes(iso)
    if env is None:
        raise SystemExit(f"no ramp-envelope artifact for {iso}")

    plant_code = np.asarray(fleet.plant_code, dtype=int)
    pmax = np.asarray(fleet.pmax, dtype=float)
    plant_groups = np.asarray(fleet.plant_group, dtype=object)
    buckets = np.array(
        [_RAMP_BUCKET_BY_GROUP.get(str(g), "") for g in plant_groups], dtype=object
    )

    measured = {
        (int(r.plant_code), str(r.bucket)): (float(r.ramp_up_mw), float(r.ramp_dn_mw))
        for r in env[env.basis == "plant"].itertuples(index=False)
    }
    class_frac = {
        str(r.bucket): (float(r.ramp_up_mw), float(r.ramp_dn_mw))
        for r in env[env.basis == "class_fraction"].itertuples(index=False)
        if str(r.bucket) in ("CC", "ST")
    }
    parasitic = _ramp_parasitic_factor_map()

    members: dict[tuple[int, str], list[int]] = {}
    for i in np.flatnonzero((plant_code > 0) & (buckets != "")):
        members.setdefault((int(plant_code[i]), str(buckets[i])), []).append(int(i))

    rows = []
    for (pk, bucket), m in members.items():
        cap = float(pmax[m].sum())
        groups = sorted({str(plant_groups[i]) for i in m})
        rec = {
            "plant_code": pk,
            "bucket": bucket,
            "plant_groups": "+".join(groups),
            "n_cols": len(m),
            "cap_net_mw": cap,
            "path": "none",
            "factor": np.nan,
            "factor_src": "",
            "ru_mw": np.nan,
            "rd_mw": np.nan,
            "pruned": False,
            "live": False,
        }
        if (pk, bucket) in measured:
            ru, rd = measured[(pk, bucket)]
            factor = _net_basis_factor_for(pk, m, parasitic, plant_groups, pmax)
            rec["path"] = "measured"
            rec["factor"] = factor
            rec["factor_src"] = "measured" if int(pk) in parasitic else "class_default"
            ru, rd = ru * factor, rd * factor
        elif bucket in class_frac:
            fu, fd = class_frac[bucket]
            ru, rd = fu * cap, fd * cap
            rec["path"] = "class_fraction"
        else:
            rows.append(rec)
            continue
        rec["ru_mw"], rec["rd_mw"] = ru, rd
        rec["pruned"] = bool(ru >= cap and rd >= cap)
        rec["live"] = not rec["pruned"]
        rows.append(rec)
    return pd.DataFrame(rows)


def _net_basis_factor_for(pk, m, parasitic, plant_groups, pmax) -> float:
    """Gross->net factor for one group, via the loader's own resolution rule."""
    from market_sim.data.campd import DEFAULT_PARASITIC_LOAD_PCT
    from market_sim.data.fleet.campd_bins import _DEFAULT_PARASITIC_LOAD_PCT

    factor = parasitic.get(int(pk))
    if factor is not None:
        return float(factor)
    by_group: dict[str, float] = {}
    for i in m:
        g = str(plant_groups[i])
        by_group[g] = by_group.get(g, 0.0) + float(pmax[i])
    dominant = max(by_group, key=by_group.get) if by_group else ""
    pct = DEFAULT_PARASITIC_LOAD_PCT.get(dominant, _DEFAULT_PARASITIC_LOAD_PCT)
    return 1.0 - pct


def main() -> None:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", default="results/calibration/pjm137_ctheatrate_B")
    ap.add_argument("--iso", default="PJM")
    ap.add_argument("--years", nargs="+", type=int, default=[2023, 2024, 2025])
    ap.add_argument("--json-out", default="results/probes/pjm140_ramp_coverage.json")
    args = ap.parse_args()

    from market_sim.data.fleet.campd_bins import (
        build_ramp_groups,
        load_campd_ramp_envelopes,
    )

    env = load_campd_ramp_envelopes(args.iso)
    print(f"=== ARTIFACT: campd_ramp_envelopes_{args.iso}.csv — {len(env)} rows ===")
    tab = env.groupby(["bucket", "basis"]).size().unstack(fill_value=0)
    print(tab.to_string())
    print("\nclass_fraction fallback rows (loader uses CC/ST only):")
    print(
        env[env.basis == "class_fraction"][
            ["bucket", "ramp_up_mw", "ramp_dn_mw", "n_online_hours"]
        ].to_string(index=False)
    )
    meas = env[env.basis == "plant"]
    sparse = env[env.basis == "sparse"]
    print(
        f"\nENVELOPED (basis=plant, >= MIN_OBS_HOURS=4000 online h): {len(meas)} "
        f"(plant,bucket) groups, {meas.pmax_obs_mw.sum():,.0f} MW observed gross pmax"
    )
    print(
        f"SPARSE fallback (< 4000 online h, loader never reads these): "
        f"{len(sparse)} groups, {sparse.pmax_obs_mw.sum():,.0f} MW observed gross pmax"
    )

    out: dict = {
        "iso": args.iso,
        "bundle": str(args.bundle),
        "artifact_rows": int(len(env)),
        "artifact_by_bucket_basis": {
            f"{b}/{s}": int(n)
            for (b, s), n in env.groupby(["bucket", "basis"]).size().items()
        },
        "class_fraction": {
            str(r.bucket): {"up": float(r.ramp_up_mw), "dn": float(r.ramp_dn_mw)}
            for r in env[env.basis == "class_fraction"].itertuples(index=False)
        },
        "years": {},
    }

    for year in args.years:
        print(f"\n{'=' * 72}\n=== FLEET-SIDE COVERAGE, {args.iso} {year} ===")
        state = _keeper_fleet(Path(args.bundle), year)
        fa = state["fleet_arrays"]
        aud = _group_audit(fa, args.iso)

        pmax = np.asarray(fa.pmax, dtype=float)
        total_cap = float(pmax.sum())
        thermal_cap = float(aud.cap_net_mw.sum())  # ramp-bucket-eligible columns

        live = aud[aud.live]
        pruned = aud[aud.pruned]
        norow = aud[aud.path == "none"]
        live_cap = float(live.cap_net_mw.sum())

        print(
            f"model fleet: {len(pmax)} generator columns, {total_cap:,.0f} MW; "
            f"ramp-bucket-eligible (CC/CT/ST plant groups) "
            f"{len(aud)} (plant,bucket) groups, {thermal_cap:,.0f} MW"
        )
        for path in ("measured", "class_fraction", "none"):
            g = aud[aud.path == path]
            if not len(g):
                continue
            print(
                f"  path={path:<14} {len(g):>4} groups  {g.cap_net_mw.sum():>9,.0f} MW"
                f"   pruned {int(g.pruned.sum()):>3}  live {int(g.live.sum()):>3}"
            )
        print(
            f"\nPRUNED as non-binding (RU>=cap AND RD>=cap): {len(pruned)} groups, "
            f"{pruned.cap_net_mw.sum():,.0f} MW"
        )
        if len(pruned):
            print("  by bucket: " + ", ".join(
                f"{b} {int(n)}" for b, n in pruned.groupby("bucket").size().items()
            ))
        print(
            f"NO ROW at all (CT without a measured trace — no class fallback): "
            f"{len(norow)} groups, {norow.cap_net_mw.sum():,.0f} MW"
        )

        # --- K7 -----------------------------------------------------------
        k7_thermal = live_cap / thermal_cap if thermal_cap else 0.0
        k7_all = live_cap / total_cap if total_cap else 0.0
        print(
            f"\n*** K7: LIVE envelope on {len(live)} groups = {live_cap:,.0f} MW "
            f"= {k7_thermal:.1%} of ramp-eligible thermal capacity "
            f"({k7_all:.1%} of all capacity) ***"
        )
        print(f"    K7 verdict: {'PASS' if k7_thermal >= 0.5 else 'FAIL'} (>= 50 % of thermal)")
        print("    live groups by bucket: " + ", ".join(
            f"{b} {int(n)} ({c:,.0f} MW)"
            for (b, n), c in zip(
                live.groupby("bucket").size().items(),
                live.groupby("bucket").cap_net_mw.sum().values,
            )
        ))

        # envelope tightness on the live groups
        live_frac_up = (live.ru_mw / live.cap_net_mw).astype(float)
        live_frac_dn = (live.rd_mw / live.cap_net_mw).astype(float)
        print(
            "    live up-envelope as frac of group pmax: "
            f"min {live_frac_up.min():.2f} / p25 {live_frac_up.quantile(.25):.2f} / "
            f"median {live_frac_up.median():.2f} / p75 {live_frac_up.quantile(.75):.2f} / "
            f"max {live_frac_up.max():.2f}"
        )
        print(
            "    live dn-envelope as frac of group pmax: "
            f"min {live_frac_dn.min():.2f} / median {live_frac_dn.median():.2f} / "
            f"max {live_frac_dn.max():.2f}"
        )

        # --- gross->net rebasis factors ----------------------------------
        mg = aud[aud.path == "measured"]
        nm = int((mg.factor_src == "measured").sum())
        nc = int((mg.factor_src == "class_default").sum())
        print(
            f"\n    gross->net rebasis on {len(mg)} measured groups: "
            f"{nm} measured per-plant factor(s), {nc} cited class default(s)"
        )
        if len(mg):
            f = mg.factor.astype(float)
            print(
                f"      factor min {f.min():.4f} / median {f.median():.4f} / "
                f"max {f.max():.4f}"
            )
            for src in ("measured", "class_default"):
                s = mg[mg.factor_src == src].factor.astype(float)
                if len(s):
                    print(
                        f"      {src:<14} n={len(s):>3} min {s.min():.4f} "
                        f"median {s.median():.4f} max {s.max():.4f}"
                    )

        # --- cross-check against the production loader --------------------
        got = build_ramp_groups(fa, args.iso)
        if got is None:
            print("\n    LOADER build_ramp_groups -> None  (NO ROWS WOULD BE BUILT)")
            n_loader_groups, n_loader_members = 0, 0
        else:
            gen_idx, group_col, ru, rd = got
            n_loader_groups, n_loader_members = int(ru.size), int(gen_idx.size)
            print(
                f"\n    LOADER build_ramp_groups -> {n_loader_groups} groups, "
                f"{n_loader_members} member columns  "
                f"(audit says {len(live)} live groups, {int(live.n_cols.sum())} members)"
                f"  {'MATCH' if n_loader_groups == len(live) else '*** MISMATCH ***'}"
            )
            # PREREG §7.1 sizes this as "2 x n_ramp_groups x (T-1) rows"; the
            # matrix ``_build_ramp_rows`` actually emits is
            # ``n_groups x (T-1)`` rows, each carrying BOTH a row_lower and a
            # row_upper (the two-sided form), so the PREREG's figure counts
            # bounds and this one counts rows. Both are reported.
            n_rows = n_loader_groups * (HOURS - 1)
            print(
                f"    LP row cost: {n_loader_groups} x (T-1) = {n_rows:,} rows, "
                f"each two-sided ({2 * n_rows:,} bounds); nnz = "
                f"2 x {n_loader_members} x (T-1) = "
                f"{2 * n_loader_members * (HOURS - 1):,}"
            )

        out["years"][str(year)] = {
            "n_gen_cols": int(len(pmax)),
            "total_cap_mw": total_cap,
            "ramp_eligible_cap_mw": thermal_cap,
            "n_groups_total": int(len(aud)),
            "n_groups_measured": int((aud.path == "measured").sum()),
            "n_groups_class_fraction": int((aud.path == "class_fraction").sum()),
            "n_groups_no_row": int(len(norow)),
            "n_groups_pruned": int(len(pruned)),
            "pruned_cap_mw": float(pruned.cap_net_mw.sum()),
            "no_row_cap_mw": float(norow.cap_net_mw.sum()),
            "n_groups_live": int(len(live)),
            "live_cap_mw": live_cap,
            "k7_live_share_of_thermal": k7_thermal,
            "k7_live_share_of_all": k7_all,
            "k7_pass": bool(k7_thermal >= 0.5),
            "live_by_bucket": {
                str(b): {
                    "n": int(g.shape[0]),
                    "cap_mw": float(g.cap_net_mw.sum()),
                    "up_frac_median": float((g.ru_mw / g.cap_net_mw).median()),
                    "dn_frac_median": float((g.rd_mw / g.cap_net_mw).median()),
                }
                for b, g in live.groupby("bucket")
            },
            "rebasis_measured_factor_groups": nm,
            "rebasis_class_default_groups": nc,
            "rebasis_factor_min": float(mg.factor.min()) if len(mg) else None,
            "rebasis_factor_median": float(mg.factor.median()) if len(mg) else None,
            "rebasis_factor_max": float(mg.factor.max()) if len(mg) else None,
            "loader_n_groups": n_loader_groups,
            "loader_n_members": n_loader_members,
            "loader_new_lp_rows": n_loader_groups * (HOURS - 1),
            "loader_new_lp_bounds": 2 * n_loader_groups * (HOURS - 1),
            "loader_new_lp_nnz": 2 * n_loader_members * (HOURS - 1),
        }

        csv = Path("results/probes") / f"pjm140_ramp_groups_{year}.csv"
        csv.parent.mkdir(parents=True, exist_ok=True)
        aud.sort_values(["bucket", "plant_code"]).to_csv(csv, index=False)
        print(f"    per-group audit -> {csv}")
        del state, fa

    dest = Path(args.json_out)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, indent=2))
    print(f"\nwrote {dest}")


if __name__ == "__main__":
    main()
