# FINDING — nyiso-105: the ST_GAS p25 lever is INERT, the export-sink seam is LIVE, and "zero delta" was half true

**Session:** nyiso-105. **Keeper under test:** `2026-07-30-nyiso-100-silretire`
(CALIBRATED-WITH-CAVEATS, 0 FAILs, 1 ledgered caveat C3c).
**Frozen HEAD:** `0852d5b`. **Pre-registration:**
`results/calibration/PREREG-nyiso105-chp-heat-rates-2026-07-31.md`.
**Probe (no LP):** `scripts/probes/_nyiso105_seam_recipe_stgas.py`.

Three of the session's four scoped items closed **on measurement alone, with no
LP solved** — the nyiso-93/94/95/97/99/101 pattern. A kill-before-solve is a full
result. §5.5 queue items **6** and **10** are struck by this session.

---

## §A — Lever 1 `st_gas_mustrun_p25_level`: INERT as shipped, and the queue's premise was wrong

The scope asked the session to "decide and pre-register whether NYISO's arm is
one flag or the pair, and justify from NYISO's own D-2 attribution." The answer
is **the pair — and the pair still cannot fire.** Four independent blockers, each
measured, any one of which is decisive.

### A.1 The single flag is a no-op by construction

`src/market_sim/data/fleet/arrays.py:1750-1753` gates the p25 block on **both**
flags:

```python
st_gas_p25_level_on = (
    config is not None
    and getattr(config, "st_gas_mustrun_p25_level", False)
    and getattr(config, "st_gas_mustrun_per_plant", False)
)
```

The nyiso-100 keeper carries `st_gas_mustrun_per_plant=False`. The scope's
suggested arm — `--set st_gas_mustrun_p25_level=true` — would therefore have
solved a **bit-identical control**, burning two multi-hour NYISO solves to
discover a flag ordering. This is exactly what the no-solve-first sequencing is
for.

### A.2 The pair is a no-op on today's artifact — 0 of 11 plants are armable

The runtime needs, per plant, `p25_level > 0` **and** `online_frac > 0`.
`thermal_tranche_online_frac("NYISO")` returns **0 rows**, because
`data/raw/_processed-legacy/thermal_tranches_NYISO.csv` **has no `online_frac`
column at all**:

```
plant_code, plant_group, name, status, nameplate_mw, online_hours,
committed_pct, mustrun_pct, p25_cf, median_cf, chp_pmin_cf, chp_sector, peaking_pct
```

`thermal_tranche_p25_level("NYISO")` does return 63 rows (11 ST_GAS), so the
*level* is present — the *window* is not. Cross-ISO census (rule 25: a
measurement of artifact state, never a verdict in another lane):

| ISO | `online_frac` column | ST_GAS rows | with `online_frac` |
|---|---|---|---|
| CAISO | yes | 3 | 0 |
| PJM | yes | 10 | 0 |
| **MISO** | yes | 16 | **16** |
| **NYISO** | **no** | 11 | **0** |
| NEISO | no | 1 | 0 |

MISO is the only ISO whose artifact can drive this mechanism. NYISO's cannot.

### A.3 Making it fire is a fleet-wide re-basing, not a mechanism arm

`_ONLINE_FRAC_GROUPS` gained `ST_GAS` on 2026-07-12 for the MISO lane, so the
current deriver *would* emit the column. Re-deriving to a scratch path at HEAD
(`derive_thermal_tranches.py --iso NYISO --years 2023 2024 2025`,
`--chp-floors-from` the committed artifact) shows the refresh is **not** a
schema-only catch-up. Diffed against the committed file on the 78 shared rows:

| column | identical | max abs Δ |
|---|---|---|
| `online_hours` | 32/78 | 26,271 |
| `median_cf` | 41/78 | 72.1 |
| `committed_pct` | 42/78 | 27.2 |
| **`p25_cf`** | **46/78** | **83.6** |
| `peaking_pct` | 70/78 | 9.3 |
| `nameplate_mw` | 75/78 | 102 |
| `chp_pmin_cf`, `chp_sector`, `mustrun_pct`, `name` | 78/78 | 0 |

