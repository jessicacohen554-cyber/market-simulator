"""miso-97 TASK 1 derive — give MISO real CHP sector data, and size what it moves.

Measurement/derive only: **no LP is built and nothing is solved**. The output is
a per-plant ``chp_sector`` for the ISO plus the in-LP capacity delta that
populating it implies.

THE DEFECT (measured by ``scripts/probes/_caiso128_heat_rate_source_audit.py``
and reported in ``results/calibration/FINDING-caiso128-heat-rate-provenance-2026-07-27.md``):
MISO is the only ISO whose ``thermal_tranches_<ISO>.csv`` carries an EMPTY
``chp_sector`` column, and 0 of its CHP plants appear in the hardcoded
``fleet.CHP_SECTOR_CLASS_BY_PLANT`` (44 plants, 41 of them ERCOT's). So
``data.chp.chp_btm_pct`` falls through to ``CHP_BTM_PCT_BY_SECTOR["merchant"]``
= 35.0 for every MISO CC_CHP/CT_CHP plant and to ``CHP_ST_BTM_PCT`` = 90.0 for
every ST_CHP. Merchant 35.0 is the ONE value in that table with no independent
source (constants.py: "residual-identified, forecast-risk"; DOF item S5 /
issue #1335), while industrial 70 / commercial 65 are grounded in the EIA-923
Schedule-8 CHP fuel allocation. MISO is therefore defaulting its entire CHP
fleet onto the single fitted number.

THE SOURCE, and why it is not the raw EIA-923 ZIPs. ``scripts/data/
derive_thermal_tranches._chp_sector_map`` reads "EIA Sector Number" from the
``f923_<year> (1).zip`` Page-1 workbooks. Those raw archives are NOT committed
(only the derived ``eia923_monthly_generation.parquet`` is, and it carries no
sector column), so that path cannot be re-run in-session. The identical
attribute is committed on disk in the EIA-860 plant sheet
(``data/raw/eia-860/eia860_plant.parquet``, columns ``Sector`` / ``Sector
Name``), on the SAME 1-7 taxonomy (1 Electric Utility, 2 IPP Non-CHP, 3 IPP
CHP, 4 Commercial Non-CHP, 5 Commercial CHP, 6 Industrial Non-CHP, 7
Industrial CHP), so it maps through the same ``_EIA_SECTOR_CLASS`` table.

``--validate`` is the load-bearing check that the two sources are the same
attribute rather than two plausible ones: it replays the EIA-860 sector onto
the four peer ISOs whose committed ``chp_sector`` was derived from EIA-923 and
reports the agreement rate. Measured 2026-07-27: **232/232 plants, 100 %, all
four ISOs, zero plants missing from EIA-860** — so this is the same measured
EIA sector attribute read off a different committed release, not a substitute
estimator. That makes the swap a rule-14 ``[R-ACCURATE]`` replacement of an
unsourced default by a measured value and a rule-24 ``[R-REGISTRY]`` SHRINK
(one fewer plant falling to the fitted merchant number), NOT a new degree of
freedom.

Note the ST_CHP consequence, which is a behaviour change and is reported
explicitly: ``chp_btm_pct`` returns the 90.0 ``CHP_ST_BTM_PCT`` only when the
plant has NO sector (or when the ISO is ERCOT). Populating MISO's sectors
therefore moves MISO ST_CHP off 90.0 and onto its measured sector share — which
is exactly how PJM/NEISO/NYISO ST_CHP already behave. No code change is needed
for that and no per-ISO literal is introduced (rule 25 ``[R-ISO-SCOPE]``).

Usage:
    PYTHONPATH=.:src .venv/bin/python scripts/probes/_miso97_chp_sector_btm.py
    ... --validate                       # peer agreement vs the 923-derived column
    ... --iso PJM                        # any ISO
    ... --plants                         # per-plant detail
    ... --write                          # patch chp_sector into the ISO artifact
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(1, str(ROOT / "src"))

from market_sim.config.constants import (  # noqa: E402
    CHP_BTM_PCT_BY_SECTOR,
    CHP_ST_BTM_PCT,
)
from market_sim.config.paths import EIA_860_DIR, PROCESSED_DIR  # noqa: E402

# EIA-860 plant "Sector" -> the BTM sector class chp_btm_pct keys on. Identical
# mapping to scripts/data/derive_thermal_tranches._EIA_SECTOR_CLASS (which reads
# the same 1-7 taxonomy off EIA-923 Page 1); duplicated rather than imported so
# this instrument stays runnable without the raw f923 ZIPs that module needs.
_EIA_SECTOR_CLASS: dict[int, str] = {
    1: "merchant",
    2: "merchant",
    3: "merchant",
    4: "commercial",
    5: "commercial",
    6: "industrial",
    7: "industrial",
}

_CHP_GROUPS: tuple[str, ...] = ("CC_CHP", "CT_CHP", "ST_CHP")

# ISOs whose committed thermal_tranches chp_sector column was derived from the
# EIA-923 Page-1 workbooks — the control set for --validate.
_PEER_ISOS: tuple[str, ...] = ("PJM", "CAISO", "NYISO", "NEISO")


def eia860_sector_class() -> dict[int, str]:
    """Return ``{plant_code: sector_class}`` from the EIA-860 plant sheet.

    Reads the committed ``eia860_plant.parquet`` ``Sector`` column and maps it
    through :data:`_EIA_SECTOR_CLASS`. Plants with a null sector are omitted, so
    a caller that misses a plant keeps whatever default it already had.
    """
    df = pd.read_parquet(EIA_860_DIR / "eia860_plant.parquet")
    sub = df[["Plant Code", "Sector"]].dropna()
    out: dict[int, str] = {}
    for code, sector in sub.itertuples(index=False):
        klass = _EIA_SECTOR_CLASS.get(int(sector))
        if klass is not None:
            out[int(code)] = klass
    return out


def validate_against_peers(sector: dict[int, str]) -> pd.DataFrame:
    """Replay the EIA-860 sector onto the peers' 923-derived ``chp_sector``.

    Agreement here is what licenses using EIA-860 as the source for an ISO whose
    923-derived column is empty: it shows the two releases carry the same
    measured attribute rather than two independent guesses.
    """
    rows = []
    for iso in _PEER_ISOS:
        path = PROCESSED_DIR / f"thermal_tranches_{iso}.csv"
        if not path.exists():
            continue
        df = pd.read_csv(path)
        if "chp_sector" not in df.columns:
            continue
        sub = df[df["chp_sector"].notna()]
        n = agree = missing = 0
        for r in sub.itertuples(index=False):
            got = sector.get(int(r.plant_code))
            if got is None:
                missing += 1
                continue
            n += 1
            agree += int(got == r.chp_sector)
        rows.append(
            {
                "iso": iso,
                "plants_923": len(sub),
                "matched": n,
                "agree": agree,
                "pct": 100.0 * agree / n if n else float("nan"),
                "absent_from_860": missing,
            }
        )
    return pd.DataFrame(rows)


def chp_fleet(iso: str, year: int | None) -> pd.DataFrame:
    """Return one row per (plant, CHP class) with the fleet's own nameplate.

    Built through the model's own ``load_fleet_from_csv`` so ``pmax`` is the
    capacity the BTM pull-out is actually applied to. The pull-out itself is NOT
    applied here (it lives in ``offer_curves.plant_cf_bands`` /
    ``fleet.assembly.bins_to_fleet``, gated on ``chp_steam_following``), so these
    are pre-hold-out nameplates.
    """
    from market_sim.data.fleet import load_fleet_from_csv

    rows = []
    for g in load_fleet_from_csv(iso, year=year):
        if (g.plant_group or "") not in _CHP_GROUPS:
            continue
        rows.append(
            {
                "plant_code": int(g.plant_code),
                "plant_group": str(g.plant_group),
                "pmax": float(g.pmax_mw),
            }
        )
    if not rows:
        return pd.DataFrame(columns=["plant_code", "plant_group", "pmax"])
    return (
        pd.DataFrame(rows)
        .groupby(["plant_code", "plant_group"], as_index=False)["pmax"]
        .sum()
    )


def proposed_btm_pct(group: str, sector: str | None, iso: str) -> float:
    """The share :func:`market_sim.data.chp.chp_btm_pct` would return.

    Mirrors that function's resolution order exactly for the no-per-plant-override
    case, so the "proposed" column is what the model would do once the artifact
    carries a sector — not a re-implementation of the policy.

    ``sector`` is normalised with an ``isinstance(str)`` test rather than
    ``is None``: these values round-trip through an object-dtype DataFrame
    column, where pandas stores a missing entry as ``NaN``, and ``NaN is None``
    is False. Testing identity instead silently sent every unreachable ST_CHP
    plant down the sector branch and reported 35.0 where the model returns the
    90.0 ``CHP_ST_BTM_PCT`` — a 452 MW error, 425 MW of it one plant.
    """
    if not isinstance(sector, str) or not sector:
        return CHP_ST_BTM_PCT if group == "ST_CHP" else CHP_BTM_PCT_BY_SECTOR["merchant"]
    if group == "ST_CHP" and iso.upper() == "ERCOT":
        return CHP_ST_BTM_PCT
    return CHP_BTM_PCT_BY_SECTOR.get(sector, CHP_BTM_PCT_BY_SECTOR["merchant"])


def artifact_codes(iso: str) -> set[int]:
    """Return the plant codes the ISO's tranche artifact can deliver a sector for.

    ``data.chp.chp_overrides`` is the only ISO-generic sector channel, and it
    keys its map on ``plant_code`` ALONE — not on ``(plant_code, plant_group)``.
    That matters here: 19 MISO CHP plants sit in the artifact under a different
    ``plant_group`` than the fleet assigns them (a plant EIA-860 vintages as
    ST_CHP whose artifact row says CT_CHP, and so on), and every one of them
    still receives its sector. Scoping reachability by the (code, group) pair
    understates the change by ~380 MW.

    Only CHP-group rows are counted: the derive writes ``chp_sector`` on those
    rows only, so a plant whose sole artifact row is COAL (e.g. MISO 1393)
    genuinely cannot be reached. A CHP plant absent from the artifact entirely
    keeps falling through to the default; every peer has the same structural
    gap, so that is accepted structure rather than a MISO defect.
    """
    path = PROCESSED_DIR / f"thermal_tranches_{iso.upper()}.csv"
    if not path.exists():
        return set()
    art = pd.read_csv(path, usecols=["plant_code", "plant_group"])
    return {
        int(c)
        for c, g in art.itertuples(index=False)
        if str(g) in _CHP_GROUPS
    }


def baseline_sector_by_code(iso: str) -> dict[int, str]:
    """Return ``{plant_code: chp_sector}`` as the artifact carried it at git HEAD.

    The baseline must come from the COMMITTED file, not from a live
    ``chp_btm_pct`` call: once ``--write`` has patched the working-tree
    artifact that function returns the SOURCED share for both sides and every
    delta collapses to zero. Reading HEAD makes this probe report the same
    numbers before and after the patch is applied.
    """
    import subprocess
    from io import StringIO

    rel = f"data/raw/_processed-legacy/thermal_tranches_{iso.upper()}.csv"
    blob = subprocess.run(
        ["git", "show", f"HEAD:{rel}"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    art = pd.read_csv(StringIO(blob))
    if "chp_sector" not in art.columns:
        return {}
    return {
        int(c): str(s)
        for c, g, s in zip(art["plant_code"], art["plant_group"], art["chp_sector"])
        if str(g) in _CHP_GROUPS and isinstance(s, str) and s
    }


def build(iso: str, year: int | None) -> pd.DataFrame:
    """Join the ISO's CHP fleet to the HEAD-baseline share and the sourced one."""
    base = baseline_sector_by_code(iso)
    sector = eia860_sector_class()
    fleet = chp_fleet(iso, year)
    codes = artifact_codes(iso)
    fleet["in_artifact"] = [int(c) in codes for c in fleet["plant_code"]]
    # A plant outside the artifact cannot be reached by the sector channel, so
    # its "sourced" share must stay at whatever it resolves to today.
    fleet["sector_860"] = [
        sector.get(int(c)) if ok else None
        for c, ok in zip(fleet["plant_code"], fleet["in_artifact"])
    ]
    fleet["sector_860_fleet"] = [sector.get(int(c)) for c in fleet["plant_code"]]
    fleet["btm_today"] = [
        proposed_btm_pct(str(g), base.get(int(c)), iso)
        for c, g in zip(fleet["plant_code"], fleet["plant_group"])
    ]
    fleet["btm_proposed"] = [
        proposed_btm_pct(str(g), s, iso)
        for g, s in zip(fleet["plant_group"], fleet["sector_860"])
    ]
    fleet["btm_fleetwide"] = [
        proposed_btm_pct(str(g), s, iso)
        for g, s in zip(fleet["plant_group"], fleet["sector_860_fleet"])
    ]
    fleet["inlp_today"] = fleet["pmax"] * (1.0 - fleet["btm_today"] / 100.0)
    fleet["inlp_proposed"] = fleet["pmax"] * (1.0 - fleet["btm_proposed"] / 100.0)
    fleet["inlp_fleetwide"] = fleet["pmax"] * (1.0 - fleet["btm_fleetwide"] / 100.0)
    fleet["delta_mw"] = fleet["inlp_proposed"] - fleet["inlp_today"]
    return fleet


