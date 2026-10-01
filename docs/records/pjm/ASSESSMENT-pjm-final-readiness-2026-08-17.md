# ASSESSMENT — PJM `final` (locked-test) readiness under rubric v3.3

**Session:** iso-final-readiness (PJM/NYISO/NEISO sweep) · **Date:** 2026-08-17 ·
**HEAD:** `d1932e8` · **Branch:** `claude/iso-final-readiness-assessment-gx3iei`
**Keeper:** `2026-08-15-pjm-162-inputclock` (bundle `results/calibration/pjm_debugb_inputclock_A`)
**Markers:** `complete` HELD (2026-07-31, re-keyed 2026-08-16) · `final` **EMPTY** ·
**Freeze:** `holdout-freeze.json` **ACTIVE** at HEAD (`"active": true`, re-armed 2026-08-06).

**THIS DOCUMENT GRANTS NOTHING AND SPENDS NOTHING.** No year — in or out of training — was
solved, scored or registered. No LP was constructed. Every number below is a committed
artifact, an on-disk measured input, or a published actual. Input inspection is unrestricted
under rule 22 as amended 2026-08-06 (*"WHAT IS HELD OUT IS THE SCORE, NEVER THE DATA"*); the
spend is looking at an out-of-training answer, which nothing here does. Granting the locked
tier is the owner's separate, explicit act.

---

## 0. Recommendation

> ## **NOT YET.** On the merits.

PJM's keeper is genuinely CALIBRATED and its status does **not** depend on the v3.3 amendment
(§1) — of the three ISOs in this sweep, PJM is the only one whose determination is carried by
criteria that actually pass. That is real standing. It is not sufficient, because `final` is
touch-once and three independent things are still true:

| # | ground | status |
|---|---|---|
| 1 | **H1-2026 is unsolvable at HEAD** — `load_demand('PJM', 2026)` raises. Half the locked tier cannot be built at all (§3.1). | **blocking** |
| 2 | **The validation tier below it is unresolved.** PJM's only touchpoint (2022) scored **NOT-YET** and was never re-tested; 2021 and 2020 have never been run, and **2020's demand feed is defective** (new measurement, §4). Spending touch-once while the iterable tier is open inverts the ladder. | **blocking** |
| 3 | **The freeze is ACTIVE** and its stated lift condition is unmet (§3.4). | **blocking, owner-level** |

Carried forward from `ASSESSMENT-pjm162-final-readiness-2026-08-15.md` §2 and unchanged by
v3.3: the **DA-virtual escalation**, 2019 net DA virtual position **+7.08 TWh** against
−0.82 / −2.11 / −0.84 in the training years — 2019 is a *2022-like* year for that layer.

**What v3.3 changed for PJM: nothing.** The keeper carried zero caveats before the amendment
and carries zero after; the v3.3 block's own measured effect list records PJM as UNCHANGED.

**One genuinely good piece of news, and it is not enough on its own:** 2019 is *solvable* for
PJM at HEAD, and 2019 C3c would *discriminate* (§3.2–§3.3). PJM is the best-prepared of the
three ISOs for a 2019 spend. The blockers are the ladder and the freeze, not the year.

---

## 1. Determination — confirmed independently, and it is **not** a v3.3 artifact

`python3 scripts/calibration_verdict.py --run-id 2026-08-15-pjm-162-inputclock`, committed
artifacts only, no solve, run at HEAD this session:

> **CALIBRATED** · scorable years 2023, 2024, 2025

| criterion | tier | verdict |
|---|---|---|
| C1 fuel-mix by class (grid-delivered) | LOAD | **PASS** |
| C2 system volume (gas/coal families) | LOAD | **PASS** |
| C3a mean LMP | LOAD | **PASS** |
| C3b price duration/shape | LOAD | **PASS** |
| C3c price tail / scarcity (RT hourly) | SUPP | **PASS** |
| C4 fleet hourly dispatch correlation | SUPP | **PASS** |
| C6 governance gate | PROT | **PASS** |
| C8 forced-energy share (D-2) | PROT | **PASS** |

D-10 free-class C1: **all 16/16 · free 12/12**. **Zero caveats, zero FAILs.**
Determination basis, verbatim: *"all criteria pass, governance attested."*

**Is CALIBRATED carried by the v3.3 caveat re-reading, or by criteria that actually pass?**
**By criteria that actually pass.** There is no ledgered caveat on this run for v3.3 to
re-read. The determination basis line names no caveat, `caveats.ledgered` is empty, and the
run reads CALIBRATED identically under v3.2 and v3.3. This is corroborated by the amendment
block's own measured effect statement (`scripts/calibration_verdict.py` v3.3 note): six
determinations changed, two of them keepers — NYISO and NEISO — and *"CAISO/ERCOT/MISO/PJM are
UNCHANGED"*.

