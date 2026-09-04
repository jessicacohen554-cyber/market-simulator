# FINDING — nyiso-187 (`ct-steam-merit` lane): the hours the market gave to NYC / Long Island combustion turbines and steam are OUT OF THE MONEY at the actual price on the LP's installed offer (bucket B 0.57–0.89, bucket C nil) — owner = out-of-market commitment, the owner-closed load-pocket route — with the CT_PEAKER separation carried by an owner-accepted markup stack; the Astoria registry split's availability half is repaired by the caiso-196 remap form and A/B-solved

**Session:** nyiso-187, `ct-steam-merit` lane (`claude/nyiso-187-ct-steam-merit`),
NYISO backcast-calibration track, 2026-09-04. **Solves run: TWO** — the Object-2
arm (`results/calibration/nyiso187_astoria_routing`) and its same-HEAD control on
the committed artifacts (`results/calibration/nyiso187_control`, an instrument).
**Keeper at entry: `2026-09-04-nyiso-186-astoria-identity`** — NOT-YET, target
grade 5, fail set {C1-2024 `CC_REGULAR` +3.80 TWh / +3.1 pp, C3a-2025 −10.4 %
(owner-court, not touched), C3c}.
**Pre-registration:** `results/calibration/PREREG-nyiso187-ct-steam-merit-position.md`,
pushed at `533e37e6` before the first measurement; every bar below is read
verbatim. **Machine records:** `results/calibration/_nyiso187_merit_position.json`
(installed-offer basis), `_nyiso187_merit_position_bare_srmc.json` (the
post-hoc sensitivity, labelled), probe `scripts/probes/nyiso187_merit_position.py`.

---

## 1. The result in one paragraph

On the keeper's own 2024 sidecars, in every deficit hour of every class × zone
the market's extra CT / steam energy was filled from the model's cheapest
un-run capacity and each MW bucketed against the model's zonal price and the
actual RT price. **Bucket B — out of the money at BOTH prices — carries 0.57 to
0.89 of every class-zone's deficit** (`CT_PEAKER` NYC 0.85 / LI 0.83; `CT_CHP`
NYC 0.88 / LI 0.89; `ST_GAS` LI 0.89 / CH 0.75 / NYC 0.57), **bucket C — in the
money at the model price yet un-run — is nil (≤ 0.011)**, and bucket A —
priced out only by the model's price — is 0.11–0.42. Under the pre-registered
ownership rule the owner is **OUT-OF-MARKET commitment** in every cell: the
capacity the market ran would not clear at the price the market itself paid,
on the model's offer. M4 finds **no measured input wrong on its source** — CT
delivered gas, heat rates and carbon are what their sources say — so no
CT / steam-side repair is admissible. The post-hoc sensitivity (labelled, not a
bar) sharpens WHAT separates them: with every markup removed, **96 % of the
NYC `CT_PEAKER` deficit capacity and 73 % of Long Island's would be in the
money at the model's own price** — the CT's bare SRMC (~$30) sits under both
prices and the ~$24/MWh stack of committed-band, start-amortization and
bid-cost markups puts it out; for `CT_CHP` and `ST_GAS` the bare cost itself is
above the actual price. That stack is an **owner-accepted trade** (nyiso-96 §5
rejected the amortization on rule 1; the owner re-armed it and recorded the
peaker under-representation as a "known, deliberately-accepted
misrepresentation", un-acceptable only by the load-pocket lane) — so the
2024 `CC_REGULAR` cell is blocked behind an owner ruling and an owner-closed
data route, not behind a CC mechanism. **Object 2:** the Astoria registry
split's availability half is repaired by the caiso-196 registry form (two
`CAMPD_UNIT_PLANT_REMAP` entries), the outage extract and tranche artifact
re-derived with their committed invocations (G-DELTA: only 55375 / 57664 rows
move; the ramp-envelope artifact's class-fraction fallback ALSO moves and is
therefore excluded by the pre-registered stop), and the arm is A/B-solved (§4).

---

## 2. The decomposition, as pre-registered and as measured (2024, keeper sidecars)