def _wavg(values: pd.Series, weights: pd.Series) -> float:
    tot = float(weights.sum())
    return float((values * weights).sum() / tot) if tot > 0 else float("nan")


def report(df: pd.DataFrame, iso: str) -> None:
    """Print the sector mix, the implied per-class shares and the MW delta."""
    print(f"\n=== {iso}: EIA-860 sector coverage of the CHP fleet ===")
    print("(reachable = in the tranche artifact, the only ISO-generic sector channel)")
    cov = df.groupby("plant_group").apply(
        lambda g: pd.Series(
            {
                "plants": g["plant_code"].nunique(),
                "mw": g["pmax"].sum(),
                "has_860_sector": int(g["sector_860_fleet"].notna().sum()),
                "reachable": int(g["in_artifact"].sum()),
                "mw_reachable": float(g.loc[g["in_artifact"], "pmax"].sum()),
                "mw_unreachable": float(g.loc[~g["in_artifact"], "pmax"].sum()),
            }
        ),
        include_groups=False,
    )
    cov["pct_mw_reachable"] = 100.0 * cov["mw_reachable"] / cov["mw"]
    print(cov.round(1).to_string())

    print(f"\n=== {iso}: sector mix (plants / MW, whole CHP fleet) ===")
    mix = (
        df[df["sector_860_fleet"].notna()]
        .groupby(["plant_group", "sector_860_fleet"])
        .agg(plants=("plant_code", "nunique"), mw=("pmax", "sum"))
    )
    print(mix.round(1).to_string())
    tot = df[df["sector_860_fleet"].notna()].groupby("sector_860_fleet").agg(
        plants=("plant_code", "nunique"), mw=("pmax", "sum")
    )
    tot["pct_mw"] = 100.0 * tot["mw"] / tot["mw"].sum()
    print("\n-- fleet total --")
    print(tot.round(1).to_string())

    print(f"\n=== {iso}: BTM share and in-LP capacity, today vs sourced ===")
    rows = []
    for grp, g in df.groupby("plant_group"):
        rows.append(
            {
                "class": grp,
                "plants": g["plant_code"].nunique(),
                "nameplate_mw": g["pmax"].sum(),
                "btm_today_%": _wavg(g["btm_today"], g["pmax"]),
                "btm_sourced_%": _wavg(g["btm_proposed"], g["pmax"]),
                "inlp_today_mw": g["inlp_today"].sum(),
                "inlp_sourced_mw": g["inlp_proposed"].sum(),
                "delta_mw": g["delta_mw"].sum(),
            }
        )
    out = pd.DataFrame(rows).set_index("class")
    out.loc["TOTAL"] = {
        "plants": df["plant_code"].nunique(),
        "nameplate_mw": df["pmax"].sum(),
        "btm_today_%": _wavg(df["btm_today"], df["pmax"]),
        "btm_sourced_%": _wavg(df["btm_proposed"], df["pmax"]),
        "inlp_today_mw": df["inlp_today"].sum(),
        "inlp_sourced_mw": df["inlp_proposed"].sum(),
        "delta_mw": df["delta_mw"].sum(),
    }
    out["delta_%"] = 100.0 * out["delta_mw"] / out["inlp_today_mw"]
    print(out.round(1).to_string())

    unreach = df.loc[~df["in_artifact"], "pmax"].sum()
    if unreach > 0:
        head = df["inlp_fleetwide"].sum() - df["inlp_today"].sum()
        print(
            f"\n{unreach:,.0f} MW ({100.0 * unreach / df['pmax'].sum():.1f} % of CHP "
            f"nameplate) sits OUTSIDE the tranche artifact and keeps today's "
            f"default share. Were every plant reachable the total in-LP delta "
            f"would be {head:,.0f} MW instead of {df['delta_mw'].sum():,.0f} MW."
        )


