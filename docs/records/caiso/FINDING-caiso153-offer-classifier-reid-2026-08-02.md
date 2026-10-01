# FINDING — caiso-153: the CAISO gas-coupling classifier IS re-identifiable. The defect is the ESTIMATOR, not the body probe; all four frozen gates PASS, reproducibility is restored, and the re-derived surface is PROMOTED as the CAISO keeper

Lever: **mechanism-matrix §5.2 item 9** — opened NEW, BLOCKING and unowned at
caiso-152. Prerequisite, not a price lever.

Pre-registration: `PREREG-caiso153-offer-classifier-reid-2026-08-01.md`,
committed and pushed **before any classifier value on this session's corpus
existed**. No addendum was needed: no registered input changed mid-session.

Instrument: `scripts/probes/_caiso153_offer_classifier_reid.py`
(`curate` / `diagnose` / `derive`). Outputs
`results/calibration/caiso153_classifier_reid.json`,
`caiso153_classifier_slopes.csv`, `caiso153_P035_TS/`,
`caiso153_shipped_verify/`.

**Keeper CHANGED**: `2026-07-31-caiso-151-firm-selfsched` →
**`2026-07-31-caiso153-reid-b`**, CALIBRATED-WITH-CAVEATS, 0 FAILs, C1 12/12 ·
free 8/8, the same 2 of 3 ledgered non-protective slots, protective 0/1.

---

## §A — the corpus, exactly as registered

The full contiguous 2023–2025 span, **1,095 trade days** (364/366/365 —
2023-06-01 is the documented OASIS archive hole), fetched by
`fetch_caiso_public_bids.py` with no arguments and curated one year per
invocation under the corrected (HEAD, post-caiso-152) RLE-expanding parser:
**66,985,503 GENERATOR EN curve rows**, 50,164,548 at cap ≥ 20 MW, 694
resources. This is `FINDING-caiso152` §D's measured corpus requirement; the
caiso-151 balanced sample was not used and is not reopened.

## §B — the diagnosis: attenuation, and it is the ESTIMATOR

`FINDING-caiso152` §I's lead was the body-price probe. **It is refuted**, in
two independent steps.

First, before pre-registration, a throwaway raw-CSV measurement (12 trade days,
no classifier) found `_price_at_frac` falls back to the first step on only
**8.5 %** of curve-hours, and those curves are near-flat (first/top price ratio
median 0.995). The min-load-block form of the lead cannot carry the effect.
This was disclosed in PREREG §2 as a partial refutation, and the grid was given
a second axis precisely because it settled nothing about the alternative.

Second, the grid itself. Across the frozen 3×3 (PREREG §4), **the body axis
barely matters and the estimator axis carries everything**:

| estimator | body probe | implied non-fuel adder \|L\| | admissible? | slope p25/p50/p75 | split-half instability |
|---|---|---|---|---|---|
| **OLS** | P035 (incumbent) | **$37.48** | **NO** | 4.86 / 6.07 / 7.91 | 0.586 |
| **OLS** | BAND | **$34.77** | **NO** | 4.71 / 5.95 / 7.38 | 0.597 |
| **OLS** | P060 | **$32.68** | **NO** | 4.71 / 5.95 / 7.46 | 0.592 |
| **TS** | **P035** | $11.71 | yes | 7.49 / **10.03** / 11.36 | **0.109 ← winner** |
| TS | BAND | $12.65 | yes | 7.07 / 9.20 / 11.15 | 0.186 |
| TS | P060 | $10.07 | yes | 7.23 / 9.79 / 11.19 | 0.155 |
| TRIM | P035 | $10.13 | yes | 7.59 / 10.30 / 12.19 | 0.286 |
| TRIM | BAND | $11.03 | yes | 7.16 / 10.11 / 12.14 | 0.272 |
| TRIM | P060 | $9.63 | yes | 7.45 / 10.39 / 12.17 | 0.326 |

Changing the body probe under OLS moves the adder by $4.8 and leaves every cell
inadmissible. Changing the estimator under **the same** body probe moves it by
$25.8 and flips admissibility. The mechanism is regression leverage: the
CA-composite citygate reaches **$24.29/MMBtu** in January 2023 against a
2023–25 median near $3–4, so a pooled OLS slope is levered on a few days of one
month of one year, and every resource that did not track that spike
proportionally — a different CA hub, a monthly index, a cost-verified DEB on a
lagged index — is attenuated toward zero **with its correlation intact**. That
is exactly caiso-152 §I's reported signature. The physically-impossible
population (`r ≥ 0.6`, slope < 4 MMBtu/MWh) falls from **32 resources /
10,880 MW under OLS to 13 / 2,692 MW under Theil-Sen**.

**Winner by the frozen rule: `P035_TS`** — admissible at $11.71 with the lowest
split-half instability (0.109). It keeps the **incumbent** body probe and
changes only the slope estimator, so the shipped diff in
`derive_caiso_offer_surface.py` is one line plus its citation.

## §C — the frozen gates, unmoved, all PASS

