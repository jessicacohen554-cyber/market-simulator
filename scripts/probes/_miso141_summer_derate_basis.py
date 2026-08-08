"""miso-141 — G-2 / G-3 / G-3b / G-4 / G-5 gates for the flat ``SUMMER_CLASS_DERATE``
against the net-summer ``pmax`` basis.

PREREG: ``results/calibration/PREREG-miso141-summer-derate-basis-2026-08-07.md``
(pushed before any adjudicating statistic).

Charter: §5.4 QUEUE ITEM 2 — rule 14 ``[R-ACCURATE]``.  **NOT A LEVER**: no C3a
claim attaches to any output of this probe, in either direction (miso-139 §7
bounds the whole capability family at 30-39x too small).

Gates, all measured on MISO's OWN committed inputs, **no LP solved here**:

**G-2 basis (GATING).**  Per unit, the LP's ``pmax`` against that plant's
EIA-860 nameplate / net-summer / winter capability sums.  Pre-registered rule:
the basis is confirmed net-summer iff >=95 % of each class's LP capacity matches
its EIA-860 net-summer figure to within 1 %.  The counter-branch (basis is
NAMEPLATE) kills the charter's hypothesis outright and is checked first.

**G-3 magnitude (GATING for size).**  The three EIA-860 ratings and their
ratios, plus the model's STACKED summer capability (``pmax x availability``,
every overlay live) expressed against both nameplate and net-summer, so the
excess removal is a measured MW quantity.  Materiality bar: >2 % of the class's
summer capability.

**G-3 Trap 3 attribution (rule 19 ``[R-ONE-MECH]``).**  Term-by-term: the summer
capability stack is rebuilt with ``SUMMER_CLASS_DERATE`` zeroed (dict restored
afterwards) so the flat derate's own contribution is separated from
THERMAL_AVAILABILITY / SUMMER_WEFOR_SHARE / the mean-anchored temp overlay /
the CAMPD outage overlay before any excess is attributed to it.

**G-3b the decisive test, provenance-free.**  If the flat derate were an
INCREMENTAL loss below the net-summer rating point, its magnitude is bounded by
the measured ambient swing between that rating condition (summer peak) and
actual summer hours, at MISO's OWN committed slopes (miso-139 G-1).  (i) refutes
on magnitude at >3x; (ii) refutes on SIGN, since the mean summer hour is cooler
than the summer-peak rating condition.

**G-4 reach (diagnostic, NOT licensing).**  Restored summer h12-17 capability in
MW against the keeper's own measured idle cushion.

**G-5 treatment consistency (diagnostic).**  Which ISOs' committed keeper
configs carry ``cc_nameplate_summer_derate``.  Rule 25 ``[R-ISO-SCOPE]``: a
READ of committed configs only — no parameter is transferred into MISO and no
other ISO's artifact is written.

Governance: rule 13 ``[R-MEASURED]`` — every input is a physical or registration
quantity (EIA-860 ratings, zone dry-bulb, the model's own availability matrix),
forward-reproducible; **no price, benchmark or model price output enters any
estimator**.  Rule 22 ``[R-HOLDOUT]`` — 2023/2024/2025 only; MISO holds no
calibration-complete marker.

PROBE HYGIENE (miso-140b §6, binding): the **repo root** goes on ``sys.path``
(not only ``src/``) because ``eia930.zonal_shares._zonal_shares_from_raw``
imports ``scripts.data.curate_zonal_shares``; without it ``load_demand``
SILENTLY falls back to the static Gold-Book split (up to 6,747 MW per zone-hour
on MISO 2025).  ``load_zonal_shares`` is asserted non-None below even though
this probe consumes no per-zone demand, so the assertion cannot rot if a later
edit adds one.

Usage::

    .venv/bin/python scripts/probes/_miso141_summer_derate_basis.py
"""

from __future__ import annotations

