"""pjm-153 — attribute PJM root-cause item 15 (net-export level) with NO LP.

Item 15 was opened at pjm-151 as an OPEN root cause with its own charter owed:
PJM's modelled net export is short of actual by 12.48 / 12.22 TWh in 2023-24 and
**long** by 5.21 TWh in 2025, and pjm-151 recorded that the seam repair moved all
three the same direction, so the remainder is not a seam-*deliverability* defect.

The prior session (label `pjm-152`, merged) committed the scoping half —
``results/calibration/_pjm152_item15_scope.json``, written by
``scripts/probes/pjm152_seam_export_level_scope.py`` — but wrote no finding, so
its three measurements were never adjudicated. This probe reads that committed
artifact plus the keeper's own committed attestation and closes the arithmetic:

1. **The benchmark check.** Item 15's residual is stated against the ``interchange``
   family actual, which is EIA-930 ``Total interchange``. The scope file also
   carries PJM's settlement-grade tie file and EIA-930's own internal identity
   (``Net generation - Demand``). Where the two measured sources disagree, the
   residual's *sign* is a property of the benchmark, not of the model.

2. **The ceiling check.** Summing each seam's measured p90 export envelope over
   8760 h gives the maximum annual export the cap admits at any price. Compared
   against the measured annual export, this says whether the cap can bind at all.

3. **The ladder-clearing attribution.** An export band is a negative-output
   pseudo-unit offered at ``p_k``; it clears when PJM's internal price sits at or
   below ``p_k``, so its annual energy is ``width_k x 8760 x P(price <= p_k)``.
   Evaluating that sum at the model's own price duration curve and at the one the
   ladder was identified on turns the per-band duration gap into TWh, per seam and
   per year. If that number reproduces the observed shortfall, item 15's owner is
   the model's price duration curve -- not the seam.

**No LP is solved, no keeper is touched, no artifact is regenerated.** Every
number is read from committed bytes. Training years only (2023-2025), rule 22.

Usage::

    PYTHONPATH=.:src python scripts/probes/pjm153_item15_ladder_attribution.py \
        [--out results/calibration/_pjm153_item15_attribution.json]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCOPE = REPO / "results" / "calibration" / "_pjm152_item15_scope.json"
ATTEST = (
    REPO / "results" / "calibration" / "pjm151_seam_B" / "calibration_attestation.json"
)
YEARS = ("2023", "2024", "2025")
HOURS = 8760

#: Item 15's residual as pjm-151 stated it, against the ``interchange`` family
#: actual (EIA-930 ``Total interchange``). Carried here verbatim so the probe can
#: show what changes when the benchmark is swapped for PJM's own tie file.
ITEM15_AS_STATED = {
    "2023": {"actual_twh": 39.98, "model_twh": 27.50},
    "2024": {"actual_twh": 32.64, "model_twh": 20.42},
    "2025": {"actual_twh": 17.97, "model_twh": 23.18},
}


def _band_width_mw(seam_rows: list[dict], interface_limit_mw: float) -> float:
    """Return the ladder's uniform band width for one seam.

    The derive lays the ladder on a fixed 8-band grid spanning the interface
    limit, so the width is ``limit / n_bands``. That is cross-checked against the
    committed band mid-point spacing so a future re-grid is caught here rather
    than silently mis-weighting the attribution. The committed mid-points are
    rounded to 0.1 MW, which alternates the spacing by +/-0.1 (e.g. LGEE's true
    137.5 MW appears as 137.4 / 137.6), so the check tolerance is 0.5 MW.
    """
    n = len(seam_rows)
    width = float(interface_limit_mw) / n
    mids = sorted(float(r["band_mid_mw"]) for r in seam_rows)
    if n >= 2:
        spacings = [b - a for a, b in zip(mids, mids[1:])]
        if max(abs(s - width) for s in spacings) > 0.5:
            raise ValueError(
                f"ladder grid is not limit/n_bands: width={width} spacings={spacings}"
            )
    return width


def benchmark_basis(scope: dict) -> dict:
    """Per year, both measured net-export series and EIA-930's own identity."""
    out = {}
    for y in YEARS:
        bb = scope["years"][y]["benchmark_basis"]
        eia = float(bb["eia930_total_interchange_twh"])
        tie = float(bb["pjm_tie_file_net_export_twh"])
        ident = float(bb["eia930_netgen_minus_demand_twh"])
        out[y] = {
            "eia930_total_interchange_twh": eia,
            "pjm_tie_file_net_export_twh": tie,
            "eia930_netgen_minus_demand_twh": ident,
            "sources_disagree_twh": round(eia - tie, 3),
            "eia930_self_identity_residual_twh": round(eia - ident, 3),
            "hourly_correlation": float(bb["hourly_correlation"]),
            # The identity is EIA-930's own arithmetic; a large residual means the
            # published `Total interchange` column contradicts the same table's
            # generation and demand columns, so it cannot arbitrate the model.
            "benchmark_self_consistent": abs(eia - ident) < 1.0,
        }
    return out


