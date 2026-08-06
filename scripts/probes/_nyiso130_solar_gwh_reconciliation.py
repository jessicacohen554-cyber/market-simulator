"""nyiso-130 Priority 2 Phase 0 — reconcile the registered-solar GWh, no solve.

nyiso-129 §5 reported, against interest, that its own 2026-Gold-Book extraction
of the NYISO registered PV market fleet's 2025 Net Energy came to **981.8 GWh**
where nyiso-128 had quoted **1,081.8 GWh** — exactly 100 GWh apart, over what
both sessions agree is the *same 15 units*. nyiso-129 made reconciling the two
a precondition on sizing the CF lever, because the difference moves the arm's
2025 over-removal from 0.33 TWh to 0.23 TWh.

This probe reconciles them by re-extracting Table III-2a from the committed
2026 Gold Book PDF with a parser that is deliberately **stricter about what it
reports than the one it is checking**: it counts every ``PV SUN`` line on the
page, reports the ones the row regex does NOT match (rather than silently
dropping them), and checks for name-key collisions that could make a dict-keyed
extraction lose a unit. It then cross-checks the extracted capacity against the
independently-derived market-solar registry
(``data/raw/reference/nyiso-market-solar-capacity.csv``), which was built from
the same table by a different script for a different purpose.

Rule 13 ``[R-MEASURED]``: a published registry table read as an input. Rule 19
``[R-ONE-MECH]``: this measures the CF-level object; it arms nothing.

Run: ``python scripts/probes/_nyiso130_solar_gwh_reconciliation.py``
Writes ``results/calibration/_nyiso130_solar_gwh_reconciliation.json``.
"""

from __future__ import annotations

import collections
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

GOLD_BOOK_2026 = "2026-Gold-Book-Public.pdf"

# The Table III-2a row shape: in-service date, five numeric capability columns,
# the "PV SUN" fuel/prime-mover pair, then Net Energy (GWh). Identical to the
# nyiso-129 probe's pattern ON PURPOSE — the point is to reproduce that
# extraction independently, not to invent a different reading of the table.
_ROW = re.compile(
    r"(\d{4}-\d{2}-\d{2})\s+([\d,.]+)\s+([\d,.]+)\s+([\d,.]+)\s+([\d,.]+)\s+"
    r"([\d,.]+)\s+PV SUN\s+([\d,.]+)"
)

# The two candidate figures under reconciliation.
NYISO129_FIGURE_GWH = 981.8
NYISO128_FIGURE_GWH = 1081.8
# nyiso-106's independent MIS P-63 daylight-bulge decomposition, quoted in
# PREREG-nyiso128 §2 as a LOWER BOUND on 2025 market-solar energy.
NYISO106_P63_LOWER_BOUND_TWH = 0.994


def extract() -> dict:
    """Re-extract the 2026 Gold Book Table III-2a PV rows, reporting misses."""
    try:
        from pypdf import PdfReader
    except Exception as exc:  # noqa: BLE001 - a probe reports, never crashes
        return {"unavailable": f"pypdf import failed: {exc}"}
    path = REPO_ROOT / "data" / "raw" / "NYISO" / GOLD_BOOK_2026
    if not path.exists():
        return {"unavailable": f"{path} absent"}

    matched: list[dict] = []
    unmatched: list[dict] = []
    for page_no, page in enumerate(PdfReader(str(path)).pages, start=1):
        text = page.extract_text() or ""
        if "PV SUN" not in text:
            continue
        for line in text.split("\n"):
            if "PV SUN" not in line:
                continue
            m = _ROW.search(line)
            if m is None:
                unmatched.append({"page": page_no, "line": " ".join(line.split())})
                continue
            cap = float(m.group(2).replace(",", ""))
            gwh = float(m.group(7).replace(",", ""))
            matched.append(
                {
                    "page": page_no,
                    "name": line.split(m.group(1))[0].strip(),
                    "nameplate_mw": cap,
                    "net_energy_2025_gwh": gwh,
                    "cf_2025": round(gwh * 1000.0 / (cap * 8760.0), 4) if cap else None,
                }
            )

    keys = [u["name"][:60] for u in matched]
    collisions = sorted(k for k, n in collections.Counter(keys).items() if n > 1)
    cap = sum(u["nameplate_mw"] for u in matched)
    gwh = sum(u["net_energy_2025_gwh"] for u in matched)
    return {
        "pv_sun_lines_seen": len(matched) + len(unmatched),
        "rows_matched": len(matched),
        "rows_unmatched": unmatched,
        "name_key_collisions_60char": collisions,
        "total_nameplate_mw": round(cap, 1),
        "total_net_energy_2025_gwh": round(gwh, 1),
        "fleet_cf_2025": round(gwh * 1000.0 / (cap * 8760.0), 4) if cap else None,
        "units": matched,
    }


