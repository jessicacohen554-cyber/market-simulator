"""Write the caiso-183 governance attestation for the promoted hour-grain arm.

caiso-183 is the **H-EDGE derive-grain repair**: the CAMPD unit-outage detector
has always worked in **hours** (``start = clock[s]``, ``last = clock[e-1]``)
while the extract stored **days**, so ``market_sim.data.outages`` re-expanded
every window to ``outage_start`` 00:00 → ``outage_end`` 23:00 and asserted up to
**23 h at each edge that the detector never detected** — exactly where the
event-based contract guarantees the neighbouring hour was *running*. caiso-181
§2 confirmed that seam at 100 % of unit-grain CEMS contradictions and filed the
repair as its own charter; this is that repair.

It is a rule 14 ``[R-ACCURATE]`` / rule 1 ``[R-STRUCT]`` correction with **zero
free parameters**: optional ``outage_start_hour`` / ``outage_end_hour`` carried
through deriver → schema → curate → loader. No ``ScenarioConfig`` field, no
threshold, no frozen detector constant.

**Promoted on the owner's ruling of 2026-08-08** — *"if structural integrity
improves but gates regress that may still be a keeper"* — which adjudicates the
two pre-registered gates (``G-DEPTH′`` 2023, ``G-CAISO180`` 5/9 cells) this
session reported as FAILING and explicitly declined to withdraw on its own
authority. Both are reported at full magnitude in the finding and **neither bar
was moved**; the owner's ruling supplies the adjudication, not the session.

This generator writes the promoted arm's attestation and **fails closed** on
every claim a machine can check:

* the two arms' ``scenario_config`` must be **IDENTICAL** — this session's delta
  is a data file, not a ``ScenarioConfig`` field, so any config difference means
  the arms are not comparable;
* the treated arm must actually have **SEEN** the repair. Checked on each
  bundle's **own solved output** (``hourly/class_hourly_<year>.parquet``), never
  on the current on-disk CSV — that CSV is a single mutable file both arms
  cannot simultaneously evidence, and re-deriving it post-hoc would attest to
  whichever state happened to be staged last. Freeing wrongly-derated CC
  capability must RAISE CC_REGULAR and LOWER CT_PEAKER in every year;
* the repaired envelope must clear the **G-CONTRACT** record: in-window CEMS
  contradiction exactly 0 in every year, with interior 0;
* the DOF ledger must be **UNCHANGED** at ``n_entries`` 11 / ``n_residual`` 8
  (PRECHECK-caiso183 §6). A grain repair introduces no free parameter; if either
  count moves, that is a defect in this session and the generator refuses;
* the incumbent keeper's ledgered exceptions are carried **verbatim** — this
  session creates no new caveat and spends no new ledger slot.

Usage::

    python scripts/gen_caiso183_attestation.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

import pandas as pd  # noqa: E402

from scripts.build_dof_ledger import build_ledger  # noqa: E402

KEEPER = REPO / "results/calibration/caiso175_tac_intake"
CONTROL = REPO / "results/calibration/caiso183_b0_control"
ARM = REPO / "results/calibration/caiso183_b1_hourgrain"
GCONTRACT = REPO / "results/calibration/_caiso183_gcontract.json"
YEARS = (2023, 2024, 2025)

#: PRECHECK §6. This session leaves both numbers untouched — a grain carriage
#: has no free parameter.
KEEPER_N_ENTRIES, KEEPER_N_RESIDUAL = 11, 8

#: The repair frees wrongly-derated CC capability, which must show up as MORE
#: CC_REGULAR energy and LESS peaking energy in every year. Floors are set well
#: below the measured effect (CC_REGULAR +0.195/+0.172/+0.253 TWh, CT_PEAKER
#: -0.118/-0.052/-0.071) so a null — a silently un-applied repair — fails closed,
#: while staying far from the measured value so this is a presence test and
#: never a fitted target.
MIN_CC_REGULAR_TWH_GAIN = 0.05
MIN_CT_PEAKER_TWH_DROP = 0.01

ATTESTED_ARM = (
    "caiso-183 (2026-08-08): THE H-EDGE DERIVE-GRAIN REPAIR. A rule-14 "
    "[R-ACCURATE] / rule-1 [R-STRUCT] correction with ZERO free parameters. The "
    "CAMPD unit-outage detector has always worked in HOURS (start = clock[s], "
    "last = clock[e-1]) while the extract stored DAYS, so outages.py re-expanded "
    "every window to outage_start 00:00 -> outage_end 23:00 and asserted up to "
    "23 h at EACH EDGE that the detector never detected — precisely where the "
    "event-based contract (detect_outages_eventbased, break on any hour at "
    "CF >= ST_GAS_CF_PEAK = 0.02) guarantees the neighbouring hour was RUNNING. "
    "caiso-181 §2 confirmed the seam at 100 % of unit-grain CEMS contradictions "
    "with every contradicted hour within 22 h (< 24) of a window boundary, and "
    "filed the repair as needing its own charter; this is that charter. THE FIX "
    "IS A STRICT GRAIN CHANGE: optional outage_start_hour / outage_end_hour "
    "carried deriver -> schema -> curate -> loader, emission gated on a "
    "default-off --hour-grain flag, the loader falling back to the day-granular "
    "reconstruction when the columns are absent — BY IDENTITY, not "
    "approximation (absent is exactly 0/23, and +(23+1) h == +1 day). No "
    "ScenarioConfig field is added, no threshold is re-valued, and no frozen "
    "detector constant is touched (_MIN_DAYS 5, _SMOOTH_DAYS 7, _CEILING_FRAC "
    "0.65, _RUN_FLOOR_CF 0.06, _BASELOAD_CF 0.55, ST_GAS_CF_PEAK 0.02, all "
    "imported and diffed). MEASURED EDGE OVER-DERATE: 22.54 h per window. "
    "DETECTION IS UNTOUCHED (BE-3): 4,328 rows, the same (plant, unit, "
    "start-day, end-day) tuples in the same order, 547/458/635 windows per year "
    "— identical to caiso-180's A0 census — so the SETTLED caiso-181 depth "
    "question is not re-opened; only the expressed grain differs. THE REPAIR IS "
    "PROVABLY MONOTONE: the reconstructed window is a SUBSET of the "
    "day-granular one for every row (asserted in-deriver), so no hour the "
    "detector detected can ever be removed. STRUCTURAL RESULT (G-CONTRACT): "
    "in-window CEMS contradiction collapses from 3.358/3.248/3.550 % to EXACTLY "
    "0.000000 while interior stays 0, and contradicted CEMS energy falls "
    "762,479/927,356/1,263,185 -> 185/182/299 MW-h. The model no longer asserts "
    "unavailability its own source contradicts. BYTE-INERT ELSEWHERE "
    "(G-SIXISO): with the code present and the flag absent, all six ISOs' "
    "extracts are sha256-identical to their own re-derivation, and the "
    "day-grain loader mask is bit-identical across 24 (ISO, year) digests on "
    "both consumer legs — so this is per-ISO adoptable and no other ISO's "
    "keeper availability moves (rule 25 [R-ISO-SCOPE]). C3a NARROWS IN ALL "
    "THREE YEARS as a CONSEQUENCE and never as a target (rules 1/13): "
    "+4.2 -> +3.9 % (PASS), +11.5 -> +10.9 %, +14.7 -> +13.9 %, at 50-130x the "
    "measured same-head noise floor, via a coherent mechanism (CC_REGULAR "
    "+0.195/+0.172/+0.253 TWh displacing CT_PEAKER, ST_GAS and imports). IT "
    "DOES NOT CLOSE THE RESIDUAL: 2024 and 2025 remain FAIL and the "
    "determination stays NOT-YET; the repair takes only ~1/7 and ~1/6 of the "
    "excess, and the first named remaining contributor is still the WALLED "
    "hourly pumped-storage water state (FINDING-caiso140 §B / caiso-141 A2), an "
    "owner-funded intake and not a session lever. TWO PRE-REGISTERED GATES "
    "FAILED AND ARE REPORTED AT FULL MAGNITUDE, BARS UNMOVED: G-DEPTH' (2023, "
    "1.844 M vs 1.346 M MW-h) and G-CAISO180 (5 of 9 banded class-years). Both "
    "bound the repair's footprint by the caiso-180 REGENERATION leg's footprint, "
    "presuming the repair is that leg's inverse — which BE-3 falsifies, since "
    "the window set is identical and the repair strips edge hours from EVERY "
    "window including all those pre-dating the regeneration. The session "
    "declined to withdraw its own gates; PROMOTED ON THE OWNER'S RULING of "
    "2026-08-08 that structural-integrity gain may carry a keeper even where "
    "gates regress. DOF ledger UNCHANGED at n_entries 11 / n_residual 8, "
    "verified fail-closed below."
)


def _cfg(bundle: Path) -> dict:
    """Return one bundle's recorded ``scenario_config``."""
    return json.loads((bundle / "run_config.json").read_text()).get(
        "scenario_config", {}
    )