**Instrument.** Model class MW from `unit_hourly` (installed `mc`, `mw`,
`cap_mw`, `red_cost`); measured class MW from the bench's per-plant CAMPD
series; model zonal price from `system`; actual ISO-level RT from
`actual_lmp_hourly_NYISO.parquet`, with the zonal premium from the 2024 sample
months (6 months: NYC +$2.80, Capital +$0.17, Long Island +$5.66) as the
sensitivity column. **S0 read FAIL** (the nyiso-181 reconstruction reproduces
the installed `mc` only up to the start-amortization and bid-cost terms it does
not model: max |Δ| $273 over 704 units), so per PREREG §5 the M4 term
decomposition is reported with its residual labelled **"markup" = installed
`mc` − (fuel × HR + VOM + carbon)** — every markup term the runner installs,
not one named term.

| class @ zone | measured / model TWh | D | A / **B** / C (installed offer) | A / B (+ zonal premium) | bare-SRMC A / B / **C** (post-hoc) | cheapest un-run `mc` = fuel×HR + VOM + carbon + **markup**, vs model / actual price (medians, $/MWh) | CC excess in deficit hours |
|---|---|---|---|---|---|---|---|
| `CT_PEAKER @ NYC` | 1.429 / 0.132 | **1.325** | 0.15 / **0.85** / 0.003 | 0.18 / 0.82 | 0.02 / 0.02 / **0.95** | 53.9 = 15.4 + 3.5 + 10.6 + **24.1** vs 37.9 / 36.2 | 0.33 (0.25 TWh); CC depth $11.7, headroom 158 MW |
| `CT_CHP @ NYC` | 1.693 / 0.812 | **1.026** | 0.11 / **0.88** / 0.009 | 0.16 / 0.83 | 0.04 / 0.55 / **0.41** | 34.1 = 14.9 + 3.5 + 13.3 + **2.1** vs 32.3 / 26.9 | 0.98 (0.74 TWh); CC depth $7.4, headroom 236 MW |
| `ST_GAS @ NYC` | 2.964 / 4.970 | **0.276** | 0.42 / **0.57** / 0.011 | 0.48 / 0.51 | 0.38 / 0.56 / **0.07** | 41.7 = 28.6 + 4.0 + 8.9 + **-0.0** vs 39.2 / 37.0 | 0.29 (0.22 TWh); CC depth $9.5, headroom 223 MW |
| `CT_PEAKER @ Capital_Hudson` | 0.001 / 0.006 | **0.001** | 0.34 / **0.66** / 0.000 | 0.34 / 0.66 | 0.32 / 0.54 / **0.14** | 58.3 = 26.0 + 3.5 + 12.4 + **15.2** vs 37.1 / 40.9 | 0.01 (0.01 TWh); CC depth $10.3, headroom 660 MW |
| `ST_GAS @ Capital_Hudson` | 1.629 / 0.520 | **1.188** | 0.24 / **0.75** / 0.006 | 0.25 / 0.75 | 0.24 / 0.66 / **0.10** | 45.1 = 29.5 + 4.0 + 11.2 + **0.0** vs 39.9 / 37.9 | 0.52 (0.90 TWh); CC depth $9.1, headroom 600 MW |
| `CT_PEAKER @ Long_Island` | 0.645 / 0.110 | **0.569** | 0.17 / **0.83** / 0.002 | 0.23 / 0.77 | 0.09 / 0.18 / **0.73** | 52.5 = 22.2 + 3.5 + 10.6 + **16.1** vs 39.0 / 35.6 | 0.53 (0.20 TWh); CC depth $8.7, headroom 142 MW |
| `CT_CHP @ Long_Island` | 0.528 / 0.081 | **0.452** | 0.11 / **0.89** / 0.002 | 0.19 / 0.81 | 0.09 / 0.76 / **0.15** | 39.7 = 25.0 + 3.5 + 7.0 + **2.4** vs 34.7 / 29.7 | 0.94 (0.36 TWh); CC depth $6.8, headroom 176 MW |
| `ST_GAS @ Long_Island` | 5.340 / 2.987 | **2.415** | 0.11 / **0.89** / 0.007 | 0.20 / 0.79 | 0.12 / 0.78 / **0.10** | 41.3 = 25.4 + 4.0 + 11.8 + **-0.0** vs 34.2 / 29.3 | 0.92 (0.35 TWh); CC depth $6.4, headroom 181 MW |

