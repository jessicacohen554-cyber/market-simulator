"""caiso-165 Phase 2 — measure the INTRA-SP15 corridor directly. NO LP.

caiso-164 §6 filed a data blocker on an **inference**: the model's five CAISO
zones price as one copperplate, and the reason offered was that ``LA_BASIN``
(77-83 TWh of load at a 0.11-0.12 belly renewable/load ratio) absorbs the whole
``ZP26 + SP15_rest`` belly surplus through a 12,008 MW one-way link that never
binds, so no surplus reaches Path 15 and Path 15 never binds S->N. That story
was assembled from **prices and energy balances**, never measured: the
committed CAISO LMP record carried only the three ``TH_*_GEN-APND``
**generation** hubs, and an intra-SP15 corridor is by construction invisible in
a hub-to-hub basis that has only one southern hub in it.

The caiso-165 intake puts CAISO's four ``DLAP_*-APND`` **load** aggregation
points in ``data/raw``, and a DLAP is exactly the missing object: it prices
where load is withdrawn. ``DLAP_SCE - TH_SP15_GEN`` is therefore a *direct*
measurement of the corridor caiso-164 could only infer.

This probe answers, from CAISO's own published ``MCE / MCC / MCL / MGHG``
decomposition and nothing else:

* **(a)** what is the measured ``DLAP_SCE - TH_SP15_GEN`` basis, and how much
  of it is CONGESTION (``dMCC``) vs LOSS (``dMCL``)?
* **(b)** in the solar-belly hours (Pacific 09-16) where caiso-164 measured the
  model's copperplate, does the real SCE load pocket separate from the SP15
  generation hub — by how much, in how many hours, and in which direction?
* **(c)** the same for ``DLAP_SDGE - TH_SP15_GEN``, the post-SONGS Path-44
  pocket.

**The pre-registered verdict rule** (``PRECHECK-caiso165-*``, §4, pushed before
this probe was run) is evaluated here and printed as the probe's own verdict, so
the adjudication cannot drift after the numbers land. It is stated on the belly
window because that is where caiso-164 located the defect:

* **CONFIRMED** — belly ``|dMCC|`` separation frequency >= 50 % AND mean belly
  ``|dMCC|`` >= 1.00 $/MWh AND >= 60 % of separated belly hours run in the
  pocket-dearer direction (the direction an import-constrained load pocket
  must take).
* **FALSIFIED** — belly separation frequency < 20 % OR mean belly ``|dMCC|``
  < 0.25 $/MWh.
* **PARTIAL** — anything between; reported as inconclusive, never rounded up.

Nothing here is fed back into a solve. It is a measurement, reported against
(rules 1 / 13 ``[R-MEASURED]``).

Usage:
    PYTHONPATH=.:src python scripts/probes/caiso165_intra_sp15_decomp.py \
        --json results/calibration/_caiso165_intra_sp15.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
DAM = REPO / "data/raw/lmp-data/CAISO"
KEEPER = REPO / "results/calibration/caiso164_zonal_loss_surface"
YEARS = (2023, 2024, 2025)

#: The generation hubs (caiso-164's whole record) and the load aggregation
#: points this session intook. A DLAP prices where load is WITHDRAWN; a
#: ``TH_*_GEN`` hub prices where power is INJECTED. The intra-SP15 corridor
#: lives between them and is invisible to any hub-only basis.
GEN_HUBS = ("TH_NP15_GEN-APND", "TH_SP15_GEN-APND", "TH_ZP26_GEN-APND")
DLAPS = ("DLAP_PGAE-APND", "DLAP_SCE-APND", "DLAP_SDGE-APND", "DLAP_VEA-APND")

#: The corridors under test. ``(near, far, label)``; a POSITIVE basis means the
#: first node is dearer.  The first two ARE the caiso-164 §6 attribution: an
#: import-constrained load pocket behind a binding intra-zonal corridor must
#: price ABOVE the generation hub that feeds it.
PAIRS: tuple[tuple[str, str, str], ...] = (
    ("DLAP_SCE-APND", "TH_SP15_GEN-APND", "SCE_pocket-SP15_gen"),
    ("DLAP_SDGE-APND", "TH_SP15_GEN-APND", "SDGE_pocket-SP15_gen"),
    # Context, so a null result LOCATES the congestion instead of only ruling
    # this corridor out.
    ("DLAP_SCE-APND", "TH_ZP26_GEN-APND", "SCE_pocket-ZP26_gen"),
    ("DLAP_SCE-APND", "TH_NP15_GEN-APND", "SCE_pocket-NP15_gen"),
    ("DLAP_PGAE-APND", "TH_NP15_GEN-APND", "PGAE_pocket-NP15_gen"),
    ("DLAP_SDGE-APND", "DLAP_SCE-APND", "SDGE_pocket-SCE_pocket"),
    # The caiso-164 baseline, recomputed here on the same code path so the new
    # numbers are comparable to the finding's table without re-reading it.
    ("TH_NP15_GEN-APND", "TH_ZP26_GEN-APND", "NP15_gen-ZP26_gen"),
)

#: Model zone pairs mirroring the measured corridors, read off the caiso-164
#: keeper's committed hourly sidecars (no replay).
MODEL_PAIRS: tuple[tuple[str, str, str], ...] = (
    ("LA_BASIN", "SP15_rest", "SCE_pocket-SP15_gen"),
    ("SDGE", "SP15_rest", "SDGE_pocket-SP15_gen"),
    ("NP15", "ZP26", "NP15_gen-ZP26_gen"),
)

#: A price difference below this is numerical noise, not a separated node.
#: Same value as the caiso-164 probe, so the two are read on one scale.
TOL = 0.01

#: The solar belly, Pacific local hours (inclusive) — caiso-164 §1.3 / §1.4's
#: own window, carried over unchanged so the comparison is like-for-like.
BELLY = (9, 16)

#: Pre-registered verdict thresholds (PRECHECK-caiso165 §4).
CONFIRM_FREQ_PCT = 50.0
CONFIRM_MEAN_ABS = 1.00
CONFIRM_DIR_PCT = 60.0
FALSIFY_FREQ_PCT = 20.0
FALSIFY_MEAN_ABS = 0.25


def measured(year: int) -> pd.DataFrame:
    """Return the hourly measured component frame for ``year``, GMT-indexed.

    Columns are ``<node>_<component>`` for LMP / MCE / MCC / MCL / MGHG.  Only
    hours in which **every** requested node printed are kept: a basis built
    from two different hour sets is not a basis.

    **MGHG is optional and is NOT allowed to drop an hour.** The GHG component
    is a late addition to ``PRC_LMP`` v12 and is simply absent from the
    bulk-``GRP``-sourced early-2023 rows (measured: 2,640 null MGHG cells and
    zero null LMP/MCE/MCC/MCL cells in the 2023 aggregate). Requiring it
    would silently discard every hour that only the GRP route can supply — the
    aged-out head of the record — so completeness is enforced on the four core
    components that make up the decomposition under test, MGHG is filled with
    0.0, and the fill count is reported by the caller's identity guard rather
    than buried.
    """
    path = DAM / f"CAISO_dam_hourly_{year}.csv"
    if not path.is_file():
        raise SystemExit(f"no CAISO DAM component file at {path}")
    df = pd.read_csv(path)
    want = [n for n in (*GEN_HUBS, *DLAPS) if n in set(df["node"])]
    df = df[df["node"].isin(want)]
    core = [c for c in ("LMP", "MCE", "MCC", "MCL") if c in df.columns]
    comps = core + (["MGHG"] if "MGHG" in df.columns else [])
    wide = df.pivot_table(
        index="interval_start_gmt", columns="node", values=comps, aggfunc="mean"
    )
    wide.columns = [f"{node}_{comp}" for comp, node in wide.columns]
    ghg_cols = [c for c in wide.columns if c.endswith("_MGHG")]
    wide.attrs["mghg_filled"] = int(wide[ghg_cols].isna().sum().sum())
    wide[ghg_cols] = wide[ghg_cols].fillna(0.0)
    wide = wide.dropna()
    wide.index = pd.to_datetime(wide.index, utc=True)
    return wide.sort_index()


def model_frame(year: int, value: str) -> pd.DataFrame:
    """Return the caiso-164 keeper's P1 hour x zone frame for ``value``."""
    d = pd.read_parquet(KEEPER / f"hourly/system_{year}.parquet")
    d = d[d["pass"] == "P1"]
    return d.pivot_table(index="hour", columns="zone", values=value)


