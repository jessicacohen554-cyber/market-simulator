# PRECOMMIT — neiso-116: closing the C1 CC_REGULAR misses (2019 / 2022) — phase 0, zero LP (2026-09-26)

**ISO:** NEISO · **Mode:** backcast · **LP spent:** zero · **Base:** `f30e3704` (main) ·
**Keeper = control (rule 29(b) form 4):** `2026-09-25-neiso114-arm-b-stgas`, bundle
`results/calibration/neiso114b_span` (2019–2025), legs solved at `9db30b45`.

Keeper state: train tier 2023–2025 **CALIBRATED** (C3c ledgered); full span **NOT-YET** on C1 CC_REGULAR
only — 2019 −2.87 TWh (band ±2.81, share −4.0 pp vs ±3 pp) and 2022 −3.03 TWh.

**No arm is declared here.** Each lever below needs an owner ruling before any shard launches (handoff
instruction). §5 lists the decisions.

## 0. Bench refresh + keeper re-score (work item 0) — DONE, no status flip

The keeper's full bundle was rebuilt at zero LP from its seven neiso-115 legs (still fetchable by SHA:
`5aef7e7e`, `b55c8f60`, `ad2b7366`, `3f4f1013`, `75a53bc5`, `c5f48d90`, `7bfdfc2c`; recipe re-verified per
leg — `calibration_flags.offer_curve_overrides == arm_b_offer_curve.json`, `years == [Y]`,
`coal_mustrun_requires_measured_row`, one surface `d2d76036034ff03e`), then re-registered under its own id
and label with `--no-prune` (sidecar definition restored). `check_bench_freshness.py`: NEISO **6 STALE → 0**.

| scope | before (stale parts) | after (fresh parts) |
|---|---|---|
| full span 2019–2025 | NOT-YET (C1 FAIL) | NOT-YET (C1 FAIL) — identical |
| train tier 2023–2025 | CALIBRATED (C3c ledgered) | CALIBRATED (C3c ledgered) — identical |

The only scored number that moved: C2 sysvol 2021 actual 60.07 → 60.11 TWh (+0.8 % → +0.7 %), from the
EIA-930 coal-CEMS row (2021 0.289 → 0.537, 2020 0.130 → 0.154). The rest of the part diff is per-plant
display keys (the restored plants 562, 8002, 6156, 1642, 568 now present; `COAL` → `COAL_*` labels);
`classFull` is unchanged, so every C1 number is byte-identical. `legitimacy_diagnostics.json` regenerated at
HEAD (C8 coal-subclass code): forced shares move ≤ 0.001, C8 PASS unchanged.

## 1. G-DRIFT (rule 29(b)) — keeper basis `9db30b45` → HEAD `f30e3704`: ALL INERT

37 solve-path files changed. Audited **mechanically**: `docs/handoffs/neiso114/gdrift_fleet_probe.py` rebuilt
the keeper recipe's LP inputs with the basis code (a code-only worktree at `9db30b45`, data from this tree)
and with HEAD, per year.

| year | units | max \|Δ\| over pmax, pmin, heat rate, availability, min_gen, mc_base, demand, wind, solar |
|---|---|---|
| 2019–2025 | identical (757 / 778 / 788 / 766 / 743 / 736 / 833) | **0.0 on every array, every year**; 0 class-label diffs |

Form 4 is valid for all seven years: **the keeper is the control; no control solve is owed.**
(Caveat, stated: the probe builds from the bundle's `meta.json` recipe, which does not carry arm B's ST_GAS
`--offer-curve-json`; a HEAD change confined to the override path would not show here. None of the 37 files
is on that path — `offer_curves.py` is not in the diff.)

## 2. Work item 1 — Merrimack's coal: the recommended premise is false, and price is not the binding fact

Source: EIA-923 Page 5 receipts (`data/raw/coal-receipts`), Merrimack plant 2364.

