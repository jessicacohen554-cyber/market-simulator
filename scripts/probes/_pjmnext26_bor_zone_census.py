"""PJM-NEXT-26 side card (a), ZERO LP: does real PJM out-of-merit uplift
(Balancing Operating Reserve credits, IMM State of the Market §4) line up with
the keeper's CT location residual (PJM-NEXT-25 card 2)?

Inputs
------
* ``results/phase0/pjm/_pjmnext26_bor_credits_by_zone_type.csv`` -- digitized
  from the IMM SOM Section 4 "Energy Uplift" PDFs
  (``https://www.monitoringanalytics.com/reports/PJM_State_of_the_Market/{y}/{y}-som-pjm-sec4.pdf``),
  one row per printed cell with table and PDF page (page index inside the
  Section-4 PDF). Dimensions:

  - ``unit_type``: Balancing Generator credits by unit type (Table 4-3 for
    2019-2021, Table 4-5 for 2022-2025); credits = printed share x printed
    column total.
  - ``zone``: credits by control zone from "Geography of regional charges and
    credits" (2019 T4-37, 2020 T4-37, 2021 T4-39, 2022 T4-22). This is the
    regionally allocated pool: day-ahead operating reserve + balancing
    operating reserve (reliability + deviation, LOC included), ALL unit
    types. It is not split by unit type. The table is not printed in the
    2023-2025 reports (only East/West region shares are given in prose).
  - ``zone_charges``: the same table's charges column (allocated to real-time
    load, exports and deviations by location) -- a year-specific load proxy.
  - ``zone_x_type``: the only zone x unit-type data the IMM prints: the
    top-10 BOR recipients table (unit name suffix CT/CC/F gives the type,
    the zone column the zone). Partial (13-51 % of BOR); 2019 covers
    July-December only.

* ``results/phase0/pjm/_pjmnext25_ct_location.json`` -- per model zone and
  year, ``real_minus_model_twh`` (real CEMS CT energy minus keeper CT energy).

Zone mapping (IMM control zone -> model zone, following
``market_sim.data.eia930.zonal_shares._PJM_LOAD_ZONE_GROUPS``, IMM spellings
of 2019-2020 and 2021-2022 both listed in ``IMM_TO_MODEL``). One deviation:
EKPC. The load-side map puts EKPC load in PJM_Central_PA, but BOR credits are
booked at the *resource* location and the model places Kentucky plants in
PJM_AEP_Ohio (``data/zone_assignment.py`` state map), which is the basis of
the card-2 plant residual; so EKPC credits go to PJM_AEP_Ohio. ``External``
credits (imports) are dropped and shares renormalized over the eight zones.

Pre-fixed reading (set before the numbers were seen)
----------------------------------------------------
CONFIRMED iff in >= 2 years where both exist, the zone with the most negative
model CT residual (under-run) is among the top-2 zones by real CT BOR credit
share AND every zone with positive residual (over-run) has real credit share
below its load share. Otherwise NOT CONFIRMED.

"Model CT residual" is evaluated under both sign conventions because the
card-2 field is ``real_minus_model``:

* ``literal`` (primary): residual = model - real; negative = model under-runs.
* ``as_published``: residual = real - model as stored in the card-2 JSON /
  RESULT table (negative in ComEd from 2022, the reading the card-(a) brief
  used when it called ComEd the under-run zone).

"Real CT BOR credit share" by zone is not printed; the zone-credit share
(all types; CTs carry the CT share of Balancing Generator credits shown in
``ct_share_of_bg``) is the primary proxy, the top-10 CT credits a secondary.
Load share: ``iso_configs._pjm_config`` zone ``load_share`` (primary) and the
year's charges share (check).

Run: ``.venv/bin/python scripts/probes/_pjmnext26_bor_zone_census.py``
Writes ``results/phase0/pjm/_pjmnext26_bor_zone_census.json``.
"""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CSV_PATH = REPO / "results/phase0/pjm/_pjmnext26_bor_credits_by_zone_type.csv"
CT_JSON = REPO / "results/phase0/pjm/_pjmnext25_ct_location.json"
OUT = REPO / "results/phase0/pjm/_pjmnext26_bor_zone_census.json"
YEARS = list(range(2019, 2026))

IMM_TO_MODEL: dict[str, str] = {
    "ComEd": "PJM_ComEd",
    "COMED": "PJM_ComEd",
    "AEP": "PJM_AEP_Ohio",
    "DAY": "PJM_AEP_Ohio",
    "DEOK": "PJM_AEP_Ohio",
    "DUKE": "PJM_AEP_Ohio",
    "OVEC": "PJM_AEP_Ohio",
    "EKPC": "PJM_AEP_Ohio",
    "ATSI": "PJM_ATSI",
    "APS": "PJM_West_APS",
    "DLCO": "PJM_West_APS",
    "DUQ": "PJM_West_APS",
    "PPL": "PJM_Central_PA",
    "PENELEC": "PJM_Central_PA",
    "PE": "PJM_Central_PA",
    "Met-Ed": "PJM_Central_PA",
    "MEC": "PJM_Central_PA",
    "METED": "PJM_Central_PA",
    "Dominion": "PJM_Dominion",
    "DOM": "PJM_Dominion",
    "PSEG": "PJM_EMAAC",
    "JCPL": "PJM_EMAAC",
    "JCPLC": "PJM_EMAAC",
    "PECO": "PJM_EMAAC",
    "DPL": "PJM_EMAAC",
    "AECO": "PJM_EMAAC",
    "ACEC": "PJM_EMAAC",
    "RECO": "PJM_EMAAC",
    "REC": "PJM_EMAAC",
    "BGE": "PJM_SWMAAC",
    "Pepco": "PJM_SWMAAC",
    "PEPCO": "PJM_SWMAAC",
}
DROP = {"External", "All Zones"}


