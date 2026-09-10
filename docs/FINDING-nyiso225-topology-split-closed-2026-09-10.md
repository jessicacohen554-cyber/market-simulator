# FINDING — nyiso-225: the topology split is CLOSED AT PHASE 0, and the 2022 arm is REJECTED BY OWNER RULING

**Session:** nyiso-225 (parent / orchestrator) · **ISO:** NYISO · **Date:** 2026-09-10
**Keeper:** `2026-09-09-nyiso-221-fuelvintage-span`, **UNCHANGED**.
**ZERO LP. Zero shards launched. No `ScenarioConfig` field, constant, derive script or
model artifact changed. No run produced, so none registered** (rule 15 `[R-DASHBOARD]`
registers runs; a no-LP session registering nothing is correct, not an omission).

**Predecessor:** `docs/RESULT-nyiso224-total-east-cutset-2026-09-10.md` /
`docs/PRECOMMIT-nyiso224-total-east-cutset-2026-09-10.md`.
**Control:** the committed keeper bundles `nyiso_fuelvintage_A` (2023–25) and
`nyiso_fuelvintage_H2` (2022), plus the preserved arm bundle on branch
`claude/nyiso224-cutset-2022` — rule 29(b) form 4 throughout, **no control solve spent**.

---

## 0. The headline, in three lines

nyiso-224 confirmed the 2022 object by solve and named a **topology split** as the successor,
requiring owner sign-off because it changes the ISO's zone count.

**Phase 0 kills it before it costs anything, on NYISO's own postings: there is no nested PAIR
of constraints to separate, because only ONE of the pair is ever a constraint.** Central East
is the only internal NYISO interface that binds at all. Total East — the boundary the whole
successor was built around — is ≥95 % loaded in **0.01 %** of 2022 hours and **0.00 %** in
2023, 2024 and 2025, in **both** flow directions.

**Owner ruled 2026-09-10: accept the kill and go to the queue; reject the nyiso-224 arm as
constructed.** Both are executed here.

---

## 1. The binding census — every posted internal interface, every year, both directions

Binding = hourly flow ≥ 95 % of that hour's **own posted** limit, from the committed MIS P-32
archive (`data/raw/NYISO/interface-flows/`). The ±9,999 MW "unbounded" sentinel is dropped, so
`WEST CENTRAL` — which carries the sentinel in 100 % of hours — has no limit to bind against.

| interface | 2022 | 2023 | 2024 | 2025 | reverse direction |
|---|---|---|---|---|---|
| **CENTRAL EAST - VC** | **10.01 %** | **4.36 %** | **2.50 %** | **3.62 %** | no negative limit posted |
| TOTAL EAST | 0.01 % | 0.00 % | 0.00 % | 0.00 % | no negative limit posted |
| MOSES SOUTH | 0.00 % | 0.00 % | 0.00 % | 0.00 % | **0.00 %** (−1,600 MW, posted 100 %) |
| DYSINGER EAST | 0.02 % | 0.00 % | 0.00 % | 0.00 % | no negative limit posted |
| UPNY CONED | 0.31 % | 0.00 % | 0.00 % | 0.00 % | no negative limit posted |
| SPR/DUN-SOUTH | 0.00 % | 0.03 % | 0.01 % | 0.00 % | no negative limit posted |
| WEST CENTRAL | — | — | — | — | sentinel limit, never constrained |

**One interface binds. Everything else is a monitored cutset, not a constraint.**

## 2. Why that closes the topology split — three independent legs, any one sufficient

**(a) There is no nested pair to hold.** The successor's premise is that the model's one link
must represent two nested boundaries, Central East *inside* Total East. §1 says Total East is
not a boundary the market is ever held at. The model already carries the one boundary that is
(Central East, with an already-measured, already-rule-14-grounded TTC), so the representation
it is accused of lacking is a representation of a constraint that does not exist.

**(b) The split that could separate the legs is already CLOSED at G0 with cause.** Central East
is the C/E → F cutset; the parallel non-CE leg of Total East (mean **1,626 / 1,677 / 1,461 /
1,465 MW**, remarkably stable while `MOSES SOUTH` swings from **+1,352** to **−188 MW** — so it
is *not* Moses South, corr **0.238**) bypasses zone F into zone G. **Both legs leave the same
upstate zone**, so no split of A–E separates them; the separation is on the **receiving** side,
at F|G. `docs/handoffs/nyiso-124-charter-g0-g1-2026-08-04.md` §2.1 closed exactly that split:
**no F/G transfer limit exists** in MIS P-32, in **36 months** of MIS ATC/TTC, or in any of the
**four** Gold Book editions on disk, and quantity 3 (`ext_G`, the zone-G share of the eastern
seam) is unrecoverable. **DO-NOT-REDO honoured** (rule 30(a)): this session's new 2022
*incidence* evidence — F is the **dearest zone in New York** at 97.02 vs G's 84.65, and F−G
widens to **32.86** in the market's own CE-binding hours, far above the 0.36–2.65 nyiso-124
measured in 2023–25 — is a bigger basis, and **a bigger basis does not create a published
limit**. The G0 refusal is on identifiability and it stands untouched.

**(c) The split that IS identifiable is provably inert.** Splitting inside A–E along
`DYSINGER EAST` / `MOSES SOUTH` (both posted, so quantity 2 passes there) creates links whose
limits bind in **0.00–0.02 %** of hours. The new zones would be price-identical by
construction: LP columns and a zone-count change bought for a measured zero. There is real
congestion inside A–E — **$13.66/MWh** of the $17.28 mean max-min spread is the published
congestion component, not losses — but **no posted limit produces it**, which is nyiso-124's
quantity-2 failure again, on the upstate side.