**(a) Merrimack does not burn imported coal.** Its receipts carry mine name + MSHA id, all **domestic
Northern Appalachia**: Murray American Blacksville #2 (WV, MSHA 4601968) Nov 2019–Jun 2020 by rail; Murray's
Marion Docks (WV, 4606904) 2021–2023 by barge+truck or rail; CONSOL Bailey Mine (PA, 3607230) Dec 2022 / Mar
2023. Option (i) (price at EIA's import price for the origin country) has nothing to apply to. (The
imported-coal plants are Bridgeport 568 — Indonesian SUB, Adaro Tutupan, 2018 — and Schiller 2367 —
Colombian BIT, 2017–2019.)

**(b) Merrimack's own delivered cost IS published for 2019–2020.** `FUEL_COST` is present while the plant
reported as regulated (`REG`, Nov 2019–Jun 2020): 313.2 / 318.2 / 313.1 / 317.0 / 307.5 / 310.4 / 308.0
¢/MMBtu — **≈ 3.13 $/MMBtu**, vs the Tier-3 placeholder ≈ 2.80–2.94 (the placeholder is ~0.2–0.3 *low* in
those years). From Nov 2021 the rows are `UNR` and cost is redacted.

**(c) The nearest measured comparable (option ii) exists at the SAME MINE.** Bailey Mine's delivered cost to
other plants (EIA-923, quantity×heat-weighted): 2.53 / 2.42 / 2.53 / **3.04** / 3.89 / 3.65 $/MMBtu for
2019–2024 (160–220 cost-bearing rows/yr). Merrimack's measured premium over Bailey peers: +0.64 (2019),
+0.69 (2020). A Bailey-anchored delivered price for Merrimack would read ≈ 3.2 (2021), ≈ 3.7 (2022), ≈ 4.6
(2023) — a +0.8 $/MMBtu correction in 2022.

**(d) But a price correction cannot close 2022.** Bound from the keeper's own P1 dispatch at Merrimack's
node: a +$8.5/MWh offer (+0.8 $/MMBtu × ~10.6 MMBtu/MWh) displaces ≈ **0.47 TWh in 2022** (+$15: 0.86;
+$25: 1.53), ≈ 0.21 in 2021, ≈ 0.02 in 2019 — against a 2022 COAL_BIT excess of **2.58 TWh**. The keeper's
2022 LMP exceeds $58 in 74 % of hours; gas averaged $6.45. Coal at any plausible delivered price stays in
merit.

**(e) What does bind is the coal that physically existed.** Merrimack received **175 kt in 2022** (53 kt/yr
over 2020–21) and opened 2022 with 241 kt in its yard. The keeper burns **31.0 TBtu** there in 2022 (≈ 1.19
Mt) — ~4× what was on hand plus what the prior years delivered. This is precisely the object
`coal_fuel_inventory` (miso-259) and `coal_fuel_inventory_plant_grain` (miso-268) were built for — zero free
parameters, rule-13 admissible (every sizing quantity predates the year), **NEISO cell U** on both.

**Census** (`phase0_coal_budget_census.py` → `phase0_coal_budget_census.json`; budget = (Dec(Y−1) stock + mean
receipts Y−2..Y−1) × heat content, the plant-grain construction; model burn = keeper P1 MW × LP heat rate):

