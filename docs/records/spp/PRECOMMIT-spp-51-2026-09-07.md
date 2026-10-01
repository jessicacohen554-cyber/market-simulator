# PRECOMMIT — SPP-51: the priced seams (MISO / AECI / ERCOT), P2's forward mechanism

**Lane** SPP-51 · **Model** Fable `claude-fable-5-1` · **Date** 2026-09-07 ·
**Branch** `claude/spp-51-priced-seams-hqgei3` (stem `claude/spp-51-priced-seams-t4nb`) ·
**DATA PROFILE** `spp` (full clone — every blob local)
**Plan** `docs/multi-iso/spp-addition-plan-2026-09.md` §3 P2/P3 (ruled r#2), §5 row SPP-51, §4 W5 charter
**Control** keeper-3 `2026-09-07-spp-3-screened-input` = `results/calibration/spp43_screened_B`,
`git_sha 623184f3` (rule 29(b) form 4 — no control solve)
**Inputs** FINDING-spp-33 entire (§3 `hr_by_year`, §4 R2, §2/§6 R1, §5/§6 R3, §7/§7b), FINDING-spp-20 §5 R-7,
`model/interchange/spec.INTERFACE_NEIGHBORS["SPP"]`, MISO keeper `2026-09-07-miso-233-spp-hourly`
(`results/calibration/miso233_sppseam_K`, `PRECOMMIT-miso233-spp-hourly-seam-2026-09-07.md` — read, never edited)

> Written BEFORE any solve. Every number below is computed from committed inputs and the committed keeper-3
> bundle (zero LP). §3.4 declares a pre-solve gate and §3.5 records its outcome; the screen (§4) is reached
> only if §3.4 passes.

---

## 0. TL;DR

1. **Three adjudications, all made (§1):** (a) a per-ISO anchor map for the `hr_by_year` producer, one entry per
   SPP neighbour, with an explicit failure where the producer used to `continue` silently; (b) the registered flat
   `marginal_heat_rate`s divide by bare Henry Hub where the pricing formula multiplies `(HH + gas_basis)` — corrected
   to the `HH + basis` construction; (c) the ERCOT DC-tie limit moves from the 820 MW CDR rating sum to the **835 MW
   measured clip** (rule 14), misalignment stated.
2. **A blocker the charter did not anticipate (§2): at HEAD `--priced-interchange` cannot build a priced seam for
   SPP.** `IMPORT_ZONE` and `IMPORT_NODE_LINKS` carry no SPP entry (SPP-20 registered "no import node, G7" for the
   served keeper), so `get_interchange_spec` returns an empty spec, `extend_with_import_node` no-ops, and the flag's
   only effect would be to DROP the served schedule — an SPP with no interchange at all. The obvious repair (one
   external bus linked to both zones) is a free wheeling path around the SPP-53 3,400 MW N↔S corridor — the exact
   defect `split_miso_south_external_node` exists to remove on MISO's RDT. The structurally right topology is two
   external buses, one per side, with the MISO seam split into its West (→ SPP-North) and South (→ SPP-South) legs.
   That is a mechanism-shaped topology change outside this lane's files; it is DESIGNED here and ROUTED, not built.
3. **Zero-LP phase 0 (§3): the screen year is 2024** (largest gross MWh through the three seams, 9.706 TWh), and
   **the pre-solve gate P0-b FAILS on the MISO seam in every year and both runs** — the MEASURED SPP hub minus the
   MEASURED MISO-West / MISO-South anchor predicts the MEASURED seam direction in 0.42–0.50 of non-hold hours
   (corr(spread, import) −0.02…+0.08), i.e. no better than a coin flip, on the seam that carries 41–47 % of the
   footprint. **Per rule 29(0) the screen solve is NOT spent.** ERCOT alone reads 0.56–0.61 (weak pass) but cannot
   be armed alone under the all-or-nothing served/priced switch; AECI's spread is degenerate by construction (its
   anchor IS the SPP hub).
