"""Derive measured per-plant POWER-ONLY heat rates for the CHP classes from CAMPD.

The measured replacement for the **steam-credited** heat rate eGRID gives a
cogeneration plant. eGRID's ``PLHTRT`` allocates only the *electric* share of a
CHP plant's fuel to its MWh, so the published rate is not the rate at which the
machine converts fuel to power — it is that rate minus a process-steam credit.
Fed to the LP as a marginal cost it makes CHP the cheapest thermal on the
system. Measured on a consistent net basis, six ISOs' CHP rates are wrong by
−12 % to −62 % (understated) while CAISO's CT_CHP is +40 % over
(``results/calibration/FINDING-caiso128-heat-rate-provenance-2026-07-27.md``
§4), which is why the ISO-keyed hand factors this artifact replaces
(:data:`market_sim.data.fleet.CHP_STEAM_CREDIT_HR_CORRECTION_ISOS`, a single
1.8x topping factor) cannot be right everywhere: they are wrong in both
directions at once.

CEMS meters the fuel and the power at the stack and the generator terminals —
it never sees the steam host — so ``Σ heatInput / Σ grossLoad`` over full-clock,
near-full-load unit-hours **is** the power-only rate, measured rather than
credited. The design is caiso-128 §6, endorsed unchanged by
``results/calibration/FINDING-miso97-chp-sector-btm-2026-07.md`` §3.

Method — per unit and YEAR, then generation-weighted to one row per
``(plant, model class)``::

    peak      = p95 of that unit-year's gross load
    window    = hours with opTime >= 0.99 AND grossLoad > 0.5 x peak
    hr_gross  = sum(heatInput) / sum(grossLoad) over ``window``
    hr_net    = hr_gross / parasitic_factor(plant, SAME YEAR)

**The net-basis reconciliation is not optional**, and it is the step caiso-128
records getting wrong first. eGRID ``PLHTRT`` is ``PLHTIAN/PLNGENAN`` — heat per
**NET** MWh — and the LP dispatches net MW, while CEMS reports **gross**.
Comparing a gross-basis measured rate against the net-basis model rate
overstates the correction by the whole station-service fraction, which for
MISO's CHP classes is 8.0 % (CC_CHP), 23.7 % (CT_CHP) and 30.8 % (ST_CHP) of
the number. This is rule 14 `[R-ACCURATE]`'s named "different boundary"
exception: a *reconciled* real value, never a guess. The factor is read from the
same committed ``parasitic_load_factors.parquet`` the benchmark's per-plant net
actual is built from, so the derived rate and the generation it will be scored
against share one gross-to-net convention.

Zero fitted parameters (rule 24 `[R-REGISTRY]`). ``opTime >= 0.99`` is
"the unit ran the whole clock hour" and the half-peak gate is "at load" — both
definitional, neither swept against a residual. The peak is the unit-year p95
rather than its raw maximum for the same meter-noise reason
``derive_campd_ct_heat_rates.py`` uses p95: one over-range sample must not be
allowed to define full output.

Scope: the CHP classes only — ``CC_CHP``, ``CT_CHP``, ``ST_CHP``. ``CT_PEAKER``,
``CC_REGULAR``, ``COAL`` and ``ST_GAS`` are explicitly OUT of scope: caiso-128
§3 measures them accurate to 0–3 % on a consistent net basis in all six ISOs,
and rule 1 `[R-STRUCT]` forbids changing a correct input to chase a residual.

Output: ``data/raw/_processed-legacy/campd_chp_heat_rates_{ISO}.csv``, one row
per ``(plant, class)``, consumed by
:func:`market_sim.data.fleet.campd_bins.measured_chp_heat_rates` under
``ScenarioConfig.measured_chp_heat_rates``. Where CEMS does not cover a plant
the artifact simply has no row and the existing eGRID -> hand-factor chain is
left untouched — no new estimator, no new free parameter.

Governance (rules 13 `[R-MEASURED]` / 14 `[R-ACCURATE]` / 23
`[R-FROZEN-DERIVE]`): a unit's power-only heat rate is a physical property of
the machine, the same admissibility class as the CAMPD min-stable loads, CT run
horizons and the CO2 emission rates. It regenerates for a forward year from the
same pipeline and responds to changed conditions (a retrofit moves it, a new
unit carries its design rate) — measured per-plant cross-year ``r`` is
0.987–0.993 at a median CV of 0.4–0.7 % (FINDING-miso97 §3.1), so it is stable
enough to carry forward on the CO2-rate precedent
(``docs/handoffs/emissions-co2-rate-plan-2026-07.md``). It is an INPUT, not a
measured outcome fed back to close a residual, and nothing in it is fitted to
one. Per rule 23 it re-derives ONLY when CAMPD publishes new or revised
vintages, and the re-derivation commit must cite that data change.

Usage::

    python scripts/data/derive_campd_chp_heat_rates.py --iso MISO
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.config.paths import PROCESSED_DIR, RAW_DIR  # noqa: E402
from market_sim.data import campd  # noqa: E402
from market_sim.data.fleet import load_fleet_from_csv  # noqa: E402

UNIT_LEVEL_DIR = RAW_DIR / "campd-unit-level"

#: The model classes this artifact prices, and the CAMPD ``unitType`` family
#: each draws its units from. Mirrors ``campd_bins._RAMP_BUCKET_BY_GROUP``'s
#: CC/CT/ST bucketing, so a mixed facility contributes only the units of the
#: technology being priced instead of being dropped as unattributable.
TARGET_CLASSES: tuple[str, ...] = ("CC_CHP", "CT_CHP", "ST_CHP")
_UNIT_FAMILY_BY_CLASS: dict[str, str] = {
    "CC_CHP": "CC",
    "CT_CHP": "CT",
    "ST_CHP": "ST",
}

#: ``unitType`` prefixes per family. Matched with ``startswith`` because CAMPD
#: appends a commissioning note to the type of a unit that entered service
#: mid-year ("Combined cycle (Started Apr 29, 2023)"); an exact-equality match
#: silently drops exactly the newest units.
_CC_PREFIX = "combined cycle"
_CT_PREFIX = "combustion turbine"

#: Full-clock gate: the unit ran the entire metered hour. Definitional, not a
#: swept threshold — a partial ``opTime`` hour blends a start or a shutdown tail
#: into the fuel, which is not the rate at which the machine makes power.
_MIN_OP_TIME: float = 0.99

#: At-load gate, as a fraction of the unit-year's own p95 gross load. Also
#: definitional ("near full output"): below it the unit is part-loaded and its
#: heat rate is the part-load rate, not the one that should set an offer.
_LOAD_FRAC: float = 0.50
_PEAK_PCTILE: float = 95.0

#: Minimum qualifying hours before a unit-year's rate is trusted. A machine that
#: never reached its own at-load band in a year has no measured rate that year.
_MIN_WINDOW_HOURS: int = 50

#: Physical plausibility band (MMBtu/MWh, HHV, NET) for a gas-fired power train.
#: A DATA-INTEGRITY guard on the meter, not a tuning knob: below ~5.5 the row is
#: a broken heat-input channel (no thermal machine beats the ~6.0 best-in-class
#: CC rate by a margin, and a *steam-credited* rate is precisely what this
#: artifact exists to stop trusting), above ~30.0 the gross-load channel is
#: broken or the unit is a tiny auxiliary. Rows outside the band are written
#: with their measured value and a ``flag`` and excluded from the applied map
#: (the loader reads ``flag == "ok"``).
_HR_MIN: float = 5.5
_HR_MAX: float = 30.0


def _unit_family(unit_type: pd.Series) -> pd.Series:
    """Map CAMPD ``unitType`` strings onto the CC / CT / ST family buckets."""
    t = unit_type.astype(str).str.strip().str.casefold()
    return pd.Series(
        np.where(
            t.str.startswith(_CC_PREFIX),
            "CC",
            np.where(t.str.startswith(_CT_PREFIX), "CT", "ST"),
        ),
        index=unit_type.index,
    )


def target_plants(iso: str) -> dict[tuple[int, str], float]:
    """Return ``{(plant_code, class): capacity MW}`` for the ISO's CHP fleet.

    Keyed by the PAIR because one plant can host more than one CHP class, and
    each class is priced from its own CAMPD unit family.
    """
    fleet = load_fleet_from_csv(iso, get_iso_config(iso))
    caps: dict[tuple[int, str], float] = {}
    for gen in fleet:
        if gen.plant_group not in TARGET_CLASSES:
            continue
        code = int(gen.plant_code or 0)
        if code:
            key = (code, gen.plant_group)
            caps[key] = caps.get(key, 0.0) + float(gen.pmax_mw)
    return caps


def model_heat_rates(iso: str) -> dict[tuple[int, str], float]:
    """Return the CURRENT capacity-weighted eGRID heat rate per (plant, class).

    Written to the artifact alongside the measured rate so the table records
    what it replaces and by how much — the provenance a later reader needs to
    judge the swap without re-running anything.
    """
    fleet = load_fleet_from_csv(iso, get_iso_config(iso))
    num: dict[tuple[int, str], float] = {}
    den: dict[tuple[int, str], float] = {}
    for gen in fleet:
        if gen.plant_group not in TARGET_CLASSES:
            continue
        code = int(gen.plant_code or 0)
        if not code:
            continue
        key = (code, gen.plant_group)
        num[key] = num.get(key, 0.0) + float(gen.pmax_mw) * float(gen.heat_rate)
        den[key] = den.get(key, 0.0) + float(gen.pmax_mw)
    return {k: num[k] / den[k] for k in num if den[k] > 0}


def parasitic_factors() -> tuple[dict[tuple[int, int], float], dict[int, float]]:
    """Return the committed gross-to-net maps: ``(per (plant, year), pooled)``.

    Same-year first (caiso-128 §6a: "the plant's own SAME-YEAR measured
    gross->net ratio"), the plant's pooled factor as the fallback where a year
    has no measured row. Only ``source == "measured"`` rows are offered as
    same-year values — a ``class_default`` row carries no plant information, so
    taking it would put a hand constant on the year axis; the pooled fallback
    (and, below it, the class default) is where a constant belongs.

    2025 is the year this matters: its EIA-923 vintage is the monthly early
    release, so far fewer plants carry a measured same-year factor than in 2023
    or 2024 (FINDING-miso97 §2.2, the coverage trap).
    """
    path = PROCESSED_DIR / "parasitic_load_factors.parquet"
    if not path.exists():
        return {}, {}
    df = pd.read_parquet(path)
    measured = df[(df["year"] != 0) & (df["source"] == "measured")]
    by_year = {
        (int(r.plant_id), int(r.year)): float(r.parasitic_factor)
        for r in measured.itertuples(index=False)
    }
    return by_year, campd.pooled_factor_map(df)


def unit_year_heat_rates(
    iso: str, years: list[int], keys: set[tuple[int, str]]
) -> pd.DataFrame:
    """Return one row per (CHP unit, year) with its measured power-only rate.

    Each state-year extract is read once and immediately narrowed to the ISO's
    own CHP plants, so a shared state file cannot leak another ISO's units in.
    The percentile and the window are computed WITHIN a year — the rate is a
    plant-year quantity per caiso-128 §6a, because the gross-to-net ratio it is
    reconciled by is a plant-year quantity.

    Args:
        iso: ISO identifier.
        years: CAMPD vintages to derive.
        keys: ``(plant_code, class)`` pairs from :func:`target_plants`.

    Returns:
        Columns ``plant_code``, ``plant_group``, ``plant_name``, ``unit_id``,
        ``year``, ``gross_mwh``, ``window_hours``, ``peak_mw``, ``hr_gross``.
    """
    codes = {code for code, _ in keys}
    families = {code: set() for code in codes}
    for code, klass in keys:
        families[code].add(_UNIT_FAMILY_BY_CLASS[klass])
    class_by_family = {v: k for k, v in _UNIT_FAMILY_BY_CLASS.items()}

    rows: list[dict] = []
    for state in campd.states_for_iso(iso):
        for year in years:
            path = UNIT_LEVEL_DIR / f"{state}_{year}.parquet"
            if not path.exists():
                print(f"  (skip {path.name}: not on disk)")
                continue
            df = pd.read_parquet(
                path,
                columns=[
                    "facilityId",
                    "facilityName",
                    "unitId",
                    "unitType",
                    "opTime",
                    "grossLoad",
                    "heatInput",
                ],
            )
            df["facilityId"] = pd.to_numeric(df["facilityId"], errors="coerce")
            df = df[df["facilityId"].isin(codes)]
            if df.empty:
                continue
            df["family"] = _unit_family(df["unitType"])
            df = df.dropna(subset=["grossLoad", "heatInput"])
            df = df[(df["grossLoad"] > 0.0) & (df["heatInput"] > 0.0)]
            if df.empty:
                continue
            for (code, unit, family), g in df.groupby(
                ["facilityId", "unitId", "family"], sort=True
            ):
                code = int(code)
                if family not in families.get(code, ()):
                    continue  # the model carries no CHP class of this technology
                peak = float(np.percentile(g["grossLoad"], _PEAK_PCTILE))
                window = g[
                    (g["opTime"].astype(float) >= _MIN_OP_TIME)
                    & (g["grossLoad"] > _LOAD_FRAC * peak)
                ]
                if len(window) < _MIN_WINDOW_HOURS:
                    continue
                rows.append(
                    {
                        "plant_code": code,
                        "plant_group": class_by_family[family],
                        "plant_name": str(g["facilityName"].iloc[0]),
                        "unit_id": str(unit),
                        "year": int(year),
                        "gross_mwh": float(window["grossLoad"].sum()),
                        "window_hours": int(len(window)),
                        "peak_mw": round(peak, 3),
                        "hr_gross": float(
                            window["heatInput"].sum() / window["grossLoad"].sum()
                        ),
                    }
                )
    return pd.DataFrame(rows)


def plant_table(
    units: pd.DataFrame,
    iso: str,
    years: list[int],
    caps: dict[tuple[int, str], float],
    model_hr: dict[tuple[int, str], float],
    by_year: dict[tuple[int, int], float],
    pooled: dict[int, float],
) -> pd.DataFrame:
    """Aggregate the per-unit-year rates to one measured row per (plant, class).

    Each unit-year is converted to the net basis by its plant's OWN same-year
    factor before aggregation, so the pooled value is a weighted mean of
    correctly-reconciled rates rather than a pooled gross rate divided by one
    blended factor. The weight is generation in the qualifying window: the
    machine that made most of the plant's at-load energy should dominate the
    rate the plant offers at.
    """
    units = units.copy()
    default = {
        k: 1.0 - campd.DEFAULT_PARASITIC_LOAD_PCT.get(k, 0.03) for k in TARGET_CLASSES
    }
    factors, sources = [], []
    for r in units.itertuples(index=False):
        f = by_year.get((int(r.plant_code), int(r.year)))
        src = "same_year"
        if f is None:
            f = pooled.get(int(r.plant_code))
            src = "pooled"
        if f is None:
            f = default[r.plant_group]
            src = "class_default"
        factors.append(float(f))
        sources.append(src)
    units["parasitic_factor"] = factors
    units["factor_source"] = sources
    units["hr_net"] = units["hr_gross"] / units["parasitic_factor"]

    rows: list[dict] = []
    for (code, klass), g in units.groupby(["plant_code", "plant_group"], sort=True):
        weight = float(g["gross_mwh"].sum())
        if weight <= 0.0:
            continue
        hr_net = float((g["gross_mwh"] * g["hr_net"]).sum() / weight)
        hr_gross = float((g["gross_mwh"] * g["hr_gross"]).sum() / weight)
        model = model_hr.get((int(code), klass))
        if hr_net < _HR_MIN:
            flag = "below_physical_band"
        elif hr_net > _HR_MAX:
            flag = "above_physical_band"
        else:
            flag = "ok"
        rows.append(
            {
                "plant_code": int(code),
                "plant_group": klass,
                "plant_name": str(g["plant_name"].iloc[0]),
                "n_units": int(g["unit_id"].nunique()),
                "n_unit_years": int(len(g)),
                "years_covered": "-".join(
                    str(y) for y in sorted(g["year"].unique().tolist())
                ),
                "class_capacity_mw": round(float(caps.get((int(code), klass), 0.0)), 3),
                "gross_mwh": round(weight, 1),
                "window_hours": int(g["window_hours"].sum()),
                "parasitic_factor": round(
                    float((g["gross_mwh"] * g["parasitic_factor"]).sum() / weight), 6
                ),
                "factor_source": "+".join(sorted(set(g["factor_source"]))),
                "heat_rate_gross": round(hr_gross, 4),
                # The applied column: MMBtu per NET MWh, the basis the model's
                # heat rate and the benchmark's actual generation both use.
                "heat_rate": round(hr_net, 4),
                "model_heat_rate_egrid": (
                    round(float(model), 4) if model is not None else float("nan")
                ),
                "model_over_measured": (
                    round(float(model) / hr_net, 4)
                    if model is not None and hr_net > 0.0
                    else float("nan")
                ),
                "flag": flag,
            }
        )
    out = pd.DataFrame(rows).sort_values("class_capacity_mw", ascending=False)
    out["iso"] = iso
    out["years"] = "-".join(str(y) for y in years)
    out["source"] = (
        "EPA CAMPD unit-level hourly opTime + grossLoad + heatInput "
        "(data/raw/campd-unit-level); per unit-YEAR heat_rate = "
        f"sum(heatInput)/sum(grossLoad) over hours with opTime >= {_MIN_OP_TIME} "
        f"and grossLoad > {_LOAD_FRAC} x p{_PEAK_PCTILE} of that unit-year's "
        f"gross load (>= {_MIN_WINDOW_HOURS} qualifying hours), converted to a "
        "NET basis by the plant's OWN same-year parasitic factor "
        "(parasitic_load_factors.parquet, the same map the benchmark's net "
        "actual uses; pooled then class default where a year has no measured "
        "row); (plant, class) value is the window-generation-weighted mean "
        "across its unit-years. Units are attributed to a class by CAMPD "
        "unitType family (CC / CT / ST). Physical band "
        f"[{_HR_MIN}, {_HR_MAX}] MMBtu/MWh flags meter defects; only "
        "flag=='ok' rows are applied."
    )
    return out


def main(argv: list[str] | None = None) -> int:
    """Derive and write the measured CHP power-only heat-rate artifact."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iso", required=True, help="ISO name, e.g. MISO")
    parser.add_argument(
        "--years",
        nargs="+",
        type=int,
        default=[2023, 2024, 2025],
        help="CAMPD vintages to derive (default 2023 2024 2025)",
    )
    parser.add_argument("--out", default=None, help="Output CSV path override")
    parser.add_argument(
        "--detail",
        action="store_true",
        help="ALSO write the per-unit-year table alongside the plant summary",
    )
    args = parser.parse_args(argv)
    iso = args.iso.upper()

    caps = target_plants(iso)
    if not caps:
        raise SystemExit(f"{iso}: model fleet has no CHP plants")
    units = unit_year_heat_rates(iso, args.years, set(caps))
    if units.empty:
        raise SystemExit(f"{iso}: no unit-year cleared the at-load window screen")
    by_year, pooled = parasitic_factors()
    table = plant_table(
        units, iso, args.years, caps, model_heat_rates(iso), by_year, pooled
    )

    out_path = (
        Path(args.out)
        if args.out
        else (PROCESSED_DIR / f"campd_chp_heat_rates_{iso}.csv")
    )
    table.to_csv(out_path, index=False)
    print(f"wrote {out_path} ({len(table)} (plant, class) rows)")
    if args.detail:
        detail_path = out_path.with_name(out_path.stem + "_units.csv")
        units.sort_values(["plant_code", "plant_group", "unit_id", "year"]).to_csv(
            detail_path, index=False
        )
        print(f"wrote {detail_path} ({len(units)} unit-year rows)")

    ok = table[table["flag"] == "ok"]
    for klass in TARGET_CLASSES:
        total = sum(mw for (_, k), mw in caps.items() if k == klass)
        sub = ok[ok["plant_group"] == klass]
        n_total = sum(1 for (_, k) in caps if k == klass)
        covered = float(sub["class_capacity_mw"].sum())
        if total <= 0.0:
            continue
        line = (
            f"  {klass:<8} {len(sub):>3}/{n_total:<3} plants  "
            f"{covered:8.0f}/{total:8.0f} MW ({100.0 * covered / total:5.1f} %)"
        )
        if not sub.empty:
            w = sub["class_capacity_mw"].to_numpy(dtype=float)
            meas = sub["heat_rate"].to_numpy(dtype=float)
            model = sub["model_heat_rate_egrid"].to_numpy(dtype=float)
            fin = np.isfinite(model) & (w > 0)
            if fin.any():
                mw_meas = float(np.average(meas[fin], weights=w[fin]))
                mw_model = float(np.average(model[fin], weights=w[fin]))
                line += (
                    f"  model {mw_model:6.2f} vs measured {mw_meas:6.2f} "
                    f"MMBtu/MWh ({100.0 * (mw_model / mw_meas - 1.0):+6.1f} %)"
                )
        print(line)
    if (table["flag"] != "ok").any():
        print("  FLAGGED (not applied):")
        print(
            table[table["flag"] != "ok"][
                ["plant_code", "plant_name", "plant_group", "heat_rate", "flag"]
            ].to_string(index=False)
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
