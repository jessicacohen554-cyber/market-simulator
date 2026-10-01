# FINDING — lane NWPP-34 (the seam derive: served interchange, BPAT adjudication, R-a magnitude)

Lane **NWPP-34** · 2026-09-14 · branch `claude/nwpp-34-seam-a7f3` · base sha **`d54cd9c5`**
· MODEL Opus `claude-opus-5` · DATA PROFILE `nwpp`.

Charter: `docs/multi-iso/nwpp-addition-plan-2026-09.md` §5 row NWPP-34 / §8 prompt pack; card **N4
RULED** (desk sitting #4, 2026-09-14: *"SERVED MEASURED INTERCHANGE, PRICED LINKS DEFAULT-OFF"*);
ledger routed item **R-a**. **Zero solves. Nothing armed. No `ScenarioConfig` field, no
`enabled`/default flipped, no matrix cell moved, no CAISO artifact touched.**

---

## 0. THE TWO NUMBERS THE CHARTER ASKED FOR FIRST

### 0.1 The BPAT residual — the trap is real, and it is worse than the charter states

Residual `r = NG_adj − D_adj − TI_adj` (MW; the identity the naive derive assumes is `r ≡ 0`),
measured over 2023-2025 on the committed per-BA extracts:

| | pooled 2023-2025 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|
| **BPAT** energy | **−84.284 TWh** | −35.319 | −36.045 | −12.920 |
| **BPAT** mean | **−3,205.7 MW** | −4,036.5 | −4,103.9 | −1,475.1 |
| **BPAT** hours missing by > 1 MW | **81.54 %** | **100.00 %** | **100.00 %** | 44.59 % |
| every other member (15, `Adjusted`) | ≤ \|0.365\| TWh | | | |

The charter's −3,206 MW / 81.5 % is **confirmed to the MW and the tenth of a percent**. But the
pooled 81.5 % understates the exposure in the years that matter: **in 2023 and 2024 the identity
fails in 100.00 % of hours — all 8,760, both years.** The pooled figure is diluted by the second
half of 2025, where BPAT's reporting is repaired (§2.2). BPAT is **20.47 %** of 2023-2025
footprint load, the largest member, so a derive that assumed the identity would have been wrong
for a fifth of the footprint in **every hour of two of the three training years**.

**What the naive derive would have produced** (`Σ₁₇ Total interchange` against the served schedule):

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| naive `Σ TI` | **+28.799** | **+32.612** | **+18.251** TWh (net EXPORTER) |
| served schedule | **−13.745** | **−12.891** | **−4.785** TWh (net IMPORTER) |
| error | +42.545 | +45.502 | +23.036 TWh |
| mean hourly error | +4,857 | +5,194 | +2,630 MW (15.0 / 15.7 / 7.9 % of mean footprint load) |
| **hours the two disagree on the DIRECTION of flow** | **6,143 (70.1 %)** | **6,063 (69.2 %)** | 2,985 (34.1 %) |

It is not a level offset that would wash out of a calibration. It **reverses the sign of the
footprint's annual position** and disagrees about which way the power is flowing in **seven hours
out of ten**.

### 0.2 The CAISO-facing magnitude — the number ledger item R-a was missing

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| **NWPP ↔ CISO measured seam** (+ = NWPP exports) | **+8.691** | **+11.388** | **+12.504** TWh |
| hours NWPP is exporting to CAISO | 7,510 (86 %) | 7,936 (90 %) | 8,041 (92 %) |
| as a share of \|the whole served schedule\| | **63 %** | **88 %** | **261 %** |
| CAISO's own PNW import tranches (`PNW_hydro_base` + `PNW_midC`) | 2,872 MW | 3,358 MW | 3,366 MW |
| …their annual energy at full output | 25.159 | 29.416 | 29.486 TWh |
| …utilisation that would reproduce the measured seam | **34.5 %** | **38.7 %** | **42.4 %** |

**R-a's exposure is 8.7 / 11.4 / 12.5 TWh per year, and it is the whole seam, not a corner of
it.** The CAISO side's PNW block stack is of exactly the right order to carry that energy — it
would run at a 35-42 % capacity factor to do so — which is the point: `PNW_hydro_base` is not an
incidental tranche that happens to share a name, it is a representation of this footprint sized
from a California capacity source (DMM RA `Imports` × the MIC north-of-Path-15 share) while NWPP
represents the same seam from a measured energy schedule. Two constructions, two sources, one
physical object, no conservation between them.

**R-a also under-names its own exposure.** The ledger names `PNW_hydro_base` (1,072 / 1,558 /
1,566 MW @ $28, the firm/contracted tranche CAISO prices as an inframarginal Tier-3 contract
proxy). `PNW_midC` (1,800 MW @ $36, the Mid-Columbia economy block) is **the same footprint** —
Mid-C is NWPP's own traded hub, the one NWPP-20 anchored its `WECC_CAN` seam on. The routed item
should carry both. **This lane changed nothing on the CAISO side and proposes nothing for it**
(rule 25 `[R-ISO-SCOPE]`); §4 states the exposure and it stays routed.

---

## 1. Preconditions, and what this lane found already built

Both preconditions **MET** at base sha `d54cd9c5`:

| Precondition | State |
|---|---|
| NWPP-20 landed | `INTERFACE_NEIGHBORS["NWPP"]` carries **3** blocks — `CAISO` / `WECC_SW` / `WECC_CAN` (`model/interchange/spec.py`) — and all three are inert: NWPP is absent from `REFERENCE_PRICE_DEFAULT_ISOS` and has no `IMPORT_ZONE` / `IMPORT_NODE_LINKS` entry, so `get_interchange_spec` returns an empty spec and they build no LP rows even under `--priced-interchange` |
| NWPP-11 interchange data landed | `data/raw/eia-930-interchange/` — 17 member DIBA files + `CISO` |

**NWPP-20 also already landed the served derive itself** (`eia930.envelopes.nwpp_net_interchange`,
`_SCALAR_INTERCHANGE_ISOS["NWPP"]`), on the construction its PRECOMMIT §3.4 fixed, and explicitly
**routed the residual adjudication to this lane** (`FINDING-nwpp-20` §5, and the derive's own
docstring). So this lane did not re-derive a construction that was already frozen against nothing
(rule 23 `[R-FROZEN-DERIVE]`): it **adjudicated the routed conflict, measured the construction
against the alternative it displaces, and pinned the trap so it cannot be re-armed.** The derive's
numbers are unchanged — `nwpp_net_interchange(2024)` reads −12.890671 TWh before and after this
branch.

---

## 2. The BPAT adjudication — TI is the defective series, and a natural experiment proves it

### 2.1 The residual is one BA's, on both column families

`r = NG − D − TI` over 2023-2025, all seventeen members, raw and `(Adjusted)` (TWh):

| BA | raw | `(Adjusted)` | | BA | raw | `(Adjusted)` |
|---|---:|---:|---|---|---:|---:|
| **BPAT** | **−84.271** | **−84.284** | | PACE | 0.000 | +0.002 |
| NEVP | +0.126 | +0.365 | | DOPD | 0.000 | −0.001 |
| GCPD | −0.109 | −0.109 | | WAUW | −0.001 | −0.000 |
| PGE | −0.036 | −0.036 | | NWMT | +0.002 | −0.000 |
| IPCO | −0.016 | −0.016 | | AVA, CHPD, PACW, PSEI, SCL, TPWR | ≤ \|0.003\| | ≤ \|0.0005\| |

`AVRN` and `GRID` carry **no `Demand` column at all** (null in all 26,304 hours) — they are
generation-only balancing areas where `Total interchange ≡ Net generation`, which is why they
enter the pool frame at zero demand and why they cannot be residual-tested. That is a
**structural property, not a gap.**

EIA's `(Adjusted)` family does **not** repair BPAT: the two columns agree to 0.013 TWh on an
84 TWh residual. NWPP-10's demand-column ruling, whichever way it had gone, never touched this.

**BPAT's residual is one-signed and persistent, not noisy**: of 26,292 hours, 21,315 read `r < 0`,
4,844 read exactly 0 and **133 read `r > 0`**. The **earliest exact zero in the whole three-year
record is the step hour itself** (§2.2) — before it, BPAT never once closes its own identity.
Percentiles
(p0 / p5 / p25 / p50 / p75 / p95 / p100) = **−7,702 / −5,324 / −4,397 / −3,810 / −2,478 / 0 /
+1,565 MW**.

### 2.2 The step is in ONE hour, and it is in `Total interchange`

BPAT monthly mean residual falls off a cliff, not a ramp:

| 2025-03 | 2025-04 | 2025-05 | **2025-06** | 2025-07 | 2025-08 | … | 2025-12 |
|---:|---:|---:|---:|---:|---:|---|---:|
| −3,514.8 | −2,786.9 | −2,767.9 | **−48.7** | −2.9 | −0.0 | | −0.0 MW |

Resolved to the hour, the transition is **exactly one hour wide**: UTC **2025-06-01 07:00** =
BPAT hour-ending **2025-06-01 00:00 Pacific**, the first hour of BPAT's local June.

| | hour before | hour at the step | move |
|---|---:|---:|---:|
| Demand (Adjusted) | 6,303 | 6,011 | −292 MW |
| Net generation (Adjusted) | 8,815 | 8,228 | −587 MW |
| **Total interchange (Adjusted)** | **7,045** | **2,217** | **−4,828 MW** |
| residual `r` | −4,533 | **0** | |

**That 4,828 MW is the single largest hour-to-hour move `Total interchange` makes in the whole of
2025** — the 100.000th percentile of \|ΔTI\|, and equal to the year's maximum to the MW. Demand
and Net generation move at their **80.1st and 80.4th** percentiles in the same hour: ordinary
hours. *The discontinuity is in TI and in nothing else.* Before the step: 3,631 hours, mean
−3,555.4 MW, **99.97 %** missing by > 1 MW. After: 5,129 hours, mean \|r\| **3.563 MW**, 94.6 %
within 1 MW.

This is what turns "which column do we trust" from a judgement into a measurement, and it is why
rule 14 `[R-ACCURATE]` points at TI rather than at the energy balance.

### 2.3 The natural experiment — the two constructions CONVERGE once BPAT is repaired

The step splits the record into a broken window and a repaired one. The footprint-position
constructions can be compared inside each:

| window | hours | `Σ₁₇ (NG − D)` | `Σ₁₇ TI` | spread | mean gap |
|---|---:|---:|---:|---:|---:|
| **pre-step** (2023-01-01 → 2025-06-01 07:00 UTC) | 21,166 | **−8.332** | **+75.273** | **83.604 TWh** | +3,950 MW |
| **post-step** (2025-06-01 07:00 → 2026-01-01 UTC) | 5,129 | **+3.980** | **+4.450** | **0.470 TWh** | **+92 MW** |

**`Σ (NG − D)` is the construction that is stable across the reporting change.** The moment BPAT's
TI is repaired, the two agree to 0.47 TWh over seven months — a 178× collapse in the spread, on
the same seventeen files, with no parameter and no choice. The energy-balance construction NWPP-20
adopted is therefore **validated out-of-window by BPA's own repair**, not asserted. That is the
adjudication the routing asked for, and it is **evidence of a kind a fitted choice cannot
produce**.

### 2.4 Where BPAT's over-report actually lives — INTERNAL legs, and the CAISO leg is clean

Mirror test on BPAT's per-counterparty book: BPAT's leg to X plus X's own leg to BPAT (a perfect
mirror sums to 0), TWh:

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| **external** (`CISO`, the only external counterparty with a committed file) | **−0.001** | **+0.057** | **+0.022** |
| **internal** (15 NWPP members) | **+16.339** | **+15.704** | **−3.976** |