def _class_twh(bundle: Path, year: int, klass: str) -> float:
    """Annual TWh for one dispatch class, from the bundle's own sidecar."""
    df = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    return float(df[df["klass"] == klass]["mw"].sum() / 1e6)


def main() -> int:
    """Write the promoted arm's attestation, refusing on any failed check."""
    keeper_att = json.loads((KEEPER / "calibration_attestation.json").read_text())
    exceptions = keeper_att["exceptions"]

    for b in (CONTROL, ARM):
        if not (b / "run_config.json").exists():
            raise SystemExit(f"{b.name} not solved yet — nothing to attest.")

    # --- fail-closed 1: the arms' configs are IDENTICAL ---------------------
    c_cfg, a_cfg = _cfg(CONTROL), _cfg(ARM)
    diff = sorted(k for k in set(c_cfg) | set(a_cfg) if c_cfg.get(k) != a_cfg.get(k))
    if diff:
        raise SystemExit(
            f"A/B NOT CLEAN: scenario_config differs on {diff}, expected NO "
            "difference at all — caiso-183's delta is a data file, so any config "
            "difference means the arms are not comparable."
        )
    print(f"OK: arms' scenario_config IDENTICAL across {len(a_cfg)} keys")

    # --- fail-closed 2: the treated arm actually saw the repair -------------
    for year in YEARS:
        cc = _class_twh(ARM, year, "CC_REGULAR") - _class_twh(
            CONTROL, year, "CC_REGULAR"
        )
        ct = _class_twh(CONTROL, year, "CT_PEAKER") - _class_twh(ARM, year, "CT_PEAKER")
        if cc < MIN_CC_REGULAR_TWH_GAIN:
            raise SystemExit(
                f"{year}: CC_REGULAR gain {cc:+.4f} TWh < {MIN_CC_REGULAR_TWH_GAIN} "
                "— the freed capability did not reach the LP, so the attestation "
                "may not claim the repair was applied."
            )
        if ct < MIN_CT_PEAKER_TWH_DROP:
            raise SystemExit(
                f"{year}: CT_PEAKER drop {ct:+.4f} TWh < {MIN_CT_PEAKER_TWH_DROP} "
                "— freed CC capability did not displace peaking, so the claimed "
                "mechanism is not evidenced in the solved output."
            )
        print(f"OK: {year} CC_REGULAR {cc:+.4f} TWh, CT_PEAKER {-ct:+.4f} TWh")

    # --- fail-closed 3: G-CONTRACT — zero contradiction on the repair -------
    if not GCONTRACT.exists():
        raise SystemExit(f"{GCONTRACT.name} missing — G-CONTRACT unverifiable.")
    gc = json.loads(GCONTRACT.read_text())
    for year in YEARS:
        after = gc["years"][str(year)]["after_hour_grain"]
        if after["share_above_contract"] != 0.0:
            raise SystemExit(
                f"{year}: repaired envelope still contradicts CEMS in "
                f"{after['share_above_contract']:.8f} of in-window hours — the "
                "structural claim this promotion rests on does not hold."
            )
        if after["interior_share_above_contract"] != 0.0:
            raise SystemExit(f"{year}: interior contradiction is non-zero.")
    print("OK: G-CONTRACT — contradiction exactly 0.000000, interior 0, all years")

    # --- fail-closed 4: the DOF ledger has not moved ------------------------
    led = build_ledger(ARM, "CAISO")
    if (led["n_entries"], led["n_residual"]) != (KEEPER_N_ENTRIES, KEEPER_N_RESIDUAL):
        raise SystemExit(
            f"DOF ledger moved to {led['n_entries']}/{led['n_residual']}, expected "
            f"{KEEPER_N_ENTRIES}/{KEEPER_N_RESIDUAL} — a grain repair introduces no "
            "free parameter, so a move is a defect in this session."
        )
    print(f"OK: DOF ledger {led['n_entries']}/{led['n_residual']} (unchanged)")

    att = {
        "schema": "calibration-attestation/v1",
        "governance": {
            "levers_trace_to_measured_input": True,
            "no_fit_to_price_residuals": True,
            "no_pinning_to_actuals": True,
            "outage_filter_exogenous_net_load": True,
            "attested_by": ATTESTED_ARM,
            "note": (
                "The single delta vs the control is "
                "data/raw/campd-unit-outages-CAISO.csv re-derived with "
                "--hour-grain (sha256 25360e90a9d11f32c293edf3224047da0d6fab447b"
                "551fac81b983e2da1166c6), regenerable byte-identically with "
                "`python scripts/data/derive_campd_unit_outages.py --iso CAISO "
                "--years 2018 2019 2020 2021 2022 2023 2024 2025 2026 "
                "--merit-order-guard --hour-grain`. The sha ladder "
                "(_caiso183_sha_ledger.json) records each arm's pre- and "
                "post-solve extract sha as equal, so neither arm's envelope "
                "moved under it."
            ),
        },
        "exceptions": exceptions,
        "free_parameters": led,
    }
    out = ARM / "calibration_attestation.json"
    out.write_text(json.dumps(att, indent=1) + "\n")
    print(f"wrote {out.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
