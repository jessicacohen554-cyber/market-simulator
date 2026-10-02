#!/usr/bin/env python3
"""Closeout MISO L3/L4 (ZERO LP): coal incremental-HR offers and the committed-band continuum.

Plan: ``docs/backcast-closeout-plan-2026-10.md`` §3.3 step 2; research shard
``docs/records/governance/closeout-2026-10/SHARD-MISO-closeout-research-2026-10-02.md``
§4 rows L3/L4 and §8 step 2. Evidence base: FINDING-miso296 (model low-load coal
marginal share 7 % vs IMM ~40 %; the coal offer curve has a hole between the ~$9
committed band and the ~$30 econ band) and FINDING-miso297 (a single coal econ
multiplier cannot be identified from the IMM census: shape, not level).

Nothing here feeds a solve (rule 13); no value is tuned against a residual
(rule 1); every input is a measurement already on disk.

1. **MISO incremental-HR ratio** (rule 25: MISO derives its own, same method as
   SOCO). ``scripts/data/derive_coal_incremental_hr_ratio.derive("MISO")`` is
   called unchanged (its CLI refuses MISO through ``ISO_SCOPE``; the function is
   the frozen construction) and written to ``--scratch`` (never ``data/``).
2. **Night p50** for every MISO coal plant: the ``derive_prb_committed_split``
   WP-3 construction verbatim (plant gross load summed over units, HSL = p99.5
   of pooled load, online = load >= max(10 MW, 2 % HSL), p50 of load/HSL over
   online h0-5, pooled 2023-2025), extended from PRB to all coal; plants with
   no 2023-2025 online night hours fall back to their pooled 2019-2025 hours.
   Reproduction of the registered PRB artifact is reported.
3. **Arms on the bid stack** at the keeper's own P1 thermal quantity (the
   miso-297 construction, keeper gas, ``clear_vec`` + the miso-287 markup):

   * ``KEEPER``  -- reproduces miso-297 ``coal_only|1.00`` (error reported).
   * ``L3``      -- coal econ tranches at the plant's measured INCREMENTAL HR,
     taken from a second fleet-only rebuild with the registered
     ``coal_econ_marginal_hr_two_sided`` mechanism armed on the MISO ratio
     (the ratio REPLACES the band multiplier, soco-81 / rule 19; scope =
     plants with a measured must-run floor, rule 18); committed unchanged.
   * ``L3flag``  -- the registered flag exactly (committed + econ).
   * ``L3stack`` -- econ fuel component x ratio with the band multiplier kept
     (the plan's "-5 to -15 %" reading), for the record.
   * ``L4a``     -- committed coal band split at the measured night p50
     (hold = min(committed, max(0, night_p50 x nameplate - mustrun)), the
     miso-112 formula); the hold slice keeps the keeper's committed offer; the
     cycling slice bids VOM + incremental HR x spot share x delivered fuel
     (spot share = 1 - EIA-923 Page 5 contract share; no measured share ->
     1.0). The keeper's take-or-pay discount is not applied to the slice
     (rule 19: the spot share IS the take-or-pay representation there).
   * ``L4b``     -- same split; the cycling slice bids VOM + incremental HR x
     full delivered fuel (the contract is sunk only up to its minimum, which
     mustrun + hold carry; the swing ton is bought at spot).
   * ``L3+L4a``, ``L3+L4b`` -- the combinations.

4. Per arm per year: coal marginal share (bid stack) all hours, q1-q4 and per
   load quintile (measured zonal demand) vs IMM SOM Table 1; static price change
   vs KEEPER at q1-q4 (load-weighted mean and median) and all hours; q1-q2
   error vs the zone-resolved RT actual; static coal dispatch change by
   subclass (TWh) and LP-converted at 0.27x (miso-224/225) against the
   keeper's C1 rows (``calibration_verdict.py --json``).
5. Plan gate (ex ante, plan §3.3 step 2): PASS iff the q1-q4 static price
   change <= -$1.0/MWh (load-weighted mean over q1-q4 hours) in 2020 AND
   COAL_PRB 2019/2021/2022 stay inside the C1 band after the LP-converted
   move. Applied to 2020 primarily, reported for every year.

Output: ``results/phase0/miso/_closeout_miso_l3l4_census.json``.

Usage (repo root)::

    .venv/bin/python scripts/probes/_closeout_miso_l3l4_census.py --scratch <dir>
"""

from __future__ import annotations

