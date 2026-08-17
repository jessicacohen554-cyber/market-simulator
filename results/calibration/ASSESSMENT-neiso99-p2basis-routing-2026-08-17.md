# ASSESSMENT — neiso-99: the legacy-P2 scoring basis and the Stony Brook outage routing, settled in ONE re-solve

**Date:** 2026-08-17 · **Session:** neiso-99 · **Branch:** `claude/neiso-99-p2-basis-routing-f8asmp`
(off `origin/main` @ `6cc332e`) · **New keeper:** `2026-08-17-neiso-99-joint-p1`
(supersedes `2026-08-17-neiso-97-dstrepair`, **superseded-not-retracted**)

**Pre-registered:** `results/calibration/PREREG-neiso99-p2basis-routing-2026-08-17.md`, committed
and pushed **before either arm solved**.

**Rule 22 `[R-HOLDOUT]` posture:** the holdout spend freeze is **ACTIVE** and was **never
engaged**. No out-of-training year was solved, scored or registered. The measured-input repair is
applied to **every** year consistently ("what is held out is the SCORE, never the DATA"). NEISO's
locked test remains **NEVER GRANTED and NEVER SPENT**.

---

## Verdict in one line

**Both standing owner escalations are CLOSED by one re-solve — the keeper is off the archived P2
pass and the Stony Brook routing defect is repaired — and the determination did not move: 0 FAILs,
C3c the sole ledgered caveat, criterion for criterion identical to the superseded keeper. No gate
was traded.**

---

## 1. What was wrong, and how big it was

### 1.1 O5 — the keeper was SCORED on a pass CLAUDE.md says no keeper uses

NEISO was the only ISO of six whose keeper ran, and was **rendered from**, the archived P2
commitment pass. neiso-84 identified it; neiso-98 proved by two independent routes that the
registered payload came from P2, so every published NEISO number and the scored determination sat
on it. Three keeper generations carried it forward with **no operator decision anywhere**, because
of a seam: `run_replay_bundle` and `replay_keeper.main` rebuild their kwargs from a committed
`meta.json` **after** `_enforce_legacy_p2_gate` has run on parsed CLI args, so `commitment=true`
re-armed the pass invisibly on every replay.

### 1.2 The Stony Brook routing defect — much larger than the escalation implied

`_resolve_unit_group`'s `fac_group` short-circuit was a pjm-75 **conservatism** ("single-group gas
facilities are byte-identical"), not a physical claim. At a facility mixing an oil peaker with a
gas block it hands the peaker's outage window to the block. Measured on the incumbent's own
settings (`cc_steam_part_reclass=True`), capacity-year lost to the mis-routed rows:

| bin | 2023 | 2024 | 2025 |
|---|---|---|---|
| 6081 Stony Brook `CC_REGULAR` (305.1 MW) | 1.0000 → 0.9955 | **0.4872 → 0.0000** | **0.5600 → 0.0000** |
| 1595 Kendall `CC_CHP` (206 MW) | 0.1160 → 0.0192 | 0.1506 → 0.0685 | 0.1374 → 0.0548 |

**In 2024 and 2025 the Stony Brook CC units 001/002/003 have no outage windows of their own at
all** — the entire derate of that block was imposed by two Diesel Oil combustion turbines that are
not in it (83 MW each, 74 windows each). Two further plants were affected the same way: 568
Bridgeport Harbor BHB4 (Other Oil — **absent from the model fleet entirely**) and 1588 Mystic MJ-1.

---

## 2. The fix, and the measurement that stopped a worse one

The obvious repair — route by CAMPD `unitType` — would have been **wrong**. Measured across all
six ISOs' committed extracts (`neiso99_routing_blast_radius.py`), **35** CAMPD units filed
"Combustion turbine" sit in a non-CT bin, and **27 of them are gas-fired members of a genuine
combined-cycle or gas-steam block that must keep inheriting it**: ERCOT Sand Hill SH1–SH7 and
Colorado Bend CT-4A/4B, CAISO Glenarm GT3/GT4, MISO Zeeland CC1/CC2 and Perryville, NYISO
Ravenswood CT0001/0010/0011 and Bethpage GT3, among others.

