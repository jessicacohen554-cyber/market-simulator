"""nyiso-115 Task 3: adjudicate the five cross-ISO TRANSFER candidates, ex ante.

The matrix's `U` cells that carry a `K` in some other ISO's column are the
standing transfer queue. nyiso-111 swept the three it judged live at NYISO and
killed two of them **before a solve was spent**, each on NYISO's own measurement
rather than on analogy. This is the same exercise for the five that remain:

| candidate | donor(s) |
|---|---|
| ``cc_committed_offer_margin`` | ERCOT |
| ``maxgen_emergency_tier_pricing`` | MISO |
| ``measured_offer_surface`` | ERCOT, CAISO (PJM **R**, NEISO **I**) |
| ``reference_price_interface`` | PJM, MISO |
| ``storage_vintage_ramp`` | ERCOT, CAISO, NEISO |

**Rule 25 ``[R-ISO-SCOPE]`` / 28(d) govern.** A verdict never transfers across an
ISO boundary: a donor's `K` makes a candidate worth ASKING about at NYISO, never
worth arming there. Every parameter must come from NYISO's own market, and a
candidate that cannot be identified from NYISO data is REFUSED rather than
imported at the donor's fitted value — that is exactly how nyiso-111 resolved
``temp_dependent_derate`` (U -> G) when the MISO estimator re-run on NY CAMPD
returned the wrong sign.

Everything here reads already-committed artifacts. **No solve is spent**, and
each refusal is written down — a rejection nobody records gets re-run.

Run:
    PYTHONPATH=.:src python scripts/probes/_nyiso115_transfer_queue_adjudication.py
"""

from __future__ import annotations

import json
import re

import pandas as pd

from market_sim.config.paths import REPO_ROOT

YEARS = (2023, 2024, 2025)
KEEPER_BUNDLE = REPO_ROOT / "results/calibration/nyiso113_lilocational_B"

# NYISO's own published operational record (P-35 Real-Time Events + P-25
# Operational Announcements). This is the ONLY instrument that can say whether
# the MISO emergency-tier mechanism has a declared window to bind in at NYISO.
EVENT_FEEDS = (
    "realtime-events/NYISO_realtime_events",
    "oper-messages/NYISO_oper_messages",
)
EVENT_PATTERNS = {
    "maxgen_declaration": r"maximum generation|max ?gen",
    "emergency_energy_alert": r"emergency energy|EEA[- ]?[123]",
    "major_emergency_state": r"major emergency",
    "dr_activation_scr_edrp": r"\bSCR\b|EDRP|demand response",
    "reserve_pickup": r"reserve pick.?up",
    "thunderstorm_alert": r"thunderstorm",
}


def _keeper_config() -> dict:
    doc = json.loads((KEEPER_BUNDLE / "run_config.json").read_text())
    return doc.get("scenario_config", doc)


def adjudicate_maxgen() -> dict:
    """MISO's declared-window emergency tier: does NYISO declare such windows?

    MISO's ``maxgen_emergency_tier_pricing`` prices resources deployed inside a
    DECLARED Maximum Generation Emergency window at published tier floors
    ($500/$1,000). The mechanism is a *window* mechanism, so rule 17
    ``[R-FLOOR-WINDOW]`` applies directly: no declared window, no mechanism. That
    is answerable from NYISO's own published message log alone.
    """
    counts: dict[str, dict[str, int]] = {}
    for year in YEARS:
        msgs = pd.concat(
            [
                pd.read_csv(
                    REPO_ROOT
                    / "data/raw/NYISO-AS/requirements"
                    / f"{feed}_{year}.csv"
                )["message"].astype(str)
                for feed in EVENT_FEEDS
            ]
        )
        counts[str(year)] = {"messages_scanned": int(len(msgs))} | {
            name: int(msgs.str.contains(pat, case=False, regex=True, na=False).sum())
            for name, pat in EVENT_PATTERNS.items()
        }
    total_maxgen = sum(c["maxgen_declaration"] for c in counts.values())
    total_eea = sum(c["emergency_energy_alert"] for c in counts.values())
    return {
        "candidate": "maxgen_emergency_tier_pricing",
        "donor": "MISO (K)",
        "instrument": "NYISO P-35 Real-Time Events + P-25 Operational Announcements",
        "counts_by_year": counts,
        "verdict": "I",
        "reason": (
            f"INERT — the mechanism's own driver does not occur at NYISO in the "
            f"training window. Across all three years and "
            f"{sum(c['messages_scanned'] for c in counts.values())} published "
            f"operational messages there are {total_maxgen} Maximum Generation "
            f"declarations and {total_eea} emergency-energy alerts; the single "
            f"'major emergency state' entry (2025) is a system-state change, not "
            f"a MaxGen window with a tier price. A declared-window offer floor "
            f"with no declared window is inert by construction (rule 17 "
            f"[R-FLOOR-WINDOW]). Separately, the NYISO-native analogues of the "
            f"phenomenon are ALREADY armed as distinct mechanisms — reserve "
            f"scarcity through the RCPF families and demand response through "
            f"nyiso_scr_edrp — so arming a third would stack on both (rule 19 "
            f"[R-ONE-MECH]). Recorded observation, NOT opened here: the log does "
            f"carry 126-195 reserve pick-up events a year, which belongs to the "
            f"everyday-reserve-formation question nyiso-110 adjudicated."
        ),
    }


