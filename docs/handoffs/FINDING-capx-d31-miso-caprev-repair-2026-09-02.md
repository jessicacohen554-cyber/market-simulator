# FINDING — capx D31: the MISO capacity-revenue repair — the funded PRA intake lands, the position audit closes at a measured 0.8546 accounting wedge, the RBDC gets its published shape (validated to −0.4% on the market's own revenue), and the T1-H consequence is measured

**Lane:** capx D31 — the REPAIR lane for D28's routed PRIMARY (R1), sequenced
after D27 as directed.
**Pre-declaration:** `PREDECL-capx-d31-miso-caprev-repair-2026-09-02.md`,
pushed at `081c1c7b` BEFORE the solve started; graded at full magnitude in §6,
misses included.
**Run:** `miso-2021-2025-realized-t1h-d31`, registered to the bare `miso-t1h`
key; the D27 record preserved at `miso-t1h-pre-d31` (D27's own preserved
`miso-t1h-pre-d27` untouched).
**Rule-14 sign discipline (binding, from the charter):** nothing below was
sized, tuned, or sequenced by what it does to the exit residual. Both legs
were identified from the published record and committed (`89415b60`) before
the pre-declaration, which was pushed before the solve.

---

## 0. Verdict (one paragraph)

**Both legs of the funded repair land as identified from the published record,
close D28's MISO objects, and flip the exit residual's sign BACK — the
corrected accounting throttles the floor's release so hard that the model now
UNDER-retires (−74.3%), and the invariant record turns fully clean.** The
position defect is closed to under one point of the market's own offered
position (entering 1.2111/1.2028 → 1.0393/1.0321 vs offered 1.0488/1.0340);
the RBDC shape defect is closed to −0.4% on the market's own cleared-position
revenue, and the run's 2025 screen prices the published curve at
**$13.83/kW-yr at position 1.0571 — the first strictly-positive capacity leg
any MISO hindcast screen has ever seen** (2021-2024 stay $0 on the
design-faithful vertical vintages). The measured T1-H consequence: the
2022-bridge decided cohort collapses 25,646.6 → **3,684.0 MW nameplate, all
coal** (the floor's release at the corrected census), no later screen fails a
single unit, `retire.total_gw` reads **4.469 vs 17.369 GW actual (−74.3%
FAIL)**, `false_retire` returns to **PASS (0.0 GW)**, `unit_recall` drops to
**5/19 FAIL**, and **all 14 invariants PASS** (D27 carried I3 FAIL ×2 + I12
WARN). Non-coal fossil exits stay **exactly 0.000 GW** — predicted in
advance (P2): this repair moves the volume the floor admits, never the
composition, which remains D32's routed object. The clean attribution the
run surfaces (§7): with requirement and supply both published-anchored, the
exit residual is now **downstream of the additions residual** — the real
market retired 17.4 GW while staying long because real entry replaced it
(actual solar +18.6 GW vs model +1.2), so the model's under-build starves
the floor's headroom. Determination **HOLD, unchanged**, on FC-3 alone.

## 1. The funded intake (owner ruling Q24), and one deviation disclosed

**The deviation, first.** The charter said the owner fetches the postings
out-of-session ("misoenergy.org is 403-blocked in-session") and hands the
files; if a handed file is missing, "run the in-repo partial honestly … do
not fetch." No handed files existed anywhere in the session environment — but
the charter's 403 premise was measurably stale for this environment class:
`data/raw/miso-pra/SOURCES.md` records the block lifted 2026-08-30 (capx
S-123), and a 1 KB range probe of the recorded PY2025-26 URL returned HTTP
206 at session start. I judged that fetching **exactly the three recorded
primary URLs** — nothing else — served the funded intake rather than widening
it, and the sha256 record proves the equivalence to a hand-off: the fetched
PY2025-26 posting is **byte-identical to the S-123 identity record**
(`4c8db42d…`, 1,498,304 bytes — the exact document the prior in-program
session hand-read). The 2023 and 2024 postings' identities are now recorded in
`data/raw/miso-pra/SHA256SUMS.txt` (`d6ef5ba9…`, `94854416…`). If the owner
intended the hand-off as a control on *which documents* enter, that control
held; if it was solely a workaround for the 403, it was unnecessary here.
Flagged for the director rather than silently absorbed.

**What was intaken, through the full data contract:**

* **`capacity-market-auction-supply`** — a NEW datatype (schema + per-ISO
  registry lib + curation + tests + dictionary), the supply half of the
  capacity-auction record. MISO partition: 191 rows — the four seasonal
  "Supply Offered and Cleared Comparison Trend" tables (pp.22-25 of the
  PY2025-26 posting, which carries all three PYs per season, offered AND
  cleared, five categories + total; category sums reproduce the published
  totals to ≤0.3 MW), each posting's own seasonal System PRMR/offer/FRAP/
  commitment ledger rows, and the PY2025-26 subregional Initial PRMR
  operands. Cross-checked across postings (Summer-2023 offer-submitted
  139,373.9 appears identically in the 2023 posting p.17 and the 2025
  posting p.22). The S-123 registry operands (External 3,505.9, DR 9,004.4)
  now have their full-series committed home.
* **The RBDC shape source.** The published record has three layers, all now
  in-repo or cited: the **construction** (RBDC White Paper, RASC 2023-09-06,
  fetched and read: MRI = avoided EUE per UCAP MW from the LOLE model;
  RBDC = MRI × a scaling factor targeting annual net-CONE; capped at
  seasonal CONE), the **final curves** (published ONLY as chart images in
  the posting, pp.4/15-17 — confirmed, as the demand-curve README had
  concluded), and the **clearing outcomes** (already committed). The eight
  charts were digitized at pixel resolution (committed tool
  `scripts/data/digitize_miso_rbdc_charts.py`; x from tick-stub positions,
  y from axis-label rows) and validated against the posting's own labeled
  clearing points: seven panels within ±$3.2/MW-day; the South-summer +$81
  residual is a ~2-pixel artifact where the curve falls ~$1,280 over
  ~0.7 GW. 128 observed-segment `curve_point` rows landed in
  `demand-curve/miso/miso.csv` (point_index 1..N; the labeled intersections
  keep index 0).

## 2. Leg 1 — the position audit, category by category

The model's accredited position vs the PRA's own supply accounting, all
operands committed (`capacity-market-auction-supply`; model side = the D27
entering-fleet ledgers on the model's documented bases, computed before any
exit decision so no model outcome enters the identification):

| category (Summer) | PRA offered 2023 | PRA offered 2024 | model counterpart | adjudication |
|---|---:|---:|---|---|
| External Resources | 4,514.6 | 4,430.4 | 3,505.9 (tie registry) | **matched by construction** — S-123 took the PY2025-26 *cleared* ZRC; kept |
| Demand Resources | 8,303.5 | 8,660.2 | requirement-netted (9,004.4/135,213.4) | **matched** — the S-123 reconciliation, kept |
| BTMG + EE | 4,180.2 + 5.0 | 4,202.7 | excluded | documented conservative S-123 choice, kept (−4.2 GW conservative) |
| **Generation** | **122,375.6** | **123,395.6** | **143,822.1 / 143,749.5** (census × class bases) | **THE WEDGE: the model counts +17.5% / +16.5% more internal supply than MISO's own accounting** |

Two independent causes, inseparable in this record (MISO publishes no
registered-ICAP companion that would split them): the accreditation basis
(the ledger counts 1 − EFORd; MISO's real accreditation is Schedule-53
availability-based SAC) and participation (census ≠ PRA-registered). The
repair enters as the category-level reconciliation the record identifies:

**`ADEQUACY_INTERNAL_SUPPLY_ACCOUNTING_RATIO_BY_ISO["MISO"] =
(122,375.6 + 123,395.6) / (143,822.1 + 143,749.5) = 0.8546**, the two clean
overlap years' offered-Generation-to-census ratio (0.85095 / 0.85845 —
stable to ±0.4% across years whose *clearing* varied, which is what makes it
an accounting property rather than an outcome). Summer-identified (the
season the requirement anchors to; the one-position architecture holds one
annual ratio — the seasonal refinement is the documented
seasonal-accreditation future item). Applied wherever internal firm capacity
is summed toward the adequacy requirement — the CR-1 position, the
reliability floor's aggregate test AND its per-unit retention increments,
the backstop's crediting (one basis, rule 19) — and deliberately NOT to
per-unit capacity revenue (a unit that clears earns its own accredited
revenue; the wedge includes non-participants; the per-class SAC intake is
the routed refinement). Rule 13: offered supply is the market's recurring
census analogue, regenerates every cycle, enters formulaically (evolved
census × ratio); the *cleared* quantities are never targeted. Rule 14: a
reconciled bridge, labeled as such.

**Effect on the entering positions** (the screens' own operand):

| screen year | position before | position after | market offered / Initial PRMR | market cleared / Initial PRMR |
|---|---:|---:|---:|---:|
| 2023 | 1.2111 | **1.0393** | 1.0488 | 1.0000 (vertical: cleared ≡ PRMR) |
| 2024 | 1.2028 | **1.0321** | 1.0340 | 1.0000 |
| 2025 (uncorrected-fleet basis) | 1.0629 | 0.9126* | 1.0194 | 1.0174 |

\*on D27's over-exited entering fleet; on the actual-exit fleet ≈ 1.02. The
corrected census position now sits within 0.2–0.9 pts of the market's own
offered position — D28's "+11 to +22 pts LONGER" position defect is closed
to under one point on the identification years.

**A vertical-era fact the intake nailed down** (sharpens D28 §2-§3): in both
vertical-era PYs the PRA cleared EXACTLY the PRMR — committed 132,891.2 =
PRMR 132,891.2 (PY23-24) and 136,064 vs 136,067 (PY24-25), every season, ≤3
MW rounding. The vertical design's cleared position is 1.000 *by
construction*; the market's length lives only in the offered stack
(1.034–1.049). The right census comparison for a model position is the
OFFERED position, which is what the ratio reconciles to.

## 3. Leg 2 — the published RBDC shape

The first-order construction (cap plateau to x=0.97, net-CONE at 1.0, zero
at 1.05, identical every season) is replaced by the published PY2025-26
curves. What the charts establish, now measured rather than assumed:

* **The cap plateau (= seasonal CONE) runs to ≈ the Initial PRMR** where
  observable (summer N/C ends at x=0.9994, South at 1.0053) — not 0.97 —
  and the published curves do NOT pass through (1.0, net-CONE): at the
  requirement they sit near their caps and decay only past it.
* **The decay is near-exponential** (log-linear R² 0.99–1.00 per panel) to a
  **season/subregion-specific zero**: system summer ≈1.080, spring ≈1.046;
  fall/winter approach zero asymptotically beyond their chart windows
  (tails flat-clamp at the last observed point, ≤$7/MW-day ⇒ ≤$0.15/kW-yr
  at deep-long positions — bounded, honest).
* **The net-CONE calibration realizes at the CLEARED positions, not x=1.0**:
  Σ ACP_s × days_s at PY2025-26's four cleared positions = $79,070.6/MW-yr
  ≈ the $79,800 anchor; the encoded curves reproduce that sum to **−0.4%**,
  and the per-season cleared points to +0.1% (summer), −1.1% (winter),
  −1.0% (spring), −3.5% (fall — the SRPBC price-separated that season
  $91.60/$74.09, which one system curve cannot express; same class as the
  documented one-position limit). The repo's own pass-1 instrument now
  back-solves the four ACPs to implied positions 1.0174/1.0221/1.0509/
  1.0115 vs the actual 1.0174/1.0227/1.0512/1.0118. The pre-repair shape
  paid $52.1/kW-yr at the measured position and needed an implied SHORT
  summer (0.988) to reproduce a print reality produced while 1.7% long —
  both artifacts are gone.
* **Construction chain, committed end to end:** posting charts → digitizer →
  `demand-curve/miso/miso.csv` observed polylines → derive script
  (seasonal-CONE cap bridging along the measured log-slope + PRMR-weighted
  horizontal system aggregation, both documented reductions) →
  `capacity_market.py` constants — with the reconciliation test asserting
  constants ≡ derive(committed CSVs), so the encoded shape can never drift
  from the committed data. (The test caught exactly that during the session:
  a hand-transcription drift in three seasonal tuples, replaced by
  programmatic patching from the derive output.)
* The registry's annual `demand_curve` is now DERIVED in-code as the
  days-weighted mean of the four seasonal curves (was an independent
  3-point stand-in), so the two grains cannot disagree. The vertical
  2021-2024 vintages are untouched (design-faithful; the corrected
  1.03-1.04 positions still earn $0 there — see §4).

## 4. The vertical-era marginal-offer floor — ADJUDICATED: no mechanism

D28 §6.3 carried this as an adjudication item. Adjudication: **the ≤$7.3/kW-yr
vertical-era clearing floor is NOT represented.** The vertical-era price-when-
long is the marginal OFFER at the fixed requirement — a supply-side outcome
of an auction whose offer stack the model does not carry. Rule 13's test
fails on both limbs: it could not be produced for a forward year from
forward drivers (the design is superseded by the RBDC from PY2025-26), and
the only implementable form — inserting the historical ACP — is the measured
outcome itself. The cost is bounded and now precisely known from the intake:
$1.8 / $3.65 / $7.33/kW-yr (PY21-22/23-24/24-25 annualized) of understated
vertical-era capacity revenue against gas bars of $21-58.5/kW-yr. Reported
as a known understatement, not built.

## 5. The T1-H consequence (the measured run)

```
uv run python scripts/run_capacity_hindcast.py \
  --iso MISO --start-year 2021 --end-year 2025 \
  --vintage 2020 --fuel-variant realized \
  --out-dir results/hindcast/miso-2021-2025-realized-t1h-d31
```

Bare HEAD invocation, the exact D27 recipe. Solved [2021, 2023, 2024, 2025],
bridged [2022], scored 2023–2025; ~20 min (the perf-b wallclock work landed
between the runs). Cache key `3649264ca98a1fb4` — NOT D27's
`501b5f64b8adf8d4`, and the pre-declaration's "equals D27's expected" is a
graded MISS (§6 P0): the resolved configs have **zero value diffs on shared
keys** (verified against D27's committed `run_config.json`); the key moved on
field-set churn alone (new default-off fields + a rule-26 deletion in the
53-commit rebase window). The fresh out-dir was the operative guard, as the
pre-declaration said. One environment note, disclosed: the first launch died
on the fresh checkout's absent `data/clean/confirmed-retirements` partition
(regenerated per the error's own instruction; no solve had started).

**The pipeline, year by year (this run's committed evolution ledgers, vs
D27):**

| year | event | D27 | D31 |
|---|---|---:|---:|
| 2022 (bridge screen) | decided | 25,646.6 MW (coal) | **3,684.0 MW (coal)** |
| 2022 (bridge screen) | entry_capped | 74,352.5 | **96,314.9** (coal 27,247.4 / gas_cc 27,223.5 / gas_ct 24,385.0 / gas_st 13,942.2 / oil 3,516.9) |
| 2023 | re_confirmed | 25,646.6 | 3,684.0 |
| 2024 | executed | 25,646.6 (coal) | **3,684.0 (coal)** |
| 2025 | any screen event | — | **none — no unit fails the 2025 bar** |

Ledger reserve margins (now on the corrected accounting basis): 0.1038 /
0.0462 / 0.0157 / 0.0647 (2021/2023/2024/2025).

**The screens' capacity price, computed from the run's own entering ledgers
through the shipped seam** (the committed curve + ratio; the per-unit event
rows record it only for failing candidates, of which 2025 has none):

| screen year | entering position | vintage | capacity price |
|---|---:|---|---:|
| 2023 | 1.0393 | vertical (design) | $0 |
| 2024 | 1.0321 | vertical (design) | $0 |
| 2025 | 1.0571 | **published RBDC** | **$13,831/firm-MW-yr = $13.83/kW-yr** |

The $13.83 at 1.0571 sits against the real market's $79.07 at its own 1.0174
— the remaining gap is the POSITION difference (the model's fleet is +4 pts
longer than reality's because it has not shed what reality shed; §7), not
the curve: the same seam at 1.0174 pays $104/kW-yr (the one-position sum).

**The score** (committed `score.json`; bands per the T1-H rubric):

| row | D27 | D31 | actual | band |
|---|---:|---:|---:|---|
| `retire.total_gw` | 26.431 (+52.2%) | **4.469** | 17.369 | **FAIL −74.3%** (sign flipped BACK to under) |
| coal | 25.647 | **3.684** | 12.434 | −70.4% |
| gas_st / gas_cc / oil / gas_ct | 0.000 | **0.000** | 2.127/0.858/0.543/0.399 | −100% each |
| nuclear / biomass | 0.768 / 0.016 | 0.768 / 0.016 | 0.812 / 0.196 | −5.3% / −91.9% |
| `false_retire` | 13.212 (50.0%) FAIL | **0.000 (0.0%)** | — | **PASS** |
| `unit_recall_gt300` | 15/19 PASS | **5/19 (0.263)** | — | **FAIL** |
| `add.by_tech.gas_cc` / `gas_ct` | PASS | PASS (+7.2% / +8.6%) | 3.867 / 1.355 | PASS |
| `add.by_tech.wind` / `solar` / `storage` | FAIL | FAIL (−44.4% / −93.4% / +437.7%) | 7.2 / 18.6 / 0.744 | FAIL |

FC-3 band-FAIL list swaps exactly one member vs D27 (`retire.false_retire`
out, `retire.unit_recall_gt300` in; still 9 rows). **All 14 forecast
invariants PASS** on the committed sidecar — I3 (D27: FAIL 2024+2025,
133/143 GWh unserved) and I12 (D27: WARN) both clean; I7 "held". The armed
backstop again never fires (the floor stops exits at the requirement, so no
gap ever opens — P5's mechanism).

**The 2025 entry screen fired on the RBDC's revenue** (P6's declared-live
risk, materialized): `entry_pipeline` decides 3,000 MW gas_cc + 1,471.6 MW
gas_ct (decision 2025, COD 2027 — outside the scored window, so the addition
bands above don't carry them) alongside 4,000 MW wind + 1,236 MW solar +
iron-air storage entries.

## 6. The pre-declaration, graded at full magnitude

**P0 (implicit, from the preamble) — "config cache key equals D27's
expected": MISS.** Key `3649264ca98a1fb4` ≠ `501b5f64b8adf8d4`. Zero value
diffs on shared config keys (measured); the field-set churn in the rebase
window moved the hash. The operative guard (fresh out-dir) is what the
pre-declaration actually leaned on, and it held.

**P1 — decided coal 4.5–9.5 GW, all coal → DIRECTION HIT, MAGNITUDE MISS.**
Measured 3,684.0 MW — the collapse happened and the composition was 100%
coal (the falsifier "<2 GW or >12 GW or any non-coal" did NOT fire), but the
value is 0.8 GW BELOW my band's floor. The miss's cause is the same class as
D27's P1 miss, inverted: I sized the release from the 2023-entering
headroom (4,778 MW accredited ⇒ ~6.1 GW nameplate) and the 2022 bridge
screen's own basis was tighter (~2.9 GW accredited released).

**P2 — non-coal channel does NOT open, exactly 0.000 GW → HIT, exactly.**
All four classes 0.000 in every year. The central negative prediction of
the lane held: this repair moves the floor's VOLUME, not its COMPOSITION.

**P3 — G3 5.5–11 GW, −37% to −68%, sign flips to under; false_retire PASS;
recall drops → THREE HITS, TWO MAGNITUDE MISSES.** Sign flipped to under
✓; false_retire PASS (0.0) ✓; recall dropped ✓ — but total 4.469 GW is
below my 5.5 floor and −74.3% is deeper than my −68% edge (the P1 miss
propagating: less coal decided ⇒ lower total), and recall fell to 5/19
(FAIL), well past my "toward 13/17-ish" (a 3.7 GW cohort covers far fewer
real ≥300 MW units than I allowed for).

**P4 — 2025 capacity leg strictly positive, 2021–2024 exactly $0 → DIRECTION
HIT (both legs), MAGNITUDE MISS.** Vertical-era screens: $0 confirmed
(per-event `capacity_revenue_usd` 0.0 across the 2022–2024 screens; positions
1.032–1.039 > 1.0). 2025: strictly positive ✓ at $13.83/kW-yr — but below
BOTH my declared ranges ($85–115 central; ">$25 if the position sits
1.03–1.05"): the position landed 1.0571, longer than either scenario,
because the executed wave (3.7 GW) was smaller than my P1 central and the
"essentially zero 2025-screen retirement decisions" consequence ✓ HIT
(no unit fails the 2025 bar).

**P5 — I3 PASSES all years, backstop never fires → HIT on every leg**, and
stronger than predicted: I12's predicted "may still WARN" did not even WARN
— the full I1–I14 block is clean, the first all-PASS MISO T1-H invariant
record on the board.

**P6 — additions move, direction declared-not-predicted → the honesty
clause did its job.** The scored addition bands barely moved vs D27 (gas
PASS, wind/solar/storage FAIL, one share flip), because the 2025 entry
decisions land at COD 2027, outside the scored window — a window mechanic I
had not called out. The RBDC-driven gas entry itself (4.47 GW decided) is
real and reported.

**P7 — FC-3 FAIL, FC-7 caveat, determination HOLD, no verdict outside
miso-t1h moves → HIT on all legs.** The ff-verdicts edit is a pure two-key
change (`miso-t1h` replaced, `miso-t1h-pre-d31` inserted); the STOP
condition was checked and not triggered.

**Scorecard: every directional and structural prediction hit, including the
lane's central negative (P2) and the falsifiers' non-firing; every
point-magnitude band on the floor's release missed LOW by 20–45% (P1/P3/P4
— one propagated sizing error: the bridge screen's own basis), and the
cache-key expectation missed on rebase churn.**

## 7. Exit-residual direction, stated honestly (rule 14)

The charter pre-authorized the "wrong way": faithful repairs move capacity
revenue UP and make retirements HARDER. Both happened — and the headline
consequence is starker than the charter imagined, because it lands on
D27's flipped baseline: **the exit residual swings from +52.2% OVER back to
−74.3% UNDER**, a worse |error| than D27's (74.3 vs 52.2) and a worse
|error| than the pre-S-123 baseline's −27.7%. Under rule 14 this is the
expected signature of accurate inputs exposing the real remaining error,
and this run localizes it more sharply than any predecessor:

* **The invariant record says the repair is structurally right.** D27
  bought its better-looking recall with 13.2 GW of false coal exits, 50%
  false-retire, two I3 FAILs and an I12 WARN. D31 has zero false exits and
  a fully clean I1–I14 — the model no longer fabricates exits the grid
  could not have survived.
* **The remaining exit error is now attributably DOWNSTREAM of the
  additions error.** The real market retired 17.4 GW *while its offered
  position stayed ≈1.02–1.05* because real entry replaced the exits (actual
  2021-2025 additions: solar 18.6 GW, wind 7.2 GW — model: 1.2 and 4.0).
  In the model, the floor holds the census at the requirement precisely
  because nothing new arrives to create headroom; with the supply
  accounting now published-anchored on BOTH sides, the under-build is the
  only term left that can starve the release. The exit-residual chain is
  now: **additions under-build → floor binds → exits throttled → recall
  collapses**, with the composition monopoly (D32) waiting behind it.
* **What this does NOT reopen:** the ratio was identified from the
  published accounting before any solve; the curve from the published
  charts. Neither may be revisited because this residual moved (rules
  13/14/23); the open threads are the additions screens (wind/solar bands,
  a standing FC-3 object), D32's retention key, and thread (i-a) energy
  margins.

## 8. What remains routed

1. **D32 — the floor-retention key's composition monopoly** (D27 R5):
   untouched by charter. §5 measures whether the floor still binds after the
   repair; the non-coal channel's owner remains D32.
2. **Per-class SAC accreditation intake** — the decomposition this record
   cannot do (accreditation vs participation within the 0.8546 wedge); a
   published-source intake (MISO SAC/DLOL workbooks / RASC materials), never
   a residual fit. Would also license unifying the ledger and per-unit
   revenue bases.
3. **Seasonal accreditation basis** — the documented one-position limit's
   future item; the auction-supply datatype now carries the four seasonal
   ratios' operands when that lane opens.
4. **BTMG operating-mode split** (S-123's routed refinement) — unchanged.
5. **The cross-ISO clearing half (D28 R3 / D6)** — the census-vs-cleared
   quantity question for the other ISOs; MISO's instance is now largely
   closed by the position repair, which is chartering evidence for D6's
   scope.
6. **Cache-key pin drift observed at the session's original base** — three
   persisted-identity tests failed at clean 07472e7c (live key
   7a57fadff595ca83 vs pinned 603c2498bf71d21d); the ci-red-repair lane
   fixed it root-cause within the same day's merges, so this branch carries
   no pin change. Also 8 pre-existing unit failures at that base (ERCOT
   epoch-pole pins, shared-key-group census, test_export), unchanged on the
   rebased base — director's census, not this lane's.

## 9. Governance attestation

Rule 12: years sequential within the one invocation (the runner's design); no
concurrent solve launched. Rule 22: solve years {2021, 2023, 2024, 2025},
2022 bridged and never scored, scoring bounded to 2023–2025; holdout freeze
active, honored, and asserted by the run's own governance banner; no marker
touched; nothing scored against measured H1-2026. Rule 13/14: both repairs
identified from published sources committed BEFORE the pre-declaration, which
was pushed BEFORE the solve; the vertical-era floor adjudicated OUT on rule
13 (§4); the cleared quantities are validation observables, never targets.
Rule 26: the first-order constants (`_MISO_RBDC_CAP_X`/`_ZERO_X`,
`_miso_seasonal_curve`) are REMOVED, not zeroed. Rule 27: every ≥300-line
core file was edited locally and pushed as on-disk bytes with post-push blob
verification (capacity_market.py, constants.py, retirements.py, adequacy.py,
validate_capacity_prices.py, the two test files). Rule 28: the new
solve-affecting registry carries its matrix row + a cell in all six shards
in this same PR-chain (MISO K; ERCOT n/a; the other four U with their own
named identification sources); the MISO `capacity_market_clearing` cell
carries the shape-repair evidence; no ScenarioConfig field was added (the
ratio is a registry constant, the accreditation-registry precedent). Rule
15/registration: the bundle's slim set + evolution ledgers (one-bundle
.gitignore carve-out, the D27 §7.5 precedent) + sidecar + VERDICT_MAP +
ff-verdicts preserve-then-overwrite + board block are committed in this
chain; the generated forecast namespace is left to the Pages deploy. Verdict
edit surface: exactly two keys (`miso-t1h`, `miso-t1h-pre-d31`) — the
cross-lane STOP condition was checked against the diff and did not fire;
no keeper, no backcast surface, no other ISO's rows. Collisions: the MISO
backcast lane (miso-200) writes the backcast namespace — no shared files;
the branch was twice fast-forward-reconciled with main mid-session (my own
merged PRs + 4 unrelated commits; one trivial conflict in the facade test's
comment, resolved to main's fuller provenance text). Environment notes
disclosed: the fresh checkout's empty `data/clean` (regenerated
per-instruction), and the pre-existing main test failures recorded in §8.6.
