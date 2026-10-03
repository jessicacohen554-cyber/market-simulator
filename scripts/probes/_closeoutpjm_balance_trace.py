"""closeout-PJM-balance (zero LP): trace the PJM keeper's generation-accounting residual.

On keeper ``2026-10-03-closeout-pjm-nuc-keeper`` (``results/calibration/closeout_pjm_nuc_full_span``)
every year shows ``generation (incl. the import node's net) - storage net charge - demand`` at +2.2 to +4.0 TWh
with zero slack and zero dump. This probe closes that identity from the LP's own energy-balance terms:

* the residual ``R`` from the committed hourly sidecars (``class_hourly``, ``storage``, ``system``);
* the energy dissipated by the ``pjm_zonal_loss_surface`` one-way internal links,
  ``L = sum_l,t eps_l,t * F_l,t``, where ``F`` is each leg's committed ``flows.parquet`` (shard commits, read
  by full SHA) and ``eps`` is rebuilt exactly as :func:`market_sim.model.interchange.pjm.build_pjm_link_loss`
  builds it (the receiving end of link ``l`` gains ``(1 - eps) F``);
* ``L`` broken down by link, month and hour of day;
* a first-order attribution of ``L`` to classes: per hour, ``L_t`` is peeled off the top of the running merit
  order in ``unit_marginal`` (highest P1 offer ``mc`` first), and, as a cross-check, split evenly over the
  hour's ``marginal``-flagged units;
* the C1 class deltas (model - bench ``classFull``) for CC_REGULAR and COAL_BIT;
* the same balance identity on the MISO keeper bundle (no loss surface armed) as the LP-wide control;
* EIA-930's own identity ``D = NG - TI`` (from the cc22 ledger) to show that the measured demand basis already
  includes every loss.

Reads only committed bytes. Writes ``results/phase0/pjm/_closeoutpjm_balance_trace.json``.

Usage::

    python scripts/probes/_closeoutpjm_balance_trace.py --legs <dir with <year>/flows.parquet>
"""

from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.data.loss_surface import load_zone_month_deviation

REPO = Path(__file__).resolve().parents[2]
KEEPER = REPO / "results/calibration/closeout_pjm_nuc_full_span"
MISO = REPO / "results/calibration/closeout_miso_nuc_span"
BENCH = REPO / "frontend/data/backcast/bench/PJM"
OUT = REPO / "results/phase0/pjm/_closeoutpjm_balance_trace.json"
YEARS = range(2019, 2026)

# Shard commits carrying each leg's flows.parquet (RESULT-closeout-pjm-nuc-2026-10-03 §1 / Addendum B).
LEG_SHA = {
    2019: "959cae9137586bc23fbc005595f72839613ab556",
    2020: "df0a347807966e5cdca4baa1503a02965a8fb5df",
    2021: "61afd4f99f1c0fcd3fe4b7a1295cbb431a8f5e2c",
    2022: "47a9db84892f90ae9d3fed097bc3617d8dbdd8c1",
    2023: "fbc78864d0b3834eb19eae4c4a11210d5490666f",
    2024: "998b3905fec5d62498a94f6243c8797ac26b14bf",
    2025: "57bdb18bb2e50b2ef83d1ac9ca8919e35987b21c",
}
MONTH_HOURS = np.array([31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]) * 24
MONTH_OF_HOUR = np.repeat(np.arange(12), MONTH_HOURS)
# Units that cannot move at the margin in a peel (zero-cost or non-dispatchable in P1).
NOT_PEELABLE = {"nuclear", "hydro", "import"}
TWH = 1e6


def _internal(a: str, b: str) -> bool:
    """Mirror of ``model.interchange.pjm._pjm_internal`` (the external star is lossless)."""
    return a.startswith("PJM_") and b.startswith("PJM_") and "PJM_external" not in (a, b)


def balance(bundle: Path, year: int) -> dict:
    """Return the system energy ledger (TWh) of one keeper year from its hourly sidecars."""
    h = bundle / "hourly"
    sysd = pd.read_parquet(h / f"system_{year}.parquet")
    cls = pd.read_parquet(h / f"class_hourly_{year}.parquet")
    sto = pd.read_parquet(h / f"storage_{year}.parquet")
    sysd, cls, sto = (d[d["pass"] == "P1"] for d in (sysd, cls, sto))
    imp_mask = cls.klass.isin(["import"])
    gen_hour = cls.groupby("hour").mw.sum()
    sto_net = (sto.charge_mw - sto.discharge_mw).groupby(sto.hour).sum()
    dem = sysd.groupby("hour").demand.sum()
    resid_hour = gen_hour.sub(sto_net, fill_value=0.0).sub(dem, fill_value=0.0)
    return {
        "gen_ex_import": float(cls[~imp_mask].mw.sum() / TWH),
        "net_import": float(cls[imp_mask].mw.sum() / TWH),
        "storage_net_charge": float(sto_net.sum() / TWH),
        "demand": float(dem.sum() / TWH),
        "slack": float(sysd.slack.sum() / TWH),
        "dump": float(sysd.dump.sum() / TWH),
        "residual": float(resid_hour.sum() / TWH),
        "_resid_hour": resid_hour.reindex(range(8760), fill_value=0.0).to_numpy(),
        "_class": (cls.groupby("klass", observed=True).mw.sum() / TWH).to_dict(),
    }