def _split(diff: np.ndarray) -> dict:
    """Frequency / conditional-magnitude decomposition of a basis series."""
    sep = np.abs(diff) > TOL
    pos = sep & (diff > 0)
    return {
        "hours": int(len(diff)),
        "sep_hours": int(sep.sum()),
        "sep_pct": round(100.0 * float(sep.mean()), 3) if len(diff) else 0.0,
        "mean": round(float(diff.mean()), 4) if len(diff) else 0.0,
        "mean_abs": round(float(np.abs(diff).mean()), 4) if len(diff) else 0.0,
        "cond_absmean_when_sep": round(
            float(np.abs(diff[sep]).mean()) if sep.any() else 0.0, 4
        ),
        "pos_hours": int(pos.sum()),
        "pos_pct_of_sep": round(
            100.0 * float(pos.sum()) / max(1, int(sep.sum())), 2
        ),
        "p95_abs": round(float(np.percentile(np.abs(diff), 95)), 4) if len(diff) else 0.0,
        "max_abs": round(float(np.abs(diff).max()), 4) if len(diff) else 0.0,
    }


def _verdict(freq_pct: float, mean_abs: float, dir_pct: float) -> str:
    """Apply the pre-registered verdict rule to one belly-window measurement."""
    if freq_pct < FALSIFY_FREQ_PCT or mean_abs < FALSIFY_MEAN_ABS:
        return "FALSIFIED"
    if (
        freq_pct >= CONFIRM_FREQ_PCT
        and mean_abs >= CONFIRM_MEAN_ABS
        and dir_pct >= CONFIRM_DIR_PCT
    ):
        return "CONFIRMED"
    return "PARTIAL"


