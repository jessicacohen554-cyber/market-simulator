# PREREG miso-122 — the hybrid-cogen scope gate on `chp_power_only_heat_rates`

Session miso-122, 2026-08-03, branch `claude/miso-c7-coal-mechanism-6d828k`, off
`origin/main` at `9aca82b`. **Written and committed BEFORE any probe is run and
before any derive line is changed.**

## 1. The cell picked, and why

**Queue head, taken as written.** `docs/mechanism-testing-matrix.md` §5.4 ends:

> **The live head of the MISO queue is now the 55088 Dearborn hybrid-cogen
> scope gate (item 4 above, named not chartered).**

Every other MISO queue item is adjudicated or blocked, and the session prompt
re-states the same closures: item 0 / 0b's whole regulated-PRB self-commitment
family is spent (`R`/`R`/`I` at miso-111/112/113, re-confirmed at miso-114),
items 1 and 2 are data-blocked, item 3 is `R` ex ante (miso-105), item 4 is
`K` and closed across six ISOs (miso-117), item 5 is `I` (miso-121), item 6 is
`I` (miso-108/109/110). The Dearborn item is the only named, un-adjudicated,
non-data-blocked head left.

**Matrix cell: `measured_chp_heat_rates` × MISO, currently `K`.** This session
does **not** propose a new mechanism and adds no `ScenarioConfig` field — it
proposes a **scope correction inside the existing mechanism's derive**, which
is the rule 19 `[R-ONE-MECH]`-correct shape: fix the mechanism that already
owns this phenomenon rather than stack a second one beside it.