The guard is therefore **conjunctive**: `unitType` is a combustion turbine **AND** the unit's own
`primaryFuelInfo` is liquid-only (`Diesel Oil` / `Residual Oil` / `Other Oil`, every comma-separated
token — so a dual-fuel `"Natural Gas, Residual Oil"` machine is excluded). That selects exactly the
**8** real peakers and **none** of the 27. **Zero free parameters**: a predicate over a closed CAMPD
fuel vocabulary. The physical claim is checkable — a combined-cycle CT fires pipeline gas into the
block's HRSG and a gas-steam boiler burns its fuel in the boiler itself, so neither can be an
oil-only CT — and the model fleet corroborates it: these machines are `fuel="oil"` rows carrying an
**empty `plant_group`**, or absent from the fleet.

### 2.1 Extract diff, accounted to the row

Standard extract **3,189 → 2,932**, **0 rows added**. The 257 dropped decompose exactly:

* **236** — the fix (all 5 liquid-fuel CT units, every year);
* **21** — reclassified standard → layup, in **2019/2020/2026 only**. A **pre-fix control
  re-derivation at HEAD** reproduces those same 21 and drops **zero** flagged rows, so they are
  ambient HEAD drift, not this change.

All **2,932** surviving rows are byte-identical on every column. **Within 2023–2025 the only change
is the 236 rows.** The BLOAT-S2-untracked CAMPD **2018 vintage was re-fetched first** per the corpus
README, so the re-derivation was not silently short 434 rows (5 of 6 states byte-identical to
`SHA256SUMS`; `CT_2018` carries an EPA revision — the current federal record).

### 2.2 The seam, closed

`enforce_legacy_p2_kwargs` gates the **reconstructed recipe** at both replay entry points and
**hard-fails** rather than silently rewriting it (a silent rewrite is precisely the miso-50..53
lossy-reconstruction class `build_kwargs` exists to prevent). Verified: the incumbent bundle now
refuses to replay without `--enable-legacy-p2` or `--set commitment=false`.

---

## 3. The two arms, and the decomposition

| arm | run id | isolates |
|---|---|---|
| **A** | `2026-08-17-neiso-99-basis-p1` (PROBE) | the P2 → P1 basis change; also the same-HEAD control |
| **B** | `2026-08-17-neiso-99-joint-p1` (**KEEPER**) | basis **+** routing |

Arm A was solved on the **pre-fix** extract via a `MARKET_SIM_DATA_ROOT` shadow root, so the two
arms differ within the solve years by **exactly the 236 rows and nothing else**.

### 3.1 Prediction P1 — CONFIRMED, and it is what makes the arms separable

Arm A's `system` / `class_hourly` / `reserve_family` sidecars are **BIT-IDENTICAL** to the
incumbent's own persisted **P1** in all three years — **0 differing cells** of 43,800 + 122,640 +
26,280 rows per year, max |Δ| 0.0. **P2 never fed back into P1; it was only ever what got
published.** So the basis leg is a pure re-render and every remaining difference between the arms
is the routing repair.

### 3.2 The decomposition, measured

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| **basis** leg — mean λ | −0.0575 | −0.0110 | −0.0378 |
| **basis** leg — annual max | −0.5341 | **−38.687** | 0.0 |
| **routing** leg — mean λ | −0.0162 | −0.0133 | −0.1112 |
| **routing** leg — annual max | 0.0 | 0.0 | 0.0 |
| **joint** — mean λ | −0.0737 | −0.0243 | −0.1490 |

The headline price-formation number: the **2024 annual maximum** of the max-across-zones price is
**$256.93 → $218.24**. Stated the other way — the way audit row O5 stated it — P2 had been standing
**+17.7 %** above P1 on that statistic. *(The prompt's "−18 %" is the same fact with the sign and
base flipped; measured from P2 the move is −15.1 %, measured from P1 the gap was +17.7 %. Reported
here at full magnitude, not tuned around.)*

### 3.3 Prediction P3 — **REFUTED**, and recorded as such