def write_artifact(df: pd.DataFrame, iso: str) -> None:
    """Patch the derived ``chp_sector`` column into the ISO's tranche artifact.

    Only the ``chp_sector`` cell is written, and only for plants the EIA-860
    sheet covers; every other column (including ``chp_pmin_cf``, which the same
    artifact carries and which this lane does not touch) is preserved byte-for-
    byte from the committed file.
    """
    path = PROCESSED_DIR / f"thermal_tranches_{iso.upper()}.csv"
    art = pd.read_csv(path)
    if "chp_sector" not in art.columns:
        raise SystemExit(f"{path.name} carries no chp_sector column")
    # Keyed by plant_code onto CHP-group rows, mirroring how chp_overrides
    # resolves a sector (plant_code alone); a plant whose fleet group differs
    # from its artifact row's group must still receive it.
    sector = {
        int(c): s
        for c, s in zip(df["plant_code"], df["sector_860_fleet"])
        if isinstance(s, str)
    }
    before = int(art["chp_sector"].notna().sum())
    art["chp_sector"] = [
        sector.get(int(c), existing) if str(g) in _CHP_GROUPS else existing
        for c, g, existing in zip(
            art["plant_code"], art["plant_group"], art["chp_sector"]
        )
    ]
    after = int(art["chp_sector"].notna().sum())
    art.to_csv(path, index=False)
    print(f"\nwrote {path}: chp_sector filled {before} -> {after} rows")