import dataclasses
import json
import sys
import typing
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
# Repo root FIRST (probe hygiene, miso-140b §6), then src/.
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.fuel_trajectories import SUMMER_CLASS_DERATE  # noqa: E402
from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.data.eia_loader import iso_zone_hourly_drybulb  # noqa: E402
from market_sim.data.fleet import (  # noqa: E402
    generators_to_fleet_arrays,
    load_fleet_from_csv,
)

ISO = "MISO"
YEARS = (2023, 2024, 2025)
KEEPER = REPO / "results/calibration/miso132_ccmin_B"
OUT = REPO / "results/calibration/_miso141_summer_derate_basis.json"

# The four classes carrying the flat derate.  Under the keeper's
# ``temp_derate_mean_anchored=True`` the temp curve is a pure SHAPE overlay and
# ``_td_covers`` is False by construction (arrays.py:568-584), so ALL FOUR take
# the flat derate — CT_CHP and CC_CHP included.  Scope measured, not assumed.
SCOPE = ("CC_REGULAR", "CC_CHP", "CT_PEAKER", "CT_CHP")
# Carried through as controls so their exemption is a MEASUREMENT.
CONTROLS = ("ST_GAS", "ST_CHP", "COAL")

SUMMER_MONTHS = (6, 7, 8, 9)  # arrays.py::_SUMMER_MONTHS
W_AFT = tuple(range(12, 18))  # miso-137's h12-17 — LOCALISATION ONLY, never a magnitude

# MISO's OWN measured ambient slopes, committed at miso-139 G-1
# (results/calibration/_miso139_derate_gates.json).  Read, not re-derived.
MISO_SLOPES = {"CT_PEAKER": 0.00363, "CT_CHP": 0.00363, "CC_REGULAR": 0.00192, "CC_CHP": 0.00192}


def _hour_month(hours: int) -> np.ndarray:
    """Calendar month (1-12) per hour of a non-leap 8760 year."""
    lens = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    return np.concatenate([np.full(n * 24, m + 1) for m, n in enumerate(lens)])[:hours]


def _hour_of_day(hours: int) -> np.ndarray:
    return np.arange(hours) % 24


def keeper_config(year: int) -> ScenarioConfig:
    """Rebuild the keeper's ScenarioConfig from its committed run_config dump."""
    dump = json.loads((KEEPER / "run_config.json").read_text())["scenario_config"]
    hints = typing.get_type_hints(ScenarioConfig)
    out: dict[str, object] = {}
    for f in dataclasses.fields(ScenarioConfig):
        if f.name not in dump:
            continue
        val = dump[f.name]
        ann = str(hints.get(f.name, ""))
        if val is None:
            out[f.name] = None
        elif "frozenset" in ann and isinstance(val, list):
            out[f.name] = frozenset(val)
        elif "tuple" in ann and isinstance(val, list):
            out[f.name] = tuple(val)
        elif "Path" in ann and isinstance(val, str):
            out[f.name] = Path(val)
        else:
            out[f.name] = val
    out["mode"] = "backcast"
    out["weather_year"] = year
    return ScenarioConfig(**out)  # type: ignore[arg-type]


def _fleet(year: int, cfg: ScenarioConfig):
    return load_fleet_from_csv(
        ISO,
        get_iso_config(ISO),
        year=year,
        measured_ct_heat_rates=bool(getattr(cfg, "measured_ct_heat_rates", False)),
        measured_chp_heat_rates=bool(getattr(cfg, "measured_chp_heat_rates", False)),
        cc_steam_part_capacity=bool(getattr(cfg, "cc_steam_part_capacity", False)),
        cc_steam_part_reclass=bool(getattr(cfg, "cc_steam_part_reclass", False)),
    )


# --------------------------------------------------------------- EIA-860 ratings