The prereg predicted the routing arm would be driven by Stony Brook's restored block and would
**raise** `CC_REGULAR`. It is driven by **Kendall**, and `CC_REGULAR` **falls**:

| class, routing leg (TWh) | 2023 | 2024 | 2025 |
|---|---|---|---|
| `CC_CHP` | **+0.0532** | **+0.0644** | **+0.0221** |
| `CC_REGULAR` | −0.0535 | −0.0605 | −0.0026 |
| `CT_PEAKER` | −0.0014 | −0.0035 | −0.0193 |

The reason is measurable and already on this lane's record: 6081's heat rate **10.6062** sits above
**97.5 %** of NEISO's `CC_REGULAR` capacity (cap-weighted p50 7.340), so that block is **deep out of
merit whether or not it is available** — exactly what neiso-83 measured at the same plant. Restoring
a fully-available *expensive* block correctly changes its **availability** without changing its
**dispatch** much; the dispatch that moves is the CHP block at Kendall, which outranks merchant CC
on its host steam obligation.

### 3.4 Prediction P4 — the declared risk did not materialise

The prereg declared in advance that, with the model already **below** actual mean λ in all three
years (38.48/39.41, 43.71/44.07, 69.44/71.60), both legs push prices **down** and a C3a/C3b
degradation was therefore expected and would be **accepted** under rules 1 `[R-STRUCT]` and 14
`[R-ACCURATE]` — the accurate input staying in regardless. **In the event no degradation had to be
accepted:** both criteria still PASS. The moves are pennies against a ±10 % band.

---

## 4. Determination — no gate traded

`scripts/calibration_verdict.py --run-id` on **committed artifacts**, no solve:

| criterion | incumbent | **new keeper** |
|---|---|---|
| C1 fuel-mix · C2 volume · C3a mean LMP · C3b shape · C4 dispatch r · C6 governance · C8 forced share | PASS | **PASS** |
| C3c price tail / scarcity | CAVEAT (ledgered) | **CAVEAT (ledgered)** |
| grade | 8 / 7 / 0 / 1 / **0 fails** | 8 / 7 / 0 / 1 / **0 fails** |

**Rule 22 D-5(b) satisfied and not merely asserted:** re-verified against the new run **before** the
re-key commit landed; **not worse — identical**. `scripts/audit_keepers.py --iso NEISO`: **PASS, 0
failures / 0 warnings**, all four scopes.

The attestation generator computes every premise and aborts on failure, including a **hash-level**
one: `meta.json`'s content-addressed `shared_inputs` show the only measured inputs that moved are
`unit_outages` and `unit_outages_layup` — EIA-930, EIA-923, CAMPD and the short/partial/e923
companions are **byte-identical**. DOF ledger (7 entries / 5 residual) and exceptions ledger (7
entries) carried and **asserted** unchanged in count, criterion set and text.

**One inherited text defect repaired, deliberately:** all 7 exception entries attributed their
carry-forward to *caiso-159* — reported by neiso-98 §5, which declined to repair it because editing
a **registered** run's evidence record would falsify what that run asserted. That reason does not
apply to a **new** attestation for a **new** run; the sentence's substance is true of neiso-99
verbatim; and the repair is asserted to be the attribution token and nothing else.

---

## 5. Frontier — RE-ESTABLISHED on the new keeper's own sidecars