def main() -> None:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--iso", default="MISO")
    ap.add_argument("--year", type=int, default=None, help="EIA-860 CHP vintage year")
    ap.add_argument("--validate", action="store_true", help="peer agreement check")
    ap.add_argument("--plants", action="store_true", help="per-plant detail")
    ap.add_argument("--write", action="store_true", help="patch the ISO artifact")
    ap.add_argument("--csv-out", default=None)
    args = ap.parse_args()

    sector = eia860_sector_class()
    print(f"EIA-860 plant sheet: {len(sector)} plants carry a Sector")

    if args.validate:
        v = validate_against_peers(sector)
        print("\n=== EIA-860 Sector vs the peers' EIA-923-derived chp_sector ===")
        print(v.round(1).to_string(index=False))
        n = int(v["matched"].sum())
        a = int(v["agree"].sum())
        print(f"TOTAL matched={n} agree={a} ({100.0 * a / n:.1f} %)")

    df = build(args.iso, args.year)
    report(df, args.iso)

    if args.plants:
        print(f"\n=== {args.iso}: per-plant ===")
        cols = [
            "plant_code",
            "plant_group",
            "pmax",
            "sector_860",
            "btm_today",
            "btm_proposed",
            "delta_mw",
        ]
        print(df.sort_values("delta_mw")[cols].round(1).to_string(index=False))

    if args.csv_out:
        df.to_csv(args.csv_out, index=False)
        print(f"\nwrote {args.csv_out}")

    if args.write:
        write_artifact(df, args.iso)


if __name__ == "__main__":
    main()
