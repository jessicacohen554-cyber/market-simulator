"""Derive measured per-plant POWER-ONLY heat rates for topping-cycle CHP classes.

The measured replacement for the **steam-credited** heat rate eGRID gives a
cogeneration plant. The model's offer heat rate is eGRID ``PLNT23.PLHTRT``
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

Rule 14 `[R-ACCURATE]`'s named "different boundary" exception is what both
gates implement: outside them the real datum is defined on a boundary that is
not the LP's marginal offer rate, so it is not applied — never replaced by a
guess.

Zero fitted parameters (rule 24 `[R-REGISTRY]`). Nothing here is swept against
a residual; the thermal-share ceiling falls out of the EPA CHP envelope
arithmetic and the heat-rate bands are the repo's existing committed physical
bands.

Governance (rule 13 `[R-MEASURED]`): a plant's power-only heat rate is a
physical property of the machine, the same admissibility class as the CAMPD
min-stable loads, CT run horizons and the CO2 emission rates. It regenerates
for a forward year from the same published pipeline (each eGRID vintage carries
both columns) and responds to changed conditions. It is an INPUT, not a
measured outcome fed back to close a residual. Per rule 23 it re-derives ONLY
when EPA publishes a new eGRID vintage, and the re-derivation commit must cite
that data change.

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

from market_sim.config.constants import (  # noqa: E402
    EGRID_CC_HR_PHYSICAL_CEILING,
)
from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.config.paths import PROCESSED_DIR, RAW_DIR  # noqa: E402
from market_sim.data import campd  # noqa: E402
from market_sim.data.fleet import load_fleet_from_csv  # noqa: E402

UNIT_LEVEL_DIR = RAW_DIR / "campd-unit-level"
EGRID_DIR = RAW_DIR / "fleet-egrid"

#: eGRID vintage the model's own ``heat_rate`` column is joined from
#: (``scripts/data/process_eia860._join_egrid_heat_rate`` reads PLNT23 of this
#: workbook). The correction MUST come from the same vintage: the delta is
#: "eGRID's CHP allocation, undone", and mixing vintages would smuggle a
#: re-basing in alongside it.
DEFAULT_EGRID_VINTAGE: int = 2023
_EGRID_WORKBOOK: dict[int, str] = {
    2022: "egrid2022_data.xlsx",
    2023: "egrid2023_data_rev2.xlsx",
    2024: "egrid2024_data.xlsx",
}

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

_CC_PREFIX = "combined cycle"
_CT_PREFIX = "combustion turbine"


def target_plants(iso: str) -> dict[tuple[int, str], float]:
    """Return ``{(plant_code, class): capacity MW}`` for the ISO's topping CHP.

    Keyed by the PAIR because one plant can host more than one CHP class, and
    the loader applies the rate per (plant, class) so a mixed facility's
    out-of-scope rows are never repriced.
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
    """Return the CURRENT capacity-weighted model heat rate per (plant, class).

    The value the LP prices with today, read through the model's own loader —
    so the artifact records exactly what it replaces, and the basis check below
    compares like with like.
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


def basis_heat_rates(iso: str) -> dict[tuple[int, str], float]:
    """Return the incumbent heat rate AT THE SEAM the measured rate replaces.

    Identical to :func:`model_heat_rates` except that the legacy hand-factor
    CHP correction is skipped — i.e. the eGRID join and the boundary repairs
    have run, but :func:`market_sim.data.chp._correct_chp_steam_credit_hr` has
    not. This is what :func:`apply_measured_chp_heat_rates` actually overwrites
    (it runs first and hands the hand factor a ``skip_ids`` set), so it is the
    rate the basis check below must compare eGRID's credited rate against.

    WHY THIS IS NOT ``model_heat_rates`` (caiso-147): in the two ISOs that
    carry the hand factor (``CHP_STEAM_CREDIT_HR_CORRECTION_ISOS`` = CAISO,
    PJM) the shipped rate is ``credited x 1.8`` for a sub-8.0 CT_CHP and
    ``max(credited x 1.15, 6.3)`` for a sub-6.0 CC_CHP, so EVERY hand-corrected
    plant fails ``_BASIS_TOL`` and the artifact excludes precisely the
    population the mechanism exists to fix. Measured in CAISO: 59 of the 65
    ``basis_mismatch`` rows — 3,089 of 3,186 MW — were excluded by the hand
    factor alone, leaving only the 14 plants it never touched. Comparing at
    the seam restores the check's actual discriminating power: the six genuine
    boundary-repair / ``HEAT_RATE_BINS``-fallback rows still fail it. In an ISO
    without the hand factor (MISO) the two functions are identical and this
    changes nothing.
    """
    fleet = load_fleet_from_csv(
        iso, get_iso_config(iso), apply_chp_steam_credit_correction=False
    )
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
    path = EGRID_DIR / _EGRID_WORKBOOK[vintage]
    if not path.exists():
        raise SystemExit(f"eGRID workbook not on disk: {path}")
    raw = pd.read_excel(
        path,
        sheet_name=f"PLNT{str(vintage)[2:]}",
        skiprows=1,
        usecols=["ORISPL", "PNAME", "PLHTIAN", "CHPCHTI", "PLNGENAN", "PLHTRT"],
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


def cems_annual_heat(iso: str, year: int, codes: set[int]) -> dict[int, float]:
    """Return ``{plant_code: annual CEMS heat input MMBtu}`` for ``year``.

    The INDEPENDENT validation of eGRID's split: CEMS meters the fuel at the
    stack, so ``PLHTIAN + CHPCHTI`` should reproduce it. Each state-year extract
    is narrowed to the ISO's own plants on read, so a shared state file cannot
    leak another ISO's units in. Missing extracts simply leave the plant
    unvalidated (``NaN``) — the validation never gates the applied value.
    """
    totals: dict[int, float] = {}
    for state in campd.states_for_iso(iso):
        path = UNIT_LEVEL_DIR / f"{state}_{year}.parquet"
        if not path.exists():
            continue
        df = pd.read_parquet(path, columns=["facilityId", "heatInput"])
        df["facilityId"] = pd.to_numeric(df["facilityId"], errors="coerce")
        df = df[df["facilityId"].isin(codes)].dropna(subset=["heatInput"])
        if df.empty:
            continue
        for code, heat in df.groupby("facilityId")["heatInput"].sum().items():
            totals[int(code)] = totals.get(int(code), 0.0) + float(heat)
    return totals


def plant_table(
    iso: str,
    vintage: int,
    caps: dict[tuple[int, str], float],
    model_hr: dict[tuple[int, str], float],
    basis_hr: dict[tuple[int, str], float],
    egrid: pd.DataFrame,
    cems_heat: dict[int, float],
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
                power_only = total / ngen
                rec["heat_rate_credited"] = round(credited, 4)
                rec["heat_rate"] = round(power_only, 4)
                if model is not None and power_only > 0.0:
                    rec["model_over_measured"] = round(float(model) / power_only, 4)
                cems = cems_heat.get(code)
                if cems is not None and total > 0.0:
                    rec["cems_vs_egrid_total"] = round(cems / total, 5)
                rec["flag"] = _flag(klass, credited, power_only, therm / total, basis)
        rows.append(rec)

    out = pd.DataFrame(rows)
    out["iso"] = iso
    out["egrid_vintage"] = vintage
    out["source"] = (
        f"EPA eGRID{vintage} plant sheet PLNT{str(vintage)[2:]} "
        f"({_EGRID_WORKBOOK[vintage]}, data/raw/fleet-egrid) — heat_rate = "
        "(PLHTIAN + CHPCHTI) / PLNGENAN, i.e. the model's own incumbent "
        "PLHTRT = PLHTIAN/PLNGENAN with eGRID's published CHP useful-thermal "
        "heat-input allocation CHPCHTI added back, on the SAME net-generation "
        "denominator (no gross-to-net factor is involved). Validated against "
        "independently metered CAMPD/CEMS annual heat input "
        "(cems_vs_egrid_total). Applied only where flag=='ok': topping-cycle "
        f"classes {'/'.join(TARGET_CLASSES)}, thermal_share <= "
        f"{_MAX_THERMAL_SHARE} (EPA CHP Partnership unfired gas-turbine "
        "envelope), corrected rate inside the class physical band, and the "
        "incumbent rate AT THE REPLACEMENT SEAM (basis_heat_rate — after the "
        "eGRID join and boundary repairs, before the legacy hand factor) "
        "equal to eGRID's credited rate."
    )
    return out


def _flag(
    klass: str,
    credited: float,
    power_only: float,
    thermal_share: float,
    basis: float | None,
) -> str:
    """Return the applicability flag for one (plant, class) row."""
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
    lo, hi = _HR_BAND[klass]
    if power_only < lo:
        return "below_physical_band"
    if power_only > hi:
        return "above_physical_band"
    return "ok"


def main(argv: list[str] | None = None) -> int:
    """Derive and write the measured CHP power-only heat-rate artifact."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iso", required=True, help="ISO name, e.g. MISO")
    parser.add_argument(
        "--vintage",
        type=int,
        default=DEFAULT_EGRID_VINTAGE,
        choices=sorted(_EGRID_WORKBOOK),
        help=(
            "eGRID vintage (default 2023 — the vintage the model's own "
            "heat_rate column is joined from)"
        ),
    )
    parser.add_argument(
        "--no-cems",
        action="store_true",
        help="Skip the CAMPD validation column (faster; applied values unchanged)",
    )
    parser.add_argument("--out", default=None, help="Output CSV path override")
    args = parser.parse_args(argv)
    iso = args.iso.upper()

    caps = target_plants(iso)
    if not caps:
        raise SystemExit(f"{iso}: model fleet has no topping-cycle CHP plants")
    codes = {code for code, _ in caps}
    cems = {} if args.no_cems else cems_annual_heat(iso, args.vintage, codes)
    table = plant_table(
        iso,
        args.vintage,
        caps,
        model_heat_rates(iso),
        basis_heat_rates(iso),
        egrid_chp_split(args.vintage),
        cems,
    )

    out_path = (
        Path(args.out)
        if args.out
        else (PROCESSED_DIR / f"chp_power_only_heat_rates_{iso}.csv")
    )
    table.to_csv(out_path, index=False)
    print(f"wrote {out_path} ({len(table)} (plant, class) rows)")

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
    counts = table["flag"].value_counts()
    print("  flag census: " + ", ".join(f"{k}={v}" for k, v in counts.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