plus 3 new columns (`online_frac`, `mustrun_online_pct`, `steam_level_cf`) and
1 new row. `committed_pct` / `p25_cf` / `peaking_pct` are the tranche shares the
**entire NYISO thermal offer curve** is built from, so refreshing the artifact
re-bases every gas plant's offer, not just the ST_GAS floor level. That is a
rule-23 `[R-FROZEN-DERIVE]` re-derivation needing its own charter and its own
control arm — it is categorically not the single-delta lever the queue described.

**Deriver defect found in passing (reported, not fixed — out of scope and inert
for NYISO today).** The refreshed artifact emits **`p25_cf > 100 %`** on two
ST_GAS plants — S A Carlson **142.2**, Astoria **101.7** — against
`campd_bins.thermal_tranche_p25_level`, which applies **no upper clamp**:

```python
level = max(0.0, p25 / 100.0) * max(0.0, nameplate)
```

`committed_pct` and `mustrun_pct` are capped (`_COMMITTED_CAP` 0.70,
`_MUSTRUN_CAP` 0.60); `p25_cf` is not. A p25 swap on such a row asks for a floor
**above nameplate**; the per-hour `min(target, pmax × availability)` clip stops it
crashing but pins the plant flat at full available capacity across its whole
window. Any future session that refreshes this artifact must clamp first.

### A.4 The premise is false for NYISO, and rule 19 forbids the stack

The queue entry reads "re-ground the in-city ST_GAS persistent bases on measured
levels **instead of fitted fractions**". That describes **MISO's** incumbent —
`committed_pct`, the P5-of-online LSL. It does **not** describe NYISO's. The two
ST_GAS limbs that survive the keeper's `reliability_floor_overrides` are already
measured p25:

| limb | floor_pct | `threshold_basis` |
|---|---|---|
| `NYC:ST_GAS:tmax:_none` | 0.1750 | *persistent 24h base: base_24h (**when-available cool-day CF p25**), re-derived 2026-07-26 on the guard-corrected outage extract* |
| `Long_Island:ST_GAS:tmax:_none` | 0.2620 | *persistent 24h base: base_24h (**when-available cool-day CF p25**), same re-derivation* |
| `Capital_Hudson:ST_GAS:tmax:_none` | 0.0973 | hot: zone p95 tmax (design cooling day) |

So NYISO's in-city ST_GAS bases are **already** the measured 25th percentile. The
only real difference the mechanism would buy is *per-plant* rather than
*zone-pooled* p25, with a top-`online_frac` load window replacing a 24 h base —
a genuine but much smaller rule-14 refinement than the queue implied, and one
that A.2/A.3 block anyway.

And **rule 19 `[R-ONE-MECH]`** independently forbids adding it as a third
mechanism. From the keeper's own D-2:

| year | mechanism | forced TWh | share of ST_GAS |
|---|---|---|---|
| 2023 | `reliability_floor` | 2.9143 | 24.23 % |
| 2023 | `nyiso_gas_commitment_bridge` | 0.2212 | 1.84 % |
| 2024 | `reliability_floor` | 3.0739 | 27.78 % |
| 2024 | `nyiso_gas_commitment_bridge` | 0.3079 | 2.78 % |
| 2025 | `reliability_floor` | 2.6791 | 19.43 % |
| 2025 | `nyiso_gas_commitment_bridge` | 0.3387 | 2.46 % |

with D-2 already recording **`2024 ST_GAS: forced share 30.6 % > 30 %`**. A
rule-19-compliant arm would have to *replace* the NYC/LI limbs, which is the
`nyiso_incity_commitment_obligation` substitution path
(`iso_configs._INCITY_OBLIGATION_OWNED_LIMBS`) — a different mechanism under a
different charter, not this flag pair.

**Verdict: matrix cell `st_gas_mustrun_p25` NYISO `U → I`.** Inert as shipped.
§5.5 item 6 is struck. The deriver refresh is named as a separate charter with a
clamp prerequisite; it is not a lever-queue entry.

---

## §B — Item A: the caiso-142 export-sink seam is CONFIRMED on NYISO's own keeper, and it is LIVE

