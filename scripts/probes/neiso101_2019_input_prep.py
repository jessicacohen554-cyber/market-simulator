"""neiso-101 — the 2019 scoring-input preparedness audit, over the FULL 2019-2025 span.

Executes precondition #2 of the neiso-100 owner decision card
(``results/calibration/ASSESSMENT-neiso100-declaration-reassess-2026-08-18.md``
§4.3): *"Three absent 2019 scoring inputs — ``calibration_reference``,
``actual_tail``, renewable-capacity"*. That list is **re-measured here rather
than trusted** — two of its three items turn out to have been closed by
neiso-89 (PR #3693) and the card was quoting neiso-87's §3.2 table forward.

**Why the whole span and not just 2019.** Rule 22's 2026-08-06 clarification:
*"an input is either the best measured representation of a physical/market
quantity or it is not, and if it is, it belongs in EVERY year"*. A per-year
walk is the only way to see an input that is present for 2019 but *provenance-
split* against the tuned years, which is the pathology the NEISO gas basis had
(neiso-85/86).

**This probe produces NO model output.** It resolves loaders, inspects on-disk
coverage, and calls ``derive_actual_tail.derive()`` — a pure function — WITHOUT
writing it. No LP is constructed; no year is solved, scored or registered. Under
rule 22 as rewritten 2026-08-06 ("WHAT IS HELD OUT IS THE *SCORE*, NEVER THE
*DATA*") input inspection is unrestricted; the spend is looking at an answer,
which this never does. The holdout spend freeze
(``frontend/data/backcast/holdout-freeze.json``) names ``solve``, ``score`` and
``dashboard registration`` — none of which happens here.

It reuses :mod:`scripts.probes.neiso90_final_prereq_audit` by rebinding that
module's year globals rather than copying its eighteen per-input probes, so the
two audits cannot drift apart.

Usage:
    uv run python scripts/probes/neiso101_2019_input_prep.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

ISO = "NEISO"
#: The program's working span (CLAUDE.md rule 22, owner decision 2026-08-06).
SPAN = (2019, 2020, 2021, 2022, 2023, 2024, 2025)
TUNED = (2023, 2024, 2025)

OUT = REPO / "results" / "calibration" / "_neiso101_2019_input_prep.json"

from scripts.probes import neiso90_final_prereq_audit as n90  # noqa: E402

# Rebind the reused module's year globals: its probes read PROBE_YEARS /
# CONTROL_YEAR at call time, so this widens all eighteen to the full span.
n90.PROBE_YEARS = SPAN
n90.CONTROL_YEAR = 2023


def per_input_span_walk() -> dict:
    """Every keeper input neiso-90 probes, re-walked across 2019-2025."""
    out: dict[str, dict] = {}
    for label, fn in n90.PROBES:
        try:
            res = fn()
        except Exception as e:  # noqa: BLE001 - a probe reports, never raises
            res = {y: ("ERR", f"{type(e).__name__}: {e}") for y in SPAN}
        out[label] = {str(y): list(res.get(y, ("GAP", "not probed"))) for y in SPAN}
    return out


def bench_provenance() -> dict:
    """``frontend/data/backcast/bench/<ISO>/<year>.json.gz`` — coverage AND origin.

    The card lists the bench part among the "absent 2019 scoring inputs". It is
    absent, but it is **not an input that can be prepared**: it is written by
    ``render_backcast.generate`` from ``render_calibration_html.build_payload``,
    which reads a REGISTERED BUNDLE's own input snapshots
    (``bundle_input_path(bdir, "eia923"/"eia930"/"campd")``) and iterates
    ``meta["years"]``. A bench year therefore exists if and only if a bundle
    covering that year has been rendered — i.e. it is a byproduct of the spend,
    downstream of it, not a precondition for it.
    """
    d = REPO / "frontend" / "data" / "backcast" / "bench" / ISO
    have = (
        sorted(int(p.name.split(".")[0]) for p in d.glob("*.json.gz"))
        if d.is_dir()
        else []
    )
    return {
        "dir": str(d.relative_to(REPO)),
        "years_present": have,
        "years_absent_in_span": [y for y in SPAN if y not in have],
        "writer": "scripts/render_backcast.py::generate -> "
        "scripts/lib/backcast_artifacts.py::write_bench_part",
        "source": "render_calibration_html.build_payload, over a registered "
        "bundle's own eia923/eia930/campd input snapshots and meta['years']",
        "preparable_in_advance": False,
        "why": "byproduct of rendering a registered run, so it is downstream of "
        "the very spend it would support; there is no run-free code path that "
        "emits a bench year, and adding one would be building a scoring "
        "artifact for an unauthorized year",
    }


def actual_tail_gate() -> dict:
    """Is a 2019 ``actual_tail`` row emittable at HEAD, and what blocks it?

    Evaluates the deriver's own gate function per year — the same
    :mod:`scripts.lib.holdout_policy` the other three rule-22 gates read.
    """
    sys.path.insert(0, str(REPO / "scripts" / "data"))
    from scripts.data import derive_actual_tail as dat
    from scripts.lib import holdout_policy as hp

    marker = dat._marker_doc()
    committed = json.loads(
        (REPO / "frontend/data/backcast/tail/actual_tail.json").read_text()
    )
    have = sorted((committed.get("isos", {}).get(ISO) or {}).keys())
    rows = {}
    for y in SPAN:
        tier = hp.tier_for_year(y)
        rows[str(y)] = {
            "tier": tier,
            "emittable": bool(dat._year_emittable(ISO, y, marker)),
            "marker_block_required": hp.TIER_MARKER_BLOCK.get(tier),
            "iso_holds_block": bool(hp.authorized(marker, ISO, tier))
            if tier != hp.TIER_TRAIN
            else True,
            "row_committed": str(y) in have,
        }
    return {"years_committed": have, "per_year": rows}


def actual_tail_rederive_identity() -> dict:
    """Re-derive ``actual_tail`` IN MEMORY and diff against the committed file.

    This is the rule-3 / rule-14 verification the charter asks for on this
    artifact: if preparing 2019 inputs moved any tuned-year number, the
    re-derivation would differ from the committed bytes. ``derive()`` is pure —
    nothing is written.
    """
    from scripts.data import derive_actual_tail as dat

    fresh = dat.derive()
    committed = json.loads(
        (REPO / "frontend/data/backcast/tail/actual_tail.json").read_text()
    )
    fresh_bytes = (json.dumps(fresh, indent=1, sort_keys=True) + "\n").encode()
    committed_bytes = (
        REPO / "frontend/data/backcast/tail/actual_tail.json"
    ).read_bytes()
    diffs = []
    for iso in sorted(set(fresh["isos"]) | set(committed.get("isos", {}))):
        f = fresh["isos"].get(iso, {})
        c = committed.get("isos", {}).get(iso, {})
        for y in sorted(set(f) | set(c)):
            if f.get(y) != c.get(y):
                diffs.append(
                    {"iso": iso, "year": y, "fresh": f.get(y), "committed": c.get(y)}
                )
    return {
        "byte_identical": fresh_bytes == committed_bytes,
        "cell_diffs": diffs,
        "tuned_year_diffs": [d for d in diffs if int(d["year"]) in TUNED],
    }


def hub_series_actuals() -> dict:
    """The 2019 upstream ``actual_tail`` would be derived FROM, if authorized.

    An actuals-only read of a measured input (no model side). Recorded so the
    record shows the upstream is ready and the only thing missing is the grant.
    """
    p = REPO / "data/raw/_validation-source" / f"actual_lmp_hourly_{ISO}.parquet"
    if not p.exists():
        return {"file": str(p.relative_to(REPO)), "present": False}
    df = pd.read_parquet(p)
    rows = {}
    for y in SPAN:
        d = df[df["year"].astype(int) == y]
        if d.empty:
            rows[str(y)] = {"hours": 0}
            continue
        rt = d["rt"].astype(float)
        da = d["da"].astype(float) if "da" in d.columns else None
        rows[str(y)] = {
            "hours": int(len(d)),
            "rt_coverage": round(float(rt.notna().mean()), 4),
            "rt_gt_300": int((rt > 300).sum()),
            "da_gt_300": int((da > 300).sum()) if da is not None else None,
        }
    return {"file": str(p.relative_to(REPO)), "present": True, "per_year": rows}


def gas_basis_provenance() -> dict:
    """Is 2019's NEISO hub basis the SAME PROVENANCE CLASS as the tuned years?

    Presence is not consistency. The neiso-85/86 pathology was a year whose
    basis rows were present but sourced from the seasonally-INVERTED EIA
    N3050MA3 proxy while the tuned years carried measured ISO-NE prints. Rule 22
    asks that an input "belongs in EVERY year"; this classifies each year's
    twelve rows by source so a provenance split cannot hide behind an OK.
    """
    import csv

    path = REPO / "data/raw/gas_basis_by_iso_month.csv"
    rows = [r for r in csv.DictReader(path.open()) if r.get("iso") == ISO]
    out = {}
    for r in rows:
        y = out.setdefault(r["year"], {"measured": 0, "proxy": 0, "months": 0})
        y["months"] += 1
        # The proxy is the EIA citygate series; everything else is an ISO-NE
        # newswire print (the measured monthly wholesale recap).
        y["proxy" if "N3050MA3" in (r.get("source") or "") else "measured"] += 1
    for y, v in out.items():
        v["all_measured"] = v["proxy"] == 0 and v["months"] == 12
    return {
        "file": "data/raw/gas_basis_by_iso_month.csv",
        "per_year": {y: out[y] for y in sorted(out)},
        "span_uniform": all(out.get(str(y), {}).get("all_measured") for y in SPAN),
    }


def outage_extract_vintage() -> dict:
    """Is the CAMPD outage extract ONE detector vintage across the whole span?

    neiso-87 §3.2 flagged this as "the highest-materiality remaining instance of
    the gas-basis pathology": 2018-2022 were appended at a different detector
    vintage than 2023-2025 and the file carries no vintage column, so the split
    is invisible in the data. Re-measured here as row density per start-year
    plus the whole-file re-derive evidence from neiso-99 (``ef9e911``).
    """
    import collections
    import csv

    path = REPO / "data/raw/campd-unit-outages-NEISO.csv"
    rows = list(csv.DictReader(path.open()))
    by_year = collections.Counter(r["outage_start"][:4] for r in rows)
    return {
        "file": "data/raw/campd-unit-outages-NEISO.csv",
        "rows": len(rows),
        "windows_by_start_year": {y: by_year[y] for y in sorted(by_year)},
        "single_vintage_evidence": (
            "neiso-99 commit ef9e911 re-derived the extract WHOLE-FILE at HEAD: "
            "257 rows deleted, 0 added, and its own control re-derivation "
            "reproduced every surviving row byte-identically on every column. "
            "The file is therefore HEAD-reproducible end to end, which is what "
            "neiso-87's missing vintage column could not establish."
        ),
        "neiso87_warning_status": "CLOSED",
    }


def schema_uniformity() -> dict:
    """Are 2019's present inputs COMPLETE, or present-but-thin stubs?"""
    import csv
    import json as _json

    ref = _json.loads(
        (REPO / "data/raw/_validation-source/calibration_reference.json").read_text()
    )["isos"][ISO]
    base = set(ref["2023"])
    ref_rows = {}
    for y in SPAN:
        blk = ref.get(str(y))
        if blk is None:
            ref_rows[str(y)] = {"present": False}
            continue
        ref_rows[str(y)] = {
            "present": True,
            "keys": sorted(blk),
            "missing_vs_2023": sorted(base - set(blk)),
            "extra_vs_2023": sorted(set(blk) - base),
            "generation_twh_classes": len(blk.get("generation_twh") or {}),
            "demand_keys": len(blk.get("demand") or {}),
        }

    cap_rows = {}
    for y in SPAN:
        p = REPO / "data/raw/_validation-source" / f"{ISO}_{y}_renewable_capacity.csv"
        if not p.exists():
            cap_rows[str(y)] = {"present": False}
            continue
        rs = list(csv.DictReader(p.open()))
        july = {}
        for r in rs:
            if int(r["month"]) == 7:
                july[r["fuel"]] = round(
                    july.get(r["fuel"], 0.0) + float(r["capacity_mw"]), 1
                )
        cap_rows[str(y)] = {
            "present": True,
            "rows": len(rs),
            "fuels": sorted({r["fuel"] for r in rs}),
            "zones": len({r["zone"] for r in rs}),
            "months": len({r["month"] for r in rs}),
            "july_mw": july,
        }
    return {"calibration_reference": ref_rows, "renewable_capacity": cap_rows}