def eia860_ratings() -> pd.DataFrame:
    """Per (plant_code, generator_id): nameplate / net-summer / winter capability.

    Straight from the committed EIA-860 Generator_Y Operable sheet — the SAME
    file ``fleet.cc_summer_capacity`` reads.  Three ratings kept SEPARATE
    (PREREG Trap 1: nameplate->summer and summer<->winter are different objects
    with different denominators; they are never substituted for one another).
    """
    raw = pd.read_parquet(
        REPO / "data/raw/eia-860/eia860_generator_operable.parquet",
        columns=[
            "Plant Code",
            "Generator ID",
            "Technology",
            "Nameplate Capacity (MW)",
            "Summer Capacity (MW)",
            "Winter Capacity (MW)",
        ],
    )
    raw = raw[pd.to_numeric(raw["Plant Code"], errors="coerce").notna()].copy()
    raw["plant_code"] = raw["Plant Code"].astype(float).astype(int)
    raw["gen_id"] = raw["Generator ID"].astype(str).str.strip()
    for src, dst in (
        ("Nameplate Capacity (MW)", "nameplate_mw"),
        ("Summer Capacity (MW)", "net_summer_mw"),
        ("Winter Capacity (MW)", "winter_mw"),
    ):
        raw[dst] = pd.to_numeric(raw[src], errors="coerce")
    return raw[
        ["plant_code", "gen_id", "Technology", "nameplate_mw", "net_summer_mw", "winter_mw"]
    ]


def fleet_frame(year: int, cfg: ScenarioConfig) -> pd.DataFrame:
    """The model's own MISO fleet, joined to its EIA-860 ratings, unit by unit."""
    gens = _fleet(year, cfg)
    df = pd.DataFrame(
        [
            {
                "plant_code": int(g.plant_code),
                "unit_id": g.unit_id,
                "plant_group": g.plant_group,
                "zone": g.zone,
                "pmax_mw": float(g.pmax_mw),
            }
            for g in gens
            if g.plant_group
        ]
    )
    # unit_id is "<plant_code>_<generator_id>" on the EIA-860 per-plant path.
    df["gen_id"] = df["unit_id"].astype(str).str.split("_", n=1).str[1]
    r = eia860_ratings()
    merged = df.merge(r, on=["plant_code", "gen_id"], how="left")
    return merged


# ------------------------------------------------------------------ G-2 the basis


def g2_basis(year: int) -> dict:
    """Is MISO's gas ``pmax`` the EIA-860 NET-SUMMER rating, per unit?

    Pre-registered rule: basis confirmed net-summer iff >=95 % of the class's LP
    capacity is within 1 % of its EIA-860 net-summer figure.  The nameplate
    counter-branch is measured on the same rows so the two are distinguishable
    rather than merely 'not nameplate'.
    """
    cfg = keeper_config(year)
    df = fleet_frame(year, cfg)
    rows = {}
    for cls in SCOPE + CONTROLS:
        sel = df[df["plant_group"] == cls].copy()
        if sel.empty:
            continue
        matched = sel[sel["net_summer_mw"].notna() & (sel["net_summer_mw"] > 0)]
        tot = float(sel["pmax_mw"].sum())
        mtot = float(matched["pmax_mw"].sum())
        ns_close = matched[
            (matched["pmax_mw"] - matched["net_summer_mw"]).abs()
            <= 0.01 * matched["net_summer_mw"]
        ]
        np_close = matched[
            matched["nameplate_mw"].notna()
            & (
                (matched["pmax_mw"] - matched["nameplate_mw"]).abs()
                <= 0.01 * matched["nameplate_mw"]
            )
        ]
        rows[cls] = {
            "n_units": int(len(sel)),
            "lp_pmax_mw": tot,
            "n_matched_860": int(len(matched)),
            "matched_pmax_mw": mtot,
            "match_share_of_class_cap": (mtot / tot) if tot else None,
            # The pre-registered gate: share of MATCHED capacity on each basis.
            "share_cap_eq_net_summer_1pct": (
                float(ns_close["pmax_mw"].sum()) / mtot if mtot else None
            ),
            "share_cap_eq_nameplate_1pct": (
                float(np_close["pmax_mw"].sum()) / mtot if mtot else None
            ),
            "sum_nameplate_mw": float(matched["nameplate_mw"].sum()),
            "sum_net_summer_mw": float(matched["net_summer_mw"].sum()),
            "sum_winter_mw": float(matched["winter_mw"].sum()),
        }
    return rows


