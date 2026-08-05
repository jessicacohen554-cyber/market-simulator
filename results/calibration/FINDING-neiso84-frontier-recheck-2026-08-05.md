# FINDING — neiso-84: NEISO frontier re-assessment on the neiso-83 keeper, and the cross-ISO charter

**Session:** neiso-84 · **Date:** 2026-08-05 · **ISO:** NEISO (rule 25 `[R-ISO-SCOPE]`)
**Keeper assessed:** `2026-08-05-neiso-83-ca1-reclass` (bundle
`results/calibration/neiso83_ca1reclass_B`)
**Supersedes as the current re-verification:**
`FINDING-neiso82-frontier-reassessment-2026-08-04.md`

## 0. Headline

**FRONTIER HOLDS, re-verified on the designated keeper's OWN committed sidecars.
`complete` unchanged. `final` NOT proposable — NEISO's locked test is SPENT and never
re-grantable. Object (a) chartered as a cross-ISO lane with its six-ISO census done.**

**NO RUN WAS PRODUCED IN THIS SESSION** — no LP, no solve, no
`run_calibration_full.py` invocation, no bundle, no dashboard registration. Stated
explicitly per rule 15 `[R-DASHBOARD]` (the neiso-80/82/83 discipline): the registration
duty is not implied-and-skipped, it is **inapplicable** because there is nothing to
register. Every number below comes from committed artifacts only — the keeper's `hourly/`
sidecars, its registered run payload, `scripts/calibration_verdict.py --run-id` (which
reproduces the determination byte-for-byte), the committed CAMPD outage extracts, and a
no-LP `audit_eia923_completeness.py --no-write` re-check.

Rule 22 `[R-HOLDOUT]`: no holdout year of either tier was solved, scored, or touched; the
spend freeze was never approached. Rule 28b: **no mechanism was tested**, so no
`mechanism-matrix.js` cell verdict moves and the matrix is not stamped. Rule 28a honoured
— no closed lever re-opened (no C3c lever, `chp_steam_floor_p25` still unarmed,
`cc_steam_part_capacity` still `I` and not re-stamped, `cc_steam_part_reclass` not
re-tested, Kendall's capacity basis left as ADJUDICATED-ARTIFACT, CC_CHP under-shoot not
re-argued).

**Three carried-forward numbers were found wrong and corrected in place**, and one of them
turned out to rest on a **basis defect worth escalating** (§1.3).

---

## 1. Q1 — Does the 2026-07-11 frontier declaration still hold on the new keeper?

### 1.1 The load-bearing check: YES, on this keeper's own data

The declaration's load-bearing claim is that the in-LP ISO-NE RCPF reserve co-optimization
is **dormant**. Read from `hourly/reserve_family_<year>.parquet` — the **only** artifact in
which a locational reserve family's binding is observable (`system`'s `reserve_price` is
the cross-family SUM broadcast identically to every zone, so it cannot answer this).

| Family | Requirement | Years | Passes | Hours ea | `shortfall_mw` max | `held_mw` |
|---|---|---|---|---|---|---|
| `ne_30min_total` | 1,800 MW | 2023/24/25 | P1, P2 | 8,760 | **0.0** | 1,800 |
| `ne_10min_total` | 1,200 MW | 2023/24/25 | P1, P2 | 8,760 | **0.0** | 1,200 |
| `ne_10min_spin` | 600 MW | 2023/24/25 | P1, P2 | 8,760 | **0.0** | 1,200 |

**157,680 family-hours** (3 years × 8,760 h × 3 families × 2 persisted passes) at exactly
the published static requirements. **No hour goes reserve-short in any of them**, so the
frontier basis has NOT moved.

### 1.2 Correction 1 — the dual is NOT bit-zero on this keeper

neiso-82 recorded "`dual` min = max = −0.0 … zero exceptions" on the prior keeper.
Reproduced on **this** keeper, that wording is not exact:

| Year | Family | Pass | Nonzero-dual hours | max\|dual\| | shortfall |
|---|---|---|---|---|---|
| 2024 | `ne_30min_total` | P2 | 1 | 1.42e-14 | 0.0 |
| 2025 | `ne_30min_total` | P1 | 2 | 2.84e-14 | 0.0 |

