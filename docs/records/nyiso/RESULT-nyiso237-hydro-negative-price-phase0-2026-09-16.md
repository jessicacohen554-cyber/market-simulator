# RESULT — nyiso-237: the hydro "cannot withhold" hypothesis is REFUTED, and the G2 kill of `hydro_budget_period_by_instrument` is a West-zone PRICE defect, not a hydro one

**Session** nyiso-237 (ORCHESTRATOR — rule 32 `[R-SHARD]` (a); **ZERO LP ran, no shard launched**).
**Date** 2026-09-16. **Keeper** `2026-09-14-nyiso-235-gas-repair` — **UNCHANGED.**
**Inputs** `docs/RESULT-nyiso236-hydro-budget-period-screen-2026-09-16.md` (addendum A2–A3),
`docs/PRECOMMIT-nyiso236-…`, `docs/FINDING-nyiso236-…`. **Probe**
`scripts/probes/nyiso237_hydro_negprice_phase0.py` (every number below; all inputs committed).

> ## VERDICT
> 1. **The repair hypothesis is REFUTED on measured data.** Real NYISO hydro is price-responsive at the
>    bottom: in the lowest fifth of each month's real West prices it runs **≈210 MW below** its
>    hour-of-day × month mean, and in every real low-price cut wider than a handful of hours it sits at
>    **0.83–0.86 of the matched level (−390 to −460 MW)**. A run-of-river plant that "cannot withhold"
>    is not what the meter shows. **The equality floor was NOT built.**
> 2. **The premise of the hypothesis is empty anyway.** The model's Upstate_West price is ≤ $0 in
>    **498 hours** of 2022; the real West zone was ≤ $0 in **21** (WEST alone) or **127** (five-zone
>    mean). Whole shoulder months average **≈ $0** in the model against **$22–58** measured. Hydro
>    "backs off at negative prices" in hours the model fabricates.
> 3. **The nyiso-236 G2 kill is fully localized to those fabricated hours**: 2022's −55.1 GWh falls in
>    Mar/Apr/Jun/Oct/Nov and 2023's −25.5 GWh in Oct/Nov — the months in which the model's Central-East
>    link sits **at its monthly cap in every hour** (720/720, 744/744) and curtailed wind sets a
>    **−$26 (PTC) price**. 2024 and 2025 have **zero** such hours, and there the arm is exact (G2 0.000 %).
> 4. **The successor is the Central-East seam, and it is already owner-gated** (nyiso-224: a topology
>    change). Hydro cannot be closed from the hydro side until the West stops being priced at wind's
>    PTC for a third of the year in 2022–23. **Nothing is promotable; nothing was screened.**

---

## 1. G-DRIFT at this head (rule 29 (b))

`moved_rows("NYISO") == {}` and `surface_stamp("NYISO", keeper_cfg).fingerprint == bd2b4657f9b5df7e`
at `a3df8337` (origin/main at session start), 5 merges after nyiso-236's audited head. Form 4 valid;
the keeper's committed bundle is the control. **No control solve owed.** (No solve was spent either way.)

## 2. The test, as the handoff wrote it — and what the meter says

Sources: EIA-930 `NG: WAT` (NYIS is **not** in `EIA930_PS_FOLDED_INTO_WAT`, and the 2022 annual
26.183 TWh matches the conventional census, so no pumped-storage pumping is hiding in the low hours);
NYISO 5-minute zonal RT LBMP averaged to the hour (all of 2022). Matching is (year × month × hod), so the
Treaty's diurnal scenic-flow schedule and the water year cannot confound it. Two price bases are
reported: **WEST alone** (the zone Niagara sits in) and the **five-zone mean A–E** (the model's
`Upstate_West`).

| real price cut, 2022 | basis | n hours | measured hydro ÷ matched | Δ MW |
|---|---|---:|---:|---:|
| ≤ $0 | WEST | 21 | **0.979** | −63 |
| ≤ $0 | A–E mean | 127 | **0.866** | −387 |
| ≤ $5 | WEST | 277 | 0.834 | −461 |
| ≤ $5 | A–E mean | 508 | 0.850 | −427 |
| ≤ $10 | WEST | 699 | 0.850 | −432 |
| ≤ $15 | WEST | 1,031 | 0.862 | −407 |

