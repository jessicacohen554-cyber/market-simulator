# PREREG miso-223 — THE BODY, NOT THE SEASON: one flat defect read at two points on the scarcity gradient. Screen arm = revert the miso-220 ×1.10 lift on the `committed` band ONLY

**Written and committed BEFORE the screen solve.** Rule 29 `[R-SCREEN]`: phase 0 is
complete and recorded below; the screen year is named here, from the mechanism's own
measured footprint, before any LP is launched.

Keeper at entry: **`2026-09-05-miso-220-nonsteam-lift`** (bundle
`results/calibration/miso220_nonsteamlift_B`), CALIBRATED, C3c the single ledgered caveat.
Rule 22 `[R-HOLDOUT]`: 2023–2025 only.

---

## 1. THE PREMISE CORRECTION — the session was chartered on two seasonal misses; there is one defect

Charter: *"the miss in July 2025 and the overshoot in August for 2023 and 2024."* Measured
against the keeper's committed `hourly/system_<year>.parquet` (load-weighted across the six
carrying zones) and MISO's published RT hub LMPs (`data/raw/lmp-data/MISO/*_rt.csv.gz`,
mean over hubs), on the model clock:

| month | model $ | actual $ | err |
|---|---:|---:|---:|
| 2025-Jul | 44.70 | 59.45 | **−24.8 %** |
| 2025-Jun | 42.68 | 57.39 | **−25.6 %** |
| 2024-Aug | 37.90 | 32.53 | **+16.5 %** |
| 2023-Aug | 37.93 | 36.02 | **+5.3 %** |
| 2023-Dec | 35.07 | 27.29 | **+28.5 %** |
| 2023-Feb | 33.76 | 26.81 | **+25.9 %** |

**Both halves of the premise are confirmed but neither is seasonal.** July-2025 is the
smaller half of a Jun–Jul block; August-2023 (+5.3 %) is not 2023's overshoot at all —
December (+28.5 %) and February (+25.9 %) are, and they are the two months with the fewest
real scarcity hours (Dec-2023: **zero** actual hours > $100).

**The decomposition (all 36 train months, own-distribution quantile match, top decile = tail):**

- **Body (bottom 90 %) is too HIGH in 36 of 36 months**, +$5.0 … +$12.4/MWh, mean **+$7.68**.
  Per year: **+8.71 / +8.24 / +8.55**. Flat — no season, no year, no load dependence.
- **Tail (top 10 %) is too LOW in 33 of 36 months**, and its size *is* seasonal:
  **−15.62 / −18.90 / −44.17** by year, reaching −$85 … −$89 in Jun/Jul/Sep 2025.
- **corr(monthly mean error, count of actual hours > $100) = −0.676.**

So the monthly error is the sum of a constant positive body term and a scarcity-scaled
negative tail term. A month with many real scarcity hours reads as a **miss**; a month with
few reads as an **overshoot**. They are the same defect: **the model's price distribution is
too flat.**

Median and p99, model vs actual, by year:

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| p50 model / actual | 33.98 / 25.18 | 31.20 / 22.47 | 39.42 / 30.28 |
| p99 model / actual | 49.80 / 93.54 | 55.17 / 103.61 | 80.15 / 173.14 |

**The floor is the sharpest statement of it.** Across **210,240 committed zone-hours** the
model never prices below **$17.28**; MISO cleared below $20 in **1,781 / 3,097 / 510** hours
and went negative in 2023 and 2024 (min −$39.16).

## 2. IT IS AN OFFER-LEVEL DEFECT, NOT A DISPATCH DEFECT

In the model's own bottom price decile of 2025 the dispatch mix is close to EIA-930's in
the *actual* bottom decile — coal +2.2 GW, gas −1.7 GW, wind +1.9 GW on a ~63–66 GW load —
while the price is **+$12.48** ($31.22 vs $18.74). The model runs roughly the right units in
its cheapest hours and charges too much for them.

