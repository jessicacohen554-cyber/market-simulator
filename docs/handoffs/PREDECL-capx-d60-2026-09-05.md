# PRE-DECLARATION — capx D60: the three-ruling arming batch (Q40 · Q41 · Q42)

**Pushed BEFORE any code change on this branch.** Everything below — every cache
key, every rename source, every expected FC row, every STOP — was resolved at
HEAD `ee7754c1` through the harness path and written down before
`scenarios.py` or `iso_configs.py` was touched. Graded at full magnitude in
`FINDING-capx-d60-2026-09-05.md`.

**Lane:** capx D60 — the EXECUTION of three owner rulings given 2026-09-05 on
measured records (capx ledger §0ah.3 / §3). A ruled, mechanical lane: **no
measurement of a new mechanism, no new field, no new parameter value, no
keeper, no marker, no shard promotion field.** A surprise is a STOP, not a
decision.

| ruling | what arms | form | record |
|---|---|---|---|
| **Q40** | `adequacy_accounting_ratio_dated_net` for **MISO** | `_miso_config` `default_scenario_overrides` (rule 25) | `FINDING-capx-d51-2026-09-04.md` §7 — 0.8546 → 0.8934, zero DOF |
| **Q41** | `nyiso_requirement_forecast_peak` **and** `nyiso_requirement_vintage_factors` for **NYISO** | `_nyiso_config` `default_scenario_overrides` (rule 25) | `FINDING-capx-d52-2026-09-04.md` §8(1) |
| **Q42** | `ccs_retrofit_capex_co2_scaling` as **THE DEFAULT for all six ISOs** | dataclass default → `True` + a dated (b′-1) line in `_CACHE_KEY_OPTIONAL_FIELD_DEFAULT_FLIPS`; the frozen drop value stays `"False"` | `FINDING-capx-d50-2026-09-04.md` §8 |

The NYCA demand curve stays **OFF** (D52 §8(2) P9 failed; re-affirmed D59).
`locality_capacity_curves` stays **OFF** (D59). PJM's D48 fields and D57's gate
stay **OFF** (D57 is measuring them). Nothing beyond the three rulings arms.

**Order of operations: FLIP FIRST.** All three edits land in ONE commit before
any re-solve, so every re-solve lands on the final posture exactly once.

---

## 0. Step 0 (hygiene) is already satisfied at HEAD — no commit

The director's §0ah.4 hygiene routing named
`src/market_sim/model/capacity_evolution/new_entry.py`,
`scripts/gen_nyiso191_attestation.py` and
`tests/curation/test_derive_cc_capacity_reconcile_scope.py` for `ruff format`.
At HEAD `ee7754c1` all three are **already formatted**: `ruff format` (0.15.17)
reports *"3 files left unchanged"* and `ruff check` reports *"All checks
passed!"*. `git log -1` on each names commit `0b51f28e`, *"Y-7 item 2: ruff
format the six files the check named (format-only)"*, which landed the same
work before this lane opened. **There is nothing to commit**; a no-op commit is
not made. Stated rather than silently skipped.

---

## 1. The three edits, exactly as they will be written

### 1.1 Q40 — MISO's ratio (rule 25, an ISO override)

`src/market_sim/config/iso_configs.py`, `_miso_config()`
`default_scenario_overrides`, **appended beside the D53 `retirement_sector_gate`
line already there**:

```python
"adequacy_accounting_ratio_dated_net": True,
```

with the Q40 citation, D51 §7's four limbs, and the letter-vs-substance
divergence the owner resolved. The `ScenarioConfig` default stays `False`; no
other ISO's shard is touched (an ISO absent from
`ADEQUACY_INTERNAL_SUPPLY_ACCOUNTING_RATIO_DATED_NET_BY_ISO` falls through to
D31's value even when armed — the registry's own rule-25 guard, unchanged).

### 1.2 Q41 — NYISO's two requirement gates (rule 25, an ISO override)

`_nyiso_config()` today returns
`ISOConfig(name="NYISO", zones=zones, links=links, voll=2000.0)` — **it declares
no `default_scenario_overrides` at all**. D60 adds the mapping with exactly two
entries:

```python
default_scenario_overrides={
    "nyiso_requirement_forecast_peak": True,
    "nyiso_requirement_vintage_factors": True,
},
```

Stated because it changes `apply_iso_scenario_defaults`'s NYISO branch from the
`if not overrides: return config` early-return to the override path. That
function is a strict narrowing (it applies an override only to a field the
caller did not explicitly set), so no caller's explicit posture moves; and both
fields are coerced to the dataclass default in a plain backcast by the D52
`__post_init__` block, which runs after `with_overrides`.

### 1.3 Q42 — the CCS capex default (the D44 (b′-1) pattern, global posture)

`src/market_sim/config/scenarios.py`:

```python
ccs_retrofit_capex_co2_scaling: bool = True   # was False
```

plus, **APPENDED** (never edited) to `_CACHE_KEY_OPTIONAL_FIELD_DEFAULT_FLIPS`,
whose second entry this is:

```python
("2026-09-05", "ccs_retrofit_capex_co2_scaling", "True"),
```

The frozen entry in `_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS` **stays `"False"`** and
is not touched — check 4 of `scripts/check_cache_key_registration.py` fails an
edit, and leaving it put is what makes a post-flip config take its own key
while an explicit `False` collapses onto the pre-flip key (D44 §2 rows 3–4).
Rule 21: no value changes — `captured_ref` is and stays
`ccs_retrofit_captured_ref_t_per_mwh` = 0.90 × 6.3 × 0.057 = 0.32319 t/MWh, and
the ratio is and stays D51's 0.893436.

**No backcast coercion is added for the CCS field**, exactly as D44 added none
for `fossil_announced_exits_enabled`. The consequence is declared in §3.

---

## 2. EVERY bare forecast key, before and after — all six ISOs, t1h / t1x / t1f / t3