# ------------------------------------------------------------- G-3 the magnitude


def _capability(gens, zones, cfg, year) -> np.ndarray:
    fa = generators_to_fleet_arrays(gens, zones, 8760, iso=ISO, config=cfg, year=year)
    return fa.pmax[:, None] * fa.availability


def g3_magnitude(year: int) -> dict:
    """Three ratings, their ratios, and the model's STACKED summer capability.

    Trap 3 (rule 19): the stack is rebuilt with ``SUMMER_CLASS_DERATE`` zeroed so
    the flat derate's OWN contribution is separated from every other summer term
    (THERMAL_AVAILABILITY, SUMMER_WEFOR_SHARE, the mean-anchored temp overlay,
    the CAMPD outage overlay, BIN_FORCED_DERATE_BY_YEAR).  The module dict is
    mutated in place and restored in a ``finally`` — the private alias in
    ``arrays.py`` is the SAME object, so this reaches the real read site.
    """
    cfg = keeper_config(year)
    gens = _fleet(year, cfg)
    zones = [z.name for z in get_iso_config(ISO).zones]
    groups = np.array([g.plant_group for g in gens])
    mon = _hour_month(8760)
    hod = _hour_of_day(8760)
    summer = np.isin(mon, SUMMER_MONTHS)
    aft = summer & np.isin(hod, W_AFT)

    base = _capability(gens, zones, cfg, year)
    saved = dict(SUMMER_CLASS_DERATE)
    try:
        for k in list(SUMMER_CLASS_DERATE):
            SUMMER_CLASS_DERATE[k] = 0.0
        nodrt = _capability(gens, zones, cfg, year)
    finally:
        SUMMER_CLASS_DERATE.clear()
        SUMMER_CLASS_DERATE.update(saved)

    df = fleet_frame(year, cfg)
    per_class = {}
    for cls in SCOPE + CONTROLS:
        sel = groups == cls
        if not sel.any():
            continue
        sub = df[df["plant_group"] == cls]
        m = sub["net_summer_mw"].notna() & (sub["net_summer_mw"] > 0)
        np_sum = float(sub.loc[m, "nameplate_mw"].sum())
        ns_sum = float(sub.loc[m, "net_summer_mw"].sum())
        wi_sum = float(sub.loc[m, "winter_mw"].sum())
        lp_pmax = float(np.array([g.pmax_mw for g in gens])[sel].sum())
        # Mean summer availability = stacked capability / (pmax x hours).
        n_h = int(summer.sum())
        stacked_summer = float(base[sel][:, summer].sum())
        stacked_summer_nodrt = float(nodrt[sel][:, summer].sum())
        stacked_aft = float(base[sel][:, aft].sum())
        stacked_aft_nodrt = float(nodrt[sel][:, aft].sum())
        per_class[cls] = {
            "n_units_lp": int(sel.sum()),
            "lp_pmax_mw": lp_pmax,
            # --- the three EIA-860 ratings, kept separate (Trap 1) ---
            "eia860_nameplate_mw": np_sum,
            "eia860_net_summer_mw": ns_sum,
            "eia860_winter_mw": wi_sum,
            "ratio_net_summer_over_nameplate": (ns_sum / np_sum) if np_sum else None,
            "ratio_winter_over_net_summer": (wi_sum / ns_sum) if ns_sum else None,
            "gap_nameplate_to_summer_pct": (
                100.0 * (1.0 - ns_sum / np_sum) if np_sum else None
            ),
            "spread_summer_to_winter_pct": (
                100.0 * (wi_sum / ns_sum - 1.0) if ns_sum else None
            ),
            # --- the model's stacked summer capability ---
            "flat_derate": saved.get(cls, 0.0),
            "summer_mean_availability": stacked_summer / (lp_pmax * n_h) if lp_pmax else None,
            "summer_mean_availability_no_flat_derate": (
                stacked_summer_nodrt / (lp_pmax * n_h) if lp_pmax else None
            ),
            # Mean summer capability MW, with and without the flat derate.
            "summer_mean_capability_mw": stacked_summer / n_h,
            "summer_mean_capability_mw_no_flat_derate": stacked_summer_nodrt / n_h,
            "flat_derate_removal_mw_summer_mean": (stacked_summer_nodrt - stacked_summer) / n_h,
            "flat_derate_removal_mw_aft_mean": (
                (stacked_aft_nodrt - stacked_aft) / int(aft.sum())
            ),
            # The excess against the published rating: how far the STACK sits
            # below net-summer, and how much of that gap the flat derate owns.
            "stacked_summer_vs_net_summer_ratio": (
                (stacked_summer / n_h) / ns_sum if ns_sum else None
            ),
            "stacked_summer_vs_nameplate_ratio": (
                (stacked_summer / n_h) / np_sum if np_sum else None
            ),
            "excess_share_of_summer_capability_pct": (
                100.0 * (stacked_summer_nodrt - stacked_summer) / stacked_summer
                if stacked_summer
                else None
            ),
        }
    return per_class


