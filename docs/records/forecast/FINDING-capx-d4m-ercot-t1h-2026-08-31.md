# FINDING — capx D4-M: the post-arming ERCOT T1-H, and the D4-I3 pre-declaration graded

**Lane:** capx D4-M · **Model:** Opus · **Branch:** `claude/capx-d4m-ercot-t1h`
**Charter:** the D4-M prompt (r#21 batch) · **Graded object:**
`docs/handoffs/FINDING-capx-d4i3-ercot-slack-2026-08-31.md` §4 (P-1..P-8, F-1..F-4, FROZEN)
**Date:** 2026-08-31 · **ONE solve** (ERCOT T1-H, years sequential in one invocation, rule 12).

**SCOPE BOUNDARY.** Card Y-C respected: the net-revenue half of the I3 object is HELD and is
not touched, measured or re-opened. The R-2 entry-volume calibration is a later lane and is
not begun here — no volume parameter was moved, and none may be fitted to close I3 (rule 13
`[R-MEASURED]`). Non-ERCOT I3 rows (MISO, NEISO) are their own ISO lanes' (rule 25).

---

## 0. Headline

1. **The pre-declaration HELD on direction and on every structural claim, and MISSED LOW on
   every magnitude.** I3 FAILs worse than the control, the 2024 breach opens, 2025 stays clean,
   the build collapses to ~28 GW — all as predicted. But 2023 slack is **0.12 %** against the
   predicted ~0.07 %, 2024 is **0.03 %** against ~0.02 %, reserve margin is **4.8 % / 5.5 %**
   against ~6.1 % / 6.8 %, and I14 is **$228.0** against ~$168.7. Every miss is in the same
   direction: **worse than pre-declared.** (§3)
2. **No falsifier fired** — F-1, F-2, F-3, F-4 all no-fire on their literal terms. F-3 came
   closest: 0.1156 % against its ~0.15 % ceiling, 77 % of the way there. (§4)
3. **But the run contradicts §2.2(a)'s volume→slack reading in the mirror image of F-4, and
   this is the lane's most useful result.** Against `d12c-armed` the model built **MORE**
   (28.587 vs 27.837 GW, +2.7 %) and the 2023 slack got **65 % WORSE** (0.1156 vs 0.07 %).
   Under a pure volume account that is backwards. The composition channel §2.2(b) measured at
   ~0.03 pp is here **larger than the volume channel it is netted against**. (§5)
4. **The posture measured is NOT the posture the pre-declaration was written for.** The
   registered ERCOT default at HEAD carries **four** armed levers, not two: owner ruling R-A
   (2026-08-31) flipped both storage-entry repairs to default-`True` the day after D12-A armed
   the pair, and `d12c-armed` ran both `False`. This is stated as a limit on the grade, not as
   a reason to adjust any prediction. (§2)
5. **The R-5 shared-cache-key hazard is no longer a hypothesis — this run demonstrates it by
   construction.** My solve computes cache key **`f061b2646bfaac8b`**, byte-identical to
   `d12c-armed`'s, while running a provably different posture. D4-I3 §5.1 could not separate
   its two candidates zero-solve; candidate **(i) is now proven possible in this exact key**,
   because the mechanism is visible in the config rather than inferred. (§6)
6. **R-4 landed first and paid for itself immediately.** The 2024 breach is **35 h deep to
   12,632 MW peak**; the 2023 breach is **185 h shallow to 8,203 MW**. 2024 is the *deeper*
   event on a *third* of 2023's energy — a shape distinction the old `% of load` instrument
   could not express at all, and the single most informative thing this run says. (§1, §5.2)
7. **This run closes a WATCH ITEM the mechanism matrix carries on four cells**: "no registered
   bundle sits at that posture — composed-by-construction, UNMEASURED." It does now. (§8)

---

## 1. STAGE 1 — R-4, the instrument grain (landed before the run was scored)

`check_i3_unserved_dump`'s slack leg now emits breach hours, slack GWh and peak slack MW
alongside `% of load`. Commit `afc79934`, pushed and blob-verified (rule 27).

```
-                problems.append(f"{year}: slack {slack_e / dem_e:.2%} of load")
+                grain = _slack_grain(yd.result.slack, slack_e)
+                problems.append(f"{year}: slack {slack_e / dem_e:.2%} of load {grain}")
```

with `_slack_grain` summing the `(n_zones, T)` slack column over zones, so one hour short in
two zones counts as one system breach hour, and

```
+    slack_report_hour_mw: float = 1.0
```

added to `Thresholds` with its citation (rule 5 `[R-NO-MAGIC]`).

**What was deliberately NOT done.** The `1e-4` `slack_frac_of_demand` gate is untouched; no
year's PASS/FAIL moves. The new threshold gates **only** the reported hour tally and reuses
this file's standing numerical-noise floor (`energy_balance_mw`, `accounting_close_mw`,
`reliability_slack_mw` are all 1.0 MW) rather than introducing a tuned quantity. `slack_e` is
passed into the reporter instead of recomputed, so the verdict arithmetic and the reported GWh
cannot drift apart. Rule 13 N/A, rule 21 N/A — reporting only, no re-solve, no free parameter.