Resolved at HEAD `ee7754c1` by reconstructing each bare key's own committed
`run_config.json` into a `ScenarioConfig` and hashing it; the post-arm column is
EMULATED by setting the field(s) the arming resolves `True` (exact for a
registered cache-optional field frozen at `"False"`: it drops at `False` and
enters at `True` — the same emulation PREDECL-capx-d50 §4 used and D50 §6.1
verified). **All 13 keys that carry a hex epoch re-resolve at HEAD to their
committed value and to the board's stamp — zero drift.**

| bare key | ISO | years | HEAD (= committed = board) | POST-D60 | what moves it |
|---|---|---|---|---|---|
| `ercot-t1f` | ERCOT | 2026–2030 | `873d8c0e6cab52ae` | **`0c3e9cd5b5993bdf`** | CCS |
| `neiso-t1f` | NEISO | 2026–2030 | `6690e4d6d66bc819` | **`18515067bf4d2fbe`** | CCS |
| `pjm-t1f` | PJM | 2026–2030 | `321f04e9060787f0` | **`167e65187f32056b`** | CCS |
| `caiso-t1f` | CAISO | 2026–2030 | `772b1e5abc7fc80c` | **`29f8eb372810195f`** | CCS |
| `miso-t1f` | MISO | 2026–2030 | `8d8bc63a0d4378a9` | **`3f85ecc45d90c248`** | CCS **+ ratio** |
| `nyiso-t1f` | NYISO | 2026–2030 | `cc7d1050a8090c76` | **`19a9690bb12c8459`** | CCS **+ 2 gates** |
| `neiso-t3` | NEISO | 2026–2050 | `67678e58b2d0526c` | **`f04fd06348e1623d`** | CCS |
| `ercot-t1h` | ERCOT | 2021–2025 | `67d5dcc1ada2e2df` | **`82b27751be747552`** | CCS (inert, §4) |
| `caiso-t1h` | CAISO | 2021–2025 | `2c8cc7d19ccaed4c` | **`7da58199acd362ee`** | CCS (inert) |
| `neiso-t1h` | NEISO | 2021–2025 | `d6c0137e37bf3200` | **`f3988df3068020d1`** | CCS (inert) |
| `pjm-t1h` | PJM | 2021–2025 | `c6091bd5b62bbc3f` | **`7297dcb3b92be3fb`** | CCS (inert) |
| `miso-t1h` | MISO | 2021–2025 | `c306ddc6d28c60c2` | **`687bd75f2828bea1`** | CCS (inert) **+ ratio** |
| `nyiso-t1h` | NYISO | 2021–2025 | `91686abe7a744a88` | **`6e70a637b3465542`** | CCS (inert) **+ 2 gates** |
| `neiso-t1x` | NEISO | 2023–2027 | *stamp* `07e416f3f8072e7c`; **does not re-resolve at HEAD** (`3aac1e9827cf6208`) | `46b510543c89e795` | pre-existing staleness, §5 |
| `nyiso-t1x` | NYISO | 2023–2027 | *stamp* `7323dc2ddabc95c7`; **does not re-resolve at HEAD** (`4993c2ec77ce6e5f`) | `eb68275727c5d2a8` | pre-existing staleness, §5 |
| `ercot-t1x` · `miso-t1x` · `pjm-t1x` | — | 2023–2027 | **no hex epoch at all** — the provenance block carries the text *"Epoch 2026-08-03 — FFR Wave-2 constants + the D-1/D-2 owner default flips."* | — | nothing to move |

### 2.1 The three required cross-checks, all HIT

1. **D50 §6.1's right-hand column, for the t1f keys.** For the four ISOs where
   CCS is D60's ONLY arm the post-D60 key **is** D50's column to the digit:
   ERCOT `0c3e9cd5b5993bdf`, NEISO `18515067bf4d2fbe`, PJM `167e65187f32056b`,
   CAISO `29f8eb372810195f`. For MISO and NYISO D60 arms MORE than D50 modelled,
   so the keys necessarily differ — and the D50 column reproduces exactly when
   the extra arms are removed: MISO CCS-only = **`f3f96e14bb75c9d9`** = D50's
   column; NYISO CCS-only = **`b9e4c79e188ab01e`** = D50's column. Both
   measured this session.
2. **`miso-t1h`, the `c306ddc6…`-successor.** The exact relation to the D53
   rider, measured: `c306ddc6d28c60c2` (bare at HEAD = sector gate via MISO's
   override) **+ ratio** = **`6ea92547eaa62559`**, which IS the committed D53
   rider key `miso-t1h-d53-sectorgate-d51ratio` — reproduced to the digit;
   **+ ratio + the flipped CCS default** = **`687bd75f2828bea1`**, the post-D60
   bare key. So the post-D60 `miso-t1h` recipe differs from the committed D53
   rider in **exactly one field**, `ccs_retrofit_capex_co2_scaling`, which
   cannot reach a 2021–2025 solve (§4).
3. **`nyiso-t1h` and the D52 arm key.** `91686abe7a744a88` (bare at HEAD)
   **+ the two gates** = **`911371a8cf23d5c3`**, which IS the committed D52 arm
   key `nyiso-t1h-d52-devintage` — reproduced to the digit; **+ the flipped CCS
   default** = **`6e70a637b3465542`**, the post-D60 bare key. Same one-field
   relation.

---

## 3. The two pinned default keys DO move — declared, not discovered

| config | HEAD | POST-D60 |
|---|---|---|
| `ScenarioConfig()` (forecast default) | `4c6b03ae098b6e3e` | **`e5ecd4105ada3e58`** |
| `ScenarioConfig(mode="backcast")` | `8211c72bb1960adc` | **`6a2845e50951394e`** |
| `ScenarioConfig(ccs_retrofit_capex_co2_scaling=False)` | `4c6b03ae098b6e3e` | `4c6b03ae098b6e3e` (**unmoved**) |
| same, backcast | `8211c72bb1960adc` | `8211c72bb1960adc` (**unmoved**) |

This is **the declared consequence of a (b′-1) default flip**, identical in kind
to D44 §2, and it is **not** the STOP condition the charter's "no keeper /
backcast key moving" clause names. That clause is the D53 **ISO-override** test —
an override must never move `ScenarioConfig()` or the bare backcast key — and
D60 asserts it unchanged for Q40 and Q41 (§7 test 3). Q42 is a *default* flip,
whose whole mechanism is that the armed default separates from the frozen drop
value; D50 §6.4, the record ruling Q42 was given on, states the backcast
consequence in terms and pre-authorises it: *"Backcast keys advance with
byte-identical behaviour (no backcast year reaches 2028 and no measured backcast
fleet contains a `gas_cc_ccs` unit) … No committed artifact moves at all."*

