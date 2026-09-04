"""caiso-245 — G-KEY: the firm import block's corridor split from CAISO's PUBLISHED RA-import capability holdings. ZERO LP.

Pre-registered in ``PRECOMMIT-caiso245-firm-import-allocation-split-2026-09-04.md``
§2 (G-KEY) and §3 (P-1..P-3), pushed before this was computed.

The model splits the DMM annual RA-import capacity (2,323 / 3,371 / 3,371 MW)
between its two firm rows by the published MIC CAPABILITY share north of
Path 15 (46.2 / 46.2 / 46.4 %; ``interchange_config.IMPORT_TRANCHES_BY_YEAR``
comment). caiso-244 located the whole CAISO over-import on that north block.
Form (i) of FINDING-caiso244 §5 asked: what share of RA import capability do
LSEs actually HOLD north vs south? This probe answers from the curated
``ra-import-allocations`` clean datatype (``scripts/data/
curate_ra_import_allocations.py`` over ``data/raw/ra-import-allocations/
CAISO/<year>-holders-of-import-capability.xlsx``), mapping each branch-group
stem to its corridor with the SAME geography the MIC comment and
``CAISO_CORRIDOR_DIBA`` use (an unknown stem is a hard error).

Diagnostic (never a key): the share of branch-group rows flagged
``USED_ALL_CAPABILITY = Yes`` in the companion "used on annual RA plans"
workbooks (May–Sep), read raw — that workbook's single code column
interleaves LSE IDs and branch-group codes, so rows whose code is not a
known branch group are dropped and counted.

STOP RULE (PRECOMMIT §0.4): held north share within 5 points of the MIC share
in every year ⇒ the re-split arm is inert by construction and is NOT built.

Writes ``results/calibration/_caiso245_allocation_split.json``.

Usage:
    PYTHONPATH=.:src uv run python scripts/probes/_caiso245_allocation_split.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

OUT = REPO / "results/calibration/_caiso245_allocation_split.json"
RAW = REPO / "data/raw/ra-import-allocations/CAISO"
YEARS = (2023, 2024, 2025)

#: Branch-group STEMS north of Path 15 — the MIC north list of the
#: ``IMPORT_TRANCHES_BY_YEAR["CAISO"]`` comment (Malin 500 / PACI, COTP, NOB,
#: Cascade, Summit, Round Mountain 230, Cottonwood 230, Northwest 230, Marble,
#: Tracy 230/500, Tracy-TEA, Westley-*, Standiford, Oakdale, New Melones,
#: Rancho Seco/Lake) in the holders workbooks' code vocabulary.
NORTH_STEMS = frozenset(
    {
        "MALIN500", "PACI", "NOB", "COTPISO", "CASCADE", "SUMMIT", "CTW230",
        "NWEST", "MARBLE", "TRACY230", "TRACY500", "TRACYTEA", "STANDIFORD",
        "OAKDALE", "NEWMELONES", "WESTLEY", "RANCHOSECO", "RNDMTN230",
    }
)
#: Branch-group STEMS south of Path 15 ("Merchant" kept south, as the MIC
#: comment does).
SOUTH_STEMS = frozenset(
    {
        "ELDORADO", "IID-SCE", "IID-SDGE", "IPPDCADLN", "MCCLMKTPC", "MCCULLGH",
        "MEADTMEAD", "MEAD", "MEADMKTPC", "MERCHANT", "MKTPCADLN", "MONAIPPDC",
        "NORTHGILA500", "PALOVRDE", "PARKER", "SILVERPK", "SYLMAR-AC", "VICTVL",
        "WSTWGMEAD", "BLYTHE", "GONDIPPDC",
    }
)
#: The MIC north share the model uses today (IMPORT_TRANCHES_BY_YEAR comment).
MIC_NORTH_SHARE = {2023: 0.462, 2024: 0.462, 2025: 0.464}
#: The DMM RA-import capacity the model splits (same comment).
DMM_RA_IMPORT_MW = {2023: 2323.0, 2024: 3371.0, 2025: 3371.0}
STOP_RULE_POINTS = 5.0


def corridor(code: str, strict: bool = True) -> str | None:
    """Map a branch-group code (any ``_ITC``/``_BG``/``_ISL``/``_MSL`` suffix) to its corridor."""
    stem = re.sub(r"_(ITC|BG|ISL|MSL)$", "", str(code).strip().upper())
    if stem in NORTH_STEMS:
        return "WECC_PNW"
    if stem in SOUTH_STEMS:
        return "WECC_DSW"
    if strict:
        raise KeyError(f"unmapped branch group {code!r} — extend the corridor map, never default")
    return None


def holdings(year: int) -> pd.DataFrame:
    """The curated holdings for ``year`` (through the clean seam)."""
    from scripts.lib.clean_io import read_clean

    return read_clean("ra-import-allocations", iso="CAISO", year=year)


def used_diagnostic(year: int) -> dict:
    """Share of branch-group rows flagged used-all by corridor (raw companion workbook)."""
    u = pd.read_excel(
        RAW / f"{year}-import-capability-used-on-annual-resource-adequacy-plans.xlsx",
        header=None,
    )
    hdr = u.index[u[0].astype(str).str.strip() == "MONTH"][0]
    u = u.iloc[hdr + 1 :].rename(columns={0: "month", 1: "code", 2: "used"})
    u = u[u["used"].isin(["Yes", "No"])].copy()
    u["corridor"] = u["code"].map(lambda c: corridor(c, strict=False))
    unmapped = int(u["corridor"].isna().sum())
    ub = u.dropna(subset=["corridor"])
    return {
        "used_all_share_by_corridor": ub.groupby("corridor")["used"]
        .apply(lambda s: round(float((s == "Yes").mean()), 3))
        .to_dict(),
        "rows_by_corridor": ub.groupby("corridor")["used"].size().to_dict(),
        "rows_dropped_non_branch_group_codes": unmapped,
    }


def main() -> None:
    out: dict = {
        "_provenance": {
            "session": "caiso-245",
            "precommit": "PRECOMMIT-caiso245-firm-import-allocation-split-2026-09-04.md §2 G-KEY",
            "holdings_source": "clean ra-import-allocations (CAISO) <- data/raw/ra-import-allocations/CAISO/<year>-holders-of-import-capability.xlsx",
            "used_source": "raw <year>-import-capability-used-on-annual-resource-adequacy-plans.xlsx (diagnostic only)",
            "corridor_map": "branch-group stem -> north list of the IMPORT_TRANCHES_BY_YEAR comment (same geography as CAISO_CORRIDOR_DIBA); unmapped stem = hard error",
            "stop_rule": f"held north share within {STOP_RULE_POINTS} points of the MIC share in every year => arm not built",
            "note": "ZERO LP; nothing armed",
        },
        "years": {},
    }
    for y in YEARS:
        d = holdings(y)
        d["corridor"] = d["branch_group"].map(corridor)
        frac = (
            ((d["end_date"] - d["start_date"]).dt.total_seconds() / 86400.0 + 1 / 24) / 365.0
        ).clip(0.0, 1.0)
        tot = float(d["allocation_mw"].sum())
        north = float(d.loc[d["corridor"] == "WECC_PNW", "allocation_mw"].sum())
        rec = {
            "rows": int(len(d)),
            "lses": int(d["lse"].nunique()),
            "branch_groups": int(d["branch_group"].nunique()),
            "partial_year_rows": int((frac < 0.99).sum()),
            "total_alloc_mw": round(tot, 1),
            "north_mw": round(north, 1),
            "south_mw": round(tot - north, 1),
            "north_share": round(north / tot, 4),
            "mic_north_share": MIC_NORTH_SHARE[y],
            "diff_points": round(100.0 * (north / tot - MIC_NORTH_SHARE[y]), 1),
            "dmm_ra_import_mw": DMM_RA_IMPORT_MW[y],
            "alloc_over_dmm": round(tot / DMM_RA_IMPORT_MW[y], 2),
            "north_bgs_mw": d[d["corridor"] == "WECC_PNW"]
            .groupby("branch_group")["allocation_mw"]
            .sum()
            .round(1)
            .to_dict(),
            "top_bgs_mw": d.groupby("branch_group")["allocation_mw"]
            .sum()
            .sort_values(ascending=False)
            .head(10)
            .round(1)
            .to_dict(),
            **used_diagnostic(y),
        }
        out["years"][y] = rec
        print(
            f"{y}: held {rec['total_alloc_mw']:.0f} MW over {rec['lses']} LSEs; north {rec['north_share']:.1%} "
            f"vs MIC {rec['mic_north_share']:.1%} ({rec['diff_points']:+.1f} pts); alloc/DMM {rec['alloc_over_dmm']}; "
            f"used-all {rec['used_all_share_by_corridor']}"
        )
    out["stop_rule_fires"] = all(
        abs(out["years"][y]["diff_points"]) < STOP_RULE_POINTS for y in YEARS
    )
    out["P1_north_share_le_0p36_every_year"] = all(
        out["years"][y]["north_share"] <= 0.36 for y in YEARS
    )
    out["P2_alloc_ge_dmm_every_year"] = all(
        out["years"][y]["total_alloc_mw"] >= DMM_RA_IMPORT_MW[y] for y in YEARS
    )
    out["P3_north_used_le_south_every_year"] = all(
        out["years"][y]["used_all_share_by_corridor"].get("WECC_PNW", 0)
        <= out["years"][y]["used_all_share_by_corridor"].get("WECC_DSW", 0)
        for y in YEARS
    )
    print(
        f"STOP RULE FIRES: {out['stop_rule_fires']} | P-1 {out['P1_north_share_le_0p36_every_year']} "
        f"| P-2 {out['P2_alloc_ge_dmm_every_year']} | P-3 {out['P3_north_used_le_south_every_year']}"
    )
    OUT.write_text(json.dumps(out, indent=1, default=float) + "\n")
    print(f"wrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