**And the keeper's own config says where the charge comes from.** miso-220's authorized
×1.10 lift was applied UNIFORMLY to all four bands of eleven fossil classes. Differenced
against the predecessor bundle `miso217_intermphys_B`, it moved:

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| body error, miso-217 → miso-220 | +6.86 → **+8.71** | +6.38 → **+8.24** | +6.27 → **+8.55** |
| tail error, miso-217 → miso-220 | −18.41 → **−15.62** | −21.98 → **−18.90** | −47.43 → **−44.17** |

The lift bought C3a-2025 (−12.3 → −7.0) mostly out of the **body** — the 90 % of hours where
the model was already too dear — and left the tail −$44 short. It is a level correction
applied to a shape defect. The mean now passes because two large errors of opposite sign
cancel.

**The tail half is not reachable and this arm does not attempt it.** miso-221 measured that
at the model's own annual maximum hour only **10.2 %** of the supply above the clearing price
carries an `offer_curve_by_group` entry (the rest is the ~2.9 GW oil fleet, already offering
$241–249); `ordc_scarcity_overlay` is `G`; the reserve/ORDC family needs 3.26–10.62× the
published requirement (miso-219); the ELMP emergency range is 3.4–11.8× short (miso-222).
**The body is the reachable object and no MISO session has attacked it.**

## 3. THE ARM — 11 values, all of them already-registered, zero new numbers

Revert the miso-220 ×1.10 on the **`committed` band only**, to each class's miso-217 value:

| class | keeper | arm | class | keeper | arm |
|---|---:|---:|---|---:|---:|
| CC_REGULAR | 1.1055 | **1.0050** | COAL_LIGNITE | 1.1000 | **1.0000** |
| CC_INTERMEDIATE | 1.1055 | **1.0050** | COAL_PRB | 1.1000 | **1.0000** |
| CC_CHP | 1.1000 | **1.0000** | COAL_BIT | 1.1000 | **1.0000** |
| CT_CHP | 1.1000 | **1.0000** | COAL_WC | 1.1000 | **1.0000** |
| CT_PEAKER | 1.1275 | **1.0250** | COAL | 1.1000 | **1.0000** |
| CT_INTERMEDIATE | 1.1000 | **1.0000** | | | |

`econ_low`, `econ_high` and `peak` **keep their miso-220 lifted values**; `phys_*`,
`econ_low_share`, `pct_peaking` are never touched; ST_GAS and ST_GAS_INTERMEDIATE are
untouched (already 1.0). Applied through `replay_keeper --offer-curve-json`, which
deep-merges only the named bands.

**The structural claim, stated as a claim and not as a residual:** the `committed` band is
the plant's CAMPD-observed **stay-online** band — the block it runs regardless of price. A
unit does not mark up the band it must run. Its offer belongs at its measured physics basis,
which is exactly where miso-217 had it (`phys_committed` 1.005 / 1.0 / 1.025). A 10 % markup
on the stay-online band has no market story; the markup bands above it (`econ_high`, `peak`)
do, and they stay.

**Governance.** Rule 1 `[R-STRUCT]` carve-out, every condition: (a) `offer_curve_by_group`
band multipliers only; (b) ONE config across all three scored years; (c) values fixed here,
ex ante, and **not swept** — each is the value already registered in a committed bundle, so
there is nothing to select; (d) merit-order change is intended; (e) declared in
`governance.authorized_price_tuning`. DOF ledger unchanged at **41/2** — this narrows the
scope of an already-ledgered parameter, it does not mint one. Rule 19 `[R-ONE-MECH]`: a bid
change on one band; no floor, no D-2 id.

## 4. SCREEN YEAR = **2024**, named from the mechanism's own footprint

`committed`-band energy of the eleven lifted classes, from the keeper's committed
`class_band_hourly_<year>.parquet`:

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| committed-band TWh | 162.43 | **171.19** | 164.15 |
| % of lifted-class energy | 45.6 | **47.4** | 43.4 |
| % of system load | 25.3 | **26.6** | 24.7 |

2024 is the largest footprint. It is **not** the largest-residual year (2025 is, at −$44 on
the tail and −24.8 % in July), so the choice is demonstrably not residual-driven.

## 5. SCREEN GATES — structural, STOP-only, never gated on the target residual

