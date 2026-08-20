"""Derive the measured NYISO per-plant CHP behind-the-meter electric share.

The identification (nyiso-147, rule 13 [R-MEASURED] / rule 14 [R-ACCURATE]):
a CHP plant's grid-delivered share is the ratio of two independent published
meters —

    grid_share = NYISO Gold Book net energy / EIA-923 net generation
    btm_pct    = 100 x clip(1 - grid_share, 0, 1)

* **Numerator** — NYISO Load & Capacity Data ("Gold Book") Table III-2a
  "Net Energy GWh": the ISO's own settlement-metered energy per station for
  the prior calendar year (`data/raw/NYISO/2023-NYCA-Generators.xlsx` →
  CY2022, `2024-NYCA-Generators.xlsx` → CY2023,
  `2025-NYCA-Existing-Generating-Facilities.xlsx` → CY2024).
* **Denominator** — EIA-923 Page-1 net generation (gross minus station
  service — includes host on-site consumption) per plant-year, from the
  committed `data/raw/_processed-legacy/eia923_monthly_generation.parquet`.

The difference between the two meters IS the electricity that never reached
the NYISO grid (host self-supply, plus any non-NYISO delivery — for Linden
Cogen the Bayway host and the PJM side of its dual market, which the model's
NYC zone equally never sees). Both meters regenerate every year and respond
to changed host arrangements, so the share passes rule 13's forward test; it
replaces `constants.CHP_BTM_PCT_BY_SECTOR` sector defaults whose own comment
declares them residual-identified ("merchant": 35.0 — "no independent source
yet").

Ratios are pooled over CY2022-2024 **pairwise** (a year enters only when both
meters carry the plant), so a thin EIA-923 vintage (Selkirk CY2023) cannot
skew the share. Pooling across years is the plant-physical-property reading
the `chp-btm-share` datatype already uses. Only plants with a PTID-verified
station mapping (below) receive a row; a CHP plant absent from the Gold Book
resource table (campus/industrial cogens that are not NYISO market resources:
Cornell 50368, Riverbay 52168, Ticonderoga 54099, World Generation X 54131,
and the sub-5 MW tail) keeps the sector default — absence is weaker evidence
than a meter, so no value is written for it.

Output: ``data/raw/_processed-legacy/chp_btm_share_measured_NYISO.csv``,
consumed by the fleet build / BTM add-back / benchmark under
``ScenarioConfig.nyiso_chp_btm_measured`` (default off; NYISO-only, rule 25).

Rule 23 [R-FROZEN-DERIVE]: re-run only when a new Gold Book edition or
EIA-923 vintage lands — never against a residual.

Usage:
    PYTHONPATH=.:src python scripts/data/derive_nyiso_chp_btm_share.py
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
RAW = REPO / "data" / "raw"
OUT = RAW / "_processed-legacy" / "chp_btm_share_measured_NYISO.csv"

#: Gold Book edition file -> the calendar year its "Net Energy GWh" column
#: reports (each edition reports the PRIOR year's settlement energy).
GOLD_BOOK_EDITIONS: dict[int, str] = {
    2022: "NYISO/2023-NYCA-Generators.xlsx",
    2023: "NYISO/2024-NYCA-Generators.xlsx",
    2024: "NYISO/2025-NYCA-Existing-Generating-Facilities.xlsx",
}

#: EIA plant code -> exact Gold Book Table III-2a station names (verbatim,
#: stable across the 2023/2024/2025 editions — verified nyiso-147). PTIDs
#: cited for the join's audit trail; the name is the join key because PTID
#: is unique per unit while the GWh cell is reported per station block.
GOLD_BOOK_STATIONS: dict[int, tuple[str, list[str]]] = {
    54547: (
        "Sithe Independence Station",
        [
            "Independence GS1",
            "Independence GS2",
            "Independence GS3",
            "Independence GS4",
        ],
    ),  # PTID 24169-24172, Zone C
    50006: ("Linden Cogen Plant", ["Linden Cogen"]),  # PTID 23786, Zone J
    56259: (
        "Empire Generating Co LLC",
        ["Empire CC1", "Empire CC2"],
    ),  # PTID 323656/323658, Zone F
    10725: ("Selkirk Cogen", ["Selkirk-I", "Selkirk-II"]),  # PTID 23801/23799, Zone F
    54914: (
        "Brooklyn Navy Yard Cogeneration",
        ["Brooklyn Navy Yard"],
    ),  # PTID 23515, Zone J
    54041: (
        "Lockport Energy Associates LP",
        ["Lockport CC1", "Lockport CC2", "Lockport CC3"],
    ),  # PTID 323769-323771, Zone A
    50458: ("Indeck Corinth Energy Center", ["Indeck-Corinth"]),  # PTID 23802, Zone F
    54114: (
        "Kennedy International Airport Cogen",
        ["KIAC_JFK (BTM:NG)"],
    ),  # PTID n/a (BTM-flagged, still settlement-metered), Zone J
    10617: ("CH Resources Beaver Falls", ["Beaver Falls"]),  # PTID 23983, Zone E
    54076: ("Indeck Olean Energy Center", ["Indeck-Olean"]),  # PTID 23982, Zone A
    50451: ("Indeck Yerkes Energy Center", ["Indeck-Yerkes"]),  # PTID 23781, Zone A
    50449: (
        "Indeck Silver Springs Energy Center",
        ["Indeck-Silver Springs"],
    ),  # PTID 23768, Zone C
    50450: ("Indeck Oswego Energy Center", ["Indeck-Oswego"]),  # PTID 23783, Zone C
    54149: (
        "Stony Brook Cogen Plant",
        ["Stony Brook   (BTM:NG)"],
    ),  # PTID 24151, Zone K
    2493: (
        "East River",
        ["East River 1", "East River 2", "East River 6", "East River 7"],
    ),  # PTID 323558/323559/23660/23524, Zone J
    10025: ("RED-Rochester, LLC", ["Red Rochester (BTM:NG)"]),  # PTID 323720, Zone B
}


def _gold_book_gwh(cy: int) -> dict[int, float | None]:
    """Per-plant Gold Book net energy (GWh) for calendar year ``cy``."""
    path = RAW / GOLD_BOOK_EDITIONS[cy]
    df = pd.read_excel(path, sheet_name="Table III-2a", header=6)
    name_col = [c for c in df.columns if "Station" in str(c)][0]
    names = df[name_col].astype(str).str.strip()
    gwh = pd.to_numeric(df["GWh"], errors="coerce")
    out: dict[int, float | None] = {}
    for code, (_, stations) in GOLD_BOOK_STATIONS.items():
        sel = names.isin([s.strip() for s in stations])
        if not sel.any():
            out[code] = None  # station absent from this edition
            continue
        vals = gwh[sel]
        # Station blocks report either one station-total cell (footnote (G))
        # or per-unit cells; the NaN-safe sum covers both conventions.
        out[code] = float(vals.sum()) if vals.notna().any() else None
    return out


def _eia923_gwh() -> pd.DataFrame:
    g = pd.read_parquet(RAW / "_processed-legacy" / "eia923_monthly_generation.parquet")
    g = g[g["plant_id"].isin(GOLD_BOOK_STATIONS)]
    ann = g.groupby(["plant_id", "year"])["netgen_annual_mwh"].sum() / 1000.0
    return ann.unstack("year")


def main() -> None:
    eia = _eia923_gwh()
    gb = {cy: _gold_book_gwh(cy) for cy in GOLD_BOOK_EDITIONS}
    rows = []
    for code, (name, stations) in GOLD_BOOK_STATIONS.items():
        gb_sum = eia_sum = 0.0
        years = []
        detail = {}
        for cy in GOLD_BOOK_EDITIONS:
            g = gb[cy].get(code)
            e = (
                float(eia.loc[code, cy])
                if code in eia.index
                and cy in eia.columns
                and pd.notna(eia.loc[code, cy])
                else None
            )
            detail[cy] = (g, e)
            # pairwise: a year pools only when BOTH meters carry the plant
            # with a positive EIA denominator.
            if g is not None and e is not None and e > 0.0:
                gb_sum += g
                eia_sum += e
                years.append(cy)
        if not years:
            continue
        grid_share = gb_sum / eia_sum
        btm_pct = 100.0 * min(1.0, max(0.0, 1.0 - grid_share))
        rows.append(
            {
                "plant_code": code,
                "plant_name": name,
                "gb_stations": "; ".join(stations),
                "years_pooled": "-".join(str(y) for y in years),
                "gb_gwh_pooled": round(gb_sum, 1),
                "eia923_gwh_pooled": round(eia_sum, 1),
                "grid_share": round(grid_share, 4),
                "btm_pct": round(btm_pct, 2),
                "source": (
                    "NYISO Gold Book Table III-2a Net Energy GWh (2023/2024/2025 "
                    "editions -> CY2022/2023/2024) / EIA-923 Page-1 net generation "
                    "(eia923_monthly_generation.parquet); pairwise-pooled; "
                    "derive_nyiso_chp_btm_share.py (nyiso-147)"
                ),
            }
        )
    out = pd.DataFrame(rows).sort_values("plant_code")
    OUT.write_text(out.to_csv(index=False))
    print(f"wrote {OUT} ({len(out)} rows)")
    print(
        out[
            [
                "plant_code",
                "plant_name",
                "years_pooled",
                "gb_gwh_pooled",
                "eia923_gwh_pooled",
                "grid_share",
                "btm_pct",
            ]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()
