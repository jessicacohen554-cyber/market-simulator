# PRECOMMIT — miso-266: the derate denominator is not the capacity the derate is applied to

```
SESSION : miso-266        ISO: MISO        PHASE 0: ZERO LP. No shard launched before this doc.
KEEPER  : 2026-09-20-miso-264-anchor-vintage (results/calibration/miso264_anchor_span,
          2020-2025) — VERIFIED ON main BEFORE ANY WORK. UNCHANGED by phase 0.
          Train tier 2023-2025 CALIBRATED, C3c the lone ledgered caveat.
CHARTER : FINDING-miso265 §7 routed two repair directions and instructed that the
          choice be made on the extract's/LP's own CONSTRUCTION, never on the
          residual (rule 1 [R-STRUCT]).
ANSWER  : direction (a) is CLOSED BY CONSTRUCTION — under per_unit_clip the sum
          already IS the per-unit union, so no union remains to take. Direction
          (b) is the live one, and its cause is NOT the "window mass" §3.2
          proposed: the derate DENOMINATOR is a SECOND, YEAR-INDEPENDENT
          reconstruction of a capacity the LP already holds, and it is 0.414x to
          0.814x the dispatched capacity at exactly the contradicted plants.
LANDED  : ScenarioConfig.unit_outage_dispatched_bin_denominator, GATED default
          OFF, zero free parameters, cache-key registered at its False drop
          value, 22 unit tests, matrix row + a cell in all nine ISO shards.
```

---

## 1. THE MECHANISM, LOCATED EXACTLY — and a correction to the charter

FINDING-miso265 §3.2 measured window mass as the separator between the 33
contradicted plants and the 12 clean ones (median summed `unit_pct_of_plant`
400.0 against 180.2) and named it "the operative quantity". **It is a
correlate, not the cause, and the cause is one line of arithmetic.**

The accumulator removes `share = sum_u ucap_u / denom` and the LP applies
`1 - share` to the bin's `pmax`. The MW actually removed is therefore
`share x cap_LP`, which equals the MW that went out **iff `denom == cap_LP`**.
That is an identity, and `outages._iso_plant_capacity`'s own docstring already
states it as the invariant:

> *"this denominator has to be THE SAME capacity the derate multiplier is
> applied to in the LP … reading the denominator off an un-armed fleet while
> the LP holds an armed one would remove the wrong absolute MW."*