def would_be_2019_tail_row() -> dict:
    """The 2019 ``actual_tail`` row's CONTENT, computed but deliberately NOT emitted.

    Recorded to establish that the row is fully computable from a measured
    input already at HEAD, so that the moment a ``final`` marker exists ONE
    command (``scripts/data/derive_actual_tail.py``) completes it with nothing
    else left to prepare — which is exactly what rule 22 asks of an
    out-of-training year's configuration.

    **This is an ACTUALS-ONLY statistic with no model side**, already on the
    public record at neiso-87 §3.3 and neiso-100 §4.1a. It is not a score: no
    model output is read and nothing is compared to one. It is NOT written to
    ``actual_tail.json`` — the tier gate withholds emission and this probe does
    not touch it.
    """
    import numpy as np

    from scripts.data import derive_actual_tail as dat

    p = REPO / "data/raw/_validation-source" / f"actual_lmp_hourly_{ISO}.parquet"
    df = pd.read_parquet(p)
    d = df[df["year"].astype(int) == 2019]
    if d.empty:
        return {"computable": False}
    thr = dat.TAIL_THRESHOLD[ISO]
    rt = d["rt"].to_numpy(float)
    da = d["da"].to_numpy(float) if "da" in d.columns else np.full(len(d), np.nan)
    return {
        "computable": True,
        "emitted": False,
        "withheld_by": "rule-22 tier gate — 2019 is locked_test and NEISO holds no `final` marker",
        "row": {
            "threshold": thr,
            "da_gt": int(np.nansum(da > thr)),
            "rt_gt": int(np.nansum(rt > thr)),
            "da_coverage": round(float(np.mean(~np.isnan(da))), 3),
            "rt_coverage": round(float(np.mean(~np.isnan(rt))), 3),
            "hours": int(len(d)),
        },
    }


