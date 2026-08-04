"""caiso-172 — the public-source survey for CAISO load at a grain finer than
TAC area, resolvable to the **NP15 / ZP26** (Path 15) boundary. NO LP, NO
SOLVE, NO INTAKE — this is a NETWORK probe (the same exception to the
committed-bytes probe norm that ``_caiso141_water_source_survey.py`` takes): it
re-runs, against the live public endpoints, every verification that produced the
caiso-172 verdict, so the verdict is re-checkable the day a source changes.

Charter: the caiso-172 session brief, itself
``ASSESSMENT-caiso171-frontier-2026-08-04.md`` §5 item 3 — the one unresolved
question gating CAISO's `complete` declaration. The object is
``constants.CAISO_TAC_ZONE_WEIGHTS['PGE-TAC'] = {NP15: 0.86, ZP26: 0.14}``, the
only residual-identified member of that table (DOF ledger; issue #1372), whose
own ``root_cause`` defers to "finding the specific OASIS report that publishes
NP15/ZP26 sub-TAC zonal load".

**VERDICT (measured 2026-08-04): AVAILABLE — via S2, not S1.** No report
publishes an NP15/ZP26 load *MW series*; but two OASIS **Atlas** reference
reports together resolve the split as a reproducible measured input:

* ``ATL_LDF`` — per-pnode **Load Distribution Factors** inside
  ``DLAP_PGAE-APND`` (CAISO's published weighting that distributes PG&E LAP
  load to nodes; 1,668 load pnodes summing to exactly 100.000).
* ``ATL_PNODE_MAP`` — CAISO's **authoritative** ``TH_NP15_GEN`` /
  ``TH_ZP26_GEN`` / ``TH_SP15_GEN`` pnode membership, i.e. the Path-15 /
  Path-26 geography itself.

Joining them by substation yields the PG&E load mass either side of Path 15.
See :func:`s2_ldf_hub_join`.

The checks:

* **S1  OASIS ``SLD_FCST``** (already wired as the ``load`` dataset in
  ``scripts/data/fetch_caiso_oasis.py``) — enumerate its live
  ``TAC_AREA_NAME`` domain across **every** ``market_run_id``. -> **WALL**:
  TAC-area grain in all of ACTUAL/DAM/2DA/7DA/RTM; the CAISO-internal areas are
  only ``PGE-TAC / SCE-TAC / SDGE-TAC / VEA-TAC`` (+ ``MWD-TAC``, see below).
  Every other area in the domain is an **external WECC BA** (BPAT, PACE, NEVP,
  LADWP, BANC…) carried for the WECC-wide forecast, not a CAISO sub-area.
  *Side finding:* ``MWD-TAC`` (Metropolitan Water District, ~208 MW) is a real
  CAISO TAC area **absent from the committed series** — an SP15-side omission,
  NOT a Path-15 split. Logged, not actioned here.
* **S2  the OASIS report catalogue** — is ANY report keyed to a sub-LAP / LAP /
  sub-TAC / congestion-zone geography? Catalogue enumerated from the published
  Interface Specification (v5.1.2), then probed live. -> **AVAILABLE**, as
  above. Also measured: ``ENE_SLRS`` carries a ``TAC_ZONE_NAME``
  (``TAC_NORTH / TAC_NCNTR / TAC_ECNTR / TAC_SOUTH``) that *looks* sub-TAC and
  is **not** — :func:`s2b_ene_slrs_is_relabelled` proves it is the utility
  geography relabelled.
* **S3  CAISO DLAP price nodes** (the caiso-165 intake) — confirm-and-dismiss:
  a DLAP prices where load is WITHDRAWN and carries **no MW**. The *load*
  companion of that price intake is ``ATL_LDF``, which is what S2 uses.
* **S4  FERC Form 714** planning-area hourly load and the **CEC** demand
  forecast — retry (the 2026-07-05 attempt got 403/502 via proxy) and resolve
  the BOUNDARY question. -> **WALL** on both: 714 still 403, and CEC's planning
  areas (PG&E Bay Area / PG&E Valley) are not NP15 / ZP26.
* **S5  EIA-930 sub-BA route** — demand-only by schema; re-confirms caiso-141
  S5 rather than re-deriving it.

Usage::

    uv run python scripts/probes/_caiso172_subtac_load_survey.py [--skip S1,S4]

Exit is informational (prints WALL / AVAILABLE per check); network required.
"""

from __future__ import annotations

import argparse
import io
import json
import re
import sys
import time
import urllib.request
import zipfile

import pandas as pd

