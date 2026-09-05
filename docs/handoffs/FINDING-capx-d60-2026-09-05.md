# FINDING — capx D60: the three-ruling arming batch executed (Q40 · Q41 · Q42), the pre-declaration graded at full magnitude, one STOP fired on PJM and one pre-declaration miss recorded against myself

**Lane:** capx D60 — the EXECUTION of three owner rulings given 2026-09-05 at director
sitting r#37 (capx ledger §0ah.3 / §3). A ruled, mechanical lane: **no new mechanism, no new
field, no new parameter value, no keeper, no shard promotion field, no `complete` / `final`
marker, no freeze, nothing against measured H1-2026.** Everything below is what the three
armings made true, and what they made false that the pre-declaration had claimed.

**Pre-declaration:** `PREDECL-capx-d60-2026-09-05.md`, pushed **before any code change on
the branch**, with **Addendum A** (every bare key re-resolved through the real harness path,
before any solve) and **Addendum B** (the T3 attestation's six assertions fixed before the
GOLDEN-3 solve was launched).

---

## 0. Verdict (one paragraph)

All three rulings are armed, flip-first, in one commit: `adequacy_accounting_ratio_dated_net`
for MISO and both NYISO requirement gates through their ISOs' `default_scenario_overrides`
(rule 25 — both dataclass defaults stay `False`), and `ccs_retrofit_capex_co2_scaling` as the
dataclass default for all six ISOs through a **(b′-1) declared flip** whose frozen drop value
stays `"False"`. Both pinned default keys advance —
`4c6b03ae098b6e3e` → `e5ecd4105ada3e58`, bare backcast `8211c72bb1960adc` →
`6a2845e50951394e` — which is the designed behaviour of (b′-1), pre-authorised in terms by
D50 §6.4, and **no committed artifact moves at all**. Twelve of the thirteen bare forecast
keys landed exactly on their pre-declared post-arm values; the thirteenth is a defect in my
own pre-declaration, graded in §3. Four bare keys were RENAMED onto committed legs at zero
solve, with byte-identity established field-by-field first and every prior preserved at
`-pre-d60`; a fifth rename — PJM's — was **reversed before it was pushed** when capx D57
merged mid-lane and moved PJM's bare t1f recipe, which is D60's **STOP 1 firing exactly as
written** (§4). The four re-solves the flip owes are in §5.

---

## 1. What was armed, and in what form

| ruling | field(s) | form | record it executes |
|---|---|---|---|
| **Q40** | `adequacy_accounting_ratio_dated_net` | `_miso_config` `default_scenario_overrides` | `FINDING-capx-d51-2026-09-04.md` §7 |
| **Q41** | `nyiso_requirement_forecast_peak` + `nyiso_requirement_vintage_factors` | `_nyiso_config` `default_scenario_overrides` — **NYISO's first ISO-level overrides** | `FINDING-capx-d52-2026-09-04.md` §8(1) |
| **Q42** | `ccs_retrofit_capex_co2_scaling` | dataclass default `True` + a dated (b′-1) line, frozen drop value untouched | `FINDING-capx-d50-2026-09-04.md` §8 |

