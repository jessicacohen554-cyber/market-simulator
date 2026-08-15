# ASSESSMENT — neiso-95: the `frontier` and `complete` declarations re-verified on the CURRENT keeper, the stale `disposition_note` repaired, and gap 3 checked downstream

**Session:** neiso-95, 2026-08-15 · **Branch:** `claude/neiso-95-frontier-reverify-gkqw95`
**Keeper:** `2026-08-14-neiso-93-envelope` — **UNCHANGED**; no promotion, no re-key of `keeper`.
**Markers:** `frontier` HELD (2026-07-11) · `complete` HELD (2026-07-07, validation tier) · `final` **EMPTY**
**Ordinal:** the prompt asked to verify against `docs/calibration-log/neiso.md`. It is **neiso-95** —
the neiso-94 entry closes with *"Next shorthand: `neiso-95`"*, and no neiso-95 entry exists. No
divergence to report.

**Freeze:** `frontend/data/backcast/holdout-freeze.json` **VERIFIED ACTIVE AT HEAD** — `"active": true`,
declared 2026-07-25, lifted-and-re-armed 2026-08-06, scope `isos: ALL`, tiers
`[validation, locked_test]`. Read directly, not inferred. **No grant exists and none is inferred.**
NEISO's locked test remains **NEVER GRANTED and NEVER SPENT** (owner decision D-23).

> **NO YEAR WAS SOLVED, SCORED OR REGISTERED — in or out of sample. No LP was constructed.**
> Every number below is read from a committed artifact: the keeper bundle's own hourly sidecars,
> the committed dashboard payload, the committed input parquets, or a git blob. The only 2019–2022
> reads are of **inputs** (§4), which rule 22 as amended 2026-08-06 leaves unrestricted — *"what is
> held out is the SCORE, never the DATA"*. `holdout-freeze.json` and `calibration-complete.json`
> are **unedited**.

**Probes (new, committed):**

| probe | output |
|---|---|
| `scripts/probes/neiso95_declaration_recheck.py` | `results/calibration/_neiso95_declaration_recheck.json` |
| `scripts/probes/neiso95_gap3_chp_downstream.py` | `results/calibration/_neiso95_gap3_chp_downstream.json` |

---

## 0. Headline

| # | task | outcome |
|---|---|---|
| **1** | Re-verify `frontier` on the neiso-93 keeper's own sidecars | **HOLDS.** C3c model tail **0 h** in every year on **both** passes; reserve families zero-shortfall with dual ≡ 0 in all 157,680 family-hours. **No C3c evidence moved.** Re-stamped. |
| **2** | Re-verify `complete` and its D-5(b) re-key | **REPRODUCES EXACTLY.** `calibration_verdict.py --run-id` returns CALIBRATED-WITH-CAVEATS, 0 FAILs, 1 ledgered C3c caveat, grade summary 8/7/0/1 — the marker's recorded numbers. `audit_keepers.py --iso NEISO`: **0 failures / 0 warnings.** |
| **3** | Repair the stale `disposition_note` | **REPAIRED.** Rewritten for the actual current keeper; superseded text preserved verbatim in `prior_keeper_note`. Two of the four disclosed defects are **closed with measurement**. The `calibration-keeper-auditor` re-checked it independently: **PASS, 0 repairs needed** (§3.6). |
| **4** | Gap-3 downstream check | **COVERAGE ONLY, TUNED YEARS UNMOVED.** 2023/2024/2025 partitions plant-for-plant byte-identical; the solve path is vintage-correct per year at both fleet-sourcing branches. One latent seam found, **provably inert** for this keeper. |
| **5** | Re-solve if items 1–4 leave an in-sample delta | **NO DELTA ⇒ NO RUN PRODUCED.** Nothing to register under rule 15. |

---

## 1. Task 1 — `frontier` re-verified on the current keeper's own artifacts

### 1.1 Why this needed doing at all

