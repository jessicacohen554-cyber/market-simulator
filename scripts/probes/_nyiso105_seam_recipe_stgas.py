"""nyiso-105 — the three no-LP measurements. NO LP IS BUILT AND NO SOLVER RUNS.

Three independent questions, all answered from the committed ``nyiso100_silretire``
keeper bundle, the model's own config tables and the real runtime functions:

* **§A — Item A, the caiso-142 P1 export-sink seam.** caiso-142 §F measured NYISO
  as EXPOSED from the (then) ``nyiso99_demandfix`` keeper: one −600 MW absorption
  row plus ``nyiso_gas_commitment_bridge`` armed, so
  ``pipeline.commitment._bridge_floored_fleet`` composes ``new_min_gen`` over a
  zeros-initialised floor and the sink's ``max(-TTC, 0) = 0`` pins the LP variable
  off. This re-measures the exposure on NYISO's OWN current keeper fleet — the
  nyiso-100 fleet, which RETIRED the ``NYISO_simultaneous_import`` limit and so
  carries a different interchange row set. INFRASTRUCTURE DEFECT AUDIT, not a
  lever: the CAISO mechanism is rejected there on a sign argument and nothing is
  armed here.

* **§B — Item B, ``dual_fuel_oil_reattribution`` on the NYISO recipe metas.**
  §5.5 queue item 10 asserts a zero delta because the calibration CLI pins the
  flag NEISO-only. This VERIFIES rather than asserts, and separates the two
  deltas the queue entry conflates: the DISPATCH delta (which is zero, and why)
  from the RECORDED-CLASS delta (which is not).

* **§C — Lever 1, ``st_gas_mustrun_p25_level`` identification.** Whether the flag
  — or the ``st_gas_mustrun_per_plant`` pair MISO arms it with — can place any
  floor at all on NYISO, and what already floors NYISO ST_GAS (rule 19
  ``[R-ONE-MECH]`` enumeration from the keeper's own D-2 attribution).

Usage:
    PYTHONPATH=.:src .venv/bin/python scripts/probes/_nyiso105_seam_recipe_stgas.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

ISO = "NYISO"
HOURS = 8760
YEARS = (2023, 2024, 2025)
BUNDLE = REPO / "results/calibration/nyiso100_silretire"
TRANCHES = REPO / "data/raw/_processed-legacy/thermal_tranches_NYISO.csv"
FLOOR_COEFFS = REPO / "data/raw/reference/reliability_floor_coeffs_NYISO.csv"

_META_RENAME = {
    "coal_prb_passthrough_sigmoid": "prb_sigmoid",
    "coal_prb_sigmoid_overrides": "prb_overrides",
    "coal_bit_passthrough_sigmoid": "coal_bit_sigmoid",
    "coal_bit_sigmoid_overrides": "bit_overrides",
}


def _meta() -> dict:
    return json.loads((BUNDLE / "meta.json").read_text())


def fleet_state(year: int, **overrides) -> dict:
    """Reconstruct the keeper's fleet for *year* (no LP, no solve).

    Mirrors ``_caiso142_export_sink_basis.fleet_state``: the keeper's
    ``meta.json`` IS the kwargs snapshot, so filtering it against
    ``run_year``'s signature reproduces the solved fleet exactly.
    """
    import inspect

    from run_calibration import run_year

    meta = _meta()
    params = inspect.signature(run_year).parameters
    skip = {
        "year",
        "iso",
        "hours",
        "gas_price",
        "ttc_overrides",
        "fleet_only",
        "xyear_cache",
        "must_run_mw",
    }
    kwargs = {
        _META_RENAME.get(k, k): v
        for k, v in meta.items()
        if _META_RENAME.get(k, k) in params and _META_RENAME.get(k, k) not in skip
    }
    kwargs.update(overrides)
    gp = meta["gas_prices"]
    gas = float(gp.get(str(year), gp.get(year, 0.0)))
    return run_year(
        year,
        meta["iso"],
        int(meta.get("hours", HOURS)),
        gas,
        {},
        fleet_only=True,
        **kwargs,
    )


# --------------------------------------------------------------------------- #
# §A — Item A: the P1 export-sink seam, on NYISO's own keeper fleet
# --------------------------------------------------------------------------- #
def section_a(year: int = 2025) -> dict:
    """Compose the real NYISO bridge floor both ways and diff the result."""
    from market_sim.data.floor_mechanisms import MECH_NYISO_GAS_COMMITMENT_BRIDGE
    from market_sim.pipeline.commitment import _bridge_floored_fleet

    print("\n" + "=" * 78)
    print(f"§A  Item A — the caiso-142 export-sink seam on the NYISO keeper ({year})")
    print("=" * 78)
    state = fleet_state(year)
    fa = state["fleet_arrays"]
    pmin = np.asarray(fa.pmin, dtype=float)
    pmax = np.asarray(fa.pmax, dtype=float)
    uid = np.array([str(u) for u in fa.unit_ids])
    absorb = pmin < 0.0
    # Interchange rows: the import/export pseudo-generators the interchange spec
    # builds. Identified by their pmin<0 or by the model's own supply label.
    supply = np.array([str(s) for s in getattr(fa, "supply", [""] * pmin.size)])
    inter = np.array(
        [s in ("import", "interchange") for s in supply]
    ) | np.char.startswith(uid, "IMPORT")
    print(f"fleet rows={pmin.size}  interchange-ish rows={int(inter.sum())}  "
          f"pmin<0 rows={int(absorb.sum())}")
    for r in np.flatnonzero(absorb):
        print(
            f"  absorption row: {uid[r]:38s} pmin={pmin[r]:10.1f} pmax={pmax[r]:9.1f}"
        )

    base_min_gen = (
        np.asarray(fa.min_gen, dtype=float)
        if fa.min_gen is not None
        else np.broadcast_to(pmin[:, None], (pmin.size, HOURS)).copy()
    )
    # Smallest floor with the shape nyiso_gas_commitment_bridge returns: positive
    # only on bridged thermal rows, zeros everywhere else.
    floor = np.zeros((pmin.size, HOURS), dtype=float)
    thermal = np.flatnonzero(~absorb & (pmax > 0))
    pick = int(thermal[np.argmax(pmax[thermal])])
    floor[pick, 100:200] = 0.52 * float(pmax[pick])

    off = _bridge_floored_fleet(fa, floor, MECH_NYISO_GAS_COMMITMENT_BRIDGE)
    kw = {}
    try:
        _ = _bridge_floored_fleet.__code__.co_varnames
        if "preserve_absorption" in _bridge_floored_fleet.__code__.co_varnames:
            kw = {"preserve_absorption": True}
    except AttributeError:  # pragma: no cover - defensive
        kw = {}
    on = _bridge_floored_fleet(
        fa, floor, MECH_NYISO_GAS_COMMITMENT_BRIDGE, **kw
    )
    mg_off = np.asarray(off.min_gen, dtype=float)
    mg_on = np.asarray(on.min_gen, dtype=float)
    base = np.asarray(base_min_gen, dtype=float)

    rows = []
    print(f"\nbridge floor written on row {uid[pick]} (hours 100-200)")
    for label, mg in (("flag OFF (keeper today)", mg_off), ("flag ON (the fix)", mg_on)):
        print(f"  {label}:")
        for r in np.flatnonzero(absorb):
            verdict = (
                "range DELETED (pinned off)"
                if mg[r].min() == 0.0
                else "range PRESERVED"
            )
            print(
                f"    {uid[r]:38s} min_gen min={mg[r].min():10.1f} "
                f"max={mg[r].max():9.1f}  base min={base[r].min():10.1f} -> {verdict}"
            )
            rows.append(
                {
                    "arm": label,
                    "unit": uid[r],
                    "min_gen_min": float(mg[r].min()),
                    "base_min": float(base[r].min()),
                    "pinned_off": bool(mg[r].min() == 0.0),
                }
            )
    diff = np.abs(mg_on - mg_off) > 0.0
    rows_diff = np.flatnonzero(diff.any(axis=1))
    other = sorted(set(rows_diff.tolist()) - set(np.flatnonzero(absorb).tolist()))
    print(
        f"\nrows differing OFF vs ON: {rows_diff.size} "
        f"(absorption {int(absorb.sum())}, other {len(other)})"
    )
    print(f"  availability identical: {np.array_equal(off.availability, on.availability)}")
    lost = float((base[absorb].min(axis=1) * -1).sum()) if absorb.any() else 0.0
    print(f"  absorption capacity pinned off with the flag OFF: {lost:,.0f} MW")
    return {
        "year": year,
        "fleet_rows": int(pmin.size),
        "absorption_rows": int(absorb.sum()),
        "absorption_mw": lost,
        "preserve_kw_available": bool(kw),
        "rows": rows,
        "other_rows_differing": len(other),
    }


# --------------------------------------------------------------------------- #
# §B — Item B: dual_fuel_oil_reattribution, dispatch vs recorded-class delta
# --------------------------------------------------------------------------- #
def section_b() -> dict:
    """Measure what the NYISO recipe meta's ``dual_fuel_oil_reattribution`` does."""
    print("\n" + "=" * 78)
    print("§B  Item B — dual_fuel_oil_reattribution on the NYISO recipe meta")
    print("=" * 78)
    meta = _meta()
    prb = meta.get("coal_prb_sigmoid_overrides") or {}
    print(f"recipe meta prb_overrides carries the flag : {prb.get('dual_fuel_oil_reattribution')}")
    cfg = json.loads((BUNDLE / "run_config.json").read_text())
    print(f"solved scenario_config.dual_fuel_oil_reattribution : "
          f"{cfg['scenario_config'].get('dual_fuel_oil_reattribution')}")
    print(f"calibration_flags (CLI channel)                    : "
          f"{cfg['calibration_flags'].get('dual_fuel_oil_reattribution')}")

    out = {"recipe_meta": prb.get("dual_fuel_oil_reattribution"),
           "solved_scenario_config": cfg["scenario_config"].get(
               "dual_fuel_oil_reattribution"),
           "cli_flag": cfg["calibration_flags"].get("dual_fuel_oil_reattribution"),
           "years": {}}

    # The keeper's own sidecars: the "oil" klass is written ONLY by the
    # re-attribution (_dispatch_frame relabels klass/fuel in place on the mask).
    print("\nrecorded 'oil' class in the keeper's committed class_hourly sidecars:")
    tot_oil = 0.0
    for y in YEARS:
        d = pd.read_parquet(BUNDLE / "hourly" / f"class_hourly_{y}.parquet")
        d = d[d["pass"] == "P1"] if "pass" in d.columns else d
        by = d.groupby("klass")["mw"].sum()
        oil = float(by.get("oil", 0.0)) / 1e6
        total = float(by.sum()) / 1e6
        hrs = int((d[d.klass == "oil"].groupby("hour")["mw"].sum() > 0).sum())
        tot_oil += oil
        print(f"  {y}: oil {oil:7.4f} TWh of {total:8.3f} TWh served "
              f"({100 * oil / total:5.3f} %) in {hrs} h")
        out["years"][y] = {"oil_twh": round(oil, 4), "served_twh": round(total, 3),
                           "hours_with_oil": hrs}
    print(f"  3-yr total re-attributed: {tot_oil:.4f} TWh")
    out["total_oil_twh"] = round(tot_oil, 4)

    # Structural proof of the ZERO DISPATCH delta: enumerate every consumer of
    # the mask the flag switches on.
    print("\ndispatch-delta proof — every consumer of dual_fuel_oil_mask:")
    src = (REPO / "scripts/run_calibration.py").read_text().splitlines()
    hits = [(i + 1, l.strip()) for i, l in enumerate(src) if "dual_fuel_oil_mask" in l]
    for ln, txt in hits:
        print(f"  run_calibration.py:{ln}: {txt[:110]}")
    src2 = (REPO / "scripts/run_calibration_full.py").read_text().splitlines()
    hits2 = [(i + 1, l.strip()) for i, l in enumerate(src2)
             if "dual_fuel_oil_mask" in l or "oil_switch_mask" in l]
    for ln, txt in hits2:
        print(f"  run_calibration_full.py:{ln}: {txt[:110]}")
    out["mask_consumers"] = [f"run_calibration.py:{ln}" for ln, _ in hits] + [
        f"run_calibration_full.py:{ln}" for ln, _ in hits2
    ]
    return out