**Tests** (`tests/regression/test_forecast_invariants.py`, trivial fixture first per CLAUDE.md):
a clean year PASSes; hours/GWh/peak are reported on a 2-breach-hour fixture; two zones short in
one hour count as **one** system hour; and sub-MW dust is excluded from the tally but **not**
from the fraction — that last one guards the only real hazard here, that the reporting floor
could become a second gate. Four pass; `ruff` clean.

**Scope of effect.** Committed sidecars keep their coarse strings — the grain is not
reconstructible from them. So the two grains coexist for now, and an ERCOT I3 magnitude stays
comparable only within a solve vintage (D4-I3 §5.1). This lane's run is the first ERCOT record
at the fine grain.

---

## 2. STAGE 2 — the run, and the posture actually measured

`scripts/run_capacity_hindcast.py --iso ERCOT --start-year 2021 --end-year 2025 --vintage 2020
--fuel-variant realized` — a bare invocation at HEAD, no lever flags, years sequential in one
invocation (rule 12). Solved `[2021, 2023, 2024, 2025]`, bridged `[2022]`. Registered
`ercot-2021-2025-realized-t1h-d4m`, provenance `scored_at_sha afc799347bfd`, `cache_epoch
f061b2646bfaac8b`.

### 2.1 POSTURE ASSERTION (F-1's first clause) — from the run's OWN `run_config.json`

| field | value |
|---|---|
| `entry_margin_exhaustion` | **True** |
| `entry_forward_reserve_leg` | **True** |
| `entry_lookahead_reprice` | True |
| `screen_reserve_value_enabled` | True |
| `mode` | forecast |

**Both D12-A fields are armed.** F-1's escape clause ("first check the run's own
`run_config.json`") is therefore spent: any contradiction found below is real, not a posture
error.

### 2.2 …AND TWO MORE FIELDS THE PRE-DECLARATION'S BASIS DID NOT CARRY

