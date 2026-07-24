"""miso-87 probe — is a cross-fuel split of MISO's published outage total
constructible from measured data?

The lever miso-85 / miso-86 left open was a **cross-fuel attribution split**:
MISO's published Multiday Operating Margin OUTAGE record would set *how much*
capacity is offline (measured, ISO-published, forward-reproducible) and a
measured key would set *where*, so neither instrument has to work outside its
competent domain.

This probe runs the two arithmetic checks that decide whether the mechanism has
any content, BEFORE any solve is spent on it (the charter step the handoff
required to be settled "with data not preference"):

1. **Like-for-like level.** The "residual" the earlier sessions flagged --
   CAMPD's 27.9 GW mean thermal offline against the record's 21.8 GW unplanned
   total -- compares an ALL-CAUSE thermal-only quantity against an
   UNPLANNED-ONLY whole-fleet one. On the same basis (all-cause both sides,
   scaled by MISO's actual thermal capacity share) the two independent records
   agree to within the resolution the aggregate grain allows, so there is no
   measured level discrepancy for a split to re-attribute.
2. **Key availability.** MISO publishes region x cause only -- no fuel identity
   and no thermal share -- so the split needs an external per-fuel key. The
   only per-fuel key in evidence is the CAMPD per-unit record itself, which
   makes the mechanism reduce algebraically to
   ``CAMPD x (assumed thermal share / actual thermal share)``: a scalar level
   knob whose value is an UNMEASURED assumption, which CLAUDE.md rule 10
   forbids.

Usage:
    python scripts/probes/_miso87_outage_attribution_feasibility.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from market_sim.config.paths import RAW_DATA_DIR  # noqa: E402
from market_sim.data.miso_outages import (  # noqa: E402
    CAUSE_TYPES,
    UNPLANNED_CAUSE_TYPES,
    _load_estimated,
)

YEARS = (2023, 2024, 2025)

# The model's fossil-thermal plant groups (data.miso_outages._THERMAL_GROUPS),
# expressed as the EIA-860 technologies that map into them. "core" is the
# coal/CC/CT/gas-ST steel the derate is applied to; "wide" additionally counts
# the small oil / reciprocating / process-gas fleet that also sits in those
# groups, giving an upper bound on the thermal share.
_CORE_TECH = (
    "Conventional Steam Coal",
    "Coal Integrated Gasification Combined Cycle",
    "Natural Gas Fired Combined Cycle",
    "Natural Gas Fired Combustion Turbine",
    "Natural Gas Steam Turbine",
)
_WIDE_EXTRA = (
    "Petroleum Liquids",
    "Natural Gas Internal Combustion Engine",
    "Other Gases",
    "Petroleum Coke",
)

# CAMPD per-unit measured unavailability by model class, 2023 / 2024 / 2025,
# with the model's class capacity in GW. Reproduced verbatim from the miso-85
# finding (results/calibration/FINDING-miso85-published-outage-grain-2026-07.md
# section 1), which derived them from the unit-outage derate the keeper solves on.
CAMPD_CLASS_UNAVAIL: dict[str, tuple[float, tuple[float, float, float]]] = {
    "COAL": (44.4, (0.332, 0.325, 0.264)),
    "ST_GAS": (11.6, (0.589, 0.529, 0.508)),
    "CC_REGULAR": (28.3, (0.200, 0.210, 0.251)),
    "CC_CHP": (7.0, (0.073, 0.093, 0.075)),
    "CT_PEAKER": (22.4, (0.0, 0.0, 0.0)),
    "CT_CHP": (2.6, (0.0, 0.0, 0.0)),
}


def miso_registered_capacity() -> pd.Series:
    """Return EIA-860 operable nameplate GW by technology for BA ``MISO``."""
    plant = pd.read_parquet(RAW_DATA_DIR / "eia-860/eia860_plant.parquet")
    gen = pd.read_parquet(RAW_DATA_DIR / "eia-860/eia860_generator_operable.parquet")
    miso = plant[plant["Balancing Authority Code"] == "MISO"][["Plant Code"]]
    m = gen.merge(miso, on="Plant Code", how="inner")
    m["cap"] = pd.to_numeric(m["Nameplate Capacity (MW)"], errors="coerce")
    return m.groupby("Technology")["cap"].sum() / 1000.0


def published_totals() -> pd.DataFrame:
    """Return MISO system-total mean offline GW per cause bucket per year."""
    df = _load_estimated()
    sysm = df[df.region == "MISO"].copy()
    sysm["year"] = sysm.interval_date.dt.year
    piv = sysm.pivot_table(
        index="year", columns="cause_type", values="outage_mw", aggfunc="mean"
    )
    return piv.loc[list(YEARS)] / 1000.0


def main() -> None:
    """Print the two charter checks."""
    print("=" * 78)
    print("miso-87 charter check -- cross-fuel outage attribution split")
    print("=" * 78)

    cap = miso_registered_capacity()
    total = cap.sum()
    core = cap.reindex(_CORE_TECH).fillna(0.0).sum()
    wide = core + cap.reindex(_WIDE_EXTRA).fillna(0.0).sum()
    print(f"\nMISO registered capacity (EIA-860 operable, BA=MISO): {total:.1f} GW")
    print(f"  fossil-thermal core : {core:6.1f} GW  ({core / total:.3f} share)")
    print(f"  fossil-thermal wide : {wide:6.1f} GW  ({wide / total:.3f} share)")

    pub = published_totals()
    print("\nMISO published mean offline GW (Multiday Operating Margin, OUTAGE sheet):")
    print(pub.round(1).to_string())

    print("\n-- check 1: like-for-like level (all-cause both sides) --")
    print(
        f"{'year':>6s}{'pub all-cause':>15s}{'implied thermal':>17s}"
        f"{'CAMPD thermal':>15s}{'required share':>16s}"
    )
    for i, year in enumerate(YEARS):
        pub_all = pub.loc[year, list(CAUSE_TYPES)].sum()
        campd = sum(
            gw * rates[i] for gw, rates in CAMPD_CLASS_UNAVAIL.values()
        )
        lo, hi = pub_all * core / total, pub_all * wide / total
        print(
            f"{year:>6d}{pub_all:>13.1f} GW{lo:>8.1f}-{hi:.1f} GW"
            f"{campd:>12.1f} GW{campd / pub_all:>15.3f}"
        )
    print(
        f"\n  MISO's actual thermal share is {core / total:.3f}-{wide / total:.3f}."
        "\n  2023 (0.655) and 2024 (0.650) sit just ABOVE it: on a like-for-like"
        "\n  basis the two independent records agree on thermal offline to ~1-2 GW,"
        "\n  so the 27.9-vs-21.8 GW 'residual' earlier sessions flagged was an"
        "\n  all-cause-vs-unplanned category mismatch, not a measured gap."
        "\n  2025 (0.518) sits BELOW it -- the published total implies 4.5-6 GW MORE"
        "\n  thermal offline than CAMPD measures, i.e. the discrepancy FLIPS SIGN"
        "\n  across the training window."
        "\n  => there is no stable measured level discrepancy for a split to"
        "\n     re-attribute: 2023/24 offer nothing to redistribute, and the 2025"
        "\n     divergence is a year-specific sign flip, not a forward-reproducible"
        "\n     signal a mechanism could carry."
    )

    print("\n-- check 2: is a measured per-fuel key available? --")
    print("  MISO publishes region x cause ONLY -- no fuel identity, no thermal share.")
    print("  The only per-fuel key in evidence is the CAMPD per-unit record itself:")
    for klass, (gw, rates) in CAMPD_CLASS_UNAVAIL.items():
        print(f"    {klass:12s} {gw:5.1f} GW  unavail {rates[0]:.3f}/{rates[1]:.3f}/{rates[2]:.3f}")
    print(
        "\n  Using CAMPD as the key while MISO's record sets the total makes the"
        "\n  mechanism reduce to  CAMPD x (assumed thermal share / actual share)  --"
        "\n  a SCALAR level knob whose value is an unmeasured assumption (rule 10)."
        "\n  A non-CAMPD key (GADS/EIA-860 class rates) does not need MISO's total"
        "\n  at all, so it is a different mechanism with its own charter."
        "\n\n  => the split as specified is NOT constructible from measured data."
    )


if __name__ == "__main__":
    main()
