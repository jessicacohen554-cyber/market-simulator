"""One-shot CI-side companion for the ercot55-solve-register workflow.

Two jobs the authoring session could not do through the MCP relay (single-call
content ceiling ~200 KB; the subagent push path additionally hit the account
spend limit, 2026-07-10):

* ``--thread-other``: land the 9-line NG:OTH threading in the ~240 KB
  ``scripts/run_calibration_full.py`` (guarded, byte-anchored, no-op when the
  threading is already present). The patched file is then uploaded via
  ``ci_api_upload_multi.py --extra`` so the branch carries the REAL change and
  the probe-seam wrapper in ``_ercot55_ab.py`` becomes a documented no-op.
* ``--append-log``: append this session's calibration-log entry (the ~590 KB
  log is far beyond the relay ceiling; CI reads/writes it from disk).

Both operations are idempotent (anchor / marker guarded) so a workflow re-run
cannot double-apply them.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

RUNNER = REPO / "scripts" / "run_calibration_full.py"
LOG = REPO / "docs" / "calibration-log.md"

IMPORT_ANCHOR = "    load_ercot_nuclear_gen,\n"
IMPORT_ADD = "    load_ercot_nuclear_gen,\n    load_ercot_other_gen,\n"
NETGEN_ANCHOR = (
    "    # net generation = Demand + Interchange = load_demand with no gross-up.\n"
)
OTHER_BLOCK = (
    '    # "Other Fuel Sources" (NG: OTH) — carried so the gas fold-in deflation\n'
    "    # can subtract only the genuinely-folded other/biomass portion from the\n"
    "    # EIA-930 gas cell (post-Nov-2024 storage breakout, ERCO's Other series\n"
    "    # is ~biomass alone and the OTHER-class generation sits inside NG: NG);\n"
    "    # see load_ercot_other_gen and calibration_verdict.score_sysvol.\n"
    "    other = load_ercot_other_gen(year)\n"
)
NUCLEAR_ANCHOR = '    if nuclear is not None:\n        series["nuclear"] = nuclear\n'
OTHER_SERIES_ADD = (
    '    if nuclear is not None:\n        series["nuclear"] = nuclear\n'
    '    if other is not None:\n        series["other"] = other\n'
)

ENTRY_MARKER = "## 2026-07-10 — ERCOT-55"

ENTRY = """
## 2026-07-10 — ERCOT-55: C2 gas counting root-caused and fixed (EIA-930 fold-in + OTHER_FOSSIL symmetry + measured 48-h gap fill); the ercot50 conditional offer surface RE-TESTED full-span on the keeper config under v2.4 — C3c-2025 closes by mechanism (24 h vs 23 DA); keeper stays ercot53, promotion pending owner

**Task (owner, this session).** (1) Resolve the C2-2025 gas counting vs
EIA-930 — is the model side full-family or completed-923-only, and is 930
booking non-gas generation (other/biomass/other-fossil) inside NG? (2) Take
one more owner-sanctioned crack at the C3c scarcity-hour under-tail.