import argparse
import gc
import json
import re
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
for p in (str(REPO), str(REPO / "src"), str(REPO / "scripts"), str(REPO / "scripts/data")):
    if p not in sys.path:
        sys.path.insert(0, p)

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from scripts.probes import _miso271_cc_decomp as dec  # noqa: E402
from scripts.probes._miso296_lowload_stack import (  # noqa: E402
    COAL,
    IMM_SMP_SHARE,
    INTERNAL,
    KEEPER,
    NON_LP,
    T,
    YEARS,
    family,
    zone_actual,
)
from scripts.probes._miso297_joint_census import (  # noqa: E402
    clear_vec,
    markup_for,
    rebuild,
)

OUT = REPO / "results/phase0/miso/_closeout_miso_l3l4_census.json"
REF297 = REPO / "results/phase0/miso/_miso297_joint_census.json"
PRB_SPLIT = REPO / "data/raw/_processed-legacy/coal_prb_committed_split_MISO.csv"
#: LP conversion of a static coal move (miso-224/225, cited in FINDING-miso297 §1.5).
LP_CONVERSION = 0.27
#: Plan §3.3 step 2 gate, stated ex ante.
GATE_DPRICE = -1.0
GATE_PRB_YEARS = (2019, 2021, 2022)
NIGHT_POOL = (2023, 2024, 2025)  # derive_prb_committed_split.YEARS
ONLINE_MW, ONLINE_FRAC = 10.0, 0.02
ARMS = ("KEEPER", "L3", "L3flag", "L3stack", "L4a", "L4b", "L3+L4a", "L3+L4b")


def _r(x, k=3):
    """Round for the JSON record."""
    if x is None:
        return None
    x = float(x)
    return None if np.isnan(x) else round(x, k)


# --------------------------------------------------------------------------- 1
def derive_ratio(scratch: Path) -> pd.DataFrame:
    """MISO incremental/average ratio table (frozen SOCO construction) -> scratch CSV."""
    import derive_coal_incremental_hr_ratio as dci

    path = scratch / "coal_incremental_hr_ratio_MISO.csv"
    if path.exists():
        return pd.read_csv(path)
    tab = dci.derive("MISO")
    tab.to_csv(path, index=False)
    return tab


def ratio_map(tab: pd.DataFrame, year: int | None) -> dict[int, tuple[float, float]]:
    """``campd_bins.coal_incremental_hr_ratios`` year rule on the scratch table."""
    df = tab[tab["flag"].astype(str) == "ok"]
    out: dict[int, tuple[float, float]] = {}
    for yr in (0, year):
        if yr is None:
            continue
        for r in df[df["year"] == int(yr)].itertuples(index=False):
            lo, hi = float(r.ratio_econ_low), float(r.ratio_econ_high)
            if lo > 0.0 and hi > 0.0:
                out[int(r.plant_code)] = (lo, hi)
    return out


# --------------------------------------------------------------------------- 2
def night_p50_all_coal() -> tuple[dict[int, float], dict]:
    """WP-3 night p50 (pooled 2023-25, fallback 2019-25) for every MISO coal facility."""
    from derive_campd_marginal_hr import UNIT_LEVEL_DIR

    from market_sim.data.campd import states_for_iso

    tokens = ("coal", "bituminous", "lignite", "anthracite", "petroleum coke")
    frames = []
    for st in states_for_iso("MISO"):
        for y in YEARS:
            p = UNIT_LEVEL_DIR / f"{st}_{y}.parquet"
            if not p.exists():
                continue
            d = pd.read_parquet(
                p, columns=["facilityId", "date", "hour", "grossLoad", "primaryFuelInfo"]
            )
            d["facilityId"] = pd.to_numeric(d["facilityId"], errors="coerce")
            d = d.dropna(subset=["facilityId"])
            fuel = d["primaryFuelInfo"].astype(str).str.lower()
            is_coal = fuel.str.contains("|".join(tokens), regex=True)
            fac = set(d.loc[is_coal, "facilityId"].astype(int).unique())
            d = d[d["facilityId"].astype(int).isin(fac)]
            if d.empty:
                continue
            red = pd.DataFrame(
                {
                    "facilityId": d["facilityId"].astype(np.int32).to_numpy(),
                    "year": np.int16(y),
                    "doy": pd.to_datetime(d["date"]).dt.dayofyear.astype(np.int16).to_numpy(),
                    "hour": d["hour"].astype(np.int8).to_numpy(),
                    "grossLoad": d["grossLoad"].fillna(0.0).astype(np.float32).to_numpy(),
                }
            )
            del d
            frames.append(
                red.groupby(["facilityId", "year", "doy", "hour"], sort=False)["grossLoad"]
                .sum()
                .reset_index()
            )
    c = pd.concat(frames, ignore_index=True)
    ts = c.groupby(["facilityId", "year", "doy", "hour"], sort=False)["grossLoad"].sum()
    ts = ts.reset_index()
    del c, frames
    out: dict[int, float] = {}
    basis = {"pooled_2023_25": 0, "fallback_2019_25": 0, "none": 0}
    for fac, g in ts.groupby("facilityId"):
        val = None
        for pool, tag in ((NIGHT_POOL, "pooled_2023_25"), (YEARS, "fallback_2019_25")):
            gg = g[g["year"].isin(pool)]
            if gg.empty:
                continue
            load = gg["grossLoad"].to_numpy(float)
            hsl = float(np.percentile(load, 99.5))
            if hsl <= ONLINE_MW:
                continue
            on = load >= max(ONLINE_MW, ONLINE_FRAC * hsl)
            sel = on & gg["hour"].isin(range(6)).to_numpy()
            if not sel.any():
                continue
            val = float(np.percentile(load[sel] / hsl, 50))
            basis[tag] += 1
            break
        if val is None:
            basis["none"] += 1
            continue
        out[int(fac)] = val
    rep = {"n_facilities": len(out), "basis": basis}
    if PRB_SPLIT.exists():
        art = pd.read_csv(PRB_SPLIT)
        diffs = [
            abs(out[int(r.plant_code)] - float(r.night_p50))
            for r in art.itertuples(index=False)
            if int(r.plant_code) in out
        ]
        rep["prb_artifact_reproduction"] = {
            "n_artifact": int(len(art)),
            "n_matched": len(diffs),
            "max_abs_diff": _r(max(diffs) if diffs else np.nan, 4),
        }
    return out, rep


