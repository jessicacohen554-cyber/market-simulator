#!/usr/bin/env python3
"""ERCOT-160 — enumerate the CT target population from the SCED corpus itself.

ERCOT-146 §3 and ERCOT-147 §3 both left the CT *target population* open: the
crosswalk carries 165 ``CT_PEAKER`` rows with 6 accepted, but nobody had
checked that list against the resources ERCOT's own 60-Day SCED disclosure
actually publishes. This probe answers that from the corpus — no model, no
LP, no derivation, no free parameter. It is a census, and it reports what it
cannot resolve rather than guessing.

It also settles a GRAIN question those charters got wrong. The crosswalk's
``site`` column is not one grain: for ``CC_REGULAR`` it holds a site prefix
(``RIONOG``, settlement point ``RIONOG_CC1``), but for ``CT_PEAKER`` it holds
the full RESOURCE name (``VICTPORT_CTG01``). Measured here — 165/165 CT rows
match a corpus resource name, 0/165 match a site prefix — so "165 CT_PEAKER
sites" counts RESOURCES, and the hand-crosswalk task the charters sized at
"~150 sites" is a much smaller and differently-shaped job: see the emitted
``corpus_resources_absent_from_crosswalk`` (no candidate row at all) versus
the listed-but-unaccepted remainder (an adjudication, not an identification).

Reads the all-resource delivery-2023 corpus (``data/raw/ercot/SCED/``, the
ERCOT-157 re-upload) and, when present, the CT-scoped full-span shards
(``data/raw/ercot/SCED-CT/``, ERCOT-160). Emits, per CT resource
(``Resource Type`` in SCLE90/SCGT90): its site prefix, QSE(s), max published
HSL, and whether the site is already crosswalked/accepted in
``data/raw/reference/ercot-dam-plant-crosswalk.csv``.

The site prefix convention is ERCOT's own resource-naming: a resource name is
``<SITE>_<UNIT>`` (e.g. ``MGSES_CT1`` → site ``MGSES``). Resources that do not
split on ``_`` are reported as their own site and flagged, never dropped.

Run:
    python scripts/probes/ercot160_ct_target_population.py
    python scripts/probes/ercot160_ct_target_population.py --out results/calibration/ercot160_ct_population.json
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
ALL_RESOURCE_DIR = REPO / "data/raw/ercot/SCED"
CT_SCOPED_DIR = REPO / "data/raw/ercot/SCED-CT"
CROSSWALK = REPO / "data/raw/reference/ercot-dam-plant-crosswalk.csv"
CT_TYPES = ("SCLE90", "SCGT90")


def _site_of(resource: str) -> tuple[str, bool]:
    """Return (site prefix, split_ok) for an ERCOT resource name."""
    if "_" not in resource:
        return resource, False
    return resource.rsplit("_", 1)[0], True


def scan_corpus(dirs: list[Path]) -> pd.DataFrame:
    """Census every CT resource across the given corpus directories."""
    hsl_max: dict[str, float] = defaultdict(float)
    restype: dict[str, set[str]] = defaultdict(set)
    qses: dict[str, set[str]] = defaultdict(set)
    files = [p for d in dirs if d.is_dir() for p in sorted(d.glob("*.parquet"))]
    if not files:
        raise SystemExit(f"no parquet found under {[str(d) for d in dirs]}")
    for path in files:
        df = pd.read_parquet(
            path, columns=["Resource Name", "Resource Type", "QSE", "HSL"]
        )
        df = df[df["Resource Type"].isin(CT_TYPES)]
        if df.empty:
            continue
        for name, grp in df.groupby("Resource Name", observed=True):
            name = str(name)
            hsl_max[name] = max(hsl_max[name], float(grp["HSL"].max()))
            restype[name].update(str(x) for x in grp["Resource Type"].unique())
            qses[name].update(str(x) for x in grp["QSE"].dropna().unique())
    rows = []
    for name in sorted(hsl_max):
        site, split_ok = _site_of(name)
        rows.append(
            {
                "resource": name,
                "site": site,
                "site_prefix_parsed": split_ok,
                "resource_type": ";".join(sorted(restype[name])),
                "qse": ";".join(sorted(qses[name])),
                "max_hsl_mw": round(hsl_max[name], 1),
            }
        )
    return pd.DataFrame(rows), [str(p.relative_to(REPO)) for p in files]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=None, help="write the census JSON here")
    ap.add_argument(
        "--csv", default=None, help="also write the per-resource census CSV"
    )
    args = ap.parse_args()

    census, sources = scan_corpus([ALL_RESOURCE_DIR, CT_SCOPED_DIR])
    cw = pd.read_csv(CROSSWALK)
    ct_cw = cw[cw["class"] == "CT_PEAKER"]

    # GRAIN, measured not assumed (ERCOT-160): the crosswalk's `site` column
    # is NOT one grain. For CC_REGULAR it holds a SITE prefix (RIONOG, whose
    # settlement_points is RIONOG_CC1); for CT_PEAKER it holds the full
    # RESOURCE name (VICTPORT_CTG01). Measured on this corpus: 165/165 CT
    # `site` values match a corpus RESOURCE name and 0/165 match a site
    # prefix. So the CT join is per-resource, and the "165 CT_PEAKER sites"
    # framing carried by ERCOT-146 §3 / ERCOT-147 §3 counts RESOURCES.
    listed = set(ct_cw["site"].astype(str))
    accepted = set(ct_cw.loc[ct_cw["accepted"] == 1, "site"].astype(str))
    resource_names = set(census["resource"])
    site_names = set(census["site"])
    grain = {
        "ct_rows_matching_corpus_resource": len(listed & resource_names),
        "ct_rows_matching_corpus_site_prefix": len(listed & site_names),
        "join_grain": (
            "resource"
            if len(listed & resource_names) >= len(listed & site_names)
            else "site"
        ),
    }

    census["in_crosswalk"] = census["resource"].isin(listed)
    census["crosswalk_accepted"] = census["resource"].isin(accepted)

    by_site = (
        census.groupby("site")
        .agg(
            n_resources=("resource", "size"),
            site_hsl_mw=("max_hsl_mw", "sum"),
            n_in_crosswalk=("in_crosswalk", "sum"),
            n_accepted=("crosswalk_accepted", "sum"),
        )
        .reset_index()
        .sort_values("site_hsl_mw", ascending=False)
    )
    by_site["site_fully_crosswalked"] = (
        by_site["n_in_crosswalk"] == by_site["n_resources"]
    )
    by_site["site_fully_accepted"] = by_site["n_accepted"] == by_site["n_resources"]

    total_mw = float(census["max_hsl_mw"].sum())
    acc_mw = float(census.loc[census["crosswalk_accepted"], "max_hsl_mw"].sum())
    in_mw = float(census.loc[census["in_crosswalk"], "max_hsl_mw"].sum())
    summary = {
        "crosswalk_join_grain": grain,
        "n_ct_resources": int(len(census)),
        "n_ct_sites": int(len(by_site)),
        "ct_fleet_hsl_mw": round(total_mw, 1),
        "resources_in_crosswalk": int(census["in_crosswalk"].sum()),
        "resources_accepted": int(census["crosswalk_accepted"].sum()),
        "hsl_share_in_crosswalk": round(in_mw / total_mw, 4) if total_mw else None,
        "hsl_share_accepted": round(acc_mw / total_mw, 4) if total_mw else None,
        "sites_fully_crosswalked": int(by_site["site_fully_crosswalked"].sum()),
        "sites_fully_accepted": int(by_site["site_fully_accepted"].sum()),
        "crosswalk_ct_rows": int(len(ct_cw)),
        "crosswalk_ct_accepted": int((ct_cw["accepted"] == 1).sum()),
        "crosswalk_rows_absent_from_corpus": sorted(listed - resource_names),
        "corpus_resources_absent_from_crosswalk": sorted(resource_names - listed),
        "resources_without_site_split": sorted(
            census.loc[~census["site_prefix_parsed"], "resource"]
        ),
        "n_source_files": len(sources),
    }

    print(json.dumps(summary, indent=2)[:4000])
    print("\nTop 15 CT sites by published HSL:")
    print(by_site.head(15).to_string(index=False))

    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            json.dumps({"summary": summary, "sources": sources}, indent=2) + "\n"
        )
        print(f"\nwrote {out}")
    if args.csv:
        Path(args.csv).parent.mkdir(parents=True, exist_ok=True)
        census.to_csv(args.csv, index=False)
        print(f"wrote {args.csv}")


if __name__ == "__main__":
    main()
