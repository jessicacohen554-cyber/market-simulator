# FINDING — ercot-169: the fuel-invariance claim of the three armed ERCOT margin identifications, tested on the delivery-2023 SCED corpus — 1 CONFIRMED, 2 NOT-IDENTIFIABLE-2023

**Charter:** mechanism-testing-matrix §5.1 **item 13**, chartered by the ercot-169 handoff on the
ercot-168 FINDING §4 named-successor list. **PHASE 0 — NO LP, no solve, keeper UNCHANGED
(`2026-08-05-run168b-year-curves`), no `ScenarioConfig` field written, no cell verdict flipped
(all three mechanisms stay `K`).** Decision rule pre-registered and committed BEFORE any derive
ran: `docs/PRECOMMIT-ercot169-margin-fuel-invariance-2026-08-05.md` (commit
`ercot-169 PRECOMMIT…`, pushed and blob-verified before the corpus was read). **No band,
threshold or instrument was moved after measurement, and no amendment was needed.**

## 0. The object

Three armed identifications each carry the same declared-extrapolation note: *"2023 application
is a declared extrapolation (no 2023 SCED disclosure exists) — the margin is fuel-invariant by
construction."* The ercot-157 delivery-2023 corpus dissolves that premise. Because all three are
**margin forms** — 2023 is reached as `level + HR × (fuel₂₀₂₃ − anchor)` — the corpus does not
merely enable re-derivation, it **tests the invariance claim itself**:

```
level₂₀₂₃ = measured_instrument₂₀₂₃ − HR × (fuel₂₀₂₃ − anchor)      vs      armed constant
```

## 1. Headline

| limb | constant | measured 2023 | level₂₀₂₃ | armed | Δ | band | Δ/band | coverage | **verdict** |
|---|---|---|---|---|---|---|---|---|---|
| **A** | `COAL_OFFER_MARGIN_LEVEL_BY_ISO` (ERCOT-137) | 18.380 | 17.5211 | 15.8807 | **+1.6404** | ±0.9300 | 1.76× | 0.9702 ✗ | **NOT-IDENTIFIABLE-2023** |
| **B** | `CC_COMMITTED_OFFER_LEVEL_BY_ISO` (ERCOT-139) | 13.390 | **10.6276** | 10.354 | **+0.2736** | ±0.6699 | **0.41×** | 0.95084 ✓ | **CONFIRMED** |
| **C** | `COAL_PEAK_OFFER_LEVEL_BY_ISO` (ERCOT-140) | **75.000** | 71.3378 | 35.1989 | **+36.139** | ±2.5062 | **14.4×** | 0.9702 ✗ | **NOT-IDENTIFIABLE-2023** |

