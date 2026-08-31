"""c3c-Q2 (read-only, no LP): **SUPERSEDED AND DEFECTIVE — retained as the
reproducible record of a FALSE POSITIVE. Do not cite its numbers.**

**For the correct Q2 measurement use
``scripts/probes/nyiso164_nyca_shortage_check.py``**
(record ``results/calibration/_nyiso164_nyca_shortage_check.json``, finding
``docs/FINDING-nyiso164-c3c-product-level-2026-09-01.md``), which answers charter
Q2 **CONFIRMED — reality was NOT NYCA-short in its own price tail**.

This probe answered the same question NEGATIVE (i.e. "reality WAS NYCA-short"),
and that answer is **WRONG**. It is kept, unrepaired, because
``docs/FINDING-c3c-q2-nyiso-nyca-shortage-2026-08-31.md`` §3 documents the two
defects it inherited, and a finding that describes a false positive should ship
with the construction that produced it. **Both defects are in the committed input
it reads, not in this file's arithmetic** — which is the point of §4 of that
finding:

* **Defect A (aggregate).** It reads ``nyca_reserve_adder`` from
  ``data/raw/_validation-source/actual_as_reserve_NYISO.parquet``, which
  ``scripts/data/process_nyiso_as.py::build_reference`` computes as
  ``spin_10 + nonsync_10 + op_30``. NYISO's three posted products are a
  **cumulative cascade**, not increments: ``spin_10 >= nonsync_10 >= op_30``
  holds in 100.0000 % of 289,344 rows across all zones and all three years, and
  all three are exactly equal in 82-84 % of them. A 10-minute spinning MW earns
  ``spin_10``, NOT the sum. Summing triple-counts one shadow price (exactly 3.0x
  in 28-79 % of priced hours) and is what breaks the opportunity-cost-vs-shortage
  ceiling test below.
* **Defect B (clock).** ``build_reference`` maps the CSV's naive **prevailing**
  Eastern ``Time Stamp`` onto the model's 8760 index positionally, while the
  model's NYISO clock is fixed standard time ``Etc/GMT+5``
  (``derive_actual_lmp._STD_TZ``). The two differ through the whole DST season —
  5,710 of 8,760 hours — which is where every tail hour sits.

**The corrected measurement** (independently re-derived from the raw
``data/raw/NYISO-AS/NYISO_as_rt_<year>.csv``, taking the cascade MAX and
localizing prevailing -> ``Etc/GMT+5``) reproduces nyiso-164 exactly: NYCA-tier
tail-hour mean $306.74 / $254.62 / $393.31, and the NYCA-tier price exceeds the
concurrent LMP in **0 of 65** tail hours (ratio median 0.573 / 0.536 / 0.654).
A reserve holder's opportunity cost is bounded by LMP; an RCPF shortage price is
not. So the tail's reserve prices are the opportunity cost of scarce ENERGY, and
the charter's kill gate FIRES.

---

Original (defective) description follows, unaltered, for the record.

Executes question Q2 of ``docs/CHARTER-c3c-scarcity-program-2026-08-31.md`` §5,
opened by the charter's own chaining condition after Q1 returned REAL
(``docs/FINDING-c3c-q1-pjm-phantom-audit-2026-08-31.md``). **Solves nothing,
scores nothing, modifies nothing** — no LP, no re-score, 2023-2025 only.

The charter's §2 census established that the NYISO keeper's scarcity channel is
capped by construction: only the cheap locational families
(``nyc_10min_total`` / ``nyc_30min_total`` at $25/MW, ``seny_30min_total`` at
$40/MW) ever bind, while the expensive NYCA-level products
(``nyca_10min_total`` $750, ``nyca_10min_spin`` $775) never bind in any hour of
any year — a maximum available reserve adder of $90 against an actual tail mean
of $505/$517/$659. §3 established the TIMING is right (the model is short in
reality's tail hours). Q2 asks the remaining question: was reality short on the
NYCA-level REQUIREMENT in those hours, or only on the locational ones the model
already prices?

**The instrument is reality-vs-reality**, so no model/published clock alignment
is at stake for the kill gate:

* ``data/raw/_validation-source/actual_as_reserve_NYISO.parquet`` column
  ``nyca_reserve_adder`` — the stacked RT reserve price (``spin_10 +
  nonsync_10 + op_30``) at the **WEST** settlement zone, hourly max over the
  5-minute postings, already on the model's non-leap 8760 clock
  (``scripts/data/process_nyiso_as.py::build_reference``). WEST lies outside
  every locational region (East / SENY / NYC / LI), so its stacked RT reserve
  price carries the NYCA-level component ALONE — it *is* the published
  NYCA-level reserve shadow price. Ultimate source: NYISO MIS public
  ``rtasp`` postings.
* ``data/raw/_validation-source/actual_lmp_hourly_NYISO.parquet`` column
  ``rt`` — the actual NYCA-hub hourly RT price, the same series
  ``derive_actual_tail.py`` counts the C3c tail from, on the same clock.

Severity tiers, all published: ``> 0`` (the NYCA constraint priced at all),
``>= $40`` (the first step of the published NYCA 30-minute $40..$750 RCPF
curve, ``NYISO_RCPF_EAST_FAMILIES``), ``>= $100``, and ``>= $750`` (the NYCA
RCPF ceiling carried in ``NYISO_RCPF_PRODUCTS`` — unambiguous deep NYCA
shortage).

Four measurements:

1. **The kill gate.** Reality's C3c tail hours (actual RT > $300, the rubric §5
   NYISO threshold) against the NYCA-level severity tiers, with the year's base
   rate, lift and a one-sided hypergeometric p-value. The charter's gate: if
   reality's tail hours show NO NYCA-level shortage, NYISO's C3c ledger is
   CONFIRMED and the leg closes as CAISO's did.
2. **The model's NYCA families in exactly those hours** — dual, shortfall and
   held-vs-requirement slack, read from the keeper's committed
   ``reserve_family_<y>.parquet`` (rule 15: the only artifact in which a
   family's binding is observable).
3. **The residual it sizes.** Actual RT, the published NYCA adder, and the
   model's max-zonal energy dual in the tail hours and in the NYCA-short
   subset.
4. **Requirement-level attribution.** Whether the model's static NYCA
   requirement equals the published as-enforced requirement (if it does, the
   gap is a supply/headroom object, not a requirement-level one).

Usage::

    python scripts/probes/c3c_q2_nyiso_nyca_shortage.py \
        [--out results/calibration/_c3c_q2_nyiso_nyca_shortage.json]
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]

KEEPER_ID = "2026-08-30-nyiso-159-loss-surface"
BUNDLE = REPO / "results" / "calibration" / "nyiso159_lossarm_B"
VS = REPO / "data" / "raw" / "_validation-source"
AS_REF = VS / "actual_as_reserve_NYISO.parquet"
LMP_REF = VS / "actual_lmp_hourly_NYISO.parquet"

YEARS = (2023, 2024, 2025)
TAIL_THRESHOLD = 300.0  # rubric section 5, NYISO (calibration_verdict.TAIL_THRESHOLD)
# The three NYCA-level (system-wide) products, NYISO_RCPF_PRODUCTS.
NYCA_FAMILIES = ("nyca_10min_spin", "nyca_10min_total", "nyca_30min_total")
# The locational families the model DOES bind on (charter section 2).
LOCATIONAL_FAMILIES = ("nyc_10min_total", "nyc_30min_total", "seny_30min_total")
# Published NYCA-level severity tiers ($/MW of the stacked RT reserve price).
TIERS = (
    ("gt_0", 0.01, "NYCA reserve constraint priced at all"),
    ("ge_40", 40.0, "first step of the published NYCA 30-min $40..$750 RCPF curve"),
    ("ge_100", 100.0, "well up the published NYCA RCPF curve"),
    ("ge_750", 750.0, "at/above the NYCA RCPF ceiling (NYISO_RCPF_PRODUCTS)"),
)


def _hypergeom_sf(k: int, N: int, K: int, n: int) -> float:
    """P(X >= k) for X ~ Hypergeometric(N population, K successes, n draws)."""
    if n == 0 or K == 0:
        return 1.0
    denom = math.comb(N, n)
    return sum(
        math.comb(K, i) * math.comb(N - K, n - i) for i in range(k, min(K, n) + 1)
    ) / denom


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--out",
        default=str(
            REPO / "results" / "calibration" / "_c3c_q2_nyiso_nyca_shortage.json"
        ),
    )
    args = ap.parse_args()

    res = pd.read_parquet(AS_REF)
    lmp = pd.read_parquet(LMP_REF)

    out: dict = {
        "charter": "docs/CHARTER-c3c-scarcity-program-2026-08-31.md section 5 Q2",
        "opened_by": "docs/FINDING-c3c-q1-pjm-phantom-audit-2026-08-31.md (Q1 = REAL)",
        "keeper": KEEPER_ID,
        "bundle": str(BUNDLE.relative_to(REPO)),
        "nyca_observable": {
            "series": "actual_as_reserve_NYISO.parquet::nyca_reserve_adder",
            "definition": (
                "stacked RT reserve price (spin_10 + nonsync_10 + op_30) at the "
                "WEST settlement zone, hourly max over the 5-minute NYISO MIS "
                "rtasp postings, on the model's non-leap 8760 clock"
            ),
            "why_it_is_the_nyca_level": (
                "WEST lies outside every locational region (East / SENY / NYC / "
                "LI), so its stacked RT reserve price carries the NYCA-level "
                "component alone"
            ),
            "builder": "scripts/data/process_nyiso_as.py::build_reference",
        },
        "solve": "none — read-only over committed artifacts and published data",
        "years": {},
    }

    for year in YEARS:
        r = res[res["year"] == year].set_index("hour")["nyca_reserve_adder"]
        a = lmp[lmp["year"] == year].set_index("hour")["rt"]
        n_cov = int(r.notna().sum())
        tail = sorted(int(h) for h in a.index[a > TAIL_THRESHOLD])

        rf = pd.read_parquet(BUNDLE / "hourly" / f"reserve_family_{year}.parquet")
        sysd = pd.read_parquet(BUNDLE / "hourly" / f"system_{year}.parquet")
        mx = sysd.groupby("hour")["price"].max().reindex(range(8760))

        gate: dict = {}
        for key, thr, why in TIERS:
            hrs = set(int(h) for h in r.index[(r >= thr).fillna(False)])
            hits = len(set(tail) & hrs)
            gate[key] = {
                "threshold_usd_per_mw": thr,
                "meaning": why,
                "reality_hours_in_year": len(hrs),
                "base_rate": round(len(hrs) / n_cov, 6) if n_cov else None,
                "tail_hours_with_nyca_shortage": hits,
                "share_of_tail": round(hits / len(tail), 4) if tail else None,
                "lift_vs_base_rate": (
                    round((hits / len(tail)) / (len(hrs) / n_cov), 2)
                    if tail and hrs and n_cov
                    else None
                ),
                "hypergeom_p_ge": (
                    round(_hypergeom_sf(hits, n_cov, len(hrs), len(tail)), 12)
                    if tail and hrs and n_cov
                    else None
                ),
            }

        nyca_short_tail = [h for h in tail if float(r.get(h, 0.0) or 0.0) >= 40.0]

        def _fam_state(fams: tuple[str, ...], hrs: list[int]) -> dict:
            sub = rf[rf["family"].isin(fams) & rf["hour"].isin(hrs)]
            if sub.empty:
                return {}
            slack = sub["held_mw"] - sub["requirement_mw"]
            return {
                "hours": len(hrs),
                "max_dual": round(float(sub["dual"].max()), 4),
                "hours_any_dual_gt_0": int(sub[sub["dual"] > 1e-6]["hour"].nunique()),
                "max_shortfall_mw": round(float(sub["shortfall_mw"].max()), 3),
                "hours_any_shortfall": int(
                    sub[sub["shortfall_mw"] > 1e-6]["hour"].nunique()
                ),
                "min_slack_mw": round(float(slack.min()), 2),
                "mean_slack_mw": round(float(slack.mean()), 2),
            }

        def _levels(hrs: list[int]) -> dict:
            if not hrs:
                return {}
            return {
                "n": len(hrs),
                "actual_rt_mean": round(float(a.loc[hrs].mean()), 1),
                "actual_rt_max": round(float(a.loc[hrs].max()), 1),
                "published_nyca_adder_mean": round(float(r.loc[hrs].mean()), 1),
                "published_nyca_adder_max": round(float(r.loc[hrs].max()), 1),
                "model_max_zonal_dual_mean": round(float(mx.loc[hrs].mean()), 1),
                "model_max_zonal_dual_max": round(float(mx.loc[hrs].max()), 1),
            }

        # Requirement-level attribution: is the model's NYCA requirement static
        # at the published MW in every hour?
        req_attr = {}
        for fam in NYCA_FAMILIES:
            f = rf[rf["family"] == fam]
            req_attr[fam] = {
                "requirement_mw_unique": sorted(
                    round(float(v), 2) for v in f["requirement_mw"].unique()
                )[:5],
                "held_equals_requirement_all_hours": bool(
                    np.allclose(f["held_mw"], f["requirement_mw"], atol=1e-3)
                ),
                "min_slack_mw": round(
                    float((f["held_mw"] - f["requirement_mw"]).min()), 2
                ),
                "hours_dual_gt_0": int((f["dual"] > 1e-6).sum()),
                "hours_shortfall_gt_0": int((f["shortfall_mw"] > 1e-6).sum()),
            }

        out["years"][str(year)] = {
            "covered_hours": n_cov,
            "actual_tail_hours_gt300": len(tail),
            "kill_gate": gate,
            "nyca_short_tail_hours_ge40": len(nyca_short_tail),
            "model_nyca_families_in_tail_hours": _fam_state(NYCA_FAMILIES, tail),
            "model_nyca_families_in_nyca_short_tail_hours": _fam_state(
                NYCA_FAMILIES, nyca_short_tail
            ),
            "model_locational_families_in_tail_hours": _fam_state(
                LOCATIONAL_FAMILIES, tail
            ),
            "levels_all_tail": _levels(tail),
            "levels_nyca_short_subset": _levels(nyca_short_tail),
            "requirement_attribution": req_attr,
        }

    out["SUPERSEDED"] = (
        "DEFECTIVE — do not cite. Charter Q2 is answered CONFIRMED by "
        "scripts/probes/nyiso164_nyca_shortage_check.py; this construction "
        "inherits two defects from actual_as_reserve_NYISO.parquet (cascade "
        "summed instead of maxed; naive prevailing->8760 positional clock). See "
        "docs/FINDING-c3c-q2-nyiso-nyca-shortage-2026-08-31.md sections 3-4."
    )
    Path(args.out).write_text(json.dumps(out, indent=1) + "\n")
    print("*** SUPERSEDED/DEFECTIVE probe — see docstring; do not cite these numbers ***")
    print(f"wrote {args.out}")

    for year in YEARS:
        y = out["years"][str(year)]
        print(f"\n=== {year} === actual tail (>${TAIL_THRESHOLD:.0f}) "
              f"{y['actual_tail_hours_gt300']} h")
        for key, g in y["kill_gate"].items():
            print(
                f"  NYCA {key:6s} (>= ${g['threshold_usd_per_mw']:>6.2f}) "
                f"{g['tail_hours_with_nyca_shortage']:3d}/{y['actual_tail_hours_gt300']:<3d} "
                f"share {g['share_of_tail']} base {g['base_rate']} "
                f"lift {g['lift_vs_base_rate']} p {g['hypergeom_p_ge']}"
            )
        m = y["model_nyca_families_in_tail_hours"]
        if m:
            print(
                f"  model NYCA families in those hours: max dual ${m['max_dual']}, "
                f"hours dual>0 {m['hours_any_dual_gt_0']}, max shortfall "
                f"{m['max_shortfall_mw']} MW, hours shortfall>0 {m['hours_any_shortfall']}"
            )
        lv = y["levels_all_tail"]
        if lv:
            print(
                f"  levels: actual RT mean ${lv['actual_rt_mean']} | published NYCA "
                f"adder mean ${lv['published_nyca_adder_mean']} (max "
                f"${lv['published_nyca_adder_max']}) | model max-zonal mean "
                f"${lv['model_max_zonal_dual_mean']}"
            )


if __name__ == "__main__":
    main()
