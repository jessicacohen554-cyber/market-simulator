# PRECOMMIT ADDENDUM — pjm-d4-4 stage-2 screen: the gates, registered before the solve

**Session:** pjm-d4-4 · **Date:** 2026-09-10 · Extends
`docs/PRECOMMIT-pjm-d4-4-forced-outage-composition-2026-09-10.md`.
**LP spent at the time of writing: ZERO.** This file registers the stage-2 screen's gates before
the shard is launched, and RETIRES one of the handoff's own gates on arithmetic rather than on a
solve.

---

## §1 — the kill gate cleared, so the arm was built

Measured, merit-guarded, 2022 (full numbers and the six-year table:
`docs/RESULT-pjm-d4-4-forced-outage-composition-2026-09-10.md`):

| bar | registered | measured | verdict |
|---|---|---|---|
| **G-KILL-1** mean removed MW over the 92 actual RT > $200 h | ≥ 2,425 | **4,570** | **PASS 1.88×** |
| **G-KILL-2** annual-mean removed MW | ≥ 700 | **1,185** | **PASS 1.69×** |

Stage 1 is built and committed: `ScenarioConfig.unit_outage_short_windows_gas` (default off),
`data/raw/campd-unit-outages-shortgas-PJM.csv` (1,859 windows, 2020-2025), the matrix row and
all seven cells, the cache-key registration, and four tests. The off path is proved
byte-identical to `origin/main` over 7 ISOs × 4 years × `extract_basis_share` {False, True}.

## §2 — G-DRIFT (rule 29(b)): form 4 holds, and NO control solve is spent

The keeper `pjm_d4_2_TP`'s `meta.git_sha` is `5f133fd5`. Rather than classify the 21 changed
solve-path files hunk by hunk, the question is answered **exactly**, at zero LP, by the object the
question is really about:

> `ScenarioConfig.cache_key()` computed on the keeper's own 833-field `scenario_config`
> **at `5f133fd595aeb8d6c88058b566fce4b4e8b56e19` and at HEAD is the identical
> `725009b54d387c32`.**

Since capx D79 (owner ruling Q54) the key also carries the **solve-surface fingerprint** — a
per-name, per-ISO value hash of the seven `config/solve_surface.py` `SURFACE_MODULES`. An
unmoved key therefore certifies that no registry table, no solve-surface row and no config
default the keeper touches has moved. That is strictly stronger than a hunk-by-hunk audit and
strictly stronger than a control solve, and it costs seconds. **The keeper's committed bundle IS
the control.**

*(Corroborating the same conclusion by inspection: every changed solve-path hunk outside my own
`outages.py` / `arrays.py` / `scenarios.py` edits is another ISO's branch behind its own
default-off gate — SPP `spp_curtailment_ceiling` in `renewables.py` / `runner.py` /
`curtailment_share.py`, NYISO `nyiso_total_east_cutset_ttc` in `pipeline/ttc.py` and
`nyiso_hub_gap_month_level` in `fuel/hubs.py`, CAISO in `model/interchange/`, MISO and SPP
reference data — or forecast-only plumbing a `mode="backcast"` run never enters.)*

## §3 — THE HANDOFF'S RESERVE-DUAL GATE IS RETIRED, ON ARITHMETIC, AT ZERO LP

The handoff pre-registered as the screen's first gate: *"the reserve dual becoming non-zero in
the target hours."* **That gate is unreachable by this mechanism and I can say so before
spending the LP, which is what rule 29 clause 0 asks of a screen.**

The arithmetic, entirely on committed numbers:

| quantity | value | source |
|---|---|---|
| model thermal headroom in the 92 RT > $200 hours | **≈ 19 GW** | ADDENDUM §3 (its own corrected figure, restated against the earlier 43-61 GW error) |
| PJM `pjm_primary` reserve requirement | mean 2,663 MW, **max 4,224 MW** | ADDENDUM §2 |
| availability this arm removes in those same hours | **4,570 MW** | §1 above |
| headroom after the arm | **≈ 14.4 GW** | 19 − 4.57 |

**14.4 GW is still 3.4× the requirement's own maximum.** No reserve balance row can bind against
it, so the dual stays at exactly 0.00 whatever this arm does — and a screen whose gate is
"did the dual move" would spend a PJM year to rediscover a subtraction. **Retiring it is not
lowering a bar to let an arm through: it is refusing to spend an LP on a question already
answered, and the retirement is registered here BEFORE the solve so it cannot be a
post-hoc excuse.** What it costs the card is stated plainly rather than absorbed: **this
mechanism cannot, alone, restore PJM's scarcity price formation through the co-optimisation.**
The co-opt's inertness is a SEPARATE open root cause (inherited item 5), it is about the
headroom's *level*, and it is not closed by a composition repair.

