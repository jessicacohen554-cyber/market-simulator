# PRECOMMIT — SPP-55: VRL-based scarcity as an in-LP Contingency Reserve demand curve (SPP's published curve, one family, `energy_reserve_coopt`)

**Lane** SPP-55 · **Model** Fable (`claude-fable-5-1`) · **Date** 2026-09-07 ·
**Branch** `claude/spp-55-vrl-scarcity-jgqidm` (stem `claude/spp-55-vrl-scarcity-d7xm`; base `origin/main` `9708d69e`) ·
**Data profile** `spp` · **Charter** plan §5 row SPP-55 (issued r#10), §5.7 item 5; FINDING-spp-price-family §1.3 / §6 (the
measured target); FINDING-spp-44 §2 (rule 19) / §6 R-17 (the curve prices scarcity, it does not start plants); FINDING-spp-12
§6 (Exhibit 4-1); cards P4 (one curve, not SPP-56's co-opt) and P5 (no seed at registration; design against keeper-3).

**Written before any solve, and — as §6 records — no solve is spent by this lane.** Everything below is a zero-LP
measurement on committed artifacts and SPP's own postings, a declaration, or a gate with its thresholds. Nothing is revised
after a result; every miss is reported at full magnitude in the FINDING.

---

## 0. The pin, the control, G-DRIFT

```
9708d69e   origin/main at branch cut (PRECOMMIT time); origin/main advanced to 5376ccef during the session (rebased LAST, §7)
623184f3   keeper-3 git.sha  (results/calibration/spp43_screened_B, 2026-09-07-spp-3-screened-input)
```

| precondition | check | result |
|---|---|---|
| SPP-43 landed — keeper-3 is the control | `keepers/SPP.json` → `2026-09-07-spp-3-screened-input`; bundle `spp43_screened_B` + `hourly/` committed | **yes** |
| SPP-44 landed — its 28c every-shard edit merged | `spp_gas_commitment_bridge` row + 7 cells at `19e1c867` / `7e9b34d9` (PR #5535) | **yes** |
| rule 12 — other solves on this desk | none in this container (`ps`: no `run_calibration` process; 15 GB free) | no contention; no solve is spent anyway (§6) |
| RTBM MCP files (manifest row 9, "SPP-56 input only") | `data/raw/spp-or-mcp/RTBM_MCP_{2023,2024,2025}.csv.zip` on disk, 630,720 / 632,448 / 630,720 rows | READ for the footprint and the gate, never priced on (card P4) |

### 0.1 G-DRIFT (rule 29(b)) — keeper-3 `623184f3` → `9708d69e`

`git diff --stat 623184f3 HEAD -- src/market_sim scripts/run_calibration.py scripts/run_calibration_full.py scripts/lib
data/raw/_validation-source data/raw/reference` → 13 files, 538 insertions.

| # | files | hunk | verdict for SPP | reason |
|---|---|---|---|---|
| 1 | `config/scenarios.py` (+68 of 129), `config/constants.py`, `config/solve_surface_declared.py`, `data/floor_mechanisms.py`, `pipeline/commitment.py`, `pipeline/__init__.py`, `pipeline/year.py`, `runner.py`, both runners' CLI | **SPP-44** `spp_gas_commitment_bridge` (field default-off, registered at its `"False"` drop value; constants declared at their live hash) | **INERT** | absent from keeper-3's recipe (`run_config.json`: `spp_gas_commitment_bridge=False`); the P1 prep hook returns `None` unless armed; FINDING-spp-44 §5: seven keeper keys byte-identical |
| 2 | `config/scenarios.py` (+61), `data/fuel/basis/ercot.py` (+118), `data/fuel/__init__.py`, `data/fuel/basis/__init__.py` | `ercot_zonal_spread_ep_referenced` (ERCOT-only implementation, default `False`) | **INERT** | another ISO's branch; the field is absent from SPP's recipe (FINDING-spp-price-family §2 addendum classified the same hunk INERT) |

**All hunks INERT ⇒ form 4 is valid: keeper-3's committed bundle is the control** and no control solve is earned. (No arm
solve is spent either — §6.)

---

## 1. Rule 19 enumeration — what prices scarcity or reserves in SPP today: nothing

Keeper-3's `run_config.json`: `scarcity_pricing_enabled=False`, `scarcity_price_overlay=False`, `energy_reserve_coopt=False`,
`ercot_rtordpa_overlay=False`, no reliability-floor limb registered for SPP, `spp_gas_commitment_bridge=False`, every offer band
1.0. Keeper-3's `system_<year>.parquet`: `reserve_price` is 0.0 in all 8,760 hours of every year; `slack` is 0 in 2023 and 2024
and 89.3 MWh in one 2025 hour (h6520, SPP-South behind the bound N→S link — FINDING-spp-43); `dump` 0. The ORDC post-solve
overlay is `·` for SPP (rule 19: one scarcity mechanism per ISO, and this lane's is in the LP).

**The family REPLACES nothing and STACKS on nothing.** The one existing energy-shortage price object — the load slack at the
registered `voll` ($2,000/MWh, owner ruling P10) — is left as it is: SPP's $50,000/MW Global Power Balance VRL is the SCED
relaxation cap on that same energy-balance constraint (Protocols §4.1.4 / Exhibit 4-1), not a second object, and `voll` is
`iso_configs.py`'s — MUST-NOT-TOUCH for this lane.

---

## 2. THE OBJECT — SPP's published Contingency Reserve Demand Curve, one BAA-wide family, MISO-RBDC form

### 2.1 Correction to the charter's expected object, from SPP's own protocols

The charter expected "the $250/MW spinning VRL as the first step and the $50,000/MW power-balance VRL as the ceiling". SPP's
Market Protocols (v119, transcription in `data/raw/spp-planning/transcriptions/`) say the object that prices a **contingency
reserve capacity shortage into the energy LMP** is neither VRL. It is the **Contingency Reserve Demand Curve**:

| element | SPP's own text | value | cite |
|---|---|---|---|
| scarcity price | "the product of the applicable Contingency Reserve Scarcity Factor … and the sum of the Safety-Net Energy Offer Cap and the Contingency Reserve Offer Cap" | factor × ($1,000 + $100) | §4.1.5(1)(a), printed p. 74; caps §8.2.5 pp. 356–357 (FINDING-spp-12 §6) |
| factor 0.25 | shortage ≤ ½ of "the SPP Reserve Sharing Group Contingency Reserve requirement above the BAACRM" | **$275/MW** | §4.1.5.2(1)(a), p. 87 |
| factor 0.5 | ½ < shortage ≤ the whole of it | **$550/MW** | §4.1.5.2(1)(b) |
| factor 1.0 | beyond | **$1,100/MW** | §4.1.5.2(1)(c); ASOM 2024 p. 98 / ASOM 2025 p. 94: "three steps with a maximum price of $1,100/MW" |
| LMP impact | "The Energy LMP is increased by the Operating Reserve shortage price of $1100/MW if the cost of serving an incremental MW of Energy worsens the Operating Reserve capacity shortage condition (i.e. Operating Reserve Demand Curve is included in the LMP calculation)" | the LP's balance-row dual, by construction | §4.1.5(2)(a), pp. 78–79; Exhibit 4-2 scenario C, p. 83 |
| **$250/MW Spinning Reserve VRL** | "limits the costs of redispatch need to meet the Spinning Reserve requirement by capping the Spinning Reserve Shadow Price" | a CAP on the spin **sub**-constraint (the ≥ ½ spinning share), not a demand-curve step | §4.1.4 p. 69; §4.1.4.1(5) p. 73 |
| **$50,000/MW Global Power Balance VRL** | the energy-balance relaxation cap | the LP's `voll` slack, already present | §4.1.4, Exhibit 4-1 pp. 70–71 |

**Measured corroboration (RTBM MCPs, reserve zone 1 = every zone, §3):** in every 2023–2025 interval where the Supplemental
MCP is at or above $275, its value is **exactly 275, 550 or 1,100** (90-30-20 / 65-33-14 / 43-23-40 intervals; five "other"
values in 2024–2025 are the additive Reserve-Zone curve of §4.1.5(4)); the annual maximum Supp MCP is **1,100.0** in all three
years; the Spin MCP maximum is **1,344.5 / 1,200 / 1,350 = the curve plus the $250 spin VRL** stacked on top, exactly as the
cascade in §4.1.5(2) says. The published curve is the object; the VRLs sit beside it.

### 2.2 The family

One `ReserveFamily` **`spp_contingency_reserve`** (`model/reserves/spec.py::_spp_design`, reached through the existing
`get_reserve_design` dispatcher under the existing shared gate **`energy_reserve_coopt`** — the MISO template exactly: the base
RBDC-form family, on which a later SPP-56 co-opt would add its product families and deliverability bound):

- **Basis:** the SPP Balancing Authority Area. `zone_mask` = both model zones. Protocols §4.1.5(1) applies the curves "on an
  SPP Balancing Authority Area basis and/or a Reserve Zone basis"; the per-Reserve-Zone curves never separated from the BAA
  curve in the window — all five reserve zones carry **identical** MCPs in all 315,648 posted 2023–2025 intervals (§3), and
  the posted `SPP` row is a zero placeholder. One BAA-wide family is the measured structure.
- **Products pooled:** Spinning + Supplemental draw on the whole reserve-eligible thermal headroom (`_reserve_eligible`,
  `RESERVE_FUEL_TYPES`); storage not eligible (SPP-56). The ≥ ½ spinning share (RSG Operating Process definitions, p. 5) and
  its $250 VRL are a sub-constraint this family does not carry — stated, and SPP-56's.
- **Demand curve:** `spp_contingency_reserve_demand_steps(req_max)` → penalties **(275, 550, 1,100)**, widths
  **(req/12, req/12, 10·req/12)** — "the RSG requirement above the BAACRM" read as the §4.2 scaling margin
  0.2·MSSC = req·(1.2−1)/1.2, so each shallow band is half of it. The reading is corroborated by the step distribution:
  the ASOM's median shortage ("about 95 % of the requirement" cleared, ASOM 2024 p. 99 → ~75 MW) lands in the $275 band,
  which carries 40–64 % of the short intervals; the alternative reading (the ~3 % of the RSG requirement other members
  carry, ~40 MW) would put that median at $1,100. Widths are static and span the requirement's annual max (the NYISO /
  MISO feasibility convention).
- **Rule 4:** the price enters as a demand-curve step in the reserve balance row; the LMP moves only through the row's dual.

### 2.3 The requirement — SPP's own rule, regenerating from the fleet each year (rule 13)

SPP Reserve Sharing Group Operating Process – East, **0820EXT00002 v4.0** (effective 2026-06-01; the v2.0 rule of
2022-06-01 through the window; fetched 2026-09-07 from `https://www.spp.org/documents/63838/`, extracted to the session's
scratch — **not landed**, the document is a 380 KB PDF outside this lane's file ownership; page cites from its own footer):

| rule | text | model construction |
|---|---|---|
| §4.1 (p. 10) MSSC | "the largest potential Balancing Contingency Event due to a single contingency on an hourly basis … events totaling **600 MW or greater** of nameplate capacity … A. Loss of the MW output of a **single generating unit** or multiple intermittent resources using a common interconnection point" | `MSSC_t = max_g nameplate_unit(g) × availability[g,t]` over reserve-eligible rows whose plant's largest single EIA-860 generator ≥ 600 MW (per-plant CAMPD rows carry the STATION; the rule names the UNIT, so the largest generator at the plant is read from the active EIA-860 vintage — Wolf Creek 1 1,296.3 / Iatan 2 999.0 / La Cygne 1 873.0 / Cooper 801.0 / Nebraska City 2 738.0 / Jeffrey 720.0) |
| §4.1.2 (p. 11) | "Units not on outage are considered online for the purpose of determining potential MSSCs" | the availability scaling (an outaged unit is not the MSSC) |
| §4.2 (p. 11) | "Minimum Hourly Contingency Reserve … equal to the greater of hourly potential MSSC times a scaling factor or potential SMCE times a separate scaling factor … minimum scaling factor … **1.2 for the MSSC** and 1.0 for the SMCE" | `SPP_RSG_CR_SCALING_FACTOR = 1.2`; the SMCE (common-fuel / RAS multi-unit event) is not modelled |
| §4.3 (p. 12) | each BA's requirement is "a prorated amount of the total SPP Reserve Sharing Group Minimum Hourly Contingency Reserve Requirement" by its previous-year system-peak-responsibility ratio | `SPP_BA_CR_REQUIREMENT_RATIO`, MEASURED (§2.4) — posted to members, not published |
| definitions (p. 5) | "Contingency Reserve is the sum of Operating Reserve - Spinning and Operating Reserve - Supplemental. At least half of the Contingency Reserve shall be Operating Reserve - Spinning" | pooled family (the spin share is SPP-56's) |

`req_t = 0.964 × 1.2 × MSSC_t`. Forward story: a retired Wolf Creek drops the requirement to Iatan 2's 999 MW; a new ≥ 600 MW
unit raises it; the availability overlay moves it hour by hour. No year key, no measured outcome.

### 2.4 The one measured share, and the rule-14 alignment of the whole construction

`SPP_BA_CR_REQUIREMENT_RATIO = 0.964`, identified ONCE before any solve as the pooled 2023–2024 median of the hourly-mean
SPP-BAA cleared Spinning + Supplemental reserve (portal `operating-reserves` RTBM-OR 5-minute files, 2023 + 2024 annual
archives, 103,087 + 104,789 intervals; instrument `docs/handoffs/spp55/extract_or.py`; the ~95 MB archives are NOT landed —
a scratch read, re-fetchable by the same URL grammar SPP-14 documented) over 1.2 × Wolf Creek 1's nameplate:

| year | cleared CR, hourly-mean median | ÷ (1.2 × 1,296.3) |
|---|---|---|
| 2023 | 1,514 MW (p1 1,431 · p99 1,706) | 0.973 |
| 2024 | 1,484 MW (p1 1,403 · p99 1,651) | 0.954 |
| pooled | | **0.964** |

The construction evaluated on keeper-3's own fleet (`docs/handoffs/spp55/req_align.py`, `fleet_only` rebuild):

| year | model req median (max) | measured median | model ÷ measured p5 / median / p95 | months the model reads > 10 % low |
|---|---|---|---|---|
| 2023 | 1,500 (1,500) | 1,514 | 0.940 / **0.983** / 1.040 | none (Oct 1,440 vs 1,477, −2.5 %) |
| 2024 | 1,425 (1,500) | 1,484 | 0.510 / **0.961** / 1.035 | Apr 756 / May 1,200 / Aug 1,320 / Oct 915 vs ~1,480 |
| 2025 | 1,500 (1,500) | 1,372–1,516 (six posted samples) | — | Oct 756 / Nov 1,050 |

**The declared misalignment (rule 14, documented, not tuned around):** in the MSSC unit's refuelling months the model's
availability is a MONTHLY derate (`NUCLEAR_MONTHLY_CF_BY_YEAR["SPP"]`, 0.79 / 0.66 / …), not an outage state, so the model's
requirement falls to a blend (756–1,320 MW) while SPP's posted requirement stays ~1,480 (its MSSC passes to a different
≥ 1,250 MW event — a wind cluster at a common interconnection or an SMCE — that this construction does not carry). Median
alignment is 0.96–0.98; the misalignment is confined to 2–4 months a year and reads LOW, i.e. it can only make the family
bind LESS — it cannot manufacture the verdict in §6.

---

## 3. THE FOOTPRINT — measured, by year, from the RTBM MCPs (reserve zone 1; every zone identical; hourly on the fixed 8,760 local calendar)

`docs/handoffs/spp55/footprint.csv`. "CR-short" = Supplemental MCP ≥ $275 (the curve's first step). Cross with the RT hourly
LMP the scorer uses (`actual_lmp_hourly_SPP.parquet`, which reproduces the C3c counts 42 / 59 / 68 exactly).

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| CR-short 5-minute intervals | **140** | **117** | **109** |
| … at $1,100 (deep) | 20 | 14 | 40 |
| shortage EVENTS (consecutive intervals) | 68 (34 one-interval; longest 6) | 45 (24 one-interval; longest 9) | 37 (14 one-interval; longest 8) |
| hours with ≥ 1 short interval | 66 | 43 | 40 |
| hours with ≥ 6 short intervals (half the hour) | 1 | 5 | 5 |
| **hours whose hourly-MEAN Supp MCP ≥ $275** (the hour-long shortage an hourly LP can represent) | **4** | **3** | **7** |
| hours with Spin MCP ≥ $250 (the charter's measure) | 70 | 51 | 49 |
| … of which spin-only (Supp < 275: the $250 VRL, not the curve) | 4 | 8 | 9 |
| RT LMP > $200 hours (C3c) | 42 | 59 | 68 |
| **C3c hours that are ALSO CR-short (any interval)** | **1** | **0** | **0** |
| RT LMP in the CR-short hours: median / mean | $32.0 / $47.2 | $32.2 / $47.6 | $36.1 / $44.1 |

Two things the footprint establishes before any solve:

1. **SPP's contingency-reserve shortage is a 5-minute object.** 140 / 117 / 109 intervals ≈ 12 / 10 / 9 hour-equivalents a
   year, in 68 / 45 / 37 events of median length one interval (ASOM 2024 p. 99: "about 10 operating reserve scarcity
   intervals per month"; the scarcity "can be caused by a lack of capacity or a lack of ramp" — the MMU cannot tell which).
   At the hour, the mean price clears the first step in 4 / 3 / 7 hours a year.
2. **The C3c tail is a different object from reserve shortage.** 1 / 0 / 0 of the 42 / 59 / 68 > $200 hours carry any
   CR-short interval; the CR-short hours themselves price at a median $32–36. Complementary attribution of the tail (zonal
   parquet): DA > $200 in 0 / 14 / 0 of those hours (RT-only events); both hubs > $200 in 32 / 31 / 50 (system-wide RT
   events, not one-hub congestion), with |N−S| a median $37–64 in the tail against $5–7 otherwise. The tail is real-time,
   intra-hour price formation (ramp scarcity, VRL relaxations, the 5-minute SCED) — consistent with FINDING-spp-price-family
   §1.3's "spikes at ordinary load at 79–93× gas". Reported here because the charter routed C3c to this lane; it is NOT a
   gate, and no criterion is read by the gate (§5).

**Screen year, named ex ante on the mechanism's own largest hourly-representable footprint: 2025** (7 hours whose hourly mean
clears the first step; 40 deep intervals — the most of the three years). Not the year with the biggest C3c residual (2024's
59 vs 3 h is the worst C3c ratio; 2023's +14.1 % is the worst C3a).

---

## 4. Rule 17 — the row's driver, window, forward story

- **Driver:** SPP's own tariff scarcity pricing (Protocols §4.1.5 Contingency Reserve Demand Curve) on SPP's own RSG
  requirement rule (0820EXT00002 §4.1–4.3).
- **Window:** the family may price only in hours where the reserve-eligible thermal headroom is below the requirement —
  in the measured record, the 4 / 3 / 7 hours a year whose mean Supp MCP clears $275 (up to the 66 / 43 / 40 hours with any
  short interval). It has no calendar window and no declared season; binding in an hour where SPP posted no shortage is a
  false positive the gate counts against it.
- **Forward story:** the three prices are tariff constants ($1,000 + $100 caps × published factors), the 1.2 scaling and
  600 MW screen are RSG constants, the share is an RSG parameter re-set each June from peak responsibility, and the MSSC
  regenerates from the fleet and its availability every hour of every year.

---

## 5. THE STOP GATE — structural, declared before the result; never C3c, never C3a

Graded against keeper-3's committed bundle (form 4), on the screen year, from the arm's `hourly/reserve_family_2025.parquet`
(`dual`, `requirement_mw`, `held_mw`, `shortfall_mw`) and `system_2025.parquet`:

| leg | quantity | STOP if |
|---|---|---|
| **(i) window agreement** | (a) share of the measured hourly-mean-≥ $275 hours in which the family's `dual > 0`; (b) share of all OTHER hours in which `dual > 0` | (a) < 0.50 **or** (b) > 0.01 (88 hours) |
| **(ii) the identity the design asserts** | in every hour with `shortfall_mw > 0`: `dual` ∈ {275, 550, 1,100} (±$1) and the system-price rise over keeper-3 in that hour equals the dual (±$1) where a thermal unit is marginal | any hour violating either |
| **(iii) R-17 guard — the curve prices scarcity, it does not start plants** | ΔE by class vs keeper-3; the family's held MW is headroom, so `ΔE(ST_GAS) + ΔE(CC_REGULAR)` must be ≤ 0.05 TWh and every class's ΔE ≤ 0.10 TWh outside the binding hours | a gas-start footprint beyond what the requirement's MW implies |
| **(iv) non-target load-bearing** | C1 class bands, C2, C4 r vs keeper-3 | any PASS → FAIL flip |

Reported beside the gate, never gated: hours > $200 vs 42 / 59 / 68, the C3c row, the load-weighted price, unserved / dump.

### 5.1 The pre-solve half of leg (i) — computable from the committed bundle (rule 29 step 0)

The reserve balance row `Σ_z R[z,t] + Σ_k shortfall_k[t] ≥ req_t` with `R[z,t] ≤ cap_z,t − P_z,t` can carry a positive dual
only in an hour where the reserve-eligible headroom `Σ_g∈elig (pmax_g·avail_g,t) − Σ_g∈elig P_g,t` is below `req_t`; where it
is above, `R` absorbs the requirement out of existing slack at zero cost and the keeper's dispatch remains optimal
unchanged. So leg (i) is decided by keeper-3's own sidecars **before any LP** — `docs/handoffs/spp55/headroom.py`
(`fleet_only` rebuild for `pmax × availability`, `class_hourly_<year>.parquet` for the dispatch of the same classes,
`_spp_design` for `req_t`): **if the headroom is above the requirement in every measured shortage hour, leg (i)(a) reads
0 and the arm is killed without a solve** (rule 29 step 0: "an arm that has a computable pre-solve gate does not reach a
solve until that gate passes").

---

## 6. Pre-solve result — the gate is decided at zero LP, and it KILLS the arm

`docs/handoffs/spp55/presolve_gate.csv` / `headroom_summary.csv`:

| | 2023 | 2024 | **2025 (screen year)** |
|---|---|---|---|
| requirement, median (max) MW | 1,500 (1,500) | 1,425 (1,500) | 1,500 (1,500) |
| keeper-3 eligible headroom: min / p1 / median MW | 2,884 / 6,668 / 18,181 | 1,169 / 6,323 / 18,046 | 2,399 / 6,983 / 17,581 |
| headroom ÷ requirement: min / p1 / median | 1.92 / 4.45 / 12.3 | 0.89 / 4.65 / 13.6 | 1.60 / 4.70 / 12.2 |
| hours with headroom < requirement (the ONLY hours the row can bind) | **0** | **1** (h5727, shortfall 151 MW) | **0** |
| … of which in the measured hourly-mean-≥ $275 window | 0 of 4 | 0 of 3 | **0 of 7** |
| … of which in ANY measured CR-short hour | 0 of 66 | 0 of 43 | 0 of 40 |
| … of which in a C3c (> $200) hour | 0 | 0 | 0 |
| min headroom inside the measured window (hourly-mean / any-interval) | 4,540 / 2,884 | 7,616 / 2,503 | 8,051 / 6,480 |

**Leg (i)(a) = 0.00 in every year (0 / 7 on the screen year); the arm cannot bind in a single measured shortage hour.** Leg
(i)(b) is 0 / 8,760 in 2023 and 2025 and 1 / 8,760 in 2024 — an hour SPP posted no shortage in, i.e. the one hour the row
could bind is a false positive. The mechanism is **INERT on keeper-3's dispatch in every measured shortage hour of the window**,
and the verdict does not depend on the 0.964 share, the monthly derate misalignment (§2.4, which reads LOW) or the width
reading (§2.2): with headroom 3.4–17× the requirement inside the measured window, no admissible requirement level reaches it.

**Therefore no screen solve is spent** (rule 29 step 0; the charter's step (2) is superseded by the owner's own rule that a
failed pre-solve gate does not reach a solve). Legs (ii)–(iv) are consequently NOT graded on a bundle; leg (ii)'s identity is
proven at toy scale in `tests/unit/model/test_reserve_coopt.py::TestSppContingencyReserveLP` (slack → $0; a 50 MW shortage →
dual $275 and the LMP up by exactly $275; a 400 MW shortage → $1,100). A verification solve on 2025 would cost ~10 minutes of
wall clock on this box and is offered to the desk in the FINDING; it is not run here because its outcome — a `reserve_family`
sidecar with `dual = 0` in every hour of 2025 — is what the arithmetic above already states.

**Structural reading, for the record (FINDING §3 carries it in full):** SPP's contingency-reserve shortages are 1–9-interval
ramp/capacity events inside the 5-minute RTBM; an hourly perfect-foresight LP over a two-zone SPP with ~36 GW of reserve-
eligible available capacity holds 6–18 GW of headroom in 99 % of hours and never falls to 1.5 GW in a posted shortage hour —
the miso-38 gate-4 lesson (without a deliverability / ramp bound the LP always clears the requirement out of slow-unit
headroom) repeated on SPP's own data. Making this family LIVE is a deliverability question (a 10-minute ramp bound on the
held MW, the `miso_reserve_pergen` construction) — SPP-56's object under card P4, not a scarcity-curve question.

---

## 7. What lands regardless (rule 28; the registered SPP entry)

- `model/reserves/spec.py` (the `reserve_config` facade): the SPP constants block (six published / one measured value, each
  cited), `spp_contingency_reserve_demand_steps`, `_spp_largest_unit_nameplate`, `_spp_design`; `get_reserve_design` routes
  `iso == "SPP"`. **No new `ScenarioConfig` field** — the existing `energy_reserve_coopt` gate reaches it (the MISO template),
  so rule 28(c) owes no matrix row and no foreign-shard line; `check_cache_key_registration` 0 new fields, `solve_surface_register
  --diff` 0 moved; every keeper key unmoved by construction (nothing in any key changed).
- `pipeline/kwargs.py::_log_reserve_coopt`: an SPP log line.
- Tests: `tests/unit/config/test_reserve_config.py::TestSppContingencyReserveDesign` (5), `tests/unit/model/test_reserve_coopt.py::
  TestSppContingencyReserveLP` (1), `tests/regression/test_config_model_layering.py` surface list (+2 names).
- SPP shard cell `energy_reserve_coopt` U → **I** with this evidence (`reserve_family_dual_sidecar`, `ordc_scarcity_overlay`,
  `dynamic_reserve_requirements` annotated, not moved: no sidecar was produced, no overlay tested, no measured-hourly
  requirement armed); §5.7 item 5; plan §5 / §9 rows; `docs/calibration-log/spp.md` spp-8.
- Nothing registered; `keepers/SPP.json` untouched; no bundle written, so rules 29(c) / 31 have nothing to keep or delete.
- Rebase onto `origin/main` LAST, then `check_mechanism_matrix` re-run (the SPP-44 28c collision the charter names is moot:
  no shard line is added).

## 8. DOF ledger (rule 21) — zero tuned

| parameter | value | identification |
|---|---|---|
| Safety-Net Energy Offer Cap | $1,000/MWh | PUBLISHED — Protocols §8.2.5 |
| Contingency Reserve Offer Cap | $100/MW | PUBLISHED — Protocols §8.2.5 |
| Contingency Reserve Scarcity Factors | 0.25 / 0.5 / 1.0 at ½·margin / margin | PUBLISHED — Protocols §4.1.5.2(1) |
| RSG MSSC scaling factor | 1.2 | PUBLISHED — 0820EXT00002 §4.2 |
| potential-MSSC nameplate screen | 600 MW | PUBLISHED — 0820EXT00002 §4.1 |
| SPP BAA Contingency Reserve Requirement Ratio | 0.964 | MEASURED — SPP's posted cleared reserves ÷ (1.2 × Wolf Creek 1 nameplate), 2023–2024 pooled median (§2.4); identified once, before any result |
| the MSSC | fleet-derived, hourly | RULE — largest single reserve-eligible unit × availability |

No value in this table was selected against a residual, a gate or a criterion; the family's verdict (§6) was computed from
keeper-3's committed sidecars with these values fixed.