It states it about one FLAG (`cc_steam_part_reclass`) and patches a second
channel by hand (`mid_vintage_exit_carry`, SPP-48's Oklaunion 127). **The
invariant is general and the map cannot honour it by reconstruction**: built
from `load_fleet_from_csv` + `load_retired_within_window`, it is blind to every
other way the dispatched fleet differs from that pair — above all the
**EXIT-COHORT bins** `fleet/assembly.py` synthesizes with an `_r{yyyy}{mm}` tag
(miso-191), which carry real dispatched capacity under the SAME
`(plant_code, plant_group)` key the overlay is looked up by.

### 1.1 The measurement (`scripts/probes/_miso266_denominator_vs_lp.py`, zero LP)

Rebuilt off the keeper's own fleet, each year on its OWN partition leg
(RESULT-miso263 §3), `denom / cap_LP` per COAL bin, MISO 2020:

| plant | name | LP MW | denom MW | denom/LP |
|---:|---|---:|---:|---:|
| 976 | Marion | 290.0 | 120.0 | **0.414** |
| 963 | Dallman | 492.3 | 209.3 | **0.425** |
| 6085 | R M Schahfer | 1,625.0 | 722.0 | **0.444** |
| 6055 | — | 1,101.3 | 551.3 | 0.501 |
| 4041 | South Oak Creek | 1,112.0 | 616.0 | 0.554 |
| 994 | — | 1,701.5 | 1,057.2 | 0.621 |
| 1073 | — | 43.6 | 29.3 | 0.672 |
| 6090 | Sherburne County | 2,238.0 | 1,556.0 | 0.695 |
| 6705 | — | 662.0 | 538.7 | 0.814 |

**That list IS FINDING-miso265 §3's hard-zero table**, in the same order:
Schahfer, South Oak Creek, Dallman, Sherburne County, Marion. Window mass
tracked the defect because a plant with mid-window unit retirements has both
more detected windows AND a denominator missing those units — the correlation
§3.2 measured, with the causal arrow pointing the other way.

At Schahfer one 432 MW unit out removes `432/722 = 60 %` of the plant instead
of `432/1,625 = 27 %`, and three concurrent units remove **242 %**, clipping a
plant to zero in 8,019 hours its own meter says it ran.

### 1.2 The signature that settles it: the denominator does not know what year it is

| year | LP COAL total MW | denominator total MW | ratio | bins denom < LP by >2 % | bins LP dispatches that the map LACKS |
|---|---:|---:|---:|---:|---:|
| 2020 | 54,238.1 | **50,365.4** | 0.9286 | 10 | 4 (538.0 MW) |
| 2021 | 54,227.8 | **50,365.4** | 0.9288 | 10 | 4 |
| 2022 | 54,065.1 | **50,365.4** | 0.9316 | 9 | 4 |
| 2023 | 54,038.0 | **50,365.4** | 0.9320 | 9 | 4 |
| 2024 | 53,945.7 | **50,365.4** | 0.9336 | 8 | 4 |
| 2025 | 53,391.6 | **50,365.4** | 0.9433 | 7 | 4 |

The denominator is **50,365.4 MW in every year, to the tenth of a MW**, while
the fleet it is supposed to describe retires 846 MW of coal across the span.
A year-independent constant standing in for a year-varying capacity is not a
modelling choice; it is the defect, visible without reference to any residual.

**It runs in BOTH directions**, which is what a basis error looks like and a
level haircut does not: 7 bins carry a denominator ABOVE the LP by >2 % and
therefore UNDER-remove, in every year.

### 1.3 Why charter direction (a) is closed by construction, not by test

FINDING-miso265 §7 direction (a) was to "cap a plant's accumulated share
strictly below 1.0 unless its units are *simultaneously* flagged by a union
rather than a sum". Under `unit_outage_per_unit_clip` — **TRUE in this keeper**
— each unit's removed MW is already capped at that unit's own capacity, so at
any hour

```
v[t] = sum_{u flagged at t} ucap_u / denom          EXACTLY
```

i.e. the per-unit union is already in place and there is no further union to
take (two DIFFERENT units out concurrently genuinely remove both capacities).
The only remaining arithmetic source of `v[t] > 1` is the basis. Measured
rather than asserted (`scripts/probes/_miso266_excess_decomposition.py`,
MISO 2020): of the 23,849 contradicted hours, **20,516 (86.0 %) occur while NOT
every unit at the plant is flagged** — basis excess — against 3,333 in which
every extract unit is flagged and a full derate is correct.

## 2. THE MECHANISM AS LANDED

`ScenarioConfig.unit_outage_dispatched_bin_denominator`, GATED default `False`.
`outages.lp_bin_capacity_index(generators, pmax)` sums the LP fleet's own
`pmax` per `(plant_code, plant_group)` **off the very generators and pmax the
overlay is then multiplied into**, and the accumulator uses that map in place of
the reconstructed one.

* **One map for MEMBERSHIP and for the DIVIDE**, because they are the same
  object: a bin the LP does not dispatch has nothing to derate, and a bin it
  does dispatch must be derated against what it dispatches. The second half is
  the SPP-48 Oklaunion pathology generalized — 4 MISO COAL bins (538.0 MW) ride
  un-derated through their own measured outages today.
* **Threaded into every layer that divides by `cap[bin]`** (rule 19
  `[R-ONE-MECH]`): std ≥5-day, short, partial, the lay-up loader (whose
  contract is that a lay-up share and an outage share are additive) **and
  MAXGEN**, which keeps its own accumulator loop but divides by the same
  `cap[bin]` on the same key. MAXGEN is INCLUDED here although `per_unit_clip`
  and `st_capacity_basis` exclude it — their exclusions rest on properties of
  the numerator and of window grain; this flag touches neither.
* **Non-ERCOT only**, like every sibling basis flag.
* **Mutually exclusive** with `unit_outage_lp_capacity_basis` and
  `unit_outage_extract_basis_share` — all three set the denominator, and the
  first reconstructs the `fleet_to_bins` raise that is already inside the `pmax`
  this flag reads. The loaders raise.
* **Zero free parameters** (rule 21 `[R-DOF]`) — every MW is the fleet's own.
  The keeper's DOF ledger carries over unchanged.
* **Rule 13 `[R-MEASURED]` forward-regenerable** and deliberately ABSENT from
  `_BACKCAST_ONLY_OVERLAY_FIELDS`: a forecast fleet has `pmax` exactly as a
  backcast one does. Listing it there would assert a non-regenerability that is
  false (the miso-200 reasoning).
* Full plumbing: `run_year` kwarg, `run_calibration_full` recorded config +
  forwarding + meta + `--replay`/`--rebuild` kwargs, and
  `--unit-outage-dispatched-bin-denominator` / `--no-…`. **This is deliberate**:
  FINDING-miso265 §4 found two registered outage tunables with no `run_year`
  plumbing at all, which `replay_keeper`'s binding guard rejects outright — a
  rule 24 `[R-REGISTRY]` gap this field does not repeat.

## 3. THE SIZE, AT ZERO LP, BEFORE ANY SOLVE

### 3.1 On the hard-zero subset (`_miso265_derate_variant_sizing.py`, MISO 2020)

| variant | avail == 0 plant-h | contradicted h | metered TWh | plants |
|---|---:|---:|---:|---:|
| incumbent (keeper) | 103,704 | 23,849 | 5.184 | 33 |
| `-fleet_status_scope` | 103,704 | 23,849 | 5.184 | 33 |
| `+extract_basis_share` | 103,704 | 23,849 | 5.184 | 33 |
| `+merit_order_guard` | 125,880 | 24,193 | 5.234 | 37 |
| **`+dispatched_bin_denom`** | **80,808** | **3,234** | **0.922** | **30** |

**−86.4 % of the contradicted hours and −82.2 % of the contradicted energy**,
against four predecessor candidates that moved it by 0 % or made it worse.

*Correction to the instrument:* miso-265's `BASE_KWARGS` omitted
`fleet_status_scope=True`, which the keeper's `run_config_2020.json` carries, so
its "incumbent" row was one flag off the keeper's real posture. Corrected here.
It changes no number — the flag is measured inert in both directions — but the
base is now the keeper's.

### 3.2 On the full ceiling contradiction (`_miso266_repair_ceiling_ab.py`, all six years)

Both legs rebuild the SAME year's fleet from the SAME keeper recipe with
`fleet_only=True`, differing in exactly one flag.

| year | control TWh | control p-h | armed TWh | armed p-h | ΔTWh | closed |
|---|---:|---:|---:|---:|---:|---:|
| 2020 | 25.414 | 142,058 | 18.933 | 121,198 | −6.481 | 25.5 % |
| 2021 | 32.427 | 192,247 | 26.618 | 177,019 | −5.809 | 17.9 % |
| 2022 | 28.939 | 171,591 | 23.444 | 162,655 | −5.495 | 19.0 % |
| 2023 | 22.337 | 135,172 | 18.468 | 126,541 | −3.869 | 17.3 % |
| 2024 | 20.243 | 119,639 | 18.564 | 115,120 | −1.680 | 8.3 % |
| 2025 | 26.097 | 164,540 | 25.291 | 158,168 | −0.806 | 3.1 % |
| **TOTAL** | **155.457** | | **131.318** | | **−24.139** | **15.5 %** |

**The control column reproduces FINDING-miso265 §2.2 in all six years to the
milli-TWh**, which validates this instrument against the predecessor's before
any claim is made from it.

**The fade from 25.5 % to 3.1 % is the mechanism's own signature, not a
weakness**: exit cohorts are the 2020-2022 retiring coal fleet, so the defect is
largest where that fleet is largest and shrinks as those units leave. A
mechanism whose footprint tracked nothing in particular would not do that.

### 3.3 What it does NOT close, stated now

**84.5 % of the ceiling contradiction survives the repair.** The residual is
the two shapes FINDING-miso265 §2.2 named — plants short on LEVEL and plants
whose ceiling sits in the WRONG HOURS — plus the ~7 % nameplate-over-net-summer
numerator inflation that `st_capacity_basis` refuses at precisely these bins
(its 1-1 unit pairing fails where the fleet roster is missing the very units
this defect is about). **The numerator cannot be put on "the LP's own per-unit
capacity" the way the denominator can**: at a per-plant-binned ISO the LP has
no units, only tranches. So charter direction (b) is delivered on its
denominator half exactly and on its numerator half not at all, and that is
stated rather than glossed. `COAL_LIGNITE` 2025's negative annual headroom
(FINDING-miso265 §7.2) is untouched by any of this.

## 4. G-DRIFT — form 4 is **VOID**. Control solves are earned.

Rule 29 `[R-SCREEN]` (b), `git diff 23b5d44e..origin/main` over `src/market_sim`,
`scripts/run_calibration.py`, `scripts/run_calibration_full.py`, `scripts/lib`,
`data/raw/_validation-source`, `data/raw/reference` — 27 commits, 5,618
insertions over 27 files.

**The audit terminates on its first LIVE finding, and the verdict is monotone**
(one LIVE hunk voids form 4; further INERT classifications cannot restore it):

| commit | what | verdict |
|---|---|---|
| `d45d57f9` | un-nest the same-year P1 basis seed from the cross-year gate; `MARKET_SIM_P1_BASIS_SEED` becomes its own env var | **LIVE** |
| `5cb65892` / `e107949d` PERF-C S1/S2 | slim the P0 extraction; the same-year seed's default | **LIVE** |
| rule 36 `[R-YEAR-ISOLATION]` (d) | `resolve_xyear_warmstart_default` and `resolve_p1_basis_seed_default` both now default **OFF**; the keeper was solved with both **ON** | **LIVE** |
| `src/market_sim/data/fuel/basis/miso.py` | MISO-specific, but every hunk threads `gas_flow_date_year_start_package`, a new field defaulting `False` and absent from the keeper's recipe | INERT |

**The LIVE finding is not a surprise — it is this repo's own published
measurement.** Rule 36 was written FROM MISO: replaying the keeper's six years
standalone at one pinned HEAD reproduced the first year of each solve leg
(max |Δ class TWh| 0.0048 in 2020, 0.1440 in 2023) and diverged in the rest
(**7.1586 / 24.1796 / 4.0034** in 2021 / 2022 / 2025, with 43,160 of 70,080
price cells moving in 2022). Rule 36 (f) states the consequence plainly: *"every
ISO's keeper was solved through the CLI with both knobs ON, so every keeper
carries some of this artifact and its registered numbers will move when it is
next re-solved."*

So **the committed keeper bundle cannot be the control for a HEAD arm**, and a
control leg is solved for every year. That closes the drift question completely
rather than partially: control and arm run at the SAME pinned SHA, in the SAME
container, with the SAME year isolation, so every hunk above — classified or
not — is absorbed identically by both legs and the delta is provably the one
flag.

**This batch therefore also discharges MISO's outstanding rule-36 re-solve
debt.** The six control legs ARE the keeper's recipe re-solved under year
isolation with the warm-start knobs at their new defaults, which is what rule 36
(f) says each lane owes on its own cadence.

## 5. THE DECISION RULE, FIXED NOW

**The arm is adjudicated on rule 14 `[R-ACCURATE]` and rule 1 `[R-STRUCT]`, and
on nothing else.** `denom == cap_LP` is an identity the code already claims to
satisfy and provably does not; the evidence is §1.2's frozen 50,365.4 MW, not
any residual. Rule 14 governs the outcome in its own words: *"If swapping a hand
estimate for real data … makes the backcast worse, that is a signal that
something else in the model is miscalibrated. Keep the accurate input, find and
fix the real root cause."*

* **The arm is reported as the candidate whatever §6 turns out to be.** A worse
  gate does not retract it; a better gate does not validate it. Every regression
  is reported at full magnitude.
* **Nothing is swept.** One boolean, already built, already default-off, already
  registered at its `False` drop value. No alternative scope, cohort or
  threshold is tried, in this session or a successor's, on the strength of a
  gate.
* **Rule 21 `[R-DOF]`: zero free parameters added.**
* **Rule 25 `[R-ISO-SCOPE]`: nothing is armed outside MISO.** The code is
  shared, the default is off, every other ISO's key is unmoved, and all eight
  non-MISO shards carry the cell as `U` with the zero-LP transfer question
  written out. No MISO number crosses.

## 6. THE PREDICTION, REGISTERED BEFORE ANY SHARD IS LAUNCHED

The arm gives coal capability back — 24.139 TWh of ceiling across the span,
concentrated in 2020-2022 — so coal can dispatch more where it is in merit.
Direction, not magnitude; the LP re-dispatches and I do not claim to know by
how much.

| criterion | year | live | direction expected | why |
|---|---|---|---|---|
| **C1** COAL_BIT | 2020 | **−10.92 TWh FAIL** | toward zero | Schahfer/Dallman/South Oak Creek/Marion are COAL_BIT and carry the largest ratios |
| **C1** COAL_PRB | 2022 | **+8.13 TWh FAIL** | **AWAY — could deepen** | PRB is already LONG; giving it capability can only lengthen it where it is in merit |
| **C3a** mean LMP | 2020 | **+14.6 % FAIL** | toward zero | cheap coal displacing gas at the margin lowers price |
| **C3b** shape | 2021 | **0.304 FAIL** | unknown | 2021 carries the span's largest single-year Δ (−5.809 TWh) |
| **C1 / C3a** | 2023-2025 | all PASS, **CALIBRATED** | **EXPOSED** | −3.869 / −1.680 / −0.806 TWh of ceiling moves there too |

**STATED AGAINST THE ARM, IN ADVANCE:**

1. **THE CALIBRATED TRAIN TIER IS A LIVE G-NOFLIP RISK, and it is exposed twice
   over.** 2023-2025 read CALIBRATED with zero failing criteria today. The arm
   moves them; and the CONTROL moves them too, independently, through the rule-36
   warm-start flip this batch adopts. If the tier degrades, part of that is the
   arm and part is drift MISO owes regardless — the control legs are what
   separate the two, and the RESULT will report the split rather than the total.
   **A degraded train tier is a real cost and will be reported as one, not tuned
   away** (rule 30 `[R-TOUCHPOINT-FOLD]` (c) does not apply: 2023-2025 are the
   determination).
2. **C1 2022 COAL_PRB is predicted to get WORSE.** It is +8.13 TWh long and the
   repair hands PRB capability back. If it deepens, that is reported at full
   magnitude and is not a reason to narrow the mechanism's scope.
3. **C1 2020 is not promised.** FINDING-miso265 §5 already disclosed that 2020's
   class-level headroom is +12.01 TWh against a −10.92 miss, so closure is not
   arithmetically guaranteed even from a perfect availability repair — and this
   repair closes 25.5 % of the contradiction, not all of it.
4. **84.5 % of the object survives** (§3.3). This session does not claim to have
   fixed the availability envelope; it claims to have fixed one identified,
   zero-DOF arithmetic defect inside it.
5. **The registered numbers of MISO's keeper will move even in the control leg.**
   Anyone comparing this batch's control against the committed bundle is
   comparing across the rule-36 flip, not against a like-for-like baseline.

## 7. HOW IT IS SOLVED

Rule 36 `[R-YEAR-ISOLATION]` + rule 34 `[R-SHARD-PROMOTABLE]`: **six shards, one
per year**, each running TWO separate `--years <single year>` invocations — the
control leg (`--no-unit-outage-dispatched-bin-denominator`) and the arm leg
(`--unit-outage-dispatched-bin-denominator`) — into two out-dirs, and pushing
both bundles in full including `dispatch/<y>_P1.parquet`.

**Why both legs in one container rather than twelve containers.** Year isolation
is preserved exactly (each leg is its own single-year process, so no LP basis
crosses a year boundary — rule 36 (a)), and pairing the legs in one container at
one pinned SHA makes the A/B stronger: identical code, identical inputs,
identical hydration, one flag. **The budget is stated as rule 32 (b) requires**:
MISO is the per-plant multi-zone case that clause names, ~15 min per year-leg
plus hydration, so ~40 min per shard against the 20-minute default ceiling. A
shard that reaches 60 minutes with no artifact STOPS and reports; it never
pushes a half-written bundle.

**All six years, 2020-2025** (rule 34 (c)): that is the union of the years the
ISO's registry carries, read before anything is pruned (rule 35 `[R-PROMOTE]`
(b)). The registry carries exactly one MISO run,
`2026-09-20-miso-264-anchor-vintage`, spanning 2020-2025; no run is stamped to
it, so the union is those six years and nothing else.

Composition, `stamp_config_partition.py --check`, scoring, the dashboard
registration and the promotion question are the PARENT's, once, after the shards
land (rule 32 (d)).

## 8. WHAT THIS SESSION DOES NOT CLAIM

* That the arm closes C1 2020, C3a 2020, C3b 2021, or moves any gate in any
  direction. The repair is argued from `denom == cap_LP` and from §1.2's frozen
  denominator; **the residual is not evidence for it and a worse residual would
  not retract it.**
* That the availability envelope is repaired. 84.5 % of the contradiction
  survives, and its two named shapes are untouched.
* Anything about any other ISO. The defect's SIZE is a per-ISO fleet property —
  an ISO that synthesizes no exit-cohort bins may find the two maps already
  agree and the flag inert — and no verdict transfers (rule 25).
* That `_iso_plant_capacity` is now correct. It is still a second construction of
  a capacity the LP already holds, still year-independent, and still the
  denominator whenever this flag is off. **Routed, not absorbed:** the general
  fix is to delete the reconstruction, which is a cross-ISO change no single
  lane should make on its own evidence.