4. **What lands (§5):** the corrected, per-zone-anchored SPP blocks (default-off, byte-identical no-op), the producer
   anchor map, tests, the SPP shard cell `U → R` with this evidence, FINDING-spp-51. **No solve, no bundle, no
   registration, no keeper change.**

---

## 1. The three adjudications

### 1(a) The anchor map — one entry per SPP neighbour

`scripts/data/derive_neighbor_hr_by_year.py::_NEIGHBOR_LMP_ISO` is keyed by neighbour NAME, globally
(`{"MISO": "MISO", "NYISO": "NYISO", "PJM": "PJM", "SPP": "SPP"}`), read as `actual_lmp_hourly_<value>.parquet`.
Against SPP's registered anchors it reaches none: `MISO` resolves to the MISO **system** file (the registration
anchors on the West/South zonal rows), and `AECI` / `ERCOT` have no key so the loop `continue`s silently — one
wrong-anchor row printed, two seams dropped with no diagnostic (FINDING-spp-33 §2). The repair is a **per-ISO map**,
`{iso: {neighbour: (file stem, zone filter)}}`, so a name shared by two ISOs (PJM's and SPP's `MISO`) can never take
the wrong file, and an SPP neighbour is anchored exactly as its `spec.py` block says:

| SPP block | Settlement location / hub it anchors to | Why | Producer entry |
|---|---|---|---|
| `MISO_West` (was the North leg of `MISO`) | `actual_lmp_hourly_zonal_MISO.parquet`, `zone == "MISO-West"` (the `MINN` hub) | the MISO zone physically adjacent to SPP-North (Dakotas / MN / IA ties: AMRN MEC ALTW DPC GRE MDU NSP OTP on SPP's own meter) | `("zonal_MISO", ("MISO-West",))` |
| `MISO_South` (was the South leg of `MISO`) | same file, `zone == "MISO-South"` (ARKANSAS / LOUISIANA / MS / TEXAS hubs, per-zone mean) | the MISO zone adjacent to SPP-South (Entergy / Cleco ties: EES CLEC) | `("zonal_MISO", ("MISO-South",))` |
| `AECI` | `actual_lmp_hourly_SPP.parquet` — **declared PROXY** (AECI publishes no LMP) | unchanged from SPP-20 | `("SPP", None)` |
| `ERCOT` | `actual_lmp_hourly_ERCOT.parquet`, system RT | unchanged from SPP-20 | `("ERCOT", None)` |

**Why the MISO seam is split into two blocks.** SPP-20's block anchored on "the two MISO zones physically adjacent
to SPP — one price per zone" and averaged them equal-weight (SPP-33 §2). The two zones are different prices
(RT 28.75 / 27.43 / 40.19 West vs 27.04 / 25.12 / 35.45 South, $1.7–4.7 apart) that border **different SPP zones**,
and any LP landing needs them on different sides of the N↔S corridor (§2). One block per bordering zone is the
per-zone form of the same registration; SPP-33's combined table is reproduced exactly as the equal-weight mean of
the two legs (§1(b) table), which is the check that nothing was re-derived. The names `MISO_West` / `MISO_South`
are unique across every ISO's registry, so `_assert_hr_gas_elastic_keys_unique` (plan §7 G10) is satisfied and
— reported, NOT acted on, per the charter — the R3 name collision that blocked a forward elasticity for SPP↔MISO
no longer exists for these names (`_HR_GAS_ELASTIC` is untouched; no key is added).

**The explicit failure.** An ISO with no anchor map raises `SystemExit` with a message; a neighbour with no anchor
entry is PRINTED as such (`# <name>: no measured anchor registered — structural marginal_heat_rate kept`, the
Carolinas/TVA/LGEE case, which is legitimate); a declared anchor whose file or rows are absent raises instead of
`continue`-ing. Other ISOs' entries (PJM → MISO system + NYISO; MISO → PJM + SPP) are carried unchanged and their
emitted tables are byte-identical (test).

### 1(b) The HH + basis correction — which heat rate the formula multiplies

The seam price is built in `src/market_sim/data/neighbor_price.py`:

* `neighbor_gas_price` (line 249–250): `henry_hub = _hold_flat_extrapolate(HENRY_HUB_TRAJECTORIES[...], year)`;
  `return henry_hub + neighbor.gas_basis` — the **delivered** gas price.
* `neighbor_reference_price` (357–358) and `seam_tranche_prices` (420–421): `baseload = neighbor_gas_price(...)`;
  `baseload *= neighbor_heat_rate(...)` — so the price is **`(HH + gas_basis) × HR × shape`**.
* `neighbor_heat_rate` (204–211): `hr_by_year[year]` when tabulated → `_HR_GAS_ELASTIC` (no SPP keys) → the flat
  `marginal_heat_rate`. In 2023–2025 the tabulated value wins; the flat value prices every **forecast** year.

SPP-20's flat values were built as `mean_LMP / HH` (block comments: 27.90/2.54 = 10.98 …), so they reproduce their
own anchor's annual mean with the error SPP-33 §4 measured (MISO +14.4/+6.5/+13.5 %, AECI −10.7/−23.9/+10.5 %,
ERCOT −43.0/−14.9/+25.6 %). Corrected construction, RT, `K = 1.000000` in every cell (all SPP seams carry
`load_shape_exponent = 1.0`):