A gate may **kill** this arm; none of them may promote it, and none reads C3a.

- **S-1 single delta.** Exactly 11 values differ from the keeper's recorded
  `offer_curve_by_group`; every other `run_config.json` field byte-identical. Else STOP.
- **S-2 liveness.** The merged table recorded in the arm's `run_config.json` equals the
  table in §3 exactly. Else STOP.
- **G-1 direction & magnitude.** 2024 body (bottom-90 %) mean price falls by **$1.0–$2.2**.
  Pre-solve arithmetic: the uniform lift added +$1.86 to the 2024 body across all four
  bands; reverting the band carrying 47.4 % of lifted energy should return most of it, and
  cannot return more. Outside the band ⇒ the mechanism is not doing what its arithmetic
  says ⇒ STOP.
- **G-2 confinement.** 2024 tail (top-10 %) mean price moves by **less than |$3.0|**. These
  are body bands; a large tail move means the footprint is not confined to the rows the
  mechanism claims ⇒ STOP.
- **G-3 no non-target load-bearing flip.** No 2024 C1 or C2 cell flips PASS → FAIL.

**NAMED EX ANTE AS THE LIKELIEST KILL — `CC_REGULAR`-2024**, at **+7.947 TWh against a
±8.00 band: 0.053 TWh of headroom.** The arm makes CC's stay-online band cheaper, which
pushes that cell further positive. If it exits, G-3 fires and the arm dies on the screen
year; the remaining years are never spent. Second exposure, with room: **ST_GAS-2024** at
−5.035 — ST_GAS is held at 1.0 and therefore becomes relatively dearer, partially undoing
the gain miso-220's non-uniform lift bought it.

## 6. REPORTED AGAINST THE ARM, BEFORE IT RUNS

**C3a will get worse in every year, and that is not a reason to reject it** (rule 1
`[R-STRUCT]`: a structurally-correct mechanism is never judged by the residual). Expected
direction: 2023 +7.15 → ≈ +5, 2024 +3.37 → ≈ +1.5, 2025 −7.00 → ≈ −9, with **C3a-2025 at
real risk of re-failing the ±10 % band.** This arm is therefore **unlikely to be promoted as
a keeper on the current rubric**, and it is not proposed as one. It is proposed because a
model whose median price is 30–39 % too high is misrepresenting the economics every
retirement, entry and emissions screen runs on, and because the mean currently passes only
by cancellation. The screen's job is to establish whether the body term is the offer-band
markup, at the cost of one year of LP.

## 7. CONTROL — a real one, because G-DRIFT comes back LIVE

Rule 29(b) form 4 (the committed keeper as control) is **not** available: the keeper's
`git_sha` is `4545300d` and HEAD is `d340adf1`, a diff of **66 files / +5,985 / −856** over
`src/market_sim` including `model/lp/rows.py` (+224) and `pipeline/solve.py` (+12) — solve-path
files that a backcast run enters. Rather than classify 66 files, a **zero-delta replay of the
keeper at HEAD on 2024 only** is solved alongside the arm, and every gate above is
differenced arm-vs-control at the same HEAD. Two single-year invocations, concurrent, within
rule 12's cap of ~2 for per-plant multi-zone LPs.

## 8. WHAT THIS SESSION WILL NOT DO

No dashboard registration of the screen bundles (rule 29 clause 2 — a screen bundle is a
throwaway diagnostic probe), and both bundles are **deleted before the PR merges** (rule 29(c),
owner ruling R-AV). Every number this session will ever cite lands in the FINDING doc. No
keeper promotion from a single-year screen (rule 16 `[R-ALLYEARS]`). No matrix cell verdict
moves on a screen result alone; the `offer_curve_by_group` MISO cell keeps `K` and gains
evidence.

---

## ADDENDUM A (written before the arm solve; the control was already running) — CHANNEL, not values

