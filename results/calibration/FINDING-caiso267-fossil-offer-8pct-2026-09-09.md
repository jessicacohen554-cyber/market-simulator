# FINDING — caiso-267: the owner-directed **fossil offer bands × 0.92** halves the price-level error (C3a mean |gap| **7.17 % → 2.82 %**) and breaks exactly one thing: **C4-2025 gas NRMSE 0.298 → 0.308**, 0.008 over its bound, in the one year of three where the criterion was already on the edge — while *improving* it in the other two. C3c is a ledgered caveat by owner ruling. Determination **NOT-YET on C4-2025 alone**. The factor is NOT resized. Promotion is the owner's call.

**Session caiso-267, 2026-09-09**, branch `claude/busy-volta-u6dlvt`.
Pre-registered in `PRECOMMIT-caiso267-belly-conduct-measured-2026-09-09.md` and
`ADDENDUM-caiso267-fossil-offer-8pct-2026-09-09.md` (+ its §D.1 correction), all
**pushed before the first LP**.

Run **`2026-09-09-caiso-267-fossil92`** (bundle `caiso267_fossil92`), full span
**2023–2025 in ONE invocation** (rule 16 `[R-ALLYEARS]`), registered per rule 15
`[R-DASHBOARD]` as the rejection it currently scores as.
**KEEPER UNCHANGED at `2026-09-06-caiso-260-b1-demand`** — no keeper shard was
edited, no `calibration-complete.json` entry was re-keyed.

---

## §1 — The result, in five lines

1. **The cut works on price level.** C3a **+4.38 / +8.89 / +8.25 %** →
   **−0.87 / +4.33 / +3.25 %**; mean |gap| **7.17 % → 2.82 %**. Zero dump and
   zero slack in every year.
2. **It erases the model's 2023 scarcity tail.** C3c-2023 goes from model
   **23 h** vs actual 47 h > $200 to model **0 h**. A uniform offer cut removes
   exactly the hours that were clearing highest. **OWNER RULING 2026-09-09,
   verbatim: *"C3c is an acceptable caveat."*** It is therefore ledgered
   (2023 + 2024, one criterion, one slot) and reported at full magnitude, not
   erased.
3. **C4 is the only thing that breaks, and it breaks by 0.008 in one year of
   three — while improving in the other two.** Gas hourly NRMSE
   2023 **0.287 → 0.275**, 2024 **0.260 → 0.254**, 2025 **0.298 → 0.308**
   against a ≤ 0.300 bound. Correlation is nowhere near binding anywhere
   (r = 0.874 vs a 0.70 floor). 2025 was already the knife-edge year at 0.298,
   0.002 inside — the exposure ADDENDUM §G named as most likely before the solve.
4. **Determination NOT-YET, on C4-2025 alone.** With C3c ledgered the scorecard
   is 7 of 8 clean; C4 is not a ledgerable criterion (rubric v3.1 made C3c the
   only one), so a 2.7 % overshoot of one supporting-tier bound in one year holds
   the determination down by itself.
5. **The factor is not resized, and will not be.** Carve-out condition (c)
   forbids selecting a factor because it makes a criterion pass. 0.92 stands as
   the owner set it; no second value was tried in this session.

## §2 — What was actually changed

Every `offer_curve_by_group` band multiplier of every fossil class × **0.92** —
**40 bands across 10 classes**, `committed` / `econ_low` / `econ_high` / `peak`
only. Applied through `replay_keeper.py --offer-curve-json`, which resolves at
`pipeline/backcast_config.py:2523`, **after** every per-ISO and measured-surface
merge, so the cut is not silently overwritten. Values committed verbatim at
`results/calibration/_caiso267_fossil92_offer_curve.json`.

**Untouched:** every `phys_*` key, `econ_low_share`, `pct_peaking`. `peak_ladder`
is **not** separately parameterised — the CAISO conditional split rebuilds it
from the post-override `peak`, so its five uniform rungs follow the cut and the
"N equal sub-bands at one MC == one flat band" identity is preserved (verified
pre-solve: the keeper's ladders are `[[0.2, 1.386]×5]` and `[[0.2, 1.154]×5]`,
uniform copies of `peak` in both classes).

**Rule 25 `[R-ISO-SCOPE]`:** a CLI override on a CAISO invocation. No shared
default, no `constants.py` value, no other ISO's curve.

