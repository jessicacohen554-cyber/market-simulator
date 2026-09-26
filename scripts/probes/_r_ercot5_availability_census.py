"""R-ERCOT-5 zero-LP probe: is any ERCOT availability layer capping a plant below its
own same-hour measured output?

R-ERCOT-4 found the day-shaped CAMPD partial-outage layer capping cycling coal plants
on days their own CEMS shows full load. This probe runs the same "capped below own
measured output" census over the WHOLE finished availability stack, and attributes
every violating plant-hour to the stage that put the cap there.

For each year it rebuilds the keeper recipe's LP fleet with ``run_year(fleet_only=True)``
(``_r_ercot3_coal_census.build``, repointed at the current keeper bundle), instrumented
with three snapshots of the per-tranche availability matrix:

* ``pre``   — after the statistical stack, the CAMPD >=5-day unit windows, the <5-day
              short windows, the CAMPD-blind series and the (shaped, day-guarded) partial
              plateaus; immediately before the ERCOT DAM COP plant-grain pin;
* ``dam``   — after the DAM plant pin and the class-hour water-fill;
* ``final`` — ``fleet_arrays.availability`` (after the measured-event precedence cap).

It also records the three CAMPD layer factors the event cap composes (``W`` >=5-day
windows, ``S`` short windows, ``P`` partial plateaus) and the DAM plant series.

Per (plant, class) the model's available MW is ``sum(pmax * availability)`` over the
plant's tranches; the measured output is CAMPD gross x (1 - class parasitic default),
on the model's hour clock (``campd.plant_hourly_net``). A plant-hour VIOLATES when
``measured_net > final_avail_MW + tol`` with ``tol = max(25 MW, 3 % of plant pmax)``.
Each violation is attributed to the FIRST stage at which availability fell below the
measured output: ``stack`` (already below before the DAM pin; sub-attributed to W / S /
P when that layer's own ceiling alone is below it, else ``stat`` — statistical / base
availability), ``dam_remove`` (the DAM pin took it below), or ``event_cap`` (the
precedence cap took it below; sub-attributed to W / S / P).

Usage::

    PYTHONPATH=.:src:scripts python3 scripts/probes/_r_ercot5_availability_census.py \
        --years 2019 --out <json> [--hours-file <npy of scarcity hour indices>]

Record: ``docs/handoffs/FINDING-r-ercot-5-2019-scarcity-2026-09-25.md``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
for p in (REPO, REPO / "src", REPO / "scripts"):
    sys.path.insert(0, str(p))

import scripts.probes._r_ercot3_coal_census as C  # noqa: E402

# R-ERCOT-6: the current keeper (2026-09-25-r-5-hour-grain); ``--bundle`` overrides.
C.BUNDLE = REPO / "results/calibration/r_ercot5_hourgrain_span"
CLASSES = ("COAL", "CC_REGULAR", "ST_GAS")


def _instrument():
    """Patch the fleet builder so each build records its availability stages."""
    import market_sim.data.fleet.arrays as A
    import market_sim.data.outages as O

    rec: dict = {}
    orig_pin = A._ercot_dam_plant_hourly_apply

    def pin(availability, generators, *a, **k):
        rec["pre"] = availability.copy()
        rec["gen_codes"] = [int(g.plant_code) for g in generators]
        out = orig_pin(availability, generators, *a, **k)
        return out

    A._ercot_dam_plant_hourly_apply = pin
    for name in (
        "unit_outage_derate_factors",
        "unit_outage_short_derate_factors",
        "partial_outage_derate_factors",
    ):
        f = getattr(A, name)

        def wrap(*a, _f=f, _n=name, **k):
            r = _f(*a, **k)
            rec.setdefault(_n, []).append(r)
            return r

        setattr(A, name, wrap)
    orig_ps = O.ercot_thermal_dam_availability_plant_series

    def ps(*a, **k):
        r = orig_ps(*a, **k)
        rec["dam_plant"] = r
        return r

    O.ercot_thermal_dam_availability_plant_series = ps
    # The class-hour water-fill runs after the plant pin; the event cap after that.
    # Snapshot "dam" = the matrix the event cap starts from: re-wrap np.minimum is
    # too broad, so reconstruct it as max(final, pre-cap) is not identifiable —
    # instead capture it from the event-cap layer call order (the partial-factor
    # call inside the cap block happens after the DAM block has finished).
    orig_pf = A.partial_outage_derate_factors

    def pf(*a, **k):
        if (
            "gen_codes" in rec
            and "dam" not in rec
            and rec.get("_avail_ref") is not None
        ):
            rec["dam"] = rec["_avail_ref"].copy()
        return orig_pf(*a, **k)

    A.partial_outage_derate_factors = pf
    return rec


def measured_net(year: int, H: int, keys) -> dict:
    """Per model (plant_code, class) CEMS NET MW on the model clock, at UNIT grain.

    A CAMPD facility can hold units of several model bins (W A Parish's gas-steam
    WAP1-4 are model code 34702; Barney M Davis unit 1 is 49392), so each unit is
    routed to a bin by its own fuel / unit type, never by facility: coal-fired units
    -> (facility, COAL); combined-cycle units -> (facility, CC_REGULAR); other
    gas boilers -> (facility, ST_GAS), with the two split plants re-coded; CTs
    dropped (peakers are not in the census). Gross -> net by the class parasitic
    default (``campd.DEFAULT_PARASITIC_LOAD_PCT``).
    """
    import pandas as pd
    from market_sim.data.campd import DEFAULT_PARASITIC_LOAD_PCT, _hour_index_8760

    d = pd.read_parquet(
        REPO / f"data/raw/campd-unit-level/TX_{year}.parquet",
        columns=[
            "facilityId",
            "unitId",
            "date",
            "hour",
            "grossLoad",
            "primaryFuelInfo",
            "unitType",
        ],
    )
    d = d[d["grossLoad"].fillna(0) > 0]
    fac = d["facilityId"].astype(int).to_numpy()
    fuel = d["primaryFuelInfo"].astype(str).str.lower()
    ut = d["unitType"].astype(str).str.lower()
    cls = np.where(
        fuel.str.contains("coal|lignite").to_numpy(),
        "COAL",
        np.where(
            ut.str.startswith("combined cycle").to_numpy(),
            "CC_REGULAR",
            np.where(
                ut.str.startswith("combustion turbine").to_numpy(), "CT", "ST_GAS"
            ),
        ),
    )
    code = fac.copy()
    code[(fac == 3470) & (cls != "COAL")] = 34702
    uid = d["unitId"].astype(str).to_numpy()
    b1 = (fac == 4939) & (uid == "1")
    code[b1] = 49392
    cls = np.where(b1, "ST_GAS", cls)
    hoy = _hour_index_8760(
        d["date"].dt.month.to_numpy(), d["date"].dt.day.to_numpy(), d["hour"].to_numpy()
    )
    g = d["grossLoad"].to_numpy(float)
    want = {(int(c), k) for c, k in keys}
    out = {}
    for c, k in want:
        kk = "COAL" if k == "COAL" else k
        m = (code == c) & (hoy >= 0) & (hoy < H)
        # a model bin whose class the unit typing never produces (e.g. a CC_REGULAR
        # bin at a facility CAMPD types as boilers): fall back to every non-CT,
        # non-coal unit of the facility, pro rata handled by the caller.
        mk = m & (cls == kk)
        if not mk.any() and kk != "COAL":
            mk = m & (cls != "COAL") & (cls != "CT")
        if not mk.any():
            continue
        s = np.zeros(H)
        np.add.at(s, hoy[mk], g[mk])
        out[(c, k)] = s * (1.0 - DEFAULT_PARASITIC_LOAD_PCT.get(k, 0.03))
    return out


def _fam(g: str) -> str:
    return "COAL" if g.startswith("COAL") else g


def _build(year: int, overlay: dict | None):
    """``_r_ercot3_coal_census.build`` plus an optional config overlay (``--set``)."""
    if not overlay:
        return C.build(year)
    import replay_keeper as R

    orig = R.config_partition_overlay

    def ov(meta, y):
        return dict(orig(meta, y) or {}, **overlay)

    R.config_partition_overlay = ov
    try:
        return C.build(year)
    finally:
        R.config_partition_overlay = orig


def _hour_grain_active_units(year, hours=8760, iso="ERCOT"):
    """``unit_outage_active_units`` read at the window factor's HOUR grain.

    R-ERCOT-6: the incumbent helper reads ``unit_outage_csv_for_iso(iso)`` with
    no ``hour_grain``, so under the R-ERCOT-5 keeper the unit-scoped shared-unit
    mask is day-grain while the window factor it composes with is hour-grain.
    This is the aligned mask, for the zero-LP comparison only.
    """
    import market_sim.data.outages as O

    df = O._load_unit_outage_events(
        O.unit_outage_csv_for_iso(iso, hour_grain=True), iso
    )
    if df is None:
        return {}
    df = df[df["duration_days"] >= O.UNIT_OUTAGE_MIN_DAYS]
    has_hours = O._has_hour_grain(df)
    out: dict = {}
    for r in df.itertuples(index=False):
        uid = str(r.unit_id).strip()
        tgt = O._unit_outage_target(int(r.facility_id), uid, r.plant_group)
        if tgt is None or not uid:
            continue
        w0, w1 = O.unit_outage_event_window(r, has_hours)
        mask = O.outage_hour_mask(w0, w1, year, hours)
        if not mask.any():
            continue
        arr = out.setdefault(tgt, {}).setdefault(uid, np.zeros(hours, dtype=bool))
        arr |= mask
    return out


def _apply_variant(variant: str) -> None:
    """Patch the unit-scoped seam for a zero-LP variant (``--variant``).

    ``hgmask``: the shared-unit mask at the window factor's hour grain.
    ``finer``:  ``hgmask`` plus FINER-GRAIN-WINS — at a shared-unit hour the
                unit-exact window ceiling alone stands (the plant-aggregate
                partial plateau is dropped there), instead of ``min(W, P)``.
                Implemented by returning the class-grain plateau as 1.0 at the
                bin's shared hours, so the cap's ``min(ceil_w, 1)`` is ``ceil_w``.
    """
    if variant == "none":
        return
    import market_sim.data.fleet.arrays as A
    import market_sim.data.outages as O

    if variant == "resid":
        # R-ERCOT-7 sensitivity (probe only, with --set
        # ercot_dam_availability_event_cap_per_unit=true): RESIDUAL-PRESERVING
        # per-unit composition. Instead of apportioning the plateau's removed
        # share by the carrying units' deficits (which drops plateau depth no
        # carrying unit explains together with the windowed unit), subtract
        # only the windowed carrying units' own measured deficit MW, on the
        # window accumulator's own bin-capacity denominator:
        #   f_p* = 1 - max(0, (1 - f_p) - sum_{u windowed} d_u / cap_bin)
        from market_sim.config.paths import CAMPD_BINS_CSV
        from market_sim.config.plant_taxonomy import artifact_class
        from market_sim.data.fleet import load_campd_bins

        b = load_campd_bins(str(CAMPD_BINS_CSV))
        cap = {
            (int(c), artifact_class(g)): float(m)
            for c, g, m in zip(b["Plant_Code"], b["Plant_Group"], b["capacity_mw"])
            if m and m > 0
        }
        orig_def = O.partial_outage_unit_deficits

        def deficits(year, hours=8760, iso="ERCOT"):
            out = {}
            for k, d in orig_def(year, hours, iso).items():
                if k in cap:
                    out[k] = {u: a / cap[k] for u, a in d.items()}
            return out

        def factor(fp, unit_def, win):
            fp = np.asarray(fp, float)
            if not unit_def or not win:
                return fp
            w = {O._norm_partial_unit_id(u): m for u, m in win.items()}
            n = fp.size
            sub = np.zeros(n)
            for u, d in unit_def.items():
                m = w.get(O._norm_partial_unit_id(u))
                if m is not None:
                    sub += np.where(m[:n], np.asarray(d, float)[:n], 0.0)
            if not sub.any():
                return fp
            return 1.0 - np.maximum((1.0 - fp) - sub, 0.0)

        A.partial_outage_unit_deficits = deficits
        A.per_unit_partial_factor = factor
        return

    A.unit_outage_active_units = _hour_grain_active_units
    if variant != "finer":
        return
    orig = A.partial_outage_derate_factors

    def pf(year, hours=8760, *a, class_grain=False, **k):
        r = orig(year, hours, *a, class_grain=class_grain, **k)
        if not class_grain:
            return r
        wu = _hour_grain_active_units(int(year), hours)
        pu = O.partial_outage_active_units(int(year), hours, iso="ERCOT")
        out = {}
        for key, f in r.items():
            f = np.asarray(f, float)
            sh = O.shared_unit_hours(wu.get(key), pu.get(key), hours)[: f.size]
            out[key] = np.where(sh, 1.0, f)
        return out

    A.partial_outage_derate_factors = pf


def build_stages(
    year: int, cache: Path, overlay: dict | None = None, variant: str = "none"
) -> dict:
    """Instrumented fleet-only build; returns (and caches as .npz) the stage arrays."""
    if cache.exists():
        z = np.load(cache, allow_pickle=True)
        return {k: z[k] for k in z.files}
    import market_sim.data.fleet.arrays as A

    _apply_variant(variant)
    rec = _instrument()
    # capture the live availability array object: the DAM pin receives it by reference
    orig_pin = A._ercot_dam_plant_hourly_apply

    def pin2(availability, *a, **k):
        rec["_avail_ref"] = availability
        rec.pop("dam", None)
        return orig_pin(availability, *a, **k)

    A._ercot_dam_plant_hourly_apply = pin2
    st, _ = _build(year, overlay)
    fa = st["fleet_arrays"]
    fin = np.asarray(fa.availability, float)
    pre, dam = rec.get("pre"), rec.get("dam")
    assert pre is not None and dam is not None, "instrumentation missed a stage"
    assert pre.shape == fin.shape == dam.shape, (pre.shape, fin.shape)
    H = fin.shape[1]
    grp = np.array([_fam(str(g)) for g in fa.plant_group])
    codes = np.asarray(fa.plant_code).astype(int)
    keys = sorted({(int(c), g) for c, g in zip(codes, grp) if g in CLASSES})
    W = rec["unit_outage_derate_factors"][-1]
    S = (rec.get("unit_outage_short_derate_factors") or [{}])[-1]
    P = rec["partial_outage_derate_factors"][-1]
    dp = rec.get("dam_plant") or {}
    one = np.ones(H)
    lay = {}
    for c, g in keys:
        lay[f"W_{c}_{g}"] = np.asarray(W.get((c, g), one), float)[:H]
        lay[f"S_{c}_{g}"] = np.asarray(S.get((c, g), one), float)[:H]
        lay[f"P_{c}_{g}"] = np.asarray(P.get((c, g), P.get(c, one)), float)[:H]
        if c in dp:
            lay[f"D_{c}"] = np.asarray(dp[c], float)[:H]
    sel = np.isin(grp, CLASSES)
    out = dict(
        all_codes=codes,
        all_grp=np.array([str(g) for g in fa.plant_group]),
        all_pmax=np.asarray(fa.pmax, float),
        all_avail_mean=fin.mean(1),
        pre=pre[sel],
        dam=dam[sel],
        fin=fin[sel],
        pmax=np.asarray(fa.pmax, float)[sel],
        grp=grp[sel],
        codes=codes[sel],
        mc=np.asarray(st["mc_base"], float)[sel].mean(1)
        if np.ndim(st["mc_base"]) == 2
        else np.asarray(st["mc_base"], float)[sel],
        mg=np.asarray(fa.min_gen, float)[sel]
        if np.ndim(fa.min_gen) == 2
        else np.repeat(np.asarray(fa.min_gen, float)[sel][:, None], H, 1),
        **lay,
    )
    np.savez_compressed(cache, **out)
    return out


def census(year: int, stages: dict, hours_subset: np.ndarray | None = None) -> dict:
    """Per-plant-hour census of final availability vs same-hour CEMS net output."""
    pre, dam, fin = stages["pre"], stages["dam"], stages["fin"]
    pmax, grp, codes = stages["pmax"], stages["grp"], stages["codes"]
    H = fin.shape[1]
    keys = sorted({(int(c), str(g)) for c, g in zip(codes, grp)})
    one = np.ones(H)
    net = measured_net(year, H, keys)
    hmask = np.zeros(H, bool)
    if hours_subset is None:
        hmask[:] = True
    else:
        hmask[hours_subset] = True
    out_rows = []
    tot = {}
    for c, g in keys:
        m = (codes == c) & (grp == g)
        pm = float(pmax[m].sum())
        if pm <= 0 or (c, g) not in net:
            continue
        meas = net[(c, g)][:H]
        f_mw = (pmax[m, None] * fin[m]).sum(0)
        d_mw = (pmax[m, None] * dam[m]).sum(0)
        p_mw = (pmax[m, None] * pre[m]).sum(0)
        tol = max(25.0, 0.03 * pm)
        v = hmask & (meas > f_mw + tol)
        if not v.any():
            continue
        cat = np.where(
            meas > p_mw + tol,
            "stack",
            np.where(meas > d_mw + tol, "dam_remove", "event_cap"),
        )
        lw = stages.get(f"W_{c}_{g}", one) * pm
        ls = stages.get(f"S_{c}_{g}", one) * pm
        pp = stages.get(f"P_{c}_{g}", one) * pm
        dp = stages.get(f"D_{c}")
        sub = np.where(
            meas > lw + tol,
            "W",
            np.where(meas > ls + tol, "S", np.where(meas > pp + tol, "P", "")),
        )
        for h in np.where(v)[0]:
            lab = cat[h]
            if lab in ("stack", "event_cap"):
                lab = lab + (
                    ":" + sub[h]
                    if sub[h]
                    else (":stat" if lab == "stack" else ":product")
                )
            gap = float(meas[h] - f_mw[h])
            t = tot.setdefault(g, {}).setdefault(lab, [0, 0.0, set()])
            t[0] += 1
            t[1] += gap
            t[2].add(h // 24)
            out_rows.append(
                {
                    "code": int(c),
                    "cls": g,
                    "hour": int(h),
                    "meas_net": round(float(meas[h]), 1),
                    "final_mw": round(float(f_mw[h]), 1),
                    "dam_mw": round(float(d_mw[h]), 1),
                    "pre_mw": round(float(p_mw[h]), 1),
                    "pmax": round(pm, 1),
                    "W": round(float(lw[h]), 1),
                    "S": round(float(ls[h]), 1),
                    "P": round(float(pp[h]), 1),
                    "dam_frac": None
                    if dp is None or not np.isfinite(dp[h])
                    else round(float(dp[h]), 3),
                    "stage": lab,
                }
            )
    summ = {
        g: {
            k: {"plant_hours": v[0], "MWh_gap": round(v[1]), "plant_days": len(v[2])}
            for k, v in d.items()
        }
        for g, d in tot.items()
    }
    return {"summary": summ, "rows": out_rows}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", nargs="+", type=int, required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--hours-file", default=None)
    ap.add_argument("--cache-dir", default=".")
    ap.add_argument(
        "--set", action="append", default=[], help="KEY=JSON config overlay"
    )
    ap.add_argument("--bundle", default=None, help="keeper bundle dir override")
    ap.add_argument(
        "--variant",
        default="none",
        choices=("none", "hgmask", "finer", "resid"),
        help="unit-scoped seam variant (R-ERCOT-6); see _apply_variant",
    )
    a = ap.parse_args()
    if a.bundle:
        C.BUNDLE = Path(a.bundle).resolve()
    hs = np.load(a.hours_file) if a.hours_file else None
    res = {}
    for y in a.years:
        ov = {k: json.loads(v) for k, v in (x.split("=", 1) for x in a.set)}
        tag = "".join(f"_{k}" for k in sorted(ov))
        tag += "" if a.variant == "none" else f"_{a.variant}"
        st = build_stages(
            y,
            Path(a.cache_dir) / f"r_ercot5_stages_{y}{tag}.npz",
            ov or None,
            a.variant,
        )
        res[str(y)] = census(y, st, hs)
        print(y, json.dumps(res[str(y)]["summary"]), flush=True)
    Path(a.out).write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
