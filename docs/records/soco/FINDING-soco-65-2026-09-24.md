# FINDING — SOCO-65 (2026-09-24): the keeper's start-markup census on all three years — NO/BLANK branch, zero LP

**Lane** SOCO-65 · **DATA PROFILE** soco · **Model** Opus (rule 27).
**Owner ruling on reopening `tranche_startup_amortization` for SOCO:** BLANK in the lane prompt, so this
lane ran the **zero-LP branch**: no field, no solve, no PRECOMMIT, no shard, no registration.
**Keeper / control of record:** `2026-09-24-soco61-dark-unit`, unchanged. Precondition verified at
`origin/main` `e4343fb2`: `keepers/SOCO.json` names it, and `git ls-remote origin 'refs/heads/claude/soco65*'`
printed nothing.
**Per-plant legs:** recovered at zero LP from the SOCO-61 shard SHAs (all three fetched) into
`results/calibration/soco61_arm_<Y>`. They are gitignored, and 0 files are tracked.
**Probe:** `scripts/probes/_soco65_census.py`. **LP cost: zero.**

---

## 1. The G reason, quoted (FINDING-soco-53 §2.4)

> **`tranche_startup_amortization` → `G`, no reopen condition.** It is the FERC Order-825
> **fast-start pricing** object (bid markup only), and **SOCO has no clearing price, no offers and
> no market**. Arming a market-design pricing rule on a footprint with no market is rule 1
> `[R-STRUCT]` verbatim. Derived from SOCO's own market design, not transferred from CAISO's `G`
> (rule 28(d)).

## 2. The census, all three years

**Construction (declared before reading any number).** The start markup on a tranche is its solved P1
`mc` minus its `fleet_only` `mc_base`, **minus the same difference on the same plant's econ/peak
sibling**.

- **Why subtract the sibling.** The raw difference carries a fuel-linked offset that is identical across
  one plant's tranches (they share a heat rate) and contains no start term. On an unmarked tranche the
  sibling difference is exact.
- **Which code builds `mc_base`.** The fleet is rebuilt at the **keeper's own `git_sha` `1d7edc1b`**, not at
  HEAD. HEAD's later solve-path changes (heat-rate vintage, `campd_bins`, `eia860`) shift `mc_base` by
  ±$0.2–3/MWh uniformly within a plant. A census taken at HEAD would mix that drift into the answer.
- **Check.** It reproduces SOCO-64's 2023 figure exactly: CT `_committed` median **$4.819/MWh**
  (SOCO-64: $4.82).

**Tranches carrying a start markup** (marked / total; the level is the median over marked hours, $/MWh;
the start cost is Σ markup × MWh):

| class · tranche | 2023 | 2024 | 2025 | energy on the tranche, TWh (2023/24/25) | start $ in the objective, $M (2023/24/25) |
|---|---|---|---|---|---|
| **CT_PEAKER `_committed`** | **18/18**, median $4.82, max $20 | **18/18**, $9.23, max $20 | **18/18**, $6.67, max $20 | 0.49 / 0.26 / 0.17 | 0.85 / 0.46 / 0.36 |
| **CC_REGULAR `_committed`** | **18/18**, $0.07, max $50 | **18/18**, $0.21, max $50 | **18/18**, $0.49, max $9.07 | 52.5 / 55.6 / 53.8 | 10.17 / 14.03 / 23.06 |
| CT_CHP `_committed` | 3/3, $0.03, max $6.06 | 3/3, $0.03, max $8.89 | 3/3, $0.03, max $6.45 | 0.56 / 0.56 / 0.56 | 0.03 each |
| CC_CHP `_committed` | 3/3, $0.07, max $50 | 3/3, $0.07, max $50 | 3/3, $0.83, max $50 | 0.37 / 0.37 / 0.32 | 0.04 / 0.05 / 0.04 |
| CT / CC / CHP **econ\*, peak** | **0** (exactly 0.000) | **0** | **0** | — | — |
| ST_GAS, all tranches | 0 | 0 | 0 | — | — |
| COAL `_committed` / econ / peak | 0 | 0 | 0 | — | — |

Measured on the dispatched CT `_committed` energy, the markup averages **$1.73 / $1.79 / $2.11/MWh**. That is
close to SOCO-64's rough CT estimate of ~$2/MWh ($20 spread over a 10 h run).

**Out of scope, noted.**

- Coal `_mustrun` tranches read *below* their sibling ($−0.07 to −3.0/MWh). That is the must-run tranche's
  own offer, not a start term, and it has no positive hour.
- One ST_CHP `_committed` tranche reads $0.01–0.02, which is at noise level.

**What charges it.** The markup is **not** the `tranche_startup_amortization` field. It is the core P1
bid-cost pass (`model/commitment.py::compute_monthly_markup`, "P1 = base + amortized startup markup",
CLAUDE.md), which every ISO's keeper runs.

- In SOCO it reaches every `_committed` tranche whose class keeps a start cost. SOCO's recipe exempts coal
  (`coal_warm_committed`) and ST (`gas_st_startup_cost` off).
- It also reaches CHP, because `chp_startup_covered` is off.
- The field's only job is to extend the same markup to the CT econ/peak tranches and CC peak
  (`data/fleet/assembly.py` `_fsp_econ` / `_fsp_peak`). Those tranches read exactly zero in all three years
  because the field is off.

## 3. Reading

- **The census holds in every year.** It does not depend on one year's dispatch. Every CT and CC
  `_committed` tranche carries the NREL start amortization (CT $20/MW, CC $50/MW) in 2023, 2024 and 2025.