def ceiling_check(scope: dict) -> dict:
    """Per year, whether the measured p90 export envelope can bind at all."""
    out = {}
    for y in YEARS:
        ec = scope["years"][y]["envelope_ceiling"]
        ceiling = float(ec["total_envelope_export_ceiling_twh"])
        measured = float(ec["total_measured_net_export_twh"])
        out[y] = {
            "total_envelope_export_ceiling_twh": ceiling,
            "total_measured_net_export_twh": measured,
            "headroom_twh": round(ceiling - measured, 3),
            "ceiling_binds": ceiling < measured,
        }
    return out


def ladder_attribution(scope: dict) -> dict:
    """Turn the per-band clearing-duration gap into TWh, per seam and per year.

    ``duration_measured`` is the ladder's identification target (the measured flow
    duration for that band); ``duration_model_price_clears`` is ``P(model price <=
    p_k)`` on the keeper's own P1 system price. Band energy is
    ``width x 8760 x duration``, so the difference of the two sums is the export
    the model does not clear *because its own price never reaches the band*.
    """
    out = {}
    for y in YEARS:
        rows = scope["years"][y]["ladder_clearing"]["bands"]
        limits = {
            s["seam"]: float(s["interface_limit_mw"])
            for s in scope["years"][y]["envelope_ceiling"]["seams"]
        }
        seams: dict[str, dict] = {}
        for seam in sorted({r["seam"] for r in rows}):
            srows = [r for r in rows if r["seam"] == seam]
            width = _band_width_mw(srows, limits[seam])
            twh_per_unit_duration = width * HOURS / 1e6
            e_measured = sum(float(r["duration_measured"]) for r in srows)
            e_model = sum(float(r["duration_model_price_clears"]) for r in srows)
            # Identification check: the ladder price p_k is by construction the
            # quantile at which P(actual LMP <= p_k) equals the measured flow
            # duration. Max |D_k - P(actual <= p_k)| is the residual of that fit.
            id_resid = max(
                abs(float(r["duration_measured"]) - float(r["duration_actual_lmp_clears"]))
                for r in srows
            )
            seams[seam] = {
                "band_width_mw": round(width, 4),
                "n_bands": len(srows),
                "ladder_energy_at_measured_duration_twh": round(
                    e_measured * twh_per_unit_duration, 4
                ),
                "ladder_energy_at_model_price_twh": round(
                    e_model * twh_per_unit_duration, 4
                ),
                "attributed_export_gap_twh": round(
                    (e_model - e_measured) * twh_per_unit_duration, 4
                ),
                "identification_residual_max": round(id_resid, 5),
            }
        total = sum(s["attributed_export_gap_twh"] for s in seams.values())
        out[y] = {
            "seams": seams,
            "total_attributed_export_gap_twh": round(total, 4),
            "model_price_quantiles": scope["years"][y]["ladder_clearing"][
                "model_price_quantiles"
            ],
            "measured_da_lmp_quantiles": scope["years"][y]["ladder_clearing"][
                "measured_da_lmp_quantiles"
            ],
        }
    return out


