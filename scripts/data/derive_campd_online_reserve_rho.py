"""Derive the measured online-gated reserve headroom multiplier ``rho`` from CAMPD.

The measured-conduct basis for the online-gated class-2 reserve row
(``model/lp/reserve_rows.py``)::

    R[c, z] - rho * sum_{g eligible in z} P[g, t] <= 0

The row says: the 10-minute reserve held in class *c*, zone *z* is capped at
``rho`` times the ONLINE output of the eligible fleet in that zone — idle
capacity backs none of it, which is what turns a reserve requirement into a
commitment driver. ``rho`` is therefore, in one phrase, **the MW of 10-minute
deliverable headroom that one MW of on-line output carries with it**.

WHY THIS SCRIPT EXISTS. ``model/reserves/spec.py`` declared that quantity as
the eligible fleet's own cap-weighted ``(pmax - pmin) / pmin`` — "a fleet
property read off the same arrays the LP dispatches, not a tuned coefficient".
That identification is guarded by ``valid = (pmin > 0) & (pmax > pmin)``, and
under NYISO's ``plant_level_fleet`` + ``use_campd_bins`` representation
must-run behaviour rides ``min_gen``, not ``pmin`` — so ``pmin`` is identically
zero across the merchant fleet, ZERO eligible rows are valid, and the value
that actually decided the mechanism was the literal ``1.0`` in the ``else:``
branch, in every year and in both the path-A and obligation branches. A
mechanism that is provably inert at ``rho >= 3.16`` and binds in 90 % of hours
at ``rho = 1.0``, on a coefficient that is never measured, has a free parameter
in disguise (CLAUDE.md rule 21 [R-DOF], rule 5 [R-NO-MAGIC]). Full record:
``results/calibration/FINDING-nyiso143-online-rho-unidentified-2026-08-18.md``.

WHAT IS MEASURED HERE. The same quantity, on the meter instead of on an array
the binned representation zeroes out. Over the pooled CAMPD vintages, for every
eligible unit at an eligible plant in the zones the online-gated families
actually draw on::

    HSL_u      = p99.5 of grossLoad over the pooled window   (max sustained load)
    online_u,t = grossLoad >= max(_ONLINE_MW, _ONLINE_FRAC x HSL_u)
    head_u,t   = max(0, min(HSL_u - P_u,t, ramp10_frac_u x HSL_u))
    rho        = sum_{t,u online} head_u,t / sum_{t,u online} P_u,t

``head`` is the unit's physical 10-minute deliverable headroom in that hour:
the smaller of what is left above its output and what it can actually reach
inside a 10-minute window. ``ramp10_frac`` is the model's OWN 10-minute ramp
fraction (:data:`market_sim.data.fleet.RAMP10_FRAC_BY_GROUP` /
``RAMP10_FRAC_BY_FUEL``, the NREL/TP-5500-55588 App. H class rates the
``FleetArrays.ramp10`` array is built from) — the same representation of
"10-minute deliverable" every other ISO's per-gen reserve bound already uses,
never a second construction (rule 19 [R-ONE-MECH]).

The aggregate ratio ``sum(head) / sum(P)`` is the right aggregation because the
LP row itself sums over the fleet: it is the value that makes ``rho * sum P``
reproduce ``sum head`` over the measured record. A mean of per-unit ratios is
not, and diverges as P -> 0.

BASIS-NEUTRALITY (why no plant/unit basis flag is needed here, unlike
``derive_campd_gas_commitment_params.py``). Both HSL and P are taken from the
same meter, and ``ramp10`` is a FRACTION of capacity, so every term in the
ratio scales with the unit's own capability and the MW basis cancels:
``head/P`` is a ratio of fractions. The statistic is therefore immune to the
tranche-vs-plant denominator hazard that forced ``--plant-basis`` on the
min-load derivation, and it needs no nameplate/outage crosswalk — a derated
unit reports its own reduced envelope, a fully-out unit contributes no online
hours.

TWO SENSITIVITIES are written alongside the headline so the basis choice is
auditable rather than asserted:

* ``rho_fullhour`` — the same statistic restricted to hours the unit ran the
  WHOLE hour (CAMPD ``opTime >= _FULL_HOUR_OPTIME``). The headline uses every
  online hour because the LP's ``P`` is an hourly AVERAGE and the row must be
  identified on the LP's own basis; a unit that ran 20 minutes enters the LP as
  a low-output synchronized unit, which is exactly how the headline counts it.
  The restricted value says how much of the answer is partial-hour geometry.
* ``rho_minload`` — the same fleet evaluated at its measured MINIMUM STABLE
  LOAD (the p5-of-online-hours statistic of
  ``derive_campd_gas_commitment_params.py``) instead of over the observed
  loading distribution. This is the direct successor of the DECLARED
  ``(pmax - pmin) / pmin`` basis, 10-minute-limited, and is the operating point
  the row is relevant at (it binds when little is on-line). Reported so the
  headline can be read against the identification it replaces.

Scope is read off the consuming mechanism, never chosen: ``--families``
selects the online-gated family set, and the script derives the zones and the
eligible classes from the model's own registry
(``NYISO_INCITY_OBLIGATION_FAMILIES`` -> NYC + Long Island; the path-A /
published-spinning sets -> their own zone masks). A CAMPD facility carries no
model class, so units are attributed by ``unitType`` (the
``derive_campd_ct_heat_rates.py`` device): a mixed steam/turbine plant
contributes its turbines to the quick-start set and its boilers to the steam
set instead of being dropped as unattributable.

Output: ``data/raw/_processed-legacy/campd_online_reserve_rho_{ISO}.csv``
(one row per family set) plus ``..._units.csv`` with the per-unit detail.

Governance (CLAUDE.md rules 5 [R-NO-MAGIC] / 13 [R-MEASURED] / 21 [R-DOF] /
23 [R-FROZEN-DERIVE]): a measured physical-capability statistic in the same
admissibility class as the CAMPD min-stable loads, committed shares, measured
run lengths and ramp envelopes. Rule 13 admissibility — could this same
quantity be produced for a forward year from forward drivers, and would it
respond to changed conditions? YES on both: it is a function of fleet
composition and class ramp physics evaluated over an operating record, it
regenerates from the CAMPD pipeline for any vintage, and a fleet that retires
steam or adds fast-start capacity moves it. It reads no price and no volume
residual, and it re-derives ONLY when its source data updates (rule 23).

Usage::

    python scripts/data/derive_campd_online_reserve_rho.py --iso NYISO
    python scripts/data/derive_campd_online_reserve_rho.py --iso NYISO --families incity_obligation
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
from market_sim.data.campd import _ONLINE_MW, states_for_iso  # noqa: E402
from market_sim.data.fleet import (  # noqa: E402
    RAMP10_FRAC_BY_FUEL,
    RAMP10_FRAC_BY_GROUP,
    load_fleet_from_csv,
)

UNIT_LEVEL_DIR = RAW_DIR / "campd-unit-level"

# Robust maximum-sustained-load percentile: the HSL proxy. p99.5 rather than the
# raw max so a single over-range meter sample cannot inflate the capability and
# every unit's measured headroom with it. The frozen convention of
# derive_campd_gas_commitment_params.py / derive_cc_committed_pct.py.
_HSL_PCTILE: float = 99.5

# Online threshold as a fraction of the unit's own HSL proxy, floored at the
# CAMPD online convention (market_sim.data.campd._ONLINE_MW). Same frozen "low
# bar that admits a single unit at part load while rejecting sensor noise and
# ramp-through-zero" as the sibling derivations.
_ONLINE_FRAC: float = 0.05

# Percentile of the ONLINE-hours loading distribution taken as the unit's
# minimum stable load, for the `rho_minload` sensitivity only (the headline
# statistic uses no percentile of the loading distribution at all). Frozen
# convention of derive_campd_gas_commitment_params.py.
_LSL_PCTILE: float = 5.0

# CAMPD `opTime` (fraction of the hour the unit operated) at or above which an
# hour counts as FULL-hour operation, for the `rho_fullhour` sensitivity only.
# 0.99 rather than 1.0 because CAMPD reports opTime rounded to two decimals.
_FULL_HOUR_OPTIME: float = 0.99

# CAMPD vintages pooled. 2023-2025 = the calibration span; 2022 and H1-2026 are
# the designated holdouts (CLAUDE.md rule 22), excluded by construction.
POOLED_VINTAGES: tuple[int, ...] = (2023, 2024, 2025)

# CAMPD `unitType` -> the model eligibility bucket a unit contributes to.
# CEMS unit ids carry no model class, but CAMPD's own unitType says which
# devices are simple-cycle turbines, so a mixed facility contributes its
# turbines and its boilers separately (the derive_campd_ct_heat_rates.py
# device) instead of being dropped as unattributable.
_CT_UNIT_TYPE: str = "combustion turbine"
_CC_UNIT_TYPE: str = "combined cycle"


# The online-gated family sets a consumer can identify rho for. Each entry
# names the ScenarioConfig mechanism, the model zones its families draw class-2
# in (read off the family definitions in model/reserves/spec.py), and whether
# the steam union is part of its eligible set. NOTHING here is a choice: the
# zone list is the union of the families' own zone masks and the eligibility is
# the branch's own `eligible` row.
_FAMILY_SETS: dict[str, dict] = {
    # nyiso_incity_commitment_obligation -> NYISO_INCITY_OBLIGATION_FAMILIES
    # {nyc_10min_total, li_10min_total}; obligation_elig = quick_elig | ST_GAS.
    "incity_obligation": {
        "mechanism": "nyiso_incity_commitment_obligation",
        "zones": ("NYC", "Long_Island"),
        "steam": True,
    },
    # nyiso_synchronised_reserve path A -> the hand-scoped nyc_spin_online
    # family (NYISO_DOWNSTATE_SPIN_ZONES = {NYC}); eligible = quick_elig.
    "nyc_spin": {
        "mechanism": "nyiso_synchronised_reserve",
        "zones": ("NYC",),
        "steam": False,
    },
}

# Model fuel types making up the quick-start (10-minute-capable) eligible set —
# model/reserves/spec.QUICK_START_FUEL_TYPES. Imported as a literal rather than
# from spec.py so this data script never imports the LP layer.
_QUICK_START_FUEL_TYPES: frozenset[str] = frozenset({"gas_ct", "oil"})

# Model plant group forming the steam union of the obligation eligible set —
# model/reserves/spec.py's `steam_mask` (plant_group == "ST_GAS").
_STEAM_GROUP: str = "ST_GAS"


def eligible_plants(
    iso: str, zones: tuple[str, ...], steam: bool
) -> tuple[dict[int, frozenset[str]], dict[str, float], dict[str, float]]:
    """Return ``({plant_code: buckets}, {bucket: ramp10_frac}, {bucket: MW})``.

    ``bucket`` is ``"quick"`` (the 10-minute-capable set,
    :data:`_QUICK_START_FUEL_TYPES`) or ``"steam"`` (the obligation's ST_GAS
    union), and each plant maps to the SET of buckets its own model rows
    occupy. A set rather than a label because the set is also the ADMISSIBILITY
    test :func:`_bucket_for_unit` applies: a CAMPD boiler standing at a plant
    whose model rows are all quick-start oil GTs is not silently promoted into
    the quick set — the model carries no steam row there, so the device is
    dropped.

    ``ramp10_frac`` is the capacity-weighted class 10-minute ramp fraction of
    the model rows in each bucket — the same
    :data:`~market_sim.data.fleet.RAMP10_FRAC_BY_GROUP` /
    ``RAMP10_FRAC_BY_FUEL`` lookup ``FleetArrays.ramp10`` is built from, so the
    measured statistic and the LP's own deliverability array read one source.
    The third return is each bucket's eligible model capacity, which
    :func:`family_summary` divides the METERED capability into to report CAMPD
    coverage (a plant with no CEMS contributes no hours and would otherwise
    leave the statistic silently unrepresentative).

    Args:
        iso: The ISO name.
        zones: Model zones the consuming families draw class-2 reserve in.
        steam: Whether the consumer's eligible set unions in ``ST_GAS``.
    """
    fleet = load_fleet_from_csv(iso, get_iso_config(iso))
    by_code: dict[int, set[str]] = {}
    ramp_num: dict[str, float] = {"quick": 0.0, "steam": 0.0}
    ramp_den: dict[str, float] = {"quick": 0.0, "steam": 0.0}
    for gen in fleet:
        if gen.zone not in zones:
            continue
        group = getattr(gen, "plant_group", None) or ""
        if gen.fuel_type in _QUICK_START_FUEL_TYPES:
            bucket = "quick"
        elif steam and group == _STEAM_GROUP:
            bucket = "steam"
        else:
            continue
        code = int(gen.plant_code or 0)
        if code:
            by_code.setdefault(code, set()).add(bucket)
        frac = RAMP10_FRAC_BY_GROUP.get(group)
        if frac is None:
            frac = RAMP10_FRAC_BY_FUEL.get(gen.fuel_type, 0.0)
        ramp_num[bucket] += frac * float(gen.pmax_mw)
        ramp_den[bucket] += float(gen.pmax_mw)
    mapping = {code: frozenset(b) for code, b in by_code.items()}
    ramp = {
        b: (ramp_num[b] / ramp_den[b] if ramp_den[b] > 0 else 0.0)
        for b in ("quick", "steam")
    }
    return mapping, ramp, dict(ramp_den)


def _bucket_for_unit(unit_type: str, plant_buckets: frozenset[str]) -> str | None:
    """Resolve one CAMPD unit to ``"quick"``/``"steam"``, or ``None`` to drop.

    Resolution is by DEVICE first, admissibility second, so the two failure
    modes are handled separately. CAMPD's own ``unitType`` says which device a
    CEMS unit is — combustion turbines are the quick-start devices, boilers are
    the steam devices, and a combined-cycle block is neither (CC is not
    quick-start and is not ``ST_GAS``). The device's bucket is then accepted
    only if the plant's model rows actually occupy it: that is what stops a
    boiler at an oil-GT plant from entering the quick set with a 1.00 ramp
    fraction, and what keeps the steam devices of a mixed plant (Northport,
    Port Jefferson) out of a family set whose eligibility excludes ST_GAS.
    """
    ut = unit_type.strip().casefold()
    if ut == _CC_UNIT_TYPE:
        return None
    device = "quick" if ut == _CT_UNIT_TYPE else "steam"
    return device if device in plant_buckets else None


def unit_statistics(
    iso: str,
    years: tuple[int, ...],
    mapping: dict[int, frozenset[str]],
    ramp: dict[str, float],
) -> pd.DataFrame:
    """Return one row per CAMPD unit with its measured headroom and output sums.

    Loads each state-year extract once, restricts to the eligible plant codes,
    resolves each unit's bucket from CAMPD ``unitType``, and reduces every
    ``(facilityId, unitId)`` to the pooled sums the aggregate ratio needs.
    Percentiles are taken over the POOLED window — a capability is a property
    of the unit, not of a year — while the headroom is evaluated HOUR BY HOUR,
    because ``sum_t min(HSL - P_t, ramp10)`` is not a function of ``sum_t P_t``.

    Args:
        iso: The ISO name.
        years: CAMPD vintages to pool.
        mapping: ``{plant_code: buckets}`` from :func:`eligible_plants`.
        ramp: ``{bucket: ramp10_frac}`` from :func:`eligible_plants` — the
            class 10-minute ramp fraction the model's own ``FleetArrays.ramp10``
            is built from.
    """
    codes = set(mapping)
    loads: dict[tuple[int, str], list[np.ndarray]] = {}
    optimes: dict[tuple[int, str], list[np.ndarray]] = {}
    meta: dict[tuple[int, str], tuple[str, str]] = {}
    for state in states_for_iso(iso):
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
                    "date",
                    "hour",
                    "opTime",
                    "grossLoad",
                ],
            )
            df["facilityId"] = pd.to_numeric(df["facilityId"], errors="coerce")
            df = df[df["facilityId"].isin(codes)]
            if df.empty:
                continue
            df = df.sort_values(["facilityId", "unitId", "date", "hour"])
            for (fid, uid), g in df.groupby(["facilityId", "unitId"], sort=False):
                bucket = _bucket_for_unit(str(g["unitType"].iloc[0]), mapping[int(fid)])
                if bucket is None:
                    continue
                key = (int(fid), str(uid))
                loads.setdefault(key, []).append(
                    g["grossLoad"].fillna(0.0).to_numpy(dtype=float)
                )
                optimes.setdefault(key, []).append(
                    g["opTime"].fillna(0.0).to_numpy(dtype=float)
                )
                meta[key] = (str(g["facilityName"].iloc[0]), bucket)

    if not loads:
        raise SystemExit(f"{iso}: no CAMPD hours found for the eligible plants")

    rows: list[dict] = []
    for key, chunks in loads.items():
        load = np.concatenate(chunks)
        optime = np.concatenate(optimes[key])
        name, bucket = meta[key]
        hsl = float(np.percentile(load, _HSL_PCTILE))
        if hsl <= 0.0:
            continue
        on = load >= max(_ONLINE_MW, _ONLINE_FRAC * hsl)
        if not on.any():
            continue
        frac = float(ramp[bucket])
        ramp10 = frac * hsl
        # The unit's physical 10-minute deliverable headroom, hour by hour: the
        # smaller of what is left above its output and what it can actually
        # reach inside the window. Clipped at 0 because a metered hour can sit
        # above the p99.5 capability proxy.
        head = np.clip(np.minimum(hsl - load, ramp10), 0.0, None)
        full = on & (optime >= _FULL_HOUR_OPTIME)
        # The min-load sensitivity: the SAME headroom formula evaluated at the
        # unit's measured minimum stable load — the direct successor of the
        # declared (pmax-pmin)/pmin basis, 10-minute-limited.
        lsl = float(np.percentile(load[on], _LSL_PCTILE))
        rows.append(
            {
                "plant_code": key[0],
                "unit_id": key[1],
                "plant_name": name,
                "bucket": bucket,
                "ramp10_frac": frac,
                "hsl_mw": hsl,
                "lsl_mw": lsl,
                "ramp10_mw": ramp10,
                "online_hours": int(on.sum()),
                "fullhour_online_hours": int(full.sum()),
                "total_hours": int(load.size),
                "sum_p_mwh": float(load[on].sum()),
                "sum_head_mwh": float(head[on].sum()),
                "sum_p_fullhour_mwh": float(load[full].sum()),
                "sum_head_fullhour_mwh": float(head[full].sum()),
                "minload_p_mw": lsl,
                "minload_head_mw": float(max(0.0, min(hsl - lsl, ramp10))),
                "rho_unit": (
                    float(head[on].sum() / load[on].sum())
                    if load[on].sum() > 0
                    else float("nan")
                ),
            }
        )
    return pd.DataFrame(rows)


def family_summary(
    units: pd.DataFrame,
    iso: str,
    family_set: str,
    eligible_mw: dict[str, float],
) -> pd.DataFrame:
    """Return the one-row measured-``rho`` summary for one family set.

    The headline is the aggregate ratio ``sum(head) / sum(P)`` over every online
    unit-hour of the pooled window — the value that makes ``rho * sum P``
    reproduce the measured deliverable headroom on the LP's own hourly-average
    basis. The two sensitivities (full-hour operation, and the fleet evaluated
    at its measured minimum stable load) are carried alongside so the basis
    choice is auditable.

    Args:
        units: Per-unit frame from :func:`unit_statistics`.
        iso: The ISO name (echoed into the artifact).
        family_set: The :data:`_FAMILY_SETS` key being derived.
        eligible_mw: ``{bucket: MW}`` of eligible MODEL capacity, from
            :func:`eligible_plants`, for the CAMPD coverage fraction.
    """
    if units.empty:
        raise SystemExit(f"{iso}/{family_set}: no eligible CAMPD units")
    spec = _FAMILY_SETS[family_set]
    p = float(units["sum_p_mwh"].sum())
    h = float(units["sum_head_mwh"].sum())
    p_f = float(units["sum_p_fullhour_mwh"].sum())
    h_f = float(units["sum_head_fullhour_mwh"].sum())
    p_m = float(units["minload_p_mw"].sum())
    h_m = float(units["minload_head_mw"].sum())
    by_bucket = units.groupby("bucket").agg(
        n_units=("unit_id", "size"),
        capacity_mw=("hsl_mw", "sum"),
        sum_p=("sum_p_mwh", "sum"),
        sum_head=("sum_head_mwh", "sum"),
    )
    parts = "; ".join(
        f"{b}: n={int(r.n_units)}, hsl_sum={r.capacity_mw:.1f} MW, "
        f"rho={r.sum_head / r.sum_p:.4f}"
        for b, r in by_bucket.iterrows()
        if r.sum_p > 0
    )
    return pd.DataFrame(
        [
            {
                "iso": iso,
                "family_set": family_set,
                "mechanism": spec["mechanism"],
                "zones": "|".join(spec["zones"]),
                "steam_union": bool(spec["steam"]),
                "n_units": int(len(units)),
                "n_plants": int(units["plant_code"].nunique()),
                "hsl_sum_mw": round(float(units["hsl_mw"].sum()), 3),
                "online_unit_hours": int(units["online_hours"].sum()),
                "eligible_model_mw": round(float(sum(eligible_mw.values())), 3),
                "campd_coverage_frac": (
                    round(float(units["hsl_mw"].sum() / sum(eligible_mw.values())), 4)
                    if sum(eligible_mw.values()) > 0
                    else float("nan")
                ),
                "rho": (h / p) if p > 0 else float("nan"),
                "rho_fullhour": (h_f / p_f) if p_f > 0 else float("nan"),
                "rho_minload": (h_m / p_m) if p_m > 0 else float("nan"),
                "by_bucket": parts,
                "years": "-".join(str(y) for y in POOLED_VINTAGES),
                "source": (
                    "EPA CAMPD unit-level hourly grossLoad/opTime "
                    "(data/raw/campd-unit-level); "
                    f"HSL=p{_HSL_PCTILE} of pooled load, "
                    f"online>=max({_ONLINE_MW} MW, {_ONLINE_FRAC}xHSL), "
                    "head=min(HSL-P, ramp10_frac x HSL) clipped at 0, "
                    "rho = sum(head)/sum(P) over online unit-hours; "
                    "ramp10_frac = capacity-weighted "
                    "fleet.RAMP10_FRAC_BY_GROUP/BY_FUEL of the bucket's model "
                    "rows (NREL/TP-5500-55588 App. H); units attributed to "
                    "buckets by CAMPD unitType"
                ),
            }
        ]
    )


def main() -> None:
    """CLI entry point: derive and write one ISO's measured ``rho`` artifacts."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--iso", default="NYISO", help="ISO name (default NYISO)")
    ap.add_argument(
        "--families",
        default="all",
        choices=("all", *sorted(_FAMILY_SETS)),
        help="online-gated family set to identify rho for (default all)",
    )
    ap.add_argument(
        "--years",
        type=int,
        nargs="*",
        default=list(POOLED_VINTAGES),
        help="CAMPD vintages to pool (default 2023 2024 2025)",
    )
    args = ap.parse_args()
    iso = args.iso.upper()
    years = tuple(int(y) for y in args.years)
    wanted = sorted(_FAMILY_SETS) if args.families == "all" else [args.families]

    summaries: list[pd.DataFrame] = []
    details: list[pd.DataFrame] = []
    for family_set in wanted:
        spec = _FAMILY_SETS[family_set]
        print(f"{iso}/{family_set}: zones={spec['zones']} steam={spec['steam']}")
        mapping, ramp, eligible_mw = eligible_plants(iso, spec["zones"], spec["steam"])
        if not mapping:
            raise SystemExit(f"{iso}/{family_set}: model fleet has no eligible plants")
        print(
            f"  {len(mapping)} eligible plant code(s); "
            f"ramp10_frac quick={ramp['quick']:.4f} steam={ramp['steam']:.4f}"
        )
        units = unit_statistics(iso, years, mapping, ramp)
        summary = family_summary(units, iso, family_set, eligible_mw)
        row = summary.iloc[0]
        print(
            f"  rho={row['rho']:.4f}  (fullhour {row['rho_fullhour']:.4f}, "
            f"minload {row['rho_minload']:.4f})  "
            f"over {int(row['online_unit_hours']):,} online unit-hours; "
            f"CAMPD covers {row['campd_coverage_frac']:.1%} of "
            f"{row['eligible_model_mw']:.0f} MW eligible"
        )
        print(f"  {row['by_bucket']}")
        units.insert(0, "family_set", family_set)
        units.insert(0, "iso", iso)
        summaries.append(summary)
        details.append(units)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    out = PROCESSED_DIR / f"campd_online_reserve_rho_{iso}.csv"
    out_units = PROCESSED_DIR / f"campd_online_reserve_rho_{iso}_units.csv"
    pd.concat(summaries, ignore_index=True).to_csv(out, index=False)
    pd.concat(details, ignore_index=True).to_csv(out_units, index=False)
    print(f"wrote {out}")
    print(f"wrote {out_units}")


if __name__ == "__main__":
    main()
