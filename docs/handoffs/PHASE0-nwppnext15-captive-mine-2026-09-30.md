# PHASE 0 — NWPP-NEXT-15: captive-mine marginal coal fuel cost (zero LP)

Follows `DESIGN-nwppnext14-captive-mine-marginal-fuel-2026-09-30.md` §4. Design only: no field, no solve.

## §1 Captive-identification rule — FIXED BEFORE THE CENSUS WAS READ

Committed in its own commit, before `scripts/probes/_nwppnext15_captive_census.py` was run. Nothing below §1 existed
at that commit.

**Source:** EIA-923 Page 5 receipts, `data/raw/coal-receipts/coal_receipts_<Y>.csv` (verbatim columns). Zero DOF: every
input is a filed field; no per-plant list, no ownership map, no threshold tuned to anything.

**A receipt row is CAPTIVE iff all three hold:**

1. `Primary Transportation Mode` is a mine-mouth mode: `CV` (conveyor) or `TR` (truck) — the mine delivers without a
   common carrier;
2. `Coalmine State` == `Plant State`;
3. `Purchase Type` is not `S` (spot) — a spot purchase is by definition not a dedicated supply.

Every other coal row is **NON-CAPTIVE** (rail, barge, pipeline/slurry, multi-modal, out-of-state, or spot).

**Why this and not ownership.** The economic property that makes a mine's booked cost an *average* rather than a
*marginal* cost is that it is **dedicated** to the plant: its fixed cost is recovered over that plant's tons, whether the
mine is an affiliate (Bridger Coal Co.) or a third-party cost-plus mine-mouth contract. Dedication is observable from
the delivery mode and geography; ownership is not in the filing and would need a hand-kept affiliate map (rule 24).

**Known limits, stated before the numbers:** (a) a truck-delivered in-state *non-dedicated* mine is misclassified as
captive; (b) a dedicated mine that ships by rail (none expected in NWPP) is misclassified as non-captive; (c) rows with
`FUEL_COST` withheld count toward shares but not prices.

**Derived quantities (per plant, per year Y):**
- `mmbtu = QUANTITY × Average Heat Content`;
- `captive_share = Σ mmbtu[captive] / Σ mmbtu[all coal]`;
- `p_captive`, `p_noncaptive`, `p_blend` = MMBtu-weighted `FUEL_COST` ($/MMBtu, EIA reports cents/MMBtu — converted)
  over rows with a reported cost;
- **mixed-source** iff `0 < captive_share < 1` — only these plants are in scope for the design's object;
- `gap = p_blend − p_noncaptive` ($/MMBtu), the move the object would make on the econ tranches.

**Scope:** the NWPP model coal fleet (plants in keeper #18's `dispatch/<Y>_P1.parquet` with a `COAL_*` class),
2019–2024. **2025 receipts are not on disk** (`coal-receipts/` stops at 2024) — 2025 is reported as a gap, never
extrapolated.

**§1 ERRATUM (recorded after the first census run, before any interpretation).** §1 rule 1 named the conveyor code as
`CV`. EIA-923 has no `CV`; its conveyor code is **`TC`** (tramway / conveyor / slurry pipeline), and the DESIGN doc §2
already named `TC`. The codes on disk 2019–2024 are `GL OP RR RV TC TP TR WT`. The first run (with `CV`) classified every
Bridger conveyor row as non-captive. The code list was corrected to `{TC, TR}`; the rule's intent (mine-mouth, no common
carrier, in-state, not spot) is unchanged and no other part of §1 moved. Both runs are reported here.

## §2 Census (zero LP) — `docs/handoffs/nwppnext15/captive_census.json`, `scripts/probes/_nwppnext15_captive_census.py`

Fleet source: `thermal_tranches-perunit-vintage-NWPP.csv` `COAL_*` rows (13 plants). Keeper #18's bundle on `main` is slim
(no `dispatch/`), so the fleet list is the tranche table the keeper loads, not its dispatch. $/MMBtu, MMBtu-weighted.

**Mixed-source plant-years (the only scope the object can reach):**

