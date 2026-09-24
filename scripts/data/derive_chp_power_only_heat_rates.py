"""Derive measured per-plant POWER-ONLY heat rates for topping-cycle CHP classes.

The measured replacement for the **steam-credited** heat rate eGRID gives a
cogeneration plant. The model's offer heat rate is eGRID ``PLNT<YY>.PLHTRT`` (the solve year's own vintage since F1)
(``scripts/data/process_eia860._join_egrid_heat_rate``), and for a CHP plant
eGRID does not publish that as total fuel per net MWh: it first removes the
share of the plant's fuel it attributes to **useful thermal output**, so
``PLHTRT`` is a *steam-credited* rate, not the rate at which the machine turns
fuel into power. Fed to the LP as a marginal cost it makes CHP the cheapest
thermal on the system — six ISOs' CHP rates measure 12-62 % understated on a
consistent net basis
(``results/calibration/FINDING-caiso128-heat-rate-provenance-2026-07-27.md``
§4), which is also why the ISO-keyed hand factors this artifact replaces
(:data:`market_sim.data.fleet.CHP_STEAM_CREDIT_HR_CORRECTION_ISOS`, a single
1.8x topping factor) cannot be right everywhere: caiso-128 measured them
over-correcting CAISO CT_CHP by +40 % while five ISOs sit under.

THE MEASUREMENT — eGRID publishes the credit it removed, so it can be put back
=============================================================================
The eGRID plant sheet carries **both** halves of the split:

* ``PLHTIAN``  — plant annual heat input **allocated to electricity** (MMBtu).
  ``PLHTRT = PLHTIAN / PLNGENAN``, which is the number the model loads.
* ``CHPCHTI``  — plant annual heat input **allocated to useful thermal output**
  (MMBtu). Zero / blank at a plant eGRID gives no credit, blank at every
  non-CHP plant.

so the plant's power-only heat rate on the model's own NET basis is::

    heat_rate = (PLHTIAN + CHPCHTI) / PLNGENAN

**No gross-to-net factor is involved, and that is the point.** ``PLNGENAN`` is
already NET generation — it is the denominator the model's incumbent rate
already divides by, and it is identical to the EIA-923 combustion net the
calibration benchmark holds out against (measured: ``net923 / PLNGENAN`` =
1.000000 on every MISO thermal plant). The correction is therefore a single
change to the incumbent input — eGRID's own CHP allocation, undone — with the
basis, the source, the vintage and the denominator all held fixed. This is what
unblocks the design ``results/calibration/FINDING-miso98-chp-sector-ab-2026-07.md``
§6.1 stopped on: the CEMS route needed a CHP-specific gross-to-net ratio that
``compute_parasitic_factors`` cannot supply (a cogen's CEMS gross-load channel
misses the units EIA-923 counts, so the reconciliation falls out of band on
every cogen), and the fix is to never go through gross at all.

It also cannot double-count the host: ``chp_btm_pct`` holds the host share out
as a **volume** (of capacity, of the floor, of the benchmark subtrahend), while
this is an **intensity** (MMBtu per net MWh) applied to whatever the LP
dispatches. Host-served MWh sit in the denominator of the plant's own rate
because they come off the same machine burning the same fuel.

VALIDATION — the decomposition is arithmetic on metered fuel, not a model
------------------------------------------------------------------------
``PLHTIAN + CHPCHTI`` is checked against the plant's independently metered
CAMPD/CEMS annual heat input. MISO 2023: the ratio is **1.00000** on 22 of the
25 CHP plants CEMS covers, against a median of **1.473** for ``PLHTIAN`` alone.
The three misses (10328, 55096, 55799) are plants with combustion units below
the Part-75 reporting threshold, where CEMS undercounts the fuel and eGRID is
the complete source — the check fails toward CEMS, never toward eGRID. The
``cems_vs_egrid_total`` column carries the ratio per plant so the artifact
records its own validation.

SCOPE — topping cycles only, on turbine physics
-----------------------------------------------
Adding the credit back charges **all** of the plant's fuel to its power. That
is the correct power-only rate for a **topping cycle**, where the fuel goes
through the prime mover first and the process steam is recovered from its
exhaust: the steam is a free co-product, so no fuel is avoided by making it.
It is NOT the right rate for a **boiler-first / back-pressure** cogen, whose
boiler exists to serve the host's process heat and whose turbine sits in the
let-down path — there most of the fuel is process fuel, and total-fuel-per-MWh
overstates the power-only rate by an order of magnitude (MISO ST_CHP measures
up to 435 MMBtu/MWh on the add-back). Two gates keep the correction on the
topping population, both definitional and both frozen at derive time (rule 23
`[R-FROZEN-DERIVE]`):

1. **Prime mover.** ``CC_CHP`` and ``CT_CHP`` only (the model classes are
   prime-mover-derived, :func:`market_sim.config.plant_taxonomy.classify_plant`).
   ``ST_CHP`` is out of scope for the physical reason above and keeps the
   existing eGRID -> hand-factor chain untouched; it is 0.4-0.8 TWh in MISO,
   far below the rule-20 materiality line.
2. **Unfired-topping thermal share**, :data:`_MAX_THERMAL_SHARE`. A plant whose
   thermal allocation exceeds the physical ceiling of an *unfired* topping
   cycle is firing fuel directly to steam (duct burners / a package boiler),
   which is host process fuel, not power fuel.
3. **Hybrid-cogen dark-fuel share** (miso-122, 2026-08-03). Gates 1-2 are both
   read off eGRID's PLANT-level allocation, which cannot see a **hybrid** — a
   topping CC/CT train *plus* a direct-fired package boiler on the same ORIS
   code. There the plant-average `thermal_share` sits comfortably under the
   0.50 ceiling while a large minority of the fuel never passes through a
   prime mover at all. CEMS resolves it at UNIT grain, so the boiler fuel is
   removed from the rate the power tranches are charged:

       dark_share = CEMS heat input of units reporting heatInput > 0 and
                    grossLoad == 0 over the WHOLE vintage year
                    ------------------------------------------------------
                    CEMS heat input of ALL units at the plant

       heat_rate  = (PLHTIAN + CHPCHTI) * (1 - dark_share) / PLNGENAN

   It is a **share**, never a subtraction of MMBtu: that needs CEMS's fuel
   *composition* to be representative, never CEMS's *level* to equal eGRID's,
   so the denominator stays ``PLNGENAN`` and no re-basing is smuggled in
   alongside the correction. It is measured at the SAME year as the row's eGRID vintage
   (no vintage mixing), it has NO threshold (a plant with no dark units gets
   ``dark_share = 0.0`` and a byte-identical rate, so the gate is a strict
   no-op wherever the phenomenon is absent — rule 5 ``[R-NO-MAGIC]``), and a
   plant whose corrected rate would fall BELOW eGRID's own credited rate is
   flagged ``below_credited`` and excluded rather than corrected, because that
   says the two sources disagree about the plant's boundary.
   Measured 2023 across the five artifact ISOs: MISO 55088 Dearborn 16.6 %
   (515 MW), NYISO 2493 East River 37.5 % (306 MW, ``below_credited`` — see
   above), NEISO 1595 Kendall 1.2 % (206 MW); PJM and CAISO carry none above
   0.1 %. Evidence:
   ``results/calibration/FINDING-miso122-hybrid-cogen-scope-gate-2026-08-03.md``,
   probe ``scripts/probes/_miso122_hybrid_cogen_scope.py``.

Rule 14 `[R-ACCURATE]`'s named "different boundary" exception is what all
three gates implement: outside them the real datum is defined on a boundary
that is not the LP's marginal offer rate, so it is not applied — never
replaced by a guess.

Zero fitted parameters (rule 24 `[R-REGISTRY]`). Nothing here is swept against
a residual; the thermal-share ceiling falls out of the EPA CHP envelope
arithmetic and the heat-rate bands are the repo's existing committed physical
bands.

Governance (rule 13 `[R-MEASURED]`): a plant's power-only heat rate is a
physical property of the machine, the same admissibility class as the CAMPD
min-stable loads, CT run horizons and the CO2 emission rates. It regenerates
for a forward year from the same published pipeline (each eGRID vintage carries
both columns, each CAMPD year carries the unit-grain fuel/gross channels the
dark-fuel gate reads) and responds to changed conditions — a plant that
re-configures its boilers regenerates a different rate. It is an INPUT, not a
measured outcome fed back to close a residual. Per rule 23 it re-derives ONLY
when EPA publishes a new eGRID vintage OR when a **scope gate's logic** changes
on measured grounds, and the re-derivation commit must cite that change — never
a residual.

Output: ``data/raw/_processed-legacy/chp_power_only_heat_rates_{ISO}.csv``, one
row per ``(plant_code, plant_group)``, consumed by
:func:`market_sim.data.fleet.campd_bins.measured_chp_heat_rates` under
``ScenarioConfig.measured_chp_heat_rates``. Only ``flag == "ok"`` rows are
applied; every other plant keeps the existing chain, so the mechanism is
byte-identical off and a strict no-op wherever the measurement does not reach.

Usage::

    python scripts/data/derive_chp_power_only_heat_rates.py --iso MISO
    python scripts/data/derive_chp_power_only_heat_rates.py --iso MISO --no-cems
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.config.constants import (  # noqa: E402
    EGRID_CC_HR_PHYSICAL_CEILING,
)
from market_sim.config.paths import PROCESSED_DIR, RAW_DIR  # noqa: E402
from market_sim.data import campd  # noqa: E402
from market_sim.data.egrid import (  # noqa: E402
    egrid_sheet_name,
    egrid_vintage_for_year,
    egrid_workbook_path,
)
from market_sim.data.egrid_sheets import read_egrid_sheet  # noqa: E402
from scripts.lib.heat_rate_years import (  # noqa: E402
    BACKCAST_YEARS,
    POOLED_YEAR,
    backcast_fleets,
    union_fleet,
)

UNIT_LEVEL_DIR = RAW_DIR / "campd-unit-level"

#: F1 D4: there is no single "applied vintage" any more. Each backcast year's
#: fleet joins its OWN eGRID vintage (``process_eia860._join_egrid_heat_rate``
#: via :func:`market_sim.data.egrid.egrid_vintage_for_year`), so each year's
#: row is computed against THAT vintage — the correction must still come from
#: the same vintage as the incumbent it undoes, and now it does per year.

#: The topping-cycle CHP classes this artifact prices, and the CAMPD
#: ``unitType`` family each draws its validation units from.
TARGET_CLASSES: tuple[str, ...] = ("CC_CHP", "CT_CHP")

#: Physical ceiling on the thermal share of a plant's allocated heat input,
#: ``CHPCHTI / (PLHTIAN + CHPCHTI)``, above which the plant is not an unfired
#: topping cycle. NOT a swept threshold — it is the arithmetic ceiling of the
#: EPA CHP Partnership's gas-turbine CHP envelope (Catalog of CHP Technologies,
#: gas turbine: electric 24-36 % of fuel HHV, useful thermal 30-40 % of fuel,
#: total 65-75 %). eGRID's credit is the fuel a displaced 80 %-efficient boiler
#: would have burned for the same useful thermal, i.e. ``CHPCHTI = T / 0.8``,
#: so an unfired topping cycle's thermal share cannot exceed
#: ``0.40 / 0.8 = 0.50``. A plant above it is firing fuel straight to steam.
_MAX_THERMAL_SHARE: float = 0.50

#: Physical heat-rate band (MMBtu per NET MWh, HHV) the CORRECTED rate must land
#: in, per class. Both bounds are the repo's existing committed physical bands,
#: reused rather than reinvented:
#:   CC_CHP ceiling — :data:`~market_sim.config.constants.EGRID_CC_HR_PHYSICAL_CEILING`
#:     (a combined cycle raises steam from its own topping turbine's exhaust, so
#:     it cannot be less efficient than a bare simple-cycle GT of the same era).
#:   CT_CHP band    — the committed simple-cycle band of the sibling measured
#:     derive ``scripts/data/derive_campd_ct_heat_rates.py`` (``6.0`` / ``25.0``).
#: A DATA-INTEGRITY guard, not a tuning knob: a corrected rate outside the band
#: says the eGRID row's boundaries do not line up with the plant, so the row is
#: written with its measured value and a ``flag`` and excluded from the applied
#: map (the loader reads ``flag == "ok"``).
_HR_BAND: dict[str, tuple[float, float]] = {
    "CC_CHP": (5.5, EGRID_CC_HR_PHYSICAL_CEILING),
    "CT_CHP": (6.0, 25.0),
}

#: Tolerance on "the plant's incumbent heat rate AT THE REPLACEMENT SEAM IS
#: eGRID's credited rate". A plant that fails it carries a boundary repair
#: (``fleet.eia860._apply_egrid_boundary_hr_repairs``) or a ``HEAT_RATE_BINS``
#: fallback instead, so replacing it would change more than the steam credit
#: and the single-delta property would be lost. Compared against
#: :func:`basis_heat_rates`, NOT the shipped rate — see that function for why
#: (the hand factor is a known deterministic in-repo transform that sits after
#: the seam, and comparing against it blinded the check in CAISO/PJM).
_BASIS_TOL: float = 0.005

#: Two-meter agreement band on ``cems_vs_egrid_total`` inside which the CEMS
#: unit-grain fuel SPLIT may be attributed to eGRID's plant total, i.e. the
#: precondition for SCOPE gate 3. Outside it CEMS is not seeing the same
#: machine eGRID is: the derive's own header records three MISO plants (10328,
#: 55096, 55799) whose combustion units sit below the Part-75 reporting
#: threshold, where CEMS meters the boilers and misses the turbines — and there
#: an unguarded dark share runs to 100 % and would drive the rate to zero.
#: NOT a swept threshold: it is the band miso-118 pre-registered for exactly
#: this "do two independent meters describe the same plant" question, reused
#: rather than reinvented (rule 5 ``[R-NO-MAGIC]``).
_CEMS_RECONCILE_BAND: tuple[float, float] = (0.90, 1.10)

_CC_PREFIX = "combined cycle"
_CT_PREFIX = "combustion turbine"


def target_plants(fleet: list) -> dict[tuple[int, str], float]:
    """Return ``{(plant_code, class): capacity MW}`` for a fleet's topping CHP.

    Keyed by the PAIR because one plant can host more than one CHP class, and
    the loader applies the rate per (plant, class) so a mixed facility's
    out-of-scope rows are never repriced. Since F1 D4 the fleet is the union
    of the ISO's backcast fleets over every year, so a cogen that retired
    before 2023 is in the population.
    """
    caps: dict[tuple[int, str], float] = {}
    for gen in fleet:
        if gen.plant_group not in TARGET_CLASSES:
            continue
        code = int(gen.plant_code or 0)
        if code:
            key = (code, gen.plant_group)
            caps[key] = caps.get(key, 0.0) + float(gen.pmax_mw)
    return caps


def fleet_heat_rates(fleet: list) -> dict[tuple[int, str], float]:
    """Return the capacity-weighted heat rate per (plant, class) of a fleet.

    Called on a year's fleet loaded two ways: as the model prices it (the
    ``model_heat_rate`` column — what the artifact replaces), and with the
    legacy hand-factor CHP correction skipped (``basis_heat_rate``) — the
    incumbent AT THE SEAM the measured rate replaces, i.e. after the eGRID join
    and the boundary repairs but before
    :func:`market_sim.data.chp._correct_chp_steam_credit_hr`.

    WHY THE BASIS IS NOT THE MODEL RATE (caiso-147): in the two ISOs that
    carry the hand factor (``CHP_STEAM_CREDIT_HR_CORRECTION_ISOS`` = CAISO,
    PJM) the shipped rate is ``credited x 1.8`` for a sub-8.0 CT_CHP and
    ``max(credited x 1.15, 6.3)`` for a sub-6.0 CC_CHP, so EVERY hand-corrected
    plant fails ``_BASIS_TOL`` against it and the artifact would exclude
    precisely the population the mechanism exists to fix.
    """
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


def egrid_chp_split(vintage: int) -> pd.DataFrame:
    """Return the eGRID plant sheet's CHP heat-input split for a vintage.

    Columns ``plant_code``, ``plant_name``, ``heat_input_electric_mmbtu``
    (``PLHTIAN``), ``heat_input_thermal_mmbtu`` (``CHPCHTI``, 0 where blank),
    ``net_mwh`` (``PLNGENAN``) and ``egrid_heat_rate`` (``PLHTRT``, Btu/kWh ->
    MMBtu/MWh).
    """
    path = egrid_workbook_path(vintage)
    if not path.exists():
        raise SystemExit(f"eGRID workbook not on disk: {path}")
    raw = read_egrid_sheet(
        path,
        egrid_sheet_name("PLNT", vintage),
        ["ORISPL", "PNAME", "PLHTIAN", "CHPCHTI", "PLNGENAN", "PLHTRT"],
    )
    out = pd.DataFrame(
        {
            "plant_code": pd.to_numeric(raw["ORISPL"], errors="coerce"),
            "plant_name": raw["PNAME"].astype(str),
            "heat_input_electric_mmbtu": pd.to_numeric(raw["PLHTIAN"], errors="coerce"),
            "heat_input_thermal_mmbtu": pd.to_numeric(
                raw["CHPCHTI"], errors="coerce"
            ).fillna(0.0),
            "net_mwh": pd.to_numeric(raw["PLNGENAN"], errors="coerce"),
            "egrid_heat_rate": pd.to_numeric(raw["PLHTRT"], errors="coerce") / 1e3,
        }
    )
    return out.dropna(subset=["plant_code"]).drop_duplicates("plant_code")


def cems_annual_heat(
    iso: str, year: int, codes: set[int]
) -> tuple[dict[int, float], dict[int, float]]:
    """Return ``({plant: annual CEMS MMBtu}, {plant: DARK MMBtu})`` for ``year``.

    Two products from one read of the same extract:

    * **total** — the INDEPENDENT validation of eGRID's split: CEMS meters the
      fuel at the stack, so ``PLHTIAN + CHPCHTI`` should reproduce it.
    * **dark** — the heat input of units that report fuel and **zero gross
      load** over the whole year, i.e. fuel that makes no electricity at all.
      This is the hybrid-cogen scope gate's measurement (SCOPE gate 3).

    The dark set is chosen **behaviourally**, never by a ``unitType``
    allowlist: a hand map of "boiler-looking" type strings would be exactly the
    off-registry channel rule 24 ``[R-REGISTRY]`` forbids. ``grossLoad`` is
    null — not zero — for a unit with no gross-load channel at all, which is
    the boiler case, so it is filled before aggregating. Validated at
    miso-122: every dark unit found across the five artifact ISOs is a boiler
    ``unitType`` (100 % of dark fuel, three plants).

    Each state-year extract is narrowed to the ISO's own plants on read, so a
    shared state file cannot leak another ISO's units in. A missing extract
    leaves the plant out of BOTH maps — unvalidated (``NaN``) and uncorrected
    (``dark_fuel_share`` NaN, applied as 0.0, which is the status quo and not
    a claim that the plant has no dark fuel).
    """
    totals: dict[int, float] = {}
    dark: dict[int, float] = {}
    for state in campd.states_for_iso(iso):
        path = UNIT_LEVEL_DIR / f"{state}_{year}.parquet"
        if not path.exists():
            continue
        df = pd.read_parquet(
            path, columns=["facilityId", "unitId", "heatInput", "grossLoad"]
        )
        df["facilityId"] = pd.to_numeric(df["facilityId"], errors="coerce")
        df = df[df["facilityId"].isin(codes)]
        df = df.assign(
            heatInput=df["heatInput"].fillna(0.0),
            grossLoad=df["grossLoad"].fillna(0.0),
        )
        if df.empty:
            continue
        by_unit = df.groupby(["facilityId", "unitId"])[["heatInput", "grossLoad"]].sum()
        is_dark = (by_unit["grossLoad"] <= 0.0) & (by_unit["heatInput"] > 0.0)
        for code, heat in (
            by_unit.groupby(level="facilityId")["heatInput"].sum().items()
        ):
            totals[int(code)] = totals.get(int(code), 0.0) + float(heat)
        for code, heat in (
            by_unit[is_dark].groupby(level="facilityId")["heatInput"].sum().items()
        ):
            dark[int(code)] = dark.get(int(code), 0.0) + float(heat)
    return totals, dark


def plant_table(
    iso: str,
    vintage: int,
    caps: dict[tuple[int, str], float],
    model_hr: dict[tuple[int, str], float],
    basis_hr: dict[tuple[int, str], float],
    egrid: pd.DataFrame,
    cems_heat: dict[int, float],
    cems_dark: dict[int, float],
) -> pd.DataFrame:
    """Build one measured row per ``(plant_code, plant_group)``.

    Every row is written — including the ones the gates reject — so the artifact
    is a complete record of the population and of why each plant is or is not
    corrected. Only ``flag == "ok"`` rows are applied by the loader.
    """
    eg = egrid.set_index("plant_code")
    rows: list[dict] = []
    for (code, klass), cap in sorted(caps.items(), key=lambda kv: -kv[1]):
        model = model_hr.get((code, klass))
        basis = basis_hr.get((code, klass))
        rec: dict = {
            "plant_code": code,
            "plant_group": klass,
            "plant_name": "",
            "class_capacity_mw": round(float(cap), 3),
            "heat_input_electric_mmbtu": float("nan"),
            "heat_input_thermal_mmbtu": float("nan"),
            "net_mwh": float("nan"),
            "thermal_share": float("nan"),
            "heat_rate_credited": float("nan"),
            "heat_rate": float("nan"),
            "model_heat_rate": round(float(model), 4) if model is not None else np.nan,
            "basis_heat_rate": round(float(basis), 4) if basis is not None else np.nan,
            "model_over_measured": float("nan"),
            "cems_heat_mmbtu": round(cems_heat.get(code, float("nan")), 1),
            "cems_dark_heat_mmbtu": round(cems_dark.get(code, 0.0), 1)
            if code in cems_heat
            else float("nan"),
            "dark_fuel_share": float("nan"),
            "heat_rate_all_fuel": float("nan"),
            "cems_vs_egrid_total": float("nan"),
            "flag": "no_egrid_row",
        }
        if code in eg.index:
            r = eg.loc[code]
            elec = float(r["heat_input_electric_mmbtu"])
            therm = float(r["heat_input_thermal_mmbtu"])
            ngen = float(r["net_mwh"])
            total = elec + therm
            rec["plant_name"] = str(r["plant_name"])
            rec["heat_input_electric_mmbtu"] = round(elec, 1)
            rec["heat_input_thermal_mmbtu"] = round(therm, 1)
            rec["net_mwh"] = round(ngen, 1)
            if np.isfinite(total) and total > 0.0:
                rec["thermal_share"] = round(therm / total, 6)
            if np.isfinite(ngen) and ngen > 0.0 and np.isfinite(total):
                credited = elec / ngen
                all_fuel = total / ngen
                cems = cems_heat.get(code)
                if cems is not None and total > 0.0:
                    rec["cems_vs_egrid_total"] = round(cems / total, 5)
                # SCOPE gate 3 — the hybrid-cogen dark-fuel share, applied ONLY
                # where the two meters reconcile. Absent CEMS coverage the share
                # is unmeasured and applied as 0.0: the status quo, never a
                # claim that the plant burns no dark fuel.
                dark_share = 0.0
                reconciled = True
                if cems is not None and cems > 0.0:
                    measured = cems_dark.get(code, 0.0) / cems
                    rec["dark_fuel_share"] = round(measured, 6)
                    lo_r, hi_r = _CEMS_RECONCILE_BAND
                    ratio = rec["cems_vs_egrid_total"]
                    # measured >= 1.0 means the plant's ENTIRE CEMS footprint is
                    # dark, so CEMS never saw the power train and the gate has
                    # no power-train fuel left to divide — degenerate, not a
                    # 100 % correction. Treated exactly like a failed
                    # reconciliation (the same thing is true of it).
                    reconciled = (
                        np.isfinite(ratio) and lo_r <= ratio <= hi_r and measured < 1.0
                    )
                    if reconciled:
                        dark_share = measured
                power_only = all_fuel * (1.0 - dark_share)
                rec["heat_rate_credited"] = round(credited, 4)
                rec["heat_rate_all_fuel"] = round(all_fuel, 4)
                rec["heat_rate"] = round(power_only, 4)
                if model is not None and power_only > 0.0:
                    rec["model_over_measured"] = round(float(model) / power_only, 4)
                rec["flag"] = _flag(
                    klass,
                    credited,
                    power_only,
                    # A zero-heat row (seen in older eGRID vintages, F1) has
                    # no CHP credit to undo: share 0.0 -> "no_chp_credit".
                    therm / total if total > 0.0 else 0.0,
                    basis,
                    dark_unreconciled=(
                        not reconciled and float(rec["dark_fuel_share"]) > 0.0
                    ),
                )
        rows.append(rec)

    out = pd.DataFrame(rows)
    out["iso"] = iso
    out["egrid_vintage"] = vintage
    out["source"] = (
        f"EPA eGRID{vintage} plant sheet {egrid_sheet_name('PLNT', vintage)} "
        f"({egrid_workbook_path(vintage).name}, data/raw/fleet-egrid) — heat_rate = "
        "(PLHTIAN + CHPCHTI) * (1 - dark_fuel_share) / PLNGENAN, i.e. the "
        "model's own incumbent PLHTRT = PLHTIAN/PLNGENAN with eGRID's "
        "published CHP useful-thermal heat-input allocation CHPCHTI added "
        "back, on the SAME net-generation denominator (no gross-to-net factor "
        "is involved), then the hybrid-cogen dark-fuel share removed — the "
        f"share of the plant's CAMPD/CEMS {vintage} heat input burned in units "
        "reporting fuel and ZERO gross load all year, which makes no "
        "electricity and cannot be a topping cycle's co-product "
        "(scripts/probes/_miso122_hybrid_cogen_scope.py), applied only where "
        f"cems_vs_egrid_total is inside {_CEMS_RECONCILE_BAND} so the CEMS "
        "unit split may be attributed to eGRID's plant total. "
        "heat_rate_all_fuel carries the pre-gate value. Validated against "
        "independently metered "
        "CAMPD/CEMS annual heat input (cems_vs_egrid_total). Applied only "
        f"where flag=='ok': topping-cycle classes {'/'.join(TARGET_CLASSES)}, "
        f"thermal_share <= {_MAX_THERMAL_SHARE} (EPA CHP Partnership unfired "
        "gas-turbine envelope), corrected rate at or above eGRID's own "
        "credited rate and inside the class physical band, and the incumbent "
        "rate AT THE REPLACEMENT SEAM (basis_heat_rate — after the eGRID join "
        "and boundary repairs, before the legacy hand factor) equal to "
        "eGRID's credited rate."
    )
    return out


def _flag(
    klass: str,
    credited: float,
    power_only: float,
    thermal_share: float,
    basis: float | None,
    dark_unreconciled: bool = False,
) -> str:
    """Return the applicability flag for one (plant, class) row.

    ``dark_unreconciled`` is set when the plant carries measured dark fuel but
    its two meters do NOT agree (:data:`_CEMS_RECONCILE_BAND`), so SCOPE gate 3
    could not be applied. Such a plant is excluded rather than left silently on
    the uncorrected all-fuel rate: the measurement says there IS host process
    fuel inside its rate, and the data does not say how much.
    """
    if not np.isfinite(power_only) or power_only <= 0.0:
        return "no_rate"
    if thermal_share <= 0.0:
        # eGRID applied no CHP credit, so there is nothing to add back and the
        # corrected rate IS the incumbent. Excluded so the applied map contains
        # only plants the mechanism actually changes (byte-identical no-op).
        return "no_chp_credit"
    if basis is None or abs(credited / basis - 1.0) > _BASIS_TOL:
        # The incumbent is a boundary repair or a HEAT_RATE_BINS fallback, not
        # this eGRID row — replacing it would not be a single steam-credit delta.
        return "basis_mismatch"
    if thermal_share > _MAX_THERMAL_SHARE:
        return "not_unfired_topping"
    if dark_unreconciled:
        return "dark_unreconciled"
    if power_only < credited:
        # SCOPE gate 3's own exclusion: the dark-fuel share removed MORE fuel
        # than eGRID's whole CHP credit, so the corrected rate would sit below
        # the plant's incumbent. The two sources disagree about where the
        # plant's boundary is and neither can be preferred from this data —
        # the plant keeps the existing chain rather than take a rate the
        # correction cannot justify. Measured on NYISO 2493 East River
        # (miso-122): dark share 37.5 % against a 29.6 % eGRID thermal share.
        return "below_credited"
    lo, hi = _HR_BAND[klass]
    if power_only < lo:
        return "below_physical_band"
    if power_only > hi:
        return "above_physical_band"
    return "ok"


def pooled_rows(per_year: pd.DataFrame, iso: str) -> pd.DataFrame:
    """Return one POOLED row per ``(plant_code, plant_group)`` (``year == 0``).

    The pooled rate is the net-generation-weighted mean of the pair's ``ok``
    per-year rates, i.e. ``sum(power-only heat) / sum(PLNGENAN)`` over the
    years whose own row passed every gate — so it inherits every gate and adds
    no parameter. It is what the loader applies in a solve year whose own row
    is not ``ok`` (e.g. a year the plant is missing from that eGRID vintage).
    A pair with no ``ok`` year is written with ``flag == "no_ok_year"``.
    """
    rows: list[dict] = []
    for (code, klass), g in per_year.groupby(["plant_code", "plant_group"], sort=False):
        ok = g[(g["flag"] == "ok") & (g["net_mwh"].astype(float) > 0.0)]
        rec = {
            "plant_code": int(code),
            "plant_group": klass,
            "plant_name": str(next((n for n in g["plant_name"] if n), "")),
            "class_capacity_mw": float(g["class_capacity_mw"].iloc[0]),
            "iso": iso,
            "egrid_vintage": POOLED_YEAR,
            "year": POOLED_YEAR,
        }
        if ok.empty:
            rec.update(heat_rate=float("nan"), flag="no_ok_year")
        else:
            w = ok["net_mwh"].astype(float)
            rec.update(
                heat_rate=round(float((ok["heat_rate"] * w).sum() / w.sum()), 4),
                net_mwh=round(float(w.sum()), 1),
                flag="ok",
            )
        rec["source"] = (
            "POOLED: net-generation-weighted mean of this (plant, class)'s ok "
            "per-year rows (each against its own year's eGRID vintage); "
            f"years {sorted(int(y) for y in ok['year'])}"
        )
        rows.append(rec)
    return pd.DataFrame(rows)


def main(argv: list[str] | None = None) -> int:
    """Derive and write the measured CHP power-only heat-rate artifact."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iso", required=True, help="ISO name, e.g. MISO")
    parser.add_argument(
        "--years",
        nargs="+",
        type=int,
        default=list(BACKCAST_YEARS),
        help=(
            "Backcast years (default 2019-2025). Each year's row is computed "
            "against that year's OWN eGRID vintage (2025 -> eGRID 2024), the "
            "vintage its fleet's incumbent heat rate is joined from."
        ),
    )
    parser.add_argument(
        "--no-cems",
        action="store_true",
        help=(
            "Skip the CAMPD read entirely — faster, but it also DISABLES the "
            "hybrid-cogen dark-fuel scope gate, which is measured from that "
            "same read. Output is a diagnostic, NOT the committed artifact."
        ),
    )
    parser.add_argument(
        "--cc-steam-part-capacity",
        action="store_true",
        help=(
            "Read the fleet with ScenarioConfig.cc_steam_part_capacity ARMED "
            "(miso-126), so the restored combined-cycle STEAM parts are counted "
            "in class_capacity_mw. Rule 23 [R-FROZEN-DERIVE]: this re-derives "
            "on a FLEET/denominator change measured from EIA-860, never on a "
            "residual. It moves capacity ONLY -- the rate is (PLHTIAN + "
            "CHPCHTI) * (1 - dark_share) / PLNGENAN, all eGRID/CEMS plant-grain "
            "quantities that no fleet change can touch."
        ),
    )
    parser.add_argument("--out", default=None, help="Output CSV path override")
    args = parser.parse_args(argv)
    iso = args.iso.upper()

    years = sorted(args.years)
    # F1 D4: the population is the UNION of the ISO's backcast fleets over
    # every year (year-matched vintage + retiree channel), so a cogen retired
    # before 2023 is covered. Each year is loaded twice: as priced (the
    # reported model rate) and at the replacement seam (the basis check).
    flags = {"cc_steam_part_capacity": args.cc_steam_part_capacity}
    fleets = backcast_fleets(iso, years, **flags)
    basis_fleets = backcast_fleets(
        iso, years, apply_chp_steam_credit_correction=False, **flags
    )
    caps = target_plants(union_fleet(fleets))
    if not caps:
        raise SystemExit(f"{iso}: model fleet has no topping-cycle CHP plants")
    codes = {code for code, _ in caps}
    if args.no_cems:
        # The dark-fuel share is measured from the same CAMPD read, so --no-cems
        # is no longer a validation-only switch: it changes the applied value at
        # any hybrid plant. Say so loudly rather than write a quietly different
        # artifact (rule 24 [R-REGISTRY]).
        print(
            "WARNING --no-cems: the hybrid-cogen dark-fuel scope gate is "
            "DISABLED (it reads the CAMPD extract). Applied heat rates revert "
            "to all-fuel at any hybrid plant. Do not commit this output.",
            file=sys.stderr,
        )
    splits: dict[int, pd.DataFrame] = {}
    meters: dict[int, tuple[dict[int, float], dict[int, float]]] = {}
    year_tables: list[pd.DataFrame] = []
    for year in years:
        vintage = egrid_vintage_for_year(year)
        if vintage not in splits:
            splits[vintage] = egrid_chp_split(vintage)
            # CEMS at the SAME year as the eGRID vintage (no vintage mixing).
            meters[vintage] = (
                ({}, {}) if args.no_cems else cems_annual_heat(iso, vintage, codes)
            )
        cems, dark = meters[vintage]
        year_tables.append(
            plant_table(
                iso,
                vintage,
                caps,
                fleet_heat_rates(fleets[year]),
                fleet_heat_rates(basis_fleets[year]),
                splits[vintage],
                cems,
                dark,
            ).assign(year=year)
        )
    per_year = pd.concat(year_tables, ignore_index=True)
    table = pd.concat([pooled_rows(per_year, iso), per_year], ignore_index=True)
    cols = ["plant_code", "year"] + [
        c for c in per_year.columns if c not in ("plant_code", "year")
    ]
    table = table[cols]

    out_path = (
        Path(args.out)
        if args.out
        else (PROCESSED_DIR / f"chp_power_only_heat_rates_{iso}.csv")
    )
    table.to_csv(out_path, index=False)
    print(f"wrote {out_path} ({len(table)} (plant, class, year) rows)")
    print(
        "  ok rows per year: "
        + ", ".join(
            f"{y}:{int(((table['year'] == y) & (table['flag'] == 'ok')).sum())}"
            for y in sorted(set(table["year"]))
        )
    )
    table = table[table["year"] == POOLED_YEAR]

    ok = table[table["flag"] == "ok"]
    for klass in TARGET_CLASSES:
        total = sum(mw for (_, k), mw in caps.items() if k == klass)
        sub = ok[ok["plant_group"] == klass]
        n_total = sum(1 for (_, k) in caps if k == klass)
        if total <= 0.0:
            continue
        covered = float(sub["class_capacity_mw"].sum())
        line = (
            f"  {klass:<8} {len(sub):>3}/{n_total:<3} plants  "
            f"{covered:8.0f}/{total:8.0f} MW ({100.0 * covered / total:5.1f} %)"
        )
        if not sub.empty:
            w = sub["class_capacity_mw"].to_numpy(dtype=float)
            meas = sub["heat_rate"].to_numpy(dtype=float)
            model = sub["model_heat_rate"].to_numpy(dtype=float)
            fin = np.isfinite(model) & (w > 0)
            if fin.any():
                mw_meas = float(np.average(meas[fin], weights=w[fin]))
                mw_model = float(np.average(model[fin], weights=w[fin]))
                line += (
                    f"  model {mw_model:6.2f} vs measured {mw_meas:6.2f} "
                    f"MMBtu/MWh ({100.0 * (mw_model / mw_meas - 1.0):+6.1f} %)"
                )
        print(line)

    val = table[np.isfinite(table["cems_vs_egrid_total"].astype(float))]
    if not val.empty:
        within = int(val["cems_vs_egrid_total"].between(0.99, 1.01).sum())
        print(
            f"  CEMS validation: (PLHTIAN+CHPCHTI) reproduces metered heat "
            f"input within 1 % on {within}/{len(val)} covered plants "
            f"(median ratio {val['cems_vs_egrid_total'].median():.5f})"
        )
    moved = table[table["dark_fuel_share"].fillna(0.0) > 0.0]
    if moved.empty:
        print("  hybrid-cogen scope gate: no plant carries dark fuel — no-op")
    else:
        print(
            f"  hybrid-cogen scope gate: {len(moved)} (plant, class) rows carry "
            f"dark fuel ({float(moved['class_capacity_mw'].sum()):,.0f} MW)"
        )
        for r in moved.sort_values("dark_fuel_share", ascending=False).itertuples(
            index=False
        ):
            print(
                f"    {r.plant_code:<7} {r.plant_group:<7} "
                f"{str(r.plant_name)[:28]:<30} dark {r.dark_fuel_share:6.2%}  "
                f"{r.heat_rate_all_fuel:7.4f} -> {r.heat_rate:7.4f}  "
                f"flag={r.flag}"
            )
    counts = table["flag"].value_counts()
    print("  flag census: " + ", ".join(f"{k}={v}" for k, v in counts.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