def adjudicate_offer_identification() -> list[dict]:
    """The two candidates identified from submitted unit-level offer curves.

    ``cc_committed_offer_margin`` is derived from ERCOT's 60-Day SCED disclosure
    (the bottom of a unit's Three-Part Offer curve) and ``measured_offer_surface``
    from measured DAM offer surfaces. Both need a MEASURED SUBMITTED OFFER, which
    is a different object from measured operation: CAMPD reports what a unit
    DID, never what it BID.
    """
    out = []
    for candidate, donors, source in (
        (
            "cc_committed_offer_margin",
            "ERCOT (K)",
            "ERCOT 60-Day SCED disclosure — the Three-Part Offer curve bottom",
        ),
        (
            "measured_offer_surface",
            "ERCOT (K), CAISO (K) — PJM already R, NEISO already I",
            "measured DAM offer surfaces, net-load binned",
        ),
    ):
        out.append(
            {
                "candidate": candidate,
                "donor": donors,
                "donor_identification_source": source,
                "verdict": "G",
                "reason": (
                    "GOVERNANCE-REFUSED on identification, not on fit, and not "
                    "by analogy. Both mechanisms are identified from SUBMITTED "
                    "unit-level offer curves, and NYISO publishes no such "
                    "disclosure — the repo's own record establishes this twice "
                    "over: 'NYISO publishes no 60-Day-DAM equivalent' "
                    "(docs/calibration-log/nyiso.md, the nyiso-87 gas-bridge "
                    "derivation, which is why that mechanism's min-load had to "
                    "be reconstructed from CAMPD loading-when-on instead) and "
                    "'NYISO publishes no submitted-curve equivalent' "
                    "(docs/mechanism-testing-matrix.md). There is no offer or "
                    "bid artifact for NYISO anywhere under data/raw/. CAMPD "
                    "gives what a unit DID, never what it BID, so no NYISO "
                    "source can identify an offer LEVEL. The only remaining way "
                    "to arm either is to carry the donor's fitted offer level "
                    "across the ISO boundary, which rule 25 [R-ISO-SCOPE] "
                    "forbids outright — and measured_offer_surface has already "
                    "failed to transfer twice (PJM R, NEISO I). G rather than U: "
                    "this is refused, not merely untested. Re-openable only by a "
                    "NEW NYISO offer-data source, which is what 'new evidence' "
                    "would mean for this cell under rule 28a."
                ),
            }
        )
    return out


def adjudicate_reference_price_interface() -> dict:
    """PJM/MISO's forward-grade neighbor seam, against what NYISO already arms."""
    cfg = _keeper_config()
    return {
        "candidate": "reference_price_interface",
        "donor": "PJM (K), MISO (K)",
        "keeper_already_arms": {
            "nyiso_import_hub_prices": cfg.get("nyiso_import_hub_prices"),
            "reference_price_interface": cfg.get("reference_price_interface"),
        },
        "verdict": "G",
        "reason": (
            "GOVERNANCE-REFUSED under rule 19 [R-ONE-MECH]: NYISO already has a "
            "mechanism for this exact phenomenon, ARMED ON THE KEEPER. "
            "nyiso_import_hub_prices=True reprices every import-node tranche at "
            "the MEASURED hourly neighbor system LMP (PJM_west at the PJM DA hub "
            "mean, ISONE_tie at the ISO-NE DA hub mean, the residual scarcity "
            "block at the hourly max of the two, each plus the "
            "inter-control-area wheeling hurdle, with the export sink repriced "
            "at max minus hurdle so the seam is arbitrage-free). Its own "
            "docstring names it 'the NYISO analogue of "
            "miso_pjm_lmp_import_pricing and caiso_import_hub_prices' — i.e. it "
            "IS the transfer of this family, already made and already promoted. "
            "Arming reference_price_interface on top would price the neighbor "
            "seam twice. Rule 14 [R-ACCURATE] also orders the two for a "
            "BACKCAST: the armed mechanism uses the neighbours' MEASURED hourly "
            "prices, while a reference-price interface is the forward-grade "
            "construct for years where no measured neighbour price exists. The "
            "measured one dominates in-window. NOTE FOR THE FORECAST LANE, not "
            "decided here: the fc cell is a different question, because in a "
            "forecast year there IS no measured neighbour LMP and the "
            "forward-grade seam is the natural former — that belongs to the "
            "forecast programme, not to a backcast calibration session."
        ),
    }