`hr_cut` stayed 8.5 and G1–G4 were not relaxed, re-centred or re-scoped
(rule 23 `[R-FROZEN-DERIVE]`; `FINDING-caiso152` §H). The **unmodified**
deriver, run on the re-identified classifier:

| gate | incumbent (OLS) | caiso-153 (TS) |
|---|---|---|
| G1 CC_REGULAR | 12,007 MW, ratio 0.876 PASS | 11,935 MW, ratio **0.871 PASS** |
| G1 CT_PEAKER | 1,786 MW, ratio **0.235 FAIL** | 9,950 MW, ratio **1.306 PASS** |
| G2 cut ±0.25 | — | **PASS** |
| G3 estimation LOYO | — | **PASS**, all six consumed stats, every held-out year |
| G4 physical sanity | — | **PASS** |

`GATES ALL PASS`, so the deriver writes the consumed JSONs on its own terms.
This is PREREG §6 branch **(c)**.

## §D — two corroborations the selection rule never saw

The selection rule is blind to G1 and to the committed artifact by
construction, which makes both of the following genuine out-of-sample checks.

**1. The re-derived static bands reproduce the COMMITTED artifact.**

| class | band | committed | caiso-153 | Δ | tol |
|---|---|---|---|---|---|
| CC_REGULAR | econ_low | 1.051 | 1.066 | +0.015 | 0.105 |
| CC_REGULAR | econ_high | 1.053 | 1.072 | +0.019 | 0.105 |
| CC_REGULAR | peak | 1.333 | 1.386 | +0.053 | 0.133 |
| CT_PEAKER | econ_low | 1.147 | 1.145 | −0.002 | 0.115 |
| CT_PEAKER | econ_high | 1.182 | 1.166 | −0.016 | 0.118 |
| CT_PEAKER | peak | 1.176 | 1.166 | −0.010 | 0.118 |

Every band lands inside tolerance, and G1 lands at 0.871/1.306 against the
recorded 0.981/1.416. **This explains `FINDING-caiso152` §F**: the committed
artifact was derived with a correctly-identified classifier, and the deriver
drifted to the attenuated OLS form in the eleven days before the repo's git
history begins. §F's gap was never a corpus mystery — it was this estimator.

**2. The SHIPPED deriver regenerates the promoted artifact exactly.** Run
unpatched against the same clean tree, the consumed content of both JSONs and
all four gate blocks are **identical** (only `derived_utc` differs).
`caiso_offer_curve_measured.json` and `caiso_offer_surface_condbinned.json` are
reproducible from their own script and corpus again — the defect §F recorded is
closed.

## §E — the A/B, and what it costs

Two arms, same HEAD, solved **sequentially** with the artifacts swapped between
them and **both files hashed per arm** (the static half has no path-override
field). `legitimacy_diagnostics.json` generated for both.

* control A — `2026-07-31-caiso153-control`, committed artifacts in place, a
  same-HEAD **zero-delta control**. Committed keeper bytes were not the control.
* arm B — `2026-07-31-caiso153-reid-b`, re-derived artifacts.

**The input change, in the LP:** the CC_REGULAR ladder rises **+0.451 to
+0.688** per net-load bin and the CT_PEAKER ladder falls **−0.317 to −0.370**.
These largely offset, so system prices move only **+0.17/+0.22/+0.17 $/MWh**.

**Every criterion verdict is UNCHANGED** — against the control and against the
caiso-151 keeper:

| criterion | caiso-151 keeper | caiso-153 arm B |
|---|---|---|
| C1 fuel-mix | PASS | PASS |
| C2 system volume | PASS | PASS |
| C3a mean LMP | CAVEAT | CAVEAT |
| C3b price shape | PASS | PASS |
| C3c price tail | CAVEAT | CAVEAT |
| C4 dispatch corr | PASS | PASS |
| C6 governance | PASS | PASS |
| **C7 diurnal shape** | **PASS** | **PASS** |
| **C8 forced share** | **PASS** | **PASS** |

0 FAILs, C1 12/12 · free 8/8, 2 of 3 ledgered slots, protective 0/1 — identical.

**The cost, stated not buried.** DA price MAE rises **+0.052/+0.060/+0.043
$/MWh** (2023/24/25) on a $12.998/$8.696/$7.093 base — 0.4–0.7 % relative. RT
MAE +0.088/+0.102/+0.093. DA correlation −0.002/−0.002/+0.001. C3a-2025 grows
**+9.42 → +9.92 %, i.e. +0.50 pp** on a load-weighted system basis, reported
explicitly against the caiso-145 ledgered caveat as PREREG §7 required, and
below the 1.0 pp trigger its caiso-151 predecessor fixed. C3c is
**bit-identical** across arms (0 h > $200 in every year; maxima $188/$149/$74).

Rule 1 `[R-STRUCT]` and rule 14 `[R-ACCURATE]` govern: an accurate measured
input stays in when the fit worsens, and the worse fit is a discovered cost to
name — never a reason to revert to an input that cannot be regenerated from its
own script. Equally, rule 1 forbids adopting it *because* a residual moved: it
is adopted because the incumbent classifier assigned **16,329 MW** of
gas-coupled capacity a marginal heat rate below 4 MMBtu/MWh, which no thermal
unit can have.