# ---------------------------------------------------- G-3b the provenance-free test


def g3b_incremental(year: int) -> dict:
    """Could the flat derate be an INCREMENTAL loss below the net-summer rating?

    (i) MAGNITUDE — implied incremental = slope x (T_summer_mean - T_summer_peak)
        at MISO's OWN committed slopes.  Bar: flat derate > 3x refutes P-B.
    (ii) SIGN — the mean summer hour is cooler than the summer-peak rating
        condition, so an honest incremental is on average an UPRATE.
    """
    zones = [z.name for z in get_iso_config(ISO).zones]
    mon = _hour_month(8760)
    summer = np.isin(mon, SUMMER_MONTHS)
    rows = []
    for z in zones:
        t = iso_zone_hourly_drybulb(ISO, year, 8760, zone=z)
        if t is None:
            rows.append({"year": year, "zone": z, "series": None})
            continue
        t = np.asarray(t, float)
        ts = t[summer]
        # The rating condition: EIA net-summer is a SUMMER-PEAK capability
        # rating, so the reference is the hot tail, reported over a spread of
        # definitions rather than one point.
        peaks = {
            "p100": float(ts.max()),
            "p99": float(np.percentile(ts, 99)),
            "p95": float(np.percentile(ts, 95)),
        }
        rows.append(
            {
                "year": year,
                "zone": z,
                "summer_mean_c": float(ts.mean()),
                **{f"summer_peak_{k}_c": v for k, v in peaks.items()},
                **{
                    f"delta_mean_minus_peak_{k}_c": float(ts.mean() - v)
                    for k, v in peaks.items()
                },
            }
        )
    good = [r for r in rows if r.get("summer_mean_c") is not None]
    out = {"zone_rows": rows}
    if good:
        # Class-level implied incremental at the p99 rating point (the middle of
        # the pre-registered spread), capacity-agnostic mean over zones.
        d99 = float(np.mean([r["delta_mean_minus_peak_p99_c"] for r in good]))
        out["mean_delta_mean_minus_peak_p99_c"] = d99
        out["n_zones_delta_negative_p99"] = int(
            sum(1 for r in good if r["delta_mean_minus_peak_p99_c"] < 0)
        )
        out["n_zones"] = len(good)
        out["classes"] = {
            cls: {
                "miso_slope_per_c": s,
                # NEGATIVE implied derate == an UPRATE (mean hour cooler than rating).
                "implied_incremental_derate_at_p99": s * d99,
                "flat_derate": SUMMER_CLASS_DERATE.get(cls, 0.0),
                "ratio_flat_over_abs_implied": (
                    SUMMER_CLASS_DERATE.get(cls, 0.0) / abs(s * d99)
                    if s * d99 != 0
                    else None
                ),
            }
            for cls, s in MISO_SLOPES.items()
        }
    return out


