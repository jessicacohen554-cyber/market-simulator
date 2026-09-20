"""pjm-h13 card A PHASE 0 — is PJM's ST_GAS net-load drag an ALLOCATION defect?

ZERO LP (rule 29 ``[R-SCREEN]`` clause (0) survives as practice): every number
here comes from ``run_year(..., fleet_only=True)`` over the PJM keeper pair's
own committed recipes, plus the committed benchmark plant view. No solve.

THE QUESTION. On the PJM keeper's own committed ``legitimacy_diagnostics.json``
the ``st_netload_drag`` floor is carried by exactly FOUR plants of the 8.95 GW
ST_GAS population, and the two it convicts under D-4 (3131 Shawville, 3138 New
Castle) have a measured median of **0.000 MW** over the very hours the floor
asserts they must be online — while 3148 Martins Creek (1700 MW) and 3149
Montour (1504 MW), the population's two LARGEST plants, carry no drag floor at
all. That is the ercot-259 signature (``netload_drag_merit_allocation``,
FINDING-ercot259-c8-allocation-2026-09-08.md): a FLEET capacity factor spread
pro-rata across every non-peak tranche, asserting every plant is committed at
that fraction in every hour — a uniform answer to a lumpy question.

pjm-177 measured the same fact from the other side and recorded it without
taking it: *"the measured trough block has a persistent HETEROGENEOUS
membership ... while the drag commits EVERY plant at ~83 % duty in all hours
and ~0 % in the trough — a real second defect that is ercot-259's object,
recorded not taken."*

WHAT THIS PROBE DECIDES, before any shard is launched. The merit fill orders
commitment blocks (mustrun, then committed) by ascending bid heat rate. If
Martins Creek and Montour carry no COMMITMENT tranches, the swap cannot reach
them and would merely reshuffle the mandate among the same four plants — which
would make the arm a much weaker card than its ERCOT precedent. So the probe
reports, per plant and per year: the drag floor each leg places, the measured
median over that leg's own binding hours, and the D-4 verdict each leg would
earn. Nothing here is a gate; the gates are declared in the PRECOMMIT.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

CACHE = Path(
    "/tmp/claude-0/-home-user-market-simulator/"
    "8c35a33f-011c-5085-982d-a455875cf227/scratchpad/pjm_h13"
)

BUNDLES = {
    2020: "results/calibration/pjm_h11_touchpoint_span",
    2021: "results/calibration/pjm_h11_touchpoint_span",
    2022: "results/calibration/pjm_h11_touchpoint_span",
    2023: "results/calibration/pjm_h11_keeper_span",
    2024: "results/calibration/pjm_h11_keeper_span",
    2025: "results/calibration/pjm_h11_keeper_span",
}

ARM_FIELD = "netload_drag_merit_allocation"


def floors(year: int, arm: bool) -> dict:
    """Per-plant ST_GAS net-load-drag floor MW for one year and leg."""
    CACHE.mkdir(parents=True, exist_ok=True)
    tag = "arm" if arm else "ctl"
    path = CACHE / f"drag_{tag}_{year}.npz"
    if path.exists():
        z = np.load(path, allow_pickle=True)
        return {k: z[k] for k in z.files}

    from market_sim.data.floor_mechanisms import MECH_ST_NETLOAD_DRAG
    from scripts.replay_keeper import derived_run_year_inputs, run_year_kwargs
    from scripts.run_calibration import run_year

    bundle = REPO / BUNDLES[year]
    meta = json.loads((bundle / "meta.json").read_text())
    kw = run_year_kwargs(meta)
    kw.update(derived_run_year_inputs(bundle, year))
    if arm:
        ov = dict(kw.get("prb_overrides") or {})
        ov[ARM_FIELD] = True
        kw["prb_overrides"] = ov
    gas = float(meta["gas_prices"][str(year)])
    payload = run_year(year, meta["iso"], 8760, gas, {}, fleet_only=True, **kw)

    fa = payload["fleet_arrays"]
    fleet = payload["fleet"]
    min_gen = np.asarray(fa.min_gen, dtype=float)
    mech = np.asarray(fa.min_gen_mechanism)
    plant = np.array(
        [int(getattr(u, "plant_code", 0) or 0) for u in fleet], dtype=int
    )
    group = np.array(
        [str(getattr(u, "plant_group", "") or "") for u in fleet], dtype=object
    )
    st = group == "ST_GAS"
    codes = sorted({int(c) for c in plant[st] if c})
    n_h = min_gen.shape[1]
    floor_mw = np.zeros((len(codes), n_h), dtype=np.float32)
    for i, c in enumerate(codes):
        rows = np.flatnonzero(st & (plant == c))
        sel = mech[rows] == MECH_ST_NETLOAD_DRAG
        floor_mw[i] = np.where(sel, min_gen[rows], 0.0).sum(axis=0)
    out = {
        "year": np.array(year),
        "codes": np.asarray(codes, dtype=int),
        "floor_mw": floor_mw,
    }
    np.savez_compressed(path, **out)
    return out


def main() -> None:
    from scripts.legitimacy_diagnostics import bench_plant_view, load_bench

    years = [int(a) for a in sys.argv[1:]] or [2023, 2024, 2025]
    for year in years:
        ctl = floors(year, arm=False)
        arm = floors(year, arm=True)
        codes = [int(c) for c in ctl["codes"]]
        assert codes == [int(c) for c in arm["codes"]]
        bench = bench_plant_view(load_bench(REPO, "PJM", year))

        print("=" * 112)
        print(
            f"{year}   st_netload_drag per-plant allocation   "
            f"control  vs  {ARM_FIELD}=True   (ZERO LP)"
        )
        print("=" * 112)
        print(
            f"{'plant':>7} {'ctlTWh':>9} {'armTWh':>9} {'dTWh':>9} "
            f"{'ctl_h':>7} {'arm_h':>7} {'ctlMed':>8} {'armMed':>8} "
            f"{'ctl':>5} {'arm':>5}"
        )
        tot_c = tot_a = 0.0
        for i, c in enumerate(codes):
            fc = ctl["floor_mw"][i].astype(float)
            fa_ = arm["floor_mw"][i].astype(float)
            twh_c, twh_a = fc.sum() / 1e6, fa_.sum() / 1e6
            tot_c += twh_c
            tot_a += twh_a
            if twh_c <= 0 and twh_a <= 0:
                continue
            b = bench.get(str(c))
            meas = (
                np.asarray(b["mw"], dtype=float) if b and not b.get("ct_only") else None
            )

            def verdict(f: np.ndarray) -> tuple[int, str, str]:
                h = f > 0.0
                if not h.any():
                    return 0, "     -", "    -"
                if meas is None or meas.size < h.size:
                    return int(h.sum()), "     -", " skip"
                m = float(np.median(meas[: h.size][h]))
                return int(h.sum()), f"{m:8.3f}", ("  FAIL" if m <= 0.0 else "  pass")

            hc, mc, vc = verdict(fc)
            ha, ma, va = verdict(fa_)
            print(
                f"{c:>7} {twh_c:9.4f} {twh_a:9.4f} {twh_a - twh_c:+9.4f} "
                f"{hc:>7} {ha:>7} {mc} {ma} {vc:>5} {va:>5}"
            )
        print(
            f"{'TOTAL':>7} {tot_c:9.4f} {tot_a:9.4f} {tot_a - tot_c:+9.4f}"
            f"    (aggregate-neutrality check)"
        )
        print()


if __name__ == "__main__":
    main()
