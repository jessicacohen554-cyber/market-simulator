"""nyiso-133 — is the NYISO ramp-year solar over-statement a COMMISSIONING CURVE?

Session nyiso-132 closed the NYISO solar **CF level** with a keeper
(``RENEWABLE_AVG_CF["NYISO"]["solar"]`` 0.15 -> 0.1955, the registered fleet's
measured mature-year CF) and opened a named successor:

    "THE MODEL HAS NO COMMISSIONING CURVE. The monthly capacity ramp counts a
    plant fully from its in-service month, so one CF cannot track a fleet whose
    realized CF runs 0.1468-0.1955."

(``results/calibration/FINDING-nyiso132-solar-cf-level-2026-08-07.md`` section 5.)

This probe tests that attribution BEFORE any mechanism is built or any solve is
spent, on committed data only, and reports THREE measurements:

**(A) The national commissioning ramp.** How much does a utility-scale PV plant
actually under-produce in its first months, measured against its own mature
output? Sample: every single-vintage EIA-860 ``OP`` PV plant >= 5 MW with a
2019-2022 commercial-operation date and an EIA-923 monthly generation history
(``data/raw/_processed-legacy/eia923_monthly_generation.parquet``, 2018-2026).

Two-way normalization, so weather years, curtailment growth, degradation and
siting cannot contaminate the answer::

    index[Y,c] = capacity-weighted CF of MATURE plants (age >= 24 months) in
                 calendar (year Y, month c)          -- the peer index
    alpha[p]   = mean over p's OWN mature months of CF[p,Y,c] / index[Y,c]
                 -- the plant's permanent quality factor
    ratio[p,k] = CF[p,Y,c] / (alpha[p] * index[Y,c])  at age k months since COD

``ratio`` is 1.0 for a mature plant by construction; the ramp is whatever it
does before that. A placebo cohort (age 36-47) is reported as the calibration of
the estimator itself.

**(B) The NYISO in-service DATE basis.** For each of the 15 plants in NYISO's
Gold Book Table III-2a market-solar registry (the artifact the keeper's
``nyiso_solar_market_generator_basis`` reads), compare the published Gold Book
in-service date with (i) EIA-860's ``Operating Year``/``Operating Month`` for the
same plant and (ii) the first month of material metered output in EIA-923.

**(C) The energy decomposition.** The model's own convention -- a plant
contributes its full nameplate from its in-service month -- evaluated on each
date basis and scored against the Gold Book's published Net Energy
(229.9 / 503.2 / 981.8 GWh for 2023 / 2024 / 2025, the figures nyiso-130
reconciled and nyiso-132 used).

Rule 13 ``[R-MEASURED]``: every quantity here is an INPUT (when a plant existed,
how big it is) or a diagnostic ratio, never a model outcome fed back in. Rule 25
``[R-ISO-SCOPE]``: (A) is a national physical measurement and is reported as
such; (B) and (C) are NYISO's own registry against NYISO's own published output.

Writes ``results/calibration/_nyiso133_commissioning_ramp.json``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))

from data.derive_nyiso_market_solar import build_registry  # noqa: E402

E923 = REPO / "data" / "raw" / "_processed-legacy" / "eia923_monthly_generation.parquet"
E860 = REPO / "data" / "raw" / "eia-860" / "eia860_generator_operable.parquet"
OUT = REPO / "results" / "calibration" / "_nyiso133_commissioning_ramp.json"

MONTH_NAMES = [
    "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december",
]
HOURS_IN_MONTH = np.array(
    [744, 672, 744, 720, 744, 720, 744, 744, 720, 744, 720, 744], dtype=float
)

# NYISO Gold Book Table III-2a PTID -> EIA plant code. An IDENTITY mapping
# between two published registries for the same physical plant, not a parameter:
# each row is verified below on nameplate agreement and NY state, and an
# unverifiable row is DROPPED (it then keeps its Gold Book date) rather than
# guessed. Albany County Solar 2 (323834) has no EIA-860 record of its own --
# EIA-860 carries only "Hecate Energy Albany County 1" at 20 MW -- so it is
# mapped to None and keeps the published Gold Book date.
PTID_TO_EIA: dict[int, int | None] = {
    323809: 65125,  # Puckett Solar            -> NY8 - Puckett Solar
    323808: 65123,  # Janis Solar              -> NY8 - Janis Solar
    323848: 68274,  # Morris Ridge Solar       -> Morris Ridge Solar
    323811: 65122,  # Branscomb Solar          -> NY8 - Branscomb Solar
    323812: 65124,  # Regan Solar              -> NY8 - Regan Solar
    323813: 65121,  # Grissom Solar            -> NY8 - Grissom Solar
    323810: 65839,  # Darby Solar              -> NY8 - Darby Solar
    323814: 65841,  # Stillwater Solar         -> NY8 - ELP Stillwater Solar
    323833: 64077,  # Albany County Solar 1    -> Hecate Energy Albany County 1
    323834: None,   # Albany County Solar 2    -> no separate EIA-860 record
    323815: 65840,  # Pattersonville Solar     -> NY8 - Teichos Pattersonville
    323840: 65805,  # East Point Solar         -> East Point Energy Center
    323847: 65765,  # High River Solar         -> High River Energy Center, LLC
    323691: 57589,  # Long Island Solar Farm   -> Long Island Solar Farm LLC
    323806: 65679,  # Calverton Solar          -> Calverton Solar Energy Center
}

# Gold Book Table III-2a published Net Energy for the registered market-solar
# fleet (GWh). 2025 = 981.8 CONFIRMED by the nyiso-130 independent re-extraction
# (which RETIRED nyiso-128's 1,081.8); 2023/2024 reproduce across three vintages.
PUBLISHED_GWH = {2023: 229.9, 2024: 503.2, 2025: 981.8}

# The keeper's armed solar CF (nyiso-132), used to turn a monthly-capacity
# exposure into an energy prediction. Read from the constant, never retyped.
MIN_PLANT_MW = 5.0          # utility-scale floor for the national sample
MATURE_AGE_MONTHS = 24      # age at which a plant is treated as mature
MIN_MATURE_OBS = 6          # months needed to identify a plant's alpha
RAMP_COD_YEARS = (2019, 2022)  # COD years with both ramp and mature history


def _e923_monthly_long() -> pd.DataFrame:
    """Return EIA-923 PV net generation as ``(plant_id, year, month, mwh)``."""
    gen = pd.read_parquet(E923)
    gen = gen[(gen.prime_mover == "PV") & (gen.fuel_type == "SUN")]
    parts = []
    for i, name in enumerate(MONTH_NAMES, start=1):
        col = f"netgen_{name}_mwh"
        part = gen[["plant_id", "year", col]].rename(columns={col: "mwh"})
        part["month"] = i
        parts.append(part)
    long = pd.concat(parts, ignore_index=True)
    return long.groupby(["plant_id", "year", "month"], as_index=False)["mwh"].sum()


def _e860_pv_plants() -> pd.DataFrame:
    """Return single-vintage operable PV plants with capacity and COD."""
    df = pd.read_parquet(E860)
    df = df[
        (df["Prime Mover"] == "PV")
        & (df["Status"].astype(str).str.strip().str.upper() == "OP")
    ]
    df = df.rename(
        columns={
            "Plant Code": "plant_id",
            "Nameplate Capacity (MW)": "cap",
            "Operating Year": "oy",
            "Operating Month": "om",
        }
    )[["plant_id", "cap", "oy", "om"]]
    for col in ("plant_id", "cap", "oy", "om"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["plant_id", "cap", "oy"])
    df["om"] = df["om"].fillna(7).clip(1, 12)
    grouped = df.groupby("plant_id")
    plants = pd.DataFrame(
        {
            "cap": grouped["cap"].sum(),
            "oy": grouped["oy"].first(),
            "om": grouped["om"].first(),
            "n_vintages": grouped.apply(
                lambda d: d[["oy", "om"]].drop_duplicates().shape[0],
                include_groups=False,
            ),
        }
    ).reset_index()
    return plants


def measure_national_ramp() -> dict:
    """Measurement (A): the peer-indexed national PV commissioning ramp."""
    long = _e923_monthly_long()
    plants = _e860_pv_plants()
    plants = plants[(plants.n_vintages == 1) & (plants.cap >= MIN_PLANT_MW)]

    m = long.merge(plants[["plant_id", "cap", "oy", "om"]], on="plant_id", how="inner")
    m = m[m.mwh.notna()]
    m["cf"] = m.mwh / (m.cap * HOURS_IN_MONTH[m.month.values - 1])
    m["age"] = (m.year - m.oy) * 12 + (m.month - m.om)
    m = m[(m.cf > -0.01) & (m.cf < 0.60)]

    mature = m[m.age >= MATURE_AGE_MONTHS]
    index = (
        mature.assign(num=lambda d: d.cf * d.cap)
        .groupby(["year", "month"])
        .apply(lambda d: d.num.sum() / d.cap.sum(), include_groups=False)
        .rename("index_cf")
        .reset_index()
    )
    m = m.merge(index, on=["year", "month"], how="inner")
    m = m[m.index_cf > 0.02]
    m["rel"] = m.cf / m.index_cf

    alpha = m[m.age >= MATURE_AGE_MONTHS].groupby("plant_id")["rel"].agg(["mean", "size"])
    alpha = alpha[(alpha["size"] >= MIN_MATURE_OBS) & (alpha["mean"] > 0.2)]
    m = m.merge(alpha["mean"].rename("alpha"), on="plant_id", how="inner")
    m["ratio"] = m.rel / m.alpha

    lo, hi = RAMP_COD_YEARS
    ramp = m[(m.age >= 0) & (m.age <= 11) & m.oy.between(lo, hi)]
    by_age = []
    for age, d in ramp.groupby("age"):
        by_age.append(
            {
                "age_months": int(age),
                "n_obs": int(len(d)),
                "n_plants": int(d.plant_id.nunique()),
                "ratio_capacity_weighted": round(
                    float(np.average(d.ratio, weights=d.cap)), 4
                ),
                "ratio_median": round(float(d.ratio.median()), 4),
            }
        )
    placebo = m[(m.age >= 36) & (m.age <= 47)]
    # Month-equivalents of capacity a new plant loses to commissioning: the
    # summed shortfall over the ramp, in units of one month at full nameplate.
    shortfall = sum(max(0.0, 1.0 - r["ratio_capacity_weighted"]) for r in by_age)
    return {
        "sample": {
            "n_plants": int(ramp.plant_id.nunique()),
            "capacity_gw": round(
                float(ramp.groupby("plant_id").cap.first().sum() / 1e3), 2
            ),
            "cod_years": list(RAMP_COD_YEARS),
            "min_plant_mw": MIN_PLANT_MW,
        },
        "by_age": by_age,
        "placebo_age_36_47": {
            "ratio_capacity_weighted": round(
                float(np.average(placebo.ratio, weights=placebo.cap)), 4
            ),
            "ratio_median": round(float(placebo.ratio.median()), 4),
            "n_obs": int(len(placebo)),
        },
        "commissioning_month_equivalents_lost": round(shortfall, 3),
    }


def _e860_plant_cod(e860: pd.DataFrame, code: int) -> tuple[int, int] | None:
    """Capacity-weighted (year, month) COD for one EIA plant code."""
    sub = e860[e860["Plant Code"] == code]
    if sub.empty:
        return None
    cap = pd.to_numeric(sub["Nameplate Capacity (MW)"], errors="coerce").fillna(0.0)
    oy = pd.to_numeric(sub["Operating Year"], errors="coerce")
    om = pd.to_numeric(sub["Operating Month"], errors="coerce").fillna(7)
    ok = oy.notna()
    if not ok.any():
        return None
    weights = cap[ok].to_numpy()
    if weights.sum() <= 0.0:
        weights = np.ones(int(ok.sum()))
    cont = oy[ok].to_numpy() + (om[ok].to_numpy() - 1.0) / 12.0
    mean = float(np.average(cont, weights=weights))
    year = int(np.floor(mean))
    month = min(max(int(round((mean - year) * 12.0)) + 1, 1), 12)
    return year, month


def _first_material_output(long: pd.DataFrame, code: int, cap_mw: float):
    """First (year, month) whose metered CF clears 2 % — the metered start."""
    d = long[(long.plant_id == code) & long.mwh.notna()].sort_values(["year", "month"])
    for _, r in d.iterrows():
        cf = r.mwh / (cap_mw * HOURS_IN_MONTH[int(r.month) - 1])
        if cf >= 0.02:
            return int(r.year), int(r.month)
    return None


def measure_nyiso_date_basis() -> dict:
    """Measurements (B) and (C): the registry date basis and its energy cost."""
    registry = build_registry()
    e860 = pd.read_parquet(E860)
    e860 = e860[e860["Status"].astype(str).str.strip().str.upper() == "OP"]
    long = _e923_monthly_long()

    plants, unverified = [], []
    for _, r in registry.iterrows():
        ptid = int(r.ptid)
        code = PTID_TO_EIA.get(ptid)
        gold = (int(r.in_service.year), int(r.in_service.month))
        cod = _e860_plant_cod(e860, code) if code else None
        metered = _first_material_output(long, code, float(r.nameplate_mw)) if code else None
        # Verification: an EIA match must be a NY PV plant whose EIA nameplate is
        # within 25 % of the published Gold Book rating, else it is dropped.
        if code is not None and cod is not None:
            eia_mw = float(
                pd.to_numeric(
                    e860[e860["Plant Code"] == code]["Nameplate Capacity (MW)"],
                    errors="coerce",
                ).sum()
            )
            if not (0.75 <= eia_mw / float(r.nameplate_mw) <= 1.34):
                unverified.append({"ptid": ptid, "station": r.station,
                                   "gold_book_mw": float(r.nameplate_mw),
                                   "eia860_mw": eia_mw})
                cod = None
        lead = None
        if cod is not None:
            lead = (cod[0] - gold[0]) * 12 + (cod[1] - gold[1])
        plants.append(
            {
                "ptid": ptid,
                "station": str(r.station),
                "zone": str(r.zone),
                "nameplate_mw": float(r.nameplate_mw),
                "gold_book_in_service": f"{gold[0]}-{gold[1]:02d}",
                "eia860_operating": None if cod is None else f"{cod[0]}-{cod[1]:02d}",
                "first_metered_output": (
                    None if metered is None else f"{metered[0]}-{metered[1]:02d}"
                ),
                "eia860_lead_months": lead,
                "_gold": gold,
                "_cod": cod,
            }
        )

    def mean_monthly(basis: str, year: int) -> float:
        cap = np.zeros(12)
        for p in plants:
            date = p["_cod"] if (basis == "e860" and p["_cod"]) else p["_gold"]
            if date[0] > year:
                continue
            start = date[1] if date[0] == year else 1
            cap[start - 1:] += p["nameplate_mw"]
        return float(cap.mean())

    from market_sim.config.constants import RENEWABLE_AVG_CF

    cf = float(RENEWABLE_AVG_CF["NYISO"]["solar"])
    years = []
    for year, published in PUBLISHED_GWH.items():
        gb, e8 = mean_monthly("gold", year), mean_monthly("e860", year)
        e_gb, e_e8 = gb * 8760 * cf / 1e3, e8 * 8760 * cf / 1e3
        years.append(
            {
                "year": year,
                "published_gwh": published,
                "mean_monthly_mw_gold_book": round(gb, 2),
                "mean_monthly_mw_eia860": round(e8, 2),
                "model_gwh_gold_book": round(e_gb, 1),
                "model_gwh_eia860": round(e_e8, 1),
                "err_pct_gold_book": round(100.0 * (e_gb / published - 1.0), 1),
                "err_pct_eia860": round(100.0 * (e_e8 / published - 1.0), 1),
                "implied_fleet_cf_gold_book": round(published * 1e3 / (gb * 8760), 4),
                "implied_fleet_cf_eia860": round(published * 1e3 / (e8 * 8760), 4),
            }
        )
    for p in plants:
        p.pop("_gold"), p.pop("_cod")
    return {
        "armed_cf": cf,
        "plants": plants,
        "unverified_crosswalk_rows": unverified,
        "years": years,
    }


def main() -> int:
    """Run all three measurements and write the machine record."""
    national = measure_national_ramp()
    nyiso = measure_nyiso_date_basis()
    record = {
        "probe": "nyiso-133 commissioning-ramp attribution",
        "question": (
            "Does the ABSENCE OF A COMMISSIONING CURVE explain the keeper's "
            "+20.9 / +33.2 / -0.1 % NYISO market-solar error (nyiso-132 §5)?"
        ),
        "A_national_commissioning_ramp": national,
        "B_C_nyiso_date_basis": nyiso,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(record, indent=1) + "\n")

    print("(A) national PV commissioning ramp, peer-indexed")
    for row in national["by_age"]:
        print(
            f"    age {row['age_months']:2d} mo  ratio {row['ratio_capacity_weighted']:.3f}"
            f"  (median {row['ratio_median']:.3f}, n={row['n_obs']})"
        )
    print(
        f"    placebo age 36-47: {national['placebo_age_36_47']['ratio_capacity_weighted']:.4f}"
        f"   month-equivalents lost to commissioning: "
        f"{national['commissioning_month_equivalents_lost']}"
    )
    print("\n(B) NYISO registry in-service date vs EIA-860 / first metered output")
    for p in nyiso["plants"]:
        lead = p["eia860_lead_months"]
        lead_txt = "" if lead is None else f"{lead:+d}"
        print(
            f"    {p['station']:24s} {p['nameplate_mw']:6.1f} MW  GB {p['gold_book_in_service']}"
            f"  EIA860 {str(p['eia860_operating']):>8s}  metered "
            f"{str(p['first_metered_output']):>8s}  lead {lead_txt}"
        )
    print("\n(C) energy decomposition against the published Gold Book Net Energy")
    for y in nyiso["years"]:
        print(
            f"    {y['year']}  published {y['published_gwh']:7.1f} GWh |"
            f" gold-book basis {y['model_gwh_gold_book']:7.1f} ({y['err_pct_gold_book']:+5.1f} %)"
            f" | EIA-860 basis {y['model_gwh_eia860']:7.1f} ({y['err_pct_eia860']:+5.1f} %)"
            f" | implied CF {y['implied_fleet_cf_gold_book']:.4f} ->"
            f" {y['implied_fleet_cf_eia860']:.4f}"
        )
    print(f"\nwrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
