# PRECOMMIT — neiso-109: the rule-29 screen of the repaired NEISO delivered-gas series

**Session** neiso-109 · **Date** 2026-09-16 · **Pushed BEFORE any solve.**
**Keeper under test** `2026-09-09-neiso-108-fuelvintage` (bundle `results/calibration/neiso108_fuelvintage`,
years 2023–2025) **+ its folded touchpoint run** `2026-09-09-neiso-108-fuelvintage-touchpoints`
(bundle `neiso108_fuelvintage_tp`, years 2020–2022). **Neither is changed by this session.**
**Evidence for the repair:** `docs/FINDING-neiso109-the-agt-series-is-contaminated-2026-09-16.md`.

**REGISTRY YEAR UNION, enumerated BEFORE anything is pruned (rule 35 `[R-PROMOTE]` (b)):**
`{2020, 2021, 2022}` ∪ `{2023, 2024, 2025}` = **SIX YEARS, 2020–2025**. Read from
`frontend/data/backcast/registry/2026-09-09-neiso-108-fuelvintage{,-touchpoints}.json`. A promotion
must cover all six (rules 34(c) / 35(c)).

---

## 1. WHAT IS BEING SCREENED, AND WHAT IS NOT

The arm is the keeper's frozen recipe replayed byte-faithfully with **the repaired
`data/raw/gas-prices/algonquin_citygate_daily.csv` as the only difference**.

**This is a rule 14 `[R-ACCURATE]` INPUT repair, not a mechanism.** Committed in advance:

* **ZERO `ScenarioConfig` fields move.** No flag armed, none disarmed.
* **No offer-curve multiplier is touched.** The keeper already carries an
  `authorized_price_tuning` declaration — the neiso-106 fossil offer-level scalar **0.95470** on
  12 markup bands — and it is **CARRIED FORWARD UNCHANGED**: this session neither re-sizes nor
  re-sweeps it and introduces **no new price-tuning channel of its own**. `PREREG-neiso106` §6's
  "third and LAST sizing" pre-commitment is untouched by this lane.
* **The DOF ledger is carried byte-identical** — the keeper's 5 free parameters, unchanged. No
  free parameter is added.
* **No mechanism cell moves** in `docs/codebase-site/data/mechanism-matrix/NEISO.js` (rule 28
  `[R-MECH-MATRIX]` (b)): there is no `ScenarioConfig` field to attach a verdict to.
* **Rule 25 `[R-ISO-SCOPE]`:** every changed byte is in NEISO's own AGT file. The shared
  `gas_basis_by_iso_month.csv` is **not touched**.

If this session finds itself adding a field, it has stopped doing what it set out to do.

## 2. PHASE 0 — ZERO LP, AND IT ANSWERS ALL THREE §3 QUESTIONS

`scripts/probes/_neiso109_gas_repair_footprint.py`, over all six registry years.

### (a) NEISO's repair is ONE-STEP. NYISO's worst failure mode has no analogue here. ✔

NEISO's monthly AGT basis is an **independent measured source** — `gas_basis_by_iso_month.csv`, the
ISO-NE MA gas index, read by `load_winter_gas_basis` — and is **not** recomputed from these dailies
the way NYISO's was. The daily leg is additively mean-preserved to it in **every** branch
(`hubs.iso_hub_daily_gas_prices`), so each month's mean is `hh_m + b_m` whatever the AGT prints say.

**Asserted, not assumed** — max |Δ monthly mean| over every month of every year:

```
2020 8.9e-16 · 2021 1.8e-15 · 2022 0.0 · 2023 1.8e-15 · 2024 1.8e-15 · 2025 3.6e-15   ($/MMBtu)
```

*(The probe first read 7.3e-2 in 2020 and 2024 — **its own** bug, not the model's: it labelled a
leap year from a real calendar while the model runs a fixed 365-day year in every year, rule 8
`[R-8760]`. Recorded because a phase 0 that quietly fixes its own instrument is not a measurement.)*

**Consequence, and it is the load-bearing one:** `gas_offer_margin_anchor = 4.0763` is a **frozen
scalar** (`constants.GAS_OFFER_MARGIN_ANCHOR_BY_ISO`), derived as the 2023–25 mean of exactly this
series. The annual mean does not move, so **the anchor does not need re-deriving** and rule 23
`[R-FROZEN-DERIVE]` is satisfied without a second step. Confirmed live at HEAD on the repaired
input: `gas offer net-revenue margin: 372 tranches compressed at anchor 4.0763 $/MMBtu`.

### (b) The NYISO annual-reach anchor finding does NOT reproduce. ✔