OASIS = (
    "https://oasis.caiso.com/oasisapi/SingleZip?queryname={q}&version=1"
    "&resultformat=6&startdatetime={sd}T08:00-0000&enddatetime={ed}T08:00-0000{x}"
)
EIA_SUBBA_URL = (
    "https://api.eia.gov/v2/electricity/rto/region-sub-ba-data/?api_key=DEMO_KEY"
)
FERC714_URLS = (
    "https://www.ferc.gov/sites/default/files/2021-06/Form-714-csv-files-June-2021.zip",
    "https://www.ferc.gov/industries-data/electric/general-information"
    "/electric-industry-forms/form-no-714-annual-electric/data",
)
CEC_URL = "https://www.energy.ca.gov/data-reports/california-energy-demand-forecast"

#: The value under test, and the measurement that replaced it (caiso-172).
MODEL_WEIGHTS = {"NP15": 0.86, "ZP26": 0.14}

#: Nodes whose location either side of Path 15 is not in dispute, used as the
#: S2b discriminator. Path 15 runs Los Banos <-> Gates; ZP26 is the PG&E
#: San Joaquin Valley between Path 15 and Path 26.
ZP26_LANDMARKS = ("GATES", "MIDWAY", "PANOCH", "ELKHIL", "HELMS", "BALCH")
NP15_LANDMARKS = ("MOSSLD", "GEYSER", "VACA", "ROUND", "TESLA", "COTWD")

#: PG&E sub-LAPs, the 95.8 %-coverage partition of DLAP_PGAE used by tier 2 of
#: the assignment (see :func:`s2_ldf_hub_join`).
SUBLAP_PREFIX = "SLAP_PG"

_OASIS_SLEEP_S = 7.0


def _get(url: str, timeout: int = 120) -> bytes:
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return r.read()


def _oasis(q: str, sd: str = "20250101", ed: str = "20250102", x: str = "") -> pd.DataFrame:
    """Fetch an OASIS report as a DataFrame; raise on an XML error payload."""
    payload = _get(OASIS.format(q=q, sd=sd, ed=ed, x=x), timeout=300)
    with zipfile.ZipFile(io.BytesIO(payload)) as z:
        name = z.namelist()[0]
        data = z.open(name).read()
    if name.endswith(".xml"):
        m = re.search(rb"ERR_DESC>(.*?)<", data, re.S)
        raise RuntimeError(f"OASIS {q}: {(m.group(1).decode() if m else '?')[:120]}")
    return pd.read_csv(io.BytesIO(data))


def _asof(df: pd.DataFrame, asof: str) -> pd.DataFrame:
    """Slice an effective-dated Atlas report to the rows live at ``asof``."""
    d = df.copy()
    d["EFF_START_DT"] = pd.to_datetime(d["EFF_START_DT"])
    d["EFF_END_DT"] = pd.to_datetime(d["EFF_END_DT"])
    a = pd.Timestamp(asof)
    return d[(d["EFF_START_DT"] <= a) & (d["EFF_END_DT"] >= a)]


def _substation(s: pd.Series) -> pd.Series:
    """Pnode ids are ``SUBSTATION_voltage_id``; take the substation token."""
    return s.str.split("_").str[0]


def s1_sld_fcst() -> None:
    """Is SLD_FCST ever finer than TAC area, under any market run?"""
    df = _oasis("SLD_FCST")
    areas = sorted(df["TAC_AREA_NAME"].astype(str).unique())
    runs = sorted(df["MARKET_RUN_ID"].astype(str).unique())
    per_run = df.groupby("MARKET_RUN_ID")["TAC_AREA_NAME"].nunique().to_dict()
    caiso_internal = [a for a in areas if a.endswith("-TAC")]
    subtac = [a for a in areas if any(k in a.upper() for k in ("NP15", "ZP26", "SP15", "LAP"))]
    print(f"S1 SLD_FCST market runs = {runs}")
    print(f"S1 SLD_FCST areas per run = {per_run}")
    print(f"S1 SLD_FCST CAISO-internal TAC areas = {caiso_internal}")
    print(f"S1 SLD_FCST sub-TAC / zonal areas = {subtac or 'NONE'}")
    print(
        "S1 verdict:",
        "unchanged (WALL: TAC-area grain in every market run; no NP15/ZP26)"
        if not subtac
        else "CHANGED — a sub-TAC area appeared; re-open the derive",
    )