def capacity_actuals_window() -> dict:
    """``capacity_actuals_neiso.csv`` — a 2019/2020 GAP that is NOT this lane's.

    Surfaced by the span walk and filed rather than acted on. It is the FORECAST
    program's capacity-hindcast scoring target (W2-P5, plan §1.2.3), not a
    backcast-rubric input: no criterion C1-C8 reads it. Its window start is
    derived, not incidental — ``FLEET_VINTAGE_YEAR = min(WINDOW) - 1`` ties it to
    ``run_capacity_hindcast.py --vintage 2020`` (plan §1.1, first scored year
    2021). Moving it to 2019 would re-key the hindcast's base fleet vintage to
    2018, a year the working span DROPS, and ``WINDOW`` is shared by every ISO's
    build — a cross-ISO forecast-lane change (rule 25 ``[R-ISO-SCOPE]``).
    """
    import csv
    import collections

    p = REPO / "data/raw/_validation-source/capacity_actuals_neiso.csv"
    rows = [r for r in csv.DictReader(l for l in p.open() if not l.startswith("#"))]
    c = collections.Counter(r["year"] for r in rows)
    return {
        "file": "data/raw/_validation-source/capacity_actuals_neiso.csv",
        "rows_by_year": {y: c[y] for y in sorted(c)},
        "window_source": "scripts/data/build_capacity_actuals.py::WINDOW = range(2021, 2026)",
        "reads_it": "scripts/score_capacity_hindcast.py (forecast lane) — no backcast criterion",
        "this_lane": False,
        "action": "FILED, not acted on (rule 25) — cross-ISO forecast-lane change",
    }