caiso-142 §F measured NYISO as exposed from the **then**-keeper
`nyiso99_demandfix`. This re-measures on the **current** keeper fleet — nyiso-100,
which retired the `NYISO_simultaneous_import` scalar and so builds a different
interchange row set — using the real runtime functions, no LP.

### B.1 The seam, reproduced

NYISO 2025 keeper fleet: **705 rows, exactly 1 absorption row**.

```
absorption row: NYISO_external_export_surplus   pmin = -600.0   pmax = 0.0
```

Composing a bridge floor of the shape `nyiso_gas_commitment_bridge` produces
(zeros everywhere but the bridged thermal rows) through
`pipeline/commitment.py::_bridge_floored_fleet`:

| composition | sink `min_gen` | verdict |
|---|---|---|
| `preserve_absorption=False` (**the keeper today**) | 0.0 | **range DELETED — pinned off** |
| `preserve_absorption=True` (the caiso-142 fix) | −600.0 | range PRESERVED |

**Exactly 1 row differs** between the two compositions, 0 other rows, and
`availability` is byte-identical — the same surgical signature caiso-142 measured
in CAISO. **600 MW of export absorption is absent from every scored P1 solve**
since `nyiso_gas_commitment_bridge` was armed.

### B.2 It is LIVE, not latent — and that is new

Exposure alone does not say the outlet was ever *wanted*. An absorption row with
`pmin < 0` and marginal cost `c` is a demand the LP is paid `c` to serve, so it
clears exactly when its zonal price sits **below** `c`. Scored against the
keeper's own committed P1 dual on the `NYISO_external` node:

| year | sink price p50 | node λ p50 | in-the-money hours | max gap | foregone export bound |
|---|---|---|---|---|---|
| 2023 | 24.10 | 30.93 | **921** (10.51 %) | $164.80 | ≤ 0.553 TWh |
| 2024 | 23.95 | 31.61 | **1,078** (12.31 %) | $148.20 | ≤ 0.647 TWh |
| 2025 | 33.58 | 50.75 | **679** (7.75 %) | $321.27 | ≤ 0.407 TWh |

**Stated limitation:** the dual used is the keeper's *solved* λ, produced with
the sink already pinned off, so these are a first-order screen and an upper
bound, not the counterfactual. They are enough to establish the defect is not
academic in NYISO the way caiso-142 found the CAISO legs out of the money.

### B.3 Reported, NOT armed — and the direction argues against arming it here

Per scope, this is an infrastructure-defect audit. Three reasons nothing is armed:

1. The fix is **CAISO-flag-gated** (`caiso_p1_export_sink_seam` threads
   `preserve_absorption` from the CAISO RA path only), so no NYISO keeper recipe
   moves today and no NYISO bundle is affected. The field is absent from the
   nyiso-100 `run_config` entirely.
2. Arming it for NYISO would need its **own** NYISO flag and its own charter —
   the CAISO mechanism was rejected there on a sign argument (rule 25: that
   verdict transfers nothing, but neither does its machinery).
