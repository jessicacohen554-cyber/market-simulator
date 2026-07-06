# FINDING — PJM keeper burndown: the failing legitimacy criteria (2026-07-05)

**Thread:** the pjm-76 keeper (`results/calibration/pjm76_outage_fix`) returns
legitimacy **Overall: FAIL** on **D-4 off-window binding**, and the extended
statistical-mode rubric reports it at 5→7 fails. **Task:** adjudicate the
failing criteria with single-year throwaway diagnostics; separate the
**evidence-indicted structural bugs** from the **known-open, out-of-scope**
residual (commitment / per-gen reserve, memory-blocked). Priorities: (a) which
offer bands survive a physical grounding test; (b) does PJM CT/CC evening merit
show the CAISO sub-SRMC-CC-flood pattern; (c) does any class show a
flat-floor/drag signature, and is the pjm-75 CT drag D-8-stable.

**Method.** Reproduced the pjm-76 recipe for **2024 only**
(`scripts/diag_pjm_burndown_2024.py`, rule-15 throwaway — NOT registered),
extracted P1 per-class hourly dispatch, and cross-read the reliability-floor CSV
+ engine, the offer-band overrides, and measured CAMPD pure-play CT_PEAKER
hour-of-day CF (`scripts/diag_pjm_ct_hotday_hod.py`). **This burndown also
uncovered a legitimacy-scoring integrity bug (the meta-gap, §5) that had been
masking the true D-2 picture for every drag keeper — the most consequential
finding here.**

---

## 1. Deciding failure: D-4 off-window binding (reliability_floor × CT_PEAKER)

pjm-76 D-4 FAIL, all years: `reliability_floor × CT_PEAKER` binds 99.1 / 99.7 /
97.5 % of its floored MWh **outside** its justified window h15-21.

**Root cause.** The two enabled PJM CT_PEAKER reliability limbs (`PJM_EMAAC`
tmax 33.3 °C floor 0.2838, `PJM_West_APS` tmax 31.7 °C floor 0.3208) carry **no
`start_hour`/`end_hour`**, so on a hot day they floor CT_PEAKER at ~0.28–0.32 ×
capacity **all 24 h**. pjm-75 had *added* the CT net-load deployment drag
(`ct_netload_drag`, ramp window **[15,22)**) as the CT commitment mechanism
**while the reliability floor already floored CT_PEAKER**, and never reconciled
them (CLAUDE.md rule 19).

**Measured proof (CAMPD, `diag_pjm_ct_hotday_hod.py`).** On EMAAC design-cooling
days the pure-play CT_PEAKER fleet CF is **0.0165 overnight (h0-6)** vs **0.376
afternoon (h15-19)** — a **23× ratio**. In the model P1 solve the floor forces
CT_PEAKER in the two zones to **941 MW overnight on hot days** vs **34 MW on
non-hot nights** (the economic level) — a 28× phantom equal to the 0.12 TWh
D-2 attribution. In-window [15,22) the drag (≤0.46) dominates the reliability
floor (0.28–0.32) via `np.maximum`, so the reliability floor's *only* marginal
contribution is off-window overnight — where CT is offline (rule 17: a floor
binding where its own driver says the class is offline is a bug by definition).

**Fix (implemented, `drop_drag_owned_reliability_specs`).** When a net-load drag
owns a class's commitment, drop that class's reliability-floor limbs — the drag
becomes the single CT_PEAKER mechanism (rule 19). A grounded floor removal, not
a residual tune. Gated on `config.ct_netload_drag`, so any run without the drag
is byte-identical (only CAISO — 0 enabled CT limbs — and PJM use the drag).
Confirmed: after the fix, `reliability_floor × CT_PEAKER` is gone and the drag
passes D-4 (0 % off-window, correctly windowed).

---

## 2. Priority (a) — which offer bands survive a physical grounding test

Physical floor for a non-CHP, non-take-or-pay class: **committed/econ_low ≥
1.0×** SRMC (Manual-15 composite-cost recovery; the LP has no no-load variable).

| class | committed / econ_low | verdict |
|---|---|---|
| CC_REGULAR | 1.00 / 1.00 | **SURVIVES** — Manual-15 floor (pjm-74) |
| CT_PEAKER | 1.05 / 1.05 (econ_high 1.27) | **SURVIVES** — above floor; 1.27 = Manual-15 §2.3 cost-cap |
| COAL_* | 0.51–0.68 | **SURVIVES on physics** — take-or-pay incremental cost (odd-precision values residual-set *within* the grounded band) |
| CC_CHP / CT_CHP | 0.66 / 0.86 | **SURVIVES on physics** — CHP steam-host credit |
| **ST_GAS** | **0.4752 / 0.6552** | **FAILS** — non-CHP gas steam at 0.48× SRMC; part-load IHR is *above* full-load, so committed should be ≥1.0×. Pure residual artifact (pjm-59..74 sweep). |
| **CT_INTERMEDIATE** | **0.9 / 0.92** | **FAILS** — non-CHP CT below the SRMC floor, no physical basis |