Worst internal pairs: `BPAT↔GRID` +8.057 / +7.092, `AVRN↔BPAT` +3.472 / +3.762, `BPAT↔SCL`
+2.850 / +3.023, `BPAT↔AVA` +1.808 / +1.373; and the 2025 sign flip is the same convention change
(`BPAT↔PGE` −4.562, `BPAT↔PSEI` −3.060 against ≈ 0 in 2023-24).

**Two consequences, and they cut in opposite directions — both are reported.**

1. **The over-report is a wheeling artifact on legs that never cross the footprint boundary.** BPA's
   own feed header names the mechanism (NWPP-11 §6.2, verbatim): its BA *"includes some that are
   not BPA's"* and excludes loads *"served by transfer, scheduled out of region, or scheduled to
   customers with their own BAs such as Seattle and Tacoma."* So the defect is exactly where a
   boundary construction should be immune to it — and `Σ (NG − D)` is.
2. **It does NOT follow that the external-DIBA sum is safe.** `Σ external DIBA` minus GRID's
   Desert-Southwest legs reads **+16.689 TWh pre-step against `Σ (NG − D)` = −8.332**, and
   **+6.994 post-step against +3.980**. The gap narrows by an order of magnitude at the repair but
   **does not close** (~590 MW mean, post-step). BPAT's three external counterparties without a
   committed file (`BCHA`, `LDWP`, `BANC`) cannot be mirror-tested from this tree, so the residual
   is **named and left open**, not explained. This **refines** NWPP-11's "the external-DIBA sum
   still contains BPAT's through-flow": on the one external leg that *can* be tested it is clean,
   and the contamination is elsewhere. Card N4's ruling does not depend on it — the served
   schedule never reads the external-DIBA sum — but a future priced-seam lane (NWPP-56) would, and
   should not inherit this as settled.

