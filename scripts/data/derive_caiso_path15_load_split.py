"""Derive the MEASURED split of CAISO PG&E TAC-area load across **Path 15**
(model zones ``NP15`` / ``ZP26``), from CAISO OASIS published bytes.

This replaces the residual-identified ``constants.CAISO_TAC_ZONE_WEIGHTS
['PGE-TAC'] = {NP15: 0.86, ZP26: 0.14}`` — the only residual-identified member
of that table (DOF ledger; issue #1372) — with a reproducible measured input.
Identified by caiso-172; the source survey that found the route (and walled
every alternative) is ``scripts/probes/_caiso172_subtac_load_survey.py``.

RULE 23 ``[R-FROZEN-DERIVE]`` — **this script is frozen against residuals.** It
re-derives ONLY when its source bytes change (CAISO republishes the Atlas
reports seasonally). It must never be re-run, re-parameterised or re-tiered
because a backcast residual moved. Any commit that changes the estimator cites
the source-data change.

THE CONSTRUCTION
----------------
No CAISO report publishes an NP15/ZP26 load **MW series** — S1/S2b/S3/S4/S5 of
the survey wall every such route, and ``SLD_FCST`` (the wired ``load`` dataset)
is TAC-area grain under every market run. What CAISO *does* publish is the two
halves of the split, as effective-dated Atlas reference reports:

* ``ATL_LDF`` — per-pnode **Load Distribution Factors** inside
  ``DLAP_PGAE-APND``: CAISO's own published weighting for distributing PG&E LAP
  load onto nodes. The factors sum to exactly 100.000 over 1,668 load pnodes.
* ``ATL_PNODE_MAP`` — CAISO's **authoritative** ``TH_NP15_GEN`` /
  ``TH_ZP26_GEN`` / ``TH_SP15_GEN`` pnode membership: the Path-15 / Path-26
  geography itself, as CAISO defines it for its own trading hubs.

Joining them by **substation** (pnode ids are ``SUBSTATION_voltage_id``) puts
each unit of PG&E load mass on one side of Path 15. Assignment is two-tier so
coverage is near-total, and the residue is reported rather than absorbed:

1. **tier 1 — direct substation match.** A substation is usable only if every
   hub pnode at it agrees on one hub (ambiguous substations are dropped, not
   majority-voted). Covers ~44 % of the LDF mass: load substations that also
   host a generator.
2. **tier 2 — PG&E sub-LAP dominant hub.** The 15 ``SLAP_PG*`` sub-LAPs
   partition 95.8 % of ``DLAP_PGAE`` and classify almost perfectly against
   tier 1: ``SLAP_PGZP`` (the ZP26 sub-LAP) and ``SLAP_PGKN`` (Kern) are
   **100 %** ZP26, and every other sub-LAP is ~100 % NP15 (``SLAP_PGF1`` /
   Fresno is 71 NP15 : 3 ZP26). A node with no tier-1 match inherits its
   sub-LAP's dominant hub.
3. **residue.** ~2.2 LDF points reach neither tier. They are reported in the
   output and EXCLUDED from the normalisation — never silently folded into a
   side.

Windows are **day-weighted** within the calendar year: the Atlas reports are
effective-dated and CAISO reissues them seasonally, so each (pnode, effective
window) contributes in proportion to the days of the year it is live.

BOUNDARY STATEMENT (rule 14 ``[R-ACCURATE]`` reconciliation clause)
------------------------------------------------------------------
This is **real published data reconciled onto our boundary**, not a direct
measurement of the quantity, and the difference is stated rather than papered
over:

* An LDF is a **typical** distribution factor — CAISO's own static/seasonal
  weighting — not metered hourly load. So this derives a **static** split, the
  same *kind* of object the 0.86/0.14 estimate was, measured instead of
  assumed. It is NOT an upgrade to an hourly NP15/ZP26 load series; no such
  series is published (survey S1/S2b).
* The hub geography is CAISO's **generator**-hub membership. Path 15 is a
  transmission boundary, so a substation's side of it is a property of the
  substation, not of what is connected there — which is why the substation
  join is sound. Where a load substation hosts no generator, tier 2 carries it
  via the sub-LAP partition, whose own classification tier 1 verifies.

It satisfies rule 13 ``[R-MEASURED]``'s admissibility test — the same quantity
regenerates for a forward year from published forward bytes, and responds to
changed conditions (Kern/Fresno load growth against Bay-Area load growth moves
it). It is NOT tuned to any residual: the derive never reads a model output.

Usage::

    # refresh the committed raw Atlas snapshots from OASIS (network)
    uv run python scripts/data/derive_caiso_path15_load_split.py --fetch

    # derive from the COMMITTED bytes (no network) -- the default
    uv run python scripts/data/derive_caiso_path15_load_split.py
    uv run python scripts/data/derive_caiso_path15_load_split.py --acceptance
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

from market_sim.config.paths import RAW_DIR

#: Committed raw Atlas snapshots (the derive's source bytes).
ATLAS_DIR = RAW_DIR / "caiso-atlas"
#: The derived artifact.
OUT_CSV = RAW_DIR / "zone-specific-demand" / "CAISO" / "CAISO_path15_load_split.csv"
OUT_JSON = RAW_DIR / "zone-specific-demand" / "CAISO" / "CAISO_path15_load_split.json"

#: Backcast years the split is derived for (rule 16 [R-ALLYEARS]).
YEARS = (2023, 2024, 2025)

#: The PG&E load aggregation point whose load the split apportions.
PGAE_LAP = "DLAP_PGAE-APND"
#: PG&E sub-LAP prefix backing tier 2.
SUBLAP_PREFIX = "SLAP_PG"
#: The two model zones Path 15 separates.
ZONES = ("NP15", "ZP26")

OASIS = (
    "https://oasis.caiso.com/oasisapi/SingleZip?queryname={q}&version=1"
    "&resultformat=6&startdatetime={sd}T08:00-0000&enddatetime={ed}T08:00-0000"
)
_OASIS_SLEEP_S = 7.0

#: ACCEPTANCE GATES — pre-registered in
#: results/calibration/PRECHECK-caiso172-path15-load-split-2026-08-04.md §4.
#: These are DATA gates on the measured input. They read no model output.
MIN_LDF_SUM = 99.99  # DLAP_PGAE factors must partition the LAP
MAX_UNASSIGNED_PTS = 5.0  # residue reaching neither assignment tier
MIN_TIER1_NODES = 300  # direct substation matches backing tier 2's classification
MAX_YEAR_SPREAD = 0.010  # |max - min| of the ZP26 share across YEARS


def _get(url: str, timeout: int = 300) -> bytes:
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return r.read()


def _oasis(query: str, sd: str, ed: str) -> pd.DataFrame:
    payload = _get(OASIS.format(q=query, sd=sd, ed=ed))
    with zipfile.ZipFile(io.BytesIO(payload)) as z:
        name = z.namelist()[0]
        data = z.open(name).read()
    if name.endswith(".xml"):
        m = re.search(rb"ERR_DESC>(.*?)<", data, re.S)
        raise RuntimeError(
            f"OASIS {query}: {(m.group(1).decode() if m else '?')[:120]}"
        )
    return pd.read_csv(io.BytesIO(data))


#: Columns each committed snapshot keeps. The full ``ATL_LDF`` pull is ~68 MB
#: of every APnode in CAISO; the derive needs only the PG&E LAP + its sub-LAPs
#: and five columns, so the snapshot is slimmed to those BEFORE it is written.
#: Slimming is part of the frozen construction, not a convenience: the
#: committed bytes are exactly the bytes the derive reads.
_KEEP_COLS = {
    "ATL_LDF": ["EFF_START_DT", "EFF_END_DT", "APNODE_ID", "PNODE_ID", "DIST_FACTOR"],
    "ATL_PNODE_MAP": ["EFF_START_DT", "EFF_END_DT", "APNODE_ID", "PNODE_ID"],
}


def slim_atlas(query: str, df: pd.DataFrame) -> pd.DataFrame:
    """Reduce a raw Atlas pull to the rows and columns the derive consumes."""
    if query == "ATL_LDF":
        keep = df["APNODE_ID"].astype(str).str.startswith((PGAE_LAP, SUBLAP_PREFIX))
        df = df[keep]
    return df[_KEEP_COLS[query]].drop_duplicates().sort_values(_KEEP_COLS[query])


def fetch_atlas(years: tuple[int, ...] = YEARS) -> None:
    """Download the Atlas snapshots into ``ATLAS_DIR`` (the only network step).

    Queried **monthly** so every effective window live during the year is
    captured — CAISO reissues the Atlas reports seasonally. Each pull is
    slimmed by :func:`slim_atlas` before it is written.
    """
    ATLAS_DIR.mkdir(parents=True, exist_ok=True)
    for query in ("ATL_LDF", "ATL_PNODE_MAP"):
        frames = []
        for year in years:
            for month in range(1, 13):
                sd = f"{year}{month:02d}01"
                ed = f"{year}{month:02d}02"
                try:
                    frames.append(slim_atlas(query, _oasis(query, sd, ed)))
                except Exception as e:  # noqa: BLE001 - a missing month is not fatal
                    print(f"  {query} {sd}: {type(e).__name__}: {e}")
                time.sleep(_OASIS_SLEEP_S)
        df = pd.concat(frames, ignore_index=True).drop_duplicates()
        out = ATLAS_DIR / f"{query}.csv"
        df.to_csv(out, index=False)
        print(f"wrote {out}  ({len(df)} unique rows)")


def _load_atlas(query: str) -> pd.DataFrame:
    path = ATLAS_DIR / f"{query}.csv"
    if not path.exists():
        raise FileNotFoundError(
            f"{path} missing — run with --fetch once to snapshot the Atlas reports"
        )
    df = pd.read_csv(path)
    df["EFF_START_DT"] = pd.to_datetime(df["EFF_START_DT"])
    df["EFF_END_DT"] = pd.to_datetime(df["EFF_END_DT"])
    return df


def _substation(s: pd.Series) -> pd.Series:
    """Pnode ids are ``SUBSTATION_voltage_id``; take the substation token."""
    return s.str.split("_").str[0]


def _live(df: pd.DataFrame, asof: pd.Timestamp) -> pd.DataFrame:
    """Rows of an effective-dated Atlas report live at ``asof``."""
    return df[(df["EFF_START_DT"] <= asof) & (df["EFF_END_DT"] >= asof)]


def _sub_to_hub(hub_rows: pd.DataFrame) -> pd.Series:
    """Map substation -> hub, keeping only substations whose pnodes all agree."""
    h = hub_rows.copy()
    h["SUB"] = _substation(h["PNODE_ID"])
    h["HUB"] = h["APNODE_ID"].str.extract(r"TH_(\w+?)_GEN")[0]
    return h.groupby("SUB")["HUB"].agg(
        lambda x: x.unique()[0] if x.nunique() == 1 else None
    )


def _assign(ldf_rows: pd.DataFrame, sub2hub: pd.Series) -> tuple[pd.DataFrame, int]:
    """Assign each DLAP_PGAE load pnode to NP15/ZP26. Returns (frame, n_tier1)."""
    pg = ldf_rows[ldf_rows["APNODE_ID"] == PGAE_LAP][["PNODE_ID", "DIST_FACTOR"]].copy()
    pg = pg.drop_duplicates(subset="PNODE_ID")
    pg["HUB"] = _substation(pg["PNODE_ID"]).map(sub2hub)
    pg.loc[~pg["HUB"].isin(ZONES), "HUB"] = None
    n_tier1 = int(pg["HUB"].notna().sum())

    node2hub: dict[str, str] = {}
    for slap in [
        a for a in ldf_rows["APNODE_ID"].unique() if str(a).startswith(SUBLAP_PREFIX)
    ]:
        nodes = ldf_rows[ldf_rows["APNODE_ID"] == slap]["PNODE_ID"].drop_duplicates()
        vc = _substation(nodes).map(sub2hub).value_counts()
        vc = vc[vc.index.isin(ZONES)]
        if len(vc):
            dominant = vc.idxmax()
            for n in nodes:
                node2hub[n] = dominant
    pg["HUB"] = pg["HUB"].fillna(pg["PNODE_ID"].map(node2hub))
    return pg, n_tier1


def derive(years: tuple[int, ...] = YEARS) -> pd.DataFrame:
    """Day-weighted per-year NP15/ZP26 split of PG&E TAC-area load."""
    ldf_all, hub_all = _load_atlas("ATL_LDF"), _load_atlas("ATL_PNODE_MAP")
    rows = []
    for year in years:
        y0, y1 = pd.Timestamp(f"{year}-01-01"), pd.Timestamp(f"{year}-12-31")
        days = pd.date_range(y0, y1, freq="D")
        acc = {z: 0.0 for z in ZONES}
        unassigned = 0.0
        ldf_sum = 0.0
        tier1 = 0
        n_windows = 0
        # one representative day per distinct effective window, day-weighted
        starts = sorted({s for s in ldf_all["EFF_START_DT"] if s <= y1})
        edges = [d for d in days if d in set(pd.to_datetime(starts))] or []
        marks = sorted({y0, *[e for e in edges if y0 < e <= y1]})
        for i, mark in enumerate(marks):
            nxt = marks[i + 1] if i + 1 < len(marks) else y1 + pd.Timedelta(days=1)
            w = (nxt - mark).days / len(days)
            if w <= 0:
                continue
            ldf_rows, hub_rows = _live(ldf_all, mark), _live(hub_all, mark)
            if ldf_rows.empty or hub_rows.empty:
                continue
            pg, n1 = _assign(ldf_rows, _sub_to_hub(hub_rows))
            by = pg.groupby(pg["HUB"].fillna("UNASSIGNED"))["DIST_FACTOR"].sum()
            for z in ZONES:
                acc[z] += w * float(by.get(z, 0.0))
            unassigned += w * float(by.get("UNASSIGNED", 0.0))
            ldf_sum += w * float(pg["DIST_FACTOR"].sum())
            tier1 = max(tier1, n1)
            n_windows += 1
        known = acc["NP15"] + acc["ZP26"]
        rows.append(
            {
                "year": year,
                "np15_pts": round(acc["NP15"], 4),
                "zp26_pts": round(acc["ZP26"], 4),
                "unassigned_pts": round(unassigned, 4),
                "ldf_sum": round(ldf_sum, 4),
                "n_tier1_nodes": tier1,
                "n_windows": n_windows,
                "np15_weight": round(acc["NP15"] / known, 6),
                "zp26_weight": round(acc["ZP26"] / known, 6),
            }
        )
    return pd.DataFrame(rows)


def acceptance(df: pd.DataFrame) -> bool:
    """Run the pre-registered §4 data gates. Returns True iff all pass."""
    checks: list[tuple[str, bool, str]] = []
    for _, r in df.iterrows():
        checks.append(
            (
                f"{int(r.year)} LDF partitions the LAP",
                r.ldf_sum >= MIN_LDF_SUM,
                f"sum={r.ldf_sum:.3f} >= {MIN_LDF_SUM}",
            )
        )
        checks.append(
            (
                f"{int(r.year)} residue bounded",
                r.unassigned_pts <= MAX_UNASSIGNED_PTS,
                f"{r.unassigned_pts:.3f} <= {MAX_UNASSIGNED_PTS}",
            )
        )
        checks.append(
            (
                f"{int(r.year)} tier-1 support",
                r.n_tier1_nodes >= MIN_TIER1_NODES,
                f"{int(r.n_tier1_nodes)} >= {MIN_TIER1_NODES}",
            )
        )
    spread = float(df.zp26_weight.max() - df.zp26_weight.min())
    checks.append(
        (
            "inter-year stability",
            spread <= MAX_YEAR_SPREAD,
            f"spread={spread:.4f} <= {MAX_YEAR_SPREAD}",
        )
    )
    ok = True
    for name, passed, detail in checks:
        print(f"  [{'PASS' if passed else 'FAIL'}] {name}: {detail}")
        ok &= bool(passed)
    print(f"acceptance: {sum(c[1] for c in checks)}/{len(checks)}")
    return ok


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--fetch", action="store_true", help="refresh raw Atlas snapshots (network)"
    )
    ap.add_argument(
        "--acceptance", action="store_true", help="run the pre-registered data gates"
    )
    args = ap.parse_args()

    if args.fetch:
        fetch_atlas()

    df = derive()
    print(df.to_string(index=False))
    mean_zp26 = float(df.zp26_weight.mean())
    mean_np15 = float(df.np15_weight.mean())
    print(f"\nbackcast-mean split: NP15 {mean_np15:.6f} / ZP26 {mean_zp26:.6f}")
    print("model currently carries: NP15 0.860000 / ZP26 0.140000")

    ok = acceptance(df) if args.acceptance else True

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_CSV, index=False)
    OUT_JSON.write_text(
        json.dumps(
            {
                "source": [
                    "OASIS ATL_LDF (DLAP_PGAE-APND)",
                    "OASIS ATL_PNODE_MAP (TH_*_GEN)",
                ],
                "derived_by": "scripts/data/derive_caiso_path15_load_split.py",
                "session": "caiso-172",
                "years": list(YEARS),
                "np15_weight": round(mean_np15, 6),
                "zp26_weight": round(mean_zp26, 6),
                "per_year": df.to_dict(orient="records"),
            },
            indent=2,
        )
        + "\n"
    )
    print(f"\nwrote {OUT_CSV}\nwrote {OUT_JSON}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