The `frontier` declaration is dated **2026-07-11**. The keeper has changed **twice** since
(`2026-08-05-neiso-83-ca1-reclass` → `2026-08-06-neiso-87-control` → `2026-08-14-neiso-93-envelope`),
and the shard's `carried_forward_through` field stopped at the **neiso-87** keeper. The declaration
rests on a factual claim — *C3c is the binding frontier and the model tail is identically 0* — that
is a property of a **specific run's output**, so carrying it across two promotions on assertion is
exactly the drift the re-verification is for. It is re-established here from the neiso-93 bundle's
own committed sidecars.

### 1.2 The C3c model tail: 0 hours, on both passes, in every year

Recomputed from `results/calibration/neiso93_envelope_A/hourly/system_<year>.parquet` under the
**pinned** definition the scorer's payload uses — `render_calibration_html._tail_hours`: stack the
per-zone hourly price arrays, map NaN → −∞, count an hour once if the **max across zones** exceeds
the threshold. NEISO's threshold is **$300/MWh** (`calibration_verdict.TAIL_THRESHOLD`).

| year | P1 tail h | P2 tail h | payload `ordc.hoursGt200.model` | RT actual |
|---|---|---|---|---|
| 2023 | **0** | **0** | 0 | 15 |
| 2024 | **0** | **0** | 0 | 8 |
| 2025 | **0** | **0** | 0 | 20 |

The recomputation **agrees with the committed payload**, which confirms the definition is the scored
one rather than a look-alike. Both passes are reported because NEISO is scored on **P2**
(`_primary_pass` prefers P2 where a bundle persists it, and this bundle does — §3.5).

The bundle carries **no `scarcity.parquet`**, so the payload took the fallback branch and the
`overlay` key is absent: C3c scores the **energy-only** LP dual. That is the truthful basis for this
ISO and is unchanged from the superseded keeper.

### 1.3 It is not a near miss — the threshold is never reached in any hour

A "0 h tail" is compatible with two very different situations: a model that keeps grazing the
threshold, or one that never approaches it. This is the second.

| year | pass | max | p99.9 | p99 | mean |
|---|---|---|---|---|---|
| 2023 | P1 | **248.97** | 215.87 | 182.58 | 38.42 |
| 2023 | P2 | 249.50 | 217.70 | 186.29 | 38.48 |
| 2024 | P1 | **218.24** | 198.52 | 149.38 | 43.70 |
| 2024 | P2 | 256.93 | 198.52 | 149.38 | 43.71 |
| 2025 | P1 | **280.85** | 258.98 | 193.09 | 69.40 |
| 2025 | P2 | 280.85 | 258.98 | 193.58 | 69.44 |

(max-across-zones hourly price, $/MWh, all 8,760 h.)