**C2 counting — three wedges, all fixed (zero tunables).** The fallback was
already full-model-family vs full-930 NG, but three wedges made it
apples-to-oranges: (a) the hand-curated ERCO hourly extract has a 48-h NaN
hole (2025-12-04/05 — two real winter days peaking 58.4 GW measured) that
every loader bridged by linear interpolation, fabricating ~+0.6 TWh of
benchmark gas AND feeding the solve a flat ~48 GW demand valley; NaN windows
now fill from the measured EIA-930 long-format API series before
interpolation (`eia_loader._fill_hourly_frame_from_long`; 2023/2024 have no
NaN hours — byte-identical; Dec 4-5 2025 was NOT scarce, RT max $97, so this
is hygiene, not tail-tuning). (b) Post the Nov-2024 EIA-930 storage breakout
(BAT/UES series appear; ERCO OTH collapses 1.85 → 0.26 TWh ≈ biomass alone),
the 923 OTHER-class generation (~0.9 TWh) sits inside NG:NG — but ERCOT's
dedicated `_eia930_frame` never carried the `other` series, so the standing
`_gas_foldin_deflation` could not fire for ERCOT (only the CAISO legacy
allowlist). `load_ercot_other_gen` threads NG:OTH into the bundle. (c)
`score_sysvol`'s fallback summed model gas WITHOUT the OTHER_FOSSIL mixed
gas-thermal scoring bucket while its 930 target includes those plants —
inconsistent with the render-side `_GAS_GROUPS` membership; fixed
(gas-family fallback only). Result: C2-2025 gas −2.9 % CAVEAT → **−1.7 %
PASS** (−2.3 % from the scorer fix alone on the committed bench). All five
other ISO keepers re-scored: no status changes (CAISO/NYISO/NEISO
byte-identical, PJM +0.09 TWh within PASS, MISO FAIL unchanged).

**Runs (full 2023-2025 bundles + zero-forcing twins, registered via the
`ercot55-solve-register` workflow).** Baseline recipe = ercot53 keeper
config reconstructed from its committed meta.json (`_ercot55_ab.py`), zero
config deltas; the surface arm adds only `ercot_offer_surface_conditional`.