| year | plant | captive share | p_captive | p_noncaptive | p_blend | gap = blend − noncaptive |
|---|---|---:|---:|---:|---:|---:|
| 2019 | Jim Bridger 8066 | 0.710 | 2.803 | 2.370 | 2.677 | **+0.307** |
| 2020 | Jim Bridger | 0.633 | 2.983 | 2.390 | 2.766 | **+0.376** |
| 2021 | Jim Bridger | 0.703 | 2.760 | 2.428 | 2.661 | **+0.233** |
| 2022 | Jim Bridger | 0.705 | 2.450 | 2.637 | 2.505 | **−0.132** |
| 2023 | Jim Bridger | 0.559 | 4.211 | 2.569 | 3.487 | **+0.918** |
| 2024 | Jim Bridger | 0.790 | 3.113 | 2.600 | 3.005 | **+0.405** |
| 2019 | Huntington 8069 | 0.995 | 1.970 | 1.247 | 1.967 | +0.720 (0.5 % non-captive) |
| 2022 | Huntington | 0.937 | 2.155 | 1.480 | 2.113 | +0.633 |
| 2022 | Hunter 6165 | 0.995 | 1.818 | 2.410 | 1.820 | −0.590 (0.5 % non-captive) |
| 2023 | Hunter | 0.904 | 2.684 | 2.454 | 2.662 | +0.208 |
| 2024 | Hunter | 0.933 | 3.459 | 3.367 | 3.453 | +0.086 |
| 2023 | Hardin 55749 | 0.871 | — | — | — | costs withheld |

**Not reachable:** Colstrip 6076, Centralia 3845, TS Power 56224, Sunnyside 50951 — `FUEL_COST` withheld in every year.
Dave Johnston, Naughton, Wyodak, Bonanza, North Valmy are 100 % non-captive (rail) — no move. Hunter/Huntington are
≥ 90 % captive. **2025 receipts are not on disk** — no 2025 number.

**What the census says, plainly:**
- The object is effectively a **Jim Bridger-only** lever. Every other mixed plant-year is either ≥ 99 % one kind or a
  withheld-cost row.
- At Bridger the gap is **+$0.92/MMBtu in 2023** (≈ $9–10/MWh at a ~10.5 MMBtu/MWh heat rate), and **$0.23–0.41 in
  2019–2021 and 2024** (≈ $2–4/MWh). In **2022 it is negative** (−$0.13): the object would *raise* Bridger's econ price
  that year. That is a real property of the construction, not noise.
- The DESIGN's ~$7–17/MWh 2023 figure compared captive vs non-captive; against today's blended price (what the model
  actually uses) the move is ~$9–10/MWh, the lower end.
- Huntington 2019/2022 and Hunter 2022 show large gaps on tiny volumes (0.5–6 % of tons). Pricing a plant's econ
  tranches off 0.5 % of its receipts would be a thin-sample artefact; **a minimum non-captive share is a free
  parameter** the owner would have to rule on (or the rule restricts to plants where both kinds are material).

## §3 Rule-19 seam map — every writer of a coal price today (keeper #18 posture)

Order inside `data/fuel/resolve.py::resolve_fuel_prices`, per generator row, `(n_gen, T)`:

1. **Trajectory** — `COAL_PRICE_BASE` escalated (backcast flat rate). Default for every coal row.
2. **`coal_supply_repricing`** (keeper: **True**) — `data/fuel/coal.py::apply_coal_supply_pricing`: flat annual
   lignite / PRB delivered cost by supply class (`coal_prb_contract_passthrough` 1.0).
3. **`coal_plant_monthly_pricing`** (keeper: **True**) — `data/fuel/plant_prices.py::apply_plant_monthly_fuel_prices`
   (backcast-only): overwrites each coal row whose `plant_code` has an EIA-923 monthly delivered cost with that cost.
   Keyed by **plant**, so **every tranche of the plant gets the same blended price**. Source is the legacy
   `eia923_monthly_fuel_costs.parquet`, which the `coal-receipts` README measures as an incomplete extract.
4. **`coal_fuel_inventory_take_floor`** (keeper: True) — `model/lp/rows.py` ~2182: **not a price writer.** A quantity
   floor on each yard's burn; its dual is the shadow value of the take. It already carries the take-or-pay block once.

**Where the new object would live:** inside seam 3, as a per-tranche branch at mixed-source plants — econ / peaking
tranches take `p_noncaptive`, must-run / committed keep `p_blend`. It **replaces** seam 3's value for those rows and
stacks on nothing (seams 1–2 are already overwritten there). Seam 4 is untouched, so the captive fixed cost stays in the
take and never becomes a per-MWh price.

**Open issue for the build (not decided here):** seam 3 reads the legacy parquet, the census reads Page 5. The object
must read one source; mixing a Page-5 non-captive price with a legacy-parquet blend would make `gap` partly a data-source
artefact. Either the object computes both prices from Page 5, or seam 3 is first moved to Page 5 (a separate rule-14
repair with its own footprint).