| within-month quintile, 2022 | hydro anomaly (MW) |
|---|---|
| **real West price** Q1 → Q5 | **−208 · −52 · +13 · +50 · +198** |
| real NYIS demand Q1 → Q5 | −65 · −62 · −36 · +8 · +154 |

**Reading.** The one cut that "holds up" (WEST ≤ $0, 0.979) is 21 scattered hours; every cut with a
usable sample says the real fleet **falls back ≈ 15 %** at the bottom of the price distribution, and the
price gradient (406 MW Q1→Q5) is roughly twice the load gradient (219 MW), so it is a price response, not
a load coincidence. The hypothesis (§A3 of RESULT-nyiso236) is **refuted**: an equality floor on Niagara
would force behaviour the measured fleet does not exhibit, and would do so in hours whose prices are
fabricated (§3). Not built; rule 19 reconciliation with `hydro_min_flow_floor` is therefore moot.

The same-year continuation years agree in direction where zonal data exists (2024: ≤ $15 n = 243,
ratio 0.954; 2023-06/12 and 2025-08 have no real ≤ $5 hours at all).

## 3. The model's non-positive West hours are fabricated

Keeper 2022, `Upstate_West` P1 price vs the real five-zone mean:

| month | actual ≤ $0 | **model ≤ $0** | actual ≤ $5 | **model ≤ $5** | actual mean $ | **model mean $** | CE cap MW | CE at cap (h) | arm hydro loss GWh |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 3 | 3 | 16 | 25 | 18 | 37.2 | 28.7 | 1,575 | 744/744 | **−19.1** |
| 4 | 21 | **118** | 102 | **654** | 32.3 | **−0.8** | 1,275 | 720/720 | **−10.1** |
| 5 | 48 | 20 | 119 | 635 | 31.9 | 2.5 | 1,125 | 744/744 | +2.0 |
| 6 | 4 | **93** | 20 | **472** | 57.5 | **8.3** | 2,200 | 720/720 | −3.7 |
| 10 | 10 | **116** | 36 | **484** | 39.1 | **4.7** | 1,175 | 744/744 | −0.6 |
| 11 | 23 | **131** | 156 | **579** | 22.4 | **0.5** | 725 | 720/720 | **−23.6** |
| year | 127 | **498** | 508 | **2,855** | 55.0 | 29.9 | — | — | **−55.1** |

(Jan/Feb/Jul/Aug/Dec: model 0 h ≤ $5; 2023: model 214 h ≤ $0 — May 170, Oct 23, Nov 18 — and the arm's
loss is Oct −17.8 / Nov −6.9 GWh; **2024 and 2025: model 0 h ≤ $5, arm loss 0.000**.)

**What sets the fabricated price.** 217 of the keeper's 498 hours clear at exactly **−$26** = the wind
production-tax-credit offer (`runner.py:2940`, the flat `-ira_ptc_wind` seam); the rest sit between −$11
and $0. In every one of those hours the arm's Central-East link (`Upstate_West → Capital_Hudson`) is at its
monthly measured DAM-TTC cap (`NYISO_INTERFACE_TTC_BY_MONTH`, nyiso-104: a backcast overlay of the MIS
`ATC_TTC` hourly posting, month-averaged), with the West carrying 3,277 MW nuclear + 1,799 hydro + 798 wind +
433 MW of still-flowing imports against 4,925 MW of zone load, 1,293 MW export and 278 MW of storage charge.
Zero dump, zero slack: the LP clears the surplus by withholding hydro (the only thing that is free to move
within the month) and curtailing wind at −$26.

**What the real system did in the same 498 hours** (matched): net imports fell **405 MW** toward export,
hydro fell **393 MW**, wind was +405 and nuclear +482 (the hours are real windy, low-load, no-outage hours)
— and the West price stayed positive (1st percentile **$1.97**, 5th **$6.48**). The magnitudes of the
hydro and import responses are the model's; the price is not. The model's Central-East link binds in
100 % of hours in 9 of 12 months of 2022 where the market's posted MCC is non-zero in 15–55 % (nyiso-169).

