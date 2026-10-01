# PRECOMMIT — capx D67-ARM: arming the PJM published adequacy requirement (owner ruling Q52)

**Lane:** capx D67-ARM, executing **owner ruling Q52** (capx ledger §3, r#47 amendment 1: *"ARM for
PJM"*) on the measured D67 A/B. **Branch:** `claude/capx-d67-arm-pjm-requirement-4cebpf`, fresh off
`origin/main` **`131291b5`**. **Date:** 2026-09-06. **Model:** Opus. **DATA PROFILE:** `pjm`.

**Pushed before any code change and before any solve.** Everything below — the realized cache keys,
the G-DRIFT verdict, the pre-declared magnitudes — was measured or derived at `131291b5` with **zero
LP**, through the shipped harness path, and is recorded here so it cannot be written to fit a result.

**Charter:** pack §D67-ARM + `FINDING-capx-d67-2026-09-06.md` (§3 the build; §3.1/§3.2 the vintage and
hold-last rules; §7.1 the full-span arm; §8.1 what the owner was asked) + the D57/Q44 arming precedent
(`FINDING-capx-d57-2026-09-05.md` §8.1).

---

## 1. The act

`config/iso_configs.py::_pjm_config` `default_scenario_overrides` gains one key:

```python
"capacity_adequacy_requirement_published_by_iso": {"PJM": True},
```

The D57/Q44 pattern exactly, and **nothing else**:

- the shared `ScenarioConfig` dataclass default stays `None` (no
  `_CACHE_KEY_OPTIONAL_FIELD_DEFAULT_FLIPS` entry — this is an ISO override, not a default flip);
- every other ISO's bare T1-H key and **every** backcast key are byte-identical;
- the explicit `--no-capacity-adequacy-requirement-published` CLI path reaches the pre-arm posture
  and keeps its key (the (b′-1) inverse test, in the shape `test_d60_arming_batch.py` uses);
- **zero free parameters** (rule 21 `[R-DOF]`): the requirement's operand becomes PJM's own published
  whole-RTO Reliability Requirement, reconciled byte-for-byte against
  `data/raw/capacity-market/demand-curve/pjm/pjm.csv` by test. The identification source is the
  published table; the *decision to arm* is owner ruling Q52.
- **rule 25 `[R-ISO-SCOPE]`:** a PJM posture. No other ISO's cell, key or shard is touched. The
  mechanism is generic in form and PJM-scoped by data — another ISO arms on its own evidence.

---

## 2. THE RE-KEY — declared before the solve, measured through the harness at `131291b5`

The harness path is `test_pjm_iso_override_arms_forecast_only`'s: `build_config(iso, 2021, 2025,
"realized", vintage=2020, entry_screen_diagnostics=True)` → `apply_iso_scenario_defaults` →
`cache_key()`.

| recipe | key at `131291b5` | after the arm |
|---|---|---|
| **bare `pjm-t1h`** | `15a723ba3b6dc856` | **`a9c66d8ea25acb9d`** |
| explicit `--no-capacity-adequacy-requirement-published` | `15a723ba3b6dc856` | **`15a723ba3b6dc856`** (unmoved) |
| explicit D57 all-off control | `c5ec052057905966` | `c5ec052057905966` (unmoved) |
| PJM plain backcast | `ScenarioConfig(iso="PJM", mode="backcast").cache_key()` | **unmoved** (field coerced to `None`) |

**The D65-B decomposition, measured rather than assumed.** D67 §7.1 recorded control
`aef81c84c4609c76` and arm `3f4070767f29472a`. Undoing exactly D65-B's two acts
(`ccs_retrofit_vom_adder = 8.0`, `ccs_retrofit_fixed_cost_co2_scaling = False`) on each resolved
config at `131291b5` restores **both** literals digit for digit:

| leg | at `131291b5` | undo-D65B | D67 §7.1 recorded |
|---|---|---|---|
| control (bare) | `15a723ba3b6dc856` | `aef81c84c4609c76` | `aef81c84c4609c76` ✔ |
| arm | `a9c66d8ea25acb9d` | `3f4070767f29472a` | `3f4070767f29472a` ✔ |

So the whole key move between D67's base and mine is **D65-B's and nothing else's**, on both legs —
the same decomposition `PRECOMMIT-capx-d65b-2026-09-06.md` §3.1 uses, and the same one the D57
arming pin already carries in `test_capacity.py`.

**Registration re-key** (`register_forecast_run.py::VERDICT_MAP`), declared here:

| run id | key today | key after |
|---|---|---|
| `pjm-2021-2025-realized-t1h-d57-clearing` | `pjm-t1h` | **`pjm-t1h-pre-d67`** (prior preserved verbatim, its own verdict standing — the D45-R / D57 convention) |
| the D67-ARM re-solve | — | **`pjm-t1h`** (the shipped posture) |

**Cache-epoch ledger:** `src/market_sim/results/cache.py` gets its entry. This one is a **KEY
ADVANCE, not a same-key invalidation** — the bare recipe's key moves `15a723ba3b6dc856` →
`a9c66d8ea25acb9d`, so no committed bundle is silently re-interpreted; the D57-era bundle keeps its
key under the preserved `pjm-t1h-pre-d67` id.

---

## 3. G-DRIFT (rule 29 `[R-SCREEN]` clause (b)) — hunk by hunk, `b1155995` → `131291b5`

Window: D67's own full-span commit `b1155995` to this lane's base. 37 files, +4,340/−276 over
`src/market_sim scripts/run_calibration.py scripts/run_calibration_full.py
scripts/run_capacity_hindcast.py scripts/lib data/raw/_validation-source data/raw/reference`.
**A matched cache key is NOT offered as a drift verdict** — every classification below is structural.

**Recipe posture, resolved at `131291b5` (measured, not asserted):** `retirement_sector_gate` **False**
· `capacity_no_default_cap_convention_by_iso` **None** · `capacity_going_forward_bar_published_by_iso`
**None** · `mass_cap_tons_by_year` **None** · `unit_outage_extract_basis_share` **False** ·
`miso_intermediate_gas_offer_margin` **False** · `federal_ces_target_by_year` **None** ·
`voluntary_clean_demand_path` **`"off"`** · `ccs_retrofit_available_year` **2028** ·
`fossil_announced_exits_enabled` **True** · `capacity_market_supply_clearing_by_iso` **`{"PJM": True}`**.

### 3.1 INERT — with the reason, not the assumption

| file(s) | change | INERT because |
|---|---|---|
| `config/constants.py` | **+175, −0.** Two re-export lines + the SCN-WS3b `VOLUNTARY_*` tables appended at EOF | **Purely additive: the diff contains exactly one `-` line, and it is the `---` header.** `DEMAND_GROWTH_RATES` — the hunk D67 §2.2 measured LIVE against its own older base — **does not move in this window**; that rate is common to `b1155995` and HEAD, so it is inside D67's measurement, not a drift on it. The new tables are read only behind `voluntary_clean_demand_path != "off"` |
| `runner.py` | SCN-WS3b voluntary clean-demand region | gated `voluntary_clean_demand_path`, default **`"off"`**; `append_voluntary_region` returns `arrays` unchanged |
| `policy/voluntary_demand.py` (new, +454), `data/datacenter.py` | the same family | same gate; no call site reachable with the row off |
| `policy/cap_and_trade.py` | SCN-CAP `scheduled_power_sector_budget` | `mass_cap_tons_by_year` **None** ⇒ returns `None` at the second line ⇒ the existing scalar→published→inert order is untouched |
| `config/capacity_market.py`, `data/avoidable_cost_rate.py`, `scripts/run_capacity_hindcast.py` | **D74** no-default-cap convention (resolver, predicate, CLI, record spec) | `capacity_no_default_cap_convention_by_iso` **None** ⇒ off; and it additionally *requires* `capacity_going_forward_bar_published`, which is also **None**. Two independent off-gates |
| `model/capacity_evolution/ccs.py`, `evolve.py` (the `_CCS_RETROFIT_LEDGER_SCALING_FIELDS` block), `results/evolution_ledger.py`, `config/scenarios.py` (D65-B's Act A/B + `_resolve_ccs_retrofit_fixed_cost_pair`) | **D65-B / D65-B-R** | `apply_ccs_retrofit` returns at its first line for `year < ccs_retrofit_available_year` = **2028**; every solved year here is 2021–2025. The ledger enrichment is additive keys on an empty `ccs_retrofits` list |
| `data/fleet/campd_bins.py`, `data/fleet/__init__.py`, `model/capacity_evolution/new_entry.py` | **D77** — CO2 booked net of `ccs_capture_fraction` | **ASSERTED, not assumed** (charter): the new `Generator.ccs_capture_fraction` defaults **0.0**, so `co2 * (1 - 0.0)` is an exact no-op for every unit; the only producers of a non-zero value are the retrofit screen (inert below 2028) and `_make_new_generator`'s `gas_cc_ccs` branch, whose units carry `plant_code = 0` and so never match the plant-keyed restoration at all. A guard test is added in this PR |
| `model/capacity_evolution/evolve.py`, `retirements.py` (the `_sector_exempt` routing) | **D78** | `retirement_sector_gate` **False** ⇒ `_sector_exempt` is empty ⇒ the routing change moves an empty set |
| `pipeline/solve.py` | the **P1 basis seed** (#5091) | three required conditions, one of which is `xyear_warmstart is None` — *the backcast callers only*. The forecast path passes `xyear_warmstart=config.forecast_xyear_warmstart` (`runner.py:3571`), a bool, never `None` ⇒ `_p1_seed` is `False` on every hindcast year |
| `pipeline/commitment.py`, `model/commitment.py` | NYISO bridge startup-aware screen + `screen_stats` census | `nyiso_gas_bridge_startup_aware` **False**; `screen_stats=None` is documented and coded as diagnostics-only, never read by the floor arithmetic. NYISO-scoped besides |
| `pipeline/backcast_config.py` | `nyiso_ct_peaker_bands_measured` | raises for any ISO ≠ NYISO, defaults `False`, **and `backcast_config` is the backcast path** — a `mode="forecast"` hindcast never enters it |
| `data/fuel/basis/miso.py`, `data/fuel/resolve.py`, `data/raw/reference/miso_gas_variable_transport*.csv` | MISO marginal-commodity gas | `iso == "MISO"`-gated; `miso_gas_marginal_commodity_pricing` / `miso_gas_variable_transport` both **False** |
| `model/interchange/spec.py`, `model/interchange/miso.py` | MISO neighbour-anchored seam ladder | `miso_seam_neighbour_anchored_ladder` **False**, and the injection is MISO's own seam step — PJM's solve never calls it. (PJM appears only as a *neighbour price column* in MISO's table) |
| `data/raw/reference/caiso_offer_*.{json,csv}` | CAISO offer surfaces | another ISO's branch |
| `model/lp/model.py` | solve-log line gains simplex iterations + objective | a log line; `try/except` guarded |
| `utils/heap.py` (**deleted**, −40) | `malloc_trim` helper | **no importer remains** (`grep` over `src/`, `scripts/`, `tests/`: only comment references; `run_calibration_full.py` carries its own local `_malloc_trim`). Read/free-side only — it cannot observe or alter a solve |
| `scripts/run_calibration.py`, `scripts/run_calibration_full.py`, `scripts/lib/invariant_ledger.py` | backcast runner + records tooling | **off-path by construction**: never imported by `run_capacity_hindcast.py` or by anything under `src/market_sim/` |
| `config/scenarios.py` (the `_EXPLICIT_FIELDS_ATTR` write) | refactor | value-preserving: `resolved = None if len(passed) == len(_INIT_FIELD_NAMES) else passed` is the identical expression extracted to a local; the added call is the CCS pair resolver above |

### 3.2 **LIVE — capx D81**, and the direction, pre-declared

```
evolve.py, the ONE call site of apply_economic_retirements:
-            exempt_unit_ids=_retrofitted_ids | _dated_exempt,
+            exempt_unit_ids=frozenset(),
-            exit_exempt_unit_ids=_sector_exempt,
+            exit_exempt_unit_ids=(_retrofitted_ids | _dated_exempt | _sector_exempt),
```

`_retrofitted_ids` is empty below 2028 and `_sector_exempt` is empty (gate off), but **`_dated_exempt`
is not**: this recipe resolves `fossil_announced_exits_enabled` **True** and
`capacity_market_supply_clearing_by_iso` **`{"PJM": True}`**, which is exactly D81's own arming
condition. The pending owner-filed dated block moves from the $0 price-taking residual `Q_0` into the
priced sell-offer stack at `max(0, GFC − E&AS) / (A_g × 365)`. **This hunk is LIVE on this recipe.**

**Direction, signed ex ante.** The conservation identity `Q_0 + Σ A_g == accredited` holds under both
routings, so the *total* offered MW is unchanged; what changes is that MW previously guaranteed to
clear at $0 now carries a positive offer. At any price below that offer the supply available is
strictly less, so the aggregate supply curve shifts **weakly leftward/upward**: the clearing price can
only **RISE (weakly)** and the cleared quantity only **FALL (weakly)**, never the reverse. D81's own
finding calls this out as reversing `DESIGN-capx-d54` §4.2's stated bias.

**Magnitude, from D81 §2 / §4.1 (measured, zero-LP phase 0 + its two-leg screen):**

| DY | pending dated units | accredited MW into the priced stack | D81's measured price / position effect (unarmed posture) |
|---|---:|---:|---|
| 2022 | 29 | 7,246.3 (coal 6,139.2 · gas_st 734.7 · gas_cc 372.4) | **exactly zero** — 67.760162 → 67.760162 $/MW-day, position 1.048349 → 1.048349, exits identical |
| 2023 | 19 | 5,213.6 (all coal) | **exactly zero** — same to all digits |
| 2024 | 15 | 4,989.2 (all coal) | not solved by D81 |
| 2025 | 15 | 4,217.5 (all coal) | not solved by D81 |

D81's reading: the block is coal-dominated and **deep in the money**, so its offers sit far below the
crossing and nothing downstream moves. **That measurement was taken on the D67-UNARMED posture, where
the requirement is the model's own `peak × FPR`.** My arm *moves the crossing* — up in 2024/25 and
2025/26 (requirement falls), down in 2022/23 and 2023/24 (requirement rises). **So D81's inertness
does not transfer, and I do not assume it.**

### 3.3 A correction to D81's epoch entry, recorded against interest

Epoch `2026-09-06e` in `results/cache.py` states its blast radius is *"any bundle solved in forecast
mode on an ISO whose `capacity_market_supply_clearing_by_iso` row is on … with
`fossil_announced_exits_enabled` on — **and no such bundle is committed or registered anywhere**"*.

**That is not accurate.** The committed sidecar
`frontend/data/hindcast/pjm-2021-2025-realized-t1h-d57-clearing.json` — the run holding the bare
`pjm-t1h` key today — records `capacity_market_supply_clearing_by_iso = {'PJM': True}` **and**
`fossil_announced_exits_enabled = True`, at cache key `f0e050e820c1159a`. It **is** in D81's blast
radius. The epoch's list of deleted probes is right as far as it goes; it missed the one registered
bundle. This lane's re-solve is precisely the act that repairs it: the shipped posture is re-measured
at HEAD, post-D81. The epoch entry is corrected in this PR (a records fix — no verdict, gate, score or
determination moves).

---

## 4. Rule 29(a) — why there is no screen solve, and 29(b) — why there is no control solve

**29(a) does not apply.** Rule 29's screen exists to *select* an arm before spending a full span. There
is nothing to select: the mechanism's A/B was already spent by D67 on a single base (§5–§7.1), the
screen there PASSED G1–G5, and the **owner has ruled** (Q52). This lane executes a ruled arming; the
re-solve is the shipped posture's own record, not a candidate. Rule 16 `[R-ALLYEARS]`'s spirit and the
charter both put it at the full 2021–2025 span in one invocation.

**29(b): a control solve is EARNED but buys no decision, so it is not spent.** The LIVE hunk in §3.2
would ordinarily earn a HEAD control. It is declined deliberately, and the decomposition is complete
with **one** solve because two of its three legs already exist:

- **D67 §7.1** is the clean arm effect — both legs at one base, so D81 and D65-B are absent from both
  and cancel exactly.
- **The committed `pjm-t1h` sidecar** (→ `pjm-t1h-pre-d67`) is the shipped prior.
- **The re-solve** is the new shipped posture at HEAD.

`(re-solve) − (D67 §7.1 arm)` is therefore **the D81 measurement under the arm**, obtained free — the
one quantity a control solve would have produced, and D65-B is provably inert on it (§3.1). Spending
~13 min of LP to re-derive a number the arithmetic already isolates is the waste rule 29 exists to
stop. No gate is decided on this differencing.

---

## 5. Pre-declared predictions — graded at full magnitude, whatever they read

- **P-A (unconditional).** The four delivery years' **requirement rows reproduce D67 §7.1 byte-identically**:
  control R 146,816.460 / 156,782.028 / 166,810.017 / 152,912.298; arm R = the published RR
  163,268.9 / 163,166.2 / 164,107.6 / 144,450.0 with **`arm − published = 0.000 MW`** in all four; ΔR
  +16,452.440 / +6,384.172 / −2,702.417 / −8,462.298. *Why unconditional:* the arm's R is the published
  table (fleet-independent by construction), and the control's R is `peak × FPR` on a screen peak built
  by `_scale_demand` — also fleet-independent. Neither can be reached by D81, which touches only the
  offer stack. **A departure here falsifies the arming's own central claim and is a STOP.**
- **P-B.** **DY2022/23's census positions reproduce byte-identically** — control 1.235795, arm 1.111265,
  move −12.45 pt. 2021 runs no screen (no `prior_results`), so the fleet entering the first screened
  year is pre-evolution and D81 cannot have reached it.
- **P-C.** **Signs: 2022/23 and 2023/24 FALL; 2024/25 and 2025/26 RISE.** This card is not a one-way
  residual improver — it moves two delivery years *away* from the published position and two toward
  it, which is the signature of a real operand rather than a fitted one (D67 §8.1). Reported at full
  magnitude either way.
- **P-D.** **2021 is byte-identical to the prior** in every ledger block (no screen).
- **P-E (the D81 interaction, the one genuinely open prediction).** DY2023/24, 2024/25 and 2025/26 may
  depart from D67 §7.1's census rows (1.055476 / 1.051736 / 0.993091) where the re-priced stack changed
  a prior year's exits. If D81 is inert under the arm as it was unarmed, they reproduce exactly. If it
  is not, the departure is **signed**: clearing price weakly **UP**, cleared quantity weakly **DOWN**,
  relative to the pre-D81 routing (§3.2). **A departure in the opposite direction falsifies the §3.2
  reading and is a STOP.**
- **P-F (byte-identity).** No other ISO's bare T1-H key moves (`1f92943f84f42fd0` MISO ·
  `ee6a3e764324f28f` NYISO · `5b292e24dd752ea4` NEISO · `8f1c3766703a90c4` CAISO ·
  `46d013cbf1f35d27` ERCOT); the PJM plain-backcast key is unmoved; **every backcast keeper of every
  ISO is byte-identical**; `tests/regression/test_persisted_identity.py` green;
  `check_cache_key_registration.py --base origin/main` green.
- **P-G.** The explicit `--no-capacity-adequacy-requirement-published` path reaches the pre-arm posture
  and keeps key `15a723ba3b6dc856` (the (b′-1) inverse test).

---

## 6. Execution order, and the HEAD guard

1. This PRECOMMIT, pushed **before** the override.
2. The override + tests + the epoch entry + the §3.3 records correction + the PJM matrix shard + the
   CLAUDE.md bullet line — **one PR**.
3. `data/clean` rebuilt from `data/raw` (gitignored, disposable; the harness hard-fails on the
   confirmed-exits partition rather than degrading silently — D67 §5).
4. **ONE re-solve**, PJM solo, years **sequential** (rule 12 `[R-PARALLEL]`), guarded:
   `H0=$(git rev-parse HEAD); <solve>; [ "$(git rev-parse HEAD)" = "$H0" ] || exit 90`.
5. Registered in place with its prior; FC rows at full magnitude against `pjm-t1h-pre-d67` **and**
   against D67 §7.1.
6. `FINDING-capx-d67arm-2026-09-06.md` closes the lane: this PRECOMMIT graded, the re-key table, the
   board row, the governance attestation with rule-27 blob checks.

**Rebase discipline:** between legs, never during; the rebase delta is re-audited before registering.

---

## 7. Collisions

- **D65-B-R is the SOLE writer** of `frontend/data/forecast/ff-verdicts.json` and `program-status.json`
  until its batch registers. Steps 1–5 of the charter proceed now; **the board registration is HELD**
  until D65-B-R merges. Rebase between, never during.
- **D78-R** (PJM hindcast surfaces, no code) and **D81** (one seam, already merged at `ccbf802e`) and
  **D75-R** (the ELCC registry) are different regions. **`_pjm_config` is this lane's this window.**
- The D67 lane's own branch (`claude/capx-d67-pjm-requirement-operand-18wzjf`) is another desk's and is
  closed; this lane is fresh off `origin/main`.

## 8. What this lane does NOT claim

It does not move any `ScenarioConfig` default, any other ISO, any backcast keeper, any marker or
freeze file, or any calibration determination. It re-opens no adjudicated matrix cell. It does not
re-litigate D67's own open items — **G6 remains untestable at this configuration** (D62 is default-off,
so 2024/25 is a marginal-offer year in both arms; D67 §7.1) and the two FALL delivery years remain a
stated cost with their root cause routed to the demand path (D67 §8(a)), not absorbed here. Rule 21:
**zero free parameters** — the operand is PJM's published table and the ruling is the identification.