**Mandatory, not ceremonial.** Every NEISO keeper change since neiso-93 was a dispatch no-op, so the
declaration could travel on bit-identity. **This one is not**: it changes which pass is scored *and*
a measured availability input. Probe `neiso99_declaration_recheck.py` (which **imports neiso-98's
helpers verbatim**, so the tail definition stays pinned to `render_calibration_html._tail_hours` and
the two sessions' numbers are one measurement) re-derives both legs, with the superseded keeper
re-measured alongside as a control.

* **C3c model tail = 0 h > $300/MWh in 2023, 2024 and 2025 on the now-sole P1 pass** — i.e. the
  declaration now rests on the **production basis**, which is strictly stronger than the
  pass-independence neiso-98 could claim. It **agrees with the registered payload's**
  `ordc.hoursGt200.model` (0/0/0 vs RT actuals 15/8/20).
* **Not a near miss:** annual maxima 248.9682 / 218.2412 / 280.8542 $/MWh; closest approach $280.85
  in 2025, short by **$19.15** (93.6 %). **Bit-unchanged** from the superseded keeper's own P1, so
  **no C3c evidence moved in either direction** — measured, not recalled.
* **RCPF co-optimization DORMANT:** `shortfall_mw = 0.0` and `held_mw ≥ requirement` in **all 78,840
  family-hours**, at requirements checked against `model/reserves/spec.py::NEISO_RCPF_PRODUCTS`
  (1,800 / 1,200 / 600 MW) rather than read off the artifact. **|dual| max is exactly 0.000e+00** —
  the superseded keeper's 1.42e-14 residue was P2's own LP degeneracy noise and left with the pass.

**THE DECLARATION HOLDS.** No C3c lever was opened (rule 28a DO-NOT-REDO on every `R`/`I`/`G` cell).

---

## 6. `complete` — the marker re-keyed, the tier posture untouched

`calibration-complete.json`'s NEISO `keeper` re-keyed to `2026-08-17-neiso-99-joint-p1` with the
determination re-verification recorded, per rule 22 D-5(b) and owner decision D-5(b). NEISO stays in
`complete` and **absent from `final`**; its locked test remains **NEVER GRANTED and NEVER SPENT**.
No 2022 re-iteration is requested — neiso-98 established the DST repair cannot move that
touchpoint's determination, and this session's model-side change is small enough that the same
holds; the better use of the next 2022 spend is still an owner call.

---

## 7. Open, unchanged, and filed

* **C2 still waits** on the final 2025 EIA-923 vintage: the 2025 C1 CC rows stay SKIPPED by design
  (CC_REGULAR 13/30 prior plants missing at 57 % reporting, CC_CHP 3/7). Nothing estimated around it.
* **CC_CHP still sits under actual** where it sat over — a real, ungated residual whose only named
  route is CLOSED WITH EVIDENCE by neiso-71.
* **Filed for other lanes, NOT acted on (rule 25 `[R-ISO-SCOPE]`).** The same guard would drop
  mis-routed liquid-fuel CT rows at **PJM** 593 Edge Moor 10 (33 rows), **MISO** 2001 New Ulm 7
  (114) and 8056 Waterford 4 (103), and **NYISO** 2516 Northport UGT001 (42). Only NEISO's extract
  is re-derived here; each of those is that lane's call, and each needs its own re-solve.
* **Not a NEISO lane item, reported in passing:** `scripts/check_registry_payload_parity.py` fails
  at HEAD on `results/calibration/ercot215_control_A` — a bundle dir mapping to no retained sidecar
  (Class-E retention). Untouched by this session; it belongs to the ERCOT lane.

---

## 8. What this session changed

* `scripts/data/derive_campd_unit_outages.py` — the liquid-fuel CT guard + `_is_liquid_only_fuel`;
  `scripts/data/derive_campd_maxgen_outages.py` — the shared call site.
* `scripts/run_calibration_full.py` + `scripts/replay_keeper.py` — `enforce_legacy_p2_kwargs` and
  the `--enable-legacy-p2` unlock on the replay path.
* `data/raw/campd-unit-outages-NEISO.csv` + `-layup-NEISO.csv` — re-derived.
* `tests/curation/test_derive_campd_unit_outages.py` — 8 new cases for the guard (18/18 pass).
* Two registered runs, the keeper promotion (`keepers/NEISO.json`, `status/NEISO.js`,
  `calibration-complete.json`), the matrix shard + §5.6 prose header, audit row **O5 CLOSED**.
* Probes: `neiso99_routing_blast_radius`, `neiso99_routing_derate_magnitude`,
  `neiso99_arm_decomposition`, `neiso99_declaration_recheck`, `gen_neiso99_attestation` — all
  committed with their JSON records.

**Next shorthand: `neiso-100`.** No NEISO tuning lever is open — the frontier is declared and
re-verified on the production basis. Both long-standing escalations are closed; the lane's remaining
items are the **data wait** (2025 EIA-923) and the cross-ISO routing disclosure above.