## §3 — Provenance: this is a price-tuning act, not an accuracy repair

The owner ruled mid-session, verbatim: *"pivot to a solve that reduces fossil
[offer] curves by 8 % across the board because they are overshooting
significantly that that will [bring] 2021 in tolerance"*, and after objection,
*"I don't care what measured says just adjust it 8 % downward."*

**Two objections were raised before executing and the owner reaffirmed. Both are
recorded rather than re-argued:**

1. **CAISO's measured surface points the other way.** caiso-266 §7 measured the
   pooled 2023–2025 CC bands at `committed` **1.030** vs armed 1.000, and
   `econ_low` / `econ_high` / `peak` at **exactly** their armed 1.066 / 1.072 /
   1.386. A measured-faithful repair moves the CAISO belly price **UP**; this run
   moves it **DOWN**. It is therefore the rules 1 `[R-STRUCT]` / 13
   `[R-MEASURED]` **authorized price-tuning channel** and is declared as such —
   **never** a rule 14 `[R-ACCURATE]` repair.
2. **2021 cannot receive it.** See §6.

**Carve-out conditions, each answered** (declared in
`governance.authorized_price_tuning`; **C6 PASSES**): (a) band multipliers only;
(b) ONE config across every scored year; (c) set ex ante, pushed before the first
LP, **never swept**; (d) relative band ratios are preserved, so fossil merit
order is unchanged and only fossil-vs-non-fossil moves — the intended effect;
(e) declared in the attestation and carried in the DOF ledger.

## §4 — The scorecard, keeper vs arm

| criterion | tier | keeper | arm |
|---|---|---|---|
| C1 fuel-mix | load-bearing | PASS | **PASS** |
| C2 system volume | load-bearing | PASS | **PASS** |
| C3a mean LMP | load-bearing | PASS | **PASS** |
| C3b price shape | load-bearing | PASS | **PASS** |
| **C3c price tail** | supporting | CAVEAT (ledgered) | **CAVEAT (ledgered, owner ruling)** |
| **C4 dispatch corr** | supporting | PASS | **FAIL** |
| C6 governance | protective | PASS | **PASS** |
| C8 forced share | protective | PASS | **PASS** |
| **determination** | | **CALIBRATED** | **NOT-YET** (C4-2025 alone) |

**C3a, per year** (actual = the bench `rt_lw` load-weighted basis):

| year | actual | keeper | arm | Δλ |
|---|--:|--:|--:|--:|
| 2023 | 54.17 | 56.543 (**+4.38 %**) | 53.698 (**−0.87 %**) | **−2.845** |
| 2024 | 34.65 | 37.731 (**+8.89 %**) | 36.150 (**+4.33 %**) | **−1.581** |
| 2025 | 34.42 | 37.260 (**+8.25 %**) | 35.539 (**+3.25 %**) | **−1.721** |

**The two failures, at full magnitude:**

* **C3c-2023** — keeper: model 23 h vs actual RT 47 h > $200 (0.49×). Arm: model
  **0 h** (0.00×). I initially left this undocumented on the reasoning that it is
  a regression the arm *caused*. **The owner ruled it an acceptable caveat**
  (2026-09-09), so it is ledgered alongside 2024 — one criterion, one slot, both
  magnitudes reported in full on the determination basis. Nothing is hidden by
  the ledger: it reports "model 0 h vs 47 h", it does not erase it.
* **C4 gas, all three years** — the only genuine break, and it is small and
  isolated:

  | year | keeper | arm | Δ | vs ≤ 0.300 |
  |---|--:|--:|--:|---|
  | 2023 | 0.287 | **0.275** | −0.012 | better, inside |
  | 2024 | 0.260 | **0.254** | −0.006 | better, inside |
  | 2025 | 0.298 | **0.308** | **+0.010** | **0.008 over (2.7 %)** |

  Correlation passes comfortably in every year (2025 r = 0.874 against a 0.70
  floor), so the miss is entirely in the shape term, in the one year that was
  already 0.002 inside the bound.

## §5 — Pass-through is NOT uniform, and that is the finding under the finding

| year | pre-solve mean Δmc | realized Δλ | implied pass-through |
|---|--:|--:|--:|
| 2023 | −2.845 | **−2.845** | **1.00** |
| 2024 | −2.704 | −1.581 | **0.58** |
| 2025 | −3.266 | −1.721 | **0.53** |