**Proposed re-grounding (deferred).** Apply the CC_REGULAR Manual-15 floor to
ST_GAS / CT_INTERMEDIATE committed/econ_low → 1.00. Grounded, not a re-tune.
Deferred to its own regression-logged cycle: both are small classes (ST_GAS ~15.7
TWh), neither drives a scored FAIL (2024 aggregate mix is clean — coal 122.3 vs
122.4, gas 377 vs 391 TWh), and raising them shifts all three years.

## 3. Priority (b) — CAISO evening-merit pattern? **No.**

The CAISO finding traced CT being priced out to a **sub-SRMC CC committed band
(0.90×)** flooding cheap CC. **PJM does not have that** — CC_REGULAR
committed/econ_low = **1.00 / 1.00** (Manual-15 floor). CC still runs a ~32–40 GW
block every hour, but that is the **correct LP answer** (CC HR ~7 vs CT ~10, the
same energy-only ramp-free gap as CAISO) **without the sub-SRMC offer bug**. CT
is merit-dominated + missing ramp/local structure — which the `ct_netload_drag`
stands in for. The sub-SRMC bands that *do* exist (ST_GAS, CT_INTERMEDIATE, §2)
are small classes, not the CC flood. The CC over-run + scarcity-tail miss (0
hours > $200 vs actual 6/18/59) is the **known memory-blocked per-gen reserve gap**
(`docs/multi-iso/pjm-reserve-ordc.md` Phase 2) — out of scope.

## 4. Priority (c) — flat-floor / drag signatures; the CT-drag D-8 verdict

**Two signatures found, distinct:**

1. **`reliability_floor × CT_PEAKER` flat-floor (§1) — FIXED.** The 941-vs-34 MW
   overnight measurement is a textbook flat-floor pinning a fast-start class
   overnight.
2. **`ct_netload_drag` over-forces CT in the tight 2024 year — OPEN (§5).** With
   the diagnostics counting the drag correctly (the meta-gap fixed), the drag
   floors **12.1 % of CT_PEAKER energy in 2024** (2.49 of 20.68 TWh), breaching
   rule 20's 10 % peaker budget (2023 7.6 %, 2025 7.9 % pass). This is the real
   *drag* signature — not a mis-window (the drag *is* correctly windowed [15,22),
   0 % off-window in D-4) but a *magnitude* budget breach in the tightest year.

**CT-drag D-8 stability: the hinge itself is sound.** Coefficients derive from
CAMPD pure-play CT CF vs EIA-930 net-load pooled 2023–2025, ramp-window Spearman
ρ = **0.50 / 0.51 / 0.60** (monotonic, year-stable); hinge SSE 0.133 beats the
unclipped ERCOT-recipe line 0.176. The drag is the *grounded* mechanism; its
only issue is that a grounded reserve-deployment floor sized to measured CT can
exceed the rule-20 merchant budget in a tight year (see §6 open items).

---

## 5. The meta-gap: legitimacy diagnostics were silently dropping the drag

**The most consequential finding.** `solve_and_persist` did **not** persist
`ct_netload_drag` / `ct_drag_overrides` in `meta.json`. The legitimacy-diagnostics
floor reconstruction (`run_year(fleet_only=True)` from `meta.json`) therefore
rebuilt floors **without the drag** for every drag keeper. Consequences:

- **pjm-76's committed D-2 PASS (CT_PEAKER 0.68 %) was an artifact** — its
  diagnostics JSON contains *no* `ct_netload_drag` mechanism at all. The drag's
  real ~12 % 2024 forced energy was never counted. So was every drag keeper's.
- The D-4 CT_PEAKER fix (§1) is invisible in the drag-off reconstruction (the
  gate keys on `config.ct_netload_drag`, absent from meta), so it *cannot* be
  demonstrated in committed diagnostics until the gap is closed.

**Fix (implemented).** Persist `ct_netload_drag` / `gas_st_netload_drag` /
`ct_drag_overrides` in `meta.json` so reconstruction matches the solve. With
accurate reconstruction, pjm-77 shows: **D-4 `reliability_floor × CT_PEAKER`
resolved** (the §1 fix is now visible and confirmed) while **honestly surfacing**
the two pre-existing issues the gap had hidden (§4.2 drag D-2; §6 CT_CHP D-4).
Per CLAUDE.md rule 14, the accurate diagnostics are kept even though they reveal
more failures — the residual is a discovered bug, not something to bury back in
an inaccurate input.

## 6. CT_CHP D-4 — the same disease on the CHP fast-start class (OPEN)

Removing the CT_PEAKER floor shifts the overnight merit so CT_CHP settles onto
its own all-24h reliability limb (`PJM_EMAAC` CT_CHP tmax 0.1764), which then
binds **70.8 % off-window** (0.0095 TWh — tiny, but the share trips D-4). This is
the *same* all-24h flat-floor bug as CT_PEAKER, on the CHP fast-start class, but
CT_CHP is **not drag-owned**, so `drop_drag_owned_reliability_specs` doesn't
cover it. Correct fix (follow-up): the CT_CHP tmax reliability limb is a hot-day
*cooling* commitment (daytime) — window it to the cooling peak, or disable it (its
genuine round-the-clock commitment is steam-host, handled by the `chp_steam`
mechanism, which is retained). Left as a documented open item — a small, scoped
follow-up, not bundled into this session's structural change.