**3 of 157,680 family-hours**, at magnitudes of order 1e-14 $/MWh — $0.00 to any
displayable precision, with zero shortfall in every one. These are LP degeneracy noise,
not a binding. They are **new with the arm**: the prior keeper (`neiso81_chpheatrate_B`)
and neiso-83's own zero-delta control arm are both bit-zero across all 157,680.

So **"reserve dual $0.00, no hour reserve-short" is exact and stands**; *"min = max = −0.0,
zero exceptions"* is not, and is corrected rather than carried. neiso-82's text also said
"in BOTH P0 and P1" — the sidecar's own pass labels are **`P1` and `P2`**.

### 1.3 Correction 2 — THE BASIS DEFECT: this bundle is scored on `P2`, and NEISO is the only ISO that does this

While re-deriving §2's model-side numbers I found neiso-82's 2024 figure could not be
reproduced, and traced it to which pass was read. **The bundle persists two passes and the
scored one is `P2`, not `P1`.**

**Verified two independent ways against the registered run payload**
(`frontend/data/backcast/runs/2026-08-05-neiso-83-ca1-reclass.js`):

| Quantity | Payload | sidecar `P1` | sidecar `P2` |
|---|---|---|---|
| HQ_import mean LMP 2023 / 24 / 25 | 38.490 / 43.710 / 70.090 | 38.432 / 43.697 / 70.049 | **38.490 / 43.708 / 70.087** |
| 2025 coal (TWh) | 0.21 | 0.2159 | **0.2108** |
| 2025 gas (TWh) | 61.35 | 61.3427 | **61.3457** |

**Mechanism.** `meta.json` carries `commitment: true`. In
`scripts/run_calibration.py::run_year`, `result_p1` is set non-`None` **only** when
`config.commitment_enabled` — i.e. only when the legacy commitment pass runs — and the
returned `result` is then `_commitment_pass(...)`'s output.
`run_calibration_full.py:4851` labels that final result `"P2"` and the pre-commitment one
`"P1"`. The payload is rendered from the final result. So the archived P2 pass ran and is
the scored artifact.

**NEISO is alone in this.** Census over all 126 committed bundles carrying a `meta.json`:

| ISO | bundles | `commitment: true` |
|---|---|---|
| **NEISO** | 15 | **15** |
| ERCOT / CAISO / PJM / MISO / NYISO | 19 / 20 / 16 / 34 / 22 | **0** |

**Against CLAUDE.md.** *"Dispatch & Commitment"* states P0/P1 are the only two passes,
**"P1 is THE main run … what every run is scored on"**, and of P2: **"No keeper uses it;
it is not part of any default or recommended configuration."** NEISO's designated keeper
does.

**How it survived the gate.** `--commitment` has been hard-gated behind
`--enable-legacy-p2` since 2026-08-03 (`_enforce_legacy_p2_gate`). But that gate runs at
`run_calibration_full.py:10923` on **parsed CLI args**, and `run_replay_bundle` (dispatched
at :10954) re-injects the recipe's flags from `meta.json` afterwards. Every replay
therefore carries the P2 pass forward invisibly — which is how neiso-83, run today,
inherited it.

**Materiality — small but not nil.** 2025 `COAL_BIT` 0.2159 → 0.2108 TWh (−2.3 %); mean
LMP +0.058 / +0.011 / +0.038 $/MWh; the 2024 annual maximum +18 %.

**NOT acted on.** Changing it requires a re-solve, which is outside a no-run
re-verification session and outside this charter. **Escalated to the owner, not silently
corrected.** The determination as scored is unaffected and reproduces byte-for-byte.

---

## 2. Q2 — Is the ledgered C3c caveat still correctly sized and worded?

### Sizing: CORRECT, and basis-independent. Wording: one number was wrong-basis.

Model side re-verified from the keeper's own `hourly/system_<year>.parquet`, on the
**scored (`P2`)** pass, on both an any-zone and a load-weighted basis:

| Year | Model h > $300 | Annual max | Winter (J/F/D) max | Summer (J/J/A) max |
|---|---|---|---|---|
| 2023 | **0** | $249.50 | $233.87 | $88.26 |
| 2024 | **0** | $256.93 | $198.52 | $256.93 |
| 2025 | **0** | $280.85 | $232.92 | $280.85 |

**The asserted model 0 h holds in all three years** — and also holds on the non-scored
pass, so the caveat's sizing does not depend on §1.3's basis question at all. The
determination reproduces exactly: **CALIBRATED-WITH-CAVEATS · 0 FAILs · 1 ledgered caveat
(C3c) · C1 all 12/12 · free 8/8 · C7 SKIPPED (unscored-protective)**. As neiso-82
established and this run confirms, **C3c is a caveat in 2023 and 2025 only** — 2024 is a
PASS on the small-count rule (model 0 h vs RT actual 8 h).

### Correction 3 — the 2024 maximum, twice wrong, now fixed

The attestation's 2024 exception carried *"the energy-only LP tops out at ~$204"*.
neiso-82 corrected that to **$218.24** — but $218.24 is the **non-scored `P1`** pass's
maximum. The scored-pass figure is **$256.93**.

| Source | 2024 max | Status |
|---|---|---|
| original narrative | ~$204 | stale (was already wrong before neiso-82) |
| neiso-82 correction | $218.24 | **wrong basis** (non-scored pass) |
| **this session** | **$256.93** | scored pass, keeper's own `hourly/system_2024.parquet` |

Corrected in place in `calibration_attestation.json`, no re-solve. The edit touches
**exactly 2 lines of 400**; `magnitude`, `magnitude_basis`, every scored value and the
determination are untouched, and `calibration_verdict.py --run-id` re-run after the edit
returns the identical determination and identical criterion set.

### Correction 4 — the sharpening observation survives, but one leg of neiso-82's reading reverses

neiso-82's qualitative point is **right and stronger on the scored pass**: the model's
closest approach to the threshold is SUMMER in all three years.

| Year | Top model hour(s) | Price | % of $300 |
|---|---|---|---|
| 2025 | Jun-24 17/18/19h, Jun-25 16h | **$280.85** | **93.6 %** |
| 2024 | **Jul-15 17:00** | **$256.93** | 85.6 % |
| 2023 | Sep-07 16/17h | $249.50 | 83.2 % |

2025's top-8 still sit entirely on the DA-visible Jun-23/24/25 heat wave the caveat names.

But neiso-82 concluded *"realized winter maxima sit UNDER the ~$258 dual-fuel oil-parity
cap, so the cap is not the binding constraint in the hours the model comes closest."*
On the scored pass, **2024's single closest hour is $1.07 UNDER that cap** — so in the
model's tightest 2024 hour the oil-parity wall **is** effectively the binding constraint.
That reading is reversed. It reached the wrong conclusion because it read $218.24.

This **sharpens** the frontier note's existing pointer — the remaining C3c distance is
summer peak-load-margin offer formation, which already has its own charter — and does not
overturn the declaration. **No C3c lever was re-opened.**

### C2 still waits — re-checked, still not landed

`audit_eia923_completeness.py --year 2025 --no-write` reproduces NEISO's committed block
**byte-identically**: CC_REGULAR 13/30 prior plants missing (57 % reporting), CC_CHP 3/7
(57 %), every NEISO class `gate: false`, both families incomplete. The 2025 C1 CC rows stay
SKIPPED and **nothing was estimated around it**.

`--no-write` was used as instructed and it mattered: the regenerated map carries **6 ISOs
against the committed file's 7 — SPP is dropped entirely**. The committed file was not
rewritten, so the cross-lane MISO/SPP perturbation neiso-82 had to revert never arose.

---

## 3. Q2b — `complete` / `final`, answered explicitly so it is not re-litigated