**What that costs, exactly:** a one-time cache MISS per config, never a wrong
answer — a key that moved cannot mis-serve. **No keeper, sidecar, determination,
dashboard row or backcast bundle moves**, because committed artifacts are files,
not cache lookups. Rows 3–4 are the protection: any control arm that carries the
field explicitly `False` keeps its bundle (one committed artifact already
exercises it — `results/hindcast/miso-2021-2025-realized-t1h-d55-keyfix`).

Both pins are advanced with dated cause blocks in the **26 files** that carry
them (`tests/regression/test_persisted_identity.py`, the cache-epoch ledger in
`src/market_sim/results/cache.py`, `src/market_sim/config/scenarios.py`'s live-pin
comment, 21 unit-test pins, `CHANGELOG.md`).

---

## 4. Why the CCS flip is BYTE-IDENTICAL for every t1h and t1x key — proved in code, not asserted

`src/market_sim/model/capacity_evolution/ccs.py::apply_ccs_retrofit`, line 305:

```python
if year < config.ccs_retrofit_available_year:      # default 2028
    return fleet, []
```

This early return precedes **every** read of the flag — `scale_capex =
bool(config.ccs_retrofit_capex_co2_scaling)` is line 330, and `ccs.py:330` is
the field's ONLY consumer in the whole source tree (verified by grep across
`src/`). A run whose horizon ends at 2025 (t1h) or 2027 (t1x) therefore cannot
reach the flag on any path. Byte-identity of every scored row is **by
construction**, not by measurement.

---

## 5. Disposition of every bare key: RENAME, NO-OP, or RE-SOLVE

### Class A — RENAME to a different committed bundle (zero solve)

The post-D60 bare recipe's scored rows are produced by an ALREADY-COMMITTED
suffixed leg; the bare verdict key is repointed to it and the current record is
preserved at `<key>-pre-d60`. Exactly the D53 §6.1 procedure.

| bare key | renames FROM (preserved at `-pre-d60`) | renames TO (committed bundle) | leg's own key | relation to the post-D60 bare recipe |
|---|---|---|---|---|
| `miso-t1h` | `miso-2021-2025-realized-t1h-d53-sectorgate` (D53) | **`miso-2021-2025-realized-t1h-d53-sectorgate-d51ratio`** | `6ea92547eaa62559` | differs in `ccs_retrofit_capex_co2_scaling` ALONE; inert by §4 |
| `nyiso-t1h` | `nyiso-2021-2025-realized-t1h-d45r` (D45-R) | **`nyiso-2021-2025-realized-t1h-d52-devintage`** | `911371a8cf23d5c3` | differs in `ccs_retrofit_capex_co2_scaling` ALONE; inert by §4 |
| `ercot-t1f` | `ercot-2026-2030-d46-remeasure` (D46) | **`ercot-2026-2030-d50-ccscapex`** | `0c3e9cd5b5993bdf` | **EQUAL** to the post-D60 bare key |
| `neiso-t1f` | `neiso-2026-2030-d46-remeasure` (D46) | **`neiso-2026-2030-d50-ccscapex`** | `18515067bf4d2fbe` | **EQUAL** |
| `pjm-t1f` | `pjm-2026-2030-d45r-remeasure` (D45-R) | **`pjm-2026-2030-d50-ccscapex`** | `167e65187f32056b` | **EQUAL** |

The three t1f renames are the four-arms-already-paid half of D50 §6.3: those
arms **are** the post-flip bare bundles, at the post-flip bare key.

### Class B — NO-OP: the bare key keeps its run; only the recipe's resolved key moves

`ercot-t1h`, `caiso-t1h`, `neiso-t1h`, `pjm-t1h` and all five `*-t1x` keys.
The only D60 arm reaching them is the CCS default, inert by §4, and no committed
leg carries it. The verdict row, its run, its determination and every scored row
stay exactly as they are; the recorded `cache_epoch` remains the key the run was
**solved at**, which stays a true statement. The post-D60 recipe key is recorded
in the finding's blast-radius reconciliation, not written into the stamp — a
stamp naming a key at which nothing was ever solved would be worse than a
disclosed drift. **This is D50 §6.2's own disposition for the 108 configs whose
horizon ends ≤ 2027: "a cache-key formality, never a re-measure on the merits."**

**Pre-existing staleness, disclosed and NOT repaired here.** `neiso-t1x` and
`nyiso-t1x` already fail to re-resolve at HEAD *before* D60 touches anything:
their committed configs carry two fields deleted under rule 26
(`caiso_bidir_intertie`, `renewable_buildout_pace`) and predate D44's own flip.
`ercot-t1x`, `miso-t1x` and `pjm-t1x` carry no hex epoch at all. Repairing the
t1x stamps is a different lane's question and is **routed**, not absorbed.

### Class C — RE-SOLVE (the Q42 §6.3 residual + the two ISO-override legs)

| leg | key it must land on | rate | why it cannot rename |
|---|---|---:|---|
| `miso-t1f` 2026–2030 | **`3f85ecc45d90c248`** | ~65 min (D45-R 65.0 / D50 64.3) | D50's MISO arm is CCS-only (`f3f96e14bb75c9d9`); the ratio is not in it |
| `nyiso-t1f` 2026–2030 | **`19a9690bb12c8459`** | ~12 min (D45-R) | no NYISO CCS arm exists; the two gates are not in any t1f leg |
| `caiso-t1f` 2026–2030 | **`29f8eb372810195f`** | 22.6 min (D46) | D50 never solved CAISO |
| `neiso-t3` GOLDEN-3 2026–2050 | **`f04fd06348e1623d`** | 33.0 min (D47) | the 25-year golden was never solved on the flipped default |