`--offer-curve-json` **refuses** the three duty-split classes: its validator allowlists only
the eleven base router classes and rejects `CC_INTERMEDIATE` / `CT_INTERMEDIATE` /
`ST_GAS_INTERMEDIATE`. That is a CLI validator limitation, not a modelling one — the
`*_INTERMEDIATE` curves ARE consumed (`data/offer_curves.py` routes an intermediate-duty unit
to them, and miso-217's `miso_intermediate_gas_offer_margin` grafts the parent's `phys_*`
onto them at read time). Dropping them would leave `CC_INTERMEDIATE`/`CT_INTERMEDIATE`
`committed` at 1.1055/1.1 while their parents sat at 1.005/1.025 — a scope inconsistency, and
a partial arm.

The arm therefore rides `replay_keeper --set offer_curve_by_group=<full table>` (the generic
`prb_overrides` → `ScenarioConfig.with_overrides` channel, applied last), supplying the
keeper's own recorded 13-class table with **exactly the 11 `committed` values of §3 changed**
and every other value byte-copied from `miso220_nonsteamlift_B/run_config.json`.

**No value in §3 changes, and no gate changes.** S-2 (liveness) is unaffected in form and
becomes the check that catches any surprise from the wholesale-replacement channel: the arm's
recorded `offer_curve_by_group` must equal the keeper's table with those 11 substitutions and
nothing else. S-1 remains "exactly 11 values differ".

---

## ADDENDUM B (written before either screen solve ran) — execution route and a stale ref

Three corrections to this document's own text, recorded rather than silently fixed.

**(1) THE SOLVES RUN IN CI, ON EXPLICIT OWNER AUTHORIZATION.** A MISO per-plant
single-year LP peaks near **14 GB** of anon RSS; a Claude Code session's Bash cgroup caps at
**13 GB**. Measured this session, three times: the concurrent pair was OOM-killed (one process
at anon-rss 13,954,092 kB), and the control and arm were each killed **running alone** at the
cap (`memory.failcnt` 131,171; `memory.max_usage_in_bytes` = `memory.limit_in_bytes` = 13 GB).
The gap is ~1 GB and there is no recipe-neutral way to close it — every knob that would
(fleet binning, zone count, the 2,606-member per-asset reserve columns) changes the recipe,
and a screen solved on a different recipe than the keeper measures nothing. CLAUDE.md's
"never offload work to CI" section requires owner sign-off before spending runner minutes on
this private repo; **the owner gave it.** The route is
`.github/workflows/calibration-solve.yml` — `workflow_dispatch`-only, parameterized, dry-run
by default, and the bundle leaves as a **build artifact that is never committed** (rule 29(c)
deletes screen and control bundles before merge; rule 15 registers runs from a session, not
from CI). Rule 22 is untouched: the tier-marker gate still lives in `replay_keeper` /
`run_calibration_full`, and CI is not a route around it.

**(2) THE G-DRIFT REF IN §7 IS STALE, AND THE CONTROL IS WHY THAT IS HARMLESS.** §7 recorded
HEAD as `d340adf1`. This session's work was merged and `main` has since moved to `42fcc058`.
**Both the control and the arm are dispatched against `42fcc058`**, so the A/B differencing is
between two solves of one code state and every gate in §5 stands as written. This is exactly
the situation §7 spent a control solve to be immune to: a form-4 differencing against the
keeper's committed numbers would now be reading two code states, and it is not being used.
The §7 diff (`4545300d..d340adf1`, 66 files) is superseded as a **count**, not as a
**conclusion** — G-DRIFT was LIVE then and is more so now, and the remedy is unchanged.

**(3) A NUMBER IN §1.** The model's minimum price across all committed zone-hours is
**$17.18** (2024), not the $17.28 §1 states. The draft figure came from a load-weighted
system-average series; the instrument
(`scripts/probes/_miso223_body_tail_phase0.py` → `_miso223_body_tail.json`) takes the true
zone-hour minimum. The claim is unchanged and marginally stronger. Every other pre-registered
number reproduces exactly from that instrument: body too high **36/36** months, tail too low
**33/36**, corr(monthly error, actual hours > $100) = **−0.676**, screen year **2024** derived
from the committed-band footprint.

**No pre-registered value, gate band, or kill condition is amended by this addendum.**
