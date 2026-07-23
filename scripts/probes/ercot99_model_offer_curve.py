"""ERCOT-99 model offer-curve reconstruction: why the measured wall is never
marginal at the missed tail hours (charter steps 1-2, model side).

Captures the keeper's P1 offer curve WITHOUT an LP solve by monkeypatching
``run_energy_solve`` to intercept the fully-built fleet + ``mc_base`` +
``mc_bid_adjust`` (the summed offer-surface markups: conditional peak surface +
cleared-share wall + RT ladder + state weight) and aborting before the solve.
The P1 bid the LP clears on is ``mc_bid = mc_base + startup_markup + mc_bid_adjust``;
the startup amortization needs the P0 dispatch, so it is OMITTED here (it only
RAISES gas offers a few $/MWh, so the reconstructed curve is a slight LOWER bound
on the true bid — conservative for the "wall too cheap / stack too deep" thesis).

For each missed tail hour the probe sorts the fleet by offer, cumulates
deliverable MW (pmax x availability), finds the marginal offer at the model's
committed clearing MW (from the keeper sidecar's total dispatch), and reports the
depth of the sub-$200 stack, the MW the surface repriced, and the marginal
tranche class/position — the decisive test of DEPTH-miss (wall repriced but above
a deep cheap stack) vs BIN-miss (wall never repriced there).

Usage:
    python -m scripts.probes.ercot99_model_offer_curve --year 2023 \\
        [--bundle results/calibration/ercot98_np6_hsl_fullspan] \\
        [--dump scratch/ercot99_offer_2023.npz]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))

TAIL_THRESHOLD = 200.0


class _StopAfterCapture(BaseException):
    """Abort the run after the fleet build is captured (dodges except Exception)."""


def _capture_offer_curve(bundle: Path, year: int) -> dict:
    """Drive the keeper's fleet build for one year; capture the P1 offer inputs."""
    import replay_keeper  # noqa: E402  (adds scripts to path, pins warmstart)
    import run_calibration_full as rcf  # noqa: E402

    # Patch run_energy_solve in the EXACT module run_year is defined in — it is
    # imported as ``from scripts.run_calibration import run_year`` so its globals
    # live in ``scripts.run_calibration``, not the bare ``run_calibration`` alias.
    rc_mod = sys.modules[rcf.run_year.__module__]

    meta = json.loads((bundle / "meta.json").read_text())
    kwargs = replay_keeper.build_kwargs(meta)
    kwargs["years"] = [year]
    kwargs["iso"] = meta["iso"]
    kwargs["hours"] = int(meta.get("hours", 8760))
    kwargs["reference"] = rcf._load_reference()
    kwargs["run_dir"] = Path(REPO / "scratch" / "ercot99_capture_junk")
    kwargs["note"] = "ERCOT-99 offer-curve capture (aborts before solve)"

    grabbed: dict = {}
    real = rc_mod.run_energy_solve

    def _patched(fleet, fleet_arrays, demand, mc_base, dispatch_kwargs, config,
                 **kw):
        grabbed["fleet"] = fleet
        grabbed["fa"] = fleet_arrays
        grabbed["mc_base"] = np.asarray(mc_base)
        adj = kw.get("mc_bid_adjust")
        grabbed["mc_bid_adjust"] = None if adj is None else np.asarray(adj)
        grabbed["demand"] = np.asarray(demand)
        raise _StopAfterCapture()

    rc_mod.run_energy_solve = _patched
    print(f"[capture] patched {rc_mod.__name__}.run_energy_solve; "
          "driving fleet build (aborts at the solve)...", flush=True)
    try:
        rcf.solve_and_persist(**kwargs)
    except _StopAfterCapture:
        print("[capture] fleet build captured; solve aborted", flush=True)
    finally:
        rc_mod.run_energy_solve = real
    return grabbed


def _gen_meta(fleet, fa) -> pd.DataFrame:
    """Per-generator class / tranche / deliverable-cap metadata."""
    cls, uid, tr = [], [], []
    for gen in fleet:
        c = getattr(gen, "plant_group", None) or getattr(gen, "efficiency_bin", None)
        cls.append(c or "?")
        u = getattr(gen, "unit_id", "")
        uid.append(u)
        tr.append(u.rpartition("_")[2])
    return pd.DataFrame({"cls": cls, "uid": uid, "tranche": tr,
                         "pmax": np.asarray(fa.pmax, float)})


def _sidecar_clear(bundle: Path, year: int):
    """Model total dispatch (clearing MW) + demand-weighted hub price per hour."""
    s = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    p1 = s[s["pass"] == "P1"]
    price = p1.pivot(index="hour", columns="zone", values="price")
    demand = p1.pivot(index="hour", columns="zone", values="demand")
    hub = (price * demand).sum(axis=1) / demand.sum(axis=1)
    ch = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    ch = ch[ch["pass"] == "P1"]
    total = ch.groupby("hour")["mw"].sum()  # model total generation
    return hub.reindex(range(8760)).to_numpy(), total.reindex(range(8760)).to_numpy()