Total **≈ 132.6 min**. D50 §6.3's card said **67.6 min ≈ 1.1 h** for CAISO t1f +
NYISO t1f + GOLDEN-3; D60 adds **MISO t1f (~65 min)**, which D50's card did not
carry because Q40 had not been ruled when that card was priced. Stated as an
overrun against the card, with its cause, rather than buried: **the 1.1 h is the
Q42-only residual; the batch is ~2.2 h because Q40 forces a MISO t1f re-solve
D50 costed as a rename.** Run sequentially, one solve at a time in this session
(rule 12: years never parallel; and a per-plant multi-zone t1f already peaks at
~10 GB).

---

## 6. Expected FC rows, per re-solve — pre-declared from the committed arms' evidence

### 6.1 `miso-t1f` — the ratio's I7/I12 rows are the ONE place a board row may move

The CCS half is pre-declared a **measured null**, on D50 §4b's own MISO leg:
0 rows / 0 MW converted in every year against the control's 4,631.1 MW, with the
FC-1 invariant detail string **byte-identical** and reserve margins identical to
six decimals. The control's committed ledger reproduces it — 2028 12 rows /
2,985.2 MW, **all 12 CC_CHP**; 2029 18 rows / 1,645.9 MW, 14 CHP; 2030 zero — so
seam 2 alone reaches almost all of it. **P1: MISO converts 0 MW in 2028, 2029
and 2030.**

The ratio half is where movement is expected, in the sign D51 §7 named (position
LONGER, exits HARDER). The control's FC-1 detail is the arithmetic base:

| year | accredited firm (control) | requirement | margin (I12) |
|---|---:|---:|---:|
| 2026 | 118,091 | 129,467 | −8.1 % |
| 2027 | 118,727 | 130,809 | −8.6 % |
| 2028 | 119,698 | 132,275 | −8.9 % |
| 2029 | 128,138 | 133,871 | −3.6 % |

The ratio moves 0.854600 → 0.893436, i.e. **×1.04544**, applied to the internal-supply
term inside `accredited_firm_capacity_mw`; the requirement is untouched. That
gives a strict **UPPER bound** on each year (the whole ledger scaled, which
over-states it because non-internal terms do not scale):

- **P2 (HIGH):** I7 stays FAIL in **2026, 2027 and 2028** — upper bounds 123,452 /
  124,117 / 125,133 MW against 129,467 / 130,809 / 132,275, short by ≥ 6.0 / 6.7 /
  7.1 GW. *Falsifier: any of those three clearing.*
- **P3 (MED):** I7 **2029** is the single row that can flip — upper bound
  133,957 vs requirement 133,871, i.e. **+86 MW at the ceiling**. Either outcome
  is admissible and neither is a STOP; a flip in the OTHER direction (2029
  falling further short) is a STOP.
- **P4 (HIGH):** I12 stays FAIL in every year — upper-bound margins −4.65 / −5.12 /
  −5.40 / **+0.06** %, and even 2029's ceiling lands below the band floor of
  +0.7 %. **FC-1 therefore stays `FAIL ['I12','I7']` and FC-2 row1 stays FAIL.**
- **P5 (MED):** FC-2 **row4** (backstop share 33.6 % > 30 %) moves **DOWN** — the
  longer position needs less adequacy backstop, the direction D51 §3.3 measured
  on t1h (BLK-10 backstop 2,414.8 MW → **0**). A crossing to PASS is admissible;
  a move UP is a STOP.
- **P6 (HIGH):** determination **HOLD → HOLD**; FC-7 stays CAVEAT (the unattested
  DOF skeleton, a MISO lane's item under rule 25); FC-8 stays CAVEAT (~65 min,
  ~10 GB).

### 6.2 `nyiso-t1f` — D52's +0.24 % requirement, and the CHP exclusion

- **P7 (HIGH):** the requirement in **2026–2030 is entirely beyond NYSRC Table
  D.2**, so `nyiso_requirement_vintage_factors` HOLDS-LAST at the 2025/26 pair's
  ratio 1.244 × 0.870 = **1.0823**, **+0.24 %** over the shipped composite
  (D52 §8(1), card C-A), and `nyiso_requirement_forecast_peak` returns the model's
  own peak UNCHANGED (the same float object) outside the table. The two gates are
  therefore a **+0.24 % requirement bump and nothing else** on this horizon.
- **P8 (HIGH):** the CCS half is a **composition-only** change, on this lane's own
  zero-solve census (§6.5): NYISO's scaled bar removes essentially nothing
  (11.13 → 11.14 GW clears at the hour ceiling, the RGGI signature D50 §1 named),
  and the whole movement is seam 2 — **4.31 GW of CHP** leaves an 11.20 GW
  eligible pool. The control converts 2,994.7 / 2,997.1 / 2,979.7 MW in
  2028/29/30 (37 / 18 / 8 rows, of which **20 / 8 / 3 are CHP**), i.e. the
  **3 GW/yr cap binds every year**.
- **P9 (MED):** under the repair **2028 and 2029 stay at the cap** (2,900–3,000 MW
  each) with **zero CHP rows**, and **2030 falls below it** — the non-CHP pool
  that clears the ceiling is **6.86 GW**, so two capped years exhaust it and 2030
  lands in **[0, 1.1] GW**. Window total pre-declared **6.8–7.1 GW** against the
  control's 8,971.5 MW. *Falsifier: any CHP row converting, or a window total
  above 8.0 GW.*
- **P10 (HIGH):** **`nyiso-t1f` is currently `PROMOTE`.** Every gated FC-1/FC-2 row
  is capacity-side and a retrofit preserves MW, zone and accreditation (D50 §5's
  reasoning, HIT in all four arms), and +0.24 % on the requirement is far inside
  every band; so the determination is pre-declared **PROMOTE → PROMOTE**. **A
  move off PROMOTE is a STOP-and-report** — reported at full magnitude, never
  reverted (rule 1: a structurally-correct mechanism stays in).

### 6.3 `caiso-t1f` — untested, pre-declared from this lane's own census

CAISO carries **no row in D50 §1's census** (that census covered ERCOT / NEISO /
PJM / MISO only), so this lane **ran the same instrument for CAISO and NYISO**
(zero solve, §6.5) rather than pre-declaring from a table that does not contain
them.