**The whole-run maximum never reaches $300 in any year — closest by $19.15, in 2025.** This is the
dual-fuel oil-parity cap the C3c ledger entry describes (*"the energy-only LP caps the cold-hour
price at ~$258/MWh"*) showing up directly in the price distribution, and it is why the frontier is a
**formation** gap rather than a magnitude one: no amount of moving the model within its current
mechanism set produces a tail hour.

### 1.4 Reserve families: the co-optimization is dormant, measured where it is observable

Read from `hourly/reserve_family_<year>.parquet` — the **only** artifact in which a locational
reserve family's binding is observable (CLAUDE.md rule 15), because `system`'s `reserve_price` is
the cross-family **sum** broadcast identically to every zone.

| family | zones | requirement | static? | shortfall h | held < req h | dual ≠ 0 h |
|---|---|---|---|---|---|---|
| `ne_30min_total` | North\|Central\|Boston\|Connecticut\|HQ_import | 1,800 MW | yes | **0** | **0** | **0** |
| `ne_10min_total` | (same) | 1,200 MW | yes | **0** | **0** | **0** |
| `ne_10min_spin` | (same) | 600 MW | yes | **0** | **0** | **0** |

Identical in **all** of 2023 / 2024 / 2025 × P1 / P2 — **157,680 family-hours** (3 families ×
8,760 h × 3 years × 2 passes), `shortfall_mw` max **0.0**, `held_mw − requirement_mw` min **0.0**,
and `dual` max |·| **1.42e-14** — floating-point noise, i.e. identically zero.

> **The in-LP ISO-NE RCPF co-optimization is DORMANT**, exactly as the frontier note states. It is
> armed and it never binds, because at the published **static** requirements the NEISO fleet is
> never reserve-short. Nothing stacks into the LMP from the reserve side, in any hour of any year.

### 1.5 Did any C3c evidence move? No — and the counterfactual was measured, not assumed

The superseded keeper's own sidecars (`results/calibration/neiso87_control_A/`) were run through the
**same** recomputation: **0 h on both passes in all three years**, and its payload carries the same
`0/0/0` against the same `15/8/20` actuals. neiso-93's measured-envelope repair — which *did* move
prices (§3.3) — left the frontier basis **bit-unchanged in both directions**.

> ### VERDICT: the `frontier` declaration **HOLDS** on the current keeper.
> `frontier.carried_forward_through` is re-stamped to `2026-08-14-neiso-93-envelope` with this
> evidence. **No escalation is triggered**: the prompt's stop condition was "if any C3c evidence
> moved", and none did.

---

## 2. Task 2 — `complete` and the D-5(b) re-key

### 2.1 The determination reproduces from committed artifacts

`scripts/calibration_verdict.py --run-id 2026-08-14-neiso-93-envelope` — **committed artifacts only,
no solve** (the scorer never re-solves the LP and never touches the gitignored dispatch parquets):

| quantity | marker's recorded re-verification | reproduced this session |
|---|---|---|
| determination | CALIBRATED-WITH-CAVEATS | **CALIBRATED-WITH-CAVEATS** |
| FAILs | 0 | **0** |
| ledgered caveats | 1 — C3c price tail / scarcity (RT hourly) | **1 — C3c price tail / scarcity (RT hourly)** |
| C1 free-class | all 12/12 · free 8/8 | **all 12/12 · free 8/8** |
| grade summary | scored 8 / target 7 / commercial 0 / ledgered 1 | **`{"scored": 8, "target_grade": 7, "commercial_grade": 0, "ledgered": 1, "fails": 0}`** |

Every criterion PASSes except C3c, which is the single ledgered caveat: C1, C2, C3a, C3b (load-bearing),
C4 (supporting), C6 and C8 (protective). **The D-5(b) re-verification is reproducible, not merely
asserted** — the entry's own claim that the determination is "IDENTICAL, CRITERION FOR CRITERION, to
the superseded `2026-08-06-neiso-87-control` basis" is the reason the promotion was allowed to
proceed without owner escalation, and it checks out.

### 2.2 M1 passes

`scripts/audit_keepers.py --iso NEISO` → **PASS: 0 failure(s), 0 warning(s)**, across all four
audited scopes (`NEISO` keeper text, `holdout`, `marker`, `status`). Check **M1** — that a `complete`
ISO's marker `keeper` field tracks the shard's current designated keeper — passes: both read
`2026-08-14-neiso-93-envelope`.

### 2.3 One stale clause inside the `complete` entry — reported, deliberately NOT edited

The entry's `locked_test` field still argues, as part of its *"the readiness answer is still NO"*
reasoning, that **"2019 is UNSOLVABLE at HEAD"**. That specific claim was **withdrawn** by neiso-88
and neiso-90, and neiso-94 §3.2 re-confirms the withdrawal at the post-neiso-93 HEAD (*"the audit
re-confirms every solve-path input resolves for 2019"*).

**The conclusion the clause supports is unaffected** — neiso-94 finds `final` still **DO NOT GRANT**
on two live reasons (2019 cannot exercise C3c; the Pilgrim gap), neither of which is the solvability
claim. **Not edited here**, for two reasons: this session's authority over `calibration-complete.json`
is the D-5(b) *re-key* verification, not a rewrite of the owner's `locked_test` reasoning; and the
field is load-bearing governance prose about a **never-granted** locked test, where the conservative
posture is to leave the owner's own text alone and surface the drift. **Flagged for the owner or a
governance lane.**

---

## 3. Task 3 — the stale `disposition_note`, repaired

### 3.1 The defect, confirmed before repairing it

neiso-94 §6 reported it and deliberately left it. Confirmed here by diffing the shard across the
neiso-93 promotion: `keeper`, `prior_keeper_note` and `note` all changed; **`disposition_note` is
byte-unchanged.** Under the current keeper it therefore:

- named the wrong superseded run — *"criterion for criterion identical to the superseded
  `2026-08-05-neiso-83-ca1-reclass` keeper"*, when the superseded keeper is now
  `2026-08-06-neiso-87-control`; and
- disclosed **defect (i)**, the stale Aug-2025 gas-basis row, as a live defect of *"THIS KEEPER"* —
  which the keeper's own sidecar refutes.

Over-conservative rather than over-claiming, and the determination was never affected — but a reader
of the shard alone would draw a false conclusion about the current keeper.

### 3.2 What the repair did

Three fields changed in `frontend/data/backcast/keepers/NEISO.json`; **every other field is
byte-identical** (verified by flattened key-by-key comparison: 17 of 20 leaf fields unchanged, key
order preserved):

1. **`disposition_note`** — rewritten to describe the actual current keeper.
2. **`prior_keeper_note`** — the superseded disposition text **appended verbatim**, under a labelled
   header recording why it moved. **Preserved, not deleted**: it remains a *correct* description of
   `2026-08-06-neiso-87-control` as promoted.
3. **`frontier.carried_forward_through`** — re-stamped (§1).

`scripts/build_status.py --iso NEISO` rebuilt `status/NEISO.js`; `status/shared.js` is unchanged
(the rubric did not move). No other ISO's files were touched (rule 25).

### 3.3 Defect (i) — CLOSED, with the measurement

The prior keeper was arm A of the neiso-87 Aug-2025 basis A/B and carried the stale `NEISO,2025,8`
gas-basis interpolation (**+0.04**) against HEAD's measured **−0.38**. This keeper is the re-solve at
HEAD that the prior shard's own standing recommendation called for. Measured on the committed
`hourly/system_<year>.parquet`:

| year | superseded keeper | current keeper | note |
|---|---|---|---|
| 2023 | 38.4324 | **38.4215** | −0.0109 |
| 2024 | 43.6971 | **43.6970** | essentially bit-identical |
| 2025 | 69.7149 | **69.3989** | −0.3160 — **the predicted 69.399** |

Basis: unweighted mean of the P1 energy dual over zone-hours. The load-weighted companion moves
71.9228 → **71.5412** in 2025. The repair is bounded to one month of one year, exactly as disclosed.

### 3.4 Defect (ii) — CLOSED

The prior bundle was registered **without** `legitimacy_diagnostics.json`, so C8 scored SKIPPED and
the file had to be generated at promotion. This bundle's `legitimacy_diagnostics.json` was committed
in the **registration commit itself** — `git log` puts it in `2cf773c` ("neiso-93 Phase B: re-solve
the keeper in-sample on the corrected envelope"), the same commit as `meta.json`. **C8 scores PASS
on artifacts that shipped with the run.**

### 3.5 Defects (iii) and (iv) — carried forward, and RE-CHECKED rather than assumed

- **(iii)** CC_CHP under actual, and the 2025 C1 CC rows SKIPPED on the preliminary EIA-923 vintage
  (13/30 CC_REGULAR and 3/7 CC_CHP prior plants missing, 57 % reporting) — both visible in this
  session's verdict output. The **neiso-83 open root-cause issue was re-checked at HEAD**:
  `data/raw/campd-unit-outages-NEISO.csv` still routes plant **6081** Stony Brook's units **004** and
  **005** (the DIESEL peakers) to `plant_group=CC_REGULAR` — **74 outage rows each** — because `oil`
  carries no `plant_group` at all. Still open, still unfixed, still derating a fully-available CC
  block on outages of machines that are not in it.
- **(iv)** **NEISO is still the only ISO of six running the archived P2 commitment pass** —
  re-checked on this bundle's own `meta.json`, which carries `commitment: true` and
  `passes: ["P1","P2"]`, and it is scored on P2. The neiso-84 escalation is neither resolved nor
  worsened. **Open for the owner**; resolving it needs a re-solve.

### 3.6 The `calibration-keeper-auditor` re-checked the repair independently — **PASS, 0 repairs**

Run after the repair, scoped `--iso NEISO`. It **independently reproduced every specific claim**
this session wrote into the shard, from the committed artifacts, and **found no drift and changed
nothing**:

- the determination and `grade_summary` `{scored 8, target 7, commercial 0, ledgered 1, fails 0}`;
- 0 tail hours in every year on both passes, and the un-rounded P1 maxima **248.9682 / 218.2412 /
  280.8542** behind this assessment's 248.97 / 218.24 / 280.85;
- the decoded payload's `ordc.hoursGt200` = `{0, 15}` / `{0, 8}` / `{0, 20}`;
- 157,680 reserve-family rows, `shortfall_mw` all 0.0, `held_mw ≥ requirement_mw` in 100 % of rows,
  static 1,800 / 1,200 / 600 MW;
- 2025 unweighted P1 mean 69.3989 vs the superseded bundle's 69.7149;
- `legitimacy_diagnostics.json` and `meta.json` committed together in `2cf773c`;
- `meta.json` `commitment: true`, `passes ["P1","P2"]`;
- the gap-3 artifact figures, re-derived directly from the parquet;
- **and, at the JSON-value level, that the shard diff touches exactly the three intended fields** —
  the raw `git diff` line noise is unicode-escaping variance, not content.

It also confirms `build_status.py --check --iso NEISO` reports *"status parts in sync"*, and that
`calibration-complete.json` already names the current keeper (M1a/M1b satisfied by the neiso-93
promotion). **It reported one refinement, adopted here and in the shard**: the reserve `dual` is
zero to floating-point noise (max |·| **1.42e-14**), not literally `0.0` — stated that way rather
than rounded, so the artifact and the prose agree.

### 3.7 Defect (v) — added, and explicitly scoped OUT of the tuned years

The 2019 **Pilgrim** fleet-vintage gap (neiso-93 found it, neiso-94 adjudicated it) is now recorded
in the shard. It is stated there as what it is: **a 2019-only blocker that does not touch 2023–2025**,
because `RETIREMENT_WINDOW_START = 2023` means every affected plant retired before the training
window and is availability-zero within it. The repair is **cross-ISO** (264 plants / 21.5 GW across
all six) and belongs to `docs/handoffs/fleet-vintage-retiree-window-charter-2026-08.md`. **It is not
a NEISO lane item and this session did not touch it** — per the prompt's instruction.

---

## 4. Task 4 — gap 3's downstream check

**The question:** neiso-93 extended `data/raw/_processed-legacy/eia860_chp_by_year.parquet` to
2018–2025. Is the CHP classification the **solve path actually consumes** vintage-correct per year,
and are the 2023–2025 rows unmoved — i.e. did gap 3 change **coverage**, not the tuned years?

**Answer: yes to both. Coverage only.** Three legs.

### 4.1 Leg A — the artifact, plant for plant

Against the pre-extension blob (`git show 20c2a4b^:`, the parent of the gap-3 commit):

| year | plants before → after | index identical | values identical | CHP=Y before → after |
|---|---|---|---|---|
| 2023 | 12,477 → 12,477 | ✓ | **✓** | 879 → 879 |
| 2024 | 13,371 → 13,371 | ✓ | **✓** | 861 → 861 |
| 2025 | 14,189 → 14,189 | ✓ | **✓** | 848 → 848 |

Rows grew **40,037 → 92,633**; years **[2023–2025] → [2018–2025]**. **All 52,596 new rows are in
2018–2022.** The tuned years are byte-identical.

### 4.2 Leg B — the reader

`market_sim.data.chp._chp_by_plant(dir, year)` returns **that year's own row** for all eight covered
years (verified against the artifact partition, year by year), and the snapshot fallback
(`year=None`, 14,189 plants) is a genuinely **distinct** series:

| year | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|---|
| plants whose flag differs from the snapshot | 45 | 37 | 31 | 23 | 20 | 15 | 5 | **0** |

The monotone decay to exactly 0 at 2025 is the expected signature — 2025 **is** the snapshot vintage —
and it confirms the vintage path is live rather than silently falling back.

### 4.3 Leg C — the fleet, and the solve path

`scripts/run_calibration.py` passes the solve year at **both** of its fleet-sourcing branches: the
per-plant bin synthesis (`load_fleet_from_csv(..., year=year)`, line 2943) and `build_base_fleet(...,
vintage_year=year)` (line 2969), which forwards it into `load_fleet_from_csv` on both of its own
branches. **The backcast's CHP classification is vintage-correct per solve year.**

NEISO fleet CHP composition, built through that loader:

| vintage | CC_CHP | CT_CHP | ST_CHP |
|---|---|---|---|
| 2019–2021 | 23 u / **739.0 MW** | 44 u / 254.2 MW | 17 u / 73.2 MW |
| 2022 | 23 u / **739.0 MW** | 45 u / 257.5 MW | 17 u / 73.2 MW |
| 2023 | 20 u / **494.0 MW** | 45 u / 257.5 MW | 17 u / 73.2 MW |
| 2024–2025 | 20 u / **494.0 MW** | 46 u / 267.5 MW | 19 u / 79.3 MW |

**The extension is materially live where it was meant to be, and the instance is nameable.** NEISO
plant **10726 — Masspower**, 3 CC units, **245 MW**: `chp = Y` through 2022, `chp = N` from 2023. It
is the whole CC_CHP step. Before gap 3, a 2019–2022 solve would have read the 2025-era snapshot and
classed those 245 MW as **CC_REGULAR**; now they are **CC_CHP**, with that class's BTM host pull-out,
must-run floor and heat-rate treatment. That is precisely the mis-vintaging gap 3 existed to close.

Because leg A shows the 2023–2025 partitions are byte-identical and leg B shows the reader is a pure
function of (year → artifact row), the tuned-year fleet **cannot** have moved. Confirmed by
construction rather than by a redundant re-solve.

### 4.4 One latent seam found — reported, PROVABLY INERT here, not fixed

`market_sim.data.fleet.eia860._dual_fuel_plant_groups(eia860_dir)` takes **no year parameter at
all**. It keys its `(plant_code, plant_group)` dual-fuel pairs off `_chp_by_plant(dir)` — the
**un-yeared snapshot** flag. A plant whose vintage CHP flag differs from the snapshot therefore gets
a dual-fuel key built on `CC_REGULAR` while the fleet carries it as `CC_CHP` (or vice versa), so the
key silently fails to match and **the unit loses its dual-fuel pairing**. That matters for NEISO
specifically, whose winter price formation runs on dual-fuel oil parity.

**It does not bite this keeper.** Of the nationally-differing plants in the tuned years —
15 (2023) / 5 (2024) / 0 (2025) — **none is in the NEISO fleet**, in any of the three years. NEISO's
fleet matches 47 / 49 / 49 dual-fuel pairs and every one is correctly keyed. In 2019–2022 the seam
would reach exactly one plant: Masspower again.

**Reported, not fixed.** It is ISO-generic and would need its own scoped change plus a six-ISO
in-sample proof; fixing it here would be an unrequested mechanism change in a session whose remit is
re-verification, and rule 1 `[R-STRUCT]` makes it a structural question, not a residual one.

---

## 5. Task 5 — no run produced

**Items 1–4 left no in-sample delta**, so under the prompt's own condition **no solve was run and
nothing was registered**:

- the tuned-year CHP artifact partitions are byte-identical (§4.1) and no other input changed;
- the determination re-verifies unchanged from committed artifacts (§2.1);
- `audit_keepers.py --iso NEISO` passes 0 / 0 (§2.2);
- the frontier basis recomputes to the same 0 h tail and the same dormant reserve families (§1);
- the changes this session made are **text and stamps in a keeper shard** — they cannot change a
  solve.

Rule 15 `[R-DASHBOARD]` is not engaged: **there is no run to register.** Rule 16 `[R-ALLYEARS]` is
likewise not engaged.

---

## 6. Data blocker, recorded and not chased

The `final` grant's **H1-2026 half stays hard-blocked**:
`data/raw/_validation-source/actual_lmp_hourly_NEISO.parquet` carries **2018–2025 and no 2026 rows**,
and `bench/NEISO/` holds 2022–2025. There is nothing to score H1-2026 against. That intake is
**unrestricted** under rule 22 (data, not score) but is **not this session's task** — noted, not
pursued, per the prompt.

---

## 7. Deliverables

| deliverable | path |
|---|---|
| This assessment | `results/calibration/ASSESSMENT-neiso95-declaration-recheck-2026-08-15.md` |
| Frontier/`complete` re-verification probe | `scripts/probes/neiso95_declaration_recheck.py` |
| — its machine output | `results/calibration/_neiso95_declaration_recheck.json` |
| Gap-3 downstream probe | `scripts/probes/neiso95_gap3_chp_downstream.py` |
| — its machine output | `results/calibration/_neiso95_gap3_chp_downstream.json` |
| Repaired keeper shard (NEISO only) | `frontend/data/backcast/keepers/NEISO.json` |
| Rebuilt status part | `frontend/data/backcast/status/NEISO.js` |
| Calibration-log continuation | `docs/calibration-log/neiso.md` |

---

## 8. Rule compliance

| rule | status |
|---|---|
| 1 `[R-STRUCT]` | No mechanism armed, tested or proposed. §4.4 declines to fix a seam on the grounds that it is a structural change needing its own proof, explicitly not on any residual argument. |
| 12 `[R-PARALLEL]` | Not engaged — no solve. |
| 13 `[R-MEASURED]` | No measured outcome fed back. The keeper's own sidecars are read to **verify** declarations and disclosed defects; nothing is pinned, tuned or fed back. |
| 14 `[R-ACCURATE]` | §4 confirms the more accurate per-vintage CHP input is the one the solve path consumes. §3.5 keeps the 6081 outage-routing inaccuracy on the record as an open root cause rather than burying it. |
| 15 `[R-DASHBOARD]` | **No run produced ⇒ nothing to register.** No solve of any kind. |
| 16 `[R-ALLYEARS]` | Not engaged — no bundle produced. |
| 22 `[R-HOLDOUT]` | **Freeze VERIFIED ACTIVE at HEAD and never engaged. NO year solved, scored or registered — 2019, 2020, 2021, 2022 and H1-2026 all untouched.** `holdout-freeze.json` and `calibration-complete.json` are **unedited**; the `final` block was not read for a grant and not written. §4's 2019–2022 reads are of **inputs only**, unrestricted under the 2026-08-06 amendment. D-5(b) re-verification reproduced from committed artifacts with no solve. NEISO's locked test remains **NEVER GRANTED and NEVER SPENT**. |
| 23 `[R-FROZEN-DERIVE]` | No derive script re-run and no measured-behaviour parameter re-derived. |
| 24 `[R-REGISTRY]` | No tunable touched; no `ScenarioConfig` field added or changed. |
| 25 `[R-ISO-SCOPE]` | **NEISO files only.** `keepers/NEISO.json` + `status/NEISO.js` (`status/shared.js` unchanged). No other ISO's shard, keeper, marker or matrix cell edited. |
| 27 `[R-PUSH]` | Opus session (`claude-opus-5`). No file was bulk-rewritten from regenerated response content. The only existing file ≥300 lines touched is `docs/calibration-log/neiso.md` (2,409 → 2,521 lines), **append-only**; `keepers/NEISO.json` is 36 lines and was edited programmatically in place, with a flattened key-by-key diff proving 17 of 20 leaf fields byte-identical and key order preserved. Every push sends the exact local on-disk bytes and is followed by a blob verification of the ≥300-line files. Both probes and the assessment are new files. |
| 28 `[R-MECH-MATRIX]` | **No mechanism tested ⇒ no cell verdict minted** (duty d). No `ScenarioConfig` field added ⇒ duty (c) not engaged. No lever opened, no `R`/`I`/`G` cell re-tested; the NEISO queue stays cleared. |

---

## Appendix — reproduction

```
uv run python scripts/probes/neiso95_declaration_recheck.py
uv run python scripts/probes/neiso95_gap3_chp_downstream.py
uv run python scripts/calibration_verdict.py --run-id 2026-08-14-neiso-93-envelope
uv run python scripts/audit_keepers.py --iso NEISO
uv run python scripts/build_status.py --iso NEISO
```