**Verdicts on the bars (PREREG §3):** every cell reads **OWNER = OUT-OF-MARKET
(G)** — `b ≥ 0.50` everywhere, including `ST_GAS @ NYC` at 0.57 (0.51 with the
premium). Bucket C is nil in every cell, which independently reproduces
nyiso-181's retirement of the "un-run in-the-money" object on a per-zone
grain. Bucket A never reaches 0.50. **M4 names no wrong input**: delivered CT
gas in the deficit hours (median $1.64–2.34/MMBtu) is the curated Transco Z6
NY daily index the flag reads; the `CT_PEAKER` heat rate (9.0) is the
measured loaded rate; the carbon term ($7–13/MWh) is RGGI at the measured
plant rates.

### 2.1 Where the CC fill sits

The CC excess coincides with the `CT_CHP` and Long Island deficits almost
entirely (0.98 / 0.94 / 0.92 of the excess falls in their deficit hours) and
with the `ST_GAS` CH deficit at 0.52; the NYC `CT_PEAKER` deficit hours carry
only 0.33 of it. In those hours the NYC / CH combined cycles run $7–12/MWh
under the model price with 140–660 MW of headroom — the fill is robust to
any small CC repricing (nyiso-186 §4.1 measured exactly that).

### 2.2 What separates the classes from the money, and who owns it

* **`CT_PEAKER` (NYC, LI):** bare SRMC is IN the money at both prices in 73–96 %
  of the deficit capacity; the $16–24/MWh markup stack is the separator.
  The stack is the registered `CT_PEAKER` committed band (1.35 vs a measured
  `phys` 0.843 — a DOF-ledger residual entry), `tranche_startup_amortization`
  + `_measured_runs` (measured NREL start ÷ measured run) and the P1 bid-cost
  markup. **nyiso-96 §5 measured that 53–66 % of the market's CT energy clears
  BELOW bare SRMC at its own zonal price and rejected the amortization on rule
  1; the owner re-armed it (calibration log, `2026-07-29-nyiso-96-ctamort`)
  and recorded the peaker under-representation as a deliberately-accepted
  misrepresentation, to be un-accepted only by the load-pocket lane
  (`scuc_load_pocket_commitment`, cell G, data route closed at nyiso-163b).**
  Nothing here re-opens either; the measurement sizes the trade.
* **`CT_CHP` (NYC, LI) and `ST_GAS` (LI, CH):** bare SRMC itself is above the
  actual price in 55–78 % of the deficit capacity — the market ran them out
  of merit (the nyiso-175 §3.4 RESPONSE signature and the nyiso-181 steam
  deficit, both out-of-market). No offer term reaches them.
* **`ST_GAS @ NYC`:** the only near-split cell (A 0.42 / B 0.57): the one
  place the model's own price level does half the work — the C3a / C3b lane.

**So the 2024 `CC_REGULAR` cell closes from the CT / steam side only through
mechanisms the owner has closed or accepted, and no CC lever is proposed
(PREREG §2 ownership rule).**

---

## 3. Object 2 — the Astoria registry split's availability half: the repair and its measured footprint

**Correction to nyiso-186 §3 / §5.2 item 2:** the outage derive DOES apply
`campd.CAMPD_UNIT_PLANT_REMAP` before its group lookup (lines 405 / 1568 of
`derive_campd_unit_outages.py`) and the tranche derive loads through
`campd.load_campd_hourly` → `_normalize_campd`; only the merit-order PANEL
reads raw parquets. The caiso-196 registry form therefore reaches both.