What survives is the handoff's SECOND gate, which is reachable and is the mechanism's real
claim: the model out-generates the CAMPD meter by **+9.7 GW** in those 92 hours (+11.1 GW in
the 26 above $500), and this arm takes 4,570 MW of gas availability out of exactly those hours.

## §4 — THE SCREEN GATES, registered now

Screen year **2022**, by FOOTPRINT (92 tail hours against 6-59 elsewhere; 2022 also carries the
largest measured gas family, 494 windows), never by residual — the same year the PRECOMMIT named.
ONE shard, one year, pinned to this commit's SHA. Control = the keeper's committed bundle (§2).

**S-1 — THE MECHANISM DOES WHAT ITS OWN ARITHMETIC SAYS.** The solved availability envelope must
reproduce the pre-solve delta:
* annual-mean PJM fossil unavailable, arm − control: **+1,185 MW ± 15 %**
* mean over the 92 actual RT > $200 hours, arm − control: **+4,570 MW ± 20 %**

A miss means the consumer is not applying what the extract states, and the arm dies as a wiring
defect.

**S-2 — CONFINEMENT.** Only bins whose `plant_group` is in `outages._SHORT_GAS_GROUPS`
(`CC_REGULAR`, `CC_CHP`, `ST_GAS`, `ST_CHP`) may show any availability difference from the
control. **Zero** COAL, CT_PEAKER, nuclear, hydro, wind, solar or storage availability change.
Any leak is a stacking defect (rule 19 `[R-ONE-MECH]`) and kills the arm.

**S-3 — THE CLAIMED EFFECT, and the only gate that can kill the arm on substance.** The
model-minus-meter thermal over-dispatch over the 92 actual RT > $200 hours must **FALL by at
least 2.0 GW** from its measured **+9.7 GW** (i.e. at least ~44 % of the 4,570 MW removed must
survive rather than being backfilled by other thermal). Below 2.0 GW the LP is simply refilling
the hole from elsewhere in the stack and the composition repair is doing no structural work —
which is a real answer, and the successor (§6) takes over.

**S-4 — NO NON-TARGET LOAD-BEARING FLIP.** On 2022, no criterion outside the target family
(C3a, C3b, C1) may flip PASS → FAIL.

**NOT GATED, IN EITHER DIRECTION: C3a, C3b and C1.** They are the target family and they are
**reported at full magnitude, both signs, regressions included**. Gating the screen on the target
residual is precisely the fitted-mechanism selection rule 1 `[R-STRUCT]` forbids, done one year at
a time. A screen **may kill an arm; it may never promote one** — clearing S-1..S-4 authorises only
the full six-year span (rule 16 `[R-ALLYEARS]`: 2020-2025, six shards, one bundle), never a
keeper.

## §5 — the identification objection is TESTED, not assumed away

Registered in the parent PRECOMMIT §4 as a stage-1 blocker: ERCOT's lane struck a near-neighbour
arm because *"a cycling unit's brief stop can be economic dispatch"* and the only separator it
could see was the unit's metered on/off state (rule 13 pinning). **The gas scope answers it with a
different instrument and the answer is measured, not argued**: the merit-order guard — the unit's
own SRMC against the revealed clearing cost of the capacity that WAS running — removes
**10.8 % of the annual mean and 5.1 % of the tail-hour family** (93 of 494 windows). The derive
CLI *refuses* to emit the gas scope without it. The choice was made **against interest**: both
guarded and unguarded families clear both kill bars, and the guarded — SMALLER — one is what the
committed artifact carries.

Corroboration that the survivors are mechanical rather than economic is a **natural experiment,
not an argument**: over Winter Storm Elliott (Dec 24-27 2022) PJM published FORCED outage of
31,078 / 35,844 / 27,058 / 24,052 MW and the recovered gas family reads
10,998 / 13,611 / 13,297 / 10,158 MW, rising from a 3.0-4.5 GW pre-event baseline. In hours whose
RT averaged **$844**, no unit is idling economically.

## §6 — the successor, if S-3 fails, named before the result

Unchanged from the parent PRECOMMIT §7: PJM's published forced outage may be largely **PARTIAL
derates** — a unit on a forced derate still generates — which a stop-detector cannot see at any
duration. pjm-162 measured a model PARTIAL block of 14,653 MW against a HARD-ZERO block of
27,009 MW. PJM's matrix carries `ercot_partial_outage_shaped_derate` at `·` (n/a) — unbuilt, not
refused. **And §3 adds a second successor with a stronger claim on the price question**: the
co-optimisation's ~19 GW of tail-hour headroom, which no composition repair reaches.