# --------------------------------------------------------------------------- #
# §C — Lever 1: st_gas_mustrun_p25_level identification
# --------------------------------------------------------------------------- #
def section_c() -> dict:
    """Can the p25 level swap place any floor on NYISO, and what already does?"""
    from market_sim.data.fleet import (
        thermal_tranche_online_frac,
        thermal_tranche_p25_level,
    )

    print("\n" + "=" * 78)
    print("§C  Lever 1 — st_gas_mustrun_p25_level identification (NYISO)")
    print("=" * 78)
    frac = thermal_tranche_online_frac(ISO)
    lvl = thermal_tranche_p25_level(ISO)
    st_frac = {k: v for k, v in frac.items() if k[1] == "ST_GAS"}
    st_lvl = {k: v for k, v in lvl.items() if k[1] == "ST_GAS"}
    print(f"thermal_tranche_online_frac('{ISO}') -> {len(frac)} rows "
          f"({len(st_frac)} ST_GAS)")
    print(f"thermal_tranche_p25_level('{ISO}')   -> {len(lvl)} rows "
          f"({len(st_lvl)} ST_GAS)")
    art = pd.read_csv(TRANCHES)
    print(f"\nartifact columns: {list(art.columns)}")
    print(f"  'online_frac' column present: {'online_frac' in art.columns}")
    print(f"  'online_hours' column present: {'online_hours' in art.columns}")

    # The runtime gate, verbatim from arrays.py: BOTH flags, and per plant a
    # positive level AND a positive online_frac.
    armable = [k for k in st_lvl if st_lvl.get(k, 0.0) > 0 and st_frac.get(k, 0.0) > 0]
    print(f"\nplants the p25 block could floor (level>0 AND online_frac>0): "
          f"{len(armable)}")
    print("  -> the p25 floor places NOTHING" if not armable else f"  -> {armable}")

    # Cross-ISO: which artifacts carry the column at all.
    print("\ncross-ISO artifact census (rule 25: measurement, not a verdict):")
    for iso in ("ERCOT", "CAISO", "PJM", "MISO", "NYISO", "NEISO"):
        p = REPO / f"data/raw/_processed-legacy/thermal_tranches_{iso}.csv"
        if not p.exists():
            print(f"  {iso:6s} (no artifact)")
            continue
        df = pd.read_csv(p)
        has = "online_frac" in df.columns
        st = df[df.plant_group == "ST_GAS"] if "plant_group" in df.columns else df[:0]
        n_of = int(st["online_frac"].notna().sum()) if has else 0
        print(f"  {iso:6s} online_frac col={str(has):5s}  ST_GAS rows={len(st):3d}  "
              f"with online_frac={n_of:3d}")

    # Rule 19 — what ALREADY floors NYISO ST_GAS, from the keeper's own D-2.
    diag = json.loads((BUNDLE / "legitimacy_diagnostics.json").read_text())
    print("\nrule 19 [R-ONE-MECH] — mechanisms ALREADY forcing NYISO ST_GAS (keeper D-2):")
    d2 = [r for r in diag["diagnostics"]["D2"]["rows"] if r["class"] == "ST_GAS"]
    for r in d2:
        print(f"  {r['year']}  {r['mechanism']:32s} {r['forced_twh']:7.4f} TWh "
              f"= {100 * r['share_of_class']:5.2f} % of class "
              f"({r['class_total_twh']:.4f} TWh)")
    print("  D-2 C8 failures:", diag["diagnostics"]["D2"]["failures"])

    # And which reliability-floor limbs actually survive the keeper's overrides.
    ov = (_meta().get("coal_prb_sigmoid_overrides") or {}).get(
        "reliability_floor_overrides", {}
    )
    coeff = pd.read_csv(FLOOR_COEFFS)
    st = coeff[(coeff.plant_class == "ST_GAS") & (coeff.enabled)].copy()
    print("\nenabled NYISO ST_GAS reliability-floor limbs, after keeper overrides:")
    for r in st.itertuples(index=False):
        rg = r.ramp_group if isinstance(r.ramp_group, str) else "_none"
        key = f"{r.zone}:ST_GAS:{r.driver}:{rg}"
        killed = ov.get(key, {}).get("enabled") is False
        basis = str(r.threshold_basis)[:72].replace("\n", " ")
        print(f"  {'OFF' if killed else 'ON ':3s} {key:44s} "
              f"thr={r.threshold:7.2f} floor_pct={r.floor_pct:6.4f}  {basis}")
    return {
        "online_frac_rows": len(frac),
        "st_gas_online_frac_rows": len(st_frac),
        "st_gas_p25_rows": len(st_lvl),
        "armable_plants": len(armable),
        "artifact_has_online_frac_col": "online_frac" in art.columns,
        "d2_st_gas": d2,
        "d2_failures": diag["diagnostics"]["D2"]["failures"],
    }


