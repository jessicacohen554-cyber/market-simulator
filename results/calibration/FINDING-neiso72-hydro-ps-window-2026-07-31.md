# FINDING (neiso-72): NEISO's hydro LEVEL is PER-WINDOW — the pumped-storage
# TIME SPLIT closes the last open cell of the `hydro_level_923_hy` row

**Session:** neiso-72 (the miso-109 §7 / pjm-143 §2 hand-back — NEISO's own
lane; handoff Lever B)
**Date:** 2026-07-31
**Verdict:** LEVEL FIX **landed** (rule 14 `[R-ACCURATE]`) and the candidate is
**CALIBRATED-WITH-CAVEATS with every criterion IDENTICAL to the outgoing
keeper** — all nine statuses unchanged (6 PASS, C3c `price_tail` CAVEAT
ledgered, `shape` SKIPPED), C1 **all 12/12 · free 8/8**, determination
unchanged. **No gate flipped in either direction.** Promoted to NEISO keeper
(owner authorization on record in-session: design D sign-off + "if structural
integrity improves but gates regress that may still be a keeper" — the
regression clause was **not needed**). `hydro_level_923_hy` NEISO **`U` → `K`**;
the row's cross-ISO audit is now **CLOSED at all six ISOs**.
**Rule 25:** every number derived from NEISO's own data this session
(`scripts/probes/_neiso72_ps_window_audit.py`); §2 states where the MISO and
PJM arguments do NOT transfer.
**Runs:** `neiso72_control_A` (keeper recipe at HEAD `10c624e`, pin armed all
years) and `neiso72_hy_window_B` (same HEAD + the single-delta windowed
refusal) — both registered (rule 15).
**Pre-registration:** `PREREG-neiso72-hydro-ps-window-2026-07-31.md`, committed
and pushed **before either arm solved**, including the E1 sign, the kill/keep
rule, the liveness bar, and the owner-adjudicated design decision (D over
B/C/E).

---

## 1. The defect: a time split, not a standing fold

NEISO is the **only one of the six ISOs that files an EIA-930 `NG: PS` column
at all**, and it starts filing part-way through the series. The seam is a
single hour, measured: **2024-11-07 00:00** (row 7440 of the 2024 extract) —
zero filed `NG: PS` hours in every month 2019-01 → 2024-11-06, continuous
filing after, discharge-only (2025: +1.932 TWh, 0.000 pumping).

Before that hour NEISO's `NG: WAT` folds pumped-storage discharge; after it,
the series is clean. Four independent tests (probe §§2, 6, 8, 9), the decisive
one confound-free: **the seam falls inside November 2024**, so Nov 1–6 vs
Nov 7–30 compares the same fleet on the same water six days apart — max
1,873 → 685 MW, diurnal swing 7.11× → 1.79× — while the identical cut in the
five no-seam years 2019–2023 moves only 0.77–1.03×. Nameplate breaches
(63–276 h/yr through 2024) stop **permanently** at the seam: 0 hours in 2025.

**The level gap understates the defect by ~8×.** The 930-vs-923 gap is only
+2.7 % / +10.1 % (2023/2024) because two large errors cancel: the ~1.9 TWh/yr
PS fold rides on top of a ~1.2–1.6 TWh/yr **under-count** of conventional
hydro in the 930 telemetry (Dec 2024, the one clean complete-census month,
runs 8 % below 923). The pinned level was not "nearly right" — it was two
~1.5–1.9 TWh errors landing near zero together, exactly the silent
compensation rule 14 exists to catch.

**Pumped storage itself is untouched and was never absent.** NEISO PS is
endogenous storage in the LP (`model/storage.py::load_eia860_pumped_storage`,
tech `pumped_storage`, **1,865.0 MW** = Northfield 1,168 + Bear Swamp 666 +
Rocky River 31, RTE 0.80), discharging 0.400/0.364/0.497 TWh in the keeper.
The pin **double-represented** PS: endogenous storage dispatch *plus* the same
discharge again as MC=0 "river water" in the conventional budget. The fix
removes the mislabeled copy, not the resource.

## 2. The fix — design D, and where the sibling ISOs' arguments do not transfer

