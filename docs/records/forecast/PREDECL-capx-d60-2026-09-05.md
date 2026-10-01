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

---

## Addendum R2 (2026-09-05) — the D60-R2 relaunch: STATE AT START, before any solve, any row and any registration

D60's own session died after landing its flip commit, four renames and two of five
re-solves; the first relaunch (**D60-R**) never launched; **D60-R2** is this session
(director r#39 amendment 2). This addendum is the relaunch's first commit and it carries
**zero solve**: it establishes, from the committed record alone, that the pins D60 wrote
are still the pins HEAD resolves — because every remaining leg's STOP 1 reads against
them, and a relaunch that inherited drifted keys would spend three LPs on the wrong
recipes.

### R2.1 The twin check — CLEAR

The charter's first instruction is a collision check: two writers on `ff-verdicts.json` is
the one collision this program cannot absorb. Executed at session start with
`git fetch origin --prune`:

- **No `claude/capx-d60r*` branch exists on origin** — neither D60-R's stem nor this
  session's. (The fetch pruned a stale remote-tracking ref for this session's own branch
  name; origin has never held it.)
- The only commits anywhere mentioning **"D60-R"** are the director's own two records
  (`ca3a8703`, `7dd401d9`, r#39 amendment 2), and **both are on the director branch, not
  on `origin/main`** — they are the issuance of this session, not a twin's output.
- **Two owner-track merges are newer than `c3addecc`**, neither a twin:
  `1b9af38b` (PR #4819, `caiso-252`) — **one file, +229 lines**, the backcast PRECOMMIT
  `docs/handoffs/PRECOMMIT-caiso252-c4-gas-nrmse-anatomy-2026-09-05.md`, touching no `src/`,
  no `scripts/` and no forecast surface; and **`6619fb4a` (PR #4817, the `nyiso-192`
  promotion), which merged DURING this session's first commit** and is handled in §R2.1a.
- No open branch is writing `ff-verdicts.json`.

No twin is mid-flight. D60-R2 proceeds.

### R2.1a The `nyiso-192` promotion merged mid-commit — kept verbatim, and it moves no forecast key

The charter named this one in advance ("the pending nyiso-192 promotion (if it merges) moves
NYISO's marker and gate-(a) row — rebase before every push and keep its edits verbatim"). It
merged as `6619fb4a` while this addendum was being written, so this lane's base is
`6619fb4a`, not `1b9af38b`, and the §R2.2 table below was **re-measured at the new base**
rather than left standing on the old one.

What it changed on the ONE forecast surface it touches, `program-status.json`, read as a
structural diff of the JSON rather than as a text diff — **NYISO only, and records-only**:
`isos.NYISO.marker_complete` `True → False`; `gate.a_keeper_marker.status` `pass → fail`
with its `detail` / `read_live_at` / `corrected_by` re-stamped onto the new keeper;
`gate.closed_on` gaining one entry; `isos.NYISO.keeper`
`2026-09-05-nyiso-189-steam-identity → 2026-09-05-nyiso-192-astoria-panel`; the `headline`,
`gate_reading` and `sources` prose; and a new `nyiso193_promotion_withdrawal` block whose own
note records that **no forecast run was solved or re-scored**. **No `isos.*` entry of any
other ISO moves, and no verdict, no cache key and no bundle is touched.**

Two consequences this lane states rather than absorbs:

1. **It changes nothing D60-R2 does.** Every one of this lane's edits is a forecast verdict
   row, a `-pre-d60` prior, a bundle or a document. It authors **no marker, no gate-(a) row,
   no keeper and no `complete` / `frontier` field**, and it rebases before every push so
   these edits survive verbatim.
2. **It is a start precondition of a DIFFERENT card.** `T3-NYISO-GOLDEN` Amendment 1 makes
   `complete.NYISO` a start precondition, and this merge withdraws it. That is the
   director's call to make on its own card, not this lane's, and it is flagged here only so
   the release decision after D60 closes is made with it in view.

### R2.2 Every bare forecast key re-resolved through the harness path at HEAD `6619fb4a` — **ZERO DRIFT**

Resolved exactly as Addendum A §A.2 resolved them:
`run_full_horizon.reference_config(iso, 2026, 2030|2050, False, golden_posture=True)` →
`apply_iso_scenario_defaults(cfg, iso)` → `cache_key()` for t1f/t3, and
`run_capacity_hindcast.build_config(iso, 2021, 2025, "realized", vintage=2020,
entry_screen_diagnostics=True)` → `apply_iso_scenario_defaults(cfg, iso)` → `cache_key()`
for t1h. Config construction only; no fleet build, no solve.

| bare key | D60's pin (source) | resolved at HEAD `6619fb4a` | verdict |
|---|---|---|---|
| `ercot-t1f` | `0c3e9cd5b5993bdf` (§A.2) | `0c3e9cd5b5993bdf` | **HIT** |
| `caiso-t1f` | `29f8eb372810195f` (§A.2) | `29f8eb372810195f` | **HIT** — leg 3 runs on it |
| `pjm-t1f` | `09996eca71ee80fd` (Addendum C.1) | `09996eca71ee80fd` | **HIT** — leg 4 runs on it |
| `miso-t1f` | `b1a73a087064ffd8` (§A.1 correction) | `b1a73a087064ffd8` | **HIT** — leg 1, registered |
| `nyiso-t1f` | `19a9690bb12c8459` (§A.2) | `19a9690bb12c8459` | **HIT** — leg 2, registered |
| `neiso-t1f` | `18515067bf4d2fbe` (§A.2) | `18515067bf4d2fbe` | **HIT** |
| `neiso-t3` | `f04fd06348e1623d` (§A.2) | `f04fd06348e1623d` | **HIT** — leg 5 runs on it |
| `ercot-t1h` | `82b27751be747552` (§A.2) | `82b27751be747552` | **HIT** |
| `caiso-t1h` | `7da58199acd362ee` (§A.2) | `7da58199acd362ee` | **HIT** |
| `pjm-t1h` | `aef81c84c4609c76` (finding §3, D57's move) | `aef81c84c4609c76` | **HIT** |
| `miso-t1h` | `687bd75f2828bea1` (§A.2) | `687bd75f2828bea1` | **HIT** |
| `nyiso-t1h` | `6e70a637b3465542` (§A.2) | `6e70a637b3465542` | **HIT** |
| `neiso-t1h` | `f3988df3068020d1` (§A.2) | `f3988df3068020d1` | **HIT** |

And the four pinned defaults, against finding §6:

| config | finding §6 "after" | resolved at HEAD | verdict |
|---|---|---|---|
| `ScenarioConfig()` | `e5ecd4105ada3e58` | `e5ecd4105ada3e58` | **HIT** |
| `ScenarioConfig(mode="backcast")` | `6a2845e50951394e` | `6a2845e50951394e` | **HIT** |
| `ScenarioConfig(ccs_retrofit_capex_co2_scaling=False)` | `4c6b03ae098b6e3e` (unmoved) | `4c6b03ae098b6e3e` | **HIT** |
| same, backcast | `8211c72bb1960adc` (unmoved) | `8211c72bb1960adc` | **HIT** |

**Seventeen of seventeen, measured twice** — once at `1b9af38b` and again after rebasing
onto `6619fb4a`, with **identical results both times**. The assertion the charter asked for
is therefore a MEASUREMENT, not an argument: **both** owner-track merges landed since D60's
pins leave **every forecast key unmoved**, and so do the two (b′-1) protection rows. **STOP 1
stands unchanged for all three remaining legs**, reading against `29f8eb372810195f`,
`09996eca71ee80fd` and `f04fd06348e1623d`.

### R2.3 What the committed record already holds, and what D60-R2 owes

**Landed on main and NOT re-done** (verified in `ff-verdicts.json` and
`register_forecast_run.VERDICT_MAP` at HEAD): the flip commit `13f711bc` (Q40/Q41/Q42); the
four zero-solve renames `6fc29446` with the fifth reversed on STOP 1; leg 1 `e7412237`
(`miso-t1f` → `b1a73a087064ffd8`, run `miso-2026-2030-d60-arm`, **HOLD**); leg 2 `091023a3`
(`nyiso-t1f` → `19a9690bb12c8459`, run `nyiso-2026-2030-d60-arm`,
**PROMOTE-WITH-CAVEATS** on FC-7 alone — the P10 STOP); the finding's §§0–4, 6–7 (`84a0839b`).
Six `-pre-d60` priors exist and are untouched by this lane:

| prior | preserves |
|---|---|
| `ercot-t1f-pre-d60` | `ercot-2026-2030-d46-remeasure` (`873d8c0e6cab52ae`) |
| `neiso-t1f-pre-d60` | `neiso-2026-2030-d46-remeasure` (`6690e4d6d66bc819`) |
| `miso-t1f-pre-d60` | `miso-2026-2030-d45r-remeasure` (`8d8bc63a0d4378a9`) |
| `nyiso-t1f-pre-d60` | `nyiso-2026-2030-d45r-remeasure` (`cc7d1050a8090c76`, PROMOTE) |
| `miso-t1h-pre-d60` | `miso-2021-2025-realized-t1h-d53-sectorgate` (`c306ddc6d28c60c2`) |
| `nyiso-t1h-pre-d60` | `nyiso-2021-2025-realized-t1h-d45r` (`91686abe7a744a88`) |

**OWED, and the only thing this session writes:** three re-solves — `caiso-t1f`
(prior `caiso-2026-2030-d46-remeasure`, `772b1e5abc7fc80c`, HOLD → `caiso-t1f-pre-d60`),
`pjm-t1f` (prior `pjm-2026-2030-d45r-remeasure`, `321f04e9060787f0`, HOLD →
`pjm-t1f-pre-d60`), `neiso-t3` GOLDEN-3 (prior `neiso-2026-2050-t3-golden3-bau`,
`67678e58b2d0526c`, HOLD → `neiso-t3-pre-d60`); the Q37 attestation rows and the
artifact-only re-scores (Addendum D); the finding's §5 and §8.

### R2.4 The one environment fact worth recording

This container had **no `data/clean`** (it is derived and gitignored) and no installed
dependency set. Both were built before the first leg — `pip install -r requirements.txt`
plus an editable install of the package, then one `scripts/regenerate_clean.py` pass — the
D60 discipline of regenerating `data/clean` **once** before the first solve, not per leg.
Recorded because the wall-clock figures in §5 of the finding are per-leg solve times and do
not include it.

---

## Addendum D (2026-09-05) — DIRECTOR AMENDMENT 2 (r#39) absorbed: the seven Q37 attestation rows, pre-declared BEFORE any row is authored and before the first D60-R2 solve

Amendment 2 resolves leg 2's P10 STOP under **owner ruling Q37** (r#34, rubric §5 second
limb): *a follow-up lane may author an attestation iff pre-declared before authoring,
attestation row only, artifact-only re-score.* This addendum is that pre-declaration. It is
pushed **before a single row is written, before `caiso-t1f` is launched, and therefore before
any of the three outstanding legs' FC-7 rows have been read** — which is the whole point of
the sequence: D46 refused to author an instrument *after* reading that it failed a row, leg 2
refused it again, and Q37's limb exists so the fix can be taken in the honest order instead.

**What is being repaired, stated once.** FC-7's DOF-ledger row scores a ledger entry carrying
the literal token `unattested` **exactly as it scores a missing ledger** — CAVEAT at t1, FAIL
at t3 (`scripts/forecast_verdict.py::_dof_ledger_row`). `scripts/build_forecast_dof_ledger.py`
emits that token for any non-default solve-affecting field with **no curated identification
row**, and it *reports* identification, never supplies it (rule 21). So arming a field whose
identification is already committed to the repository, without also writing its curated row,
mechanically degrades FC-7 — a **measurement gap, not a model gap**. The rows below close it.

### D.1 The seven rows, exactly as they will be written

All seven go in **`CURATED_IDENTIFICATIONS` in `scripts/build_forecast_dof_ledger.py`** — the
D8 / D8-V instrument, the same committed, reviewed surface D50's and D52's rows live in.
**No `run_config`, no solve, no verdict edited by hand.** Six are new; the seventh
(`ccs_retrofit_capex_co2_scaling`) is **already committed by D50** and is listed for
completeness with what the Q42 flip did to it.

Every new row is keyed `(ISO, field)` — never `("*", field)` — so it is **rule 25
`[R-ISO-SCOPE]`-scoped by construction**: it cannot identify another ISO's value even if that
ISO later arms the same field. Every new row carries `requires: "iso-registry"`, so the
builder applies it **only** when the run's value byte-matches the live registered override; a
run carrying the field from anywhere else stays UNIDENTIFIED and the artifact records the
refusal.

| # | key | identification | source (what identifies the value) | evidence (committed) | rule-13: does it regenerate forward? | rule-21 DOF |
|---|---|---|---|---|---|---|
| 1 | `("NYISO", "nyiso_requirement_forecast_peak")` | `design-decision` | Prices the NYCA requirement on the **NYSRC ICAP-market forecast peak of the capability year** (IRM Study Appendices Table D.2 col. 1) instead of the model's own peak; a capability year outside the published table returns the model's peak **unchanged**, so the forward horizon keeps a forecast peak and never a held-last MW. A published market-design input, not a magnitude. | `_nyiso_config` `default_scenario_overrides` cite block; `FINDING-capx-d52-2026-09-04.md` §8(1); the digitized rows in `data/raw/demand-curve/nyiso/nyiso.csv`, reconciled to source by test | **Yes.** Each capability year's row is published before that year begins and is read in model year Y only (vintage-gated); the identical construction regenerates from the next Gold Book / IRM Study with no re-fit. | **Zero.** A selector, not a magnitude — the peak is read, never chosen. |
| 2 | `("NYISO", "nyiso_requirement_vintage_factors")` | `design-decision` | Prices the requirement **factor** at that capability year's **EC-adopted IRM × (1 − NYCA derate)** (Table D.2 cols. 2–3) instead of the single mixed vintage 1.244 × (1 − 0.1321); beyond the last published pair it **holds that pair's ratio**, 1.244 × 0.870 = 1.0823. In-table, the requirement IS Table D.2's published NYCA UCAP requirement to under 1 MW. | same cite block; `FINDING-capx-d52-2026-09-04.md` §8(1); LOYO 3/3 with an identical fleet, FC-3 byte-identical at the shipped default | **Yes**, identically vintage-gated; the hold-last limb is the documented behaviour beyond the table, not an extrapolated fit. | **Zero.** Every factor is a published adopted value. |
| 3 | `("MISO", "adequacy_accounting_ratio_dated_net")` | `design-decision` | Selects **D31's own arithmetic with the denominators net of the step-1b fossil-dates channel's accredited exits** — 0.854600 → **0.893436**, derived from three committed inputs and reconciled by test. The gate chooses *which consistent accounting* is used; it supplies no number. | `_miso_config` `default_scenario_overrides` cite block (owner ruling Q40); `FINDING-capx-d51-2026-09-04.md` §1.3 (construction) and §7 (the four limbs, incl. limb (c) failing by the letter and the owner's decision on the measured cause) | **Yes.** The ratio is recomputed by the same construction from whatever the dated channel holds in a forward year; it responds to a changed fleet by construction. | **Zero free parameters** (D51 §1.3). Note the token: `design-decision` is admissible here because the *gate* is boolean — the builder itself refuses to attach it to a numeric magnitude. |
| 4 | `("PJM", "pjm_accreditation_design_vintage")` | `design-decision` | Reads the accreditation design **of the delivery year being screened**: UCAP + the published **pre-CIFP FPR** before DY 2025/26, ELCC class + **post-CIFP FPR** from it. A published design vintage, applied by date. | `_pjm_config` `default_scenario_overrides` cite block (owner ruling Q44, in-session on the D57 A/B); `FINDING-capx-d48-*` / `DESIGN-capx-d54-pjm-clearing-half-2026-09-05.md`; `FINDING-capx-d57-2026-09-05.md` §8.1 | **Yes.** A forward delivery year takes the design in force for it; nothing is fitted to a residual. | **Zero.** Published design selection. |
| 5 | `("PJM", "pjm_demand_response_supply")` | `design-decision` | Counts the **published OFFERED DR UCAP as supply** with the peak un-netted, instead of netting DR off the peak — the accounting PJM's own auction uses. | same cite block; capx D48 | **Yes.** The offered DR UCAP is a published auction quantity available for any forward delivery year. | **Zero.** An accounting-side selection; no MW is invented. |
| 6 | `("PJM", "capacity_market_supply_clearing_by_iso")` | `design-decision` | Clears the fleet's **net-ACR sell-offer stack** (`offer = max(0, going-forward cost − E&AS margin) / accredited MW`, every other accredited MW a $0 price taker) against the **delivery year's published VRR curve**, so the screen's failing set IS the auction's uncleared set. Every operand is the screen's own. | `_pjm_config` cite block; `DESIGN-capx-d54-pjm-clearing-half-2026-09-05.md` §3.7 (DOF ledger: zero); `FINDING-capx-d57-2026-09-05.md` §8.1 | **Yes.** The VRR curve is published per delivery year; the offer stack is computed from the fleet's own costs. | **Zero** (design §3.7). Value is `{"PJM": True}` — a dict of booleans, **no numeric leaf**, so the builder's magnitude guard is satisfied. |
| 7 | `("*", "ccs_retrofit_capex_co2_scaling")` | `design-decision` | **ALREADY COMMITTED by D50** — the capture island sized to the host's captured CO2 against the ATB reference host, `captured_ref` = 0.90 × 6.3 × 0.057 = **0.32319 t/MWh**, every term an existing cited constant; CC_CHP hosts excluded on the electric-only ATB/NETL basis. | `ccs.py::ccs_retrofit_captured_ref_t_per_mwh`; `FINDING-capx-d49-2026-09-04.md` §1.4–§1.5; `PREDECL-capx-d50-2026-09-04.md` §1; `FINDING-capx-d50-2026-09-04.md` | Yes (D50). | **Zero** (D50 §1.2). |

**Row 7 needs no edit and gets none** — and D60-R2 states the consequence of its own flip
rather than letting it pass silently: Q42 made this field the **dataclass default**, and the
ledger enumerates **non-default** solve-affecting fields, so the field **no longer appears in
any post-flip bundle's ledger at all** and its curated row is now dormant. It is left in place
(a run that carries the field explicitly still matches `expected: True`), and this is exactly
the mechanism P20 pre-declared for GOLDEN-3: the flip adds **no eighth ledger entry**.

**What is NOT written, and why.** Six is the count of new rows, not seven, and the scope is
the seven fields Amendment 2 enumerated — **nothing else**. In particular the five OTHER
MISO registry overrides that read `unattested` today (`entry_vre_capacity_revenue`,
`entry_vre_zone_selection`, `miso_rps_compliance_regions`, `miso_clean_tier_rows`,
`retirement_sector_gate`) and CAISO's one (`negative_renewable_offers`) are **left
untouched**. They pre-date this batch, Q37's limb does not reach them, and this lane holds no
pre-declared identification for them. They are **routed**, not absorbed — and §D.3 states
plainly what that costs each key.

### D.2 The keys whose FC-7 the rows change — expected before → after, pre-declared

Measured from each bundle's committed `dof_ledger.json` where one exists, and from the ISO's
live `default_scenario_overrides` where the leg has not run yet. The **only** ledger entries
any t1f/t3 bundle carries are `forecast_xyear_warmstart` (already `design-decision`) plus that
ISO's registry overrides.

| bare key | ledger today (or as the leg will emit it) | FC-7 now | after the six rows | determination now → after |
|---|---|---|---|---|
| `nyiso-t1f` | 3 entries, **2 unattested** (both Q41 gates) | **CAVEAT** | 3/3 identified → **PASS** | **PROMOTE-WITH-CAVEATS → PROMOTE** |
| `miso-t1f` | 7 entries, **6 unattested** (the ratio + **five** pre-existing MISO overrides) | **CAVEAT** | ratio identified; **five still unattested** → **CAVEAT** | **HOLD → HOLD** (FC-7 stays a caveat) |
| `caiso-t1f` (leg 3) | will emit 2 entries, **1 unattested** (`negative_renewable_offers`, pre-existing) | CAVEAT (control reads CAVEAT) | **CAVEAT — unchanged; no row of the six touches CAISO** | **HOLD → HOLD** |
| `pjm-t1f` (leg 4) | will emit 4 entries, **3 unattested** (exactly D57's three gates) | would read **CAVEAT** | 4/4 identified → **PASS** | pre-declared **HOLD → HOLD** (P24 already pre-declared FC-7 **PASS**, which without these rows it could not have reached) |
| `neiso-t3` (leg 5) | will emit **7 entries, 0 unattested** (six NEISO ORDC/scarcity rows, all curated `published` by D8, plus warmstart) | **PASS** | **PASS — unchanged; no row of the six touches NEISO** | **HOLD → HOLD** |

Two of these are worth stating as blunt negatives rather than leaving to be inferred:

- **MISO's FC-7 does NOT clear.** The ratio row is written and MISO's ledger still reads
  CAVEAT, because five MISO overrides outside this batch remain unattested. Writing only the
  authorized row and reporting the caveat that survives is the honest outcome; widening the
  scope to make a row read PASS is the thing Q37's limb is narrow in order to prevent.
- **CAISO's and NEISO's FC-7 are untouched by this work entirely.** CAISO keeps its
  pre-existing caveat; NEISO already passes.

### D.3 FC-7 is the ONLY row that may move — and anything else is a STOP

A `CURATED_IDENTIFICATIONS` row is read by **one consumer**,
`build_forecast_dof_ledger._apply_curation`, and it can set only an entry's
`identification` / `status` / `source` / `evidence` / `provenance`. It **cannot** reach a
`ScenarioConfig` field, a cache key, a solve, a trajectory, an invariant or any other FC
category. So the re-scores of Amendment 2 step 3 are **artifact-only** in the strict sense:
same bundle, same bytes, same key, a re-run of `forecast_verdict.py --tier` over a ledger
whose *labels* changed.

**Therefore: FC-7 is the only row that may move.** If any other row moves — any FC-1
invariant, any FC-2 row, FC-3, FC-4, FC-5, FC-6, FC-8, or a determination changing for any
reason other than FC-7's own status — that is a **model effect the rows cannot own**, and it
is **STOP-and-route**: reported at full magnitude, escalated, **not registered**. It would
mean either the ledger builder or the scorer has a side effect neither is supposed to have,
and no attestation row may be allowed to carry that through to a board determination.

**And the two determinations this is expected to move, stated in advance so neither is a
surprise at reading time:** `nyiso-t1f` **PROMOTE-WITH-CAVEATS → PROMOTE** (the P10 STOP's
repair, and the whole reason Amendment 2 exists) and **nothing else**. `miso-t1f`,
`caiso-t1f`, `pjm-t1f` and `neiso-t3` are pre-declared to hold their determinations across
the re-score. A determination moving anywhere else is covered by §7 STOP 6.

### D.4 Order

Addendum D lands **now** (before leg 3). The **rows themselves** are written and the
**re-scores** run after the last leg registers, so that all five bundles are re-scored once,
at one sha, against one committed table — and so that no leg's FC-7 is read before its
identification row was pre-declared here. Every re-score happens **after that leg's final
rebase** (X-6b: no orphaned `scored_at_sha`).

---

## Addendum R3 (2026-09-06) — the D60-R3 relaunch: STATE AT START, before any solve, any row and any registration

D60-R2 (PR #4824) landed only its state-at-start commit and Addendum D, then went
silent; the owner ruled it dead at director r#42 amendment 2 and issued **D60-R3**,
re-emitted and dispatched at r#43 with the D65/D71 HEAD-drift instrument folded in.
This addendum is the relaunch's first commit and it carries **zero solve**.

### R3.1 The twin check — CLEAR

Executed at session start with `git fetch origin --prune`, at base `fca3b656`:

- **No `claude/capx-d60r*` branch exists on origin.** `git ls-remote --heads origin`
  returns exactly two refs — `main` and `claude/scn-ws4c-load-hi-probes-o85iyi` (the
  SCN-WS4c lane, disjoint). The fetch pruned a stale remote-tracking ref for this
  session's own branch name; origin has never held it.
- **The only commits mentioning "D60-R2" / "D60-R3" newer than `342c7593` are the
  director's own** (`8cdc5d7f` r#43, `eca6c798` r#42 am.2) — docs only
  (`capx-director-handoff` / `-ledger` / `-prompt-pack`), the issuance of this session,
  not a twin's output.
- **`frontend/data/forecast/ff-verdicts.json` has NOT been touched since `342c7593`**
  (`git log 342c7593..origin/main -- …/ff-verdicts.json` → empty). `program-status.json`
  carries only the three backcast gate-(a) re-keys the charter named (`32f8de52` NYISO,
  `4d1ed3ad` MISO, `e2412b82` CAISO) — **no forecast verdict moved**.

No twin is mid-flight. D60-R3 proceeds.

### R3.2 Every bare forecast key re-resolved through the harness path — **ZERO DRIFT, 17/17**

Resolved exactly as Addendum A §A.2 and R2.2 resolved them
(`run_full_horizon.reference_config(iso, 2026, 2030|2050, False, golden_posture=True)`
→ `apply_iso_scenario_defaults` → `cache_key()` for t1f/t3;
`run_capacity_hindcast.build_config(iso, 2021, 2025, "realized", vintage=2020,
entry_screen_diagnostics=True)` → same → `cache_key()` for t1h). Config construction
only; no fleet build, no solve.

| bare key | pin (source) | resolved at HEAD | verdict |
|---|---|---|---|
| `ercot-t1f` | `0c3e9cd5b5993bdf` (§A.2) | `0c3e9cd5b5993bdf` | **HIT** |
| `caiso-t1f` | `29f8eb372810195f` (§A.2) | `29f8eb372810195f` | **HIT** — leg 3 runs on it |
| `pjm-t1f` | `09996eca71ee80fd` (§C.1) | `09996eca71ee80fd` | **HIT** — leg 4 runs on it |
| `miso-t1f` | `b1a73a087064ffd8` (§A.1) | `b1a73a087064ffd8` | **HIT** — registered |
| `nyiso-t1f` | `19a9690bb12c8459` (§A.2) | `19a9690bb12c8459` | **HIT** — registered |
| `neiso-t1f` | `18515067bf4d2fbe` (§A.2) | `18515067bf4d2fbe` | **HIT** |
| `neiso-t3` | `f04fd06348e1623d` (§A.2) | `f04fd06348e1623d` | **HIT** — leg 5 runs on it |
| `ercot-t1h` | `82b27751be747552` (§A.2) | `82b27751be747552` | **HIT** |
| `caiso-t1h` | `7da58199acd362ee` (§A.2) | `7da58199acd362ee` | **HIT** |
| `pjm-t1h` | `aef81c84c4609c76` (finding §3) | `aef81c84c4609c76` | **HIT** |
| `miso-t1h` | `687bd75f2828bea1` (§A.2) | `687bd75f2828bea1` | **HIT** |
| `nyiso-t1h` | `6e70a637b3465542` (§A.2) | `6e70a637b3465542` | **HIT** |
| `neiso-t1h` | `f3988df3068020d1` (§A.2) | `f3988df3068020d1` | **HIT** |

And the four pinned defaults, against finding §6:

| config | finding §6 "after" | resolved at HEAD | verdict |
|---|---|---|---|
| `ScenarioConfig()` | `e5ecd4105ada3e58` | `e5ecd4105ada3e58` | **HIT** |
| `ScenarioConfig(mode="backcast")` | `6a2845e50951394e` | `6a2845e50951394e` | **HIT** |
| `ScenarioConfig(ccs_retrofit_capex_co2_scaling=False)` | `4c6b03ae098b6e3e` | `4c6b03ae098b6e3e` | **HIT** |
| same, backcast | `8211c72bb1960adc` | `8211c72bb1960adc` | **HIT** |

**Seventeen of seventeen.** STOP 1 stands unchanged for all three remaining legs.

### R3.3 The three STATE-AT-START assertions the charter demanded, each MEASURED

**(a) D65 Act A is key-neutral.** `ccs_retrofit_fixed_cost_co2_scaling` is registered in
`_CACHE_KEY_OPTIONAL_FIELDS` at its shipping `False` (`scenarios.py:1941`), so it drops
from the hash at its default. Measured, not asserted:

| config | key |
|---|---|
| `ScenarioConfig()` | `e5ecd4105ada3e58` |
| `ScenarioConfig(ccs_retrofit_fixed_cost_co2_scaling=False)` | `e5ecd4105ada3e58` — **identical** |
| `ScenarioConfig(ccs_retrofit_fixed_cost_co2_scaling=True)` | `2186aa915ad19c59` — **distinct** |

The default and the explicit `False` collide exactly; an armed run keys distinctly. Every
one of the seventeen keys above therefore carries D65 Act A's landing without moving.

**(b) The R-AZ registration gate does NOT touch this lane's registration path.** R-AZ
(`ee0c1676`) changed six files: `CLAUDE.md`, `docs/governance/rule-history.md`, its own
FINDING, **`scripts/dashboard_add_run.py`**, **`scripts/lib/holdout_policy.py`** and
`tests/scoring/test_registration_marker_gate.py`. This lane registers through
`scripts/register_forecast_run.py`, which imports **neither** `holdout_policy` nor
`dashboard_add_run` (grep for `holdout_policy|dashboard_add_run|registration_refusals|
enforce_registration_marker_gate` over that file: **zero hits**). The gate is a BACKCAST
registration gate on the backcast registry; the forecast namespace is disjoint by
construction (plan §7.5). **Not touched — no STOP.**

**(c) The SCN sidecars are not the board.** The three SCN hindcast sidecars named in the
charter — and the three more that landed under this session (`fbef3a91`, SCN-WS2b's NEISO
ladder) — are `frontend/data/hindcast/neiso-2026-2030-scn-ws2-ladder-{bau,ces-20,ces-40}.json`
and their siblings, registered under their own campaign keys. **No file under
`frontend/data/forecast/` is touched by any of them.**

### R3.4 main moved twice under this session — both times DISJOINT, both kept verbatim

The charter's base pin was `04e6906d`; this session opened at `fca3b656` and, during the
history deepen described in §R3.5, `origin/main` advanced again to **`fbef3a91`** (PRs
#4932–#4936: SCN-WS2b, SCN-WS4c, miso-222, Y-18 FR-22 parity). Measured as a structural
diff rather than asserted:

- `git diff --stat fca3b656..fbef3a91 -- frontend/data/forecast/` → **empty**.
- `git diff --stat fca3b656..fbef3a91 -- src/market_sim/` → **empty**.

So the seventeen keys of §R3.2, resolved at `fca3b656`, hold verbatim at `fbef3a91`; this
lane's base is `fbef3a91` and every one of those lanes' edits survives untouched. The one
new file worth naming because it sits near this lane's surface is
`scripts/lib/forecast_parity_registry.py` (Y-18): a **parity registry read by
`tests/scoring/test_forecast_parity.py`**, not by the solve path and not by
`register_forecast_run.py`.

### R3.5 Two environment facts that would have corrupted every number in this finding

Both are recorded because they were found and repaired **before the first solve**, and
because neither is visible in a bundle after the fact.

1. **The container's stack did not match the committed record.** `pip install -r
   requirements.txt` failed on a Debian-owned PyYAML (`Cannot uninstall PyYAML 6.0.1,
   RECORD file not found`), and the packages it did not overwrite left the environment at
   **highspy 1.15.1 / pandas 3.0.5 / pydantic 2.13.5** — against `requirements.txt`'s
   pins of **1.14.0 / 3.0.3 / 2.13.4**. A different HiGHS build is a different LP solver,
   and D65 §3b's whole drift argument rests on the stack being identical to the committed
   control's. Repaired with `pip install --force-reinstall --no-deps highspy==1.14.0
   pandas==3.0.3 pydantic==2.13.4 pydantic-core==2.46.4`. The stack this lane solves on is
   now **python 3.11.15, highspy 1.14.0, numpy 2.4.6, scipy 1.17.1, pandas 3.0.3, pyarrow
   24.0.0, pydantic 2.13.4** — D65 §3b's recorded control stack, to the digit.
2. **The clone is SHALLOW** (`.git/shallow` present; 183 first-parent commits, floor
   2026-09-04 19:07), so `9e48ff6` — the `git.sha` of the committed `neiso-t1f` bundle and
   the charter's bisect endpoint — was **not a resolvable revision**. Deepened with
   `git fetch --deepen=400 origin main` (183 → 1,049 first-parent commits, floor
   2026-08-11), which brings every committed bundle's `basis_sha` into range. As with
   §R2.4, `data/clean` was absent and was regenerated **once**, before the first leg; the
   per-leg wall-clock figures in the finding exclude it.

### R3.6 The blast-radius boundary, pinned at ZERO LP cost — and why no bisect was spent

The charter folds in D65 §3b/§3c and asks for a `git bisect` over `9e48ff6..HEAD`
(≤ 8 probes × ~5 min) to name the drift hunk. **That bisect's object was already
achieved, by a stronger instrument, before this lane opened.** D65 §3d pins the hunk by a
**one-hunk revert** — a copy of the exact HEAD tree with only that hunk reverted, verified
by `diff -r` to differ in exactly one file and one hunk, reproducing the pre-drift 2027
ledger exactly (33 rows / 2,369.81 MW / `reserve_margin` 0.045867 / gas_cc 10,713.803). A
bisect names a *commit*; §3d names the *lines* and proves them causal. Re-running the
bisect to re-derive a weaker fact would spend ~40 LP-minutes for nothing.

What the bisect *would* still have supplied, and what §3d does not, is the **commit
boundary** — needed to classify committed bundles pre/post. That is a **content**
question, not a solve question, and it is answered by a binary search over `main`'s
first-parent chain for the hunk's own docstring marker (`git show <sha>:…retirements.py |
grep`), ten probes, seconds, zero LP:

- **`da007e0f6f73f64a248ed92b4f922f0a06a52c6e`** — PR #4747,
  `claude/capx-d55-retention-key-fix-xqrcfv`, **2026-09-04 19:06:53 −0700** — the FIRST
  commit on `main` carrying the hunk. The hunk itself is commit **`32f9628c`** ("capx D55:
  floor-retention key 1 as the class constant (D32 §3.2 / R2) …").
- Its first-parent predecessor **`3e9f191a`** (PR #4746, capx D54) is the last pre-hunk
  commit on `main`.

**The hunk, named as the charter asks (commit, file, function, lines, and what it does in
words).** `src/market_sim/model/capacity_evolution/retirements.py::_floor_retention_merit`,
key 1 of the reliability-floor retention sort. D55 replaced the per-unit quotient
`(FOM × multiplier × pmax × 1000) / (pmax × accreditation_fraction)` with the
class-constant `(FOM × multiplier × 1000) / accreditation_fraction`. The two are equal in
exact arithmetic and **not** in IEEE-754: the quotient form put same-fuel units on 4–5
distinct floats at the 1e-11 level, so the tuple sort consulted the CO2 and heat-rate keys
only *inside a rounding bucket*, and the designed three-key ordering was reproduced only
piecewise. **This is an intentional repair** — of the defect recorded as D32 §3.2 — and
what it also does, necessarily, is change the retention **sort order**. Under the
charter's clause (c) that reading is explicit: *"if it is an intentional repair (D55's is),
the committed bundles are stale and the re-solves you run ARE the remedy."* This lane
therefore names it and **does not touch it**.

**Why it is silent** (D65 §3d, restated because it is what makes the staleness invisible):
`_apply_reliability_floor` has three call sites and only two are logged
(`retirements.py:2565`, `:3486`); the call at `:2517` — the pipeline **admission-cap**
screen, invoked for its in-place mutation of the `scheduled` set — discards its return, so
`floor_retained` is `[]` on both sides of the hunk and the diagnostic that exists to make
floor behaviour visible is blind to it. That is D65's second routed item, not this lane's.

### R3.7 Every committed forecast bundle classified — 28 PRE-hunk, 5 POST-hunk

Classified by ancestry of each bundle's own `git.basis_sha` against `da007e0f`
(`git merge-base --is-ancestor`). "PRE-hunk" means **solved on the other side of the D55
ordering change, so its reproduction at HEAD is not established** — it does not by itself
mean the bundle's numbers move (see the two measured counter-examples below).

| bundle (`results/ff-*/…/run_config.json`) | ISO | cache key | basis | date | side |
|---|---|---|---|---|---|
| `ff-t1f-d45r/miso` | MISO | `8d8bc63a0d4378a9` | `334be8c2a322` | 2026-09-04 | PRE |
| `ff-t1f-d45r/nyiso` | NYISO | `cc7d1050a8090c76` | `334be8c2a322` | 2026-09-04 | PRE |
| `ff-t1f-d45r/pjm` | PJM | `321f04e9060787f0` | `334be8c2a322` | 2026-09-04 | PRE |
| `ff-t1f-d46/caiso` | CAISO | `772b1e5abc7fc80c` | `d375bde39a32` | 2026-09-03 | PRE |
| `ff-t1f-d46/ercot` | ERCOT | `873d8c0e6cab52ae` | `d375bde39a32` | 2026-09-03 | PRE |
| `ff-t1f-d46/neiso` | NEISO | `6690e4d6d66bc819` | `d375bde39a32` | 2026-09-03 | PRE |
| `ff-t1f-d50/ercot` | ERCOT | `0c3e9cd5b5993bdf` | `a35c9f9bc0d1` | 2026-09-04 | **PRE** |
| `ff-t1f-d50/neiso` | NEISO | `18515067bf4d2fbe` | `a35c9f9bc0d1` | 2026-09-04 | **PRE** |
| `ff-t1f-d50/pjm` | PJM | `167e65187f32056b` | `c9f1d26e3463` | 2026-09-04 | POST |
| `ff-t1f-d60/miso` | MISO | `b1a73a087064ffd8` | `b87c057ae4bb` | 2026-09-05 | POST |
| `ff-t1f-d60/nyiso` | NYISO | `19a9690bb12c8459` | `b87c057ae4bb` | 2026-09-05 | POST |
| `ff-t1f-d65-a1/neiso` | NEISO | `8ebed20ae90ec0e7` | `e5ac39f1b2a6` | 2026-09-05 | POST |
| `ff-t1f-d65-ctl/neiso` | NEISO | `18515067bf4d2fbe` | `e5ac39f1b2a6` | 2026-09-05 | POST |
| `ff-t1f-s123/verify` | MISO | `587dc5b32ba71ceb` | `54ca19ae0782` | 2026-08-30 | PRE |
| `ff-t1f-s4hydro/neiso-control` | NEISO | `9a7f68fc7dcac931` | `6136a2964264` | 2026-08-30 | PRE |
| `ff-t1f-s4hydro/neiso` | NEISO | `9a7f68fc7dcac931` | `6136a2964264` | 2026-08-30 | PRE |
| `ff-t1f-s6-pjm/ledger` | PJM | `31a19d815fa319a7` | `54ca19ae0782` | 2026-08-30 | PRE |
| `ff-t3-neiso-golden/bau-d46` + its 4 FC-6 arms | NEISO | `67678e58b2d0526c` (+4) | `d375bde39a32` | 2026-09-03 | PRE (×5) |
| `ff-t3-neiso-golden/bau-prera-2026-08-31` + its 5 FC-6 arms | NEISO | `a4b11ef4aaa1be35` (+5) | `9e56f0fecd86` | 2026-08-30 | PRE (×6) |
| `ff-t3-neiso-golden/bau` + its 4 FC-6 arms | NEISO | `706e7ba8e6582d42` (+4) | `a5523fac1b18` / `5083e29e2562` | 2026-09-01 | PRE (×5) |

**28 PRE-hunk, 5 POST-hunk, 33 total.** Two measured counter-examples keep "PRE" from
being read as "wrong": D55's own A/B measured `miso-t1h` **byte-identical** across the
hunk (retirements and `pipeline_events` every year, 21/21 FC-3 rows — commit `8181bc64`),
while D65 measured `neiso-t1f` **materially changed** (7 rows, −124.92 MW of gas_cc in
2027). The hunk is a *tie-break ordering* change: it bites only where the reliability
floor has ties to break and headroom to spend. Everything not on one of those two lists is
**unmeasured**, and this lane says so rather than guessing.

### R3.8 The bare keys, by side — and the residue D60-R3 will leave

| bare key | registered run | side today | after this lane lands |
|---|---|---|---|
| `caiso-t1f` | `caiso-2026-2030-d46-remeasure` | PRE | **POST** (leg 3) |
| `pjm-t1f` | `pjm-2026-2030-d45r-remeasure` | PRE | **POST** (leg 4) |
| `neiso-t3` | `neiso-2026-2050-t3-golden3-bau` | PRE | **POST** (leg 5) |
| `miso-t1f` | `miso-2026-2030-d60-arm` | POST | POST |
| `nyiso-t1f` | `nyiso-2026-2030-d60-arm` | POST | POST |
| `pjm-t1h` | `pjm-2021-2025-realized-t1h-d57-clearing` | POST | POST |
| `ercot-t1f` | `ercot-2026-2030-d50-ccscapex` | PRE | **PRE — residue** |
| `neiso-t1f` | `neiso-2026-2030-d50-ccscapex` | PRE | **PRE — residue** (the D65 case) |
| `ercot-t1h` | `ercot-2021-2025-realized-t1h-d46` | PRE | **PRE — residue** |
| `caiso-t1h` | `caiso-2021-2025-realized-t1h-d46` | PRE | **PRE — residue** |
| `miso-t1h` | `miso-…-t1h-d53-sectorgate-d51ratio` | PRE | **PRE — residue** (measured INERT by D55) |
| `nyiso-t1h` | `nyiso-…-t1h-d52-devintage` | PRE | **PRE — residue** |
| `neiso-t1h` | `neiso-2021-2025-realized-t1h-d45r` | PRE | **PRE — residue** |

**Seven bare keys remain PRE-hunk after this lane lands.** They are D60-R3's *routed
residue*, not its scope: the charter's owed list is three legs, and re-solving seven more
keys is a separate campaign for the director to charter. `neiso-t1f` is the one with a
measured magnitude already attached (D65 §3c) and is the obvious first rung.

### R3.9 What is OWED, unchanged from §R2.3

Three re-solves — `caiso-t1f` (prior `caiso-2026-2030-d46-remeasure`, `772b1e5abc7fc80c`,
HOLD → `caiso-t1f-pre-d60`), `pjm-t1f` (prior `pjm-2026-2030-d45r-remeasure`,
`321f04e9060787f0`, HOLD → `pjm-t1f-pre-d60`), `neiso-t3` GOLDEN-3 (prior
`neiso-2026-2050-t3-golden3-bau`, `67678e58b2d0526c`, HOLD → `neiso-t3-pre-d60`); the
seven Q37 attestation rows and the artifact-only re-scores (Addendum D); the finding's §5,
§8 and its §8-blast-radius. Verified at HEAD: none of the three `-pre-d60` priors exists
yet, and the six that D60 wrote are untouched.