# --------------------------------------------------------------------------- #
# §A2 — Item A: is the deleted outlet LIVE or LATENT? (no LP)
# --------------------------------------------------------------------------- #
def section_a2() -> dict:
    """Count the hours the pinned-off export sink would have been in the money.

    An absorption row with ``pmin < 0`` and marginal cost ``c`` is a demand the
    LP is paid ``c`` to serve, so it clears exactly when the sink's zonal energy
    price is BELOW ``c``. Scoring that against the keeper's own committed P1
    zonal duals bounds how much of the scored solve the caiso-142 seam actually
    changed — exposure alone does not say the outlet was ever wanted.
    """
    print("\n" + "=" * 78)
    print("§A2 Item A — how LIVE is the deleted outlet? (keeper duals vs sink price)")
    print("=" * 78)
    out = {}
    for year in YEARS:
        state = fleet_state(year)
        fa = state["fleet_arrays"]
        uid = [str(u) for u in fa.unit_ids]
        pmin = np.asarray(fa.pmin, dtype=float)
        r = int(np.flatnonzero(pmin < 0.0)[0])
        mc = np.asarray(state["mc_base"], dtype=float)
        sink_mc = mc[r] if mc.ndim == 2 else np.full(HOURS, float(mc[r]))
        sys_ = pd.read_parquet(BUNDLE / "hourly" / f"system_{year}.parquet")
        sys_ = sys_[sys_["pass"] == "P1"]
        # The solved LP zone vector = the ISO's mainland zones followed by the
        # interchange NODE zones apply_interchange_topology appends
        # (NYISO_external). Rebuild it from the config plus whatever extra
        # zones the keeper's own system sidecar recorded.
        from market_sim.config.iso_configs import get_iso_config

        mainland = [z.name for z in get_iso_config(ISO).zones]
        extra = [z for z in sorted(sys_["zone"].unique()) if z not in mainland]
        zone_names = mainland + extra
        zi = int(fa.zone_idx[r])
        zone = zone_names[zi] if zi < len(zone_names) else f"zone_idx={zi}"
        price = sys_.pivot_table(index="hour", columns="zone", values="price")
        dem = sys_.pivot_table(index="hour", columns="zone", values="demand")
        lam = (
            price[zone].reindex(range(HOURS)).to_numpy()
            if zone in price.columns
            else ((price * dem).sum(axis=1) / dem.sum(axis=1))
            .reindex(range(HOURS))
            .to_numpy()
        )
        itm = np.isfinite(lam) & np.isfinite(sink_mc) & (sink_mc > lam)
        gap = np.where(itm, sink_mc - lam, 0.0)
        print(
            f"  {year}: sink={uid[r]} zone={zone} pmin={pmin[r]:.0f} MW  "
            f"sink price p50={np.nanmedian(sink_mc):8.2f}  zone lambda p50={np.nanmedian(lam):8.2f}"
        )
        print(
            f"        in-the-money hours {int(itm.sum()):5d}/{HOURS} "
            f"({100 * itm.mean():5.2f} %)  max gap {gap.max():8.2f} $/MWh  "
            f"foregone export <= {abs(pmin[r]) * itm.sum() / 1e6:6.4f} TWh"
        )
        out[year] = {
            "sink": uid[r],
            "zone": zone,
            "pmin_mw": float(pmin[r]),
            "itm_hours": int(itm.sum()),
            "itm_share": round(float(itm.mean()), 4),
            "max_gap": round(float(gap.max()), 2),
            "bound_twh": round(float(abs(pmin[r]) * itm.sum() / 1e6), 4),
        }
    return out


def main() -> int:
    out = {"probe": "nyiso-105", "bundle": BUNDLE.name}
    out["C"] = section_c()
    out["B"] = section_b()
    out["A"] = section_a()
    out["A2"] = section_a2()
    dest = REPO / "results/calibration/_nyiso105_noLP_measurements.json"
    dest.write_text(json.dumps(out, indent=1, default=str))
    print(f"\nwrote {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