## §F — disposition

- **PROMOTED.** Keeper `2026-07-31-caiso-151-firm-selfsched` →
  `2026-07-31-caiso153-reid-b`. `keepers/CAISO.json` updated,
  `build_status.py --iso CAISO` rebuilt, attestation + DOF ledger written.
- **The measured offer surface gains its first DOF ledger entry**,
  identification `measured`. It was armed from caiso-51 onward with **no entry
  at all** — a real gap this session closes, with its `root_cause` recording
  §F's reproducibility defect as CLOSED.
- **caiso-152's parse correction now ships**, carried by this keeper. It was
  blocked solely on the derive refusing to write; the refusal was correct and
  the block is now lifted by fixing the identification, not the gate.
- **Both arms registered** (rule 15). No gate threshold, no `hr_cut`, no
  `ScenarioConfig` field changed — the promoted arm is flag-identical to the
  control.
- **CAISO still holds no rule-22 calibration-complete marker.** 2023/2024/2025
  only; no out-of-training year touched; **no marker written**.

## §G — DO-NOT-REDO (new, binding)

* **Re-testing the BODY PROBE as the cause of the CT-bucket collapse.** §B
  settles it on the full corpus across all three estimators: the body axis
  moves the adder $4.8 and flips nothing; the estimator axis moves it $25.8 and
  flips everything. `BODY_FRAC` stays 0.35. A body-probe proposal needs new
  evidence about *curve geometry*, not a re-run of this grid.
* **Re-running the estimator grid to pick a different cell.** The rule was
  frozen ex ante and applied once; `P035_TS` won on out-of-sample stability
  among admissible cells. Re-ranking with a different metric, or dropping
  admissibility so a lower-instability inadmissible cell wins, is answer-key
  selection.
* **Moving `hr_cut` off 8.5 on the strength of the re-identified slope
  density.** Explicitly out of scope and NOT examined here. G2 (cut ±0.25)
  PASSES, which is the frozen test for whether 8.5 is still right. Moving it is
  a separate owner-visible act.
* **Re-deriving either half against the price residual to recover the +0.05
  $/MWh MAE.** The cost is recorded in the keeper's disposition note; it is not
  a defect to tune away. Carried unchanged from `FINDING-caiso152` §H.
* **Quoting the OLS arm's absolute band or ladder levels as measured CAISO
  conduct.** All three OLS cells are physically inadmissible; only the
  OLD-vs-NEW difference and the admissibility verdict are results.
* **Treating §D's reproduction of the committed bands as licence to chase
  committed values.** It is a blind corroboration of an independently-selected
  estimator, not a target that was aimed at, and it must never become one.
* Carried forward unchanged: `FINDING-caiso152` §H (except its §I lead, which
  §B here refutes on measurement), `FINDING-caiso151` §H, `FINDING-caiso150`
  §H, `FINDING-caiso149` §G, `FINDING-caiso148` §G, `FINDING-caiso147` §G,
  `FINDING-caiso146` §G, `FINDING-caiso144` §G, caiso-143 §I, caiso-142 §H,
  caiso-141, caiso-138 §G, caiso-137b §6, caiso-131 §10.

## §H — carried open items and cross-ISO notes

* **The `dam-public-bids` corpus is gitignored and dies with the container.**
  `fetch_caiso_public_bids.py` with no arguments regenerates it in ~3 h at
  ~6.7 s/day. Background processes do NOT survive session idle in this
  environment — the fetch was reaped mid-run and had to be resumed in
  foreground chunks. A successor re-deriving this surface should budget for
  that.
* **Cross-ISO:** the Theil-Sen change is inside
  `derive_caiso_offer_surface.py` and touches CAISO only (rule 25
  `[R-ISO-SCOPE]`). But the *failure mode* — a per-resource daily fuel
  regression whose slope is levered on one gas spike — is generic to any ISO
  whose offer surface is identified the same way, and the PJM/NEISO derives use
  the same family. **Not tested here and not claimed**; flagged for their lanes.
* **The mechanism-matrix §5.2 item 9 blocker is CLEARED.** Item 3 (the S2
  DA/RT two-settlement charter) is now CAISO's only live queue item.
* Unchanged carried items: the caiso-151 §F diagnostics-harness plant-set
  defect (D-1/D-2/D-4 drop intertie tranches; ISO-generic, hides MISO Manitoba
  and NYISO HQ too); the shared CT heat-rate sub-6.0 MMBtu/MWh meter bug (four
  ISOs); the latent CHP derive defect in PJM; the caiso-148 Diablo
  nameplate/uprate basis mismatch; `compute_monthly_markup`'s unconditional
  committed-tranche start amortization (six ISOs); CT_CHP's thin CAISO
  coverage; `audit_keepers.py`'s missing E7 staleness check.
* **Two pre-existing test failures**, reproduced on clean `origin/main` at
  caiso-152 and not attributable to this session:
  `test_clean_io.py::TestRegenerateEntrypoint::test_datatype_list_matches_schemas`
  and `test_consume_phase3d.py::EgridZoneAssignmentParity::test_zone_lookup_matches_raw`.

Next number: caiso-154.