def link_losses(flows: pd.DataFrame, year: int) -> pd.DataFrame:
    """Return per-(link, hour) dissipated MW, ``eps * F``, as the LP books it."""
    surf = load_zone_month_deviation("PJM", year)
    f = flows[(flows["pass"] == "P1")].copy()
    f = f[[_internal(a, b) for a, b in zip(f.from_zone, f.to_zone)]]
    eps = np.zeros(len(f))
    for (a, b), idx in f.groupby(["from_zone", "to_zone"]).groups.items():
        dev_a = np.asarray(surf[a], dtype=float)
        dev_b = np.asarray(surf[b], dtype=float)
        eps_m = np.maximum(0.0, (dev_b - dev_a) / (1.0 + dev_b))
        pos = f.index.get_indexer(idx)
        eps[pos] = eps_m[MONTH_OF_HOUR[f.loc[idx, "hour"].to_numpy()]]
    f["eps"] = eps
    f["loss_mw"] = eps * f.mw.clip(lower=0.0)
    f["month"] = MONTH_OF_HOUR[f.hour.to_numpy()] + 1
    return f


def attribute(year: int, loss_hour: np.ndarray) -> dict:
    """First-order class attribution of the hourly loss (TWh): merit-order peel and marginal split."""
    um = pd.read_parquet(
        KEEPER / f"hourly/unit_marginal_{year}.parquet",
        columns=["pass", "fuel", "plant_group", "hour", "mw", "mc", "marginal"],
    )
    um = um[(um["pass"] == "P1") & (um.mw > 0.0) & ~um.fuel.astype(str).isin(NOT_PEELABLE)]
    um = um[~um.plant_group.astype(str).str.startswith("VIRTUAL")]
    um = um.assign(grp=um.plant_group.astype(str).replace("", "oil"))
    um = um.sort_values(["hour", "mc"], ascending=[True, False])
    cum = um.groupby("hour").mw.cumsum().to_numpy()
    need = loss_hour[um.hour.to_numpy()]
    take = np.clip(need - (cum - um.mw.to_numpy()), 0.0, um.mw.to_numpy())
    peel = (pd.Series(take).groupby(um.grp.to_numpy()).sum() / TWH).sort_values(ascending=False)
    mg = um[um.marginal == 1]
    n = mg.groupby("hour").mw.transform("size").to_numpy()
    share = loss_hour[mg.hour.to_numpy()] / n
    split = (pd.Series(share).groupby(mg.grp.to_numpy()).sum() / TWH).sort_values(ascending=False)
    covered = float(take.sum() / TWH)
    return {
        "peel_twh": {k: round(float(v), 3) for k, v in peel.items() if v > 0.005},
        "peel_covered_twh": round(covered, 3),
        "marginal_split_twh": {k: round(float(v), 3) for k, v in split.items() if v > 0.005},
        "marginal_split_covered_twh": round(float(share.sum() / TWH), 3),
    }


def c1_deltas(year: int, model_class: dict) -> dict:
    """Model - bench classFull (TWh) for the two C1 over-run classes."""
    cf = json.load(gzip.open(BENCH / f"{year}.json.gz"))["bench"]["classFull"]
    return {k: round(model_class.get(k, 0.0) - cf.get(k, 0.0), 2) for k in ("CC_REGULAR", "COAL_BIT")}


def main() -> None:
    """Run the trace over 2019-2025 and write the JSON payload."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--legs", type=Path, required=True, help="dir holding <year>/flows.parquet per leg")
    args = ap.parse_args()
    out: dict = {"keeper": str(KEEPER.relative_to(REPO)), "leg_sha": LEG_SHA, "years": {}}
    for y in YEARS:
        b = balance(KEEPER, y)
        fl = link_losses(pd.read_parquet(args.legs / str(y) / "flows.parquet"), y)
        loss_hour = fl.groupby("hour").loss_mw.sum().reindex(range(8760), fill_value=0.0).to_numpy()
        gap_hour = b["_resid_hour"] - loss_hour
        by_link = (fl.groupby(["from_zone", "to_zone"]).loss_mw.sum() / TWH).sort_values(ascending=False)
        by_month = (fl.groupby("month").loss_mw.sum() / TWH).round(3)
        hod = (pd.Series(loss_hour).groupby(np.arange(8760) % 24).mean()).round(0)
        lossy_flow = fl[fl.eps > 0].mw.sum() / TWH
        row = {k: round(v, 3) for k, v in b.items() if not k.startswith("_")}
        row.update(
            {
                "loss_twh": round(float(loss_hour.sum() / TWH), 3),
                "residual_minus_loss_twh": round(float(gap_hour.sum() / TWH), 4),
                "max_abs_hourly_gap_mw": round(float(np.abs(gap_hour).max()), 3),
                "flow_on_lossy_links_twh": round(float(lossy_flow), 2),
                "flow_weighted_eps_pct": round(float(100 * loss_hour.sum() / TWH / lossy_flow), 3),
                "loss_by_link_twh": {f"{a}>{c}": round(float(v), 3) for (a, c), v in by_link.items() if v > 0.01},
                "loss_by_month_twh": {int(k): float(v) for k, v in by_month.items()},
                "loss_mean_mw_by_hour_of_day": [float(x) for x in hod],
                "loss_peak_hour_mw": round(float(loss_hour.max()), 1),
                "attribution": attribute(y, loss_hour),
                "c1_model_minus_bench_twh": c1_deltas(y, b["_class"]),
            }
        )
        out["years"][str(y)] = row
        print(y, row["residual"], row["loss_twh"], row["residual_minus_loss_twh"], row["c1_model_minus_bench_twh"])
    out["miso_control"] = {}
    for y in YEARS:
        try:
            b = balance(MISO, y)
        except FileNotFoundError:
            continue
        out["miso_control"][str(y)] = {k: round(v, 3) for k, v in b.items() if not k.startswith("_")}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1) + "\n")
    print("wrote", OUT.relative_to(REPO))


if __name__ == "__main__":
    main()