def load_csv() -> list[dict]:
    """Read the digitized IMM rows as dicts with numeric fields parsed."""
    with CSV_PATH.open() as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["year"] = int(r["year"])
        r["credits_usd_million"] = float(r["credits_usd_million"])
        r["share"] = float(r["share"])
    return rows


def config_load_shares() -> dict[str, float]:
    """Return the eight model zones' static load shares from iso_configs."""
    from market_sim.config.iso_configs import _pjm_config

    return {z.name: z.load_share for z in _pjm_config().zones}


def zone_shares(rows: list[dict], year: int, dimension: str) -> dict[str, float]:
    """Aggregate an IMM per-zone column to model zones, renormalized (External dropped)."""
    agg: dict[str, float] = defaultdict(float)
    for r in rows:
        if r["year"] != year or r["dimension"] != dimension or r["key"] in DROP:
            continue
        agg[IMM_TO_MODEL[r["key"]]] += r["credits_usd_million"]
    tot = sum(agg.values())
    return {z: v / tot for z, v in agg.items()} if tot else {}


def top10_ct_by_zone(rows: list[dict], year: int) -> dict[str, float]:
    """Return top-10-recipient CT BOR credits by model zone as a share of total BOR."""
    out: dict[str, float] = defaultdict(float)
    for r in rows:
        if (
            r["year"] == year
            and r["dimension"] == "zone_x_type"
            and r["key"].endswith("|CT")
        ):
            out[IMM_TO_MODEL[r["key"].split("|")[0]]] += r["share"]
    return dict(out)


def ct_share_of_bg(rows: list[dict], year: int) -> float | None:
    """Return the Combustion Turbine share of Balancing Generator credits."""
    for r in rows:
        if (
            r["year"] == year
            and r["dimension"] == "unit_type"
            and r["key"] == "Combustion Turbine"
        ):
            return r["share"]
    return None


def apply_reading(
    resid: dict[str, float], credit: dict[str, float], load: dict[str, float]
) -> dict:
    """Apply the pre-fixed test for one year and one residual sign convention."""
    under = min(resid, key=resid.get)
    top2 = sorted(credit, key=credit.get, reverse=True)[:2]
    over = [z for z, v in resid.items() if v > 0]
    over_ok = {z: credit.get(z, 0.0) < load[z] for z in over}
    return {
        "under_run_zone": under,
        "top2_credit_zones": top2,
        "under_in_top2": under in top2,
        "over_run_zones_below_load_share": over_ok,
        "all_over_below_load": all(over_ok.values()),
        "pass": under in top2 and all(over_ok.values()),
    }


def main() -> None:
    """Build the per-year comparison and verdict; write the JSON."""
    rows = load_csv()
    ct = json.loads(CT_JSON.read_text())
    load_cfg = config_load_shares()
    out: dict = {
        "what": "PJM-NEXT-26 card (a): IMM BOR credits by zone vs keeper CT location residual. ZERO LP.",
        "zone_mapping": IMM_TO_MODEL,
        "notes": [
            "zone credits = regionally allocated DA OR + BOR (incl. LOC), all unit types; printed 2019-2022 only",
            "IMM prints no full zone x unit-type split; zone_x_type = top-10 BOR recipients only",
            "EKPC credits mapped to PJM_AEP_Ohio (resource location, KY), External dropped",
        ],
        "years": {},
    }
    passes = {"literal": [], "as_published": []}
    for y in YEARS:
        rmm = {r["zone"]: r["real_minus_model_twh"] for r in ct[str(y)]["by_zone"]}
        credit = zone_shares(rows, y, "zone")
        charges = zone_shares(rows, y, "zone_charges")
        rec = {
            "ct_share_of_bg": ct_share_of_bg(rows, y),
            "top10_ct_share_of_bor_by_zone": top10_ct_by_zone(rows, y),
            "by_zone": {
                z: {
                    "real_minus_model_twh": rmm[z],
                    "model_minus_real_twh": round(-rmm[z], 2),
                    "real_credit_share": round(credit[z], 4) if credit else None,
                    "load_share_cfg": load_cfg[z],
                    "charge_share": round(charges[z], 4) if charges else None,
                }
                for z in sorted(rmm)
            },
        }
        if credit:
            lit = {z: -v for z, v in rmm.items()}
            rec["test_literal"] = apply_reading(lit, credit, load_cfg)
            rec["test_as_published"] = apply_reading(rmm, credit, load_cfg)
            rec["test_literal_chargeproxy"] = apply_reading(lit, credit, charges)
            rec["test_as_published_chargeproxy"] = apply_reading(rmm, credit, charges)
            passes["literal"].append((y, rec["test_literal"]["pass"]))
            passes["as_published"].append((y, rec["test_as_published"]["pass"]))
        out["years"][str(y)] = rec
    out["verdict"] = {
        k: {
            "years_tested": [y for y, _ in v],
            "years_pass": [y for y, p in v if p],
            "CONFIRMED": sum(p for _, p in v) >= 2,
        }
        for k, v in passes.items()
    }
    OUT.write_text(json.dumps(out, indent=1))
    print(json.dumps(out["verdict"], indent=1))


if __name__ == "__main__":
    main()