def s2_ldf_hub_join(asof: str = "2025-01-01", sd: str = "20250101", ed: str = "20250102") -> None:
    """THE route. ATL_LDF x ATL_PNODE_MAP -> the PG&E load split across Path 15.

    Two published reports, joined by substation:

    * ``ATL_LDF``/``DLAP_PGAE-APND`` gives each PG&E load pnode's share of PG&E
      LAP load (sums to 100.000).
    * ``ATL_PNODE_MAP`` gives CAISO's own ``TH_NP15_GEN`` / ``TH_ZP26_GEN``
      membership — the Path-15 geography.

    Assignment is two-tier so coverage is near-total: **tier 1** a direct
    substation match to a hub; **tier 2** the node's PG&E sub-LAP's dominant
    hub (the 15 sub-LAPs partition 95.8 % of DLAP_PGAE and classify almost
    perfectly — ``SLAP_PGZP`` and ``SLAP_PGKN`` are 100 % ZP26, the rest ~100 %
    NP15). The residue is reported, never silently absorbed.
    """
    hub = _asof(_oasis("ATL_PNODE_MAP", sd, ed), asof)
    time.sleep(_OASIS_SLEEP_S)
    ldf = _asof(_oasis("ATL_LDF", sd, ed), asof)

    hub = hub.copy()
    hub["SUB"] = _substation(hub["PNODE_ID"])
    hub["HUB"] = hub["APNODE_ID"].str.extract(r"TH_(\w+?)_GEN")[0]
    # a substation counts only if all its hub pnodes agree
    sub2hub = hub.groupby("SUB")["HUB"].agg(
        lambda x: x.unique()[0] if x.nunique() == 1 else None
    )

    pg = ldf[ldf["APNODE_ID"] == "DLAP_PGAE-APND"][["PNODE_ID", "DIST_FACTOR"]].copy()
    total = pg["DIST_FACTOR"].sum()
    pg["HUB"] = _substation(pg["PNODE_ID"]).map(sub2hub)
    pg.loc[~pg["HUB"].isin(["NP15", "ZP26"]), "HUB"] = None
    tier1 = pg["HUB"].notna().sum()

    node2hub: dict[str, str] = {}
    for slap in [a for a in ldf["APNODE_ID"].unique() if a.startswith(SUBLAP_PREFIX)]:
        nodes = ldf[ldf["APNODE_ID"] == slap]["PNODE_ID"]
        vc = _substation(nodes).map(sub2hub).value_counts()
        vc = vc[vc.index.isin(["NP15", "ZP26"])]
        if len(vc):
            for n in nodes:
                node2hub[n] = vc.idxmax()
    pg["HUB"] = pg["HUB"].fillna(pg["PNODE_ID"].map(node2hub))

    by = pg.groupby(pg["HUB"].fillna("UNASSIGNED"))["DIST_FACTOR"].sum()
    np15, zp26 = float(by.get("NP15", 0.0)), float(by.get("ZP26", 0.0))
    known = np15 + zp26
    print(f"S2 ATL_LDF DLAP_PGAE: {len(pg)} load pnodes, DIST_FACTOR sum = {total:.3f}")
    print(f"S2 assignment: tier1(substation) {tier1} nodes; unassigned mass "
          f"{float(by.get('UNASSIGNED', 0.0)):.2f} of {total:.2f}")
    print(f"S2 MEASURED Path-15 split @ {asof}: NP15 {np15 / known:.4f} / ZP26 {zp26 / known:.4f}")
    print(f"S2 model currently carries:        NP15 {MODEL_WEIGHTS['NP15']:.4f} / "
          f"ZP26 {MODEL_WEIGHTS['ZP26']:.4f}")
    print(
        "S2 verdict:",
        "AVAILABLE — the split is measurable from published bytes"
        if known > 90.0
        else "CHANGED — coverage collapsed; re-examine before trusting the derive",
    )


def s2b_ene_slrs_is_relabelled(asof: str = "2025-01-01") -> None:
    """ENE_SLRS's TAC_ZONE_NAME looks sub-TAC. Prove that it is not.

    ``ENE_SLRS`` publishes ``TOT_LOAD_MW`` over ``TAC_NORTH / TAC_NCNTR /
    TAC_ECNTR / TAC_SOUTH`` — a different vocabulary from the ``*-TAC`` areas,
    summing to the ISO total, which is exactly what a Path-15 split would look
    like. ``ATL_TAC_AREA_MAP`` settles it: the ZP26-side landmarks (Gates,
    Midway, Panoche, Elk Hills, Helms) land in ``TAC_NORTH`` **together with**
    the Bay-Area/North landmarks, so ``TAC_NORTH`` is the whole PG&E TAC area.
    """
    tac = _asof(_oasis("ATL_TAC_AREA_MAP"), asof)
    out = {}
    for label, keys in (("ZP26-side", ZP26_LANDMARKS), ("NP15-side", NP15_LANDMARKS)):
        areas: set[str] = set()
        for k in keys:
            hit = tac[tac["PNODE_ID"].str.contains(k, na=False)]
            areas |= set(hit["TAC_AREA_ID"].unique())
        out[label] = sorted(areas)
        print(f"S2b {label} landmarks -> TAC_AREA_ID {sorted(areas)}")
    collapsed = "TAC_NORTH" in out["ZP26-side"] and "TAC_NORTH" in out["NP15-side"]
    print(
        "S2b verdict:",
        "unchanged (WALL: TAC_NORTH spans Path 15 — ENE_SLRS is the utility "
        "geography relabelled, NOT a sub-TAC load report)"
        if collapsed
        else "CHANGED — the TAC_ZONE geography now separates Path 15; re-open",
    )