All $/MWh; T1 = the gating matched window (h11–22 CST, all 365 delivery days).
`fuel₂₀₂₃`: gas **2.6012** $/MMBtu (ERCOT-138 §J basis, reconstructed) for B and C; coal
**1.8169** (ERCOT-137's own committed basis) for A.

## 2. Footing — the reconstruction IS the committed instrument

Before any 2023 number was taken, the harness was run over the four identification subsets on
`ercot123.load_sced`'s own frames: **8/8 subset-class reads reproduce the committed artifacts
exactly** — ERCOT-136 `bot_p50` (16.86 / 16.37 / 15.00 / 15.00 COAL; 9.83 / 10.35 / 17.39 / 18.73
CC), ERCOT-138 p90 (34.82 / 34.82 / 43.00 / 48.01 COAL), ERCOT-123 `curve_share` to 1e-6. The
three committed identifications also re-pool exactly from their own artifacts (15.8807 / 10.354 /
35.1989). Nothing here is a new construction: `scripts/lib/sced_corpus_instruments.py` imports
`ercot136._curve`/`._wq`, `ercot138.measured_curves` and `ercot123._decompose` verbatim and feeds
them delivery-year rows under the unchanged ercot-123/144 filters, CPT→CST at derivation.

**Fuel-basis footing gate (precommit §1c) PASSED.** ERCOT-138's own bundle is no longer on disk,
so the delivered-fuel basis was re-established by a no-LP keeper reconstruction that must
reproduce the committed §J values: CC **2.2129 / 3.2324** vs 2.213 / 3.232 and COAL **1.7481 /
1.6296** vs 1.748 / 1.630 — every |Δ| ≤ 0.0004 against a ±0.02 tolerance. The 2023 value is
therefore basis-consistent, and the precommit's basis-drift fallback was never invoked.

## 3. Limb B — CONFIRMED, and the extrapolation note is retired by verification

The gas-CC committed level is the one limb the corpus could both test and clear. Its measured
2023 curve bottom (13.390) minus the form's own measured fuel response
(`7.8521 × (2.6012 − 2.2494) = 2.7624`) lands at **10.6276** against the armed **10.354** —
inside the ±6.47 % band this constant is identified to, at 0.41 of it. The reading is stable:
full-day gives 10.7076 (+0.3536, still inside), and the raw-CPT clock sensitivity is ±$0.01.

**Consequence, exactly as pre-registered:** the extrapolation note is **RETIRED BY VERIFICATION**
in the `constants.py` block (its comment is the identification record) and in the matrix cell.
**No solve, no new mechanism, no new DOF, keeper unchanged.**

**Caveat carried, not buried.** The licensing margin is negligible: 2023 CC `curve_share` is
0.95084 against the 0.95054 floor (**+0.0003**), and the full-day window's 0.95051 sits 0.00003
*below* it. The confirmation is real under the pre-registered rule — the gate is the T1 statistic
and T1 passes — but this limb clears its coverage licence essentially at the boundary, and that
should be read alongside the verdict, not behind it.

## 4. Limbs A and C — the test could not be completed, and why that is itself the finding

Both COAL limbs fail the instrument's own licensing test (ERCOT-138 §3.4): delivery-2023
`curve_share` is **0.9702** (full-day 0.9794) against the **0.9876** floor the constants were
licensed on. The shortfall is not diffuse — it is located:

* **Martin Lake units 1–3** (~2.3 GW, `MLSES_UNIT1/2/3`) carry `curve_share` **0.757 / 0.761 /
  0.797**: roughly a quarter of their online intervals submit no incremental curve at all.
* It is **seasonal**: monthly COAL `curve_share` runs 0.907 / 0.937 / 0.907 / 0.917 across
  March–June 2023 against 0.995–1.000 in January and July–November.

Per the pre-registered rule the verdict is **withheld in both directions**. This is deliberate
and symmetric: a biased instrument can manufacture a false refutation exactly as easily as a
false confirmation, so the licensing gate is not lowered *against* the constants either. Both
extrapolation notes **stand**.

**The unlicensed readings are nevertheless the substantive result of this session**, and are
surfaced — not as verdicts, and not as a licence to arm anything (rule 13):

* **Limb A**: level₂₀₂₃ **17.5211**, +1.6404 vs the armed 15.8807 — **1.76×** its band.
* **Limb C**: the measured above-min-load p90 is **75.00 $/MWh**, flat at $75 in 9 of 12 months.
  This is fleet-wide conduct, not one plant: the two most common submitted **top** steps across
  delivery-2023 COAL are **$78.00** (21,677 intervals) and **$75.01** (17,869), with $34.82 — the
  2024/25 level — a distant tenth. level₂₀₂₃ **71.3378**, +36.14 vs the armed 35.1989 —
  **14.4×** its band, i.e. the armed constant is roughly half the measured 2023 top.

A 1.7 pp coverage shortfall cannot mechanically produce a 2× level shift. The direction
corroborates, at fleet scale and on an independent instrument, what **ercot-168 already measured
and promoted into the keeper**: 2023 ERCOT coal offer conduct differs structurally from 2024/25
(Oak Grove's measured overnight top $60.26 / $61.46). Limb C is the *top* of the same curve whose
*mid-band* item 12 re-identified per-year.

## 5. What is NOT claimed

* **No refutation is declared.** The pre-registered REFUTED branch was not reached for either
  COAL limb; the licensing gate fired first.
* **No arm is proposed and none may be built** on this record. The precommit's REFUTED
  consequence — a year-keyed 2023 block as a *named candidate arm* — is explicitly a separate
  owner adjudication, and this session did not reach the branch that would even name it.
* **No mechanism, no solve, no keeper change, no DOF added.** Nothing was tuned; no residual was
  consulted in either direction.
* **The coverage shortfall is not a defect to be "fixed" by relaxing the filter.** Martin Lake's
  no-curve intervals are that fleet's actual 2023 conduct (self-supply / price-taking), the same
  class of question ERCOT-123/135 adjudicated for the DAM.

## 6. Owner decision needed

How should the two COAL limbs' **2023 application** be treated, given that (a) their invariance
claim could not be licensed on 2023 rows, and (b) the unlicensed evidence points to a large,
one-directional, ercot-168-corroborated divergence? The options are the owner's to weigh, not
this session's to pick: leave both notes standing as declared extrapolations; charter a licensed
sub-population instrument for the 2023 COAL rows; or charter the year-keyed 2023 block that the
REFUTED branch would have named. **This session proposes none of them.**

Secondary, filed not acted on: the three margin constants have **no dedicated DOF-ledger entries**
in the keeper attestation (13 entries; the offer-surface mechanisms they belong to are covered,
these three identifications are not). They are zero-fitted-scalar measured mechanisms, so the gap
is bookkeeping rather than hidden freedom — the next ERCOT keeper-promoting session should add
them and carry limb B's verification into that keeper's ledger.

## 7. Artifacts and bookkeeping

* `docs/PRECOMMIT-ercot169-margin-fuel-invariance-2026-08-05.md` — pre-registered before measuring.
* `results/calibration/ercot169_margin_fuel_invariance.json` — the full record (harness fidelity,
  T1/T2/CPT windows, monthly paths, fuel basis + footing, per-limb verdicts, licensing diagnostic).
* `scripts/lib/sced_corpus_instruments.py` — the shared delivery-year instrument harness, the
  limb registry and the pre-registered verdict arithmetic.
* `scripts/probes/ercot169_margin_invariance_phase0.py` — the session probe.
* `--year` mode added to all three frozen derives (`derive_coal_offer_margin_anchor.py`,
  `derive_cc_committed_offer_margin.py`, `derive_coal_peak_offer_margin.py`); each reproduces its
  limb's verdict standalone. Rule-23 re-run cite: the ercot-157 delivery-2023 corpus landing.
* Matrix: §5.1 **item 13** stamped EXECUTED; all three mechanism rows' cells re-cited (verdicts
  unchanged at `K`); `scripts/check_mechanism_matrix.py` exit 0.
* **No run registered** — no solve was run, so rule 15 has no bundle to register.

## 8. DO-NOT-REDO honored

Per-year CT re-identification stays REFUSED (ERCOT-147, modal identity 11/160) — this lane was
not extended to CTs. Lignite offer SLOPE (ERCOT-143), `coal_min_load_floor` both grains, lignite
daily unit commitment, coal seasonal LEVEL split, `coal_offer_level_rebasis` (`R`),
`tranche_startup_amortization` (`G`) — untouched. ercot-168's **OPTION B** stays DEFERRED. The
ercot-167 SOC-reserve re-gate still waits on the H4-item-4 2024 maintenance-season availability
defect. §5.1 **item 11** (CC headroom/capability crosswalk) stays chartered and untouched.