## 3. The nyiso-224 arm — new evidence, and the ruling

Differenced against the preserved bundle on `claude/nyiso224-cutset-2022` (rule 29(b) form 4;
the bundle's own `network_2022.parquet` and `system_2022.parquet`). **No solve.**

**The frequency match was a coincidence of aggregates.** The RESULT recorded, carefully, that
the armed link binds in 12.47 % of hours against a market sub-cutset binding at 10.0 %, and
declined to claim it as a pass. Phase 0 shows it should not have been: measured hour by hour,

| | value |
|---|---|
| arm binds | 1,122 h (12.81 %) |
| market CENTRAL EAST binds | 877 h (10.01 %) |
| **hours BOTH bind** | **71** |
| expected if statistically independent | 112.3 |
| **lift** | **0.63× — anti-correlated** |
| precision (armed hours that are real) | **6.3 %** |
| recall | 8.1 % |

**The arm congests in the wrong hours, and slightly *avoids* the right ones.** No re-quantiling
of a limit can repair hour-level anti-correlation — which is a stronger and more useful reason
not to chase the envelope than rule 1 `[R-STRUCT]` (c)'s governance refusal alone, and it is a
measurement rather than a rule.

**And the rent is 14× short.** In the market's own binding hours the measured (F,G)−(A–E) basis
is **$82.54**; the arm's `Capital_Hudson − Upstate_West` in its binding hours is **$6.03**, on a
mean |dual| of **$3.36/MWh**. The arm's link runs at **67.4 %** mean loading.

**OWNER RULING 2026-09-10 — REJECT AS CONSTRUCTED.** `nyiso_total_east_cutset_ttc` stays
`False`, armed by nobody; the matrix cell stays **R**, annotated with the evidence above. The
confirmed object stands as nyiso-224's durable result. Under rule 31 `[R-RETAIN]` trigger (i)
the preserved bundle is now releasable; it is left on its branch regardless, at no cost, and
**that branch must not be merged to `main`** (rule 29(c)).

## 4. What phase 0 found instead — recorded, NOT chartered

The 2022 defect reproduces nyiso-124 §6.1's 2023–25 seam diagnosis, now on the arm's own
committed bundle. The model's east-of-cutset border links sit **at their upper bound**:

| model link | mean MW | limit | at bound |
|---|---|---|---|
| `NYISO_external>Long_Island` | 906.0 | 906.3 | **99.6 %** |
| `NYISO_external>NYC` | 880.0 | 886.1 | **98.6 %** |
| `NYISO_external>Capital_Hudson` | 253.9 | 280.1 | **93.7 %** |
| `NYISO_external>Upstate_West` | 1,218.7 | 2,421.9 | 12.6 % |

≈ **2,040 MW delivered east of the cutset as a flat, price-insensitive block in ~99 % of
hours**, against measured east-side schedules averaging **1,476 MW net** — a net that includes
`SCH - NE - NY` at **−400.3 MW**, i.e. New York *exporting* to New England on average, a
direction the model's east-side seam never takes. With 2 GW of infra-marginal import always
present, the east rarely needs the west (wrong congestion hours) and never reaches the
expensive downstate unit when it does (rent 14× short).

**This is recorded as evidence, not opened as a lever.** The seam cells are already adjudicated
**K** (`seam_flow_envelopes`, `nyiso_seam_par_attribution`, `priced_interchange`), and
nyiso-125's identification refusal on the `Capital_Hudson` and `Upstate_West` border links —
`SCH - PJ - NY` is the one posting row spanning the Central-East cutset and neither NYISO's
P-32 nor PJM's tie file separates the legs — is load-bearing and unmoved. The owner ruled this
lane to the queue; a seam charter would need its own phase 0 and PRECOMMIT.

## 5. Governance

- **Rule 1 `[R-STRUCT]`** — structure decided this, not the residual. The arm was rejected
  holding an 11-point C3a gain, and the successor was killed on a binding census, not a fit.
  `authorized_price_tuning` = **NONE**.
- **Rule 13/14 `[R-MEASURED]` / `[R-ACCURATE]`** — every number here is measured off committed
  postings; the F|G refusal is identifiability, which a larger measured basis cannot cure.
- **Rule 21 `[R-DOF]`** — zero free parameters proposed; an F/G limit would be a chosen number,
  which is why (b) refuses it.
- **Rule 29 `[R-SCREEN]`** — **phase 0 did its whole job**: an arm with a computable pre-solve
  gate never reached a solve, and the gate killed the route for ~0 LP against a ~17-min span.
  G-CTRL form 4 throughout; **no control solve spent**.
- **Rule 30 `[R-MECH-MATRIX]`** — `NYISO.js` re-stamped this session; no new row (no new
  mechanism was created).
- **Rule 31 `[R-RETAIN]`** — nothing deleted; the promotion question was put and is now RULED.
- **Rule 32 `[R-SHARD]`** — the parent ran no LP. Nothing earned a shard, so none was launched.

## 6. Reproduce

`scripts/probes/_nyiso225_topology_phase0.py` (committed) regenerates §1–§4 from
`data/raw/NYISO/interface-flows/`, `data/raw/lmp-data/NYISO/` and the two sidecars on
`claude/nyiso224-cutset-2022`. Record: `results/calibration/_nyiso225_topology_phase0.json`.