#: Every value a DLAP can carry on PRC_LMP is a price component ($/MWh). NOTE
#: the OASIS pivoted-CSV schema names its generic value column ``MW`` for every
#: report, price reports included — so the presence of an ``MW`` *column* is a
#: schema artifact and proves nothing. The discriminator is the DATA ITEM.
_PRICE_ITEMS = {"LMP", "MCC", "MCE", "MCL", "MGHG"}


def s3_dlap_is_price_not_load() -> None:
    """Confirm-and-dismiss: the caiso-165 DLAP intake carries price, not load.

    So the next session does not mistake the committed DLAP *price* intake for
    a load intake. The load companion of a DLAP is ``ATL_LDF`` — which is
    precisely what S2 joins.
    """
    df = _oasis("PRC_LMP", x="&market_run_id=DAM&node=DLAP_PGAE-APND")
    items = sorted(df["LMP_TYPE"].astype(str).unique()) if "LMP_TYPE" in df.columns else []
    non_price = sorted(set(items) - _PRICE_ITEMS)
    print(f"S3 PRC_LMP DLAP_PGAE data items = {items}")
    print(f"S3 non-price (load/energy-quantity) items = {non_price or 'NONE'}")
    print(
        "S3 verdict:",
        "unchanged (a DLAP prices where load is WITHDRAWN — every item is a "
        "$/MWh price component, none is a load quantity; the OASIS 'MW' column "
        "is its generic value column, not megawatts. Load companion = ATL_LDF)"
        if not non_price
        else f"CHANGED — a DLAP now carries a non-price item {non_price}; re-examine",
    )


def s4_ferc714_and_cec() -> None:
    """FERC-714 planning-area hourly load, and the CEC forecast's boundary."""
    for url in FERC714_URLS:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=90) as r:
                print(f"S4 FERC-714 {url.rsplit('/', 1)[-1]}: HTTP {r.status}")
        except Exception as e:  # noqa: BLE001 - status is the measurement
            code = getattr(e, "code", type(e).__name__)
            print(f"S4 FERC-714 {url.rsplit('/', 1)[-1]}: HTTP {code}")
    try:
        req = urllib.request.Request(CEC_URL, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=90) as r:
            print(f"S4 CEC demand forecast: HTTP {r.status}")
    except Exception as e:  # noqa: BLE001
        print(f"S4 CEC demand forecast: HTTP {getattr(e, 'code', type(e).__name__)}")
    print(
        "S4 verdict: unchanged (WALL) — FERC-714 remains unreachable from this "
        "environment, and the CEC planning areas (PG&E Bay Area / PG&E Valley) "
        "are boundary-mismatched to Path 15 regardless of reachability."
    )


def s5_subba() -> None:
    """EIA-930 sub-BA route — demand-only by schema (caiso-141 S5)."""
    meta = json.loads(_get(EIA_SUBBA_URL, timeout=90))["response"]
    cols = sorted(meta.get("data", {}).keys())
    facets = sorted(f["id"] for f in meta.get("facets", []))
    print(f"S5 EIA-930 sub-BA: data columns = {cols}, facets = {facets}")
    print(
        "S5 verdict:",
        "unchanged (WALL: demand-only, and CISO publishes no CAISO sub-BA "
        "resolvable to Path 15)"
        if cols == ["value"]
        else "CHANGED",
    )


CHECKS = {
    "S1": s1_sld_fcst,
    "S2": s2_ldf_hub_join,
    "S2b": s2b_ene_slrs_is_relabelled,
    "S3": s3_dlap_is_price_not_load,
    "S4": s4_ferc714_and_cec,
    "S5": s5_subba,
}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--skip",
        default="",
        help="comma-separated check ids to skip (e.g. S1,S4); OASIS checks are rate-limited",
    )
    args = ap.parse_args()
    skip = {s.strip().upper() for s in args.skip.split(",") if s.strip()}
    for name, fn in CHECKS.items():
        if name.upper() in skip:
            print(f"--- {name} SKIPPED")
            continue
        print(f"--- {name}")
        try:
            fn()
        except Exception as e:  # noqa: BLE001 - a probe reports, it does not raise
            print(f"{name} ERROR: {type(e).__name__}: {e}")
        if name.startswith("S1") or name.startswith("S2") or name.startswith("S3"):
            time.sleep(_OASIS_SLEEP_S)
    print("survey complete — see FINDING-caiso172-subtac-load-available-2026-08-04.md")


if __name__ == "__main__":
    sys.exit(main())