Four C8 **grounded-above-budget report notes** (CT_PEAKER 2023/2024/2025 at 16.2/16.4/16.7 %,
ST_GAS 2025 at 39.9 %) are clean PASSes under rule 21's grounded-pass clause — all binding
mechanisms clear D-4 and every profile clears the D-1 shape gates (r 0.897–0.974, off-peak CV
ratio 0.703–2.238). They are notes, not caveats, and they do not bear on this recommendation.

## 2. Rule 22 D-5(b) re-key — verified, no drift, no repair required

`python3 scripts/audit_keepers.py` → **PASS: 0 failure(s), 0 warning(s)** across all six ISOs
plus the `holdout` / `marker` / `status` checks.

| check | PJM state |
|---|---|
| `complete.PJM.keeper` | `2026-08-15-pjm-162-inputclock` — **matches the current designated keeper** |
| `complete.PJM.determination` | re-verified 2026-08-16 without a solve, criterion-for-criterion; **not worse** than the superseded basis (identical) |
| `keeper_at_declaration` | `2026-07-30-pjm-140-rampenv` — preserved |
| check **M1** | **PASS** |

**No drift found; nothing was edited in PJM's shard or anywhere else.**

## 3. `final` readiness on the merits

### 3.1 H1-2026 is unsolvable — a hard blocker on half the locked tier

Data-layer resolvability probe (no LP built, no model output produced):

```
PJM 2026: BLOCKED  ValueError: No EIA-930 data for ISO 'PJM' in year 2026
```

`eia_demand_profiles.parquet` carries **2021–2025 only, for every ISO**
(306,600 rows = 7 ISOs × 5 years × 8760). The locked tier is *2019 **and** H1-2026*; one of
its two years cannot be dispatched. Separately, `actual_lmp_hourly_PJM.parquet` carries **no
2026 rows at all** (2018–2025), so even a solvable H1-2026 would be unscorable for PJM —
unlike NYISO and NEISO, which do hold 4,343 h of 2026 actuals.

### 3.2 2019 **is** solvable — and this corrects the record

Contrary to the cross-ISO reading inherited from `ASSESSMENT-neiso87-declaration-2026-08-06.md`
§3.1, PJM's 2019 demand resolves cleanly at HEAD. PJM does not read the demand-profile table:
it has per-BA extract wiring (`_load_pjm_hourly_demand`, `PJM2019_hrl_load_metered.csv`).

| year | shape | system peak | annual energy | zero hours |
|---|---|---|---|---|
| **2019** | (8, 8760) | **157,644 MW** | **831.9 TWh** | 0 |
| 2023 | (8, 8760) | 152,352 MW | 824.8 TWh | 0 |
| 2025 | (8, 8760) | 163,033 MW | 876.1 TWh | 0 |

A dense, plausible, full-8760 series in family with the training years. **2019 demand is not a
blocker for PJM.**

Other 2019 scoring inputs: `calibration_reference.json` **has a PJM 2019 block** ✓;
`PJM_2019_renewable_capacity.csv` **exists** ✓. `actual_tail.json` has **no 2019 row** — but
that is by construction, not a gap: `scripts/data/derive_actual_tail.py` sets
`ALLOWED_YEARS = holdout_policy.CALIBRATION_YEARS` and emits an out-of-training row only when
the ISO holds that year's tier marker. The row materializes when `final` is granted. It is
correctly fail-closed, not missing.

### 3.3 2019 **would** discriminate on C3c — the strongest case of the three ISOs

Actuals-only, from the committed `actual_lmp_hourly_PJM.parquet` hub series. No model output
involved. `TAIL_THRESHOLD["PJM"] = 200.0`, `TAIL_SMALL_COUNT = 10`, band `[0.5×, 2.0×]`.

| year | 2018 | **2019** | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|---|
| RT h > $200 | 31 | **14** | 2 | 23 | 92 | 6 | 18 | 59 |
| RT mean $/MWh | 34.15 | **25.44** | 20.24 | 37.14 | 68.79 | 28.44 | 29.53 | 42.89 |
| RT max $/MWh | 523 | **672** | 341 | 536 | 3,543 | 631 | 439 | 1,722 |

2019's actual count is **14 ≥ TAIL_SMALL_COUNT**, so C3c would be scored on the **ratio band**,
not the degenerate small-count rule: the model would have to land in **7–28 hours** to pass. It
is a genuine two-sided test. This distinguishes PJM sharply from NEISO (0 actual hours → free
PASS) and NYISO (1 hour → one-sided only).

**So the argument against spending PJM's 2019 is not that the year is useless. It is that the
run it would be spent on carries unrepaired artifacts and sits above an unresolved rung.**

### 3.4 The freeze is ACTIVE and outranks the markers

`frontend/data/backcast/holdout-freeze.json`: `"active": true`, declared 2026-07-25, HELD
2026-07-26, narrowly lifted and re-armed twice (2026-08-05, 2026-08-06). Scope `isos: ALL`,
tiers `[validation, locked_test]`. Its basis — the CAMPD economic-layup residual over-count
surviving the merit-order guard — is unchanged. `run_calibration_full.py` checks the freeze
**before** the marker and fails closed. No session lifts it by inference.

