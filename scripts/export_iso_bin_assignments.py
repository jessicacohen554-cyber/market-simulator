"""Emit an ISO's per-plant bin-assignment rows with per-row source tags.

Non-ERCOT ISOs have no curated ``custom-bin-assignments.csv``; their
per-plant bins are synthesized at runtime by ``fleet.fleet_to_bins`` from the
EIA-860 fleet plus the CAMPD-derived thermal-tranche artifact
(``data/raw/_processed-legacy/thermal_tranches_<ISO>.csv``). This script writes that
synthetic frame out as a committed, reviewable artifact —
``data/raw/_processed-legacy/bin_assignments_<ISO>.csv`` — one row per
``(Plant_Code, Plant_Group)`` with the four tranche shares
(``Pct_Must_Run / Pct_Committed / Pct_Economic / Pct_Peaking``, summing to
100) and a source tag per derived quantity:

* ``Committed_Source`` / ``Peaking_Source`` — ``campd`` when the share is the
  plant's own CAMPD-measured value (``thermal_tranche_overrides`` /
  ``thermal_tranche_peaking``), else ``class_default``.
* ``Must_Run_Source`` — for CHP cogens the dispatched must-run is the
  behind-the-meter host self-supply (``fleet.chp_btm_pct``, sized by the
  plant's EIA-923 sector class); the tag carries the floor's provenance from
  the artifact status (``chp_campd_p2`` / ``chp_eia923_cf``), with
  ``chp_sector_default`` for cogens absent from the artifact. Coal keeps the
  artifact / class value (``campd`` / ``class_default``); other groups carry
  no must-run (``none``).

The emitted ``Pct_Must_Run`` mirrors the dispatch path: CHP rows carry the
sector-keyed BTM share that ``bins_to_fleet`` removes from LP capacity under
``chp_steam_following`` (the steam-following *grid floor* is a min-gen on the
economic tranches, not a capacity share, and lives in the tranche artifact's
``chp_pmin_cf``).

Mixed facilities — one EIA code spanning several fuel classes — are split per
``Plant_Group`` by construction (one row per ``(code, group)``), and flagged
in ``Mixed_Facility`` using the same fuel-class tags as
``scripts/tag_mixed_plants.py``. No synthetic code re-key is performed: the
re-key exists to disambiguate *cross-fuel* plant-keyed data (coal vs gas at
W A Parish), and the ISO fleets this script covers have no such facility
(CAISO's lone mixed code, Glenarm 422, is gas CC + gas CT — same fuel price,
distinct LP bins already).

Usage:
    python scripts/export_iso_bin_assignments.py --iso CAISO
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.data.chp import chp_btm_pct, chp_overrides  # noqa: E402
from market_sim.data.fleet import (  # noqa: E402
    fleet_to_bins,
    load_fleet_from_csv,
    thermal_tranche_overrides,
    thermal_tranche_peaking,
)
from scripts.tag_mixed_plants import _tag  # noqa: E402

_CHP_GROUPS: frozenset[str] = frozenset({"CC_CHP", "CT_CHP", "ST_CHP"})


def _chp_floor_status(iso: str) -> dict[int, str]:
    """Return ``{plant_code: artifact status}`` for the ISO's CHP rows.

    The thermal-tranche artifact is required to tag CHP must-run provenance. An
    absent file is a hard error, never a silent ``{}`` — a missing artifact used
    to drop every CHP ``Must_Run_Source`` to ``chp_sector_default`` unnoticed
    (the pre-W1 ``inputs/processed`` dead path guaranteed it). A present file
    with no CHP rows correctly yields an empty map.
    """
    from market_sim.config.paths import PROCESSED_DIR

    path = PROCESSED_DIR / f"thermal_tranches_{iso}.csv"
    if not path.exists():
        raise SystemExit(
            f"{iso}: thermal-tranche artifact absent: {path} — required for CHP "
            f"floor provenance; build it with "
            f"scripts/data/derive_thermal_tranches.py"
        )
    df = pd.read_csv(path)
    chp = df[df["plant_group"].isin(_CHP_GROUPS)]
    return {int(c): str(s) for c, s in zip(chp["plant_code"], chp["status"])}


def build_bin_assignments(iso: str) -> pd.DataFrame:
    """Return the ISO's bin-assignment rows with per-row source tags."""
    config = ScenarioConfig(iso=iso)
    gens = load_fleet_from_csv(iso, get_iso_config(iso))
    synth = fleet_to_bins(gens, iso, config)
    if synth.empty:
        raise SystemExit(f"{iso}: no thermal plants to bin")

    measured = thermal_tranche_overrides(iso)
    peaking = thermal_tranche_peaking(iso)
    floor_status = _chp_floor_status(iso)
    # CAMPD-p2 floors carry status "ok"; EIA-923 monthly-CF fallbacks carry
    # "eia923_cf" (or "chp_floor_only" when carried forward from a prior
    # derivation window — still a CAMPD p2 measurement).
    _floor_tag = {
        "ok": "chp_campd_p2",
        "chp_floor_only": "chp_campd_p2",
        "eia923_cf": "chp_eia923_cf",
    }

    # Fuel-class tags per plant code, to flag mixed facilities the way
    # tag_mixed_plants.py classifies them.
    tags_by_code: dict[int, set[str]] = {}
    for code, group in zip(synth["Plant_Code"], synth["Plant_Group"]):
        tags_by_code.setdefault(int(code), set()).add(_tag(str(group))[0])

    rows: list[dict] = []
    for _, b in synth.iterrows():
        code, group = int(b["Plant_Code"]), str(b["Plant_Group"])
        key = (code, group)
        pct_mr, pct_mc = float(b["pct_mr"]), float(b["pct_mc"])
        pct_peak, pct_econ = float(b["pct_peak"]), float(b["pct_econ"])
        committed_src = "campd" if key in measured else "class_default"
        peaking_src = "campd" if key in peaking else "class_default"
        if group in _CHP_GROUPS:
            # Mirror the dispatch path (bins_to_fleet under
            # chp_steam_following): the BTM host self-supply replaces the
            # synthetic frame's must-run share; committed and peaking are
            # clamped into the remaining grid share (committed keeps its
            # measured level, the scarcity peak gives way) and the economic
            # band absorbs the difference.
            pct_mr = chp_btm_pct(code, group, iso=iso)
            grid = max(0.0, 100.0 - pct_mr)
            pct_mc = min(pct_mc, grid)
            pct_peak = max(0.0, min(pct_peak, grid - pct_mc))
            pct_econ = max(0.0, grid - pct_mc - pct_peak)
            mr_src = _floor_tag.get(floor_status.get(code, ""), "chp_sector_default")
        elif group == "COAL":
            mr_src = "campd" if key in measured else "class_default"
        else:
            mr_src = "none"
        mixed = tags_by_code.get(code, set())
        rows.append(
            {
                "Plant_Code": code,
                "Plant_Name": str(b["Plant_Name"]),
                "Plant_Group": group,
                "Zone": str(b["ERCOT_Zone"]),
                "Nameplate_MW": round(float(b["capacity_mw"]), 1),
                "Plant_Avg_HR_MMBtu_MWh": round(float(b["hr_weighted"]), 3),
                "Pct_Must_Run": round(pct_mr, 1),
                "Pct_Committed": round(pct_mc, 1),
                "Pct_Economic": round(pct_econ, 1),
                "Pct_Peaking": round(pct_peak, 1),
                "Must_Run_Source": mr_src,
                "Committed_Source": committed_src,
                "Peaking_Source": peaking_src,
                "Mixed_Facility": ("+".join(sorted(mixed)) if len(mixed) > 1 else ""),
            }
        )
    out = (
        pd.DataFrame(rows)
        .sort_values(["Plant_Group", "Plant_Code"])
        .reset_index(drop=True)
    )
    # chp_overrides is keyed per ISO and cached; touch it so a stale artifact
    # fails loudly here rather than at dispatch time.
    chp_overrides(iso)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--iso", default="CAISO")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    iso = args.iso.upper()
    from market_sim.config.paths import PROCESSED_DIR

    out_path = (
        Path(args.out) if args.out else PROCESSED_DIR / f"bin_assignments_{iso}.csv"
    )

    out = build_bin_assignments(iso)
    bad = out[
        (
            out[["Pct_Must_Run", "Pct_Committed", "Pct_Economic", "Pct_Peaking"]].sum(
                axis=1
            )
            - 100.0
        ).abs()
        > 0.25
    ]
    if len(bad):
        raise SystemExit(f"tranche shares do not sum to 100 for:\n{bad.to_string()}")
    out.to_csv(out_path, index=False)

    pd.set_option("display.width", 200)
    print(f"wrote {len(out)} bin rows to {out_path}\n")
    print("measured-vs-default tranche sources (plants / MW):")
    for col in ("Committed_Source", "Peaking_Source", "Must_Run_Source"):
        parts = []
        for src, sub in out.groupby(col):
            parts.append(f"{src}: {len(sub)} / {sub['Nameplate_MW'].sum():,.0f} MW")
        print(f"  {col:<17} {';  '.join(parts)}")
    print("\nby group (capacity-weighted, % of group MW with measured committed):")
    for g, sub in out.groupby("Plant_Group"):
        m = sub[sub["Committed_Source"] == "campd"]["Nameplate_MW"].sum()
        t = sub["Nameplate_MW"].sum()
        print(
            f"  {g:<12} n={len(sub):>3}  {t:>9,.0f} MW  "
            f"measured committed {100.0 * m / t if t else 0.0:5.1f}%"
        )
    mixed = out[out["Mixed_Facility"] != ""]
    if len(mixed):
        print(
            "\nmixed facilities (split per Plant_Group; no re-key needed — "
            "same fuel class data):"
        )
        print(
            mixed[
                [
                    "Plant_Code",
                    "Plant_Name",
                    "Plant_Group",
                    "Nameplate_MW",
                    "Mixed_Facility",
                ]
            ].to_string(index=False)
        )


if __name__ == "__main__":
    main()