def main() -> int:
    """Print the caiso-165 intra-SP15 measurement; always returns 0."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--json", default=None, help="also write the report here")
    args = ap.parse_args()

    report: dict = {
        "coverage": {},
        "identity": {},
        "measured": {},
        "belly": {},
        "model": {},
        "verdict": {},
        "thresholds": {
            "confirm_freq_pct": CONFIRM_FREQ_PCT,
            "confirm_mean_abs": CONFIRM_MEAN_ABS,
            "confirm_dir_pct": CONFIRM_DIR_PCT,
            "falsify_freq_pct": FALSIFY_FREQ_PCT,
            "falsify_mean_abs": FALSIFY_MEAN_ABS,
            "belly_hours_pacific": list(BELLY),
            "tol": TOL,
        },
    }
    frames = {}

    print("=" * 79)
    print("A. COVERAGE — what the DLAP intake actually landed")
    print("   2023 is PARTIAL by construction: PRC_LMP retention starts")
    print("   2023-04-22 (re-measured 2026-08-04) and MOVES with the calendar.")
    print("=" * 79)
    print(f"{'yr':>5} {'complete hours':>15} {'nodes':>7} {'first':>12} {'last':>12}")
    for year in YEARS:
        m = measured(year)
        frames[year] = m
        nodes = sorted({c.rsplit("_", 1)[0] for c in m.columns})
        row = {
            "complete_hours": int(len(m)),
            "n_nodes": len(nodes),
            "nodes": nodes,
            "first": str(m.index.min()),
            "last": str(m.index.max()),
        }
        report["coverage"][str(year)] = row
        print(
            f"{year:>5} {len(m):>15,} {len(nodes):>7} "
            f"{str(m.index.min())[:10]:>12} {str(m.index.max())[:10]:>12}"
        )
    for year in YEARS:
        print(f"  {year} nodes: {', '.join(report['coverage'][str(year)]['nodes'])}")

    print()
    print("=" * 79)
    print("B. IDENTITY GUARDS — is the decomposition usable as published?")
    print("   MCE must be ONE system reference across ALL nodes (incl. DLAPs),")
    print("   and LMP must reconstruct from its components.")
    print("=" * 79)
    for year in YEARS:
        m = frames[year]
        if m.empty:
            print(f"{year}: no complete hours — identity guard skipped")
            report["identity"][str(year)] = {"complete_hours": 0}
            continue
        nodes = sorted({c.rsplit("_", 1)[0] for c in m.columns})
        mce = m[[f"{n}_MCE" for n in nodes]].to_numpy()
        mce_spread = float(np.abs(mce.max(axis=1) - mce.min(axis=1)).max())
        recon = []
        for n in nodes:
            parts = m[f"{n}_MCE"] + m[f"{n}_MCC"] + m[f"{n}_MCL"]
            if f"{n}_MGHG" in m.columns:
                parts = parts + m[f"{n}_MGHG"]
            recon.append(float(np.abs(parts - m[f"{n}_LMP"]).max()))
        ghg = {
            n: round(float(np.abs(m[f"{n}_MGHG"]).max()), 6)
            for n in nodes
            if f"{n}_MGHG" in m.columns
        }
        report["identity"][str(year)] = {
            "complete_hours": int(len(m)),
            "max_MCE_spread_across_nodes": round(mce_spread, 8),
            "max_LMP_reconstruction_error": round(max(recon), 6),
            "max_abs_MGHG_by_node": ghg,
            "mghg_cells_filled_zero": int(m.attrs.get("mghg_filled", 0)),
        }
        print(
            f"{year}: max MCE spread across {len(nodes)} nodes "
            f"{mce_spread:.2e} $/MWh; max |LMP - (MCE+MCC+MCL+MGHG)| "
            f"{max(recon):.2e} $/MWh"
        )
        print(
            f"      max |MGHG| by node: {ghg}"
            f"  (MGHG cells filled 0: {m.attrs.get('mghg_filled', 0):,})"
        )

    print()
    print("=" * 79)
    print("C. MEASURED BASIS, ALL HOURS — decomposed into CONGESTION vs LOSS")
    print("   basis = dMCE + dMCC + dMCL (+ dMGHG); dMCE == 0 by construction")
    print("=" * 79)
    print(
        f"{'yr':>5} {'corridor':>24} {'mean tot':>9} {'dMCC':>8} {'dMCL':>8} "
        f"{'cong%':>7} {'loss%':>7} {'sep%':>7} {'pocket-dearer %':>16}"
    )
    for year in YEARS:
        m = frames[year]
        if m.empty:
            continue
        for near, far, label in PAIRS:
            if f"{near}_LMP" not in m.columns or f"{far}_LMP" not in m.columns:
                continue
            tot = (m[f"{near}_LMP"] - m[f"{far}_LMP"]).to_numpy()
            dmcc = (m[f"{near}_MCC"] - m[f"{far}_MCC"]).to_numpy()
            dmcl = (m[f"{near}_MCL"] - m[f"{far}_MCL"]).to_numpy()
            dmce = (m[f"{near}_MCE"] - m[f"{far}_MCE"]).to_numpy()
            s_tot, s_cc, s_cl = _split(tot), _split(dmcc), _split(dmcl)
            denom = float(tot.mean())

            def share(x: np.ndarray, _d: float = denom) -> float:
                """Component's share of the total basis, in per cent."""
                return (
                    100.0 * float(x.mean()) / _d if abs(_d) > 1e-9 else float("nan")
                )

            report["measured"][f"{year}_{label}"] = {
                "mean_total": s_tot["mean"],
                "mean_dMCE": round(float(dmce.mean()), 8),
                "mean_dMCC": s_cc["mean"],
                "mean_dMCL": s_cl["mean"],
                "congestion_share_pct": round(share(dmcc), 2),
                "loss_share_pct": round(share(dmcl), 2),
                "total": s_tot,
                "dMCC": s_cc,
                "dMCL": s_cl,
            }
            print(
                f"{year:>5} {label:>24} {s_tot['mean']:>9.3f} {s_cc['mean']:>8.3f} "
                f"{s_cl['mean']:>8.3f} {share(dmcc):>6.1f}% {share(dmcl):>6.1f}% "
                f"{s_cc['sep_pct']:>6.2f}% {s_cc['pos_pct_of_sep']:>15.1f}%"
            )

    print()
    print("=" * 79)
    print(f"D. THE BELLY WINDOW — Pacific local hours {BELLY[0]:02d}-{BELLY[1]:02d},")
    print("   where caiso-164 measured the model's five zones as one copperplate.")
    print("   CONGESTION COMPONENT ONLY (dMCC) — the quantity under test.")
    print("=" * 79)
    print(
        f"{'yr':>5} {'corridor':>24} {'belly h':>8} {'sep h':>7} {'sep %':>7} "
        f"{'mean dMCC':>10} {'mean |dMCC|':>12} {'p95 |dMCC|':>11} "
        f"{'pocket-dearer %':>16}"
    )
    for year in YEARS:
        m = frames[year]
        if m.empty:
            continue
        loc = m.index.tz_convert("America/Los_Angeles")
        belly = (loc.hour >= BELLY[0]) & (loc.hour <= BELLY[1])
        for near, far, label in PAIRS:
            if f"{near}_MCC" not in m.columns or f"{far}_MCC" not in m.columns:
                continue
            dmcc = (m[f"{near}_MCC"] - m[f"{far}_MCC"]).to_numpy()[belly]
            s = _split(dmcc)
            report["belly"][f"{year}_{label}"] = s
            print(
                f"{year:>5} {label:>24} {s['hours']:>8,} {s['sep_hours']:>7,} "
                f"{s['sep_pct']:>6.2f}% {s['mean']:>10.3f} {s['mean_abs']:>12.3f} "
                f"{s['p95_abs']:>11.3f} {s['pos_pct_of_sep']:>15.1f}%"
            )

    print()
    print("=" * 79)
    print("E. THE PRE-REGISTERED VERDICT (PRECHECK-caiso165 §4)")
    print(
        f"   CONFIRMED: belly sep >= {CONFIRM_FREQ_PCT:.0f} % AND mean |dMCC| "
        f">= {CONFIRM_MEAN_ABS:.2f} AND pocket-dearer >= {CONFIRM_DIR_PCT:.0f} %"
    )
    print(
        f"   FALSIFIED: belly sep < {FALSIFY_FREQ_PCT:.0f} % OR mean |dMCC| "
        f"< {FALSIFY_MEAN_ABS:.2f}"
    )
    print("=" * 79)
    for near, far, label in PAIRS[:2]:  # the two attribution corridors
        for year in YEARS:
            key = f"{year}_{label}"
            if key not in report["belly"]:
                continue
            s = report["belly"][key]
            v = _verdict(s["sep_pct"], s["mean_abs"], s["pos_pct_of_sep"])
            report["verdict"][key] = {
                "belly_sep_pct": s["sep_pct"],
                "belly_mean_abs_dMCC": s["mean_abs"],
                "belly_pocket_dearer_pct": s["pos_pct_of_sep"],
                "verdict": v,
            }
            print(
                f"  {year} {label:>24}: sep {s['sep_pct']:>6.2f} %, "
                f"mean |dMCC| {s['mean_abs']:>7.3f} $/MWh, pocket-dearer "
                f"{s['pos_pct_of_sep']:>5.1f} %  ->  {v}"
            )

    print()
    print("=" * 79)
    print("F. WHAT THE MODEL DOES ON THE SAME CORRIDORS (caiso-164 keeper, P1)")
    print("   committed hourly sidecars — no replay, no solve")
    print("=" * 79)
    if (KEEPER / "hourly").is_dir():
        print(
            f"{'yr':>5} {'corridor':>24} {'belly h':>8} {'sep h':>7} {'sep %':>7} "
            f"{'mean':>9} {'pocket-dearer %':>16}"
        )
        for year in YEARS:
            mp = model_frame(year, "price")
            mh = np.arange(len(mp)) % 24
            belly = (mh >= BELLY[0]) & (mh <= BELLY[1])
            for near, far, label in MODEL_PAIRS:
                diff = (mp[near] - mp[far]).to_numpy()[belly]
                s = _split(diff)
                report["model"][f"{year}_{label}"] = s
                print(
                    f"{year:>5} {label:>24} {s['hours']:>8,} {s['sep_hours']:>7,} "
                    f"{s['sep_pct']:>6.2f}% {s['mean']:>9.4f} "
                    f"{s['pos_pct_of_sep']:>15.1f}%"
                )
    else:
        print(f"  keeper hourly sidecars not present at {KEEPER}/hourly — skipped")

    print()
    print("=" * 79)
    print("G. DIURNAL SHAPE — measured dMCC by Pacific local hour")
    print("   is the intra-SP15 congestion BELLY-TIMED, as the attribution needs?")
    print("=" * 79)
    for near, far, label in PAIRS[:2]:
        for year in YEARS:
            m = frames[year]
            if m.empty or f"{near}_MCC" not in m.columns:
                continue
            loc = m.index.tz_convert("America/Los_Angeles")
            s = pd.Series((m[f"{near}_MCC"] - m[f"{far}_MCC"]).to_numpy(), index=loc)
            by = s.groupby(loc.hour).mean()
            report.setdefault("diurnal", {})[f"{year}_{label}"] = {
                int(h): round(float(v), 3) for h, v in by.items()
            }
            print(
                f"{year} {label:>24}: "
                + " ".join(f"{h:02d}:{v:+.2f}" for h, v in by.items())
            )

    if args.json:
        Path(args.json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json).write_text(json.dumps(report, indent=2))
        print(f"\nwrote {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