- **P11 (HIGH):** CAISO is a **carbon-priced ISO** ($34.37 / $36.78 / $39.36 per t
  in 2028/29/30) and shows the NEISO signature exactly: the scaled bar removes
  **nothing** (16.38 GW eligible → 16.38 GW clears flat → **16.38 GW clears
  scaled**), so seam 1 is inert here and the entire change is **seam 2**, which
  removes **2.71 GW of CHP** and leaves **13.68 GW** clearing.
- **P12 (MED):** because 13.68 GW ≫ 3 GW/yr × 3 yr, the **cap keeps binding in
  every year** and the change is **composition-only**: the control converts
  2,997.1 / 2,997.9 / 2,857.3 MW (37 / 12 / 11 rows, of which **26 / 5 / 8 are
  CHP**); the arm is pre-declared at **2,850–3,000 MW per year, zero CHP rows,
  window 8.6–9.0 GW** against the control's 8,852.3 MW. *Falsifier: any CHP row
  converting, or a year below 2.5 GW.*
- **P13 (HIGH):** determination **HOLD → HOLD**; the FC-1/FC-2 gated rows are
  capacity-identical for the same reason as every other arm.

### 6.4 `neiso-t3` GOLDEN-3 — the FC map should not move

- **P14 (HIGH):** D50's NEISO t1f leg measured the cap binding in every year with
  composition-only movement (P5 HIT: 2,982.2 / 2,996.7 / 2,982.6 MW, all inside
  the pre-declared band). The GOLDEN-3 control's own 25-year ledger converts
  **11,208.9 MW total**, concentrated in 2028–2031 (2,999.6 / 2,994.4 / 2,948.6 /
  2,266.3 MW) and **nothing after 2031** — of which only **377.1 MW (3.4 %) is
  CHP**. The repair therefore removes a small candidate slice from a pool that
  is already cap-bound.
- **P15 (MED):** 2028–2030 stay at the cap; the window through 2031 loses **at
  most ~0.4 GW** (the CHP MW, partly or wholly replaced by residual non-CHP
  hosts); conversion still ends by **2032**. *Falsifier: total conversions
  outside 10.4–11.3 GW, or any year after 2032 converting.*
- **P16 (HIGH):** **the FC map does not move** — determination **HOLD → HOLD**,
  the same four FC-1/FC-2/FC-3/FC-4 reasons, FC-5/FC-6 dispositions carried per
  D47's attestation rules (the pre-declared follow-up attestation under the Q37
  limb).

### 6.5 The census instrument, disclosed

`scripts/probes/_capxd50_scaled_ceiling_census.py --isos CAISO NYISO`, run at
HEAD on the rebuilt base fleets through the same resolved golden-posture configs
the legs solve (control key echoed and matched: CAISO `772b1e5abc7fc80c`). It is
the D50 §1 instrument unmodified; **`captured_ref` = 0.32319 t/MWh**, the same
constant, is echoed by the run.

| ISO · year | gas $/MMBtu | carbon $/t | capex $/kW | eligible | clears FLAT | clears SCALED | clears SCALED+noCHP | CHP eligible | min er clearing |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| CAISO 2028 | 4.87 | 34.37 | 1,323.6 | 16.38 GW | 16.38 | 16.38 | **13.68** | 2.71 | 0.358 |
| CAISO 2029 | 5.04 | 36.78 | 1,271.8 | 16.38 | 16.38 | 16.38 | **13.68** | 2.71 | 0.358 |
| CAISO 2030 | 5.68 | 39.36 | 1,232.3 | 16.38 | 16.38 | 16.38 | **13.68** | 2.71 | 0.358 |
| NYISO 2028 | 4.22 | 27.06 | 1,323.6 | 11.20 | 11.13 | 11.14 | **6.86** | 4.31 | 0.350 |
| NYISO 2029 | 4.39 | 28.96 | 1,271.8 | 11.20 | 11.17 | 11.14 | **6.86** | 4.31 | 0.350 |
| NYISO 2030 | 5.03 | 30.98 | 1,232.3 | 11.20 | 11.17 | 11.14 | **6.86** | 4.31 | 0.350 |

A ceiling clearance is a NECESSARY condition, never a prediction — the offer
surface decides the rest — so this bounds each arm from above.

---

## 7. STOPs (binding; checked before any registration)

1. **Any bare key ≠ its §2 pre-declared value** after the flip lands.
2. **Any Class-A rename whose committed leg is not byte-identical on every
   scored row to what the post-D60 bare recipe would produce.** The three t1f
   renames are proved by key EQUALITY; the two t1h renames by the §4 code gate
   (a one-field difference the 2028 guard makes unreachable). If either t1h
   byte-identity is in doubt at execution time, **RE-SOLVE it and say so** —
   12–25 min beats a wrong rename.
3. **Any FC-3 / FC-1 row moving in a direction the committed arm did not show** —
   specifically: MISO I7 2029 falling further short (P3), FC-2 row4 rising (P5),
   any CHP row converting under the repair (P9 / P12), any conversion count
   rising above a control year's.
4. **Any keeper or backcast ARTIFACT moving**, and — for the two ISO overrides
   only — any movement of `ScenarioConfig()`, the bare backcast key, or another
   ISO's resolved forecast key. Asserted by test: (a) MISO forecast resolves the
   ratio ON and every other ISO OFF; (b) NYISO forecast resolves both gates ON
   and every other ISO OFF; (c) ERCOT / PJM / CAISO / NEISO carry neither the
   ratio nor the NYISO gates in their overrides; (d) a plain backcast of MISO and
   of NYISO still coerces all three fields to their dataclass defaults. The two
   pins DO move under Q42 alone, by §3, and that is not this STOP.
5. **`check_cache_key_registration.py --base origin/main` or
   `check_mechanism_matrix.py` failing.**
6. **A determination moving** anywhere the pre-declaration did not admit it —
   above all `nyiso-t1f` off PROMOTE (P10). A STOP is *report and escalate*, not
   revert.

---

## 8. What this lane commits