def adjudicate_storage_vintage_ramp() -> dict:
    """ERCOT/CAISO/NEISO's battery COD vintage ramp, sized against NYISO's fleet.

    The mechanism phases a battery fleet in at MONTH grain by commercial
    operation date instead of carrying the year-end fleet through the whole
    year. Its maximum possible effect is therefore bounded by the WITHIN-WINDOW
    capacity growth it re-times: a fleet that does not grow has nothing to
    phase in. That bound is computable from the keeper's own storage sidecars.
    """
    by_year = {}
    for year in YEARS:
        df = pd.read_parquet(KEEPER_BUNDLE / "hourly" / f"storage_{year}.parquet")
        by_year[str(year)] = {
            tech: round(float(v), 1)
            for tech, v in df.groupby("tech")["discharge_mw"].max().items()
        }
    li = {y: v.get("li_ion", 0.0) for y, v in by_year.items()}
    growth = li["2025"] - li["2023"]
    # Worst-case mis-timed energy: the whole increment mis-placed by half a year
    # at a generous battery capacity factor.
    bound_twh = growth * 4380.0 * 0.25 / 1e6
    return {
        "candidate": "storage_vintage_ramp",
        "donor": "ERCOT (K), CAISO (K), NEISO (K)",
        "nyiso_storage_max_discharge_mw_by_year": by_year,
        "li_ion_growth_2023_to_2025_mw": round(growth, 1),
        "worst_case_mistimed_energy_twh": round(bound_twh, 4),
        "verdict": "I",
        "reason": (
            f"INERT BY MAGNITUDE, on NYISO's own fleet rather than by analogy. "
            f"The mechanism re-times a battery fleet's month-of-COD phase-in, so "
            f"its maximum possible effect is bounded by the within-window growth "
            f"it re-times. NYISO's lithium-ion fleet moves "
            f"{li['2023']} -> {li['2025']} MW across the whole training window — "
            f"{growth:.1f} MW — and its pumped storage is FLAT at 1,220 MW "
            f"(Blenheim-Gilboa, in service since 1973, so it carries no vintage "
            f"question at all). Placing the entire increment half a year wrong at "
            f"a generous 0.25 capacity factor mis-allocates at most "
            f"{bound_twh:.4f} TWh against ~150 TWh of annual NYISO load — below "
            f"the resolution of every scored criterion. The donors are the "
            f"reason the mechanism exists and the reason it does not transfer: "
            f"ERCOT and CAISO added battery capacity in this window two to three "
            f"ORDERS OF MAGNITUDE larger than NYISO's 53 MW, where month-grain "
            f"timing genuinely moves prices. Same verdict class as nyiso-113's "
            f"measured_ramp_capability (U -> I on a 18.8x headroom margin): "
            f"arithmetic, not a solve. Re-openable if NYISO's battery build "
            f"accelerates — the bound above is the test to re-run, not a "
            f"permanent finding."
        ),
    }


def main() -> None:
    results = [
        adjudicate_maxgen(),
        *adjudicate_offer_identification(),
        adjudicate_reference_price_interface(),
        adjudicate_storage_vintage_ramp(),
    ]
    doc = {
        "probe": "nyiso-115 cross-ISO transfer-queue adjudication (Task 3)",
        "governing_rules": "25 [R-ISO-SCOPE], 28(a) DO-NOT-REDO, 28(d), 19 [R-ONE-MECH], 17 [R-FLOOR-WINDOW]",
        "solves_spent": 0,
        "candidates": results,
        "summary": {r["candidate"]: r["verdict"] for r in results},
    }
    out = REPO_ROOT / "results/calibration/nyiso115_transfer_queue_adjudication.json"
    out.write_text(json.dumps(doc, indent=2))
    for r in results:
        print(f"\n=== {r['candidate']}  ->  {r['verdict']}")
        print("   " + re.sub(r"\s+", " ", r["reason"])[:400] + " …")
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