**`complete` — HELD, unchanged, correctly keyed.** Declared 2026-07-07; `tier_authorized`
is *"validation ONLY (2022 + ladder)"* since the 2026-07-31 two-block split. Its `keeper`
field was re-keyed to `2026-08-05-neiso-83-ca1-reclass` at the neiso-83 promotion **with**
the rule 22 D-5(b) determination re-verification. **This session changes no keeper and
proposes no promotion, so no re-key and no D-5(b) re-verification is due.**

**`final` — NOT PROPOSABLE. Not pending, not deferred: SPENT.** The entry's own
`locked_test` note is unambiguous, and the `final` block's `_note` says the same
independently:

> "SPENT, NOT RE-GRANTABLE. The 2019 + H1-2026 one-shot was scored ONCE with the frozen
> neiso-53 config on 2026-07-07 and STANDS. NEISO is deliberately ABSENT from `final`: the
> locked tier is touch-once, so a spent one-shot must never be re-authorized. **Do NOT read
> the absence as a pending grant.**"

`locked_test_scored_on` (`2026-07-07-neiso53-winter-fuelsec-coldsnap`) is the frozen
config's own record and is deliberately never re-keyed on promotion. **No future NEISO
session should propose, request, or prepare a locked-test spend.**

**The holdout spend freeze outranks both markers and is ACTIVE** (declared 2026-07-25,
`held` 2026-07-26 on the merit-order-guard charter verdict). While active, NO
out-of-training year may be solved, scored or registered for ANY ISO — validation tier
included — even with `--holdout-authorized` and a `complete` marker present. Only the owner
lifts it. So even the *validation* ladder `complete` authorizes is currently suspended.

---

## 4. Q3 — Chartering object (a): the oil-unit `plant_group` gap

**Object (a) is chartered; object (b) is not** (one, per the brief). (a) has measurable
dispatch consequences at multiple plants in four ISOs; (b) was measured by neiso-83 at
0.0022 TWh = **0.11 %** of the ±1.955 TWh C1 band and is a consistency question with no
magnitude behind it. (a) is the better use of a cross-ISO lane.

Full charter: **`docs/handoffs/oil-plantgroup-outage-routing-charter-2026-08.md`**.
Census artifacts: `scripts/probes/_neiso84_oil_plantgroup_census.py` +
`results/calibration/_neiso84_oil_plantgroup_census.json`. **No LP.**

### 4.1 The mechanism, stated exactly

Two code sites, one root cause — `data/fleet/eia860.py` assigns `plant_group` only to coal
and gas, so **every oil unit carries an empty group**:

1. `outages._iso_plant_capacity` skips group-less units
   (`if code <= 0 or not g.plant_group: continue`), so oil capacity is absent from the
   derate **denominator**.
2. `derive_campd_unit_outages._resolve_unit_group` short-circuits at
   `if fac_group in QUALIFYING_PLANT_GROUPS and fac_group != "COAL": return fac_group`
   — **before** it ever consults the unit's own `unitType`. At a plant whose only *modelled*
   group is one gas bin, every non-coal CAMPD unit's outage window lands in that bin.

### 4.2 Census A — the fleet gap, all six ISOs

Units carrying **no** `plant_group` (fleet as the deriver itself loads it: EIA-860 +
`load_retired_within_window`):

| ISO | fleet units | oil units | oil MW | nuclear MW | biomass MW | total un-grouped MW |
|---|---|---|---|---|---|---|
| ERCOT | 1,463 | 292 | 672.6 | 4,980.0 | 150.1 | 5,802.7 |
| CAISO | 808 | 27 | 142.7 | 2,240.0 | 847.3 | 3,230.0 |
| PJM | 2,103 | 469 | 4,465.6 | 33,491.8 | 1,860.2 | 39,817.6 |
| MISO | 2,029 | 589 | 3,339.0 | 11,519.3 | 1,935.5 | 16,793.8 |
| NYISO | 474 | 59 | 2,926.8 | 3,325.9 | 447.4 | 6,700.1 |
| **NEISO** | 454 | **140** | **5,345.2** | 3,355.4 | 1,048.8 | 9,749.4 |