- **The G reason and the keeper disagree.** The G reason calls start amortization a market-pricing object
  that has no place in SOCO. The keeper amortizes starts on 42 `_committed` tranches in every year, and
  **in this LP that markup is an objective cost**: it enters `min Σ mc × P`, which is how a cost-based,
  vertically integrated utility commits its fleet.
  - The SOCO comment at `scenarios.py` ~8600 states the same premise: SOCO's boilers "are committed against
    total system production cost".
  - This is a structural observation, not a measurement that refutes the G. Which way to resolve it is the
    owner's call.
- **The census does not measure the reach of either resolution.** Reach remains SOCO-64 §5: greedy, first
  order, 2023–2024, carried over unchanged here.

## 4. THE OWNER QUESTION (one)

**The G on `tranche_startup_amortization` and the keeper's live `_committed` start markup cannot both stand
as written. Which do you rule?**

- **(i) Keep the G and apply it consistently.** Strip the P1 start markup from SOCO's CT and CC (and CHP)
  `_committed` tranches, which SOCO-64 calls arm Z.
  - Measured consequence (SOCO-64 §5, greedy): 2024 CC_REGULAR share margin **0.81 → 0.66 pp**; 2023 CT/ST
    margins **0.81 / 0.74 → 0.73 / 0.66**.
  - No status moves.
  - It would need a SOCO-scoped gate on `compute_monthly_markup` (new field, matrix row, and a span).
- **(ii) Amend the G reason to: "market PRICING use refused; a cost-based start cost in the dispatch
  objective is admissible."**
  - The live `_committed` markup is then consistent as it stands. Nothing changes and nothing is solved.
  - The cell stays `G` for pricing use. The cost-based reopen (SOCO-64 arm B: CT econ/peak + CC peak at the
    same NREL $20/$50 per MW, no new scalar) becomes a lane you *may* authorize separately. It is not
    authorized by this ruling.

Recommendation, neutral on the numbers: **(ii)**. It describes what the keeper already does and what a
cost-based BA does; (i) removes a physical cost to satisfy a category label. Neither choice moves a
status today.

## 5. Governance / gates

- **No field or solve.** No `ScenarioConfig` field, bundle, sidecar, payload or bench part. No offer band
  was touched, and there is no `authorized_price_tuning` key. `actual_lmp.json` gets no SOCO block.
- **Keeper reads unchanged:** C1 14/14 · free 10/10 · C2/C4/C6/C8 PASS · C3a/b/c UNSCORABLE (not failed) ·
  grade 5/5/0 · DOF 13/1. The scorer's literal "PHYSICALLY-CALIBRATED (PRICE UNSCORED)" is not SOCO's
  determination.
- **Matrix (rule 28(b)):** no verdict changed. A SOCO-65 note was prepended to `tranche_startup_amortization`
  (G) in the SOCO shard, and a §5.8 note was added.
- **E13 standing:** `2026-09-20-soco53g-prb-own-iso` is still unruled, and rule 31 forbids deleting it.
  Re-raised; the standing recommendation is **decline**.
- **Nothing was solved, so there is no promotion question.** The keeper bundle
  `results/calibration/soco61_dark_unit_span` on `main` is untouched.
  - The keeper-sha fleet `.npz` arrays and `soco65_census.csv` live only in this container's scratchpad.
  - They regenerate in about 6 min with the probe docstring's recipe.
- **Leftover refs for the owner to delete** (a session cannot delete refs, rule 33(f)(2)):
  `claude/soco61-arm-{2023,2024,2025}`, `claude/soco60-arm-*`, `claude/soco60-armB-*`. SOCO-65 created
  **no** shard branches.

## Log entry

```
## soco-65 — 2026-09-24

KEEPER START-MARKUP CENSUS ON ALL THREE YEARS -- NO/BLANK BRANCH, ZERO LP.
Owner reopen ruling blank: no field, no solve. Keeper
2026-09-24-soco61-dark-unit unchanged.

Census (solved P1 mc - fleet_only mc_base, minus the same-plant econ/peak
sibling; fleet rebuilt at the keeper's own sha 1d7edc1b because HEAD's
heat-rate-vintage drift moves mc_base; reproduces SOCO-64's 2023 CT median
$4.82 exactly). In EVERY year 2023/2024/2025: CT_PEAKER _committed 18/18
marked (median $4.82 / $9.23 / $6.67, max $20/MWh; $0.85/0.46/0.36 M in the
objective), CC_REGULAR _committed 18/18 (max $50; $10.2/14.0/23.1 M), plus
CT_CHP 3/3 and CC_CHP 3/3 _committed (chp_startup_covered off). Every
econ/peak tranche, all ST and all coal: exactly 0. The carrier is the core
P1 bid-cost compute_monthly_markup, not the tranche_startup_amortization
field (which only extends it to CT econ/peak + CC peak).

G reason (SOCO-53 §2.4, quoted) and the keeper are inconsistent in all three
years. OWNER QUESTION: (i) strip the _committed markup to honour G (SOCO-64
arm Z: 2024 CC_REGULAR margin 0.81 -> 0.66; 2023 CT/ST 0.73/0.66), or (ii)
amend G to "market PRICING use refused; cost-based start in the objective
admissible" (no change; arm-B reopen then separately authorizable)?
Recommendation (ii). (2) decline 2026-09-20-soco53g-prb-own-iso (E13)?
Leftover refs: claude/soco61-arm-*, claude/soco60-arm-*, claude/soco60-armB-*.
Records: docs/handoffs/FINDING-soco-65-2026-09-24.md,
scripts/probes/_soco65_census.py.
```