| run | C3a (23/24/25) | C3b | C3c h vs DA 311/68/23 | caveats |
|---|---|---|---|---|
| ercot53 keeper | −1.0/−6.9/−3.6 % | .109/.184/.079 | 162/24/5 | 3 (C2, C3c×2, C5c) |
| ercot55 930gap-c2fix | −1.0/−6.9/−3.5 % | .109/.184/.078 | 162/24/5 | 2 (C3c×2, C5c) |
| ercot55 surface-ab | +2.0/−4.7/−1.1 % | .106/.196/.094 | 166/27/**24 (1.04×, PASS)** | 2 (C3c-2024, C5c) |

2023/2024 of the main arm reproduce ercot53 exactly (inputs byte-identical),
isolating the 2025 delta to the measured demand fill. Both arms attested
(DOF ledger inherited from ercot53 verbatim — zero new free parameters;
the surface's rungs/bins are measured 60-Day DAM disclosure values) and
score **CALIBRATED-WITH-CAVEATS (2 caveats)** vs the keeper's 3.

**Surface re-litigation basis (rules 1/13; owner-sanctioned round).** The
ercot50 rejection (+35 % C3a-2023) predates rubric v2.4 AND the ercot52 ORDC
cap-dual fix; the ERCOT-54 entry records that no full-span surface A/B
existed on the current keeper config. On that basis the 2023 objection
dissolves (+2.0 % PASS, C3c-2023 166 h ≥ the 162 h owner gate) and the
measured surface closes C3c-2025 outright — scarcity-anticipating offer
formation pricing the $100-300 shoulder in the measured tight bins. C3c-2024
narrows 24→27 h (0.35×→0.40×, still ledgered: event depth/breadth + the
non-scarce Nov-17 event — the filed G-22 residual). C5c-2024 storage shape
inherited unchanged.

**Recommendation.** Surface arm as new keeper (resolves a caveat by
mechanism, not ledger; strictly fewer caveats; structurally real market
behaviour) — owner call, keeper untouched pending sign-off.

**Bookkeeping.** Session env hit both the MCP relay single-call ceiling
(~200 KB) and the account spend limit mid-push, so registration runs through
the one-shot `ercot55-solve-register` workflow (caiso67/69 precedent):
solves all four bundles on CI, registers, and uploads run payloads + bench +
this log entry via `ci_api_upload_multi.py --extra`. The NG:OTH threading
lands in `run_calibration_full.py` via the same workflow
(`_ercot55_ci_patch.py --thread-other`, byte-anchored + guarded), with an
equivalent no-op-guarded wrapper at the probe seam so local and CI bundles
are identical either way.

**Holdouts.** No solve, score, or intake outside 2023-2025 (rule 22); ORDC
tariff parameters untouched (rule 26); no offer-curve, sigmoid, floor, or
derive-script value changed (rules 13/21/23).
"""


def thread_other() -> None:
    """Apply the guarded NG:OTH threading to run_calibration_full.py."""
    s = RUNNER.read_text()
    if "load_ercot_other_gen" in s:
        print("thread-other: already present — no-op")
        return
    assert IMPORT_ANCHOR in s and NETGEN_ANCHOR in s and NUCLEAR_ANCHOR in s
    s = s.replace(IMPORT_ANCHOR, IMPORT_ADD, 1)
    s = s.replace(NETGEN_ANCHOR, OTHER_BLOCK + NETGEN_ANCHOR, 1)
    s = s.replace(NUCLEAR_ANCHOR, OTHER_SERIES_ADD, 1)
    RUNNER.write_text(s)
    print("thread-other: applied")


def append_log() -> None:
    """Append this session's calibration-log entry (marker-guarded)."""
    text = LOG.read_text()
    if ENTRY_MARKER in text:
        print("append-log: entry already present — no-op")
        return
    if not text.endswith("\n"):
        text += "\n"
    LOG.write_text(text + ENTRY.lstrip("\n"))
    print("append-log: appended")


# --- scorer + test hunks (same relay-ceiling fallback as thread_other) -----
# Each entry: (repo-relative path, presence-guard marker, [(old, new), ...]).
# The old strings are byte-anchored against the file as of main @ fe26a8c;
# byte-equality with the authoring session's working tree is verified by
# applying these to main's versions and diffing (session log, 2026-07-10).

_SCORER = REPO / "scripts" / "calibration_verdict.py"
_T_SCORER = REPO / "tests" / "test_calibration_verdict.py"
_T_LOADER = REPO / "tests" / "test_eia_loader.py"

_SCORER_H1_OLD = """    For a PRELIMINARY-EIA-923 family — one the completeness audit flags as not
    fully reported (:func:`family_is_complete`) — there is no trustworthy per-class
    actual (missing plants under-report thermal; EIA-930 carries no per-class
    split), so the family aggregate vs the authoritative EIA-930 grid total is the
    only available volume check — retained here as the ±2.5% family fallback,
    explicitly scoped to the no-per-class-data case. A preliminary year whose
    family DID fully report (e.g. ERCOT coal 2025) defers to the C1 per-class gate
    exactly like a complete vintage — only the still-incomplete families fall back.
    \"\"\""""

_SCORER_H1_NEW = """    For a PRELIMINARY-EIA-923 family — one the completeness audit flags as not
    fully reported (:func:`family_is_complete`) — there is no trustworthy per-class
    actual (missing plants under-report thermal; EIA-930 carries no per-class
    split), so the family aggregate vs the authoritative EIA-930 grid total is the
    only available volume check — retained here as the ±2.5% family fallback,
    explicitly scoped to the no-per-class-data case. A preliminary year whose
    family DID fully report (e.g. ERCOT coal 2025) defers to the C1 per-class gate
    exactly like a complete vintage — only the still-incomplete families fall back.

    The fallback compares like for like against the EIA-930 grid cell: the model
    gas sum spans every gas class PLUS the OTHER_FOSSIL scoring bucket (930 books
    mixed gas-thermal plants under NG:NG — same membership as
    ``render_calibration_html._GAS_GROUPS``), and when the bundle carries the
    EIA-930 "other" series the gas target is deflated by the genuinely-folded
    OTHER+biomass portion (post-Nov-2024 storage breakout, ERCO's Other series is
    ~biomass alone, so the 923 OTHER-class generation sits inside NG:NG).
    \"\"\""""

_SCORER_H2_OLD = """        if use_family_fallback:
            # EIA-930 NG:NG includes ALL gas-fired generation at the grid
            # meter (CC, CT, ST — including CHP exports), so the model sum
            # must also include every gas class, not just the C1-scored
            # subset.  The scored list excludes CT_CHP (a BTM class ungated
            # in C1), but omitting it here creates an apples-to-oranges gap
            # of ~6 TWh/yr in ERCOT.
            m_fam = sum(float(gm.get(c, 0.0)) for c in classes)
            actual = a930
            if fam == "gas" and actual is not None and "other" in e930:
                actual -= max(
                    0.0,
                    float(cf.get("OTHER", 0.0))
                    + float(cf.get("biomass", 0.0))
                    - float(e930.get("other", 0.0)),
                )
            reconciled = bool(actual and a923 < VINTAGE_RECONCILE_FRAC * actual)"""

_SCORER_H2_NEW = """        if use_family_fallback:
            # EIA-930 NG:NG includes ALL gas-fired generation at the grid
            # meter (CC, CT, ST — including CHP exports AND the genuinely-
            # mixed gas-thermal plants the scoring transform re-buckets into
            # OTHER_FOSSIL), so the model sum must also include every gas
            # class plus OTHER_FOSSIL, not just the C1-scored subset.  The
            # scored list excludes CT_CHP (a BTM class ungated in C1) and
            # OTHER_FOSSIL (not a merit-order class), but omitting them here
            # creates an apples-to-oranges gap of ~6 + ~1 TWh/yr in ERCOT —
            # the same family membership reconcile_vintage_classes uses
            # (render_calibration_html._GAS_GROUPS).
            fam_all = (*classes, "OTHER_FOSSIL") if fam == "gas" else classes
            m_fam = sum(float(gm.get(c, 0.0)) for c in fam_all)
            a923_fam = sum(float(cf.get(c, 0.0)) for c in fam_all)
            actual = a930
            if fam == "gas" and actual is not None and "other" in e930:
                # ERCO's post-Nov-2024 EIA-930 "Other" series carries roughly
                # biomass alone (the storage breakout moved batteries to
                # BAT/UES), so the OTHER-class generation the 923 books sits
                # inside NG:NG — subtract only the genuinely-folded portion
                # (mirrors render_calibration_html._gas_foldin_deflation).
                actual -= max(
                    0.0,
                    float(cf.get("OTHER", 0.0))
                    + float(cf.get("biomass", 0.0))
                    - float(e930.get("other", 0.0)),
                )
            reconciled = bool(actual and a923_fam < VINTAGE_RECONCILE_FRAC * actual)"""

_T_SCORER_OLD = "    def test_preliminary_complete_family_defers_to_c1(self):"

_T_SCORER_NEW = """    def test_preliminary_gas_fallback_other_fossil_and_fold_in(self):
        # The EIA-930 family fallback compares like for like (ERCOT 2025 C2
        # counting fix): the model gas sum includes the OTHER_FOSSIL scoring
        # bucket (930 books mixed gas-thermal under NG:NG), and when the
        # bundle carries the 930 "other" series the gas target is deflated by
        # the genuinely-folded OTHER+biomass portion. Here the raw comparison
        # (190.0 vs 196.0 = -3.1%) would breach the ±2.5% target; the
        # like-for-like one (191.2 vs 195.11 = -2.0%) passes.
        _completeness({"ERCOT": {}}, {"ERCOT": {"gas": False, "coal": False}})
        try:
            rows = cv.score_sysvol(
                2025,
                {"gmModel": {"CC_REGULAR": 190.0, "OTHER_FOSSIL": 1.2}},
                {
                    "classFull": {
                        "CC_REGULAR": 188.0,
                        "OTHER_FOSSIL": 0.6,
                        "OTHER": 0.9,
                        "biomass": 0.25,
                    },
                    "e930": {"gas": 196.0, "other": 0.26},
                },
                "ERCOT",
            )
            gas = [r for r in rows if r["key"] == "gas"][0]
            self.assertEqual(gas["status"], cv.PASS)
            self.assertIsNone(gas["classification"])
            self.assertAlmostEqual(gas["model"], 191.2, places=2)
            # target = 196.0 - max(0, 0.9 + 0.25 - 0.26) = 195.11
            self.assertAlmostEqual(gas["actual"], 195.11, places=2)
        finally:
            _reset_completeness()

    def test_preliminary_complete_family_defers_to_c1(self):"""

_T_LOADER_OLD = """    def test_ercot_battery_gen_partial_year_keeps_nan(self):
        \"\"\"2024 (reporting starts mid-year) keeps NaN, never gap-fills.\"\"\"
        bench = load_ercot_battery_gen(2024)
        self.assertIsNotNone(bench)
        dis = bench["battery_discharge"]
        reported = ~np.isnan(dis)
        self.assertGreater(reported.sum(), 0)
        self.assertLess(reported.sum(), HOURS_PER_YEAR)"""

_T_LOADER_NEW = '''    def test_ercot_battery_gen_partial_year_keeps_nan(self):
        """2024 (reporting starts mid-year) keeps NaN, never gap-fills."""
        bench = load_ercot_battery_gen(2024)
        self.assertIsNotNone(bench)
        dis = bench["battery_discharge"]
        reported = ~np.isnan(dis)
        self.assertGreater(reported.sum(), 0)
        self.assertLess(reported.sum(), HOURS_PER_YEAR)

    def test_ercot_2025_extract_hole_filled_from_measured_api(self):
        """The 48-h 2025-12-04/05 extract hole is filled with measured data.

        The hand-curated ERCO extract has all fuels + demand NaN for those two
        local days; the long-format API series carry the measured hours (both
        days for demand, Dec 4 for the fuels). A linear bridge would fabricate
        a flat ~48.6 GW demand valley where the measured days peak at 58.4 GW.
        """
        from market_sim.data.eia_loader import _load_ercot_hourly

        demand, _ = _load_ercot_hourly(2025)
        # Dec 4 = day-of-year 338 -> hours 8088..8135 cover Dec 4-5.
        window = demand[8088:8136]
        self.assertGreater(float(window.max()), 57_000.0)  # measured peak 58.4 GW
        self.assertGreater(float(window.mean()), 52_000.0)  # bridge would be ~49

    def test_ercot_fill_is_noop_for_complete_years(self):
        """2023 has no NaN hours: the measured fill must be byte-identical."""
        from market_sim.data.eia_loader import load_ercot_fossil_gen

        fossil = load_ercot_fossil_gen(2023)
        # Committed bench values (frontend/data/backcast/bench/ERCOT/2023).
        self.assertAlmostEqual(float(fossil["gas"].sum()) / 1e6, 201.465, places=2)
        self.assertAlmostEqual(float(fossil["coal"].sum()) / 1e6, 62.293, places=2)

    def test_ercot_other_gen_reflects_930_storage_breakout(self):
        """NG: OTH collapses post-Nov-2024 (storage moved to BAT/UES)."""
        from market_sim.data.eia_loader import load_ercot_other_gen

        pre = load_ercot_other_gen(2023)
        post = load_ercot_other_gen(2025)
        self.assertEqual(pre.shape, (HOURS_PER_YEAR,))
        self.assertEqual(post.shape, (HOURS_PER_YEAR,))
        self.assertFalse(np.isnan(pre).any())
        self.assertFalse(np.isnan(post).any())
        self.assertAlmostEqual(float(pre.sum()) / 1e6, 1.15, delta=0.05)
        # 2025: ~biomass alone (~0.26 TWh) — the OTHER-class generation the
        # EIA-923 books (~0.9 TWh) sits inside NG: NG (gas fold-in).
        self.assertLess(float(post.sum()) / 1e6, 0.4)'''

_HUNKS = (
    (
        _SCORER,
        "OTHER_FOSSIL scoring bucket (930 books",
        [(_SCORER_H1_OLD, _SCORER_H1_NEW), (_SCORER_H2_OLD, _SCORER_H2_NEW)],
    ),
    (
        _T_SCORER,
        "test_preliminary_gas_fallback_other_fossil_and_fold_in",
        [(_T_SCORER_OLD, _T_SCORER_NEW)],
    ),
    (
        _T_LOADER,
        "test_ercot_2025_extract_hole_filled_from_measured_api",
        [(_T_LOADER_OLD, _T_LOADER_NEW)],
    ),
)


def patch_scorer() -> None:
    """Apply the C2 scorer + test hunks (presence-guarded, byte-anchored)."""
    for path, marker, hunks in _HUNKS:
        s = path.read_text()
        if marker in s:
            print("patch-scorer: %s already patched — no-op" % path.name)
            continue
        for old, new in hunks:
            assert old in s, "anchor drifted in %s" % path.name
            s = s.replace(old, new, 1)
        path.write_text(s)
        print("patch-scorer: %s patched" % path.name)


def write_attestations() -> None:
    """Derive both arms' attestations from the ercot53 keeper's (idempotent)."""
    import json

    src = json.loads(
        (
            REPO
            / "results/calibration/ercot53_hsl_930fill/calibration_attestation.json"
        ).read_text()
    )

    def build(attested_by: str, note: str, keep: set, amend: dict) -> dict:
        out = {
            "schema": src["schema"],
            "governance": dict(src["governance"]),
            "exceptions": [],
            "free_parameters": src["free_parameters"],
        }
        out["governance"]["attested_by"] = attested_by
        out["governance"]["note"] = note
        for e in src["exceptions"]:
            key = (e.get("criterion"), e.get("year"))
            if key not in keep:
                continue
            e = dict(e)
            prefix, magnitude = amend.get(key, (None, None))
            if magnitude:
                e["magnitude"] = magnitude
            e["reason"] = (prefix or "Inherited unchanged by ercot55. ") + e["reason"]
            out["exceptions"].append(e)
        return out

    main_att = build(
        "ercot55 930gap-c2fix keeper-track candidate gate, session 2026-07-10 "
        "(full scored 2023-2025 bundle + zero-forcing ablation twin; owner "
        "promotion PENDING)",
        "Keeper-track line on the ercot53 keeper recipe (coal net-summer derate + "
        "ORDC cap-dual adder + HSL 930-fill), ONE cumulative delta, ZERO new free "
        "parameters: THIS ROUND (ercot55) is a measured-input data-quality + "
        "benchmark-counting fix only. (a) The hand-curated ERCO EIA-930 hourly "
        "extract's 48-h 2025-12-04/05 NaN hole (two real winter-peak days, "
        "measured demand tops 58.4 GW) was bridged by loader interpolation into a "
        "flat ~48 GW valley; NaN windows now fill from the measured EIA-930 "
        "long-format API series (ERCO_region/ERCO_fueltype) before interpolation "
        "(eia_loader._fill_hourly_frame_from_long) - 2023/2024 have no NaN hours "
        "and reproduce ercot53 byte-identically (C3a -1.0/-6.9, C3b 0.109/0.184 "
        "verified). (b) The NG: OTH series is threaded into the bundle "
        "(load_ercot_other_gen) and the C2 family fallback counts like-for-like "
        "against the EIA-930 NG cell: model gas includes the OTHER_FOSSIL mixed "
        "gas-thermal bucket (the membership render_calibration_html._GAS_GROUPS "
        "already used) and the 930 target is deflated by the genuinely-folded "
        "OTHER+biomass portion (post-Nov-2024 EIA-930 storage breakout, ERCO OTH "
        "~ biomass alone). No offer curve, sigmoid, floor, or ORDC parameter "
        "touched; dispatch deltas are confined to 2025 (measured Dec-4/5 demand "
        "restored; Dec 4-5 was NOT a scarcity event - RT max $97 - so no tail "
        "effect).",
        {("price_tail", 2024), ("price_tail", 2025), ("storage_shape", 2024)},
        {
            ("price_tail", 2024): (
                "Inherited unchanged by ercot55 (no scarcity/storage mechanism "
                "touched). ",
                None,
            ),
            ("price_tail", 2025): (
                "Inherited unchanged by ercot55 (no scarcity/storage mechanism "
                "touched). ",
                None,
            ),
            ("storage_shape", 2024): (
                "Inherited unchanged by ercot55 (no scarcity/storage mechanism "
                "touched). ",
                None,
            ),
        },
    )
    surf_att = build(
        "ercot55 surface-ab keeper-track candidate gate, session 2026-07-10 "
        "(full scored 2023-2025 bundle + zero-forcing ablation twin; owner "
        "promotion PENDING)",
        "Keeper-track A/B arm on the ercot55 930gap-c2fix recipe (= ercot53 "
        "keeper recipe + measured EIA-930 long-format gap fill + NG:OTH C2 "
        "counting fix), ONE config delta, ZERO new free parameters: "
        "ercot_offer_surface_conditional=True — the G-22 §8 "
        "heterogeneity-preserving condition-responsive offer surface already in "
        "code (default-off since ercot50), every number measured from the 60-Day "
        "DAM disclosure (peak-band rungs repriced to measured p70/p90 within "
        "measured net-load-percentile bins, P1-only, clamp >=1, cap 0.95xVOLL; "
        "no offer curve, sigmoid, floor, or ORDC parameter touched). "
        "Re-litigation basis: ercot50's rejection predates rubric v2.4 and the "
        "ercot52 ORDC cap-dual fix; the record (2026-07-10 ERCOT-54 log entry) "
        "notes no full-span surface A/B existed on the current keeper config. On "
        "that basis the old 2023 C3a objection dissolves (+2.0% PASS vs the "
        "ercot52-era +35%) and the mechanism closes C3c-2025 outright (24h vs 23 "
        "DA actual, 1.04x) while respecting the C3c-2023 >=162h owner gate "
        "(166h) and improving C3a-2024 (-6.9% -> -4.7%). Scarcity-anticipating "
        "DA offer formation is real ERCOT behaviour (the G-22 finding); the "
        "surface is its measured, forward-reproducible representation "
        "(rule 1/13/14).",
        {("price_tail", 2024), ("storage_shape", 2024)},
        {
            ("price_tail", 2024): (
                "Inherited open scarcity-formation limitation, narrowed by the "
                "measured offer surface (24h -> 27h, 0.35x -> 0.40x) but still "
                "short of the 0.5x gate: the residual is the depth/breadth of "
                "the 2024 shoulder events plus one non-scarce event (Nov 17 "
                "midday) — the already-filed G-22 online-capability/DA-boundary "
                "residual. ",
                "27h vs DA actual 68h (0.40x, FAIL)",
            ),
            ("storage_shape", 2024): (
                "Inherited unchanged by ercot55 (no storage mechanism touched). ",
                None,
            ),
        },
    )
    for name, att in (
        ("ercot55_930gap_c2fix", main_att),
        ("ercot55_surface_ab", surf_att),
    ):
        path = REPO / "results" / "calibration" / name / "calibration_attestation.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(att, indent=1))
        print("write-attestations: %s" % path.relative_to(REPO))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--thread-other", action="store_true")
    ap.add_argument("--append-log", action="store_true")
    ap.add_argument("--patch-scorer", action="store_true")
    ap.add_argument("--write-attestations", action="store_true")
    args = ap.parse_args()
    if not (
        args.thread_other
        or args.append_log
        or args.patch_scorer
        or args.write_attestations
    ):
        sys.exit("nothing to do: pass at least one --flag")
    if args.thread_other:
        thread_other()
    if args.patch_scorer:
        patch_scorer()
    if args.write_attestations:
        write_attestations()
    if args.append_log:
        append_log()


if __name__ == "__main__":
    main()