The flip commit (three edits + the (b′-1) line + the 26 pin files + tests +
CLAUDE.md step-2 and `model-methodology-spec.md` §5.6 dated amendments +
CHANGELOG + the three matrix rows' cells); the five Class-A renames with priors
preserved at `-pre-d60`; the four re-solves scored, verdicted and registered;
`FINDING-capx-d60-2026-09-05.md` grading every prediction above at full
magnitude. **No keeper, no shard promotion field, no `complete` / `final`
marker, no freeze, no new field, no parameter value, nothing against measured
H1-2026** (rule 22: t1h 2021–2025, t1f 2026–2030, t3 2026–2050 — all forecast
mode, no measured actuals).

---

## Addendum A (2026-09-05) — written AFTER the three edits were applied LOCALLY and every bare key was re-resolved through the REAL harness path, and BEFORE any solve, any commit of the flip, and any rename

§2 emulated each post-arm key by reconstructing the bare key's own committed
`run_config.json` and setting the armed field(s). That is exact **only when the
committed control's resolved posture already equals the bare recipe's**. It does
for twelve of the thirteen keys. It does **not** for `miso-t1f`, and the
pre-declaration is corrected here at full magnitude rather than quietly.

### A.1 CORRECTION — `miso-t1f`'s post-D60 key is `b1a73a087064ffd8`, not `3f85ecc45d90c248`

**Cause, measured:** MISO's `default_scenario_overrides` already carry
`retirement_sector_gate: True` — landed at HEAD by **capx D53** on 2026-09-05,
*before* this lane opened. The committed control `miso-2026-2030-d45r-remeasure`
predates D53 and records the field absent, so reconstructing from it and adding
only D60's two arms understated the recipe by exactly one field. Forcing the
sector gate back off returns **`3f85ecc45d90c248`**, §2's value, which confirms
the diagnosis to the digit and confirms nothing else moved.

**This is a defect in my own pre-declaration, not a surprise in the rulings.**
D53 §6.1 stated the consequence in terms when it armed the gate: *"the MISO t1f
leg (2026–2030) was not re-solved here — its next solve resolves the gated screen
by construction."* D60's MISO t1f re-solve **is** that next solve. Nothing about
Q40, Q41 or Q42 changes; no STOP fires; the correction is to the number I wrote,
and it is graded against me in the finding.

### A.2 The harness-path resolution, for every key — the authoritative table

Resolved through `run_full_horizon.reference_config(iso, …, golden_posture=True)`
→ `apply_iso_scenario_defaults` → `cache_key()` for t1f/t3, and
`run_capacity_hindcast.build_config(iso, 2021, 2025, "realized", vintage=2020,
entry_screen_diagnostics=True)` → `apply_iso_scenario_defaults` → `cache_key()`
for t1h (the recipe every committed t1h leg carries).

| bare key | §2 pre-declared | harness-resolved | verdict |
|---|---|---|---|
| `ercot-t1f` | `0c3e9cd5b5993bdf` | `0c3e9cd5b5993bdf` | **HIT** |
| `neiso-t1f` | `18515067bf4d2fbe` | `18515067bf4d2fbe` | **HIT** |
| `pjm-t1f` | `167e65187f32056b` | `167e65187f32056b` | **HIT** |
| `caiso-t1f` | `29f8eb372810195f` | `29f8eb372810195f` | **HIT** |
| `nyiso-t1f` | `19a9690bb12c8459` | `19a9690bb12c8459` | **HIT** |
| `neiso-t3` | `f04fd06348e1623d` | `f04fd06348e1623d` | **HIT** |
| `ercot-t1h` | `82b27751be747552` | `82b27751be747552` | **HIT** |
| `caiso-t1h` | `7da58199acd362ee` | `7da58199acd362ee` | **HIT** |
| `neiso-t1h` | `f3988df3068020d1` | `f3988df3068020d1` | **HIT** |
| `pjm-t1h` | `7297dcb3b92be3fb` | `7297dcb3b92be3fb` | **HIT** |
| `miso-t1h` | `687bd75f2828bea1` | `687bd75f2828bea1` | **HIT** |
| `nyiso-t1h` | `6e70a637b3465542` | `6e70a637b3465542` | **HIT** |
| `miso-t1f` | `3f85ecc45d90c248` | **`b1a73a087064ffd8`** | **MISS — §A.1** |

### A.3 STOP 2 discharged: the two t1h renames are byte-identical, measured field-by-field

The harness-resolved bare recipe was diffed field-by-field against each rename
target's own committed `run_config.json` (ignoring only fields ABSENT from the
older config that resolve to a cache-neutral `False`/`None` — schema growth, not
posture):

- **`miso-t1h` ← `miso-2021-2025-realized-t1h-d53-sectorgate-d51ratio`**: the
  **only** substantive difference is `ccs_retrofit_capex_co2_scaling: False →
  True`. The committed rider records that field EXPLICITLY `False` (it was solved
  after D50 built it), so the pair is a clean one-field A/B.
- **`nyiso-t1h` ← `nyiso-2021-2025-realized-t1h-d52-devintage`**: the **only**
  difference is `ccs_retrofit_capex_co2_scaling: <absent> → True`.

Both fields are unreachable below 2028 (§4), so **every scored row of both
targets is byte-identical to what the post-D60 bare recipe would produce**. STOP
2 does not fire and neither leg is re-solved.

### A.4 The mechanism delta of each re-solve, stated exactly

| leg | control | post-D60 key | fields that differ |
|---|---|---|---|
| `miso-t1f` | `8d8bc63a0d4378a9` | **`b1a73a087064ffd8`** | `retirement_sector_gate` (D53), `adequacy_accounting_ratio_dated_net` (Q40), `ccs_retrofit_capex_co2_scaling` (Q42) — **three** |
| `nyiso-t1f` | `cc7d1050a8090c76` | `19a9690bb12c8459` | `nyiso_requirement_forecast_peak`, `nyiso_requirement_vintage_factors` (Q41), `ccs_retrofit_capex_co2_scaling` (Q42) — **three** |
| `caiso-t1f` | `772b1e5abc7fc80c` | `29f8eb372810195f` | `ccs_retrofit_capex_co2_scaling` — **one** |
| `neiso-t3` | `67678e58b2d0526c` | `f04fd06348e1623d` | `ccs_retrofit_capex_co2_scaling` — **one** |