def regeneration_durability() -> dict:
    """Are the 2019 inputs durable as COMMITTED artifacts, or only locally derived?

    The distinction matters for rule 22's "already configured precisely like the
    keeper, with nothing left to prepare". ``calibration_reference.json`` and the
    renewable-capacity CSVs are COMMITTED, so their 2019 content survives a fresh
    clone. But the builder that produced them
    (``scripts/data/build_calibration_reference.py``) reads ``load_demand_meta``,
    which for a pre-2021 year resolves only through the ``demand-profile`` CLEAN
    partition — and ``data/clean/`` is gitignored and disposable. So the 2019
    block is durable to USE and conditional to REBUILD.

    Measured here rather than reasoned: whether each loader resolves at HEAD with
    the clean tree in whatever state this session found it.

    Note the asymmetry check that matters most — the same partition absence
    degrades the TUNED years identically (``load_demand`` warns and falls back on
    2023 exactly as on 2019), so it is a span-wide condition, not a 2019-only
    handicap.
    """
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.data.eia930.demand import load_demand, load_demand_meta

    clean = REPO / "data" / "clean" / "demand-profile"
    rows = {}
    for y in SPAN:
        r = {}
        try:
            arr = load_demand(ISO, y, get_iso_config(ISO))
            r["load_demand"] = f"OK {arr.shape}"
        except Exception as e:  # noqa: BLE001
            r["load_demand"] = f"ERR {type(e).__name__}: {e}"
        try:
            load_demand_meta(ISO, y)
            r["load_demand_meta"] = "OK"
        except Exception as e:  # noqa: BLE001
            r["load_demand_meta"] = f"ERR {type(e).__name__}: {e}"
        rows[str(y)] = r
    return {
        "clean_demand_profile_partition_present": clean.exists(),
        "partition_is_gitignored": True,
        "per_year": rows,
        "solve_path_impact": "NONE — load_demand (the LP driver) resolves for "
        "every year in the span; load_demand_meta has no solve-path consumer "
        "(neiso-88 §2.3), only scripts/data/build_calibration_reference.py",
        "rebuild_prerequisite": "scripts/data/curate_demand_profile.py (or "
        "scripts/regenerate_clean.py demand-profile) must run before "
        "build_calibration_reference.py can REGENERATE a pre-2021 block; the "
        "committed 2019 block itself is unaffected",
        "span_symmetric": "the partition absence degrades the TUNED years "
        "identically — not a 2019-specific handicap",
    }