def keeper_net_position(attest: dict) -> dict:
    """The keeper's own attested net position vs the measured tie file.

    Free-parameter entry 14 (the net-interchange envelope) records both series in
    its rule-13 admissibility note, so the comparison is the keeper's own claim
    rather than a re-derivation.
    """
    entries = attest.get("free_parameters", {}).get("entries", [])
    for e in entries:
        note = str(e.get("rule_13_admissibility", ""))
        if "arm B:" in note and "against a measured" in note:
            return {"source": "calibration_attestation free_parameters entry", "note": note}
    return {"source": None, "note": None}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--out",
        default=str(REPO / "results/calibration/_pjm153_item15_attribution.json"),
    )
    args = ap.parse_args()

    scope = json.loads(SCOPE.read_text(encoding="utf-8"))
    attest = json.loads(ATTEST.read_text(encoding="utf-8"))

    record = {
        "_what": (
            "pjm-153: no-LP attribution of PJM root-cause item 15 (net-export "
            "level). Reads the committed pjm-152 scope file and the keeper's own "
            "attestation; solves nothing."
        ),
        "inputs": {
            "scope": str(SCOPE.relative_to(REPO)),
            "attestation": str(ATTEST.relative_to(REPO)),
        },
        "item15_as_stated_at_pjm151": ITEM15_AS_STATED,
        "benchmark_basis": benchmark_basis(scope),
        "ceiling_check": ceiling_check(scope),
        "ladder_attribution": ladder_attribution(scope),
        "keeper_attested_net_position": keeper_net_position(attest),
    }

    out = Path(args.out)
    out.write_text(json.dumps(record, indent=1) + "\n", encoding="utf-8")

    # Human-readable summary.
    print("=" * 72)
    print("pjm-153 — item 15 attribution (NO LP)")
    print("=" * 72)
    print("\n[1] BENCHMARK BASIS — which measured series states the residual")
    for y in YEARS:
        b = record["benchmark_basis"][y]
        flag = "OK " if b["benchmark_self_consistent"] else "*** FAILS ITS OWN IDENTITY"
        print(
            f"  {y}: EIA-930 total_interchange {b['eia930_total_interchange_twh']:7.3f}"
            f" | PJM tie file {b['pjm_tie_file_net_export_twh']:7.3f}"
            f" | EIA-930 netgen-demand {b['eia930_netgen_minus_demand_twh']:7.3f}"
        )
        print(
            f"        disagreement {b['sources_disagree_twh']:+7.3f} TWh,"
            f" EIA-930 self-residual {b['eia930_self_identity_residual_twh']:+7.3f} TWh,"
            f" hourly r {b['hourly_correlation']:.4f}  {flag}"
        )
    print("\n[2] CEILING CHECK — can the measured p90 export envelope bind?")
    for y in YEARS:
        c = record["ceiling_check"][y]
        print(
            f"  {y}: ceiling {c['total_envelope_export_ceiling_twh']:7.3f} TWh vs"
            f" measured {c['total_measured_net_export_twh']:7.3f} TWh"
            f" → headroom {c['headroom_twh']:+7.3f} TWh"
            f" | binds={c['ceiling_binds']}"
        )
    print("\n[3] LADDER ATTRIBUTION — export the model's own price never clears")
    for y in YEARS:
        la = record["ladder_attribution"][y]
        print(f"  {y}: total attributed {la['total_attributed_export_gap_twh']:+7.3f} TWh")
        for seam, s in la["seams"].items():
            print(
                f"        {seam:<10} width {s['band_width_mw']:7.1f} MW"
                f" | at measured duration {s['ladder_energy_at_measured_duration_twh']:7.3f}"
                f" | at model price {s['ladder_energy_at_model_price_twh']:7.3f}"
                f" → {s['attributed_export_gap_twh']:+7.3f} TWh"
                f" (id resid {s['identification_residual_max']:.5f})"
            )
        mq, aq = la["model_price_quantiles"], la["measured_da_lmp_quantiles"]
        print(
            f"        low-tail price: model p5 {mq['p5']:.2f} vs actual p5 {aq['p5']:.2f}"
            f" (+{mq['p5'] - aq['p5']:.2f});"
            f" model p25 {mq['p25']:.2f} vs actual p25 {aq['p25']:.2f}"
            f" (+{mq['p25'] - aq['p25']:.2f})"
        )
    print("\n[4] KEEPER'S OWN ATTESTED NET POSITION")
    print("  " + str(record["keeper_attested_net_position"]["note"])[:400])
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