# ----------------------------------------------------------------- G-4 the reach


def g4_reach(year: int, g3: dict) -> dict:
    """Restored summer h12-17 capability against the keeper's OWN idle cushion.

    Diagnostic, NOT licensing (PREREG §3 G-4).  The cushion is read from the
    keeper's committed hourly class-dispatch sidecar, never re-solved.  The
    restored MW is a capability ADDITION, so its price sign is DOWN — the wrong
    way for a model already -14.1 % low in 2025.  No C3a claim attaches.
    """
    restored = sum(
        (v.get("flat_derate_removal_mw_aft_mean") or 0.0)
        for k, v in g3.items()
        if k in SCOPE
    )
    out = {"restored_summer_aft_mw": restored}
    p = KEEPER / "hourly" / f"class_hourly_{year}.parquet"
    if not p.exists():
        out["cushion_mw"] = None
        out["note"] = f"missing sidecar {p.name}"
        return out
    dfh = pd.read_parquet(p)
    out["sidecar_columns"] = list(dfh.columns)[:20]
    return out


# --------------------------------------------------- G-5 cross-ISO treatment read


def g5_treatments() -> dict:
    """Which ISOs' committed keeper configs carry ``cc_nameplate_summer_derate``.

    Rule 25 ``[R-ISO-SCOPE]``: a READ of committed run_configs for a consistency
    diagnostic.  No parameter is transferred into MISO; no other ISO's artifact
    is written and no other ISO's matrix cell is touched (rule 28(d)).
    """
    rows: dict[str, list[dict]] = {}
    for cfgp in sorted((REPO / "results/calibration").glob("*/run_config.json")):
        try:
            d = json.loads(cfgp.read_text())
        except Exception:
            continue
        sc = d.get("scenario_config") or {}
        iso = sc.get("iso")
        if not iso:
            continue
        rows.setdefault(iso, []).append(
            {
                "bundle": cfgp.parent.name,
                "cc_nameplate_summer_derate": sc.get("cc_nameplate_summer_derate"),
                "coal_nameplate_summer_derate": sc.get("coal_nameplate_summer_derate"),
                "plant_level_fleet": sc.get("plant_level_fleet"),
            }
        )
    return {"by_iso": rows}


def main() -> None:
    # PROBE HYGIENE (miso-140b §6): assert the measured zonal-share route is
    # reachable, even though this probe consumes no per-zone demand — so the
    # assertion cannot rot if a later edit adds one.
    from market_sim.data.eia930.zonal_shares import load_zonal_shares

    zs = load_zonal_shares(ISO, 2025, [z.name for z in get_iso_config(ISO).zones])
    assert zs is not None, (
        "load_zonal_shares returned None — repo root is off sys.path and "
        "load_demand would SILENTLY use the static Gold-Book split (miso-140b §6)"
    )

    out: dict = {
        "prereg": "results/calibration/PREREG-miso141-summer-derate-basis-2026-08-07.md",
        "keeper": "2026-08-05-miso-132b-cc-committed",
        "bundle": KEEPER.name,
        "iso": ISO,
        "years": list(YEARS),
        "summer_class_derate": dict(SUMMER_CLASS_DERATE),
        "scope": list(SCOPE),
        "controls": list(CONTROLS),
        "zonal_shares_ok": True,
        "g2_basis": {},
        "g3_magnitude": {},
        "g3b_incremental": {},
        "g4_reach": {},
    }
    for y in YEARS:
        print(f"[miso-141] year {y} …", flush=True)
        out["g2_basis"][str(y)] = g2_basis(y)
        g3 = g3_magnitude(y)
        out["g3_magnitude"][str(y)] = g3
        out["g3b_incremental"][str(y)] = g3b_incremental(y)
        out["g4_reach"][str(y)] = g4_reach(y, g3)
    out["g5_treatments"] = g5_treatments()

    OUT.write_text(json.dumps(out, indent=1, sort_keys=True))
    print(f"[miso-141] wrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