The gap is universal — **1,576 oil units / 16.9 GW across six ISOs** — and NEISO carries
the largest oil share of any ISO (20.6 % of its 25.96 GW fleet). *(neiso-83 quoted 135
units / 5,181.5 MW for NEISO; the difference is `load_retired_within_window`, which the
outage deriver also loads. Both are right for their scope.)*

### 4.3 Census B — actual exposure, and why the naive count over-states it

A raw "oil unit routed into a gas bin" count returns **885 rows at 10 plants** — but that
**over-states the defect**. A dual-fuel oil-fired *steam* unit routed to `ST_GAS` (PJM
Martins Creek 3148, NEISO Montville 546) is **correctly** modelled in that bin. The
discriminator that isolates the real defect is the deriver's *own* `unitType` branches —
precisely the ones the line-509 short-circuit skips:

| ISO | extract rows | matched to CAMPD | oil-in-gas (naive) | **DEFECT rows** | plants |
|---|---|---|---|---|---|
| ERCOT | 53 | 0 | 0 | **0** | 0 |
| CAISO | 4,328 | 4,108 | 0 | **0** | 0 |
| PJM | 10,670 | 10,406 | 312 | **33** | 1 |
| MISO | 10,445 | 10,163 | 217 | **217** | 2 |
| NYISO | 4,423 | 4,386 | 52 | **42** | 1 |
| **NEISO** | 3,189 | 3,045 | 304 | **201** | 2 |
| **total** | | | 885 | **493** | **6** |

ERCOT is **structurally out of the population** — it keeps its bin-sheet group verbatim
(`ugroup = group if iso == "ERCOT"`). CAISO has zero oil exposure.

**Every one of the 493 rows has the same signature: an oil-fired COMBUSTION TURBINE routed
into a steam or combined-cycle bin.**

| ISO | plant | bin | defect rows / total | oil units | CAMPD type | MW |
|---|---|---|---|---|---|---|
| NEISO | **6081 Stony Brook** | `CC_REGULAR` | 148 / 207 | 004, 005 | Combustion turbine | 166.0 |
| NEISO | 1595 Kendall Green | `CC_CHP` | 53 / 77 | S6 | Combustion turbine | 21.0 |
| MISO | 2001 New Ulm | `ST_CHP` | **114 / 114** | 7 | Combustion turbine | 27.5 |
| MISO | 8056 Waterford 1 & 2 | `ST_GAS` | 103 / 143 | 4 | Combustion turbine | 41.0 |
| NYISO | 2516 Northport | `ST_GAS` | 42 / 270 | UGT001 | Combustion turbine | 13.0 |
| PJM | 593 Edge Moor | `ST_GAS` | 33 / 207 | 10 | Combustion turbine | 12.5 |

**MISO 2001 New Ulm is the worst case found: 114 of 114 outage rows — every outage the
plant has — come from a 27.5 MW oil CT routed into the `ST_CHP` bin.**

**neiso-83's NEISO 6081 claim independently confirmed.** Year-scoped row counts from
`campd-unit-outages-NEISO.csv`:

| year | 001 | 002 | 003 | **004** | **005** |
|---|---|---|---|---|---|
| 2023 | 5 | 7 | 4 | 12 | 8 |
| **2024** | **0** | **0** | **0** | **10** | **12** |
| **2025** | **0** | **0** | **0** | **15** | **13** |

In 2024 and 2025 the CC block's own units contribute **zero** outage rows and the diesel
peakers are the sole source — exactly as filed.

### 4.4 The census widened the blast radius — report against interest

The oil gap is one *cause*; the line-509 short-circuit is the shared *mechanism*, and it
mis-routes **far more** than the oil half. Counting **any** `unitType`/bin contradiction,
oil or not:

| ISO | CAISO | MISO | NYISO | NEISO | PJM | ERCOT | **total** |
|---|---|---|---|---|---|---|---|
| any-type mismatch rows | 358 | 735 | 341 | 302 | 140 | 0 | **1,876** |

**~3.8× the oil-only count, and it reaches CAISO, which has no oil exposure at all.** A
charter scoped only to "give oil a `plant_group`" would fix 493 of 1,876 rows and leave the
same mechanism live elsewhere. The charter is scoped to both legs accordingly.