A single ISO-wide factor cannot hit three years at once, because the fraction of
the offer cut that reaches price varies almost two-fold across them. 2023
transmits the cut essentially completely (which is why it overshoots to −0.87 %);
2024–2025 transmit about half (which is why they stay positive at +4.33 / +3.25 %).
**This is measured, not modelled**, and it is the structural reason an 8 % cut
lands unevenly. It is reported, **not** used to justify a per-year value — rule 1
condition (b) forbids one.

## §6 — 2021 and 2020: neither is reachable, measured rather than asserted

The ruling's stated motivation was 2021. **No part of this session is identified
against 2021, and 2021 was not solved, scored or registered.**

| year | raw LMP on disk | in the scored reference | demand artifact | status |
|---|---|---|---|---|
| **2020** | **absent** | no | no | needs a data fetch (owner: *"Don't do any more data fetching"*) |
| **2021** | present but **holed** | no | **absent** | needs 3 builds + an amendment |
| **2022** | present | yes | yes | **solved in a parallel shard**, §8 |

**The 2021 hole is larger than the handoff recorded.** Counting rows in
`data/raw/lmp-data/CAISO/CAISO_rtm_hourly_2021.csv`: the file **starts
2021-04**, **August carries 70 rows**, and **September is entirely absent** —
roughly four months missing, not the sixty days the queue item names. 2021 is in
neither `actual_lmp_hourly_CAISO.parquet` (years 2022–2026) nor
`actual_lmp.json`, and `caiso_supply_consistent_demand_2021.csv` does not exist.
Reaching 2021 needs: the RTM gap re-fetched, `derive_actual_lmp.py` re-run to add
the year, a 2021 supply-consistent demand artifact built, and a
`CAISO_PARTIAL_YEARS` amendment **CAISO cannot grant itself**.

Even were it reachable, rule 22 makes 2021 a **re-test, never a fit target**: a
factor selected because it moved 2021 would be per-criterion selection against a
holdout year, which condition (c) refuses.

## §7 — Governance record

* **Rule 29 `[R-SCREEN]`** — zero-LP step 0 first (the offer-array delta of
  ADDENDUM §E). **SCREEN YEAR 2023**, named ex ante by the mechanism's own
  footprint: largest on **both** the $ of offer re-pricing (**$171.5 M** vs
  153.4 / 163.0) and raw fossil energy (**60.28 TWh** vs 56.73 / 49.91), and
  **simultaneously the year with the smallest residual** — a residual-driven
  choice picks 2024, so the selection is demonstrably not residual-driven.
  **All four STOP gates PASS:** G-IDENT max |Δdemand| **0.000 MW** over 61,320
  zone-hours; G-FOOT fossil **+2.3444** TWh vs non-fossil **−2.3475**
  (conservation residual −0.0031); G-DIR Δλ **−2.8497** against a pre-solve
  prediction of **−2.845**, i.e. the LP reproduced the zero-LP arithmetic to
  **$0.005/MWh**; G-NOFLIP C1/C2/C3b/C4 all PASS → PASS on the screen year.
  Instruments: `scripts/probes/_caiso267_screen_gates.py`,
  `scripts/probes/_caiso267_gnoflip.py`.
* **G-CTRL — form 4 was NOT claimed, and a control was spent.** The G-DRIFT
  audit measured **94 files / +46,838 / −26,486 lines** on the backcast solve
  path since the keeper's merge commit `bdfb3095`, including `results/cache.py`
  (+342), `model/interchange/spec.py` (+691) and `model/reserves/spec.py` (+272).
  A credible hunk-by-hunk INERT classification was not achievable in this
  session, so rather than assert one I spent the 2023-only control rule 29(b)
  provides. **It measured the drift at +0.0043 $/MWh** with demand identical to
  the MWh — i.e. **form 4 would have been valid after all**. Recorded because the
  honest sequence matters: I could not audit it, so I measured it.
* **Rule 22 `[R-HOLDOUT]`** — identification on 2023–2025 only. 2022 is a
  **re-test** run in a parallel shard (§8) under CAISO's `complete` marker, with
  the freeze scoped to locked test alone. No locked-test year was touched.
* **Rule 31 `[R-RETAIN]`** — nothing solved was deleted. The screen and control
  bundles are **gitignored, not removed**, and remain on local disk.