Rule 21 holds by inspection: **no value was chosen here.** The ratio IS D51's 0.893436, and
`captured_ref` IS D50's 0.90 × 6.3 × 0.057 = 0.32319 t/MWh. Rule 25 holds in both directions:
the two ISO armings are per-ISO by construction (and the dated-net registry falls through to
D31's value for any ISO absent from it, even when armed), and Q42 is a **posture, not a
transfer** — it carries no ISO's fitted number, every term is an already-cited constant, and
the reference host is the same one `new_entry._emerging_lcoe` charges the ATB increment
against. That is the same admissibility class as Q30.

**Nothing beyond the three rulings armed**, asserted by test: the NYCA ICAP demand curve
stays OFF (D52 §8(2), re-affirmed D59), `locality_capacity_curves` stays OFF (D59), and
`capacity_deliverability_limits` stays OFF everywhere.

## 2. Step 0 (hygiene) was already satisfied at HEAD — no commit

The director's §0ah.4 routing named three files for `ruff format`. At the lane's base
`ee7754c1` all three were **already formatted** — `ruff format` reported *"3 files left
unchanged"*, `ruff check` *"All checks passed!"*, and `git log -1` on each names commit
`0b51f28e` ("Y-7 item 2: ruff format the six files the check named"), which landed the same
work before this lane opened. **There was nothing to commit and no no-op commit was made.**
Stated rather than silently skipped.

---

## 3. The pre-declaration graded at full magnitude — every key

Twelve of thirteen HIT. The thirteenth is mine to own.

| bare key | §2 pre-declared | harness-resolved | verdict |
|---|---|---|---|
| `ercot-t1f` | `0c3e9cd5b5993bdf` | `0c3e9cd5b5993bdf` | **HIT** |
| `neiso-t1f` | `18515067bf4d2fbe` | `18515067bf4d2fbe` | **HIT** |
| `pjm-t1f` | `167e65187f32056b` | `09996eca71ee80fd` | **STOP 1 — §4** |
| `caiso-t1f` | `29f8eb372810195f` | `29f8eb372810195f` | **HIT** |
| `nyiso-t1f` | `19a9690bb12c8459` | `19a9690bb12c8459` | **HIT** |
| `neiso-t3` | `f04fd06348e1623d` | `f04fd06348e1623d` | **HIT** |
| `ercot-t1h` | `82b27751be747552` | `82b27751be747552` | **HIT** |
| `caiso-t1h` | `7da58199acd362ee` | `7da58199acd362ee` | **HIT** |
| `neiso-t1h` | `f3988df3068020d1` | `f3988df3068020d1` | **HIT** |
| `pjm-t1h` | `7297dcb3b92be3fb` | `aef81c84c4609c76` | moved by D57, not by D60 — §4 |
| `miso-t1h` | `687bd75f2828bea1` | `687bd75f2828bea1` | **HIT** |
| `nyiso-t1h` | `6e70a637b3465542` | `6e70a637b3465542` | **HIT** |
| `miso-t1f` | `3f85ecc45d90c248` | **`b1a73a087064ffd8`** | **MISS — §3.2** |

### 3.1 The three required cross-checks, all HIT to the digit

1. **D50 §6.1's right-hand column.** For the four ISOs where CCS is D60's only arm the
   post-D60 key **is** D50's column: ERCOT `0c3e9cd5b5993bdf`, NEISO `18515067bf4d2fbe`,
   PJM `167e65187f32056b` (as it stood before D57), CAISO `29f8eb372810195f`. For MISO and
   NYISO, where D60 arms more, removing the extra arms reproduces D50's column exactly —
   MISO CCS-only `f3f96e14bb75c9d9`, NYISO CCS-only `b9e4c79e188ab01e`.
2. **`miso-t1h`, the `c306ddc6…`-successor, and its exact relation to the D53 rider.**
   `c306ddc6d28c60c2` (bare at HEAD = sector gate via MISO's own override) **+ ratio** =
   **`6ea92547eaa62559`**, which IS the committed D53 rider key — reproduced to the digit;
   **+ the flipped CCS default** = **`687bd75f2828bea1`**, the post-D60 bare key. The
   post-D60 recipe therefore differs from the committed rider in **exactly one field**.
3. **`nyiso-t1h` and the D52 arm key.** `91686abe7a744a88` **+ the two gates** =
   **`911371a8cf23d5c3`**, the committed D52 arm — to the digit; **+ the flipped CCS
   default** = **`6e70a637b3465542`**. Same one-field relation.

### 3.2 The MISS, graded against myself

`miso-t1f`'s post-D60 key is **`b1a73a087064ffd8`**, not the `3f85ecc45d90c248` §2 declared.

**Cause, measured:** MISO's `default_scenario_overrides` already carry
`retirement_sector_gate: True`, landed at HEAD by **capx D53 earlier the same day**. The
committed control `miso-2026-2030-d45r-remeasure` predates D53 and records the field absent,
so §2's method — reconstruct the control's own `run_config.json` and set the armed fields —
understated the recipe by exactly one field. **Forcing the sector gate back off returns
`3f85ecc45d90c248`**, which confirms the diagnosis to the digit and confirms nothing else
moved.

**It is a defect in my method, not a surprise in the rulings.** §2's emulation is exact only
when the committed control's resolved posture already equals the bare recipe's — true for
twelve keys, false for this one. D53 §6.1 had stated the consequence in terms when it armed
the gate: *"the MISO t1f leg (2026–2030) was not re-solved here — its next solve resolves the
gated screen by construction."* D60's MISO t1f re-solve **is** that next solve. The
correction was published as **Addendum A §A.1 before any solve and before the flip commit**,
not retrofitted here, and Addendum A §A.5 added P17–P19 for the third mechanism the leg now
carries.

### 3.3 What Addendum A discharged: STOP 2, field-by-field

The harness-resolved bare recipe was diffed field-by-field against each rename target's own
committed `run_config.json`, ignoring only fields ABSENT from the older config that resolve
to a cache-neutral `False`/`None` (schema growth, not posture):

- **`miso-t1h` ← `…-d53-sectorgate-d51ratio`**: the ONLY substantive difference is
  `ccs_retrofit_capex_co2_scaling: False → True`. The committed rider records it
  **explicitly `False`** (solved after D50 built it), so the pair is a clean one-field A/B.
- **`nyiso-t1h` ← `…-d52-devintage`**: the ONLY difference is
  `ccs_retrofit_capex_co2_scaling: <absent> → True`.

**Why that is byte-identical rather than merely small, proved in code:**
`ccs.py::apply_ccs_retrofit` opens with `if year < config.ccs_retrofit_available_year: return
fleet, []` (line 305, default 2028), which precedes **every** read of the flag
(`scale_capex`, line 330) — and `ccs.py:330` is the field's **only consumer in the whole
source tree**. A horizon ending at 2025 (t1h) or 2027 (t1x) cannot reach it on any path. So
every SCORED row of both targets is identical to what the bare recipe would produce, STOP 2
does not fire, and neither leg is re-solved.

---

## 4. STOP 1 FIRED ON PJM — and the rename was reversed before it was pushed

**What happened.** §5 pre-declared `pjm-t1f` ← `pjm-2026-2030-d50-ccscapex` on the ground
that the D50 arm had been solved AT the key the flip would make bare (`167e65187f32056b`).
Between the pre-declaration and D60's rebase, **capx D57 merged** (PR #4786) and armed three
PJM gates by its own owner ruling — `pjm_accreditation_design_vintage`,
`pjm_demand_response_supply` and `capacity_market_supply_clearing_by_iso[PJM]`. PJM's bare
t1f recipe therefore now resolves through the harness path to **`09996eca71ee80fd`**, and the
D50 arm is no longer at it.

**What was done.** The rename was **reversed in the working tree before the commit was
pushed**: `pjm-t1f` keeps its D45-R record (`pjm-2026-2030-d45r-remeasure`,
`321f04e9060787f0`), the D50 arm keeps its suffixed key `pjm-t1f-d50-ccscapex`, and the
VERDICT_MAP rows carry the reversal with its reason. This is a wrong *rename* being undone,
never a mechanism being reverted — Q42 stands unchanged for PJM as for every other ISO.

**What it leaves open, stated plainly rather than buried.** PJM's bare t1f row is now stale
on **two postures at once** — D57's three gates and Q42's CCS default — and only a re-solve
at `09996eca71ee80fd` can make it truthful. **D60 did not run it**, for one reason stated as
a boundary rather than an excuse: PJM forecast surfaces are D57's this window, and the leg is
~28 min. It is **ROUTED to the director with the key it must land on** (§8 item 1).

**`pjm-t1h` likewise moved** — to `aef81c84c4609c76` — and that movement is **D57's, not
D60's**: D57's own arming note records the bare `pjm-t1h` recipe becoming its arm A's
`f0e050e820c1159a`, and D60's CCS flip is inert on a 2021–2025 horizon by §3.3. D60 neither
renamed nor re-stamped anything on PJM t1h.

**The test surface records D57's arming rather than asserting it away.**
`test_d60_arming_batch.TestNothingElseArmed` gains `test_the_d57_pjm_gates_stay_pjm_only`,
which pins those two gates ON for PJM and OFF for the other five — so a future lane that
widened them would fail here, and D60's own claim ("nothing else armed") stays honest about
what a *different* lane armed.

---

## 5. The re-solves

*(filled below as each leg lands)*

---

## 6. The pins, and what a moved key does and does not cost

| config | before | after |
|---|---|---|
| `ScenarioConfig()` (forecast default) | `4c6b03ae098b6e3e` | **`e5ecd4105ada3e58`** |
| `ScenarioConfig(mode="backcast")` | `8211c72bb1960adc` | **`6a2845e50951394e`** |
| `ScenarioConfig(ccs_retrofit_capex_co2_scaling=False)` | `4c6b03ae098b6e3e` | `4c6b03ae098b6e3e` (**unmoved**) |
| same, backcast | `8211c72bb1960adc` | `8211c72bb1960adc` (**unmoved**) |

Rows 3–4 are the protection and they are asserted by test: an explicit `False` still equals
the frozen declaration, is still dropped from the hash, and still addresses its pre-flip
bundle — one committed artifact already relies on it
(`results/hindcast/miso-2021-2025-realized-t1h-d55-keyfix`).

**This is not the STOP the charter's "no keeper / backcast key moving" clause names.** That
clause is the D53 **ISO-override** test — an override must never move `ScenarioConfig()`, the
bare backcast key, or another ISO's forecast key — and D60 asserts it unchanged for Q40 and
Q41 (four tests). Q42 is a *default* flip, whose entire mechanism is that the armed default
separates from the frozen drop value; D50 §6.4, the record ruling Q42 was given on,
pre-authorises the consequence in terms. The pre-declaration said so in §3 before the flip
landed, so this was declared, not discovered.

**Cost, exactly:** a one-time cache MISS per config, never a wrong answer — a key that moved
cannot mis-serve. **No committed artifact moves**: no keeper, sidecar, determination or
dashboard row, because those are files rather than cache lookups. Behaviour is byte-identical
for every backcast (which runs no capacity evolution at all, and whose years never reach 2028
and whose measured fleets contain no `gas_cc_ccs` unit) and for every hindcast/crossover
horizon ending before 2028, by §3.3.

Both pins were advanced with dated cause blocks across **26 files**: the two literals in
`tests/regression/test_persisted_identity.py`, a new 2026-09-05 cache-epoch ledger entry in
`src/market_sim/results/cache.py`, the live-pin comment in `scenarios.py`, 21 unit-test pins,
and `CHANGELOG.md`. Where a literal is a **dated historical measurement in prose** it was
left as written, per those files' own convention; the three ERCOT poles in
`test_ercot_stageb_arming.py` / `test_iso_override_precedence.py` moved together by the same
delta and their advance is recorded in each file's own docstring
(`1e1002d480fc180d` → `b5ab30d0fae9f8a3`, `ef70a350ac15fd0f` → `2c3496db2252da1d`,
`11a94474a0c824e3` → `2286402c91a65cf5`).

## 7. The t1x keys — a pre-existing staleness D60 discloses and does not repair

`neiso-t1x` and `nyiso-t1x` **already failed to re-resolve at HEAD before D60 touched
anything**: their committed configs carry two fields deleted under rule 26
(`caiso_bidir_intertie`, `renewable_buildout_pace`) and predate D44's own flip.
`ercot-t1x`, `miso-t1x` and `pjm-t1x` carry **no hex epoch at all** — their provenance blocks
hold the text *"Epoch 2026-08-03 — FFR Wave-2 constants + the D-1/D-2 owner default flips."*
D60's CCS flip is inert on all five (2023–2027 horizons, §3.3), so it neither causes nor cures
this. Repairing the t1x stamps is a different lane's question and is **routed**, not absorbed.

---