## 4. Touchpoint loop (rule 22) — PJM is stalled at step 2/3, and 2020 is defective

| rung | run | determination | state |
|---|---|---|---|
| **2022** | `2026-08-05-pjm-2022-touchpoint` | **NOT-YET** | **unresolved AND stale** |
| **2021** | — | — | **never run** |
| **2020** | — | — | **never run — and blocked by a data defect (below)** |

**2022 — what it surfaced, and why the loop did not close.** Degraded out-of-sample:
**C1 fuel-mix `CC_REGULAR` +18.28 TWh** and **C3b price duration/shape NRMSE 0.206**. Held:
C2, C3a, C3c, C4, C6, C8. Envelope parity was verified, so the degradation is not explained by
worse holdout data. Loop step 2 (diagnose) ran and produced a named object — the DA-virtual
layer, `+11.12 TWh` of net virtual demand cleared in 2022. But **step 3 (re-train on 2023–2025)
and step 4 (re-test) never completed**: `docs/calibration-log/pjm.md` §pjm-162 records the
arithmetic as having **no passing combination** (−8.9 TWh virtual-phantom removal vs +5 to
+7 TWh seam repair, against a +18.28 TWh miss), and the candidate mechanism showed the textbook
*fixes-2022-breaks-training* signature (CC_REGULAR −16.06 / −13.84 TWh in-sample, four times
outside the band). **The rung is open.**

**And the touchpoint is stale.** It was measured on the **pre-repair input clock**; the keeper
has since moved to `2026-08-15-pjm-162-inputclock`, which *is* that repair. The registered
2022 record stands as scored, but it no longer measures the current frozen recipe.

**NEW FINDING — the PJM 2020 demand feed is defective.** Measured this session from
`load_demand('PJM', y)` (no LP, no model output):

| year | system max | p99.9 | **max / p99.9** | annual energy | h > 165 GW |
|---|---|---|---|---|---|
| 2019 | 157,644 | 151,110 | 1.04 | 831.9 TWh | 0 |
| **2020** | **197,438** | **148,785** | **1.33** | **809.6 TWh** | **2** |
| 2021 | 153,412 | 151,915 | 1.01 | 834.0 TWh | 0 |
| 2022 | 152,376 | 147,488 | 1.03 | 842.0 TWh | 0 |
| 2023 | 152,352 | 148,449 | 1.03 | 824.8 TWh | 0 |
| 2024 | 156,367 | 151,970 | 1.03 | 845.6 TWh | 0 |
| 2025 | 163,033 | 159,483 | 1.02 | 876.1 TWh | 0 |

Three independent signatures that this is a metered-feed artifact and not real load:

1. **Two corrupt hours.** `2020-07-27 11:00` at **197,438 MW** and `2020-07-28 15:00` at
   **181,841 MW**, against a third-highest hour of 151,534 MW — a ~30–46 GW discontinuity.
   Both exceed PJM's all-time system peak (~165 GW, 2006).
2. **An implausible peak hour.** An annual peak at **11:00** is not a PJM summer peak shape;
   the real peak window is 16:00–18:00.
3. **A systematically inflated year.** *Every* zone's 2020 annual max exceeds both 2019 and
   2021 — zone 6 reads **42,339 MW** against 33,449 / 33,437 (**+27 %**) — while 2020 has the
   **lowest annual energy in the record** (COVID). Peak up 27 %, energy down: incoherent.

**Consequence:** the 2020 rung is not merely un-run, it is **not data-ready**. Solving it as-is
would dispatch against two impossible hours in exactly the scarcity-formation window C3c
gates. This is the neiso-85 failure mode (a single absent/defective measured input dominating
the residual with a known sign) and it should be repaired by data prep — which needs no marker
and no lift under rule 22's 2026-08-06 clarification — before any 2020 spend is requested.

## 5. What would change the answer

1. The owner **lifts the freeze**, or closes the merit-order-guard charter with cause.
2. The **DA-virtual architecture question is decided** — including a ruling that the layer
   stays as-is with the +7.08 TWh 2019 artifact disclosed in advance.
3. The **2022 rung is dispositioned** — resolved, or explicitly closed by the owner as a
   known-and-accepted open rung rather than left silently open.
4. **H1-2026 is made solvable** (demand-profile coverage past 2025) *and* PJM 2026 hub actuals
   are intaken — or the owner explicitly scopes PJM's locked test to 2019 alone.
5. The **PJM 2020 demand feed is repaired** (data prep, unrestricted), so the validation ladder
   can actually be walked.

Items 4 and 5 are data prep and need no grant. Items 1–3 are owner decisions.

---

*Precedent for a NOT-YET-on-the-merits recommendation:
`results/calibration/ASSESSMENT-neiso87-declaration-2026-08-06.md`.
Immediate predecessor for PJM: `ASSESSMENT-pjm162-final-readiness-2026-08-15.md` (pre-v3.3);
this assessment re-confirms its NOT YET under v3.3 and adds §3.2, §3.3 and the §4 2020 finding.*