| year | yard | keeper TWh (TBtu) | yard budget TBtu (≈ TWh) | annual cut TWh | pooled monthly limb: months binding / TBtu over caps |
|---|---|---|---|---|---|
| 2019 | 568 Bridgeport (PRB) | 0.787 (7.41) | 3.11 (0.33) | **0.457** | 5 / 10.4 |
| 2019 | 2364 Merrimack | 0.731 (7.75) | 6.35 (0.60) | 0.131 | |
| 2019 | 2367 Schiller | 0.089 (1.29) | 3.00 (0.21) | 0 | |
| 2020 | all three | 0.449 (4.41) | 13.66 | 0 | 1 / 1.1 |
| 2021 | 2364 Merrimack | 1.549 (15.86) | 9.23 (0.90) | **0.647** | 7 / 9.4 |
| 2021 | 568 Bridgeport | 0.277 (2.73) | 4.09 | 0 | |
| 2022 | 2364 Merrimack | **2.932 (31.00)** | **7.68 (0.73)** | **2.206** | 12 / 23.3 |
| 2023 | 2364 Merrimack | 0.648 (6.86) | 9.65 | 0 | **4 / 2.3** |
| 2024 | 2364 Merrimack | 0.397 (5.69) | 9.70 | 0 | **2 / 2.7** |
| 2025 | 2364 + 2367 (dead row) | 0.332 (5.13) | 4.81 (2367: 0) | 0.132 (2367) | 3 / 3.4 |

Reading, stated before any solve:
- The **annual yard rows** bind where the C1 misses are (2019, 2021, 2022) and are slack in 2020 and the
  whole train tier. If CC_REGULAR absorbs most of the cut, 2022's −3.03 TWh moves to roughly −1 (PASS);
  2019 volume moves inside ±2.81 but its share leg (−4.0 pp, ≈ 1.4 pp/TWh) likely stays just outside ±3 pp
  on the coal cut alone — 2019's other excess is ST_GAS +0.82 and CT_PEAKER +1.15 (§4).
- The **pooled monthly limb** (budget/12 per month, required by the code: plant-grain raises without it)
  binds in **2023 and 2024** too, because Merrimack is a winter unit and the limb spreads its budget flat.
  That moves train-tier years and cuts coal in the months it actually ran. The monthly limb is a MISO
  construction (owner ruling 2026-09-16 was taken on MISO's fleet); whether NEISO takes it is a decision.
- 2025: Schiller 2367 (a dead row in the 2025 vintage, retired 2020) dispatches 0.13 TWh against a zero
  budget — the plant-grain row would zero it, which is correct.

Arming either field for NEISO needs a code change: both raise outside MISO at the call site in
`scripts/run_calibration.py` (the lift is deliberate, per the matrix row). Rule 25: the construction is
generic; every NEISO quantity above is NEISO's own EIA-923 data. Shared storage: PSEG Provport (8858) is a
Providence coal terminal that received the same Adaro Tutupan cargo as Bridgeport in 2018 (Dec-2018 stock
117 kt); it is **not** in `coal-shared-storage-crosswalk.csv`. Adding it would raise Bridgeport's 2019 budget
from 3.11 to ≈ 5.4 TBtu (cut 0.457 → ≈ 0.23 TWh). Whether that is a published ownership fact that qualifies
is an owner call; the census above leaves it out.

## 3. Work item 2 — re-deriving `thermal_tranches_NEISO.csv`: the deriver cannot do it as-is

`derive_thermal_tranches.py --iso NEISO` run at HEAD (scratch output, not committed):

1. **It drops Merrimack's coal row.** `_THERMAL_GROUPS` still keys on the deleted `COAL` class; since COAL-SUB
   the fleet carries `COAL_BIT`/`COAL_PRB`, so every coal plant silently falls out (76 → 75 rows). A
   COAL-SUB repair to the deriver is needed first (derive under the subclass, write the artifact-family
   token, as the other artifact joins do).
2. **It reads the single canonical fleet** (`load_fleet_from_csv`), not the year-matched corrected fleet, so
   the restored ST_GAS plants (562, 8002, 6156, 1642) never appear (ST_GAS n = 1, Montville) and
   Merrimack's nameplate stays 108 MW against CEMS for both units.
3. **The committed table is not reproducible at HEAD under any tested window** (2024–25, 2023–25, 2022–24:
   0 of 42 `ok` rows exact; its sidecar records the derive vintage as unknown). A whole-table regeneration
   would therefore move **every** CC row (e.g. 3236 committed 40.3 → 14.8 %, 55517 55.3 → 8.2 % over
   2019–25) — a table-wide change, not the rule-23 membership repair.

Recommended scope, if the owner takes item 2: a **membership-scoped** addition — derive rows ONLY for the
plants whose membership/nameplate the corrected fleet changed (2364 on its vintage nameplate; 562, 8002,
6156, 1642) with the COAL-SUB-repaired deriver, on the corrected per-year fleet, leaving every other row
byte-identical. Rule 23 citation: the data change is the F1 vintage correction's membership, never a
residual. Needs a deriver option for a vintage fleet — a `scripts/` code change (Opus/Fable, rule 27).

## 4. Work item 3 — ST_GAS committed band on its physical basis: not ST_GAS-only, and the artifact is stale

`committed_band_measured_basis` is **non-selective by construction** (rule 1): it replaces the `committed`
multiplier of every class the ISO's `neiso_campd_marginal_hr_summary.csv` covers, and drops the coal
passthrough sigmoid from the coal committed band. Against the keeper's resolved committed multipliers:

| class | keeper committed | artifact `avg_committed_p50` | artifact n |
|---|---|---|---|
| ST_GAS | 0.850 | **2.394** (corrected class, arm B's 7 units: **2.449**) | 2 (Montville) |
| CC_REGULAR | 1.212 | 1.107 | 51 |
| CC_CHP | 1.098 | 1.399 | 5 |
| CT_PEAKER | 1.289 | 0.985 | 18 |
| CT_CHP | registry | 1.955 | 1 |
| coal (all subclasses) | registry + sigmoid | 0.937, sigmoid dropped | 2 (pre-correction) |

So: (a) ST_GAS's min-load block would be priced at ~2.4–2.45× base heat rate (min-load average HR ≈ 25–30
MMBtu/MWh measured on the restored units), ~2.9× the keeper's — a strong further cut to ST_GAS (2019 model
1.05 vs actual 0.23 TWh); (b) CC_REGULAR's committed block gets ~9 % cheaper and CT_PEAKER's ~24 % cheaper —
the latter pushes the wrong way on 2019's CT_PEAKER +1.15 TWh; (c) the artifact's ST_GAS and COAL rows were
derived on the pre-correction fleet (the same defect neiso-114 §1 named), so arming it honestly first needs
`derive_campd_marginal_hr.py` re-run on the corrected membership (rule 23) — which re-identifies every class
row, not just ST_GAS.

