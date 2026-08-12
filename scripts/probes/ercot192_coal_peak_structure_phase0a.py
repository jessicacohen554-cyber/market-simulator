"""ERCOT-192 Phase 0a — INSTRUMENT-STRUCTURE diagnostic for the two COAL limbs.

NO LP, no solve, no mechanism, keeper UNCHANGED, **and no price level of any
kind is read here**. This file exists to ground the *instrument design* of the
ercot-192 precommit in measured structure rather than in assumption, while
keeping the precommit's decision rule genuinely pre-registered: it reports only
the ERCOT-123 coverage/headroom decomposition of the delivery-2023 COAL rows and
of the four committed 2024/25 identification subsets.

**Why it is needed.** ercot-169 could not license either COAL limb on
delivery-2023 (``curve_share`` 0.9702 vs the 0.9876 floor); ercot-171 removed the
shortfall with a resource-drop rule that PASSED neutrality on limb A (a median of
the curve bottom) and FAILED it decisively on limb C (a p90 of the curve top,
+19.17 = 7.6x band), because dropping 26.1 % of HSL-cap moves a top-decile
boundary. Its closing sentence — *"an instrument that does not select on the tail
would need its own charter"* — is what card B / signature B1 charters. Designing
that instrument requires knowing what the missing rows ARE:

* If the no-curve rows carry little RT-dispatchable headroom (self-scheduled at
  or near their telemetered output), they contribute ~nothing to an
  incremental-MW-weighted statistic, and ``curve_share`` — an UNWEIGHTED share of
  resource-intervals — is not the exposure limb C's own statistic integrates
  over. The exposure-matched quantity is then ERCOT-123's headroom-weighted
  ``a_offered``.
* If instead they carry real unoffered headroom, the coverage gap is genuine
  exposure and must be repaired, not re-expressed.

Rule 13 ``[R-MEASURED]`` scope: a measured corpus read on an already-accepted
convention (``ercot123._decompose``, imported verbatim through the ercot-169
harness). No ``ScenarioConfig`` field, no solve path, no residual consulted.
Rule 22 ``[R-HOLDOUT]``: the corpus loader refuses any year outside 2023-2025.

Usage::

    PYTHONPATH=.:src python3 scripts/probes/ercot192_coal_peak_structure_phase0a.py
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for _p in (
    REPO,
    REPO / "src",
    REPO / "scripts",
    REPO / "scripts" / "data",
    Path(__file__).resolve().parent,
):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

DEFAULT_OUT = REPO / "results/calibration/ercot192_coal_peak_structure.json"

#: The ERCOT-138 3.4 licensing floor, unchanged and not lowered (ercot-169/171).
LICENCE_FLOOR = 0.9876


def _subset_coal_frames() -> dict[str, pd.DataFrame]:
    """The four committed 2024/25 identification subsets, COAL rows."""
    import ercot123_coal_sced_reach as e123

    out: dict[str, pd.DataFrame] = {}
    for tag, _year, _fam in e123.SUBSETS:
        got = e123.load_sced(tag)
        if got is None:
            raise SystemExit(f"identification subset missing on disk: {tag}")
        df, _cov = got
        d = df[df["cls"] == "COAL"]
        if d.empty:
            raise SystemExit(f"no COAL rows in subset {tag}")
        out[tag] = d
    return out


def _structure(df: pd.DataFrame) -> dict:
    """Coverage + headroom structure of one COAL frame, curve vs no-curve.

    Every quantity is ``ercot123._decompose``'s own; nothing is re-implemented.
    ``curve_share`` is the UNWEIGHTED share of resource-intervals carrying a
    submitted curve (the ercot-169/171 licensing quantity); ``a_offered`` is the
    headroom-weighted offered share (the exposure an incremental-MW-weighted
    statistic actually integrates over).
    """
    import ercot123_coal_sced_reach as e123

    g = e123._decompose(df)
    hc = g["has_curve"].to_numpy(bool)
    h_rt = g["h_rt"].to_numpy(float)
    hsl = g["HSL"].to_numpy(float)
    tot_rt = float(h_rt.sum())
    return {
        "res_hours": int(len(g)),
        "resources": int(g["Resource Name"].nunique()),
        # -- the two candidate licensing quantities -------------------------
        "curve_share": float(hc.mean()),
        "a_offered": float(g["off_mw"].sum() / tot_rt) if tot_rt > 0 else float("nan"),
        # -- where the RT headroom sits, curve vs no-curve -------------------
        "h_rt_MW_total": tot_rt,
        "h_rt_share_in_nocurve_rows": float(h_rt[~hc].sum() / tot_rt)
        if tot_rt > 0
        else float("nan"),
        "hsl_share_in_nocurve_rows": float(hsl[~hc].sum() / hsl.sum())
        if hsl.sum() > 0
        else float("nan"),
        "mean_h_rt_MW_curve_rows": float(h_rt[hc].mean()) if hc.any() else float("nan"),
        "mean_h_rt_MW_nocurve_rows": float(h_rt[~hc].mean())
        if (~hc).any()
        else float("nan"),
        # -- what the no-curve headroom IS (b = price-taking, e = residual) --
        "nocurve_ss_share_of_own_h_rt": float(
            g.loc[~hc, "ss_mw"].sum() / h_rt[~hc].sum()
        )
        if (~hc).any() and h_rt[~hc].sum() > 0
        else float("nan"),
        "nocurve_res_share_of_own_h_rt": float(
            g.loc[~hc, "res_mw"].sum() / h_rt[~hc].sum()
        )
        if (~hc).any() and h_rt[~hc].sum() > 0
        else float("nan"),
        "loading_curve_rows": float(g.loc[hc, e123.NETOUT].sum() / hsl[hc].sum())
        if hc.any()
        else float("nan"),
        "loading_nocurve_rows": float(g.loc[~hc, e123.NETOUT].sum() / hsl[~hc].sum())
        if (~hc).any()
        else float("nan"),
    }


def _per_resource(df: pd.DataFrame) -> list[dict]:
    """Per-resource curve_share + the headroom it carries when it has no curve."""
    import ercot123_coal_sced_reach as e123

    g = e123._decompose(df)
    rows = []
    for name, sub in g.groupby(g["Resource Name"].astype(str)):
        hc = sub["has_curve"].to_numpy(bool)
        h_rt = sub["h_rt"].to_numpy(float)
        rows.append(
            {
                "resource": name,
                "res_hours": int(len(sub)),
                "curve_share": float(hc.mean()),
                "hsl_mean_MW": float(sub["HSL"].mean()),
                "h_rt_MW_nocurve": float(h_rt[~hc].sum()),
                "h_rt_MW_total": float(h_rt.sum()),
                "below_floor": bool(hc.mean() < LICENCE_FLOOR),
            }
        )
    rows.sort(key=lambda r: r["curve_share"])
    return rows


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    args = ap.parse_args()

    from lib.sced_corpus_instruments import MATCHED_HOURS, load_corpus_year, restrict_hours

    t0 = time.time()
    out: dict = {
        "probe": "ercot192_coal_peak_structure_phase0a",
        "charter": "DECISION-CARD-ercot188 card B / signature B1 (2026-08-11)",
        "scope": "instrument-structure only — NO price level is read here",
        "licence_floor": LICENCE_FLOOR,
        "matched_hours": list(MATCHED_HOURS),
    }

    print("loading delivery-2023 COAL corpus ...", flush=True)
    d23 = load_corpus_year(2023, classes=("COAL",))
    d23 = d23[d23["cls"] == "COAL"]
    out["delivery_2023"] = {
        "matched_window": _structure(restrict_hours(d23, MATCHED_HOURS)),
        "full_day": _structure(d23),
        "per_resource_matched": _per_resource(restrict_hours(d23, MATCHED_HOURS)),
    }

    print("loading the four 2024/25 identification subsets ...", flush=True)
    subs = _subset_coal_frames()
    out["identification_subsets"] = {
        tag: _structure(restrict_hours(df, MATCHED_HOURS)) for tag, df in subs.items()
    }
    # Pooled over the four subsets on res-hours, the derives' own pooling.
    rows = list(out["identification_subsets"].values())
    w = np.array([r["res_hours"] for r in rows], dtype=float)
    out["identification_subsets_pooled"] = {
        k: float(np.average([r[k] for r in rows], weights=w))
        for k in ("curve_share", "a_offered")
    }

    out["elapsed_s"] = round(time.time() - t0, 1)
    Path(args.out).write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "delivery_2023"}, indent=2))
    print("\ndelivery-2023 matched window:")
    print(json.dumps(out["delivery_2023"]["matched_window"], indent=2))
    print("\ndelivery-2023 full day:")
    print(json.dumps(out["delivery_2023"]["full_day"], indent=2))
    print("\nper-resource (lowest curve_share first, matched window):")
    for r in out["delivery_2023"]["per_resource_matched"][:12]:
        print(
            f"  {r['resource']:<18} share={r['curve_share']:.4f} "
            f"hsl={r['hsl_mean_MW']:.0f} MW  h_rt_nocurve={r['h_rt_MW_nocurve']:.3e} "
            f"of {r['h_rt_MW_total']:.3e}"
        )
    print(f"\nwrote {args.out}  ({out['elapsed_s']} s)")


if __name__ == "__main__":
    main()