`constants.EIA930_PS_SPLIT_COMPLETE_FROM = {"NEISO": 2025}` +
`data/hydro.py::eia930_wat_level_folded`: the `NG: WAT` monthly level pin is
**refused per-year** for years before the first wholly-split calendar year
(their level stays on EIA-923 `HY`, the units' own complete-census filings —
173/169 plants in 2023/2024) and **kept** for wholly-split years (2025+). The
seam year counts as folded — one source basis per year, never a mid-year
splice. The forecast lane takes the 923 climatology while the window holds any
folded year, and **un-arms itself** once the window rolls wholly past the seam
(rule 13's forward story, mechanical). Zero free parameters; both lanes gate on
the same measured registry.

**Owner-adjudicated against three alternatives** (PREREG §4–§4a): (B) the flat
MISO/PJM registry switch would replace 2025 — the one year whose 930 series is
measured clean — with a 6-plant early-release stub; (C) a mid-year seam splice
injects an artificial step between two systematically-different sources inside
2024; (E) "930 minus an estimated PS" recovers the telemetry subset —
**16.6 % / 19.1 % below** what the modeled units measurably generated — and
adds an estimated 154–263 MW parameter with no forward story.

**Rule 25, both directions.** NEISO could not take the MISO/PJM switch
(different data situation: the split exists here), and their
no-reconciliation-factor arguments were re-derived rather than transferred:
NEISO's monthly gap changes sign in 21 of 70 pre-split months (MISO's
sign-change argument holds here; PJM's never-changes-sign does not), and the
gap's magnitude is dominated by the second discrepancy rather than the fold —
a structure neither sibling has.

**Rule 19.** The keeper carries `hydro_budget_nameplate_aware=False`,
`hydro_dispatch_envelope=False`, `hydro_min_flow_floor=False`,
`hydro_ror_split=False` — the pin was the **only** mechanism setting NEISO's
hydro level, and the fix replaces it in place. Nothing stacked; no companion
mechanism goes inert (NEISO never armed one).

## 3. The A/B — every pre-registered check passed

Same-HEAD single delta (`10c624e`; arm `changed_files` = the registry constant
+ `hydro.py` + a ScenarioConfig comment + tests). Control reproduces the
neiso-71 keeper **to 4 decimals** (hydro 8.7038/7.3273/5.1064 TWh; LMP
$39.1030/43.8038/71.9708).

| check | declared | realized |
|---|---|---|
| control integrity | reproduce keeper | **4-decimal match** on dispatch and LMP |
| budgets (builder, no-LP) | 8.5762 / 6.7144 / 5.1207 | **exact** |
| 2025 wiring (KILL check) | bit-identical | **`.equals=True`** on all three hourly sidecars |
| liveness | >50 MW in 23/24 | **632 / 713 MW** max hourly class delta; 2025 inert by design |
| E1 sign | hydro ↓, CC ↑, LMP ↑ in 23/24; 2025 flat | hydro **−0.186/−0.654/0** TWh; CC_REGULAR **+0.178/+0.583/0**; LMP **+$0.050/+$0.159/+$0.000** |
| E1 magnitude | +0.02…0.20 $/MWh | inside the band, both years |

## 4. Scoring — identical scorecard, defect removed

| criterion | keeper (neiso-71) | candidate |
|---|---|---|
| fuelmix (C1) | PASS — all 12/12 · free 8/8 | PASS — **all 12/12 · free 8/8** |
| sysvol, price_mean, price_shape, dispatch_corr, governance, forced_share (C8) | PASS | PASS |
| price_tail (C3c) | CAVEAT (ledgered) | CAVEAT (same ledger entries, carried verbatim — max +$0.16 mean move leaves the RT tail anatomy untouched; 2025 bit-identical) |
| shape (C7) | SKIPPED (NEISO) | SKIPPED |
| **determination** | CALIBRATED-WITH-CAVEATS | **CALIBRATED-WITH-CAVEATS** |

**Bench-basis note (successor, pjm-143 precedent).** The C1 hydro benchmark
actual for 2024 is itself the PS-folded 930 series (**7.3942 TWh exactly**),
and 2025's is the 930 value (5.1207) by the preliminary-923 swap. The
candidate's 2024 hydro ratio therefore degrades *on paper* (≈0.99 → ≈0.91)
against a contaminated actual while staying inside its C1 band; the honest
2024 actual (923 complete census, 6.7136 TWh) would score it ≈0.99. Re-basing
the bench hydro actual is a separate, scorer-side lane — never a reason to
re-contaminate the level (rule 14).

**Attestation** (`gen_neiso72_attestation.py`): governance re-attested to this
session; C3c exceptions carried verbatim; **DOF ledger unchanged** (n_entries
12, n_residual 5) — the delta removes a measured overlay's applicability and
adds zero parameters.

## 5. Governance

* **Rule 22:** 2023–2025 only. NEISO's locked test is SPENT and untouched; the
  probe reads 2019–2022 *raw source files* for the seam measurement only — no
  solve, no scoring, no registration outside the training years.
* **Rule 16:** both arms span 2023–2025, one bundle each. **Rule 12:** one
  3-year invocation per arm (NEISO ~3.7 GB RSS), arms sequential across the
  code edit; nothing committed while either solve ran.
* **Rule 15:** both arms registered; the retention sweep pruned
  `2026-07-13-neiso-60-phantom-outage` and `2026-07-19-neiso-gasshape-interpfix`
  (top-15 per ISO).
* **Rule 26(b):** `hydro_level_923_hy` NEISO cell `U` → `K` with citation this
  session; matrix header re-stamped; §5.6/§5.7 updated.
* **Rule 27:** Opus/Fable session; all edits local via the Edit tool; every
  pushed ≥300-line file blob-verified.

## 6. Successors (named, not begun)

1. **Storage-layer PS cycling depth** — the split data is the fleet's first
   measured gross-cycling series and shows ~4× under-cycling (1.932 measured
   vs 0.497 endogenous, 2025). A storage-side lever (dispatch-adder
   identification / AS value in the storage objective), never a hydro patch.
2. **Bench hydro basis** — re-base the 2024 C1 hydro actual onto the 923
   complete census (scorer-side; see §4).
3. **Sizing the 930 conventional under-count** (~1.2–1.6 TWh/yr) — only
   weakly identified today (one clean complete-census month).
4. **Hourly-`NG: WAT` hazard** — `hydro_dispatch_envelope` /
   `hydro_min_flow_floor` inherit the pre-seam contamination; both default-off
   and off in this keeper. Arming either at NEISO needs its own source fix.
5. **Handoff Lever A** — the CC_CHP capacity basis (Kendall Square ~90 MW),
   the PRIMARY arm left for its own session.