### 4.5 Recommendation

**Charter it as a cross-ISO lane; do NOT fix it in NEISO** — which is what the brief
anticipated, and the census supports it: the defect is in ISO-agnostic code
(`data/fleet/eia860.py`, `data/outages.py`, `scripts/data/derive_campd_unit_outages.py`),
it fires in four ISOs, and any change re-derives committed outage extracts for all six
(rule 23 `[R-FROZEN-DERIVE]` — a re-derivation commit must cite the *data* change, and here
the change is a **code** change, so every affected extract must be regenerated and diffed
deliberately, not as a side effect). NEISO 1595 Kendall appears in the defect set; its
**capacity basis** stays ADJUDICATED-ARTIFACT (neiso-73) — that adjudication is about
capacity, not outage routing, and is not re-opened here.

---

## 5. Governance

| item | status |
|---|---|
| **Rule 1 `[R-STRUCT]`** | No mechanism proposed, armed or tuned. Corrections are to *narrative numbers*, made because they were wrong, not because a residual moved. |
| **Rule 13 `[R-MEASURED]`** | No measured outcome fed back. The census reads published EIA-860 / CAMPD metadata only. |
| **Rule 14 `[R-ACCURATE]`** | §4 keeps the accurate reading and opens the root cause rather than burying it. |
| **Rule 15 `[R-DASHBOARD]`** | **NO RUN PRODUCED — stated explicitly, not left implied.** Nothing to register. |
| **Rule 16 `[R-ALLYEARS]`** | No solve. All re-verification spans 2023 + 2024 + 2025 together. |
| **Rule 19 `[R-ONE-MECH]`** | §1.3 and §4 are filed as open root causes, not stacked as new mechanisms. |
| **Rule 21 `[R-FROZEN-DERIVE]` / 23** | Nothing re-derived. `--no-write` kept the committed completeness map (7 ISOs incl. SPP) byte-unchanged. |
| **Rule 22 `[R-HOLDOUT]`** | No holdout year of either tier solved, scored, or touched. `complete` unchanged and not re-keyed (no promotion). `final` NOT proposable — SPENT. Freeze ACTIVE and never approached. |
| **Rule 25 `[R-ISO-SCOPE]`** | No ISO-agnostic code changed. The only code added is a read-only probe. The cross-ISO census is *measurement*, and §4 explicitly refuses to fix the defect inside NEISO. |
| **Rule 27 `[R-PUSH]`** | Opus. Edits made locally with exact-byte writes; the two JSON edits change 2 lines each with line counts preserved (400 and 13). Every pushed file ≥ 300 lines blob-verified after push. |
| **Rule 28 `[R-MECH-MATRIX]`** | No mechanism tested ⇒ no cell verdict moves (28b). No new `ScenarioConfig` field ⇒ no new row (28c). No `R`/`I`/`G` cell re-opened (28a). The §5.6 lever queue gains the chartered lane. |

## 6. Files

| file | change |
|---|---|
| `results/calibration/FINDING-neiso84-frontier-recheck-2026-08-05.md` | this finding |
| `docs/handoffs/oil-plantgroup-outage-routing-charter-2026-08.md` | the chartered cross-ISO lane (object (a)) |
| `scripts/probes/_neiso84_oil_plantgroup_census.py` + `results/calibration/_neiso84_oil_plantgroup_census.json` | the six-ISO Phase-0 census (no LP) |
| `results/calibration/neiso83_ca1reclass_B/calibration_attestation.json` | corrections 3 and 4 + the `P2`-basis disclosure (2 lines of 400; determination re-verified identical) |
| `frontend/data/backcast/keepers/NEISO.json` | `.frontier.reverified` re-verified on this keeper; `.frontier.carried_forward_through` stamped (2 lines of 13) |
| `docs/mechanism-testing-matrix.md` | §5.6 lever-queue entry for the chartered lane |

`manifest.js` / `benchmark.js` untouched — the Pages deploy is their single writer.