**Admissibility basis: rule 14 `[R-ACCURATE]` ONLY.** miso-118 §5 states the
charter conditions and this pre-registration adopts all three: (a) it is a
different question from miso-118's, so it gets its own decision rule; (b) it
changes the derive's **scope gate**, which needs its own pre-registration and
its own admissibility argument; (c) direction is established, materiality is
not. **The correction must never be justified by what it does to a residual**
(rules 1 / 13 / 23). If the corrected input makes the backcast worse, the
corrected input still ships and the worse fit becomes a root-cause item (rule
14's explicit instruction).

## 2. The defect, as measured by miso-118 and not re-litigated here

`scripts/data/derive_chp_power_only_heat_rates.py` computes the power-only
heat rate as eGRID's CHP allocation undone:

    heat_rate = (PLHTIAN + CHPCHTI) / PLNGENAN

which charges **all** of a plant's fuel to its power. Its own SCOPE section
says that is right for a **topping cycle** — the steam is a free co-product of
exhaust, so no fuel is avoided by making it — and wrong wherever fuel is fired
**directly** to steam. Its only guard is eGRID's plant-level `thermal_share`
against a 0.50 unfired ceiling.

Plant **55088 Dearborn Industrial Generation** is a **hybrid**: a topping
CC + CT train *plus* three direct-fired `Other boiler` units that report heat
input and **zero gross load**. eGRID's plant-level allocation cannot see the
split (`thermal_share` = 0.2396, comfortably under the ceiling, so the gate
passes it); CEMS can, at unit grain. miso-118 §5 measured the consequence —
13–17 % of the plant's CEMS fuel is host process fuel sitting inside the
topping rate charged to its `CC_CHP` (350 MW) and `CT_CHP` (165 MW) tranches,
**+20.0 / +18.0 / +13.2 % too dear** in 2023 / 2024 / 2025.

Those numbers are *inputs* to this session, published and committed; they are
not re-derived as a result.

## 3. The proposed correction (fixed here, before it is measured)

A **third scope gate**, on the same footing as the two the derive already
carries and defined entirely on measured quantities:

    dark_share  = CEMS annual heat input of units at the plant that report
                  heatInput > 0 and grossLoad == 0 over the WHOLE vintage year
                  ------------------------------------------------------------
                  CEMS annual heat input of ALL units at the plant

    heat_rate   = (PLHTIAN + CHPCHTI) * (1 - dark_share) / PLNGENAN

Four properties are pre-registered as design commitments, not as findings:

1. **It is a SHARE, not a subtraction of MMBtu.** Scale-free: it needs CEMS's
   fuel *composition* to be representative of the plant, never CEMS's *level*
   to equal eGRID's. Mixing a CEMS numerator with an eGRID denominator would
   smuggle a re-basing in alongside the correction; a share cannot.
2. **The denominator is unchanged.** `PLNGENAN`, the same net-generation
   denominator the incumbent rate already divides by, exactly as the derive's
   header insists ("no gross-to-net factor is involved, and that is the
   point").
3. **Same vintage on both sides.** `dark_share` is measured from the CEMS year
   equal to `--vintage` — the year the eGRID workbook covers — so no vintage is
   mixed. The derive already reads CEMS at `args.vintage` for its validation
   column.
4. **Zero free parameters, and a strict no-op where the phenomenon is absent.**
   A plant with no dark-fuel units has `dark_share = 0.0` and its rate is
   byte-identical. There is **no threshold** on `dark_share` — a threshold
   would be a magic number (rule 5 `[R-NO-MAGIC]`) and the measured share is
   already the right continuous quantity.

**Forward-regeneration (rule 13 `[R-MEASURED]`):** each eGRID vintage ships
`PLHTIAN`/`CHPCHTI`/`PLNGENAN` and each CAMPD year ships unit-grain
`heatInput`/`grossLoad`, so the corrected rate regenerates for a forward year
from the same published pipeline and responds to a plant re-configuring its
boilers. It is an INPUT (a physical property of the machine), never a measured
outcome fed back to close a residual.

**Rule 23 `[R-FROZEN-DERIVE]`:** this is a **logic** change on measured
grounds, which miso-118 §5(b) states rule 23 permits, and the re-derivation
commit cites *that* — not a residual, not a source-data refresh.

## 4. Phase 0 — the no-LP measurement, with its kills fixed in advance

Probe `scripts/probes/_miso122_hybrid_cogen_scope.py`, reading only committed
artifacts (`data/raw/campd-unit-level/`, `data/raw/fleet-egrid/`, the five
committed `chp_power_only_heat_rates_<ISO>.csv`, the keeper bundle
`results/calibration/miso117_ctheatrate_B`).

| id | kill / gate | bar | if it fires |
|---|---|---|---|
| **K1** | **the dark units are boilers, not mis-reporting turbines** | ≥ 90 % of dark fuel at any corrected plant sits in a CAMPD `unitType` that is not a combustion/combined-cycle turbine | correction VOID at that plant — "zero gross load" is then a reporting gap, and a reporting gap must not be subtracted |
| **K2** | **persistence** | the plant's `dark_share` is non-zero in all three of 2023/2024/2025 and the max/min ratio ≤ 2.0 | VOID — a one-year spike is an artifact, not a machine |
| **K3** | **two-meter reconciliation** | `cems_vs_egrid_total` ∈ **[0.90, 1.10]** at every corrected plant (the miso-118 pre-registered two-meter agreement band, reused rather than reinvented) | that plant is flagged out, not corrected — CEMS's composition cannot be attributed to eGRID's total |
| **K4** | **corrected rate stays physical** | the corrected rate is ≥ the plant's `heat_rate_credited` and inside `_HR_BAND` | flag out via the derive's existing band machinery (no new branch) |
| **K5** | **no-op fidelity** | re-deriving all five ISOs changes **only** rows whose measured `dark_share` > 0; every other row byte-identical | STOP — the change has a side effect and is not a scope gate |
| **K6** | **coverage honesty** | report, do not hide, the `ok` rows CEMS does not cover (`cems_vs_egrid_total` NaN): they take `dark_share = 0` and are therefore **unchanged**, which is the status quo, not a claim that they have no dark fuel | reported as a stated limitation |

**Generality sweep (not a kill).** The dark-fuel share is measured for every
`ok`-flagged plant in **all five** artifact ISOs, because the derive is
ISO-agnostic code and I must know what the change does everywhere before
shipping it. Rule 25 `[R-ISO-SCOPE]` is respected by construction: each ISO's
rows are corrected by **that ISO's own** measured share, and no parameter
crosses a boundary. Non-MISO verdict cells are **not** stamped by this session
— a re-derived artifact is an input change, not a tested mechanism, and the
other five lanes adjudicate their own price effect.

## 5. Phase 1 — the A/B, and what it is allowed to conclude

Two arms, `replay_keeper.py` off the MISO keeper
`2026-08-03-miso-117b-ct-heat` (bundle `results/calibration/miso117_ctheatrate_B`),
**one invocation per arm covering `--years 2023 2024 2025`**, arms sequential
(rules 12 / 16 / 22; the miso-119/121 form):

* **arm A control** — same HEAD, zero delta, the **pre-change** artifact.
* **arm B treatment** — identical config, the **re-derived** artifact.

**The delta is an input FILE, not a config field, and that is stated up front
so nobody reads the identical `run_config.json`s as a wiring failure.** The
arms are distinguished by the sha256 of
`data/raw/_processed-legacy/chp_power_only_heat_rates_MISO.csv`, recorded for
both arms in the finding. The mechanism-fired check (the miso-113 hazard) is
therefore **not** a log line — it is:

* **W1** the loaded fleet's capacity-weighted `CC_CHP`/`CT_CHP` heat rate for
  plant 55088 differs between the two artifacts by the pre-measured
  −13…−20 %, verified by `load_fleet_from_csv` **before** either arm is
  launched, and
* **W2** a non-zero `mc` delta on 55088's tranches in arm B's own solved
  output.

If W1 fails, no arm is launched.

### Pre-registered decision rule

Let `|Δλ|max` be the maximum zonal absolute LMP change between arms in any
year, and `ΔE` the plant's own annual energy change.

| outcome | condition | verdict |
|---|---|---|
| **LIVE** | `|Δλ|max` ≥ 0.10 $/MWh in ≥ 2 of 3 years | the correction is price-material; score the C-series and D-series and take the promotion question to the owner |
| **DISPATCH-LIVE / PRICE-INERT** | `ΔE` ≠ 0 but `|Δλ|max` < 0.10 in ≥ 2 of 3 years | the correction lands on rule 14 grounds; the **mechanism cell is not re-stamped `I`** (it is `K` and stays `K`) — the *scope gate* is recorded as price-inert, which is a different object |
| **FULLY INERT** | `ΔE` = 0 and `|Δλ|max` = 0 in all three years | same disposition; the input is still corrected |

The **0.10 $/MWh** bar is the same K3 price bar miso-119 and miso-121
pre-registered, reused for comparability across the three consecutive MISO
adjudications.

**The correction ships under every branch.** No branch of this table can
reject the corrected input — rule 14 forbids reverting to a known-wrong value
because the accurate one did not help. What the branches decide is only
whether a **keeper promotion** is proposed and whether the C/D series is
re-scored.

**Carried DO-NOT-REDO, applied here (miso-119 + miso-121):** `max |Δoffer|`
is an **upper** bound on the price effect and must never be read as a lower
bound; the predictive ex-ante statistic is the **marginal share of binding
hours**, never a percentile of the offer delta. This session therefore does
**not** pre-quote its −13…−20 % rate delta as an expected price effect, and
the A/B is what decides materiality.

## 6. What this session will NOT do

* **No sixth MISO COAL_PRB committed-band variant** — the C7 COAL_PRB lane is
  CLOSED (miso-111 `R` / miso-112 `R` / miso-113 `I`), and nothing here touches
  coal.
* **No new `ScenarioConfig` field**, no CLI flag, no env knob (rules 24 / 26).
* **No floor mechanism**, so no `p1_fleet_prep` cold-rebuild branch and none of
  the miso-114 16 GB OOM exposure.
* **No holdout year.** `--years 2023 2024 2025` only; MISO holds no
  `calibration-complete` marker, so no out-of-training year is solved, scored
  **or read** (rule 22).
* **No fix to the pre-existing `origin/main` breakage** in
  `tests/regression/test_persisted_identity.py` (default cache key
  `0e9fce2fb55b889f` vs pinned `603c2498bf71d21d`), which predates this branch.
  It is reported in the finding and left to the lane that owns it.

## 7. Rule duties this session owes

* **Rule 15 `[R-DASHBOARD]`** — both arms registered on the backcast dashboard
  in this session, whatever the verdict.
* **Rule 16 `[R-ALLYEARS]`** — 2023 + 2024 + 2025 in one bundle per arm.
* **Rule 22 `[R-HOLDOUT]`** — training years only; leave-one-year-out inside
  2023–2025 before any promotion is proposed.
* **Rule 28 `[R-MECH-MATRIX]`** — the `measured_chp_heat_rates` × MISO cell's
  evidence is re-stamped in this session with the scope-gate outcome, whatever
  it is.
</content>
</invoke>