**The change (one registry fact, zero parameters):** `(55375, "CT3") → 57664`,
`(55375, "CT4") → 57664` — EIA-860 files CT3 / CT4 / ST2 under Astoria Energy
II; eGRID `PLNGENAN(55375)` = EIA-923 (55375 + 57664) to < 0.5 MWh in seven
vintages (nyiso-186 §3). Re-derived with the committed `derive_invocation`
blocks verbatim (`--per-unit-crosswalk --merit-order-guard --min-outage-days 5`,
years 2019–2026; tranches `--per-unit-attribution --merit-order-guard`,
2023–2025; rule 23: the data change cited is EIA-860's plant boundary).

| artifact | G-DELTA (rows keyed off 55375 / 57664) | what moved |
|---|---|---|
| `campd-unit-outages-perunitmerit-NYISO.csv` | **none** (3,674 → 3,668 rows; 91 removed, 85 added, all at 55375 / 57664) | CT1 / CT2 297.5 MW on a **595 MW** plant (was 1,221); CT3 / CT4 **325.0 MW on 57664's 650 MW** (were 313.0 on 55375's 1,221) |
| `campd-unit-outages-layup-perunitmerit-NYISO.csv` | none | byte-identical (1,254 rows) |
| `thermal_tranches-perunitmerit-NYISO.csv` | **none** (85 → 86 rows) | 55375: committed 70.0 → 60.6 %, online_frac 0.992 → 0.951, median CF **150 → 99.5 %**, peaking 2.6 → 0.3; **57664 gains its row**: committed 38.9 %, online_frac 0.925, median CF 102 % |
| `campd_ramp_envelopes_NYISO.csv` | **STOP fired** — the `(0, CC)` class-fraction fallback row moves (0.4907 → 0.5000 up, 0.5623 → 0.5904 down) because it pools the plant population | 55375 splits into 55375 (626 MW obs, 372 / 449 MW·h) + 57664 (626 MW, 416 / 454); **EXCLUDED from the arm** per PREREG §3 S1, committed file restored; footprint recorded, handed forward |
| `plant_emission_rates_v2` (pooled rows the LP reads) | not re-derived — a `--repool` rebuilds every NYISO plant's pool | 57664 carries a class-default 0.4206 t/MWh against 55375's measured 0.3807; the identity would give it the facility's measured rate. Handed forward as a measured footprint |
| every other CAMPD-fed NYISO artifact | reads raw parquets (not the normalizer) | unaffected |

---

## 4. The Object-2 A/B, at full magnitude (control = same-HEAD replay on the committed artifacts, BIT-IDENTICAL to the keeper: 0 of 52,560 hourly zonal prices differ in every year; arm = `2026-09-04-nyiso-187-astoria-routing`)

**G-DELTA:** zero `scenario_config` fields; the arm resolves the same artifact
NAMES on the perunitmerit basis with the re-derived shas; the remap carries
exactly the two Astoria entries beyond CAISO's. **G-INPUTS / G-DOF / G-ENGAGE**
PASS (attestation `computed_checks`, `scripts/gen_nyiso187_attestation.py`).

### 4.1 Where the energy went (P1 unit-hourly, TWh; mean available MW)

| year | Astoria Energy I 55375 | avail MW | Astoria Energy II 57664 | avail MW | site | class `CC_REGULAR` | `ST_GAS` |
|---|---|---|---|---|---|---|---|
| 2023 | 4.134 → **4.503** (923: 4.078) | 487 → 531 | 4.679 → **4.275** (923: 3.896) | 592 → 540 | 8.813 → 8.778 (923: 7.974) | 33.568 → 33.552 (-0.016) | 10.360 → 10.365 |
| 2024 | 4.064 → **4.503** (923: 4.150) | 480 → 531 | 4.683 → **4.229** (923: 3.990) | 592 → 536 | 8.747 → 8.732 (923: 8.140) | 38.101 → 38.098 (-0.003) | 8.882 → 8.881 |
| 2025 | 2.617 → **4.068** (923: 3.900) | 311 → 482 | 4.661 → **3.067** (923: 2.116) | 592 → 392 | 7.278 → 7.135 (923: 6.016) | 36.736 → 36.672 (-0.064) | 9.529 → 9.517 |

Every pre-declared expectation holds: (i) 57664's 2025 energy FALLS by 1.59 TWh
as its outage becomes visible (residual +0.95 over EIA-923, from +2.55); (ii)
55375 is no longer derated for its sibling and rises in every year (2025:
−1.28 → +0.17 over EIA-923); (iii) the class cell moves by ≤ 0.06 TWh — the
family is pinned; (iv) no price claim. **The site's representation is
corrected while the class total is untouched: this is a rule-1 / rule-14
repair, not a gate lever, and it is reported as such.**