# --------------------------------------------------------------------------- C1
def keeper_c1() -> dict:
    """Keeper C1 coal rows (model - actual TWh, tolerance) from calibration_verdict --json."""
    res = subprocess.run(
        [sys.executable, str(REPO / "scripts/calibration_verdict.py"), str(KEEPER), "--json"],
        capture_output=True,
        text=True,
        cwd=REPO,
    )
    d = json.loads(res.stdout)
    out: dict = {}
    for r in d["criteria"]["fuelmix"]["records"]:
        if not str(r.get("key", "")).startswith("COAL"):
            continue
        if r.get("model") is None or r.get("actual") is None:
            continue
        m = re.search(r"=\s*±([0-9.]+)\s*TWh", r.get("tol") or "")
        out.setdefault(str(r["year"]), {})[r["key"]] = {
            "delta_twh": _r(r["model"] - r["actual"], 3),
            "tol_twh": float(m.group(1)) if m else 8.0,
            "status": r["status"],
        }
    return out


# --------------------------------------------------------------------------- arms
ST_KEEP = ("config", "fleet", "fleet_arrays", "demand", "solar_cap", "solar_cf", "wind_cap", "wind_cf")


def slim_two_sided(y, hh, ratios, b0):
    """Fleet-only rebuild with ``coal_econ_marginal_hr_two_sided`` on the MISO ratio.

    Only the coal rows are kept (memory bound): ``hr`` (n,), ``mc_coal``
    (n_coal, T), and the identity checks against the keeper rebuild ``b0``.
    The ratio loader is pointed at the scratch table in-process (the
    production applier is used unchanged; nothing in ``src/`` or ``data/`` is
    edited or written).
    """
    import gc

    import market_sim.data.fleet.assembly as asm
    from scripts.run_calibration import run_year  # type: ignore

    orig = asm.coal_incremental_hr_ratios
    asm.coal_incremental_hr_ratios = lambda iso, year=None, _m=ratios: _m
    try:
        st = run_year(
            y,
            "MISO",
            T,
            hh,
            {},
            fleet_only=True,
            **dec.recipe(y, {"coal_econ_marginal_hr_two_sided": True}),
        )
    finally:
        asm.coal_incremental_hr_ratios = orig
    fa = st["fleet_arrays"]
    n = len(fa.pmax)
    assert (np.asarray(list(fa.unit_ids)).astype(str) == np.asarray(list(b0["fa"].unit_ids)).astype(str)).all()
    mc = np.asarray(st["mc_base"], dtype=float).reshape(n, -1)
    coal_idx = np.nonzero(np.isin(b0["grp"], COAL))[0]
    moved = np.zeros(n, bool)
    for a in range(0, n, 256):
        bb = min(n, a + 256)
        m_ = mc[a:bb] if mc.shape[1] == T else np.repeat(mc[a:bb], T, axis=1)
        moved[a:bb] = np.abs(m_ - b0["mc"][a:bb]).max(axis=1) > 1e-9
    mc_coal = mc[coal_idx] if mc.shape[1] == T else np.repeat(mc[coal_idx], T, axis=1)
    out = {
        "hr": np.asarray(fa.heat_rate, float),
        "mc_coal": mc_coal.copy(),
        "coal_idx": coal_idx,
        "moved": moved,
        "pmax_identical": bool(np.allclose(np.asarray(fa.pmax, float), np.asarray(b0["fa"].pmax, float))),
    }
    del st, fa, mc, mc_coal
    gc.collect()
    return out