| Block | anchor mean RT $/MWh 2023 / 2024 / 2025 | HH + basis $/MMBtu | **`hr_by_year`** | **flat `marginal_heat_rate`** (mean of the three) | registered (bare-HH) | SPP-33 combined |
|---|---|---|---|---|---|---|
| `MISO_West` | 28.7524 / 27.4275 / 40.1926 | 2.84 / 2.49 / 3.82 | **10.12 / 11.02 / 10.52** | **10.55** | 11.24 | 9.82 / 10.55 / 9.90 = equal-weight mean of the two legs ✔ |
| `MISO_South` | 27.0420 / 25.1159 / 35.4525 | 2.84 / 2.49 / 3.82 | **9.52 / 10.09 / 9.28** | **9.63** | 11.24 | (10.09 = mean of the combined row ✔) |
| `AECI` (proxy) | 23.4732 / 23.3135 / 27.1112 | 2.28 / 1.93 / 3.26 | **10.30 / 12.08 / 8.32** | **10.23** | 9.19 | 10.23 ✔ |
| `ERCOT` | 48.3568 / 26.8250 / 32.4906 | 2.04 / 1.69 / 3.02 | **23.70 / 15.87 / 10.76** | **16.78** | 13.51 | 16.78 ✔ |

RT is armed (SPP-33 §3's recommendation: the seam prices against an RT-scored LP and every incumbent `hr_by_year`
table is RT-anchored); DA is reported in `data/raw/reference/spp_seam_hr_by_year.csv`. Every value is a MEASURED
price-formation input with a forward analogue (rules 13 / 21: `hr_by_year` regenerates for a forward year from
HH + basis + the neighbour's own realized price; nothing reads SPP's flow or price residual).

### 1(c) ERCOT: 820 MW rating sum → 835 MW measured clip (rule 14)

The registered 820 MW is the CDR rating sum (Oklaunion 220 + Monticello 600) that `ERCOT_DC_TIE_ZONE_MAP["SWPP"]`
carries on ERCOT's side; SPP's own SOM prints 720. The measured EIA-930 SWPP→ERCO series clips at a hard **±835 MW
in all three years** (max 835 / min −832 / −833 / −818), and SPP's own 1-minute tie meter (`ERCOTE + ERCOTN`,
SPP-14 file) agrees with it at corr **+1.0000**, mean difference 0.1 MW (SPP-33 §8) — so 835 is the ties'
scheduled operating envelope on two independent meters, not an artifact of one. At 820 an armed seam would refuse
flows the meter recorded in **547 / 128 / 21 h** (6.3 / 1.5 / 0.3 %). Rule 14: keep the accurate value.