* **Rule 27 `[R-PUSH]`** — no source file ≥ 300 lines was rewritten; the pushed
  run payload was blob-verified at 669,092 bytes against local.

## §8 — Disclosures against interest

1. **The 8 % was not chosen by me and I recommended against it on the
   measurement.** The owner reaffirmed; that is their call and it is executed in
   full. My objection is in §3 so a later reader judges the ruling, not a silence.
2. **The first screen arm was OOM-killed** at 7.5 GB RSS (cgroup kill, PID 4712)
   because I ran two CAISO per-plant LPs concurrently. Rule 12's "~2 simultaneous"
   cap is **too generous for CAISO on a 15 GB box** — it is one at a time. Cost:
   ~15 minutes. The re-run reproduced the killed run's P0 objective exactly
   (3,459,399,439.8864), so nothing was lost but time.
3. **The first shard failed to launch** (`ref_not_found`): I pointed it at a
   branch that was merged into `main` and auto-deleted between my push and its
   clone. The relaunch is pinned to an immutable commit SHA.
4. **ADDENDUM §D was corrected before the arm solved** (§D.1): 13 classes → 10.
   The offer-curve router does not read the three `*_INTERMEDIATE` classes. A
   no-op in substance — all three carry zero CAISO energy in all three years —
   but the original declaration was wrong and is corrected in place, not quietly.
5. **The cut puts two bands below their own measured physical min-load heat
   rate for the first time**: `CT_PEAKER.committed` 0.991 → 0.912 against
   `phys_committed` 0.991 (the keeper sat exactly *at* physical), and
   `CT_CHP.committed` 1.100 → 1.012 against 1.073. Three more
   (CC_REGULAR/CC_CHP `committed` and `peak`, ST_GAS `committed`) were already
   below theirs on the keeper and are deepened. `phys_*` is inert in this recipe
   (`gas_offer_net_revenue_margin=false`) and was not touched, so this changes no
   LP row — but the model now offers committed gas below its own measured fuel
   cost, which is worth a reader's attention either way.
6. **I installed the solve stack** (pandas/numpy/pyarrow/scipy/pydantic/highspy,
   pinned to the keeper's recorded versions incl. **highspy 1.14.0**) and
   rebuilt the gitignored `data/clean/capacity-deliverability` partition, absent
   at session start.
7. **The caiso-266 corpus lane produced one measurement before the pivot** and it
   is recorded so the next session does not re-pay for it: OASIS `PUB_DAM_GRP` is
   **reachable** — 2024-04-10 returned a 382,728 B zip in 1.3 s (10.99 MB CSV,
   41,616 rows, all 28 expected columns). Corpus cost: **0.38 MB/day**, ~7.3 s per
   request at the AUP throttle, hole rate **1/1,096 = 0.091 %**. No price or MW
   was read. The belly-conduct question of the original PRECOMMIT is **untouched
   and still open**.

## §9 — The promotion question (rule 31 `[R-RETAIN]`, put explicitly)

**This is the owner's decision and I have not pre-empted it.** The arm is
registered and committed; the keeper is unchanged.

The trade, stated once, **after** the owner's C3c ruling: the cut **halves the
price-level error** (mean |C3a| 7.17 % → 2.82 %), leaves 7 of 8 criteria clean,
**improves C4 in two years of three**, and costs **one supporting-tier bound
overshot by 0.008 in 2025** — which by itself takes the determination to NOT-YET.
Options:

* **(a) Promote anyway** — accept NOT-YET as the price of a materially better
  price level. Rule 30(c) is not in play (this is a training-tier verdict, not a
  holdout one). What you would be accepting is precisely one number: C4-2025 gas
  NRMSE at 0.308 instead of ≤ 0.300.
* **(b) Do not promote** — the keeper stays `2026-09-06-caiso-260-b1-demand`, and
  caiso-267 stands as a registered rejection with its evidence.
* **(c) Re-cut the factor** — **I have not done this and will not without an
  explicit ruling**, because choosing a smaller factor *because* it keeps C4-2025
  inside 0.300 is the fitted-mechanism selection condition (c) exists to forbid.
  If the owner wants a different value it must be set ex ante, for a stated
  reason that is not a gate, exactly as 0.92 was.

**Next number: caiso-268.**