### A.5 §6.1 EXTENDED — the MISO t1f leg carries a third mechanism, so a third expectation is pre-declared

§6.1 pre-declared the CCS half (P1: 0 MW converted) and the ratio half (P2–P6).
The sector gate is the third, and its expectation is pre-declared **now, before
the solve**, from D53's own measured record:

- **P17 (HIGH):** the gate is a **pure candidate-set partition** — it removes
  regulated-utility (EIA-860 Sector 1) units from the *merchant* economic screen
  and adds no unit to it. Where the reliability floor has **no headroom** it
  therefore moves **nothing**: D53 §2.1/§2.3 measured every retirement row and
  every non-screen row byte-identical on the shipped posture. *Falsifier: total
  economic-exit MW rising in any year.*
- **P18 (MED):** where the floor **does** have headroom — which is exactly what
  the Q40 ratio buys (D51 opened 0.48 GW of it on t1h) — the gate **re-targets
  which units take that headroom**, drawing from the merchant pool instead of at
  random (D53 §3: 99.8 % vs 1.1 % plant-grain precision). So on this leg the two
  D60/D53 mechanisms interact by design, and any exit-composition change is
  attributed to the gate, any exit-volume change to the ratio. *Falsifier: a
  sector-1 plant appearing in any `pipeline_events` economic-screen row.*
- **P19 (HIGH):** the gate reaches **exits only**; the additions screen, the
  requirement and the retrofit ledger are untouched by it, so P1–P6 stand as
  written.

Nothing else in §§1, 3–5, 6.2–6.5 or 7 changes. `miso-t1f`'s prior is still
preserved at `miso-t1f-pre-d60`; the leg still re-solves; STOP 1 now reads
against `b1a73a087064ffd8`.

---

## Addendum B (2026-09-05) — written BEFORE the GOLDEN-3 re-solve is launched: the T3 attestation this lane will author, pre-declared

Rubric §5 names the **producing session** as the T3 attestation's author, and D47 §0
established the discipline that makes such an attestation honest: **pre-declare it before
the run exists, and record any assertion that turns out false as false, failing FC-7 on it
at full magnitude.** D60 IS the producing session for `neiso-t3` at `f04fd06348e1623d`, so —
unlike D47, which had to attest another session's bundle — it can author in the ordinary
way. What it may not do is decide the assertions after reading the verdict. They are
therefore fixed here, before the solve.

**The six assertions, and what each will be read from — bytes only, no judgement call at
authoring time:**

| assertion | true iff |
|---|---|
| `dof_ledger_complete` | `dof_ledger.json`, built by the committed `scripts/build_forecast_dof_ledger.py` from THIS bundle's own `run_config.json`, carries **0 UNIDENTIFIED**, **0 unattested** and **0 entries whose identification is `residual`** |
| `run_config_reproducible` | the bundle's `run_config.json` records `mode=forecast`, a clean git tree at a named sha, and a `cache_key` equal to `f04fd06348e1623d` — the value §A.2 pre-declared and the harness path resolves |
| `honest_unfit_referenced` | the run's own `full_horizon_summary.json` invariant record is carried into the verdict, and the FC rows that fail are named in the finding against `program-status.json`'s `honest_unfit` block rather than only in the sidecar |
| `quarantine_attested` | every solved year lies in 2026–2050, i.e. **forecast mode, no measured actuals, no holdout tier touched** (rule 22); asserted from `solved_years` |
| `no_off_registry_knobs` | every solve-affecting non-default field in `run_config.json` appears in `ScenarioConfig`; no env knob, no per-plant dict, no `getattr` fallback (rule 24) |
| `registered` | the run is registered through the single `scripts/register_forecast_run.py` path and its verdict key is `neiso-t3` |

**Pre-declared expectation (P20, HIGH):** `dof_ledger_complete` reads **true** with the same
**7 IDENTIFIED / 0 UNIDENTIFIED** ledger D47 recorded for `bau-d46` — `forecast_xyear_warmstart`
plus NEISO's six published ORDC/scarcity registry fields. The D60 flip adds **no** eighth
entry, because `ccs_retrofit_capex_co2_scaling` is now at its **dataclass default** and the
ledger enumerates non-default solve-affecting fields. *Falsifier: any UNIDENTIFIED entry, or
an entry for the CCS field.* Should the ledger come back with an UNIDENTIFIED row, the
assertion is written **false** and FC-7 fails on it — the attestation is not re-scoped to fit.

**And the one thing this attestation will NOT claim:** that the run's FC-5 (external
corridor) or FC-6 (driver response) rows are satisfied. Both were `SKIPPED` on `bau-d46` for
want of a committed benchmark-corridor table and a paired driver battery, neither of which
D60 builds; they stay SKIPPED and are reported as such, exactly as the preserved record has
them (`neiso-t3` carries them as caveats today). D60 produces no FC-5/FC-6 evidence and
claims none.

---

## Addendum C (2026-09-05) — DIRECTOR AMENDMENT 1 (r#38) absorbed: the fifth re-solve `pjm-t1f`, pre-declared BEFORE it is run

Amendment 1 resolves D60's STOP 1 by removing its cause rather than waiving it: **D57 has
landed and its owner ruling Q44 armed the joint PJM posture through `_pjm_config`
overrides**, so PJM forecast surfaces are free this window and `pjm-t1f` becomes D60's fifth
re-solve. Q44 is D57's arming, already landed — D60 arms nothing new (§1 unchanged: Q40, Q41,
Q42 only).

### C.1 The key, re-verified at HEAD through the harness path — **`09996eca71ee80fd`, confirmed**

`reference_config("PJM", 2026, 2030, False, golden_posture=True)` →
`apply_iso_scenario_defaults` → `cache_key()` at this branch's HEAD (which carries D57's
`_pjm_config` overrides **and** D60's Q42 flip) resolves to **`09996eca71ee80fd`** — exactly
the value Amendment 1 names, and exactly the value §4 of the finding recorded when STOP 1
fired. No difference to report; the leg runs on that key.

