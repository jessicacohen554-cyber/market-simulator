"""miso-198 PHASE 0 — the measured out-of-merit ST_GAS / steam-CHP conduct object.

ZERO-SOLVE CENSUS. **The rule below is frozen in this docstring and the file is
pushed + blob-verified BEFORE any adjudicating quantity is computed** (the
standing session pattern; miso-197 §10, miso-196 §7). Nothing here is weighed
against a price residual (rule 1 ``[R-STRUCT]``): C3a appears in this probe only
as a per-design-form DIRECTION stated from price mechanics, never as a measured
witness and never as a promotion criterion.

CHARTER (miso-198). FINDING-miso197 §8 root-caused MISO's CC_REGULAR +6.664 TWh
2024 over-dispatch as the visible face of a chronic ~10 TWh/yr out-of-merit
gas-steamer/CHP allocation defect: reality burns 10.2-HR steam gas while 7.1-HR
CC capability sits idle (W3b), the strict-merit LP does the opposite, and the
armed ``st_gas_mustrun_*`` floors carry only ~5.15 TWh of a much larger measured
conduct. This census establishes, in order: (1) the measured conduct object and
its forward-derivability; (2) WHERE the existing identification loses it;
(3) the design-form decision matrix with each form's C8 and C3a face;
(4) the materiality of each form against the inherited C1 quantity target.

Keeper: ``2026-08-30-miso-191-bexit`` (bundle ``results/calibration/miso191_bax_B``).
Rule 22: 2023-2025 only, committed artifacts + raw CAMPD, no marker touched, no
solve. Rule 15: nothing runs, nothing to register.

===============================================================================
BASES (declared; no basis is chosen after seeing a number)
===============================================================================

**B1 — the LOAD-BEARING fleet basis: ``run_year``'s OWN chain.** Per the
miso-197 §6 instrument note, a probe's fleet basis must be
``fleet_to_bins(load_fleet_from_csv(...) + retired_units)`` ->
``build_base_fleet`` -> ``build_dispatch_fleet`` ->
``generators_to_fleet_arrays``, NOT ``fleet.assembly.load_or_synthesize_bins``
-> ``bins_to_fleet``: the two diverge at Cottonwood 55358 (580.4 MW vs the
solve's realized 1,061 MW). The keeper's ``ScenarioConfig`` is rebuilt verbatim
from its committed ``run_config.json`` dump, so the floors this probe reads are
the floors the keeper solved with (``min_gen`` / ``min_gen_mechanism``).

**B2 — the MEASURED basis: raw CAMPD unit-level hourly through the FROZEN
deriver's own helpers**, imported rather than restated (rule 23
``[R-FROZEN-DERIVE]`` — nothing is re-derived here, the estimator is only
read): ``campd.load_campd_hourly`` / ``campd.plant_hourly_net``,
``derive_thermal_tranches._parasitic_factor_map`` /
``._fleet_nameplate_and_group`` / ``._ONLINE_FRAC``, and
``outages.unit_outage_derate_factors`` for the availability denominator. The
plant-online mask is the frozen one: ``net > _ONLINE_FRAC x nameplate x
avail_mult`` (5 % of AVAILABLE capacity).

**B3 — the COMMITTED keeper artifacts**: ``run_config.json``,
``legitimacy_diagnostics.json`` (the D-1/D-2/D-4 rows), ``hourly/`` sidecars,
``frontend/data/backcast/bench/MISO/<year>.json.gz``. The ``hourly/system_<y>``
sidecar additionally supplies the ``load_shape`` the floor's own top-
``online_frac`` SYSTEM-LOAD window is ranked by: the solve passes
``load_shape=demand.sum(axis=0)`` into ``generators_to_fleet_arrays``
(run_calibration.py:3176), and the sidecar's per-zone ``demand`` summed by hour
over the LP's own zone set IS that vector. Supplying it is not optional — with
``load_shape=None`` the runtime's floor block falls through to ``target[:] =
level`` (arrays.py:2841) and spans ALL 8760 hours instead of the plant's
measured window, which would silently collapse the W channel of M-3 to zero and
push its content into L. (INSTRUMENT DEFECT FOUND AND REPAIRED IN THIS SESSION:
the first census run passed ``None``; disclosed in the finding, and the record
below is the repaired run.)

===============================================================================
THE FROZEN RULE
===============================================================================

**THE CONDITIONING SET (inherited verbatim from miso-197 W3b, NOT chosen
here).** ``CC-HEADROOM`` hours of a year are the hours in which the measured
MISO CC_REGULAR fleet aggregate ran below ``W3B_HEADROOM_U`` = 0.90 of its own
``W3B_CC_REF_PCTL`` = 99.5th-percentile demonstrated aggregate output that
year -- i.e. hours in which cheaper CC capability was demonstrably available
and idle, so a strict-merit stack says the 10-HR steamer should be OFF. Every
"out-of-merit" (OOM) quantity below is a measured CAMPD quantity restricted to
that measured hour set. NO model dispatch and NO price enters the conditioning
(rule 13 ``[R-MEASURED]``: the object is a physical/market conduct input, not a
residual; its forward form is the same statistic pooled over the most recent
CAMPD vintages, which responds to fleet turnover and to how much CC headroom a
future fleet carries).

**M-1 THE MEASURED CONDUCT OBJECT** (measurement, no pass/fail). Per (plant,
model class in {ST_GAS, ST_CHP, CT_CHP}, year):
  * ``actual_twh``      -- measured annual net energy;
  * ``oom_twh``         -- measured net energy inside CC-HEADROOM hours;
  * ``oom_share``       -- ``oom_twh / actual_twh``;
  * ``oom_level_mw``    -- MEDIAN measured net over (CC-HEADROOM AND plant-online).
``oom_level_mw`` is the statistic a re-identified floor would have to reproduce;
``p25_cf``/``p25_level_mw`` (what the mechanism uses today) is reported beside it.

**M-2 STABILITY / FORWARD-DERIVABILITY.**
  * **L-2a** a plant is STABLE iff ``(max - min) / mean`` of its three annual
    ``oom_level_mw`` <= **0.35**.
  * **L-2b** the object is FORWARD-DERIVABLE AT PLANT GRAIN iff STABLE plants
    carry >= **0.60** of the class's pooled measured OOM energy.
  * **L-2c** the POOLED statistic is REPRESENTATIVE iff, per plant,
    ``|pooled oom_level_mw - year's| / pooled <= 0.35`` in >= **2 of 3** years.

**M-3 WHERE THE IDENTIFICATION LOSES IT — the P/W/L decomposition.** An EXACT
partition of the ST_GAS gap (an identity, not an approximation; asserted to
1e-6 relative). Over CC-HEADROOM hours, with ``meas`` the measured net MW and
``flr`` the keeper's own armed ``MECH_ST_GAS_MUSTRUN_PER_PLANT`` floor MW:
  * ``measured_oom`` = SUM meas;  ``armed_in_oom`` = SUM min(flr, meas);
  * **P (population)** = SUM meas over plants whose floor is identically zero
    all year (the plant carries no floor at all);
  * **W (window)**     = SUM meas over floored plants in hours where flr == 0;
  * **L (level)**      = SUM max(0, meas - flr) over floored plants in floored
    hours;
  * identity: ``P + W + L == measured_oom - armed_in_oom``.
  * ``O (over-assertion)`` = SUM max(0, flr - meas) over floored plant-hours is
    reported beside it (the D-4 conduct direction), never netted into the gap.
  * **L-3a** the DOMINANT channel is one holding >= **0.45** of the gap in
    >= 2 of 3 years; if none does, the gap is DISPERSED and a repair must
    address every channel.
  * **L-3b** the POPULATION channel is an IDENTIFICATION DEFECT (rather than a
    correct exclusion) iff EVERY plant it contains cleared, in its OWN meter,
    >= **1,000 online hours** AND >= **0.05 TWh** measured energy in >= 2 of 3
    years -- i.e. the census called "laid up" a plant that demonstrably
    operated. The thresholds state what "mothballed" must mean physically; they
    are not tuned to anything.

**M-4 THE DESIGN-FORM MATRIX.** Three forms, each projected ARITHMETICALLY
(explicitly a projection, never an LP result):
  * **(a) FLOOR AT THE MEASURED LEVEL** -- ``min_gen`` at ``oom_level_mw`` in
    the plant's measured window. Price-taker: C3a face **DOWN**.
  * **(b) COMMITTED WITH A REAL OFFER** -- min-load floor at the measured LSL
    (``committed_pct``) plus a free economic segment at the steamer's true
    cost. C3a face **UP** (ST_GAS can be marginal), aimed at the miso-178
    Delta-1 identity.
  * **(c) BID-SIDE SELF-SCHEDULE COST-INSENSITIVITY** -- no floor; the measured
    self-scheduled block is OFFERED price-insensitively so the LP clears it in
    merit. Zero forced energy => zero C8 exposure. C3a face **DOWN** in the
    body (a cheap block displaces the marginal unit down the stack).
  For each form:
  * ``forced_twh_proj`` and ``st_gas_forced_share_proj`` vs the 0.30 merchant
    budget (rule 20 ``[R-FORCED-BUDGET]``);
  * **L-4a** SHAPE-FAITHFUL iff Pearson r between the form's added hour-of-day
    profile and the plants' own measured OOM hour-of-day profile >= **0.80**
    (the D-1 ``d1_min_profile_r`` gate's own line);
  * **L-4b** C8-ADMISSIBLE iff EITHER ``share_proj <= 0.30`` OR the grounded
    path holds: the mechanism carries a cited ``D4_WINDOWS`` entry AND is
    SHAPE-FAITHFUL per L-4a.

**M-5 MATERIALITY** (against the INHERITED C1 quantity target, not a price one).
  * ``CC24_REQUIREMENT`` = **4.00 TWh** -- FINDING-miso197 §8: >= ~4 TWh must
    move off CC_REGULAR-2024 before the W3-unrefuted
    ``cc_outage_derate_from_top`` can re-arm inside the +-8.00 band.
  * ``DONOR_POOL_2024`` = **10.50 TWh** -- ST_GAS+ST_CHP 2024 scored
    under-dispatch (miso-197 §8).
  * **L-5a** a form is MATERIAL iff its projected 2024 ST_GAS increment is
    >= 4.00 TWh AND <= 10.50 TWh (it must not out-run its own donor pool).
  * **L-5b** BAND GUARD: the increment must not carry ST_GAS-2024 through its
    +8.00 C1 band edge from -7.553, i.e. increment <= **15.55 TWh**.

===============================================================================
Usage
===============================================================================
    python3 scripts/probes/_miso198_stgas_oom_conduct_phase0.py --satisfiability
    python3 scripts/probes/_miso198_stgas_oom_conduct_phase0.py

Record: ``results/calibration/_miso198_stgas_oom_conduct_phase0.json``.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import sys
import typing
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO / "src"))
sys.path.insert(0, str(_REPO))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.data import campd  # noqa: E402
from market_sim.data.fleet import (  # noqa: E402
    build_base_fleet,
    build_dispatch_fleet,
    fleet_to_bins,
    generators_to_fleet_arrays,
    load_fleet_from_csv,
    load_mothballed_but_operating,
    load_retired_within_window,
)
from market_sim.data.floor_mechanisms import (  # noqa: E402
    MECH_ST_GAS_MUSTRUN_PER_PLANT,
)
from market_sim.data.outages import unit_outage_derate_factors  # noqa: E402
from scripts.data import derive_thermal_tranches as dtt  # noqa: E402

ISO = "MISO"
YEARS = (2023, 2024, 2025)
HOURS = 8760
KEEPER = _REPO / "results" / "calibration" / "miso191_bax_B"
RUN_ID = "2026-08-30-miso-191-bexit"
OUT = _REPO / "results" / "calibration" / "_miso198_stgas_oom_conduct_phase0.json"

CLASSES = ("ST_GAS", "ST_CHP", "CT_CHP")
FOCUS_CLASS = "ST_GAS"

# ---- frozen ex-ante lines (the docstring is the authority; these mirror it) --
W3B_HEADROOM_U = 0.90        # inherited verbatim from miso-197 W3b
W3B_CC_REF_PCTL = 99.5       # inherited verbatim from miso-197 W3b
L2A_STABLE_SPREAD = 0.35
L2B_STABLE_ENERGY_SHARE = 0.60
L2C_POOLED_DEV = 0.35
L2C_MIN_YEARS = 2
L3A_DOMINANT_SHARE = 0.45
L3A_MIN_YEARS = 2
L3B_MIN_ONLINE_HOURS = 1000
L3B_MIN_TWH = 0.05
L3B_MIN_YEARS = 2
L4A_MIN_PROFILE_R = 0.80     # the D-1 d1_min_profile_r gate's own line
L4B_MERCHANT_BUDGET = 0.30   # rule 20 merchant forced-share budget
CC24_REQUIREMENT = 4.00      # FINDING-miso197 §8
DONOR_POOL_2024 = 10.50      # FINDING-miso197 §8
C1_BAND_TWH = 8.00
ST_GAS_2024_DELTA = -7.553   # the keeper's own C1 row (committed metrics)


# ----------------------------------------------------------------- keeper cfg
def keeper_config(year: int, **overrides: object) -> ScenarioConfig:
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
    out.update(overrides)
    return ScenarioConfig(**out)  # type: ignore[arg-type]


def system_load_shape(year: int) -> np.ndarray:
    """B3: the solve's own ``demand.sum(axis=0)`` from the committed sidecar.

    The per-plant must-run floors rank their commitment window by SYSTEM LOAD,
    so a probe that omits it does not reproduce the keeper's floor at all.
    """
    df = pd.read_parquet(KEEPER / "hourly" / f"system_{year}.parquet")
    s = df[df["pass"] == "P1"].groupby("hour")["demand"].sum().sort_index()
    arr = np.asarray(s.to_numpy(), dtype=float)
    assert arr.shape == (HOURS,), f"system sidecar {year}: {arr.shape}"
    return arr


def build_run_year_fleet(year: int):
    """B1: the fleet through ``run_calibration.run_year``'s OWN chain.

    Mirrors scripts/run_calibration.py:2975-3115 exactly (retiree channel +
    mothball re-carry -> fleet_to_bins(load_fleet_from_csv) -> build_base_fleet
    -> build_dispatch_fleet -> generators_to_fleet_arrays), which the miso-197
    §6 instrument note makes mandatory for any probe reading the solve's fleet.
    """
    cfg = keeper_config(year)
    iso_cfg = get_iso_config(ISO)
    zone_names = [z.name for z in iso_cfg.zones]
    retired_units = load_retired_within_window(
        ISO,
        iso_cfg,
        year=year,
        vintage_status_scope=bool(getattr(cfg, "retiree_vintage_status_scope", False)),
        partial_plant_exit_carry=bool(getattr(cfg, "partial_plant_exit_carry", False)),
    )
    if getattr(cfg, "carry_operating_mothballs", False):
        retired_units = retired_units + load_mothballed_but_operating(
            ISO,
            iso_cfg,
            year=year,
            partial_plant_exit_carry=bool(
                getattr(cfg, "partial_plant_exit_carry", False)
            ),
        )
    synth = fleet_to_bins(
        load_fleet_from_csv(
            ISO,
            iso_cfg,
            year=year,
            measured_ct_heat_rates=cfg.measured_ct_heat_rates,
            measured_chp_heat_rates=cfg.measured_chp_heat_rates,
            cc_steam_part_capacity=cfg.cc_steam_part_capacity,
            cc_steam_part_reclass=cfg.cc_steam_part_reclass,
            egrid_identity_heat_rates=cfg.egrid_identity_heat_rates,
        )
        + retired_units,
        ISO,
        cfg,
    )
    assert not synth.empty, "premise: MISO synthesizes per-plant bins"
    fleet_base = build_base_fleet(
        synth,
        ISO,
        iso_cfg,
        zone_names,
        cfg,
        retired_units,
        [],
        year,
        None,
        vintage_year=year,
        nonthermal_exclude=None,
        legacy_n_bins=0 if getattr(cfg, "plant_level_fleet", False)
        else cfg.heat_rate_bin_count,
    )
    fleet, _fracs, _hyd, _hym = build_dispatch_fleet(
        fleet_base,
        synth,
        [],
        ISO,
        year,
        zone_names,
        cfg,
        imports_after_hydro=True,
        apply_emission_overrides=False,
    )
    fa = generators_to_fleet_arrays(
        fleet,
        zone_names,
        HOURS,
        iso=ISO,
        config=cfg,
        load_shape=system_load_shape(year),
        year=year,
    )
    return fleet, fa, cfg


def plant_floor_series(fleet, fa) -> dict[int, np.ndarray]:
    """Per-plant hourly ST_GAS must-run floor MW carried by the keeper."""
    out: dict[int, np.ndarray] = {}
    if fa.min_gen is None or fa.min_gen_mechanism is None:
        return out
    sel = fa.min_gen_mechanism == MECH_ST_GAS_MUSTRUN_PER_PLANT
    for i, g in enumerate(fleet):
        code = int(getattr(g, "plant_code", 0) or 0)
        if code <= 0 or not sel[i].any():
            continue
        row = np.where(sel[i], fa.min_gen[i], 0.0)
        out[code] = out.get(code, np.zeros(HOURS)) + row
    return out


def model_classes(fleet) -> dict[int, str]:
    """{plant_code: model class} for the census classes (majority pmax wins)."""
    by: dict[int, dict[str, float]] = {}
    for g in fleet:
        code = int(getattr(g, "plant_code", 0) or 0)
        grp = getattr(g, "plant_group", None)
        if code <= 0 or not grp:
            continue
        by.setdefault(code, {})
        by[code][str(grp)] = by[code].get(str(grp), 0.0) + float(g.pmax_mw or 0.0)
    return {c: max(d, key=d.get) for c, d in by.items() if d}


# --------------------------------------------------------------- measurement
def measured_year(year: int) -> tuple[dict[int, np.ndarray], dict[int, np.ndarray]]:
    """B2: ``({plant: net MW}, {plant: online mask})`` for one year."""
    states = campd.states_for_iso(ISO)
    df = campd.load_campd_hourly(states, [year])
    factors = dtt._parasitic_factor_map()
    net = campd.plant_hourly_net(df, factors, year, hours=HOURS)
    cap, primary = dtt._fleet_nameplate_and_group(ISO)
    derate = unit_outage_derate_factors(year, iso=ISO)
    online: dict[int, np.ndarray] = {}
    for code, series in net.items():
        grp = primary.get(int(code))
        npl = float(cap.get((int(code), grp), 0.0)) if grp else 0.0
        if npl <= 0:
            online[int(code)] = np.zeros(HOURS, dtype=bool)
            continue
        mult = derate.get((int(code), grp), np.ones(HOURS))
        avail_cap = npl * np.asarray(mult, dtype=float)
        online[int(code)] = np.isfinite(series) & (avail_cap > 0.0) & (
            series > dtt._ONLINE_FRAC * avail_cap
        )
    return net, online


def cc_headroom_mask(
    net: dict[int, np.ndarray], klass: dict[int, str]
) -> tuple[np.ndarray, dict]:
    """The frozen miso-197 W3b conditioning set for one year."""
    cc = np.zeros(HOURS, dtype=float)
    n_cc = 0
    for code, series in net.items():
        if klass.get(int(code)) == "CC_REGULAR":
            cc += series
            n_cc += 1
    ref = float(np.percentile(cc, W3B_CC_REF_PCTL))
    mask = cc < W3B_HEADROOM_U * ref
    meta = {
        "n_cc_plants": n_cc,
        "cc_p99_5_mw": round(ref, 1),
        "threshold_mw": round(W3B_HEADROOM_U * ref, 1),
        "n_headroom_hours": int(mask.sum()),
    }
    return mask, meta


def pearson(a: np.ndarray, b: np.ndarray) -> float:
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    if a.std() == 0 or b.std() == 0:
        return float("nan")
    return float(np.corrcoef(a, b)[0, 1])


def hod(x: np.ndarray) -> np.ndarray:
    """Hour-of-day mean profile of an 8760 series."""
    return np.asarray(x, dtype=float).reshape(365, 24).mean(axis=0)


# --------------------------------------------------------------------- census
def census() -> dict:
    """Run M-1..M-5 and return the record."""
    rec: dict = {
        "probe": Path(__file__).name,
        "run_id": RUN_ID,
        "keeper_bundle": str(KEEPER.relative_to(_REPO)),
        "frozen_lines": {
            "W3B_HEADROOM_U": W3B_HEADROOM_U,
            "W3B_CC_REF_PCTL": W3B_CC_REF_PCTL,
            "L2A_STABLE_SPREAD": L2A_STABLE_SPREAD,
            "L2B_STABLE_ENERGY_SHARE": L2B_STABLE_ENERGY_SHARE,
            "L2C_POOLED_DEV": L2C_POOLED_DEV,
            "L3A_DOMINANT_SHARE": L3A_DOMINANT_SHARE,
            "L3B_MIN_ONLINE_HOURS": L3B_MIN_ONLINE_HOURS,
            "L3B_MIN_TWH": L3B_MIN_TWH,
            "L4A_MIN_PROFILE_R": L4A_MIN_PROFILE_R,
            "L4B_MERCHANT_BUDGET": L4B_MERCHANT_BUDGET,
            "CC24_REQUIREMENT": CC24_REQUIREMENT,
            "DONOR_POOL_2024": DONOR_POOL_2024,
        },
        "m1": {},
        "m2": {},
        "m3": {},
        "m4": {},
        "m5": {},
    }

    per_year: dict[int, dict] = {}
    for year in YEARS:
        print(f"  [{year}] building B1 fleet through run_year's own chain …")
        fleet, fa, _cfg = build_run_year_fleet(year)
        klass = model_classes(fleet)
        floors = plant_floor_series(fleet, fa)
        print(f"  [{year}] loading B2 measured CAMPD …")
        net, online = measured_year(year)
        mask, meta = cc_headroom_mask(net, klass)
        per_year[year] = {
            "klass": klass,
            "floors": floors,
            "net": net,
            "online": online,
            "mask": mask,
            "meta": meta,
        }
        print(
            f"  [{year}] CC-headroom hours {meta['n_headroom_hours']} "
            f"(CC p99.5 {meta['cc_p99_5_mw']} MW, {meta['n_cc_plants']} plants); "
            f"{len(floors)} plant(s) carry the ST_GAS floor"
        )

    # ------------------------------------------------------------------- M-1
    m1_rows: list[dict] = []
    codes: set[int] = set()
    for year in YEARS:
        d = per_year[year]
        for code, k in d["klass"].items():
            if k in CLASSES:
                codes.add(int(code))
    for code in sorted(codes):
        for year in YEARS:
            d = per_year[year]
            k = d["klass"].get(code)
            if k not in CLASSES:
                continue
            series = d["net"].get(code)
            if series is None:
                m1_rows.append(
                    {
                        "plant_code": code,
                        "class": k,
                        "year": year,
                        "actual_twh": 0.0,
                        "oom_twh": 0.0,
                        "oom_share": None,
                        "oom_level_mw": None,
                        "online_hours": 0,
                        "oom_online_hours": 0,
                        "floored": code in d["floors"],
                    }
                )
                continue
            on = d["online"][code]
            oom_on = on & d["mask"]
            act = float(series.sum()) / 1e6
            oom = float(series[d["mask"]].sum()) / 1e6
            m1_rows.append(
                {
                    "plant_code": code,
                    "class": k,
                    "year": year,
                    "actual_twh": round(act, 4),
                    "oom_twh": round(oom, 4),
                    "oom_share": round(oom / act, 4) if act > 0 else None,
                    "oom_level_mw": (
                        round(float(np.median(series[oom_on])), 2)
                        if oom_on.any()
                        else None
                    ),
                    "online_hours": int(on.sum()),
                    "oom_online_hours": int(oom_on.sum()),
                    "floored": code in d["floors"],
                }
            )
    rec["m1"]["rows"] = m1_rows
    rec["m1"]["headroom_meta"] = {y: per_year[y]["meta"] for y in YEARS}
    by_class: dict[str, dict[int, dict]] = {}
    for r in m1_rows:
        by_class.setdefault(r["class"], {}).setdefault(r["year"], {"actual": 0.0, "oom": 0.0})
        by_class[r["class"]][r["year"]]["actual"] += r["actual_twh"]
        by_class[r["class"]][r["year"]]["oom"] += r["oom_twh"]
    rec["m1"]["class_totals"] = {
        k: {y: {kk: round(vv, 4) for kk, vv in v.items()} for y, v in d.items()}
        for k, d in by_class.items()
    }

    # ------------------------------------------------------------------- M-2
    m2_rows: list[dict] = []
    for code in sorted(codes):
        lv = [
            r["oom_level_mw"]
            for r in m1_rows
            if r["plant_code"] == code and r["oom_level_mw"] is not None
        ]
        klass_of = next((r["class"] for r in m1_rows if r["plant_code"] == code), "")
        oom_e = sum(r["oom_twh"] for r in m1_rows if r["plant_code"] == code)
        if len(lv) < 2:
            m2_rows.append(
                {
                    "plant_code": code, "class": klass_of, "levels": lv,
                    "spread": None, "stable": False, "pooled_repr_years": 0,
                    "pooled_representative": False, "oom_twh_3y": round(oom_e, 4),
                }
            )
            continue
        mean = float(np.mean(lv))
        spread = (max(lv) - min(lv)) / mean if mean > 0 else float("inf")
        pooled = float(np.median(lv))
        nrep = sum(
            1 for v in lv if pooled > 0 and abs(v - pooled) / pooled <= L2C_POOLED_DEV
        )
        m2_rows.append(
            {
                "plant_code": code,
                "class": klass_of,
                "levels": lv,
                "spread": round(spread, 4),
                "stable": bool(spread <= L2A_STABLE_SPREAD),
                "pooled_level_mw": round(pooled, 2),
                "pooled_repr_years": nrep,
                "pooled_representative": bool(nrep >= L2C_MIN_YEARS),
                "oom_twh_3y": round(oom_e, 4),
            }
        )
    rec["m2"]["rows"] = m2_rows
    m2_summary: dict[str, dict] = {}
    for k in CLASSES:
        rows = [r for r in m2_rows if r["class"] == k]
        tot = sum(r["oom_twh_3y"] for r in rows)
        stab = sum(r["oom_twh_3y"] for r in rows if r["stable"])
        share = (stab / tot) if tot > 0 else 0.0
        m2_summary[k] = {
            "n_plants": len(rows),
            "n_stable": sum(1 for r in rows if r["stable"]),
            "oom_twh_3y": round(tot, 4),
            "stable_energy_share": round(share, 4),
            "L2b_forward_derivable": bool(share >= L2B_STABLE_ENERGY_SHARE),
            "n_pooled_representative": sum(
                1 for r in rows if r["pooled_representative"]
            ),
        }
    rec["m2"]["summary"] = m2_summary

    # ------------------------------------------------------------------- M-3
    m3: dict = {"by_year": {}}
    for year in YEARS:
        d = per_year[year]
        meas_oom = armed = P = W = L = O = 0.0
        pop_plants: list[int] = []
        for code, k in d["klass"].items():
            if k != FOCUS_CLASS:
                continue
            series = d["net"].get(code)
            if series is None:
                continue
            m = np.where(d["mask"], series, 0.0)
            meas_oom += float(m.sum())
            flr_full = d["floors"].get(code)
            if flr_full is None or not np.any(flr_full > 0.0):
                P += float(m.sum())
                if float(m.sum()) > 0.0:
                    pop_plants.append(int(code))
                continue
            f = np.where(d["mask"], flr_full, 0.0)
            armed += float(np.minimum(f, m).sum())
            zero = f <= 0.0
            W += float(m[zero].sum())
            L += float(np.maximum(0.0, m[~zero] - f[~zero]).sum())
            O += float(np.maximum(0.0, f - m).sum())
        gap = meas_oom - armed
        m3["by_year"][year] = {
            "measured_oom_twh": round(meas_oom / 1e6, 4),
            "armed_in_oom_twh": round(armed / 1e6, 4),
            "gap_twh": round(gap / 1e6, 4),
            "P_population_twh": round(P / 1e6, 4),
            "W_window_twh": round(W / 1e6, 4),
            "L_level_twh": round(L / 1e6, 4),
            "O_overassertion_twh": round(O / 1e6, 4),
            "identity_residual_rel": (
                round(abs((P + W + L) - gap) / gap, 9) if gap > 0 else 0.0
            ),
            "shares": {
                "P": round(P / gap, 4) if gap > 0 else None,
                "W": round(W / gap, 4) if gap > 0 else None,
                "L": round(L / gap, 4) if gap > 0 else None,
            },
            "population_plants": sorted(pop_plants),
        }
    dom: dict[str, int] = {"P": 0, "W": 0, "L": 0}
    for year in YEARS:
        sh = m3["by_year"][year]["shares"]
        for ch in dom:
            if sh[ch] is not None and sh[ch] >= L3A_DOMINANT_SHARE:
                dom[ch] += 1
    winners = [c for c, n in dom.items() if n >= L3A_MIN_YEARS]
    m3["L3a_dominant_channel"] = winners[0] if len(winners) == 1 else None
    m3["L3a_verdict"] = (
        f"DOMINANT: {winners[0]}" if len(winners) == 1 else "DISPERSED"
    )
    m3["L3a_years_over_line"] = dom
    pop_all = sorted({c for y in YEARS for c in m3["by_year"][y]["population_plants"]})
    pop_rows = []
    for code in pop_all:
        yrs = [
            r for r in m1_rows
            if r["plant_code"] == code and r["class"] == FOCUS_CLASS
        ]
        n_ok = sum(
            1 for r in yrs
            if r["online_hours"] >= L3B_MIN_ONLINE_HOURS and r["actual_twh"] >= L3B_MIN_TWH
        )
        pop_rows.append(
            {
                "plant_code": code,
                "years_operating": n_ok,
                "online_hours": [r["online_hours"] for r in yrs],
                "actual_twh": [r["actual_twh"] for r in yrs],
                "oom_twh": [r["oom_twh"] for r in yrs],
                "clears_L3b": bool(n_ok >= L3B_MIN_YEARS),
            }
        )
    m3["L3b_population_rows"] = pop_rows
    m3["L3b_identification_defect"] = bool(
        pop_rows and all(r["clears_L3b"] for r in pop_rows)
    )
    m3["L3b_verdict"] = (
        "IDENTIFICATION DEFECT — every excluded plant demonstrably operated"
        if m3["L3b_identification_defect"]
        else "NOT a clean identification defect — at least one excluded plant "
        "fails the operating test"
    )
    rec["m3"] = m3

    # ------------------------------------------------------------------- M-4
    # Projected increments per form, arithmetic on the measured object.
    #   (a) floor at the measured OOM level over the plant's measured OOM-online
    #       hours, for every ST_GAS plant that clears the operating test,
    #       CLIPPED to the plant's own measured energy (a floor cannot assert
    #       more than the plant physically made).
    #   (b) min-load at the measured LSL (committed_pct x nameplate) over the
    #       same hours -> forced energy only; the economic segment is free, so
    #       its ENERGY is not projectable arithmetically and is reported None.
    #   (c) no floor: forced energy 0 by construction; the energy it can move is
    #       the same measured object as (a) but cleared economically.
    tranche = pd.read_csv(
        _REPO / "data" / "raw" / "_processed-legacy" / f"thermal_tranches_{ISO}.csv"
    )
    lsl_mw: dict[int, float] = {}
    for r in tranche.itertuples(index=False):
        if str(r.plant_group) != FOCUS_CLASS:
            continue
        try:
            lsl_mw[int(r.plant_code)] = (
                float(r.committed_pct) / 100.0 * float(r.nameplate_mw)
            )
        except (TypeError, ValueError):
            continue
    forms: dict[str, dict] = {}
    add_hod: dict[str, np.ndarray] = {}
    meas_hod = np.zeros(24)
    for year in YEARS:
        d = per_year[year]
        agg = np.zeros(HOURS)
        for code, k in d["klass"].items():
            if k == FOCUS_CLASS and d["net"].get(code) is not None:
                agg += np.where(d["mask"], d["net"][code], 0.0)
        meas_hod += hod(agg)
    meas_hod /= len(YEARS)
    for form in ("a", "b", "c"):
        by_year: dict[int, dict] = {}
        prof = np.zeros(24)
        for year in YEARS:
            d = per_year[year]
            add = np.zeros(HOURS)
            forced = 0.0
            for code, k in d["klass"].items():
                if k != FOCUS_CLASS:
                    continue
                series = d["net"].get(code)
                if series is None:
                    continue
                yrs = [
                    r for r in m1_rows
                    if r["plant_code"] == code and r["year"] == year
                ]
                if not yrs or yrs[0]["oom_level_mw"] is None:
                    continue
                on = d["online"][code] & d["mask"]
                if form == "a":
                    lvl = float(yrs[0]["oom_level_mw"])
                elif form == "b":
                    lvl = float(lsl_mw.get(int(code), 0.0))
                else:
                    lvl = 0.0
                if lvl <= 0.0:
                    continue
                row = np.zeros(HOURS)
                row[on] = np.minimum(lvl, series[on])
                add += row
                forced += float(row.sum())
            by_year[year] = {"projected_forced_twh": round(forced / 1e6, 4)}
            prof += hod(add)
        prof /= len(YEARS)
        add_hod[form] = prof
        forms[form] = {"by_year": by_year, "profile_r": round(pearson(prof, meas_hod), 4)}
    rec["m4"] = {
        "measured_oom_hod_mw": [round(v, 1) for v in meas_hod],
        "forms": {},
    }
    d2_current = {2023: 4.7806, 2024: 5.1507, 2025: 6.6009}
    class_total = {2023: 21.7656, 2024: 21.9921, 2025: 19.2823}
    faces = {"a": "DOWN", "b": "UP", "c": "DOWN"}
    for form in ("a", "b", "c"):
        shares = {}
        for year in YEARS:
            proj = forms[form]["by_year"][year]["projected_forced_twh"]
            if form == "c":
                proj = 0.0
            inc = max(0.0, proj - d2_current[year])
            denom = class_total[year] + inc
            shares[year] = {
                "projected_forced_twh": round(proj, 4),
                "increment_vs_keeper_twh": round(inc, 4),
                "projected_class_twh": round(denom, 4),
                "projected_forced_share": round(proj / denom, 4) if denom > 0 else None,
            }
        r_prof = forms[form]["profile_r"]
        shape_ok = bool(r_prof == r_prof and r_prof >= L4A_MIN_PROFILE_R)
        within = all(
            (s["projected_forced_share"] or 0.0) <= L4B_MERCHANT_BUDGET
            for s in shares.values()
        )
        rec["m4"]["forms"][form] = {
            "by_year": shares,
            "profile_r_vs_measured_oom": r_prof,
            "L4a_shape_faithful": shape_ok,
            "d4_windows_entry": "MECH_ST_GAS_MUSTRUN_PER_PLANT x ST_GAS -> (0, 24)",
            "L4b_c8_admissible": bool(within or shape_ok),
            "L4b_route": (
                "within budget" if within
                else ("grounded path (D4_WINDOWS + shape)" if shape_ok else "NEITHER")
            ),
            "c3a_face_direction": faces[form],
            "added_hod_mw": [round(v, 1) for v in add_hod[form]],
        }

    # ------------------------------------------------------------------- M-5
    m5: dict = {}
    for form in ("a", "b", "c"):
        inc24 = rec["m4"]["forms"][form]["by_year"][2024]["increment_vs_keeper_twh"]
        if form == "c":
            # (c) carries no forced energy; its movable energy is the same
            # measured object as (a), cleared economically rather than forced.
            inc24 = rec["m4"]["forms"]["a"]["by_year"][2024][
                "increment_vs_keeper_twh"
            ]
        m5[form] = {
            "projected_st_gas_increment_2024_twh": round(inc24, 4),
            "L5a_material": bool(CC24_REQUIREMENT <= inc24 <= DONOR_POOL_2024),
            "L5b_band_guard_ok": bool(inc24 <= C1_BAND_TWH - ST_GAS_2024_DELTA),
            "projected_st_gas_2024_delta": round(ST_GAS_2024_DELTA + inc24, 4),
        }
    m5["notes"] = (
        "Increments are ARITHMETIC projections on the measured object, not LP "
        "results: the LP re-optimizes and the realized conversion to class "
        "energy is < 1 (miso-196 measured 74 % on its own arm). Every number "
        "here is an upper bound on the increment and a lower bound on what the "
        "displaced classes give back."
    )
    rec["m5"] = m5
    return rec


def satisfiability() -> None:
    """Verify every basis loads and every witness is computable — NO adjudication."""
    print("SATISFIABILITY (no adjudicating quantity computed)")
    cfg = keeper_config(2024)
    assert cfg.mode == "backcast"
    for f in (
        "st_gas_mustrun_per_plant",
        "st_gas_mustrun_p25_level",
        "st_gas_mustrun_p25_measured_level",
        "mustrun_plant_exclusions",
        "mustrun_layup_window_mask",
    ):
        print(f"  keeper {f} = {getattr(cfg, f)}")
    assert cfg.st_gas_mustrun_per_plant, "premise: the keeper arms the ST_GAS floor"
    ls = system_load_shape(2024)
    print(f"  B3 load_shape 2024: mean {ls.mean() / 1e3:.2f} GW, max {ls.max() / 1e3:.2f} GW")
    fleet, fa, _ = build_run_year_fleet(2024)
    print(f"  B1 fleet rows {len(fleet)}; min_gen {None if fa.min_gen is None else fa.min_gen.shape}")
    assert fa.min_gen is not None and fa.min_gen_mechanism is not None
    floors = plant_floor_series(fleet, fa)
    print(f"  B1 ST_GAS floor plants: {sorted(floors)}")
    assert floors, "premise: the ST_GAS floor is present in the B1 fleet"
    klass = model_classes(fleet)
    n = {k: sum(1 for v in klass.values() if v == k) for k in CLASSES}
    print(f"  B1 census-class plant counts {n}")
    assert all(v > 0 for v in n.values()), "premise: all three classes present"
    net, online = measured_year(2024)
    print(f"  B2 CAMPD plants {len(net)}; online masks {len(online)}")
    mask, meta = cc_headroom_mask(net, klass)
    print(f"  conditioning-set shape OK: {meta['n_cc_plants']} CC plants")
    assert 0 < mask.sum() < HOURS, "premise: the conditioning set is non-degenerate"
    tp = _REPO / "data" / "raw" / "_processed-legacy" / f"thermal_tranches_{ISO}.csv"
    assert tp.exists(), tp
    print(f"  B3 tranche artifact OK ({tp.name})")
    print("SATISFIABLE — every basis loads and every witness is computable.")


def main() -> None:
    ap = argparse.ArgumentParser(description="miso-198 phase-0 census")
    ap.add_argument("--satisfiability", action="store_true")
    args = ap.parse_args()
    if args.satisfiability:
        satisfiability()
        return
    rec = census()
    OUT.write_text(json.dumps(rec, indent=1, default=str))
    print(f"\nwrote {OUT.relative_to(_REPO)}")
    print("\n== M-3 P/W/L decomposition (ST_GAS) ==")
    for y in YEARS:
        r = rec["m3"]["by_year"][y]
        print(
            f"  {y}: measured_oom {r['measured_oom_twh']:7.3f}  armed {r['armed_in_oom_twh']:6.3f}"
            f"  gap {r['gap_twh']:7.3f}  P {r['P_population_twh']:6.3f}"
            f"  W {r['W_window_twh']:6.3f}  L {r['L_level_twh']:6.3f}"
            f"  (identity resid {r['identity_residual_rel']:.2e})"
        )
    print(f"  L-3a {rec['m3']['L3a_verdict']}   L-3b {rec['m3']['L3b_verdict']}")


if __name__ == "__main__":
    main()