`gas_offer_margin_zonal_anchor = False` on this keeper (NYISO's is `True`), and NEISO's anchor is
applied as `markup_hr × (anchor − fuel[h])` — **hourly**, against a frozen constant. Both halves of
NYISO's channel are therefore absent: the anchor is not re-derived (a), and it has no annual reach
into untouched hours. **Predicted and pre-registered: hours where delivered gas does not move see
no price change at all.** G-1 tests it.

### (c) The cross-ISO Transco coupling is ELIMINATED by the repair — not merely quantified. ✔

The `<2 AGT prints` fallback borrows its within-month shape from the measured Transco Z6 NY basis —
the series NYISO just repaired. Positive-basis months taking that branch:

```
BEFORE  {2023: [Dec], 2024: [Dec], 2025: [Jan]}        AFTER  {}   (every year)
```

Every positive-basis month in every registered year now carries ≥2 real AGT prints, so **the
Transco branch does not fire anywhere in 2020–2025.** The 2025-01 case is the striking one: the old
series borrowed New York's polar-vortex shape and put **$44.79/MMBtu on 2025-01-17/18 in Boston**;
the measured AGT prints say **$21.18**. The old series over-amplified by more than 2×, which is
precisely what the code comment on that branch warns can happen.

**Stated because it changes what the control is:** the keeper solved 2026-09-09, before the NYISO
repair landed (2026-09-14), so its committed numbers carry the *pre-repair* Transco borrow in those
three months. The arm carries neither. The measured `arm − control` therefore contains both effects
in those months, and §5's paired control is what separates them from HEAD drift.

**The global AGT price ceiling is UNCHANGED at 38.2200 $/MMBtu**, so no cross-year coupling runs
through that channel either.

### (d) THE SCREEN YEAR IS **2025**, and it is named here before the screen runs

| year | hours moved | % of yr | mean abs Δ | max +Δ | min −Δ | **sum abs Δ ($/MMBtu·h)** |
|---|---:|---:|---:|---:|---:|---:|
| 2020 | 2,160 | 24.7 % | 0.925 | +4.30 | −2.20 | 1,998.8 |
| 2021 | 3,624 | 41.4 % | 0.965 | +4.93 | −4.03 | 3,498.5 |
| 2022 | 2,208 | 25.2 % | 1.440 | +13.33 | −6.22 | 3,179.1 |
| 2023 | 4,344 | 49.6 % | 1.802 | +4.45 | −15.69 | 7,829.7 |
| 2024 | 2,904 | 33.2 % | 1.496 | +8.64 | −9.07 | 4,345.8 |
| **2025** | **2,160** | **24.7 %** | **4.029** | **+9.38** | **−23.61** | **8,703.6** |

**2025 by footprint, 1.11× the next largest.** Chosen on the mechanism's own measured size — rule
29 (1). **No residual, no criterion and no price was consulted in making this choice**, and none is
consulted anywhere below.

The ten 2025 days that move most (model calendar): 01-17 `44.79 → 21.18`, 01-18 `44.79 → 21.89`,
01-19 `34.16 → 18.91`, 01-25 `10.12 → 19.50`, 02-26/27/28 `14.64 → ~5.50`, 01-26/27/28 `~10.15 → ~18.7`.
**The repair is TWO-SIGNED** — it lowers the borrowed NY peak and raises the true cold-snap shoulder.

### (e) THE PRE-SOLVE Δmc, measured on the keeper's own no-LP fleet reconstruction

| | value |
|---|---|
| generator rows changed | **460 of 867** (the gas fleet) |
| hours changed | **2,160 of 8,760** — identical to the delivered-array footprint |
| Δmc range | **−457.17 … +181.74 $/MWh** |
| widest class | CC_REGULAR (−457.17 … +181.74); CT_PEAKER (−276.92 … +110.09); ST_GAS (−243.15 … +105.47) |

### (f) OIL-PARITY CROSSINGS — NEISO's own measured parity, NOT NYISO's $24.85

NEISO 2025 parity: mean **14.697**, range 10.055–18.387 $/MMBtu (2023: 18.752; 2024: 13.679).

| year | hours gas > parity, OLD | NEW | Δ | max gas OLD → NEW |
|---|---:|---:|---:|---|
| 2020 | 0 | 0 | 0 | 4.52 → 8.78 |
| 2021 | 0 | 0 | 0 | 13.20 → 13.43 |
| 2022 | 48 | 48 | 0 | 27.01 → 24.41 (the Elliott hole is unfillable — FINDING §6) |
| **2023** | **96** | **0** | **−96** | **30.13 → 15.77** |
| 2024 | 96 | 24 | −72 | 26.69 → 20.94 |
| **2025** | **504** | **792** | **+288** | **44.79 → 21.89** |

**The 2023 row is the sharpest single consequence of the repair.** The model burned oil in February
2023 because it believed Boston gas reached **$30.13/MMBtu**, above the $18.75 parity. Boston gas
peaked at **$15.77**; the $28–30 print was **Transco Z6 NY's**, harvested by the unanchored extremum
pattern (FINDING §4) — and it is the very print the `hubs` docstring cites as the mechanism working.
On the repaired input 2023 has **no hour above parity at all**.

## 3. WHAT I EXPECT, PRE-REGISTERED SO IT CANNOT BE CONSTRUCTED AFTERWARDS

1. **Oil burn moves in BOTH directions, and the direction is set by the parity table, not by a
   residual.** NEISO carries `dual_fuel_switching` + `dual_fuel_oil_reattribution` armed, so:
   * **2025 oil RISES** — +288 parity-crossing hours, a 57 % increase.
   * **2023 oil FALLS to whatever the non-dual-fuel fleet burns** — 96 → **0** hours above parity.
     This is the falsifiable one: if 2023 oil does *not* fall, the dual-fuel channel is not what
     was driving it and my reading of the repair is wrong.
   * **2024 oil FALLS** — 96 → 24 hours. 2020/2021/2022 unchanged at 0/0/48.
2. **The extreme 2025 price tail FALLS.** Peak delivered gas drops 44.79 → 21.89, so the very
   highest January price hours should come DOWN even as more hours cross parity. **The repair is
   not "more winter gas" — in 2023 and 2024 it is materially LESS**, because what it removes is New
   York's pipeline constraint standing in for Boston's.
3. **C3a (2025) direction: I DO NOT KNOW, and I am not going to pretend to.** The repair is
   two-signed and the annual mean is invariant by construction, so there is no arithmetic that
   predicts the annual price statistic. **Whatever it does is not a gate** (§4).
4. **A WORSE FIT IS NOT GROUNDS TO REVERT** (rule 14, verbatim: keep the accurate input, find the
   real root cause, never bury the error back inside an inaccurate input). **AND A BETTER NUMBER IS
   NOT GROUNDS TO PROMOTE.** A screen may kill an arm; it may never promote one. Only the owner
   promotes.
5. **A NULL OR MIXED HEADLINE IS A SUCCESS.** NYISO's equivalent repair moved no determination and
   flipped no band verdict in either direction; what it bought was fidelity. The same shape of
   outcome here is the expected one and will be reported as a success.

## 4. THE GATES — STRUCTURAL, STOP-ONLY, PRE-REGISTERED

**They may kill the arm; they may never promote it. None is gated on a residual. Criteria are NOT
gates in either direction and are REPORTED ONLY.**

| gate | test | PASS condition |
|---|---|---|
| **G-1 FOOTPRINT CONFINEMENT** | written over the **delivered gas array in $/MMBtu**, so it is decidable with **zero LP** | (i) max &#124;Δ monthly mean&#124; < 1e-9 in every month of every year; (ii) hours move only in months whose AGT prints changed; (iii) **in the LP, zone-hours outside the moved hours show zero price change** — the direct test of §2(b). |
| **G-2 DIRECTION** | two-signed, matching the input | load-weighted price **falls** over 2025-01-17…19 (gas −23.61 … −15.24) and **rises** over 2025-01-25…28 (gas +8.29 … +9.38). A move of the wrong sign in either window is a STOP. |
| **G-3 ORDER OF MAGNITUDE** | bounded by the measured pre-solve Δmc, §2(e) | every zone-hour price change lies within **[−457.17, +181.74] $/MWh**, and the 2025 load-weighted annual change within the same band. Outside it the LP is amplifying, not repricing. |
| **G-4 NO STRUCTURAL BREAK** | the gate most likely to fire | **slack = 0.000000 and dump = 0.000000**, zero hours of either, in BOTH legs. This is what catches an LP pushed into shedding load by winter gas. |
| **G-5 IDENTITY** | plant-class energy | no class's annual energy moves > 10 % **without a Δmc to explain it**. **Oil is expected to move, UP in 2025** (§3.1); it passes only if the rise sits inside the touched months AND tracks the parity crossings. The Δmc half cannot be mechanized and is adjudicated in writing. |

**G-1 (i) and (ii) already PASS, pre-solve**, on the phase-0 measurement: 3.6e-15 worst, and moved
months ⊆ print-changed months in all six years (2020 [1,12] ⊆ [1,4,9,10,11,12]; 2021 [1,3,12] ⊆
[1,3,8,12]; 2022 [11] ⊆ [8,11]; 2023 [1,2,6,7,11,12] ⊆ [1,2,4,5,6,7,8,9,10,11,12]; 2024 [1,2,3,12] ⊆
[1,2,3,7,9,12]; 2025 [1,2,7] ⊆ [1,2,7,8]). G-1 (iii) is settled by the screen.

## 5. G-DRIFT — IT DOES **NOT** CLEAR, SO A PAIRED CONTROL IS EARNED

Rule 29(b) form 4 (the keeper's committed bundle as the control) requires classifying every changed
hunk on the backcast path as INERT. **I am not able to, and I am not going to assert it.**

* **The keeper's recorded shas do not resolve.** `git_sha 52a2f519` and
  `basis_sha cfc66722814990232e22f98f9ac2c63744ffef98` are both `fatal: bad object` — the keeper
  solved `dirty: true` on branch `claude/neiso-fuelvintage-1`, since auto-deleted. The prescribed
  `git diff <keeper sha> HEAD` **cannot be run at all.**
* Anchoring instead on the commit that registered the keeper (`0e016a77`, 2026-09-12 — itself
  *later* than the 2026-09-09 solve, so this **understates** the drift), the diff over
  `src/market_sim scripts/run_calibration*.py scripts/lib` is **57 files, +6,555 / −154 lines**,
  including `data/fleet/campd_bins.py`, `data/outages.py`, `data/zone_assignment.py`,
  `data/offer_curves.py` and `pipeline/backcast_config.py` — all squarely on the backcast path, with
  9 added lines naming NEISO.
* **What DOES hold, reported because it is real evidence and not because it settles the question:**
  the keeper's solve-surface fingerprint **`9d35c270c69e9eee` (197 rows) reproduces
  byte-identically at HEAD**, and `moved_rows("NEISO") = {}`. That covers the seven
  `SURFACE_MODULES` registries — not the code above.

**Therefore: the screen shard solves BOTH LEGS on 2025 at ONE pinned SHA** — control (committed CSV)
and arm (repaired CSV). Rule 29(b) permits exactly this: a LIVE hunk earns a control solve *for the
years the screen needs*.

**And it settles form 4 empirically, which is stronger than the audit.** If the control leg
reproduces the keeper's committed 2025 numbers, HEAD drift is measured at zero for NEISO and form 4
is valid for the span — so the full span then needs the **arm only**. If it does not, the span
carries a paired control too, and the drift is a finding in its own right.

## 6. THE PLAN

| step | what | LP |
|---|---|---|
| 0 | phase 0 above, the repair, the FINDING | **none** — done, in this parent |
| 1 | **SCREEN**: one shard, 2025, **two legs** (control + arm), gates G-1…G-5 | 2 × one NEISO year |
| 2 | ~~**only if the screen clears**~~ **SUPERSEDED — the owner directed "Run all years" (2026-09-16), so the span was launched in parallel with the screen**: one shard, **`--years 2020 2021 2022 2023 2024 2025`**, ONE bundle (rules 16 / 32(b) / 34(c)) | 6 years, arm |
| 3 | parent composes, scores, registers, and **asks the owner the promotion question** | none |

> **AMENDED 2026-09-16 by owner instruction — see `docs/ADDENDUM-neiso109-run-all-years-2026-09-16.md`.**
> The screen's *gating* role is waived; **G-1 … G-5 still bind on the span as STOP gates**, the
> pre-registered expectations in §3 are unedited, and nothing here promotes anything. The screen
> shard was NOT cancelled: its control leg is the only control this lane has and the only instrument
> that can settle §5's open G-DRIFT question.

**Rule 32 `[R-SHARD]` (a): this parent runs ZERO LP.** Rule 34 `[R-SHARD-PROMOTABLE]` (a): every
shard pushes its bundle to its own branch, including `dispatch/<year>_P1.parquet`, via a
`.gitignore` negation and a **plain `git add`** — never `git add -f`. Rule 31 `[R-RETAIN]`: nothing
is deleted until the owner has ruled on promotion; `.gitignore`, not `rm`, discharges rule 29(c).

**The six-year span will not fit 20 minutes and is not meant to** — rule 32(b)'s ceiling is a
STOP-and-report rule for a shard producing no artifact, not a cap on an authorized single
invocation, and fanning a registrable run out per year is banned by the same clause. The span
shard's budget is stated explicitly in its prompt.