def _actual_rt(year: int) -> np.ndarray:
    lmp = pd.read_parquet(REPO / "data/raw/_validation-source/actual_lmp_hourly_ERCOT.parquet")
    return lmp[lmp["year"] == year].set_index("hour")["rt"].reindex(range(8760)).to_numpy()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="ercot99_model_offer_curve")
    ap.add_argument("--bundle", default="results/calibration/ercot98_np6_hsl_fullspan")
    ap.add_argument("--year", type=int, default=2023)
    ap.add_argument("--dump", default=None, help="optional npz cache of the capture")
    args = ap.parse_args(argv)
    bundle = REPO / args.bundle
    year = args.year

    grabbed = _capture_offer_curve(bundle, year)
    fleet, fa = grabbed["fleet"], grabbed["fa"]
    mc_base = grabbed["mc_base"]
    adj = grabbed["mc_bid_adjust"]
    if adj is None:
        adj = np.zeros_like(mc_base)
    mc_bid = mc_base + adj  # startup markup omitted (see docstring)
    avail = np.asarray(getattr(fa, "availability"), float)
    if avail.ndim == 1:
        avail = np.broadcast_to(avail[:, None], mc_bid.shape)
    meta = _gen_meta(fleet, fa)
    pmax = meta["pmax"].to_numpy()
    deliverable = pmax[:, None] * avail  # (n_gen, T)
    print(f"[capture] {len(fleet)} gens x {mc_bid.shape[1]} h | "
          f"surface reprices {(adj > 0).any(axis=1).sum()} gen-rows in >=1 h")

    hub, total = _sidecar_clear(bundle, year)
    rt = _actual_rt(year)
    tail = rt > TAIL_THRESHOLD
    missed = tail & (hub <= TAIL_THRESHOLD)
    midx = np.where(missed)[0]
    print(f"[set] tail {int(tail.sum())} | missed {int(missed.sum())}")

    if args.dump:
        Path(args.dump).parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(args.dump, mc_bid=mc_bid[:, midx], adj=adj[:, midx],
                            deliverable=deliverable[:, midx], pmax=pmax,
                            cls=meta["cls"].to_numpy(), tranche=meta["tranche"].to_numpy(),
                            midx=midx, hub=hub[midx], total=total[midx], rt=rt[midx])
        print(f"[dump] wrote {args.dump}")

    # Aggregate depth diagnostics over the missed hours.
    below200, clr_to_200, repriced_mw, marg_off, marg_cls = [], [], [], [], []
    for t in midx:
        off = mc_bid[:, t]
        cap = deliverable[:, t]
        order = np.argsort(off, kind="stable")
        off_s, cap_s = off[order], cap[order]
        cum = np.cumsum(cap_s)
        clr = total[t]  # model clearing MW at this hour
        k = int(np.searchsorted(cum, clr))
        k = min(k, len(off_s) - 1)
        marg_off.append(off_s[k])
        marg_cls.append(meta["cls"].to_numpy()[order][k])
        below200.append(cap_s[off_s < 200.0].sum())
        # MW between the marginal offer and $200 — the cushion that keeps the
        # wall from binding (must be crossed before price reaches $200).
        band = (off_s >= off_s[k]) & (off_s < 200.0)
        clr_to_200.append(cap_s[band].sum())
        repriced_mw.append(cap[adj[:, t] > 0].sum())

    below200 = np.array(below200); clr_to_200 = np.array(clr_to_200)
    repriced_mw = np.array(repriced_mw); marg_off = np.array(marg_off)
    print("\n[depth] over the missed hours (mean unless noted):")
    print(f"    model clearing MW (total gen)   : {np.mean(total[midx]):8.0f}")
    print(f"    reconstructed marginal offer    : ${np.mean(marg_off):7.1f} "
          f"(sidecar hub ${np.mean(hub[midx]):.1f} — cross-check)")
    print(f"    deliverable MW offered < $200   : {np.mean(below200):8.0f}")
    print(f"    cushion MW [marginal, $200)     : {np.mean(clr_to_200):8.0f} "
          f"<- must be crossed before price hits $200")
    print(f"    MW the surface repriced (>0)    : {np.mean(repriced_mw):8.0f}")
    marg_series = pd.Series(marg_cls)
    print(f"    marginal tranche class mix      : {marg_series.value_counts().to_dict()}")

    # Named early-August heat-wave hours (HE15-20 CST = idx hod 14-19).
    print("\n[detail] Aug heat-wave missed hours (date HEhh: model marg / hub / actual RT):")
    cal = pd.date_range(f"{year}-01-01", periods=8760, freq="h")
    for t in midx:
        d = cal[t]
        if d.month == 8 and 14 <= d.hour <= 19 and d.day in (4, 7, 8, 10, 11):
            off = mc_bid[:, t]; cap = deliverable[:, t]
            order = np.argsort(off, kind="stable")
            off_s, cap_s = off[order], cap[order]
            cum = np.cumsum(cap_s)
            k = min(int(np.searchsorted(cum, total[t])), len(off_s) - 1)
            b200 = cap_s[off_s < 200].sum()
            print(f"    {d.strftime('%m-%d')} HE{d.hour+1:02d}: marg ${off_s[k]:6.1f} "
                  f"[{meta['cls'].to_numpy()[order][k]:>10s}] hub ${hub[t]:6.1f} "
                  f"RT ${rt[t]:7.0f} | <$200 stack {b200:6.0f} MW / clr {total[t]:6.0f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