### C.2 The mechanism deltas, stated exactly — FOUR against the control, THREE against the D50 arm

| against | key | fields that differ |
|---|---|---|
| the bare control `pjm-2026-2030-d45r-remeasure` | `321f04e9060787f0` | `ccs_retrofit_capex_co2_scaling` (Q42) · `pjm_accreditation_design_vintage` (D48) · `pjm_demand_response_supply` (D48) · `capacity_market_supply_clearing_by_iso={'PJM': True}` (D57) — **four** |
| the D50 CCS arm `pjm-2026-2030-d50-ccscapex` | `167e65187f32056b` | the three D48/D57 gates only — the CCS half is already in it |

**This is the attribution instrument.** Every FC row that moves is assigned to ONE mechanism
by differencing against whichever committed record isolates it: the D50 arm isolates Q42 on
this exact horizon, and D57's arms A/B isolate the clearing + D48 pair on 2021–2025. Nothing
is attributed by inference (Amendment 1 item 3).

### C.3 The FC rows, pre-declared — and this is the FIRST solve in which both act together on 2026–2030

The control's own gated rows are the base:

| row | control `pjm-t1f` | D50 arm (Q42 alone, same horizon) |
|---|---|---|
| FC-1 | FAIL `['I12','I7']`; I12 out 2027 **−11.2 %**, 2028 **−13.5 %**, 2029 **−13.1 %**, 2030 **−13.0 %**; I7 2027 accredited firm 145,259 < requirement 145,509 | FAIL `['I12','I7']`; I12 2028 **−13.8 %**, 2029 **−13.5 %**, 2030 **−12.6 %** (2027 identical at −11.2 %) |
| FC-2 row1 / row3 / row4 | FAIL / PASS / **FAIL 43.9 %** | FAIL / PASS / **FAIL 48.9 %** |
| FC-7 / FC-8 | PASS / CAVEAT (9.0 GB) | PASS / CAVEAT (9.0 GB) |
| determination | HOLD | HOLD |

- **P21 (HIGH) — the CCS half reproduces the D50 arm's direction.** Its window falls
  3,584.7 → 909.8 MW, 2028 to zero, and its FC-2 row4 backstop share rises 43.9 → **48.9 %**
  (D50 §4.2: the arm substitutes adequacy-backstop CT for economic-pipeline gas_ct in 2030).
  *Falsifier: row4 falling below the control's 43.9 % on the CCS half's account alone.*
- **P22 (HIGH) — the clearing half pushes FC-2 row4 the OTHER way, and it should dominate.**
  D57 §3.5 measured the mechanism this leg newly carries: once the screen reads a **positive**
  clearing price, a new gas CC's capacity term becomes **+$28,715/MW-yr** instead of $0 and
  its margin flips **−$17,947 → +$10,768/MW-yr**, so the *economic entry pipeline* builds
  where it previously did not (PJM t1h: gas_cc additions 8.118 → **12.118 GW**). Administrative
  backstop build is what fills a gap the economic screen declines; paying entry a real
  capacity price is precisely the thing that stops it. **So FC-2 row4's backstop share is
  pre-declared DOWN against the control's 43.9 %** — the two halves oppose, and the clearing
  half is the larger operand. *Falsifier: row4 above 48.9 %, i.e. the CCS half dominating.*
- **P23 (MED) — I7 and I12 improve but do not clear.** Accreditation-design devintage plus
  DR-as-supply both **raise** counted supply (D48's construction: UCAP + DR counted as supply
  with the peak un-netted), and the clearing half adds real entry, so accredited firm rises
  against an unchanged requirement in every year. The control is 11.2–13.5 points below an
  I12 band whose floor is −11.1 %/−9.7 %, and 250 MW short on I7 in 2027 — so **2027 I7 is
  the single row that can clear** (250 MW on a 145 GW ledger), while 2028–2030 stay short.
  **FC-1 therefore stays `FAIL ['I12','I7']`** unless every year clears, which it cannot.
  *Falsifier: any year's I12 moving further NEGATIVE than the control's.*
- **P24 (HIGH) — determination HOLD → HOLD**, FC-7 PASS, FC-8 CAVEAT (~9 GB, ~28 min).
- **P25 (MED) — the exit composition follows D57's t1h signature, not the control's:** coal
  retained (a cleared unit is paid $28–60/kW-yr, above its zero-E&AS gap) and **gas steam
  over-exiting** (at zero E&AS its offer is its whole bar, above every clearing price the
  window forms). This is D57's own named open item — the E&AS operand, routed to the D12
  scarcity-basis lane — and D60 inherits it, measures it on the forecast horizon and
  **claims no repair of it**. *Falsifier: gas_st exits at or below the control's.*

### C.4 STOPs for this leg

STOP 1 re-reads against `09996eca71ee80fd` (confirmed above). Additionally: **any FC-2 row4
move ABOVE 48.9 %** (P22's falsifier — it would mean the clearing half did not reach the
entry screen on this horizon, which contradicts D57's measured +$28,715/MW-yr) and **any I12
year more negative than the control's** (P23's falsifier) are STOPs — reported and escalated,
never reverted.

### C.5 Order, and the golden's protection

Remaining legs, sequential (rule 12), longest first except the golden: `miso-t1f` (~65, **in
flight, already on `b1a73a087064ffd8`**) → `nyiso-t1f` (~12) → `caiso-t1f` (~23) →
`pjm-t1f` (~28) → `neiso-t3` GOLDEN-3 (~33). Per Amendment 1 item 2, **GOLDEN-3 runs last and
is never left half-registered**: if it cannot complete inside this window, the finding says so
and the director charters it separately. Its prior stays at `neiso-t3` untouched until a
complete bundle exists.

### C.6 Hygiene, re-stated under Amendment 1 item 4

Step 0 was already a no-op at this lane's base (§0 of this pre-declaration recorded it, with
the commit that did the work: `0b51f28e` — the audit desk's Y-7 lane). **miso-217's two new
reds (`offer_curves.py`, `test_miso_intermediate_gas_offer_margin.py`) are NOT touched** —
the owner's MISO track owns them, and this lane has not formatted, edited or staged either.