## 5. Owner decisions needed before any solve

1. **Coal fuel budget (recommended lever — closes the 2022 miss by construction, zero DOF).** Arm
   `coal_fuel_inventory` + `coal_fuel_inventory_plant_grain` for NEISO (lift the MISO gate deliberately)?
   Sub-choices: (a) take the pooled **monthly** limb as built (moves 2023/2024, winter-hostile) or first make
   the plant-grain annual rows armable without it (code change, NEISO-motivated); (b) add PSEG Provport 8858
   to the shared-storage crosswalk for Bridgeport, or not.
2. **Merrimack delivered price.** Option (i) is moot (domestic coal). If still wanted after (1): (ii) Bailey
   Mine delivered peers + Merrimack's own measured 2019–20 premium (a measured reconciliation, rule 14; ≤ 0.5
   TWh effect in 2022), or leave the placeholder. Not recommended as the 2022 lever.
3. **Tranche re-derive scope** — membership-scoped (recommended) vs whole-table, and approval of the deriver
   COAL-SUB repair + vintage-fleet option.
4. **Committed measured basis** — only after re-deriving the marginal-HR artifact on the corrected fleet, and
   knowing it moves every class (CT_PEAKER the wrong way for 2019).

Proposed sequencing: (1) as arm A across all seven years (one shard per year, rule 36); (3) and (4) as later
arms on top, each with its own phase 0 on the regenerated artifact.