| field | this run | `d12c-armed` (the pre-declaration's basis) |
|---|---|---|
| `storage_entry_availability_gate` | **True** | **False** |
| `storage_entry_cost_normalized_rank` | **True** | **False** |

Owner ruling **R-A** (director sitting 2026-08-31, "Arm both") flipped both to
`ScenarioConfig` default-`True` — **the day after** Q15/D12-A armed the entry pair, and
**after** the D4-I3 pre-declaration was frozen. A bare invocation at HEAD is therefore a
**four-lever** posture. The charter is right that "a bare invocation IS the armed posture";
what it could not know is that the armed posture had grown by two fields.

**This matters quantitatively, not pedantically.** The committed `capentry` A/B measured that
storage pair alone moving 2023 slack **0.01 % → 0.04 %** at *identical* build MW and an
*identical* per-tech GW split — a 4× effect on zero MW of volume difference. So P-2/P-3/P-5/P-7,
all read off `d12c-armed`, are point predictions for a posture that no longer exists and that
no committed record measures.

**How this lane handles that.** The predictions are graded **exactly as written**, at full
magnitude, against what was measured. They are not re-based, re-centred, or re-interpreted —
the charter freezes them and this lane grades them. The superset posture is reported as a
**stated attribution limit on every magnitude row**, and §5 does the attribution work
explicitly rather than letting it sit inside a miss.

---

## 3. STAGE 3 — the P-1..P-8 grade table

Measured, `ercot-2021-2025-realized-t1h-d4m`. Control = the committed
`ercot-2021-2025-realized-t1h-d12c-control` (zero-solve, per charter).

| # | pre-declared | measured | grade |
|---|---|---|---|
| **P-1** | I3 FAILs, worse than control | **FAIL**; 2023 slack **0.1156 %** vs control 0.01 % (**≈ 12×**) | **HELD** |
| **P-2** | 2023 slack ≈ **0.07 %** (≈7× control) | **0.1156 %** (≈ 11.6× control) | **MISS — 1.65× predicted, direction right** |
| **P-3** | 2024 breach opens, ≈ **0.02 %** | **0.0334 %** (control clean) | **HELD in kind; magnitude 1.67× predicted** |
| **P-4** | 2025 stays clean | **0.0001 %** — 2 h, 0.4 GWh, peak 201 MW; far under the 0.01 % gate | **HELD** |
| **P-5** | build ≈ **27.8 GW**; RM ≈ **6.1 % / 6.8 %** | build **28.587 GW** (+2.7 %); RM **4.75 % / 5.50 %** | **build HELD; RM MISS (−1.35 / −1.30 pp, both low)** |
| **P-6** | composition super-additive vs exhaustion-only | 2024 breaches at RM 5.50 % under the composed posture, where the committed exhaustion-only arm is clean at RM 11.6 % | **CONSISTENT — but NOT independently measured here** (no exhaustion-only twin solved in this lane; the committed evidence is unchanged) |
| **P-7** | I14 2023 LW ≈ **$168.7** | **$228.0** | **MISS — 1.35× predicted, direction right** |
| **P-8** | T1-F 2027-2030 breach widens | — | **UNMEASURED.** No T1-F run in this lane; its own charter flags it UNBRACKETED, so it is recorded unmeasured rather than estimated (charter directive). |

### 3.1 The full measured record

**I3** (at the new R-4 grain, this run's novel content):

| year | slack % of load | GWh | breach hours | peak slack MW | load TWh |
|---|---|---|---|---|---|
| 2021 (seed, never scored) | 0.0077 | 30.0 | 10 | 8,816 | 391.3 |
| **2023** | **0.1156** | **515.7** | **185** | **8,203** | 446.0 |
| **2024** | **0.0334** | **154.5** | **35** | **12,632** | 462.6 |
| 2025 | 0.0001 | 0.4 | 2 | 201 | 487.8 |

**Everything else:** I1 PASS (max |supply−demand| 1.164e-10 MW), I2/I4-I11/I13 PASS. I12 WARN
(out: 2023 4.8 %, 2024 5.5 %). I14 WARN (2023 LW $228.0 vs CC MC $23.9). **No invariant fails
here that did not fail on the control** — the FAIL set is `{I3}` in both.

**Additions**, model vs actual GW: wind 0.350 / 12.663 · solar 15.916 / 25.080 · gas_cc 6.000 /
0.244 · gas_ct 3.571 / 3.692 · storage 2.750 / 13.691. Total **28.587 / 55.436**.
**Retirements 0.000 GW modelled against 2.294 GW actual** — unchanged across every committed
arm, so the deficit remains entirely entry-side (D4-I3 §2.2(a)).

---

## 4. Falsifiers — none fired

| | condition | outcome |
|---|---|---|
| **F-1** | I3 PASSes, or slack ≤ control | **NO FIRE.** FAIL at ≈12× the control; both D12-A fields asserted `True` from the run's own config (§2.1). |
| **F-2** | a 2025 breach appears | **NO FIRE.** 2025 is 0.0001 % — 2 hours, 0.4 GWh. |
| **F-3** | 2023 slack > ~0.15 %, or below the control | **NO FIRE** — but this is the close one: **0.1156 % is 77 % of the way to the ceiling**, and the four-lever posture (§2.2) is not the one F-3 was written against. A future run at this posture could cross it without anything new being wrong. |
| **F-4** | build differs materially from ≈27.8 GW **while slack still matches** P-2/P-3 | **NO FIRE on its literal terms.** Build does *not* differ materially (+2.7 %); slack does *not* match. The measured pattern is F-4's **mirror image** — see §5, which is where the substance is. |

---

## 5. The result that matters: composition beat volume

### 5.1 The arithmetic

| | build GW | 2023 slack | 2023 RM |
|---|---|---|---|
| `d12c-control` (committed) | 39.908 | 0.01 % | 8.5 % |
| `d12c-armed` (committed) | 27.837 | 0.07 % | 6.1 % |
| **`d4m` (this run)** | **28.587** | **0.1156 %** | **4.75 %** |

D4-I3 §2.2(a) — the finding's own **load-bearing claim** — is that slack is monotone in the
year's total added GW. Between `d12c-armed` and this run the model built **0.750 GW more** and
the 2023 slack got **65 % worse**. Under a pure volume account that is the wrong sign.

**This is not a refutation of §2.2(a), and I am not claiming one.** §2.2(b) already carved
composition out of the volume attribution, and §2.2(a) is a within-posture claim across build
levels. What the run shows is a **magnitude** correction: §2.2(b) measured the duration channel
at ≈0.03 pp and treated it as the small residual around a first-order volume story. Here it is
**≈0.05 pp and it has to overcome a volume move pushing the other way** — so at this posture
composition is the *larger* channel, not the residual. The framing "under-build is the
first-order cause" understates it.

### 5.2 …and the R-4 grain shows the two breaches are not the same event

2023 is **185 h shallow** (8.2 GW peak, 515.7 GWh); 2024 is **35 h deep** (12.6 GW peak,
154.5 GWh). 2024 reaches a **54 % higher peak** on **30 % of the energy**. A `% of load`
reading ranks 2023 as 3.5× the worse year; the grain says they are different failures — 2023 a
sustained capacity shortfall, 2024 a short extreme-hour one. Any repair aimed at the wrong one
would be aimed by the coarse number. This is R-4's first dividend and it arrived on the first
run that carried it.

### 5.3 Attribution — mechanism, and what I could NOT verify

The only posture delta from `d12c-armed` is the R-A storage pair (§2.2). Storage **power** is
identical in both at 2,750 MW. This run's storage build is, from its own evolution ledgers,
**100 % `li_ion_4hr` — 2,750 MW × 4.0 h = 11.0 GWh**. The committed `capentry` A/B established
that the *unarmed* screen picks iron-air + flow battery (64 h fleet) where the *armed* screen
picks 4 h/8 h li-ion. Same MW, far less stored energy, fewer scarcity hours covered, more slack
— §2.2(b)'s duration mechanism exactly.

**What I cannot verify, stated as such:** `d12c-armed`'s bundle commits only `score.json` and
the screen-signal `.npz` — **no evolution ledgers** — so its storage duration is
**inferred-with-mechanism, never measured**. This is precisely the gap NEISO-RC-R R4 closed for
crossover bundles and which plain-hindcast bundles still carry. Until a bundle at that posture
commits its ledgers, the attribution in this section is a mechanism argument, not a measurement.

**And this run inherits the same gap, which I am not fixing in-lane.** `.gitignore` (lines
667/676-677) commits the *slim set* for a plain hindcast — `meta.json` + `run_config.json` +
`score.json` + sidecar + report — and tracks `evolution_*.json` only for `*crossover*` bundles.
Extending that to plain hindcasts is a **tracked-set change**, which is what NEISO-RC-R R4 was
chartered to make for its own class; this lane is not chartered for it, so it is **routed**
(§10 item 4), not taken. The consequence is that my own ledgers are untracked too, so the
duration figures above — **2,750 MW, 100 % `li_ion_4hr`, 4.0 h, 11.0 GWh, read from
`evolution_2023.json`** — are recorded *here, in prose*, as the durable record. A reader who
needs to re-derive them must re-solve at `f061b2646bfaac8b`; and per §6 that key alone will not
tell them which posture they are getting.

### 5.4 A comparability caveat the charter's design forces

D4-I3 §5.1 is binding: **an ERCOT I3 magnitude is comparable only within a solve vintage.**
Every A/B delta in §5.1's table above is **cross-session** — `d12c-control` and `d12c-armed`
scored at `bf5e08f50f0d` on 2026-08-30, this run at `afc799347bfd` on 2026-08-31 — i.e. exactly
the class §5.1 warns about. That is not a defect of this measurement; it is a **structural
consequence of the charter mandating a zero-solve committed control**, and it should be
weighed before any of §5.1's deltas is read as a pure model effect. A same-session control
re-solve is the only thing that removes it, and it was not in this lane's scope.

---

## 6. R-5 upgraded from hypothesis to demonstrated mechanism

D4-I3 §5.1 found five committed records sharing key `28cef3500ec1fd9e` with disagreeing I3, and
left two candidates open — (i) the key carried two solves, (ii) the scorer changed — declaring
neither provable zero-solve.

**This run proves candidate (i) is realizable in this exact key.** My solve's cache key is
**`f061b2646bfaac8b`**, byte-identical to `d12c-armed`'s, while running a demonstrably
different posture (`storage_entry_availability_gate` / `storage_entry_cost_normalized_rank`
`True` here, `False` there — both recorded in the two `run_config.json` files). The mechanism
is not inferred: both fields are `_CACHE_KEY_OPTIONAL_FIELDS` members, so `cache_key()` drops
them at whichever value is the **live** default — `False` when `d12c-armed` solved, `True` now.
Same key, two different dispatches, **by construction**.

`src/market_sim/results/cache.py`'s own 2026-08-31 epoch predicted this in terms
("**FORECAST: NO KEY MOVES, AND THAT IS THE HAZARD** … the recurrence that epoch's closing note
predicted"). It is now observed.

**Consequences the director should have:**
- **This run was not itself corrupted.** `results/ERCOT/` was empty in this container, so
  nothing stale was served and the solve is genuinely fresh. The hazard is to *readers*, not to
  this dispatch.
- **The board now carries two runs at one `cache_epoch`** — `d12c-armed` and `d4m` both stamp
  `f061b2646bfaac8b` in `forecast-provenance/v1`, at different postures. **The provenance
  field's `cache_epoch` can no longer be used to establish that two ERCOT forecast runs share a
  config identity**, which is what it exists for.
- It does **not** resolve which candidate produced §5.1's `28cef3500ec1fd9e` divergence; that
  needs the full-history diff R-5 already specifies. It removes the doubt about whether the
  mechanism is real.

---

## 7. How to read this result — the binding clause, restated because it now has teeth

The pre-declaration's §4 and this lane's charter both bind: **a worse I3 under the armed pair
is NOT a regression and MUST NOT be repaired by re-disarming, by a volume knob, or by any
parameter moved to close the breach.** The measured result is worse than the control on every
axis, and worse than pre-declared on every magnitude. Nothing in this lane responds to it.

Rule 1 `[R-STRUCT]` and rule 14 `[R-ACCURATE]` in their exact intended sense: all four armed
levers are structurally-motivated corrections (a bang-bang volume artifact removed, a
cross-basis phantom revenue floor removed, a storage availability-year gate the thermal path
already carried, a cost-normalized rank that returns the duration mix the measured ERCOT fleet
actually deploys). I3 rising is **a pre-existing under-build becoming visible** as those four
stop papering over it. Rule 13 `[R-MEASURED]`: a volume parameter fitted to close I3 or I12
would be the "adder tuned to the residual" the rule forbids, and is inadmissible here and in
R-2. This lane's job ended at measuring it.

**What §5 adds to the routing, for R-2's benefit:** if composition can outweigh volume at this
posture, then R-2 framed purely as "how much the screen builds" is aimed at the smaller of the
two channels at the margin. The §2.2(b)/§5.3 duration question (routed as **R-3**, "small,
ready") is on the evidence of this run the *first-order* lever at the current posture, not the
small one. That is a routing observation, not a repair, and not a re-ordering this lane may make.

---

## 8. Registration, declaration, board, matrix

- **Registered** via the single forecast registrar (`scripts/register_forecast_run.py --bundle`,
  rule 15): canonical sidecar `frontend/data/hindcast/ercot-2021-2025-realized-t1h-d4m.json`,
  `run_config.json` committed with the bundle, forecast namespace regenerated.
  *(`register_hindcast.py` alone leaves `provenance: null` — it does not stamp; the forecast
  registrar does. Noted for the next lane.)*
- **Declared** in `frontend/data/hindcast/invariant-failures.json`:
  `"ercot-2021-2025-realized-t1h-d4m": ["I3"]` plus a `d4m_note` naming this finding, in the
  **same commit** as the registration, per that file's own `how_to_update`.
  **ONE row, mine only.** The 13 pre-existing undeclared rows (5 ERCOT + 8 non-ERCOT) are lane
  D18's sweep and are untouched — verified by running the CI gate: it still reports exactly
  those 13 and does **not** report `d4m`.
- **Board:** the ERCOT `blocking_rows` I3 entry in `frontend/data/forecast/program-status.json`,
  ERCOT block only. No verdict, gate leg or determination moved. Lane D8-V's NEISO/NYISO/PJM/MISO
  FC-7 rows are untouched.
- **Matrix (rule 28 duty (b)):** `docs/codebase-site/data/mechanism-matrix/ERCOT.js` only. Four
  cells gain this run's evidence — `entry_margin_exhaustion`, `entry_forward_reserve_leg`,
  `storage_entry_availability_gate`, `storage_entry_cost_normalized_rank` — **closing the WATCH
  ITEM** all four (and `entry_lookahead_reprice`) carry: "no registered bundle sits at that
  posture — composed-by-construction, UNMEASURED." One now does. **No cell verdict moves**: this
  run measures the composed default posture, it does not A/B any single field, so it adjudicates
  nothing. No sister-ISO shard touched (rule 25).

---

## 9. Governance

- **One solve**, ERCOT only, years sequential within the invocation (rule 12). `data/clean` was
  absent in this container (gitignored, derived) and was regenerated from `data/raw` before the
  run — 53 datatypes, no failures. No stale `results/ERCOT/` cache existed, so no bundle was
  reused (rule 7 `[R-PARQUET]`, and the §6 hazard).
- **Rule 22 `[R-HOLDOUT]`:** no out-of-training year solved, scored or registered. Solve years
  `[2021, 2023, 2024, 2025]`, 2022 bridged; scoring bounded to 2023-2025. The harness's own
  governance banner asserted the freeze at launch; no marker spent, no backcast holdout touched.
- **Rule 13 `[R-MEASURED]`:** no measured outcome fed back into any input. No parameter moved
  at all — the only code change is the R-4 reporting grain.
- **Rules 1 / 14:** the worse I3 is reported at full magnitude and left unrepaired (§7).
- **Rule 25 `[R-ISO-SCOPE]`:** ERCOT only.
- **Rule 27 `[R-PUSH]`:** `check_forecast_invariants.py` (1,148 lines) and
  `test_forecast_invariants.py` (841 lines) were edited locally and pushed as exact on-disk
  bytes, then blob-verified against the remote (line count + sha256 both matched).
- **Not touched:** any backcast keeper shard, `status/*.js`, `calibration-complete.json`, offer
  curve, commitment bridge. No new GitHub Actions workflow; the solve ran in-session.
- **Pre-existing test failure, not mine:** `tests/regression/test_constants_facade.py::
  test_moved_surface_is_complete` fails on `STORAGE_TECH_AVAILABLE_YEAR` — reproduced on stock
  `main` before any edit of mine. Reported, not fixed (outside lane scope).

---

## 10. Open items routed to the director

1. **P-8 is unmeasured.** The T1-F horizon leg of the pre-declaration needs a T1-F run; it was
   not in this lane and is not estimated here.
2. **R-5 is upgraded, not closed** (§6). The mechanism is proven realizable; which candidate
   produced §5.1's divergence still needs the full-history diff. **The board's `cache_epoch`
   field is now known to be non-identifying for ERCOT forecast runs** — that is new and reaches
   beyond this lane.
3. **R-3 (storage duration) looks first-order, not small** (§5, §7). Re-weighing R-3 against R-2
   is the director's call; this lane only reports the evidence that prompts it.
4. **Plain-hindcast bundles should commit their evolution ledgers**, as crossover bundles now do
   (NEISO-RC-R R4). §5.3's attribution is inferred-with-mechanism purely because `d12c-armed`'s
   ledgers are absent.
5. **`register_hindcast.py` does not stamp provenance**; the forecast registrar does. A sidecar
   registered by the former path alone lands with `provenance: null` and is invisible to the
   FR-21 staleness reading. Records gap, not adjudicated here.
