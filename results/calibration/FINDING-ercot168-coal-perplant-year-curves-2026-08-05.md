# FINDING — ercot-168: the coal per-plant offer curves re-identified PER-YEAR for 2023 from the delivery-2023 SCED corpus — ALL SEVEN pre-registered gates GREEN, C7-2023 CLOSED, surfaced as KEEPER CANDIDATE

**Charter:** mechanism-testing-matrix §5.1 **item 12** (owner-chartered at ercot-166;
owner-adjudicated 2026-08-05 — **OPTION A**). Governance basis, quoted, not re-litigated: *a
rule-14/23 data-vintage fix of an armed K mechanism (the ercot-157 corpus re-upload dissolves
ERCOT-143's closure premise "no 2023 SCED exists"), NOT a claim that "2023 bid differently" — same
modal derive, fed the year's own rows, zero new DOF.* No commodity backing is claimed for the
lignite repricing (precommit §1f: no measured fuel series moves at any offer step — the Aug–Oct
repricing is conduct, not commodity). OPTION B (spread-regime-conditional offer top) stays
DEFERRED as the forecast-side successor. Gates were pre-registered in
`docs/PRECOMMIT-ercot168-coal-perplant-year-curves-2026-08-05.md` BEFORE any solve; **no
amendment was needed — no gate was touched, and no feasibility repair was required.**

**Mechanism** (`coal_perplant_offer_yearly`, default off, zero fitted scalars): for a solve year
PRESENT in `constants.COAL_PERPLANT_OFFER_CURVE_YEARLY_BY_ISO` (2023 only), each CAMPD coal
`_committed`/`_econ*` tranche of a listed plant is priced per (month × hour-window) cell at the
capacity-weighted measured price of its window on that cell's plant curve — the ercot-144 modal
construction applied at the corpus's own hourly submission grain under a strict day-majority
(>0.5 of the month's live days) stability license, CPT→CST converted at derivation. `_mustrun`
(ERCOT-137) and `_peak` (ERCOT-140) rows keep their own measured owners (rule 19). A year ABSENT
falls through to the armed static curves — **verified bit-identical, not assumed (G-BIT)**.

## 1. Probe (2023-only, throwaway per rule 16 — deleted, never registered)

Engaged first try: 20 committed/econ tranches across 10 plants (Oak Grove 6180 spanning
[3.81..61.46] — the $60-class overnight curve with October's $61.46). LP feasible, no
infeasibility repair needed (unlike ercot-167's two amendments). C7 COAL_LIGNITE 2023 cv_ratio
0.331 → 1.193, profile_r 0.897 → 0.976; tail/spurious/shed 61/3/4 — all unchanged vs control.
Two container defects were repaired BEFORE any solve (neither touches the model): missing tzdata
(US/Central) installed, and the gitignored `gtc-limits` clean partition regenerated from the
committed NP6-86 raw archives (the ercot-167 discipline; 2023: 17 GTCs / 13,452 rows).

## 2. Full-span A/B (control `ercot168_control_A` = fresh same-HEAD replay; arm
`ercot168_yearcurves_B` = single delta `coal_perplant_offer_yearly=true`)

Control-A drift vs the committed keeper: **≈ zero** (C3a −32.24 vs −32.2, C3b 0.6026 vs 0.603,
tail/spurious/shed identical, D-1 identical to the third decimal) — the regenerated-input basis
is clean.

| gate | verdict | A → B |
|---|---|---|
| G-BIT (KILL) | **PASS** | ALL twelve 2024+2025 hourly sidecars sha256-IDENTICAL (class/system/storage/reserve_family/network/unit_hourly × 2 years; price series inside `system_*`) |
| G-TGT (target) | **PASS — full clear** | 2023 COAL_LIGNITE cv_ratio **0.331 → 1.193** (gate ≥0.5; model_offpeak_cv 0.019 → 0.068 vs actual 0.057) |
| G-SHAPE (KILL) | **PASS** | 2023 COAL_LIGNITE profile_r **0.897 → 0.976** (floor 0.80 — the cv fix *improves* the shape leg) |
| G-NEWROWS (KILL) | **PASS** | D-1 failing rows 1 → **0**; COAL_PRB 2023 **improves** 0.737 → 0.958 (r 0.996 → 0.997) — the Martin Lake +$1.9 effect helps, not hurts |
| G-NOREG (KILL) | **PASS** | C1/C2/C4/C6/C8 PASS all years (official verdict); 2023 C3a −32.24 → −32.23 (+0.01 pp, band ±1.0), C3b 0.6026 → 0.6043 (+0.0017, band ±0.02); 2024/25 covered by G-BIT |
| G-SPUR (KILL) | **PASS** | 2023 spurious tail 3 → 3 |
| G-SHED (KILL) | **PASS** | 2023 slack>1 MW hours 4 → 4 |

**Report-only, as pre-registered:** 2023 Aug lw −$0.34 (118.66 → 118.32), Sep +$0.01 — the
"modest belly" expectation confirmed in sign-ambiguous form: the repricing is a *dispatch-shape*
mechanism at ~$20 overnight LMPs, deep inframarginal in every actual tail hour, so it cannot and
does not move the −32 % (whose tail mass stays the rubric-v3.0 C3c model-class ledger; counts
61/25/3 UNCHANGED). Oct–Dec lift +$0.24–0.47 (the Martin Lake step crossing the ~$21 overnight
LMP at the margin). 2023 class energy: COAL_LIGNITE 17.66 → 16.91 TWh, COAL_PRB 45.05 → 43.62
TWh — the measured overnight backdown replacing forced flatness. The non-Oak-Grove admitted
cells (TNP/JKS/SCES): dispatch-inert to small, folded into the above; 2024/25 strictly zero by
G-BIT. D-4's CT_PEAKER reliability-floor rows are the keeper's own pre-existing object
(96.8 → 96.6 % / identical / identical) — no new row.

## 3. Verdict: ALL GATES GREEN — surfaced as KEEPER CANDIDATE (owner call; not self-promoted)

Official determination (registered, attested): **NOT-YET on {C3a-2023 −32.2 %, C3b-2023 0.604 +
2024 0.206}** — the fail set SHRINKS from the keeper's {C3a, C3b, **C7**}: the 2023 C7
protective FAIL, open since ERCOT-142 chartered the lane, is **CLOSED by the year's own measured
conduct**. The LP now two-shifts Oak Grove through price formation exactly as SCED did (backed
down to the mustrun floor at ~$20 overnight LMPs under its measured $60-class overnight curve;
the Aug 15–19 scarcity-night pause reproduces endogenously because those nights price ≫ $60).
DOF: zero new free parameters (n_entries 12 → 13, the added entry measured-physical; n_residual
UNCHANGED at 6); the base `coal_perplant_offer_curves` entry's "2023 application is a declared
extrapolation" note is **RETIRED by measured replacement**
(`scripts/gen_ercot168_attestation.py`). LOYO (rule 22): the identification is per-year by
construction — the 2023 table consumes only 2023 rows and 2024/25 are G-BIT byte-identical — so
leave-one-year-out reduces to the per-year gate table, green in every year.

## 4. Named successors (NOT chartered here — owner queue)

The delivery-2023 corpus dissolves the SAME declared premise ("no 2023 SCED disclosure exists")
on three more armed identifications, each a candidate rule-14/23 re-derivation charter of item-12
kind — with the sharper note that all three are margin forms claimed FUEL-INVARIANT, so the 2023
rows can now *test the invariance claim itself* (does the 2023 curve-bottom land at
level + HR×(fuel₂₀₂₃ − anchor)?), not merely re-derive:

- `COAL_OFFER_MARGIN_LEVEL_BY_ISO` ERCOT 15.8807 (ERCOT-137 coal `_mustrun` min-load level;
  ercot-136 `B1_curve_bottom`, four 2024–25 subsets);
- `CC_COMMITTED_OFFER_LEVEL_BY_ISO` ERCOT 10.354 (ERCOT-139 gas-CC `_committed` level; same
  instrument and subsets);
- `COAL_PEAK_OFFER_LEVEL_BY_ISO` 35.1989 + `COAL_PEAK_OFFER_GAS_HR_BY_ISO` 10.4100 (ERCOT-140
  coal `_peak`; ercot-138 p90 rows, same subsets).

Checked and NOT affected: the walls/fast-start pool/steam blocks (2023-refreshed at ercot-157),
storage AS product shares (2023 at ercot-167), the gas offer anchor (fuel workbooks, covers
2023), the gas bridge `min_load_frac` 0.574 (60-Day **DAM** corpus, always had 2023). CT bands
stay CLOSED — ERCOT-147's refusal was conduct-stability (modal identity 11/160), not corpus
coverage (the DO-NOT-REDO fence).

## 5. Registration & bookkeeping

Both runs registered (rule 15): control `2026-08-05-ercot168-control` (fresh same-HEAD replay;
NOT-YET, unattested-by-design) and arm `2026-08-05-run168b-year-curves` (keeper candidate).
Retention pruned `2026-07-31-ercot145-gas-daily-shape` and `2026-07-31-ercot148-dam-event-cap`
(top-15). Matrix §5.1 item 12 stamped EXECUTED-with-verdict; the `coal_perplant_offer_level`
row's note/citation and `def` updated with the new fields (rule 28b/c). The C3c model-class
ledger entries are UNAFFECTED (61/25/3 unchanged, nowhere near the [0.5×] band). Promotion is an
owner decision on this record.