---

## 7. Conclusion

| item | status |
|---|---|
| D-4 `reliability_floor × CT_PEAKER` off-window (the deciding pjm-76 failure) | **FIXED** — `drop_drag_owned_reliability_specs` (rule 19), grounded floor removal |
| meta-gap hiding the drag from diagnostics (all drag keepers) | **FIXED** — persist drag flags in meta.json (rule 14: accurate diagnostics) |
| offer bands ST_GAS / CT_INTERMEDIATE sub-SRMC (a) | **PROPOSED** re-grounding, deferred (small, own cycle) |
| CAISO sub-SRMC-CC-flood pattern (b) | **ABSENT** in PJM (CC committed at 1.0 floor) |
| `ct_netload_drag` D-2 12 % 2024 peaker-budget breach (c) | **OPEN** — pre-existing, family-wide; a grounded drag exceeding rule 20 in a tight year needs a drag-sizing or D-2-exemption decision, not a fit move |
| CT_CHP D-4 off-window | **OPEN** — same disease, window/disable its cooling limb (follow-up) |

**pjm-77** (pjm-76 recipe + the §1 fix) demonstrably resolves the deciding
CT_PEAKER D-4 failure and, via the §5 meta-gap fix, gives PJM its first
*accurate* legitimacy diagnostics — which honestly show two pre-existing issues
(drag D-2, CT_CHP D-4) that were masked before. It is structurally superior to
pjm-76 on the tasked axis and on diagnostic integrity, but it does **not** clear
Overall (the drag D-2 breach is a grounded-mechanism / rule-20 tension shared
with pjm-76 and unresolvable by weakening the drag). **Recommendation:** promote
the code fixes; treat the drag-D-2 budget and CT_CHP-D-4 as the next PJM
root-cause threads; re-score the drag-keeper family (pjm-76, caiso-51) on the now-
accurate diagnostics before any keeper-status claims.

## Files
- `scripts/diag_pjm_burndown_2024.py`, `scripts/diag_pjm_ct_hotday_hod.py` — throwaway diagnostics (rule 15).
- `src/market_sim/config/iso_configs.py` (`drop_drag_owned_reliability_specs`) + `scripts/run_calibration.py` wiring — the §1 fix.
- `scripts/run_calibration_full.py` — the §5 meta-gap fix (persist drag flags).
- `scripts/run_pjm77_ct_relfloor_reconcile.py` — keeper candidate.

---

## Addendum 2026-07-06 — §6 CT_CHP D-4 RESOLVED (scrub, option b — the driver measurement refuted option a)

§6 offered two fixes: window the EMAAC CT_CHP tmax limb to the cooling peak, or
disable it. Measuring the driver decided it: CAMPD EMAAC pure-play CT_CHP
(18 plants, 0.32 GW) hot-day hour-of-day CF, 2023–2025
(`scripts/diag_pjm_ctchp_hotday_hod.py`), shows the hot-day lift is an
**all-hours steam-host intensification, not an afternoon cooling window** —
in-window [15,22) share of the CF increment 31.3 / 32.0 / 34.6 % vs 29.2 % for
a perfectly uniform lift, with overnight hot-day CF ~0.12 vs mild-day ~0.098
(the class is NOT offline overnight, unlike pure-play CT_PEAKER at 0.0165).
Re-windowing to h15-21 would have cleared D-4 while contradicting the limb's
own driver data — a diagnostic-tuned window. The limb's floor level is also
unattainable: floor_pct 0.1764 exceeds the measured mean hot-day CF in **every
hour of the day** (max 0.149 midday 2023).

**Fix (implemented):** the limb is SCRUBBED (`enabled=False` + annotation in
`reliability_floor_coeffs_PJM.csv`), mirroring the neiso-48 / caiso-52 CT tmax
scrubs. The class's round-the-clock commitment — including its measured hot-day
lift — is the steam-host phenomenon, owned by `chp_steam` (0.29–0.31 TWh forced
in pjm-77, retained; rule 19: reconcile, never stack). Zero-parameter mechanism
deletion; no fitted value changed.

**D-4 confirmed clearing** (payload-dispatch + rebuilt-floors recompute on the
pjm-77 bundle, same method pre/post): pre-fix reproduces the
`reliability_floor × CT_CHP` off-window FAIL (share 0.7083); post-fix the
mechanism carries zero floored MWh and **D-4 passes all three years** (the drag
rows pass at 0 % off-window throughout). The only remaining D-2 failure is the
pre-existing §4.2 drag 2024 peaker-budget breach — see
`docs/handoffs/pjm-c8-drag-memo-2026-07.md` (owner decision).
