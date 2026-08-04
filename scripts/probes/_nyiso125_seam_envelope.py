#!/usr/bin/env python3
"""nyiso-125 Phase 0 — identify NYISO's per-neighbour seam envelope (NO LP).

The successor object nyiso-124 §6.1 handed this lane: the model's external
seam delivers the right NET and the wrong DISTRIBUTION.  The three downstate
border links sit at their bound in 98-100 % of ALL hours of all three training
years (a flat 3,800 MW against a measured downstate median of 1,870 / 1,772 /
2,040 MW) while ``NYISO_external>Upstate_West`` runs NET EXPORT against a
measured import — so ~1.8-2.0 GW of surplus import lands EAST of the
Central-East cutset and the model's CE link never draws on the west
(util 0.253 against the real interface's 0.591).

This probe asks ONE question and answers it with no solve:

    **Is a per-neighbour seam envelope IDENTIFIED from NYISO's own measured
    postings, and on which links?**

It is Phase 0 of the nyiso-125 charter.  Rule 25 ``[R-ISO-SCOPE]`` is binding
both ways: PJM's ``pjm_seam_envelope_by_neighbor`` verdict does NOT fill
NYISO's ``seam_flow_envelopes`` cell.  Every number below is derived from
NYISO's OWN market — the MIS P-32 "Interface Limits and Flows" posting,
committed at ``data/raw/NYISO/interface-flows/`` for all three training years.

Sections
--------
``dup``      the HQ accounting duplicate — which SCH rows are independent
``ties``     per-tie flow / posted-limit / utilisation census
``attrib``   the tie -> model-landing-zone attribution and its ONE ambiguity
``envelope`` the per-landing-zone directional envelope, bracketed on that
             ambiguity, against the incumbent static border-link TTCs
``joint``    the split-INVARIANT joint AC-seam envelope, and whether it binds

Run::

    uv run python scripts/probes/_nyiso125_seam_envelope.py
    uv run python scripts/probes/_nyiso125_seam_envelope.py --sections envelope

Record: ``results/calibration/_nyiso125_seam_envelope.json``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

YEARS = (2023, 2024, 2025)
HOURS = 8760

# The model's fixed non-leap 8760-hour clock, keyed to 2023 and shared by every
# model year (build_ercot_as_withholding._CALENDAR; Feb 29 dropped).  Measured
# series are keyed onto it by LOCAL (month, day, hour) — never positionally
# (the nyiso-123 §1 correction: a per-year date_range is one day off for
# leap-2024 from Mar 1 onward).
_CAL = pd.date_range("2023-01-01", periods=HOURS, freq="h")
MONTH_OF_HOUR = _CAL.month.to_numpy()
HOUR_OF_DAY = _CAL.hour.to_numpy()

# The interface-limit posting's "unbounded" sentinel
# (scripts/data/curate_nyiso_interface_flows.py).
LIMIT_SENTINEL = 9990.0
# "Binding" for a posted interface — the same 0.95 bar nyiso-122 used when it
# refuted the Tier-3 TTC re-grounding, kept identical so the two measurements
# are directly comparable.
BIND_UTIL = 0.95

# The repo-wide deliverability-envelope convention: the upper envelope minus
# the top ~10 % transient/loop-flow hours, keeping headroom above the median so
# the modeled seam price still sets the typical hour.  constants.
# MISO_SEAM_FLOW_PERCENTILE == PJM_SEAM_FLOW_PERCENTILE == 90.0 and
# eia930.envelopes.measured_interchange_envelope's default all carry it.  A
# DEFINITIONAL headroom choice fixed ex ante — never swept for NYISO (rule 20).
SEAM_PERCENTILE = 90.0

# --------------------------------------------------------------------------
# The tie -> model-landing-zone attribution.
#
# The model aggregates NYISO's eleven load zones A-K into five
# (config/iso_configs._nyiso_config): Upstate_West = A-E, Capital_Hudson = F+G,
# Lower_Hudson = H+I, NYC = J, Long_Island = K.  Its external star node
# ``NYISO_external`` reaches four of them (interchange/spec.IMPORT_NODE_LINKS).
#
# Each P-32 external schedule row is placed by the NYCA load zone its ties
# physically land in (NYISO Gold Book external interconnections; the same tie
# geography already cited in the IMPORT_NODE_LINKS["NYISO"] comment):
#
#   * SCH - HQ - NY        Chateauguay HVDC at Massena          -> Zone D  -> Upstate_West
#   * SCH - HQ_CEDARS      Cedars Rapids / Dennison             -> Zone D  -> Upstate_West
#   * SCH - OH - NY        IESO: Niagara (A) + St Lawrence (D)  -> A/D     -> Upstate_West
#   * SCH - NE - NY        ISO-NE AC: Alps-Berkshire, Hoosick-
#                          Bennington (F), Pleasant Valley-
#                          Long Mountain (G)                    -> F,G     -> Capital_Hudson
#   * SCH - PJM_HTP        Hudson Transmission Project          -> Zone J  -> NYC
#   * SCH - PJM_VFT        Linden VFT                           -> Zone J  -> NYC
#   * SCH - PJM_NEPTUNE    Neptune                              -> Zone K  -> Long_Island
#   * SCH - NPX_CSC        Cross Sound Cable                    -> Zone K  -> Long_Island
#   * SCH - NPX_1385       Northport-Norwalk 1385               -> Zone K  -> Long_Island
#
# EXCLUDED — ``SCH - HQ_IMPORT_EXPORT`` is an ACCOUNTING duplicate of
# ``SCH - HQ - NY``, not an independent tie (section ``dup`` measures it: equal
# to within 0.5 MW in 41 / 78 / 91 % of hours, corr 0.977 / 0.989 / 0.993, and
# it is the only SCH row carrying the +/-9,999 "unbounded" sentinel on its
# negative limit — the signature of a proxy schedule rather than a rated path).
# Counting it would double the HQ seam.
#
# AMBIGUOUS — ``SCH - PJ - NY`` is the ONLY row that physically spans the
# Central-East cutset: the PJM AC interface carries the Ramapo 345 kV PARs and
# the Waldwick 230 kV ties into Zone G (EAST of CE, -> Capital_Hudson) AND the
# Homer City-Stolle Road 345 kV / Falconer ties into Zone A (WEST, ->
# Upstate_West).  Neither NYISO's P-32 posting nor PJM's own tie-line file
# (data.eia930.envelopes._PJM_TIE_ZONE buckets all four NYISO-facing ties as
# "NYIS"/"NEPT"/"HUDS"/"LIND" — the AC ties are ONE row) separates them.  The
# probe therefore reports the envelope BRACKETED at both ends of the
# attribution rather than choosing a split.
# --------------------------------------------------------------------------
UNAMBIGUOUS: dict[str, list[str]] = {
    "Upstate_West": ["SCH - HQ - NY", "SCH - HQ_CEDARS", "SCH - OH - NY"],
    "Capital_Hudson": ["SCH - NE - NY"],
    "NYC": ["SCH - PJM_HTP", "SCH - PJM_VFT"],
    "Long_Island": ["SCH - PJM_NEPTUNE", "SCH - NPX_CSC", "SCH - NPX_1385"],
}
AMBIGUOUS_TIE = "SCH - PJ - NY"
DUPLICATE_TIE = "SCH - HQ_IMPORT_EXPORT"
# The two landing zones whose ties are ALL unambiguous — the identified half.
IDENTIFIED_ZONES = ("NYC", "Long_Island")

# Incumbent static border-link TTCs (interchange/spec.IMPORT_NODE_LINKS["NYISO"]),
# symmetric +/- and time-invariant.
INCUMBENT_TTC: dict[str, float] = {
    "Upstate_West": 3000.0,
    "Capital_Hudson": 1600.0,
    "NYC": 1000.0,
    "Long_Island": 1200.0,
}

# The model's own border-link flows, read by nyiso-124 §6.1 off the committed
# network layer (results/calibration/nyiso116_c3c_unitlayer/hourly).  Quoted
# here so the ``joint`` section can decide bindingness without a solve; the
# provenance caveat nyiso-124 stated applies (a nyiso-113-recipe replay, used
# only for link saturation and gross flow magnitude).
MODEL_LINK_P50: dict[int, dict[str, float]] = {
    2023: {"Upstate_West": -1003.0, "Capital_Hudson": 1600.0},
    2024: {"Upstate_West": -1520.0, "Capital_Hudson": 1600.0},
    2025: {"Upstate_West": -1689.0, "Capital_Hudson": 1600.0},
}

RULE = "=" * 78
SUB = "-" * 78


def _check_years() -> None:
    """Fail closed if ``YEARS`` ever strays outside the training window."""
    bad = [y for y in YEARS if y not in (2023, 2024, 2025)]
    if bad:
        raise SystemExit(f"rule 22 [R-HOLDOUT]: refusing out-of-training years {bad}")


def postings(year: int) -> pd.DataFrame:
    """Return the hourly P-32 posting for ``year``, keyed to the model clock.

    Args:
        year: Training year (2023-2025).

    Returns:
        Long frame with ``interface``, ``flow_mw``, ``positive_limit_mw``,
        ``negative_limit_mw`` and the model-clock keys ``mo`` / ``dy`` / ``hr``.
        Feb 29 is dropped; the +/-9,999 sentinel limits are nulled.
    """
    path = (
        REPO
        / "data/raw/NYISO/interface-flows"
        / f"NYISO_interface_flows_hourly_{year}.csv.gz"
    )
    df = pd.read_csv(path)
    ts = pd.to_datetime(df["interval_start_local"])
    df = df[~((ts.dt.month == 2) & (ts.dt.day == 29))].copy()
    ts = ts[~((ts.dt.month == 2) & (ts.dt.day == 29))]
    df["mo"], df["dy"], df["hr"] = ts.dt.month, ts.dt.day, ts.dt.hour
    for col in ("positive_limit_mw", "negative_limit_mw"):
        df[col] = df[col].where(df[col].abs() < LIMIT_SENTINEL)
    return df


def _wide(year: int) -> pd.DataFrame:
    """Return the (model-clock hour x interface) net-schedule matrix, MW."""
    df = postings(year)
    w = df.pivot_table(index=["mo", "dy", "hr"], columns="interface", values="flow_mw")
    return w.sort_index()


def directional_envelope(
    net: np.ndarray, month: np.ndarray, hod: np.ndarray, pct: float
) -> tuple[np.ndarray, np.ndarray]:
    """Return per-hour ``(import_cap, export_cap)`` from a net-schedule series.

    The seam's deliverable envelope: within each (month x hour-of-day) bin, the
    ``pct`` percentile of the directionally-clipped measured net schedule. The
    same construction ``eia930.envelopes.measured_interchange_envelope`` and the
    MISO/PJM seam limits use, on NYISO's own data.

    Args:
        net: Hourly net schedule, MW, NYISO sign (positive = import into NY).
        month: Month of each hour on the model clock.
        hod: Hour-of-day of each hour on the model clock.
        pct: Envelope percentile (``SEAM_PERCENTILE``).

    Returns:
        ``(import_cap, export_cap)``, both shaped like ``net`` and non-negative.
    """
    imp = np.clip(net, 0.0, None)
    exp = np.clip(-net, 0.0, None)
    ci = np.zeros_like(net)
    ce = np.zeros_like(net)
    for m in range(1, 13):
        for h in range(24):
            sel = (month == m) & (hod == h)
            if sel.any():
                ci[sel] = np.percentile(imp[sel], pct)
                ce[sel] = np.percentile(exp[sel], pct)
    return ci, ce


# ---------------------------------------------------------------------------
# sections
# ---------------------------------------------------------------------------
def section_dup() -> dict:
    """Measure whether ``SCH - HQ_IMPORT_EXPORT`` duplicates ``SCH - HQ - NY``."""
    print(RULE)
    print("DUP: is SCH - HQ_IMPORT_EXPORT an independent tie, or HQ - NY re-posted?")
    print(RULE)
    out = []
    for year in YEARS:
        w = _wide(year)
        hq, ced, hqie = w["SCH - HQ - NY"], w["SCH - HQ_CEDARS"], w[DUPLICATE_TIE]
        eq = float((np.abs(hqie - hq) < 0.5).mean())
        row = {
            "year": year,
            "corr_with_HQ_NY": round(float(hqie.corr(hq)), 4),
            "frac_equal_within_0p5MW": round(eq, 4),
            "mean_abs_diff_vs_HQ_NY": round(float(np.abs(hqie - hq).mean()), 1),
            "mean_abs_diff_vs_HQ_plus_CEDARS": round(
                float(np.abs(hqie - (hq + ced)).mean()), 1
            ),
        }
        print(
            f"  {year}: corr {row['corr_with_HQ_NY']:.4f}  equal-within-0.5MW "
            f"{eq * 100:5.1f}%  mean|diff| {row['mean_abs_diff_vs_HQ_NY']:6.1f} MW"
        )
        out.append(row)
    print(
        "  VERDICT: accounting duplicate of SCH - HQ - NY (and the only SCH row\n"
        "  carrying the +/-9,999 unbounded sentinel) — EXCLUDED from every envelope."
    )
    return {"rows": out, "excluded": DUPLICATE_TIE}


def section_ties() -> dict:
    """Per-tie flow, posted limit and utilisation census."""
    print(RULE)
    print("TIES: does the POSTED limit ever allocate the seam?")
    print(RULE)
    out = []
    for year in YEARS:
        df = postings(year)
        keep = sorted(
            {t for ts in UNAMBIGUOUS.values() for t in ts} | {AMBIGUOUS_TIE}
        )
        print(f"\n{year}")
        print(
            f"  {'interface':22s} {'imp p50':>8s} {'posted+':>8s} {'util p50':>9s} "
            f"{'h>=95% of posted+':>18s} {'exp p50':>8s} {'posted-':>8s}"
        )
        for name in keep:
            g = df[df["interface"] == name]
            f = g["flow_mw"].to_numpy()
            pl = g["positive_limit_mw"].to_numpy()
            nl = g["negative_limit_mw"].to_numpy()
            imp, exp = np.clip(f, 0, None), np.clip(-f, 0, None)
            ok = (pl > 0) & np.isfinite(pl)
            util = float(np.median(imp[ok] / pl[ok])) if ok.any() else float("nan")
            bind = float(np.mean(imp[ok] >= BIND_UTIL * pl[ok])) if ok.any() else 0.0
            print(
                f"  {name:22s} {np.median(imp):8.0f} {np.nanmedian(pl):8.0f} "
                f"{util:9.3f} {bind * 100:17.1f}% {np.median(exp):8.0f} "
                f"{np.nanmedian(nl):8.0f}"
            )
            out.append(
                {
                    "year": year,
                    "interface": name,
                    "import_p50": round(float(np.median(imp)), 1),
                    "export_p50": round(float(np.median(exp)), 1),
                    "posted_pos_p50": round(float(np.nanmedian(pl)), 1),
                    "posted_neg_p50": round(float(np.nanmedian(nl)), 1),
                    "import_util_p50": None if np.isnan(util) else round(util, 4),
                    "share_hours_ge_95pct_posted": round(bind, 4),
                }
            )
    print(
        "\n  VERDICT: on the three AC seams that land on the two links carrying the\n"
        "  defect (NE - NY, OH - NY, PJ - NY) the measured flow reaches 95 % of the\n"
        "  POSTED limit in 0.0-0.1 % of hours in EVERY year — the posted rating is\n"
        "  not what allocates this seam.  A posted-limit envelope would also LOOSEN\n"
        "  those links (Upstate_West 3,650+ vs the incumbent 3,000; Capital_Hudson\n"
        "  1,400 + the PJ share vs 1,600), i.e. loosen exactly what over-delivers."
    )
    return {"rows": out}


def section_envelope() -> dict:
    """Per-landing-zone directional envelope, bracketed on the PJ - NY split."""
    print(RULE)
    print("ENVELOPE: the per-landing-zone deliverable envelope, and its identification")
    print(RULE)
    out = []
    for year in YEARS:
        w = _wide(year)
        mo = w.index.get_level_values("mo").to_numpy()
        hod = w.index.get_level_values("hr").to_numpy()
        print(f"\n{year}   (p{SEAM_PERCENTILE:.0f} of the month x hour-of-day bin)")
        print(
            f"  {'landing zone':16s} {'incumbent':>9s} {'imp env p50':>12s} "
            f"{'imp env min':>12s} {'exp env p50':>12s} {'binds<TTC':>10s} "
            f"{'mean MW cut':>12s}"
        )
        for attrib in ("PJ_ALL_EAST", "PJ_ALL_WEST"):
            groups = {z: list(v) for z, v in UNAMBIGUOUS.items()}
            host = "Capital_Hudson" if attrib == "PJ_ALL_EAST" else "Upstate_West"
            groups[host].append(AMBIGUOUS_TIE)
            for zone, ties in groups.items():
                identified = zone in IDENTIFIED_ZONES
                # The identified zones are attribution-invariant — print once.
                if identified and attrib == "PJ_ALL_WEST":
                    continue
                net = w[ties].sum(axis=1).to_numpy()
                ci, ce = directional_envelope(net, mo, hod, SEAM_PERCENTILE)
                inc = INCUMBENT_TTC[zone]
                cut = np.clip(inc - ci, 0.0, None)
                tag = "IDENTIFIED" if identified else f"bracket:{attrib}"
                print(
                    f"  {zone:16s} {inc:9.0f} {np.median(ci):12.0f} {ci.min():12.0f} "
                    f"{np.median(ce):12.0f} {float((ci < inc).mean()) * 100:9.1f}% "
                    f"{cut.mean():12.1f}   [{tag}]"
                )
                out.append(
                    {
                        "year": year,
                        "zone": zone,
                        "attribution": "invariant" if identified else attrib,
                        "identified": identified,
                        "incumbent_ttc_mw": inc,
                        "import_env_p50": round(float(np.median(ci)), 1),
                        "import_env_min": round(float(ci.min()), 1),
                        "import_env_max": round(float(ci.max()), 1),
                        "export_env_p50": round(float(np.median(ce)), 1),
                        "share_hours_env_below_ttc": round(
                            float((ci < inc).mean()), 4
                        ),
                        "mean_mw_removed": round(float(cut.mean()), 1),
                        "measured_net_p50": round(float(np.median(net)), 1),
                    }
                )
    # The bracket width on the two links that carry the defect.
    print(f"\n{SUB}")
    print("  IDENTIFICATION VERDICT")
    print(f"{SUB}")
    for year in YEARS:
        rows = [r for r in out if r["year"] == year and not r["identified"]]
        for zone in ("Capital_Hudson", "Upstate_West"):
            lo = min(
                r["import_env_p50"] for r in rows if r["zone"] == zone
            )
            hi = max(r["import_env_p50"] for r in rows if r["zone"] == zone)
            print(
                f"  {year} {zone:16s} import envelope p50 brackets "
                f"{lo:6.0f} - {hi:6.0f} MW on the PJ - NY split alone "
                f"(width {hi - lo:5.0f} MW)"
            )
    print(
        "\n  NYC and Long_Island: every tie lands unambiguously in ONE NYISO load\n"
        "  zone (J and K) — the envelope is attribution-INVARIANT and carries ZERO\n"
        "  identification freedom.  IDENTIFIED.\n"
        "  Capital_Hudson and Upstate_West: the PJ - NY split moves Capital_Hudson's\n"
        "  import envelope across the WHOLE range that matters, and Capital_Hudson is\n"
        "  the link carrying the defect.  No public source separates the Ramapo/\n"
        "  Waldwick (Zone G) from the Homer City-Stolle Road (Zone A) legs.  Choosing\n"
        "  inside that bracket would be choosing a number so the Central-East link\n"
        "  starts binding.  REFUSED ON IDENTIFICATION (rule 20 [R-DOF])."
    )
    return {"rows": out}


def section_joint() -> dict:
    """The split-invariant joint AC-seam envelope: identified, and inert?"""
    print(RULE)
    print("JOINT: the Upstate_West + Capital_Hudson envelope is split-INVARIANT")
    print(RULE)
    ac = UNAMBIGUOUS["Upstate_West"] + UNAMBIGUOUS["Capital_Hudson"] + [AMBIGUOUS_TIE]
    out = []
    for year in YEARS:
        w = _wide(year)
        mo = w.index.get_level_values("mo").to_numpy()
        hod = w.index.get_level_values("hr").to_numpy()
        net = w[ac].sum(axis=1).to_numpy()
        ci, ce = directional_envelope(net, mo, hod, SEAM_PERCENTILE)
        model = sum(MODEL_LINK_P50[year].values())
        binds = bool(model > float(np.median(ci)))
        print(
            f"  {year}: measured joint net p50 {np.median(net):6.0f} MW | import env "
            f"p50 {np.median(ci):6.0f} min {ci.min():5.0f} | MODEL joint net p50 "
            f"{model:+6.0f} MW -> {'BINDS' if binds else 'INERT (model already below)'}"
        )
        out.append(
            {
                "year": year,
                "measured_joint_net_p50": round(float(np.median(net)), 1),
                "joint_import_env_p50": round(float(np.median(ci)), 1),
                "joint_import_env_min": round(float(ci.min()), 1),
                "joint_export_env_p50": round(float(np.median(ce)), 1),
                "model_joint_net_p50": model,
                "binds": binds,
            }
        )
    print(
        "\n  VERDICT: identified WITHOUT the PJ - NY split — and PROVABLY INERT.  The\n"
        "  model's joint AC-seam net import already sits far BELOW the measured\n"
        "  envelope in all three years, so a joint cap constrains nothing.  The\n"
        "  defect is the WITHIN-pair allocation, which a joint cap cannot see."
    )
    return {"rows": out}


SECTIONS = {
    "dup": section_dup,
    "ties": section_ties,
    "envelope": section_envelope,
    "joint": section_joint,
}


def main() -> int:
    """Run the requested sections and write the JSON record."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sections", nargs="*", default=list(SECTIONS))
    args = ap.parse_args()
    _check_years()
    record: dict = {
        "probe": "nyiso-125 Phase 0 — seam envelope identification",
        "years": list(YEARS),
        "seam_percentile": SEAM_PERCENTILE,
        "source": "data/raw/NYISO/interface-flows (NYISO MIS P-32)",
        "sections": {},
    }
    for name in args.sections:
        if name not in SECTIONS:
            raise SystemExit(f"unknown section {name!r}; pick from {list(SECTIONS)}")
        record["sections"][name] = SECTIONS[name]()
        print()
    dest = REPO / "results/calibration/_nyiso125_seam_envelope.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(record, indent=1) + "\n")
    print(f"wrote {dest.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