def build_arms(b0, b1, ratios, night, tor_share, reg_plants):
    """Return ``{arm: callable -> (mc, mg, flex, cap, extra_src)}`` plus diagnostics.

    ``extra_src`` maps each appended (cycling-slice) row to its parent row so a
    dispatch can be folded back to the original fleet for the markup. Arms are
    materialized one at a time (each full ``mc`` copy is ~0.2 GB).
    """
    n = b0["mc"].shape[0]
    cidx = b1["coal_idx"]
    pos = np.full(n, -1)
    pos[cidx] = np.arange(len(cidx))
    coal = np.isin(b0["grp"], COAL)
    econ = coal & (b0["fam"] == "econ")
    comm = coal & (b0["band"] == "committed")
    fp, hr0, hr1, vom = b0["fp"], b0["hr"], b1["hr"], b0["vom"]
    inscope = coal & (np.abs(hr1 - hr0) > 1e-9)
    mc0c = b0["mc"][cidx]
    mc1c = b1["mc_coal"]
    diag: dict = {}
    # econ rows pass full fuel (ff = 1, econ_srmc_bound), so there the move is
    # exactly d(hr) x fuel; committed rows carry the keeper's take-or-pay ff.
    ie = (inscope & econ)[cidx]
    dmc = (mc1c - mc0c)[ie]
    dfc = ((hr1 - hr0)[cidx, None] * fp[cidx])[ie]
    diag["two_sided_identity"] = {
        "rows_moved": int(b1["moved"].sum()),
        "rows_moved_outside_coal_committed_econ": int((b1["moved"] & ~(econ | comm)).sum()),
        "econ_mc_delta_eq_hr_delta_x_fuel_max_abs_err": _r(np.abs(dmc - dfc).max() if dmc.size else 0, 6),
        "pmax_identical": b1["pmax_identical"],
    }
    del dmc, dfc
    from market_sim.data.fleet.assembly import _incremental_econ_ratio

    plant = b0["plant"].astype(int)
    sel = econ & inscope
    # coal-subset variants
    l3c = mc0c.copy()
    l3c[sel[cidx]] = mc1c[sel[cidx]]
    stackc = mc0c.copy()
    econ_idx = np.nonzero(sel)[0]
    grp_key = pd.Series([f"{plant[i]}|{b0['grp'][i]}" for i in econ_idx], index=econ_idx)
    for _, rows in grp_key.groupby(grp_key):
        idx = sorted(rows.index, key=lambda i: b0["band"][i])
        nn = len(idx)
        lo, hi = ratios[int(plant[idx[0]])]
        for k, i in enumerate(idx):
            sfx = b0["band"][i]
            r = _incremental_econ_ratio(sfx if sfx in ("econlo", "econhi") else "econ", k, nn, lo, hi)
            stackc[pos[i]] = mc0c[pos[i]] - hr0[i] * fp[i] * (1.0 - r)
    # econ resid check (econ offer = hr x fuel + vom exactly)
    resid_e = (b0["mc"][econ] - hr0[econ, None] * fp[econ] - vom[econ, None])
    capm = b0["cap"].mean(axis=1)
    diag["econ_resid_max_abs"] = _r(np.abs(resid_e).max(), 6)
    del resid_e
    diag["l3_scope"] = {
        g: {
            "econ_cap_gw": _r(capm[econ & (b0["grp"] == g)].sum() / 1e3, 2),
            "in_scope_share": _r(
                capm[sel & (b0["grp"] == g)].sum() / max(capm[econ & (b0["grp"] == g)].sum(), 1e-9)
            ),
            "econ_offer_cap_wtd_keeper": _r(
                (b0["mc"][econ & (b0["grp"] == g)].mean(1) * capm[econ & (b0["grp"] == g)]).sum()
                / max(capm[econ & (b0["grp"] == g)].sum(), 1e-9),
                2,
            ),
            "econ_offer_cap_wtd_l3": _r(
                (l3c[(econ & (b0["grp"] == g))[cidx]].mean(1) * capm[econ & (b0["grp"] == g)]).sum()
                / max(capm[econ & (b0["grp"] == g)].sum(), 1e-9),
                2,
            ),
            "econ_offer_cap_wtd_l3stack": _r(
                (stackc[(econ & (b0["grp"] == g))[cidx]].mean(1) * capm[econ & (b0["grp"] == g)]).sum()
                / max(capm[econ & (b0["grp"] == g)].sum(), 1e-9),
                2,
            ),
        }
        for g in COAL
    }
    # committed resid check against the expected keeper fuel fraction
    ff_exp = np.ones(n)
    for i in np.nonzero(comm)[0]:
        s_ = tor_share.get(int(plant[i]))
        if int(plant[i]) in reg_plants and s_ is not None:
            ff_exp[i] = 1.0 - s_
    resid_c = b0["mc"][comm] - hr0[comm, None] * fp[comm] * ff_exp[comm, None] - vom[comm, None]
    diag["committed_resid_max_abs"] = _r(np.abs(resid_c).max(), 6)
    del resid_c
    # L4 split
    pmax = np.asarray(b0["fa"].pmax, float)
    grpk = np.array([f"{plant[i]}|{b0['grp'][i]}" for i in range(n)])
    split_rows, hold_frac = [], []
    nosplit = {"no_night_p50": 0.0, "night_covers_band": 0.0}
    whole = 0.0
    for i in np.nonzero(comm & (pmax > 0.5))[0]:
        same = coal & (grpk == grpk[i])
        nameplate = pmax[same].sum()
        mr = pmax[same & (b0["band"] == "mustrun")].sum()
        np50 = night.get(int(plant[i]))
        if np50 is None:
            nosplit["no_night_p50"] += pmax[i]
            continue
        hold = min(pmax[i], max(0.0, np50 * nameplate - mr))
        cyc = pmax[i] - hold
        if cyc <= 0.5:
            nosplit["night_covers_band"] += pmax[i]
            continue
        if hold <= 0.0:
            whole += pmax[i]  # night level below the mustrun band: whole band cycles
        split_rows.append(i)
        hold_frac.append(hold / pmax[i])
    split_rows = np.asarray(split_rows, int)
    h = np.asarray(hold_frac, float)
    spot = np.array(
        [
            1.0 - tor_share[int(plant[i])] if tor_share.get(int(plant[i])) is not None else 1.0
            for i in split_rows
        ]
    )
    inc_hr = np.where(inscope[split_rows], hr1[split_rows], hr0[split_rows])
    cyc_a = vom[split_rows, None] + (inc_hr * spot)[:, None] * fp[split_rows]
    cyc_b = vom[split_rows, None] + inc_hr[:, None] * fp[split_rows]
    comm_cap = pmax[comm].sum()
    w = pmax[split_rows] * (1 - h)
    diag["l4_split"] = {
        "committed_cap_gw": _r(comm_cap / 1e3, 2),
        "n_split": int(len(split_rows)),
        "cycling_cap_gw": _r(w.sum() / 1e3, 2),
        "hold_cap_gw": _r((pmax[split_rows] * h).sum() / 1e3, 2),
        "whole_band_cycles_cap_gw": _r(whole / 1e3, 2),
        "not_split_cap_gw": {k: _r(v / 1e3, 2) for k, v in nosplit.items()},
        "cycling_cap_share_of_committed": _r(w.sum() / comm_cap),
        "cycling_without_ratio_cap_gw": _r(w[~inscope[split_rows]].sum() / 1e3, 2),
        "cycling_without_contract_share_cap_gw": _r(
            w[[tor_share.get(int(plant[i])) is None for i in split_rows]].sum() / 1e3, 2
        ),
        "by_group": {},
    }
    for g in COAL:
        m = b0["grp"][split_rows] == g
        if not m.any():
            continue
        reg = np.array([int(plant[i]) in reg_plants for i in split_rows[m]])
        diag["l4_split"]["by_group"][g] = {
            "cycling_cap_gw": _r(w[m].sum() / 1e3, 2),
            "cycling_cap_gw_regulated": _r(w[m][reg].sum() / 1e3, 2),
            "keeper_committed_offer_cap_wtd": _r(
                (b0["mc"][split_rows[m]].mean(1) * w[m]).sum() / w[m].sum(), 2
            ),
            "l4a_cycling_offer_cap_wtd": _r((cyc_a[m].mean(1) * w[m]).sum() / w[m].sum(), 2),
            "l4b_cycling_offer_cap_wtd": _r((cyc_b[m].mean(1) * w[m]).sum() / w[m].sum(), 2),
            "spot_share_cap_wtd": _r((spot[m] * w[m]).sum() / w[m].sum()),
        }

    def full(variant):
        mc = b0["mc"].copy()
        if variant is not None:
            mc[cidx] = variant
        return mc

    def with_split(variant, cyc):
        mc = np.vstack([full(variant), cyc])
        cap = b0["cap"].copy()
        mg = b0["mg"].copy()
        cap_cyc = cap[split_rows] * (1 - h)[:, None]
        cap[split_rows] *= h[:, None]
        mg_hold = np.minimum(mg[split_rows], cap[split_rows])
        mg_cyc = np.minimum(mg[split_rows] - mg_hold, cap_cyc)
        mg[split_rows] = mg_hold
        cap = np.vstack([cap, cap_cyc])
        mg = np.vstack([mg, mg_cyc])
        return mc, mg, cap - mg, cap, split_rows

    plain = (b0["mg"], b0["flex"], b0["cap"], np.zeros(0, int))
    arms = {
        "KEEPER": lambda: (b0["mc"],) + plain,
        "L3": lambda: (full(l3c),) + plain,
        "L3flag": lambda: (full(mc1c),) + plain,
        "L3stack": lambda: (full(stackc),) + plain,
        "L4a": lambda: with_split(None, cyc_a),
        "L4b": lambda: with_split(None, cyc_b),
        "L3+L4a": lambda: with_split(l3c, cyc_a),
        "L3+L4b": lambda: with_split(l3c, cyc_b),
    }
    return arms, diag