**Zonal monthly error, keeper minus actual ($/MWh).** 2022 `Upstate_West` **−26.9** on the year
(Apr −33.1, Jun −49.1, Oct −34.4, Nov −21.8) while NYC runs **+9 to +16** in the same months — the model
over-separates the state; every 2023–2025 zone-month with zonal data is within **+0.9 to +5.8**. This is a
**2022–23 defect**, which is exactly where G2 failed.

## 4. Consequence for `hydro_budget_period_by_instrument`

* The mechanism did what its arithmetic says everywhere the price is real: G2 **0.000 %** in 2024 and
  2025, footprint 7.46 → 4.16 %, hourly hydro r 0.722 → 0.802 (2025).
* Where the West is priced at wind's PTC for 470–650 hours a month, a 24 h use-it-or-lose-it budget
  **deletes** the water the LP will not run at −$26. That is the correct physics of the constraint applied
  to an incorrect price, and the pre-registered identity gate caught it.
* **Matrix cell `U → R`** (rule 28 (b)), citing this document — killed at G2 on the 2022–23 span, with a
  **stated re-open condition** (rule 28 (a) new evidence): a repair of the Upstate_West non-positive-hour
  fabrication that brings the model's 2022 ≤ $0 count to the same order as the measured 21–127. Until
  then it is not re-run, and **its 24 h / 168 h period lengths are not swept** (PRECOMMIT nyiso-236 §7).
* Not promotable, not recommended for promotion: 2 of 4 registered years destroy hydro energy.

## 5. The successor — named, sized, already owner-gated

The object is the **Central-East seam in 2022–23**, and it is not new: nyiso-224 relieved that one link
in a 2022 screen and moved `Upstate_West` 33.7 → 73.4 against a measured 60.6 (84 % of the 2022 C3a
residual), then REJECTED the arm on its own structural gates and named the successor as a **topology
change, owner-gated**. nyiso-169 established that the measured TTC is correct and stays armed (rule 14)
and that the aggregate-link dual has the wrong *shape*. This session adds the price-floor half of that
record: the seam saturation also manufactures **2,855 hours ≤ $5 against 508 real** in 2022, and that is
what killed the hydro lever. **Not this lane's to open unilaterally**; it is the item in front of hydro.

Two hydro-side facts stand regardless: **hydro is still unscored by C1** (handed-forward item 1,
unchanged), and **the model over-responds to price** (r(hydro, own price) 1.5–2.2× the actual's) — but
the second is now known to be partly the price's fault, not only the budget period's.

## 6. Rule 31 / 33 / 34 accounting

* **No new bundle exists.** This session solved nothing and launched no shard, so there is nothing to
  gitignore, archive or delete. nyiso-236's five legs stay where its RESULT §A6 pinned them
  (`4f82866b…`, `5041ca0d…`, `eee2a08b…`, `e77c597d…`, screen `478267ba…`); the 2022 and 2023 legs were
  read via `git archive <sha> … | tar -x` into the session scratchpad only.
* **Promotion question (rule 31): nothing to rule on** — this session recommends against promoting the
  nyiso-236 arm and built no alternative. If the owner nonetheless wants the arm registered, it is a
  zero-re-solve composition from the SHAs above.
* Class-E parity RED for `caiso279_ablate_dswcouple_span` and `soco15_spp_arm` is pre-existing and not
  NYISO's (rule 25); reported, untouched.
* **Rule 28 (b) discharged**: cell stamped this session. The NYISO shard's `keeper:` field and the §5.5
  prose header still named `nyiso-232` (CI WARN, a nyiso-235 duty); re-stamped to
  `2026-09-14-nyiso-235-gas-repair` here since this session edits both files.

## 7. Reproduction (zero LP, `--profile nyiso`)

```
python3 scripts/probes/nyiso237_hydro_negprice_phase0.py \
  --keeper results/calibration/nyiso235_gasrepair_span \
  --arm-bundle <dir from: git archive 4f82866b64b9d96a9046ae33111a4f8c4b2089f8 \
                 results/calibration/nyiso236_hydroperiod_2022 | tar -x>
```