### 2.5 GRID — the second source conflict, and the correction the derive applies

`GRID`'s external counterparty set is **exactly `{PNM, SRP, WALC}`** (measured on the committed
file; no other non-NWPP DIBA appears in any year), and those legs carry **+7.115 / +9.774 /
+10.131 TWh** — which the served schedule subtracts. The correction is right and this lane
confirms it: Gridforce Energy Management balances two physically separate resource sets, and
EIA-860 files the Desert-Southwest ones under other balancing authorities, so the footprint fleet
cannot generate them. **The residual conflict NWPP-11 §4.4 raised is NOT closed by this lane and
is not closeable from the interchange book**: GRID's EIA-930 net generation (16.790 / 18.632 /
17.707 TWh) still implies a **278-308 % capacity factor** on the 689.4 MW EIA-860 assigns that BA.
Removing the Southwest legs fixes what the *seam* asks of the fleet; it does not fix where **card
N5** places GRID's generation. Routed on, unchanged (§6).

---

## 3. The served schedule — summary

`served(t) = Σ₁₇ (NG_adj − D_adj)(t) − Σ GRID→{PNM, SRP, WALC}(t)`, export-positive.

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| `Σ₁₇ (NG − D)` | −6.630 | −3.116 | +5.346 TWh |
| GRID Desert-Southwest legs removed | +7.115 | +9.774 | +10.131 TWh |
| **served** | **−13.745** | **−12.891** | **−4.785 TWh** |
| mean | −1,569 | −1,472 | −546 MW |
| hours exporting | 1,908 (21.8 %) | 2,210 (25.2 %) | 3,622 (41.3 %) |
| duration curve p5 / p25 / p50 / p75 / p95 | −5,053 / −3,063 / −1,630 / −226 / +2,276 | −5,101 / −2,871 / −1,430 / +17 / +2,003 | −5,064 / −2,356 / −588 / +1,237 / +4,077 MW |
| extremes (max import / max export) | −8,144 / +5,472 | −9,114 / +7,016 | −7,865 / +9,267 MW |
| footprint load (pool frame, Adjusted) | 284.206 | 290.540 | 293.483 TWh |
| served as a share of load | **−4.84 %** | **−4.44 %** | **−1.63 %** |
| \|served\| at the median hour | 1,939 MW (6.0 % of that hour's load) | 1,786 (5.4 %) | 1,848 (5.6 %) |

**NWPP is a net IMPORTER** in all three years on this construction, so the served schedule
**lowers** what the footprint fleet must generate — the opposite sign to SPP's and SOCO's, and
`_SCALAR_INTERCHANGE_ISOS`' comment already says so. The 2023 → 2025 narrowing (−13.7 → −4.8 TWh)
is **partly the BPAT convention change and partly the 2025 hydro year** (footprint hydro fell
107.9 → 74.9 TWh, NWPP-11 §5.1); **it must not be quoted as a trend** — that is two bases and two
water years in one column.

**Two limitations of the served form, stated at the gate** (neither is a defect to fix here; both
are what the default-off priced links exist to address, lever NWPP-56):

- It is a **footprint-wide scalar spread across the five zones by load share** (`demand.py`, the
  `_SCALAR_INTERCHANGE_ISOS` branch — "no per-zone tie attribution yet"). The physical legs belong
  to BPAT / NEVP / PACW, i.e. NWPP-NW / NWPP-SNV / NWPP-OR; the scalar puts a share of them on
  NWPP-EAST and NWPP-INLAND, which have none.
- It is **exogenous and price-inelastic**. A measured net position is a rule-13 `[R-MEASURED]`
  admissible input — it regenerates for a forward year from forward drivers and responds to
  changed conditions through the same construction — but within a solved year it does not respond
  to the footprint's own price. **That is the property that makes §4 a disclosure and not a
  reconciliation.**

---

## 4. R-a — the CAISO double-count, DISCLOSED (and not fixed)

**Rule 25 `[R-ISO-SCOPE]` is the whole of this section's boundary.** Nothing under
`src/market_sim/model/interchange/caiso.py`, `config/iso_configs.py`'s CAISO block, or any CAISO
registry value was read for any purpose other than quoting it, and none was modified. **This lane
proposes no CAISO-side change.** The item stays routed to the CAISO lane; what it now carries is a
number.

### 4.1 The two representations, side by side

| | NWPP's side (this lane) | CAISO's side (quoted, untouched) |
|---|---|---|
| object | one scalar served schedule, −13.7 / −12.9 / −4.8 TWh net | a `WECC_import` zone (`load_share=0.0`) feeding NP15 and SP15_rest |
| the PNW energy | **netted inside** the footprint-wide scalar; not separately identified | `PNW_hydro_base` 1,072 / 1,558 / 1,566 MW @ **$28** + `PNW_midC` 1,800 MW @ **$36** |
| source | measured EIA-930 energy balance, hourly | DMM annual RA `Imports` capacity × published MIC north-of-Path-15 share; **prices are Tier-3 contract-cost proxies, `STATIC-FITTED-PENDING-MEASURED`** (gap register G-26, labelled at the constant) |
| path limits | registered `NeighborInterface("CAISO")` 6,733 MW, **default-OFF** | `WECC_import→NP15` 4,800 MW (Path 66/COI) + `→SP15_rest` 10,623 MW (Path 46), 7,500 MW simultaneous cap |
| price behaviour | **exogenous, price-inelastic** | **priced supply that competes in CAISO's merit order** |

### 4.2 What the exposure actually is — and what it is not

It is **not** that NWPP's fleet is asked to generate the CAISO export twice. The served schedule
is a **net** position, so the +8.7 / +11.4 / +12.5 TWh flowing to California is already netted
against the footprint's larger imports (BCHA, WACM and the rest) before the LP ever sees it.

The exposure is that **the same physical seam is represented twice, on two incompatible bases,
with nothing enforcing agreement between them**:

1. **In any cross-ISO aggregate the energy is counted twice.** NWPP's fleet physically generates
   the PNW→California flow and it is inside NWPP's ~288 TWh of modelled internal generation;
   CAISO's LP **independently synthesises the same energy** at its import node. Summing the two
   models' generation double-counts **8.7 / 11.4 / 12.5 TWh/yr** (upper bound: the PNW tranche
   stack's 25.2 / 29.4 / 29.5 TWh of capability). Any national emissions, generation or fuel-burn
   roll-up across the registered ISOs inherits this.
2. **Neither side constrains the other.** CAISO's PNW blocks can clear their full depth in an hour
   in which NWPP's served schedule has the footprint **importing** at 5-8 GW. There is no shared
   row, no shared limit, and no shared price. The measured seam says NWPP exports to CAISO in
   **86 / 90 / 92 %** of hours at a p50 of **+1,020 / +1,389 / +1,513 MW**; the model reproduces
   that correlation on neither side by construction.
3. **The price bases contradict.** CAISO prices this footprint's hydro at a **$28/MWh static
   contract proxy** that its own constant declares unmeasured; NWPP prices the same energy at its
   own fleet's marginal cost, from its own hydro budget and gas basis. Under
   `caiso_perhub_firm_base` the $28 block is deliberately held **inframarginal** so CAISO clears
   domestic — i.e. the CAISO side is designed around this footprint *not* setting its price, which
   is a modelling choice this desk has no standing to revisit and every reason to name.

### 4.3 Why it could not be fixed here even if this lane wanted to

NWPP has **no admissible hourly price series** (NWPP-13 read NO), which is why card N4 ruled the
priced links default-off in the first place. A reconciled seam needs a price on both sides; NWPP
does not have one yet. So the honest state is: **served schedule now, priced seam later
(NWPP-56), double-representation disclosed in between.** Quantified above so the CAISO lane can
decide against a number instead of a name.

---

## 5. Files changed

| File | Change |
|---|---|
| `docs/handoffs/FINDING-nwpp-34-2026-09-14.md` | **NEW** — this file |
| `tests/unit/data/test_nwpp_served_interchange_trap.py` | **NEW** — 7 pins: the identity holds for PACW/PSEI/TPWR to 0.000 MW; BPAT misses in > 99 % of pre-step hours at a mean below −3 GW; **the step is in TI and nowhere else** (largest \|ΔTI\| of 2025, D and NG ordinary); the identity closes post-step; the naive `Σ TI` derive reverses the annual sign and disagrees hour-by-hour in > 60 % of 2024; GRID's external DIBA set is exactly `{PNM, SRP, WALC}`. Hydration-guarded, 0.7 s, no solve |
| `src/market_sim/data/eia930/envelopes.py` | `nwpp_net_interchange` docstring **only** — the routed adjudication line (*"is routed (FINDING-nwpp-20 §5; NWPP-34)"*) replaced by its result: the one-hour step, the natural experiment, the internal/external mirror split, and the test that pins it. **No executable line changed**; `nwpp_net_interchange(2024)` reads −12.890671 TWh on both trees |

**Not touched, deliberately:** `model/interchange/caiso.py` and every CAISO registry value; every
other region's seam rows; `ScenarioConfig`; the three `INTERFACE_NEIGHBORS["NWPP"]` blocks and
their default-off posture; `_SCALAR_INTERCHANGE_ISOS`; the plan; the ledger;
`docs/calibration-log/`; any matrix shard (rule 28 — **this lane tested no mechanism**: it armed
nothing, flipped no default and moved no cell, so duties (b) and (c) do not attach).

## 5.1 Checks

| Check | Result |
|---|---|
| `tests/unit/data/test_nwpp_served_interchange_trap.py` | **7 passed** (0.7 s) |
| `tests/unit/data/test_nwpp_pool_frame.py` + `tests/unit/config/test_nwpp_registration.py` | **23 passed** |
| `ruff check` / `ruff format --check` on both changed files | clean |
| derive output unchanged | `nwpp_net_interchange(2024)` = −12.890671 TWh, base and branch |

## 5.2 Reproduction

Every number in §0-§4 comes from four committed sources and no fitted step: the per-BA extracts
`data/raw/eia-930-hourly/<BA> hourly.parquet` (the `(Adjusted)` family throughout, per NWPP-10's
convention), the per-counterparty book `data/raw/eia-930-interchange/<BA> interchange hourly.parquet`,
`eia930.envelopes.nwpp_net_interchange` / `frames._pool_hourly_frame`, and the quoted CAISO
constants in `model/interchange/spec.py` (`IMPORT_TRANCHES`, `IMPORT_TRANCHES_BY_YEAR`) and
`config/iso_configs.py`. Windows are UTC, 2023-01-01 → 2026-01-01, on the pool clock; the residual
is `NG_adj − D_adj − TI_adj`; the mirror test sums each pair's two reported legs. The derived
ratios in §0.2 are `seam TWh ÷ (tranche MW × 8,760 h)`.

---

## 6. Routed on (nothing new is claimed closed that is not)

| Item | To | State |
|---|---|---|
| **R-a — the CAISO double-count** | the CAISO lane (rule 25) | **STILL ROUTED, now with a magnitude**: 8.7 / 11.4 / 12.5 TWh/yr, bounded above by the 25.2-29.5 TWh the PNW tranche stack can carry, and the item should be **extended from `PNW_hydro_base` to `PNW_hydro_base` + `PNW_midC`** (§0.2, §4) |
| **GRID's 278-308 % implied capacity factor** | card **N5** (NWPP-11 §7 R-3) | **OPEN.** The served schedule's Southwest-leg removal fixes what the seam asks of the fleet; it does not decide where GRID's 16.8-18.6 TWh of EIA-930 generation belongs (§2.5) |
| **The external-DIBA sum's un-closed residual** | NWPP-56 (the priced-seam lever) | **NEW, OPEN.** ~590 MW mean post-step, on legs (`BCHA`, `LDWP`, `BANC`) with no committed counterparty file to mirror-test. Card N4 does not depend on it; a priced seam would (§2.4) |
| **The 2023 → 2025 narrowing of the net position** | whoever quotes it | **NOT a trend.** Two reporting bases (the 2025-06 step) and two water years (hydro 107.9 → 74.9 TWh) in one column (§3) |
| **Per-zone attribution of the served scalar** | NWPP-56 | Known and stated: a footprint-wide scalar spread by load share puts CAISO-facing flow on NWPP-EAST / NWPP-INLAND, which have no California leg (§3) |

---

## 7. Log entry

*(For the desk to append verbatim to `docs/calibration-log/nwpp.md`.)*

```markdown
## 2026-09-14 — NWPP-34: the seam derive — BPAT adjudicated, R-a quantified

Lane NWPP-34, branch `claude/nwpp-34-seam-a7f3`, base sha `d54cd9c5`. No solve, no mechanism, no
matrix cell, nothing armed. Card N4 (served measured interchange, priced links default-off) is
unchanged and unchallenged.

**The BPAT trap is confirmed and is worse than the charter states.** Residual `NG−D−TI` at BPAT
= **−84.284 TWh / −3,205.7 MW mean** over 2023-2025 (the charter's figures, to the MW), missing by
> 1 MW in **81.54 %** of pooled hours — but in **100.00 % of every hour of 2023 and of 2024**, the
pooled figure being diluted by the repaired second half of 2025. BPAT is **20.47 %** of footprint
load. Every other member closes to ≤ |0.365| TWh on the Adjusted family; AVRN and GRID carry no
Demand column at all (TI ≡ NG, structural). The naive `Σ TI` derive would have read the footprint
as a **+28.8 / +32.6 / +18.3 TWh net EXPORTER** where the energy balance makes it a **−13.7 /
−12.9 / −4.8 TWh net IMPORTER** — and would have disagreed about the **direction** of flow in
**70.1 / 69.2 / 34.1 %** of hours.

**The adjudication rests on a natural experiment, not a choice of column.** BPAT's TI steps onto
the repaired convention in **ONE hour** — hour-ending 2025-06-01 00:00 Pacific — where TI falls
**4,828 MW, the single largest hourly move it makes in 2025** (100.000th percentile of |ΔTI|),
while Demand (−292) and Net generation (−587) move at their **80th** percentiles. Across that
step `Σ(NG−D)` and `Σ TI` **converge**: 83.604 TWh apart (+3,950 MW mean) over the 21,166 hours
before, **0.470 TWh apart (+92 MW) over the 5,129 hours after**. `Σ(NG−D)` is the construction
that survives the reporting change — which is the evidence NWPP-20's construction was routed here
to obtain. BPAT's over-report is confined to **internal** legs (mirror asymmetry +16.3 / +15.7 /
−4.0 TWh; worst `BPAT↔GRID` +8.1) while its **CAISO-facing leg mirrors CISO's own book to
−0.001 / +0.057 / +0.022 TWh**. GRID's external DIBA set is exactly {PNM, SRP, WALC}, confirming
the Southwest-leg correction; GRID's 278-308 % implied CF stays open to card N5.

**R-a now carries a number.** The NWPP↔CISO measured seam is **+8.691 / +11.388 / +12.504 TWh**,
NWPP exporting in **86 / 90 / 92 %** of hours — **63 / 88 / 261 %** of the magnitude of the whole
served schedule. CAISO's PNW import tranches (`PNW_hydro_base` 1,072/1,558/1,566 MW @ $28 +
`PNW_midC` 1,800 MW @ $36 = 25.2 / 29.4 / 29.5 TWh at full output) would run at a **34.5 / 38.7 /
42.4 %** capacity factor to carry it: the CAISO representation **is** this seam, not a corner of
it. The exposure is not double-*generation* (the served schedule is a net), it is
double-*representation* — a cross-ISO aggregate counts 8.7-12.5 TWh/yr twice, neither side
constrains the other, and the price bases contradict ($28 static Tier-3 proxy vs NWPP's own
marginal cost). **R-a should be extended to name `PNW_midC` as well.** Nothing on the CAISO side
was touched or proposed (rule 25); the item stays routed.

**Also routed, new:** the external-DIBA sum does **not** close even post-step (~590 MW mean, on
BCHA/LDWP/BANC legs with no counterparty file to mirror-test) — immaterial to card N4, material to
a priced seam (NWPP-56). And the 2023 → 2025 narrowing of the net position is **two bases and two
water years**, never a trend.

Deliverables: `docs/handoffs/FINDING-nwpp-34-2026-09-14.md`; `tests/unit/data/
test_nwpp_served_interchange_trap.py` (7 pins, hydration-guarded, 0.7 s); a docstring-only update
to `nwpp_net_interchange` closing its routed line. Derive output byte-identical
(−12.890671 TWh, 2024).
```

---

## 8. Gates and rules

| | State after this lane |
|---|---|
| **Card N4** | **UNCHANGED and now evidenced.** Served measured interchange, priced links default-off; the construction is validated by §2.3's natural experiment rather than asserted |
| **G10** (seam-name uniqueness) | untouched — no `_HR_GAS_ELASTIC` key names CAISO / WECC_SW / WECC_CAN; this lane added no key |
| **R-a** | **ROUTED, quantified**, and recommended for extension to `PNW_midC` |
| **R-3** (GRID) | **OPEN**, unchanged — the seam correction is not the N5 placement |
| Rule 13 `[R-MEASURED]` | observed — the served schedule is a measured input with a forward construction, never an outcome pinned to an actual; nothing was padded, rescaled or offset |
| Rule 14 `[R-ACCURATE]` | observed — every divergence (BPAT, GRID, the external-DIBA residual, the CAISO double-representation) is **reported at full magnitude and corrected away nowhere** |
| Rule 23 `[R-FROZEN-DERIVE]` | observed — no measured-behaviour parameter was re-derived; no residual moved anything |
| Rule 25 `[R-ISO-SCOPE]` | observed — zero CAISO artifacts modified, zero other-region seam rows touched, no value transferred in either direction |
| Rule 27 `[R-PUSH]` | observed — `envelopes.py` (1,933 → 1,948 lines) edited in place with the Edit tool and pushed as on-disk bytes; blob verified after push |
| Rule 28 `[R-MECH-MATRIX]` | **no duty attaches** — no mechanism proposed or tested, no `ScenarioConfig` field added, no default flipped, no run registered |