**Misalignment, stated:** 835 is a metered scheduled MAXIMUM, not a published rating; the 15 MW gap to the CDR sum
(and the 115 MW gap to the MMU's 720) is recorded, not explained. ERCOT's own registry row stays at 820 (rule 25 —
another ISO's row; a rating on ERCOT's side of the tie is ERCOT's to adjudicate). The SPP block carries 835.

---

## 2. Discovered blocker — the priced seam has no topology on SPP, and the naive one is a corridor bypass

**Fact 1 (HEAD).** `IMPORT_ZONE` (`spec.py:35`) and `IMPORT_NODE_LINKS` (`spec.py:899`) have no `"SPP"` entry —
SPP-20 §3 / plan §7 G7: "no import node". Consequences, traced:

* `get_interchange_spec` (`spec.py:2402`): `import_zone = IMPORT_ZONE.get(iso, "")` → `""` → returns an EMPTY
  `InterchangeSpec`; `build_interchange_fleet` returns `[]`.
* `extend_with_import_node` (`import_nodes.py:730`): `IMPORT_ZONE.get("SPP") is None` → returns the topology unchanged.
* `run_calibration.py:2655`: `load_demand(..., include_interchange=not priced_interchange)` → the served
  `spp_net_interchange` schedule is DROPPED (`demand.py:1024`).
* `apply_reference_price_seam_injections` → `inject_reference_price_mc` finds no `_refimp_`/`_refexp_` rows →
  returns `False` quietly.

So `keeper-3 recipe + --priced-interchange --reference-price-interface` at HEAD is **SPP with zero interchange** —
not the arm the charter describes, and not a screen of anything. (Also note: `--priced-interchange` alone, without
`--reference-price-interface`, would select the static `IMPORT_TRANCHES` ladder, of which SPP has none — the same
empty fleet. Both flags are required for the reference seam on any non-default ISO.)

**Fact 2 (the naive repair is wrong).** Adding `IMPORT_ZONE["SPP"] = "SPP_external"` with links to BOTH zones
gives the LP a zero-load bus joined to SPP-North and SPP-South. The bus's energy balance lets flow enter from one
zone and leave into the other with NO seam band dispatched — a free path around the internal N↔S link whose
3,400 MW TTC is the ONLY structural constraint SPP has (SPP-53, the hub spread's whole mechanism). This is
precisely the defect `split_miso_south_external_node` (`miso.py:431`) documents and removes for MISO's RDT ("the
LP can wheel energy South→external→Midwest through the external zone's energy balance without touching any priced
seam band — a free 3,000 MW bypass"). A bidirectional `EXTERNAL_SIMULTANEOUS_LIMITS` cap cannot stop it: the cap
bounds the SIGNED sum of link flows, and a wheel nets to zero.

**The structurally right topology (designed, routed — NOT built by this lane).** Two external buses, each linked
to ONE internal zone, hosting the seams that physically land on that side:

| External bus | links to | hosts | link TTC (= sum of hosted seam limits; non-binding by construction — the per-seam band sums bind) |
|---|---|---|---|
| `SPP_external_North` (= `IMPORT_ZONE["SPP"]`) | SPP-North | `AECI` (5,000), `MISO_West` (3,550) | 8,550 |
| `SPP_external_South` | SPP-South | `MISO_South` (2,450), `ERCOT` (835) | 3,285 |

The MISO seam split 3,550 / 2,450 (sum 6,000, the MMU's ">6,000 MW AC interties") follows the measured |flow| share
of SPP's own MISO-member tie columns in `TieFlows_Sep2025.csv` — West/North members 59.1 %, Entergy + Cleco 40.9 %
(673 h, the only per-member measurement in the tree; stated as a one-month reconciliation, rule 14). Machinery
needed: `extend_with_import_node` appending a second registry-declared external zone (generic, default-empty), and
`build_interchange_fleet` reading a registry-declared per-seam host zone into `build_reference_price_node`'s existing
`zone_overrides` (the MISO-South precedent). Both are `import_nodes.py` / generic-`spec.py` edits with a solve-path
footprint — a mechanism-shaped change outside "SPP blocks ONLY", so it is routed (FINDING §R) rather than made here.
Given §3.5's verdict no solve would have used it in this lane anyway, and landing dead topology would be a
re-armable path (rule 26 in spirit).

---

## 3. Zero-LP phase 0 (rule 29(0))

All numbers from `scratchpad/spp51_phase0.py` + `spp51_premise.py` (listings carried in FINDING-spp-51 §A) over
the committed keeper-3 bundle and committed measured inputs. EIA-930 SWPP→DIBA series put on the model's 8760
standard clock (hour-ending prevailing local → hour-beginning → fixed CST, Feb 29 dropped); `mw > 0` = SPP
exports (SPP-33 §1, confirmed on SPP's own meter §8).

### 3.1 Footprint — the screen year, named on measured seam MWh (never on a residual)

| year | MISO net / gross TWh | AECI net / gross | ERCO net / gross | hours | **gross through the three seams** |
|---|---|---|---|---|---|
| 2023 | −0.824 / 3.973 | +2.356 / 2.945 | +1.234 / 2.279 | 8,662 | 9.197 |
| **2024** | **−2.376 / 4.546** | +2.621 / 3.340 | +0.516 / 1.820 | 8,398 | **9.706 ← screen year** |
| 2025 | −0.784 / 3.799 | +1.984 / 2.995 | +0.552 / 1.300 | 7,822 | 8.095 |

2024 is also where the MISO seam's own footprint is largest (SPP-33 §7: −2.37 TWh, the Winter Storm Heather hour).
The C3a residual is largest in 2023 (+14.1 %) — which is exactly why 2023 is NOT the screen year.

### 3.2 Offer-array delta — served vs priced, per neighbour per year

Served (keeper-3): the seam is a demand adder with NO offer. Priced: 8 import + 8 export bands per seam at
`(HH+basis) × HR[y] × (load ± midpoint)/mean`, hurdle ±2. Annual means of the band arrays (§1(b) values):

| seam | year | import band 1 → 8 $/MWh | export band 1 → 8 | keeper-3 border-zone P1 mean | mean spread (SPP − nb) | hours import-econ / export-econ / hold |
|---|---|---|---|---|---|---|
| MISO_West | 2023 | 28.83 → 30.05 | 28.65 → 27.43 | 26.93 (N) | −1.90 | 1,454 / 4,418 / 2,888 |
| MISO_South | 2023 | 27.09 → 27.89 | 26.98 → 26.19 | 27.71 (S) | +0.62 | 3,133 / 2,442 / 3,185 |
| AECI | 2023 | 23.71 → 26.88 | 23.26 → 20.09 | 26.93 (N) | +3.22 | 5,221 / 422 / 3,117 |
| ERCOT | 2023 | 48.40 → 49.09 | 48.30 → 47.61 | 27.71 (S) | −20.69 | 3 / 8,684 / 73 |
| MISO_West | 2024 | 27.52 → 28.68 | 27.36 → 26.20 | 25.59 | −1.93 | 1,630 / 5,320 / 1,810 |
| MISO_South | 2024 | 25.18 → 25.91 | 25.07 → 24.34 | 25.80 | +0.62 | 2,615 / 3,711 / 2,434 |
| AECI | 2024 | 23.54 → 26.62 | 23.09 → 20.00 | 25.59 | +2.06 | 3,373 / 2,268 / 3,119 |
| ERCOT | 2024 | 26.85 → 27.22 | 26.79 → 26.42 | 25.80 | −1.05 | 2,275 / 4,877 / 1,608 |
| MISO_West | 2025 | 40.30 → 41.95 | 40.07 → 38.42 | 28.87 | −11.43 | 389 / 7,855 / 516 |
| MISO_South | 2025 | 35.52 → 36.52 | 35.38 → 34.38 | 29.99 | −5.53 | 1,114 / 6,490 / 1,156 |
| AECI | 2025 | 27.37 → 30.84 | 26.88 → 23.40 | 28.87 | +1.50 | 3,521 / 2,535 / 2,704 |
| ERCOT | 2025 | 32.53 → 32.95 | 32.46 → 32.04 | 29.99 | −2.54 | 2,131 / 5,257 / 1,372 |

Ex-ante (keeper-3 prices held fixed — an upper bound on the seam's appetite, since the LP's own price would move
toward the neighbour's): the economic clearing would net **+9.5 / +12.2 / +26.1 TWh of export to MISO-West**
against a measured **−0.82 / −2.38 / −0.78** (SPP is a net IMPORTER from MISO), and **−19.1 / −5.6 / −5.8 TWh of
IMPORT from "AECI"** against a measured **+2.36 / +2.62 / +1.98 export** — the AECI proxy anchor is SPP's own
realized hub, so keeper-3's price residual over that hub (+3.2 / +2.1 / +1.5 $/MWh) becomes seam flow by
construction (SPP-33 §3's warning, measured). Sign agreement with the measured direction over all hours:
MISO_West 0.40 / 0.42 / 0.48, MISO_South 0.41 / 0.45 / 0.50, AECI 0.21 / 0.35 / 0.41, ERCOT 0.67 / 0.53 / 0.57.
This is NOT the gate (the LP re-prices SPP), but it is the direction the arithmetic points.

### 3.3 The SWPP duration curves (SPP-33 §7, carried)

MISO: balanced two-way, median −70 / −205 / −37 MW, export share 0.446 / 0.351 / 0.468, p01→p99 ≈ 2,950–3,680 MW
wide. AECI: firm export, 0.811 / 0.808 / 0.719, median +284 / +333 / +248. ERCOT: export 0.634 / 0.610 / 0.648,
hard rail ±835. A priced arm that reverses any sign fails gate (i) whatever it does to a residual.

### 3.4 PRE-SOLVE GATE P0-b — declared here, before it was computed

The mechanism's identity is **flow follows spread**: import when `P_SPP > P_nb + hurdle`, export when
`P_SPP < P_nb − hurdle`. A structurally faithful mechanism must hold in the MEASURED record, independent of any
LP. Test: MEASURED SPP hub (`actual_lmp_hourly_zonal_SPP.parquet`: SPPNORTH_HUB for the North-side seams,
SPPSOUTH_HUB for the South-side) minus the MEASURED anchor (§1(a)), hurdle ±2, sign vs the EIA-930 DIBA direction.
**Gate:** ≥ 0.55 sign agreement over non-hold hours on the MISO seam (both legs), RT, in the screen year. AECI is
degenerate by construction (its anchor IS the SPP hub) and is not scored; ERCOT is reported. If the gate fails,
**the screen is not spent** (rule 29(0): an arm with a computable pre-solve gate does not reach a solve until that
gate passes) and the arm is KILLED at phase 0. Precedent: the same statistic from MISO's side,
`corr(measured SPP seam flow, MISO DA − SPP North DA) = +0.041 / −0.020 / +0.050`
(`PRECOMMIT-miso233-spp-hourly-seam-2026-09-07.md` §104–113, "the spread is UNINFORMATIVE about this seam's hourly
flow"), which is why MISO's own keeper prices this seam as a measured hourly-anchored OFFSET ladder, not a
spread-clearing economic seam.

### 3.5 P0-b outcome

| run | seam | year | hours | mean spread $/MWh | hold share | **sign agree, non-hold** | sign agree, all | corr(spread, import) | measured export share |
|---|---|---|---|---|---|---|---|---|---|
| rt | MISO_West | 2023 | 8,647 | −6.23 | 0.097 | **0.485** | 0.438 | −0.018 | 0.446 |
| rt | MISO_South | 2023 | 8,647 | −2.65 | 0.109 | **0.501** | 0.446 | +0.014 | 0.446 |
| rt | ERCOT | 2023 | 8,220 | −22.47 | 0.097 | 0.604 | 0.546 | +0.217 | 0.668 |
| rt | MISO_West | **2024** | 8,382 | −8.35 | 0.100 | **0.436** | 0.392 | −0.009 | 0.350 |
| rt | MISO_South | **2024** | 8,382 | +2.59 | 0.106 | **0.482** | 0.431 | +0.075 | 0.350 |
| rt | ERCOT | 2024 | 8,028 | +0.03 | 0.101 | 0.561 | 0.505 | +0.098 | 0.635 |
| rt | MISO_West | 2025 | 7,810 | −13.41 | 0.072 | **0.479** | 0.444 | 0.000 | 0.469 |
| rt | MISO_South | 2025 | 7,810 | −8.03 | 0.093 | **0.484** | 0.439 | −0.022 | 0.469 |
| rt | ERCOT | 2025 | 7,447 | −4.78 | 0.082 | 0.606 | 0.556 | +0.115 | 0.681 |
| da | MISO_West | 2024 | 8,388 | −6.01 | 0.096 | **0.423** | 0.382 | −0.009 | 0.351 |
| da | MISO_South | 2024 | 8,388 | +5.32 | 0.104 | **0.485** | 0.435 | +0.102 | 0.351 |
| da | ERCOT | 2024 | 8,034 | +2.46 | 0.112 | 0.510 | 0.453 | +0.107 | 0.635 |

**P0-b FAILS**: MISO_West 0.436 and MISO_South 0.482 in the screen year (RT), and no MISO cell in any year or run
reaches 0.55 — the measured SPP↔MISO flow is not a function of the measured hourly spread (corr ≈ 0). The real
seam is scheduled / JOA / loop flow, as MISO found from its own side. ERCOT clears weakly (0.56–0.61, corr
+0.10…+0.22) — the DC ties do respond to the spread — but the switch is all-or-nothing (`include_interchange=False`
drops the whole served schedule), so an ERCOT-only priced seam with MISO/AECI served is a different mechanism
(a partial served schedule), routed.

**THE ARM IS KILLED AT PHASE 0. NO LP IS SPENT.** This is a structural verdict, not a residual one: the gate read
no C3a/C3b, and it would have been the same verdict had keeper-3's prices been perfect.

---

## 4. The STOP gate that WOULD have applied to the screen (pre-registered; not reached)

`keeper-3 recipe + --priced-interchange --reference-price-interface --year 2024` (once §2's topology existed):

* **(i)** per seam, modelled interchange duration curve has the measured sign in ≥ 55 % of hours AND annual net
  within an order of magnitude of the EIA-930 DIBA (MISO −2.376, AECI +2.621, ERCO +0.516 TWh in 2024);
* **(ii)** slope of modelled seam import (MW) on `(P_SPP_border − P_nb)` > 0, per seam — ex ante by construction,
  checked on the solved bundle;
* **(iii)** no non-target load-bearing criterion flips PASS → FAIL vs keeper-3 (C1 2023-classes, C2, C6, C8);
  the gate never reads C3a/C3b/C3c, which are reported beside it.

A kill on any of (i)–(iii) is the result; the full span is never spent. Screen bundle dir would have been
`results/calibration/_spp51_screen_2024` (gitignored scratch family; rule 31 retained on disk, never `rm`'d).

---

## 5. G-DRIFT — `git diff 623184f3 HEAD` over the rule-29(b) file set

13 files, 538 insertions / 1 deletion; every hunk classified:

| file | hunk | class |
|---|---|---|
| `scripts/run_calibration.py`, `scripts/run_calibration_full.py`, `pipeline/{__init__,commitment,year}.py`, `runner.py`, `data/floor_mechanisms.py`, `config/constants.py` (SPP_GAS_BRIDGE_*), `config/solve_surface_declared.py` (two SPP_GAS_BRIDGE rows) | SPP-44 `spp_gas_commitment_bridge` — a `ScenarioConfig` flag default `False`, absent from keeper-3's recipe; `build_spp_gas_bridge_p1_prep` returns `None` when off | **INERT** (default-off flag absent from the recipe) |
| `config/scenarios.py` | the SPP-44 field + its cache-key registration at `"False"`; `ercot_zonal_spread_ep_referenced` field + registration | **INERT** (registered at default; ERCOT branch) |
| `data/fuel/basis/ercot.py`, `data/fuel/__init__.py`, `data/fuel/basis/__init__.py` | ercot-255 EP reference, gated `ercot_zonal_gas_basis and iso == "ERCOT"` | **INERT** (another ISO's branch) |

**All hunks INERT ⇒ form 4 valid: keeper-3 is the control.** (Moot for the LP since none is spent; recorded because
§3.2 differenced against keeper-3's committed prices.)

---

## 6. What this lane lands, and the files

* `src/market_sim/model/interchange/spec.py` — the `"SPP"` list of `INTERFACE_NEIGHBORS` ONLY: `MISO` → `MISO_West`
  + `MISO_South` (per-zone anchors, `hr_by_year`, HH+basis flat values, 3,550 / 2,450), `AECI` (`hr_by_year`, 10.23),
  `ERCOT` (`hr_by_year`, 16.78, **835**). Every block stays DEFAULT-OFF (`REFERENCE_PRICE_DEFAULT_ISOS` and
  `PRICED_INTERCHANGE_DEFAULT_ISOS` untouched; no `IMPORT_ZONE` entry) — a byte-identical no-op for keeper-3 and
  every other ISO. `spec.py` is OUT of the solve-surface phase-1 modules (`solve_surface.py` docstring) and no
  `ScenarioConfig` field moves, so **no cache key of any ISO moves, by construction** (tests re-run). MISO's SPP
  seam constants (its `INTERFACE_NEIGHBORS["MISO"]` `SPP` block, `MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_SPP_*`) are not
  touched — the diff hunks are confined to the SPP list (rule 25).
* `scripts/data/derive_neighbor_hr_by_year.py` — the per-ISO anchor map + explicit failure (§1(a)).
* `tests/iso/spp/test_spp_priced_seams.py` — registry ↔ producer identity, HH+basis identity, precedence, 835,
  name uniqueness, other ISOs' anchors unchanged, unregistered ISO fails loud.
* `docs/codebase-site/data/mechanism-matrix/SPP.js` — `priced_interchange` and `reference_price_interface` cells
  `U → R`, evidence = this doc + FINDING-spp-51 §3.5 (phase-0 kill on the measured premise; no solve).
* `docs/handoffs/FINDING-spp-51-2026-09-07.md`, plan §5 row → LANDED, `docs/calibration-log/spp.md` entry.
* NOT touched: `keepers/SPP.json`, offer bands, `ScenarioConfig`, `neighbor_price.py`, any other ISO's row,
  `derive_neighbor_hr_elasticity.py` (its own copy of the global map is R3's, forward-only — reported).

## 7. Rules that bite

| rule | how |
|---|---|
| 1 `[R-STRUCT]` | the kill is on the mechanism's own identity in the measured record, not on a residual; the naive topology was refused because it would have destroyed real structure (the corridor) |
| 12 `[R-PARALLEL]` | no solve launched; this container is isolated (4 CPU / 15 GB), no other lane's process is visible here |
| 13 / 14 / 21 / 23 | every armed value is a measured price-formation input regenerable forward; 835 over 820 is rule 14 with the misalignment stated; `hr_by_year` are MEASURED, ledgered as such |
| 19 `[R-ONE-MECH]` | the served schedule and the priced seam are alternatives (`include_interchange`), never stacked |
| 24 / 25 | no new tunable; nothing crosses an ISO boundary — SPP's anchors read SPP's own committed files, MISO's rows untouched |
| 27 `[R-PUSH]` | `spec.py` (2,937 lines) edited locally with Edit, pushed by `git push`, blob fetched back and hash-compared |
| 28 `[R-MECH-MATRIX]` | both cells stamped in the SPP shard in this session, rejection included |
| 29 `[R-SCREEN]` | screen year named on footprint (§3.1) before any residual was read; pre-solve gate (§3.4) declared before computed; kill ⇒ no LP |
| 31 `[R-RETAIN]` | nothing solved, nothing deleted |