# --------------------------------------------------------------------------- main
def main() -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--years", type=int, nargs="+", default=list(YEARS))
    ap.add_argument("--scratch", required=True, help="scratch dir for the ratio CSV")
    args = ap.parse_args()
    scratch = Path(args.scratch)
    scratch.mkdir(parents=True, exist_ok=True)
    from scripts.data import derive_actual_lmp as dal
    from scripts.run_calibration import _load_reference  # type: ignore
    from scripts.run_calibration_full import _henry_hub_actual  # type: ignore

    from market_sim.data.coal import coal_takeorpay_share
    from market_sim.data.fleet.eia860 import eia860_selfcommit_scope_plants

    t_all = time.time()
    dec.KEEPER = KEEPER
    out = json.loads(OUT.read_text()) if OUT.exists() else {}
    tab = derive_ratio(scratch)
    night, night_rep = night_p50_all_coal()
    c1 = keeper_c1()
    ref297 = json.loads(REF297.read_text()) if REF297.exists() else {}
    reg_plants = set(int(p) for p in eia860_selfcommit_scope_plants())
    pooled_tab = tab[(tab["year"] == 0) & (tab["flag"] == "ok")]
    out["_construction"] = {
        "ratio_source": "derive_coal_incremental_hr_ratio.derive('MISO') unchanged "
        "(frozen soco-81 construction), written to scratch, not data/",
        "ratio_scratch_csv": str(scratch / "coal_incremental_hr_ratio_MISO.csv"),
        "ratio_pooled_plants": int(len(pooled_tab)),
        "ratio_pooled_plain_stats": {
            k: {
                "mean": _r(pooled_tab[k].mean(), 4),
                "p10": _r(pooled_tab[k].quantile(0.1), 4),
                "p50": _r(pooled_tab[k].median(), 4),
                "p90": _r(pooled_tab[k].quantile(0.9), 4),
            }
            for k in ("ratio_econ_low", "ratio_econ_high")
        },
        "night_p50": night_rep,
        "lp_conversion": LP_CONVERSION,
        "gate": f"q1-q4 load-weighted static bid-stack price change <= {GATE_DPRICE} $/MWh "
        f"(2020 primary) AND keeper C1 COAL_PRB + {LP_CONVERSION} x static dCOAL_PRB "
        f"inside the band in {list(GATE_PRB_YEARS)}",
        "keeper_c1_coal": c1,
    }
    famv = np.vectorize(family)
    for y in args.years:
        t0 = time.time()
        yo: dict = {}
        hh = _henry_hub_actual(_load_reference(), y)
        b0 = rebuild(y, hh, {})
        for k_ in list(b0["st"].keys()):
            if k_ not in ST_KEEP:
                del b0["st"][k_]
        ratios = ratio_map(tab, y)
        b1 = slim_two_sided(y, hh, ratios, b0)
        plants = set(int(p) for p in b0["plant"][np.isin(b0["grp"], COAL)])
        tor = {p: coal_takeorpay_share(p) for p in plants}
        arms, diag = build_arms(b0, b1, ratios, night, tor, reg_plants)
        yo["construction"] = diag
        # ratio by subclass (fleet econ-cap weighted, in-scope rows)
        coal = np.isin(b0["grp"], COAL)
        capm = b0["cap"].mean(axis=1)
        plant = b0["plant"].astype(int)
        rs = {}
        for g in COAL:
            m = coal & (b0["grp"] == g) & (b0["fam"] == "econ")
            pl = pd.Series(capm[m]).groupby(plant[m]).sum()
            have = [p for p in pl.index if p in ratios]
            if not have:
                continue
            wv = pl[have].to_numpy()
            lo = np.array([ratios[p][0] for p in have])
            hi = np.array([ratios[p][1] for p in have])
            rs[g] = {
                "n_plants": len(have),
                "n_plants_no_ratio": int(len(pl) - len(have)),
                "cap_share_with_ratio": _r(wv.sum() / pl.sum()),
                "ratio_lo_cap_wtd": _r((lo * wv).sum() / wv.sum(), 4),
                "ratio_hi_cap_wtd": _r((hi * wv).sum() / wv.sum(), 4),
                "ratio_lo_p10_p90": [_r(np.percentile(lo, 10), 3), _r(np.percentile(lo, 90), 3)],
                "ratio_hi_p10_p90": [_r(np.percentile(hi, 10), 3), _r(np.percentile(hi, 90), 3)],
            }
        yo["ratio_by_subclass"] = rs
        # quantity, weights, quintiles, actual
        ch = pd.read_parquet(KEEPER / f"hourly/class_hourly_{y}.parquet")
        ch = ch[ch["pass"] == "P1"]
        chl = ch[~ch.klass.astype(str).isin(NON_LP)]
        q = chl.groupby("hour").mw.sum().reindex(range(T)).fillna(0).to_numpy()
        w = dal._measured_zone_demand("MISO", y)
        assert w is not None and w.shape == (6, T), w.shape
        load = w.sum(axis=0)
        q5 = pd.qcut(load, 5, labels=False)
        low = q5 <= 3
        pa = zone_actual(y)
        ok = ~np.isnan(pa).any(axis=0)
        lw_a = (pa * w).sum(0) / w.sum(0)
        wt = np.where(ok, load, 0.0)
        fam_base = famv(b0["lab"])
        res: dict = {}
        p_keep = d_keep = None
        for arm in ARMS:
            t_a = time.time()
            mc, mg, flex, cap, src = arms[arm]()
            fam_row = np.concatenate([fam_base, fam_base[src]])
            grp_row = np.concatenate([b0["grp"], b0["grp"][src]])
            band_row = np.concatenate([b0["fam"], np.full(len(src), "commitcyc")])
            p0, m0, d0 = clear_vec(mc, mg, flex, q)
            nbase = b0["mc"].shape[0]
            d0f = d0[:nbase].astype(float)
            if len(src):
                np.add.at(d0f, src, d0[nbase:])
            mk = markup_for(b0, d0f)
            if len(src):
                mk = np.vstack([mk, mk[src]])
            p1, m1, d1 = clear_vec(mc + mk, mg, flex, q)
            if arm == "KEEPER":
                p_keep, d_keep = p1, d1
            dp = p1 - p_keep

            def census(marg, mask, fr=fam_row):
                v = pd.Series(fr[marg[mask]]).value_counts(normalize=True)
                return {k: _r(x) for k, x in v.items()}

            twh = {}
            for g in COAL:
                rows = grp_row == g
                a = d1[rows].sum() / 1e6
                kk = d_keep[b0["grp"] == g].sum() / 1e6
                c1y = c1.get(str(y), {}).get(g)
                conv = LP_CONVERSION * (a - kk)
                twh[g] = {
                    "static_twh": _r(a, 2),
                    "static_delta_twh": _r(a - kk, 2),
                    "lp_converted_delta_twh": _r(conv, 2),
                    "keeper_c1_delta_twh": c1y["delta_twh"] if c1y else None,
                    "post_c1_delta_twh": _r(c1y["delta_twh"] + conv, 2) if c1y else None,
                    "tol_twh": c1y["tol_twh"] if c1y else None,
                    "in_band_lp_converted": bool(abs(c1y["delta_twh"] + conv) <= c1y["tol_twh"])
                    if c1y
                    else None,
                    "in_band_static_unconverted": bool(
                        abs(c1y["delta_twh"] + (a - kk)) <= c1y["tol_twh"]
                    )
                    if c1y
                    else None,
                }
            is_coal = fam_row[m1] == "coal"
            res[arm] = {
                "p0_all": census(m0, np.ones(T, bool)),
                "bid_all": census(m1, np.ones(T, bool)),
                "bid_q1_q4": census(m1, low),
                "bid_q": {f"q{i + 1}": census(m1, q5 == i) for i in range(5)},
                "bid_coal_band_q1_q4": {
                    k: _r(v)
                    for k, v in pd.Series(band_row[m1][is_coal & low])
                    .value_counts(normalize=True)
                    .items()
                },
                "price": {
                    "bid_q1_median": _r(np.median(p1[q5 == 0])),
                    "bid_q2_median": _r(np.median(p1[q5 == 1])),
                    "bid_lw_mean": _r((p1[ok] * wt[ok]).sum() / wt.sum()),
                    "dprice_q1_q4_lw_mean": _r((dp[low] * load[low]).sum() / load[low].sum()),
                    "dprice_q1_q4_median": _r(np.median(dp[low])),
                    "dprice_by_quintile_mean": {
                        f"q{i + 1}": _r(dp[q5 == i].mean()) for i in range(5)
                    },
                    "dprice_all_lw_mean": _r((dp * load).sum() / load.sum()),
                    "bid_minus_actual_q12_median": _r(np.median((p1 - lw_a)[(q5 <= 1) & ok])),
                    "bid_minus_actual_lw_mean_q12": _r(
                        ((p1 - lw_a)[(q5 <= 1) & ok] * wt[(q5 <= 1) & ok]).sum()
                        / wt[(q5 <= 1) & ok].sum()
                    ),
                    "bid_minus_actual_lw_mean": _r(((p1 - lw_a)[ok] * wt[ok]).sum() / wt.sum()),
                },
                "coal_twh": twh,
                "coal_gw_mean_q1_q4": _r(d1[fam_row == "coal"][:, low].sum(0).mean() / 1e3, 2),
            }
            res[arm]["gate_price_pass"] = bool(
                res[arm]["price"]["dprice_q1_q4_lw_mean"] <= GATE_DPRICE
            )
            print(
                y,
                arm,
                "coal all",
                res[arm]["bid_all"].get("coal"),
                "coal q1-4",
                res[arm]["bid_q1_q4"].get("coal"),
                "dP q1-4",
                res[arm]["price"]["dprice_q1_q4_lw_mean"],
                "dPRB",
                twh["COAL_PRB"]["static_delta_twh"],
                f"{time.time() - t_a:.0f}s",
                flush=True,
            )
            del mc, mg, flex, cap, d0, d1, mk, dp
            gc.collect()
        yo["arms"] = res
        yo["imm_smp_share"] = IMM_SMP_SHARE.get(y)
        yo["actual_q12_median"] = _r(np.median(lw_a[(q5 <= 1) & ok]))
        # reproduction vs miso-297 keeper (coal_only|1.00)
        r297 = ref297.get(str(y), {}).get("scan", {}).get("coal_only|1.00")
        if r297:
            k = res["KEEPER"]
            errs = {}
            for fam_ in ("coal", "gas", "seam"):
                errs[f"bid_all_{fam_}"] = abs(
                    (k["bid_all"].get(fam_) or 0) - (r297["bid_all"].get(fam_) or 0)
                )
                errs[f"bid_q1_{fam_}"] = abs(
                    (k["bid_q"]["q1"].get(fam_) or 0) - (r297["bid_q"]["q1"].get(fam_) or 0)
                )
            for pk in (
                "bid_q1_median",
                "bid_q2_median",
                "bid_lw_mean",
                "bid_minus_actual_q12_median",
            ):
                errs[pk] = abs(k["price"][pk] - r297["price"][pk])
            yo["reproduction_vs_miso297"] = {kk: _r(v, 4) for kk, v in errs.items()}
        del b0, b1, arms
        gc.collect()
        yo["elapsed_s"] = round(time.time() - t0, 1)
        out[str(y)] = yo
        OUT.write_text(json.dumps(out, indent=1))
    # gate table
    gate = {}
    for arm in ARMS:
        prb = {}
        for gy in GATE_PRB_YEARS:
            a = out.get(str(gy), {}).get("arms", {}).get(arm)
            prb[str(gy)] = a["coal_twh"]["COAL_PRB"]["post_c1_delta_twh"] if a else None
        prb_ok = all(
            out.get(str(gy), {}).get("arms", {}).get(arm, {}).get("coal_twh", {}).get(
                "COAL_PRB", {}
            ).get("in_band_lp_converted", False)
            for gy in GATE_PRB_YEARS
        )
        per_year = {
            str(yy): out[str(yy)]["arms"][arm]["price"]["dprice_q1_q4_lw_mean"]
            for yy in YEARS
            if str(yy) in out and "arms" in out[str(yy)]
        }
        p20 = per_year.get("2020")
        gate[arm] = {
            "dprice_q1_q4_lw_mean_by_year": per_year,
            "prb_post_c1_lp_converted": prb,
            "price_pass_2020": None if p20 is None else bool(p20 <= GATE_DPRICE),
            "prb_in_band_2019_2021_2022": bool(prb_ok),
            "PASS": bool(p20 is not None and p20 <= GATE_DPRICE and prb_ok),
        }
    out["_gate"] = gate
    out["_runtime_s"] = round(time.time() - t_all, 1)
    OUT.write_text(json.dumps(out, indent=1))
    print("GATE", json.dumps({a: g["PASS"] for a, g in gate.items()}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
