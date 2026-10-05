"""closeout-chp-floor-basis (ZERO LP): is the CHP steam-level floor applied on the
capacity it was measured on, and does any keeper floor a host above its meter?

``derive_thermal_tranches.py`` measures ``steam_level_cf`` (and ``chp_pmin_cf``)
as a percent of the ARTIFACT's ``nameplate_mw`` x the outage derate, on the
plant's facility-summed CAMPD net. ``fleet/assembly.py`` multiplies that
percent by the LP bin's ``capacity_mw`` (``floor_mw = pmin_cf x (1 - btm) x
nameplate``), and ``fleet/arrays.py`` holds it in every hour (clipped to
``pmax x availability``). This probe measures, for every keeper (the swap keepers first,
the p2-only keepers on request), per CHP plant-group and solved year:

* the level actually applied, its source (``steam_level_cf`` swap or p2
  ``chp_pmin_cf``), the artifact nameplate and the LP nameplate it multiplies;
* the realised floor energy (``min_gen`` rows tagged ``MECH_CHP_STEAM``,
  clipped to ``pmax x availability``) and the model's grid dispatch from the
  committed ``unit_marginal_<year>.parquet`` sidecar;
* the meter: CAMPD whole-plant net (``run_calibration_full._campd_hourly_frame``)
  and the EIA-923 class net (``chp.chp_class_netgen_mwh``);
* ``floor_to_meter`` = grid floor / (meter x (1 - btm)): the floor's plant-total
  equivalent against the meter, on one basis;
* the C1 exposure if the floor were capped at the metered basis: the floored
  energy above the capped level that the keeper actually dispatched (an UPPER
  bound on the class-year move before LP re-dispatch).

Fleets come from the sanctioned :func:`scripts.lib.bundle_fleet.reconstruct_bundle_fleet`.

* the re-based floor (``floor / basis ratio``, clipped to ``pmax x availability``)
  and its dispatch bound: energy released (held above the re-based floor) and
  added (re-based floor above keeper dispatch).

Run: ``uv run python scripts/probes/_closeout_chp_floor_basis_audit.py`` (SPP and
CAISO, the swap keepers) → ``results/phase0/governance/_closeout_chp_floor_basis_audit.json``;
``--isos ERCOT PJM MISO NYISO NEISO SOCO NWPP --out
results/phase0/governance/_closeout_chp_floor_basis_audit_p2.json`` for the
p2-floor keepers (desk follow-up).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(REPO), str(REPO / "src")]

from scripts.lib.bundle_fleet import (  # noqa: E402
    clear_fleet_caches,
    ensure_probe_path,
    reconstruct_bundle_fleet,
)

ensure_probe_path()

KEEPERS = {
    "SPP": "closeout_spp_nuc_span",
    "CAISO": "closeout_caiso_w1_a2_span",
    "ERCOT": "closeout_ercot_l1_span",
    "PJM": "closeout_pjm_nuc_full_span",
    "MISO": "closeout_miso_nuc_span",
    "NYISO": "w0_nyiso_span",
    "NEISO": "w0_neiso_span",
    "SOCO": "closeout_soco_3_span",
    "NWPP": "nwppnext27_span",
}
#: The two keepers that arm ``chp_steam_floor_p25`` (first pass); the other
#: seven carry only the p2 ``chp_pmin_cf`` floor (desk follow-up, ``--isos``).
SWAP_KEEPERS = ("SPP", "CAISO")
YEARS = tuple(range(2019, 2026))
OUT = REPO / "results/phase0/governance/_closeout_chp_floor_basis_audit.json"
CHP = ("CC_CHP", "CT_CHP", "ST_CHP")


def applied_levels(cfg, iso: str) -> dict[tuple[int, str], dict]:
    """Re-run assembly.py's level selection for every CHP artifact row."""
    from market_sim.config.constants import CHP_STEAM_ALLHOURS_MIN_ON_FRAC
    from market_sim.data.fleet.campd_bins import (
        thermal_tranche_chp_steam_duty,
        thermal_tranche_chp_steam_level,
        thermal_tranche_csv_for_iso,
    )

    pu = bool(getattr(cfg, "campd_per_unit_attribution", False))
    mg = bool(getattr(cfg, "campd_outage_merit_order_guard", False))
    path = thermal_tranche_csv_for_iso(iso, pu, mg)
    if not path.exists():
        return {}  # ERCOT: no artifact; the hardcoded CAMPD map has no nameplate
    art = pd.read_csv(path)
    lev = thermal_tranche_chp_steam_level(iso, pu, mg)
    duty = thermal_tranche_chp_steam_duty(iso, pu, mg)
    scope = bool(getattr(cfg, "chp_steam_floor_conduct_scope", False))
    out = {}
    for r in art[art.plant_group.isin(CHP)].itertuples(index=False):
        k = (int(r.plant_code), str(r.plant_group))
        p2 = float(r.chp_pmin_cf) if r.chp_pmin_cf == r.chp_pmin_cf else None
        sw = lev.get(k)
        on = duty.get(k, (None, None))[0]
        scoped_out = (
            sw is not None
            and scope
            and on is not None
            and (on <= CHP_STEAM_ALLHOURS_MIN_ON_FRAC)
        )
        use_sw = sw is not None and not scoped_out and sw > (p2 or 0.0)
        out[k] = {
            "status": str(r.status),
            "name": str(r.name),
            "artifact_nameplate_mw": float(r.nameplate_mw),
            "p2_pmin_cf": p2,
            "steam_level_cf": sw,
            "on_frac": on,
            "scoped_out": bool(scoped_out),
            "level": sw if use_sw else p2,
            "source": "steam_level_cf" if use_sw else "chp_pmin_cf",
        }
    return out