def registry_capacity_crosscheck() -> dict:
    """Compare the extracted capacity to the derived market-solar registry."""
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.data.nyiso_market_solar import load_market_solar_monthly

    zones = list(get_iso_config("NYISO").zone_names)
    out: dict[str, float] = {}
    for year in (2023, 2024, 2025):
        reg = load_market_solar_monthly("NYISO", year, zones)
        out[str(year)] = round(float(reg[:, -1].sum()), 1)
    return {
        "source": "data/raw/reference/nyiso-market-solar-capacity.csv "
        "(derive_nyiso_market_solar.py, built from the same Table III-2a "
        "for a different purpose)",
        "year_end_registered_mw": out,
    }


def verdict(ext: dict, cross: dict) -> dict:
    """Adjudicate the two figures on the reproduced extraction."""
    if "unavailable" in ext:
        return {"status": "UNAVAILABLE", "reason": ext["unavailable"]}
    total = ext["total_net_energy_2025_gwh"]
    cap_ok = abs(ext["total_nameplate_mw"] - cross["year_end_registered_mw"]["2025"]) < 0.15
    return {
        "status": "RECONCILED",
        "reproduced_total_gwh": total,
        "nyiso129_figure_gwh": NYISO129_FIGURE_GWH,
        "nyiso128_figure_gwh": NYISO128_FIGURE_GWH,
        "agrees_with": "nyiso-129"
        if abs(total - NYISO129_FIGURE_GWH) < 0.15
        else ("nyiso-128" if abs(total - NYISO128_FIGURE_GWH) < 0.15 else "neither"),
        "capacity_crosscheck_passes": bool(cap_ok),
        "third_instrument_nyiso106_p63_lower_bound_twh": NYISO106_P63_LOWER_BOUND_TWH,
        "distance_from_p63_bound_pct": {
            "reproduced": round(
                100.0 * (total / 1000.0 - NYISO106_P63_LOWER_BOUND_TWH)
                / NYISO106_P63_LOWER_BOUND_TWH,
                2,
            ),
            "nyiso128_figure": round(
                100.0 * (NYISO128_FIGURE_GWH / 1000.0 - NYISO106_P63_LOWER_BOUND_TWH)
                / NYISO106_P63_LOWER_BOUND_TWH,
                2,
            ),
        },
        # The arm's own 2025 delivered market-solar energy (PREREG-nyiso128 §2).
        "armed_arm_2025_twh": 0.75,
        "over_removal_2025_twh_on_reproduced": round(total / 1000.0 - 0.75, 3),
        "over_removal_2025_twh_on_nyiso128_figure": round(
            NYISO128_FIGURE_GWH / 1000.0 - 0.75, 3
        ),
    }


def main() -> int:
    """Assemble and write the GWh reconciliation record."""
    ext = extract()
    cross = registry_capacity_crosscheck()
    record = {
        "session": "nyiso-130",
        "phase": "Priority 2 Phase 0 (reconciliation, no solve)",
        "question": (
            "nyiso-129 extracted 981.8 GWh where nyiso-128 quoted 1,081.8 GWh "
            "from the same Table III-2a over the same 15 units."
        ),
        "extraction": ext,
        "capacity_crosscheck": cross,
        "verdict": verdict(ext, cross),
    }
    dest = REPO_ROOT / "results" / "calibration" / "_nyiso130_solar_gwh_reconciliation.json"
    dest.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    v = record["verdict"]
    print(json.dumps({k: val for k, val in record.items() if k != "extraction"}, indent=2))
    print(
        f"\nreproduced {ext.get('total_net_energy_2025_gwh')} GWh over "
        f"{ext.get('total_nameplate_mw')} MW / {ext.get('rows_matched')} units "
        f"-> agrees with {v.get('agrees_with')}"
    )
    print(f"wrote {dest.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