3. **The direction does not serve any open NYISO gate.** Restoring an absorption
   row can only *add* demand, so it can only weakly *raise* λ — and the hours it
   clears are the ones where λ is *below* the seam price, i.e. off-peak. Raising
   off-peak λ **compresses** the diurnal spread (C3b's direction of concern) and
   does nothing for C3c, whose miss nyiso-92 dated as a **summer peak** tail.

**Matrix cell `caiso_p1_export_sink_seam` NYISO `U → O`** — measured, confirmed,
live, charter-pending; not `R` (nothing was tested and rejected in NYISO) and not
`I` (it is demonstrably not inert here).

---

## §C — Item B: "zero dispatch delta" is TRUE; "zero delta" is FALSE

§5.5 item 10 proposes dropping `dual_fuel_oil_reattribution` from the NYISO
recipe metas on the grounds that "the CLI already pins it NEISO-only, so the
dispatch delta is zero". The scope said verify, not assert. Both halves were
measured, and they disagree.

### C.1 The flag really is on, through the overrides channel, not the CLI

| channel | value |
|---|---|
| `calibration_flags.dual_fuel_oil_reattribution` (CLI) | `None` — the CLI pin holds |
| `meta.coal_prb_sigmoid_overrides.dual_fuel_oil_reattribution` | **`true`** |
| solved `scenario_config.dual_fuel_oil_reattribution` | **`true`** |

The CLI pins it NEISO-only (`run_calibration_full.py:10704`), but the keeper
lineage carries it through the generic overrides dict, so the solved config had
it **on**. The queue item's framing — that the CLI pin makes it inert — is not
what happened.

### C.2 The dispatch delta IS zero, and here is the proof rather than the claim

Two independent lines.

**Structural.** `dual_fuel_oil_mask` has exactly two consumers:
`build_winter_fuel_budget` (gated on `neiso_winter_fuel_inventory`, which the
NYISO keeper carries as **`False`**), and `_dispatch_frame(oil_switch_mask=…)`,
which does only `klass_col[flat] = "oil"; fuel_col[flat] = "oil"` — a **reporting
relabel** applied after the solve. The mask never reaches the LP.

**Empirical byte-identity.** Rebuilding the keeper's LP inputs with the flag
flipped and hashing them:

| year | `mc_base` | `fuel_prices` | `pmax` | `pmin` | `heat_rate` | `availability` | `min_gen` | `demand` |
|---|---|---|---|---|---|---|---|---|
| 2023 | == | == | == | == | == | == | == | == |
| 2024 | == | == | == | == | == | == | == | == |
| 2025 | == | == | == | == | == | == | == | == |

**Every LP input is byte-identical in all three years.** The dispatch cannot move.

### C.3 The RECORDING-BASIS delta is not zero — and it is material

The relabel rewrites the **class** of dispatched MWh in the sidecars C1 and C7 are
scored from. In the keeper's own committed `class_hourly`:

| year | re-attributed to `oil` | of served | hours affected |
|---|---|---|---|
| 2023 | 0.1119 TWh | 0.076 % of 147.14 TWh | 53 |
| 2024 | 0.3511 TWh | 0.233 % of 150.61 TWh | 155 |
| 2025 | **1.1508 TWh** | **0.757 %** of 151.96 TWh | **715** |

**1.6139 TWh over three years.** For scale, the keeper's whole `CT_PEAKER` class
is 0.341 / 0.257 / 1.067 TWh — so the relabelled volume is of the same order as
an entire scored class, and nyiso-99 already established the basis is wrong for
NYISO (Jan-2025 parity switching relabels 0.80 TWh against a measured `NYIS`
`NG: OIL` of 0.031 TWh).

**Consequence for the queue item.** Dropping the flag is still right — it removes
a known-wrong recording basis (rule 14 `[R-ACCURATE]`) — but it is **not** the
free no-op cleanup the queue describes. It is dispatch-neutral and
**scoring-basis-changing**, so it must ride a re-solve with its own control and
be scored, not silently edited into the metas. §5.5 item 10 is **struck and
re-opened as a scored cleanup**, not as "verified zero".

---

## §D — What this session changes on the record

* **§5.5 item 6** (`st_gas_mustrun_p25_level`) — **STRUCK**, cell `U → I`.
  Successor is a chartered artifact refresh with a `p25_cf` clamp prerequisite,
  not a lever.
* **§5.5 item 10** (`dual_fuel_oil_reattribution`) — **STRUCK as written**;
  re-opened as a *scored* cleanup with a control arm, on the measured 1.61 TWh
  recording-basis delta.
* **`caiso_p1_export_sink_seam` NYISO `U → O`** — exposure confirmed on the
  current keeper and measured live; charter-pending, nothing armed, direction
  noted as adverse to C3b and irrelevant to C3c.
* **C3c is untouched.** No item in this session targeted it, and the closed queue
  stays closed.
* **Zero fitted parameters introduced. No keeper changed by this finding.**

Evidence: `scripts/probes/_nyiso105_seam_recipe_stgas.py`;
`results/calibration/_nyiso105_noLP_measurements.json`;
`results/calibration/_nyiso105_a2.json`;
`results/calibration/_nyiso105_b2_byteident.json`.