def btm_shares(cfg, iso: str, keys) -> dict[tuple[int, str], float]:
    """The BTM share assembly.py applies (sector default or measured override)."""
    from market_sim.data.chp import (
        chp_btm_measured_armed,
        chp_btm_pct,
        measured_chp_btm_pct_for_iso,
    )

    pu = bool(getattr(cfg, "campd_per_unit_attribution", False))
    mg = bool(getattr(cfg, "campd_outage_merit_order_guard", False))
    meas = measured_chp_btm_pct_for_iso(iso) if chp_btm_measured_armed(cfg) else {}
    return {
        k: float(
            meas.get(
                k[0], chp_btm_pct(k[0], k[1], iso=iso, per_unit=pu, merit_guard=mg)
            )
        )
        for k in keys
    }


def model_side(bundle: Path, iso: str, year: int) -> tuple[pd.DataFrame, object]:
    """Per CHP plant-group: grid cap, realised floor energy, keeper dispatch."""
    from market_sim.data.floor_mechanisms import MECH_CHP_STEAM

    clear_fleet_caches()
    if iso == "PJM":
        # The PJM keeper arms pjm_da_virtual_bids, whose DataMiner2 parquets are
        # gitignored (licence) and absent from a fresh container. Its INC/DEC
        # pseudo-units are APPENDED after the physical fleet and never touch a
        # CHP row's min_gen, so the fleet-only audit stubs them out (declared).
        import market_sim.data.virtual_bids as _vb

        _vb.build_pjm_da_virtual_units = lambda *a, **k: ([], {}, {})
    state, _ = reconstruct_bundle_fleet(bundle, year, verbose=False)
    fa = state["fleet_arrays"]
    gens = getattr(state["fleet"], "generators", state["fleet"])
    avail = np.asarray(fa.availability, dtype=float)
    pmax = np.asarray(fa.pmax, dtype=float)
    mg = np.asarray(fa.min_gen, dtype=float)
    mech = np.asarray(fa.min_gen_mechanism)
    rows = []
    for i, g in enumerate(gens):
        pg = str(getattr(g, "plant_group", ""))
        if pg not in CHP:
            continue
        cap_h = pmax[i] * avail[i, :]
        on = mech[i, :] == MECH_CHP_STEAM
        fl = np.where(on, np.minimum(mg[i, :], cap_h), 0.0)
        rows.append(
            {
                "unit_id": str(g.unit_id),
                "plant_code": int(g.plant_code),
                "plant_group": pg,
                "pmax": float(pmax[i]),
                "floor_mw": float(getattr(g, "chp_grid_pmin_mw", 0.0) or 0.0),
                "floor_mwh": float(fl.sum()),
                "floor_h": fl,
                # Unclipped floor in its own hours, and the clip it meets: what
                # a re-based floor (floor_mw / basis ratio) would be clipped to.
                "raw_h": np.where(on, mg[i, :], 0.0),
                "cap_h": np.where(on, cap_h, 0.0),
            }
        )
    u = pd.read_parquet(
        bundle / f"hourly/unit_marginal_{year}.parquet",
        columns=["unit_id", "hour", "mw"],
    )
    u = u[u.unit_id.astype(str).isin({r["unit_id"] for r in rows})]
    disp = {
        uid: d.sort_values("hour").mw.to_numpy(dtype=float)
        for uid, d in u.groupby(u.unit_id.astype(str), observed=True)
    }
    for r in rows:
        r["mw_h"] = disp.get(r["unit_id"], np.zeros_like(r["floor_h"]))
    return pd.DataFrame(rows), state["config"]