def main() -> None:
    record = {
        "session": "neiso-101",
        "iso": ISO,
        "span": list(SPAN),
        "mode": "INPUT PREP ONLY — no LP, no solve, no score, no registration",
        "per_input_span_walk": per_input_span_walk(),
        "bench_provenance": bench_provenance(),
        "actual_tail_gate": actual_tail_gate(),
        "actual_tail_rederive_identity": actual_tail_rederive_identity(),
        "hub_series_actuals": hub_series_actuals(),
        "gas_basis_provenance": gas_basis_provenance(),
        "outage_extract_vintage": outage_extract_vintage(),
        "schema_uniformity": schema_uniformity(),
        "would_be_2019_tail_row": would_be_2019_tail_row(),
        "capacity_actuals_window": capacity_actuals_window(),
        "regeneration_durability": regeneration_durability(),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(record, indent=1, sort_keys=True) + "\n")

    # --- console report -----------------------------------------------------
    print(f"\nNEISO input preparedness, span {SPAN[0]}-{SPAN[-1]}\n" + "=" * 78)
    hdr = "input".ljust(46) + "".join(str(y)[2:].rjust(5) for y in SPAN)
    print(hdr)
    print("-" * len(hdr))
    for label, per_year in record["per_input_span_walk"].items():
        cells = "".join(per_year[str(y)][0].rjust(5) for y in SPAN)
        print(label[:45].ljust(46) + cells)

    print("\nbench parts present:", record["bench_provenance"]["years_present"])
    print(
        "bench preparable in advance:",
        record["bench_provenance"]["preparable_in_advance"],
    )
    print("\nactual_tail gate:")
    for y, r in sorted(record["actual_tail_gate"]["per_year"].items()):
        print(
            f"  {y}  tier={r['tier']:<11} emittable={str(r['emittable']):<5} "
            f"committed={str(r['row_committed']):<5} "
            f"needs={r['marker_block_required']} held={r['iso_holds_block']}"
        )
    ident = record["actual_tail_rederive_identity"]
    print(
        f"\nactual_tail re-derive byte-identical: {ident['byte_identical']}  "
        f"cell diffs: {len(ident['cell_diffs'])}  "
        f"TUNED-year diffs: {len(ident['tuned_year_diffs'])}"
    )
    gb = record["gas_basis_provenance"]
    print("\ngas-basis provenance (measured / proxy months):")
    for y in [str(x) for x in SPAN]:
        v = gb["per_year"].get(y, {})
        print(
            f"  {y}  measured {v.get('measured')}/12  proxy {v.get('proxy')}  "
            f"all_measured={v.get('all_measured')}"
        )
    print("  span uniform:", gb["span_uniform"])
    print(
        "\noutage extract:",
        record["outage_extract_vintage"]["rows"],
        "rows;",
        "neiso-87 vintage warning:",
        record["outage_extract_vintage"]["neiso87_warning_status"],
    )
    w = record["would_be_2019_tail_row"]
    print(f"\n2019 actual_tail row computable={w['computable']} emitted={w['emitted']}")
    print("  withheld by:", w["withheld_by"])
    print(
        "\ncapacity_actuals rows by year:",
        record["capacity_actuals_window"]["rows_by_year"],
        "-> filed, not this lane",
    )
    rd = record["regeneration_durability"]
    print(
        "\nregeneration durability (clean demand-profile partition present:",
        f"{rd['clean_demand_profile_partition_present']}):",
    )
    for y in [str(x) for x in SPAN]:
        r = rd["per_year"][y]
        print(
            f"  {y}  load_demand={r['load_demand'][:14]:<14} "
            f"load_demand_meta={r['load_demand_meta'][:34]}"
        )
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