def meter_side(iso: str, year: int) -> tuple[pd.Series, dict]:
    """CAMPD whole-plant net TWh and EIA-923 class net TWh for the year."""
    import scripts.run_calibration_full as rcf
    from market_sim.data.chp import chp_class_netgen_mwh

    camp = rcf._campd_hourly_frame(year, iso, rcf._parasitic_factor_map(), 8760)
    net = (
        camp.groupby("plant_id").net_mw.sum() / 1e6
        if camp is not None
        else pd.Series(dtype=float)
    )
    f923 = {k: v / 1e6 for k, v in chp_class_netgen_mwh(year).items()}
    return net, f923


def main() -> int:
    """Measure the requested keepers and write the JSON."""
    import argparse

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--isos", nargs="+", default=list(SWAP_KEEPERS))
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args()
    from market_sim.data.chp import chp_class_netgen_mwh

    res: dict = {
        "keepers": {i: KEEPERS[i] for i in args.isos},
        "rows": [],
        "class_year": [],
    }
    for iso in args.isos:
        bundle = REPO / "results/calibration" / KEEPERS[iso]
        for year in YEARS:
            if not (bundle / f"hourly/unit_marginal_{year}.parquet").exists():
                continue
            df, cfg = model_side(bundle, iso, year)
            lv = applied_levels(cfg, iso)
            # chp_export_floor_measured (ERCOT): the solve year's EIA-923 class
            # net over the LP nameplate replaces the artifact level — already
            # on the LP basis, so a re-base does not touch it.
            measured = (
                set(chp_class_netgen_mwh(year))
                if getattr(cfg, "chp_export_floor_measured", False)
                else set()
            )
            camp, f923 = meter_side(iso, year)
            keys = sorted(
                {(int(a), str(b)) for a, b in zip(df.plant_code, df.plant_group)}
            )
            btm = btm_shares(cfg, iso, keys)
            cy: dict[str, dict] = {}
            for (pc, pg), d in df.groupby(["plant_code", "plant_group"]):
                k = (int(pc), str(pg))
                fl_h = np.sum(np.stack(d.floor_h.to_list()), axis=0)
                mw_h = np.sum(np.stack(d.mw_h.to_list()), axis=0)
                floor = float(fl_h.sum()) / 1e6
                if floor <= 0.0:
                    continue
                a = lv.get(k, {})
                b = btm.get(k, 0.0) / 100.0
                grid_cap = float(d.pmax.sum())
                lp_np = grid_cap / (1.0 - b) if b < 1.0 else float("nan")
                m_camp = (
                    float(camp.get(pc, np.nan)) if a.get("status") == "ok" else np.nan
                )
                m_923 = float(f923.get(k, np.nan))
                meter = m_camp if m_camp == m_camp else m_923
                meter_grid = meter * (1.0 - b) if meter == meter else np.nan
                ratio = floor / meter_grid if meter_grid and meter_grid > 0 else None
                # Capped at the metered basis: scale the hourly floor so its
                # energy cannot exceed the meter's grid share.
                scale = (
                    min(1.0, meter_grid / floor) if meter_grid == meter_grid else 1.0
                )
                held = np.minimum(mw_h, fl_h)
                release = float(np.maximum(0.0, held - fl_h * scale).sum()) / 1e6
                # Re-based floor: the artifact level expressed on the capacity
                # it multiplies (floor / basis ratio), clipped as arrays.py clips.
                art_np = a.get("artifact_nameplate_mw")
                basis = lp_np / art_np if art_np and k not in measured else None
                raw_h = np.sum(np.stack(d.raw_h.to_list()), axis=0)
                cap_h = np.sum(np.stack(d.cap_h.to_list()), axis=0)
                if basis:
                    rb_h = np.minimum(raw_h / basis, cap_h)
                else:
                    rb_h = fl_h
                rb_rel = float(np.maximum(0.0, held - rb_h).sum()) / 1e6
                rb_add = float(np.maximum(0.0, rb_h - mw_h).sum()) / 1e6
                row = {
                    "iso": iso,
                    "year": year,
                    "plant_code": int(pc),
                    "plant_group": str(pg),
                    "name": a.get("name"),
                    "status": a.get("status"),
                    "level_pct": a.get("level"),
                    "level_source": a.get("source"),
                    "on_frac": a.get("on_frac"),
                    "artifact_nameplate_mw": a.get("artifact_nameplate_mw"),
                    "lp_nameplate_mw": round(lp_np, 1),
                    "basis_ratio": round(basis, 3) if basis else None,
                    "level_basis": "measured_923_lp"
                    if k in measured
                    else ("artifact" if art_np else "unknown"),
                    "btm_pct": round(100 * b, 1),
                    "floor_grid_twh": round(floor, 4),
                    "model_grid_twh": round(float(mw_h.sum()) / 1e6, 4),
                    "campd_net_twh": round(m_camp, 4) if m_camp == m_camp else None,
                    "eia923_net_twh": round(m_923, 4) if m_923 == m_923 else None,
                    "floor_to_meter": round(ratio, 3) if ratio is not None else None,
                    "cap_release_twh_ub": round(release, 4),
                    "floor_rebased_twh": round(float(rb_h.sum()) / 1e6, 4),
                    "rebase_release_twh_ub": round(rb_rel, 4),
                    "rebase_add_twh_ub": round(rb_add, 4),
                }
                res["rows"].append(row)
                c = cy.setdefault(
                    str(pg),
                    {
                        "floor": 0.0,
                        "floor_rebased": 0.0,
                        "model": 0.0,
                        "release": 0.0,
                        "rb_release": 0.0,
                        "rb_add": 0.0,
                        "over": 0,
                    },
                )
                c["floor"] += floor
                c["floor_rebased"] += float(rb_h.sum()) / 1e6
                c["rb_release"] += rb_rel
                c["rb_add"] += rb_add
                c["model"] += row["model_grid_twh"]
                c["release"] += release
                c["over"] += int(ratio is not None and ratio > 1.0)
            for pg, c in sorted(cy.items()):
                res["class_year"].append(
                    {
                        "iso": iso,
                        "year": year,
                        "class": pg,
                        **{k: round(v, 4) for k, v in c.items()},
                    }
                )
            print(
                iso,
                year,
                {k: {kk: round(vv, 3) for kk, vv in v.items()} for k, v in cy.items()},
                flush=True,
            )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(res, indent=1, default=float))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
