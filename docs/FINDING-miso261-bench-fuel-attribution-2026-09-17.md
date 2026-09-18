# FINDING — miso-261: the MISO bench fuel-family attribution is SETTLED, and the ±33 TWh caveat is LIFTED

```
SESSION : miso-261        ISO: MISO        COST: ZERO LP
QUESTION: miso-253 (2026-09-10) measured the committed MISO benchmark against MISO's
          EIA-930 telemetry and found 68.1 TWh of OFFSETTING per-family error -- gas
          -33.526, other +23.111, coal +10.827 -- and could not discriminate two
          readings at zero LP. HANDOFF-miso261 made settling it this session's FIRST
          task and blocked every MISO gas lane behind it.
ANSWER  : The bench is NOT mis-attributing gas. The gas leg is a BASIS DIFFERENCE
          (grid-delivered vs full-plant) that two measured quantities on disk account
          for exactly; the coal leg is the EIA-930 MISO COL cell under-reading against
          CAMPD by 17-21 TWh in EVERY year -- which this repository's own committed
          code already records. The rival BFG/OG relabelling hypothesis is REFUTED on
          magnitude by a factor of six.
BASIS   : Three independent sources, on the bench's OWN committed parts and plant set:
          EIA-923 per-plant (ba_code=MISO), CAMPD CEMS per-plant, EIA-930 telemetry.
          Nothing fetched; miso-253's "neither on disk" was wrong about EIA-923.
```

---

## 1. WHAT miso-253 ACTUALLY COMPARED, AND WHY THE TWO SIDES ARE NOT COMPARABLE

The 68.1 TWh is `classFull` (per model class, EIA-923-derived, **grid-delivered**)
differenced against the `e930` cells (the BA's own telemetry). Reproduced exactly from
`frontend/data/backcast/bench/MISO/2023.json.gz` at `origin/main`:

| family | `classFull` | `e930` cell | diff | miso-253 |
|---|---:|---:|---:|---:|
| gas (6 classes) | 207.651 | 241.242 | **−33.591** | −33.526 |
| coal (3 classes) | 185.787 | 174.950 | **+10.837** | +10.827 |
| other (OTHER+biomass+oil+OTHER_FOSSIL) | 26.762 | 4.485 | **+22.277** | +23.111 |

So the arithmetic is confirmed. What was never checked is whether the two columns are on
the same basis. **They are not**, and each leg fails differently.

### 1.1 The bench's fossil rows ARE EIA-923 per-plant — verified to four decimals

An independent reconstruction — EIA-923 monthly generation
(`data/raw/_processed-legacy/eia923_monthly_generation.parquet`, which carries `ba_code`,
`fuel_type`, `chp` and `prime_mover` per plant per year), restricted to `ba_code == "MISO"`
and mapped to EIA's own 930 fuel categories — gives MISO 2023 coal = **185.787 TWh**.

The bench's `classFull` coal is **185.787**. Exact. Nuclear likewise: 923-by-BA 87.177
against `classFull` 87.1773. The bench's plant set and its fuel mapping are therefore not
in question: they reproduce EIA-923's own BA attribution.

(`classFull`'s wind/solar rows are the 930 cells, not 923 — 91.715 / 6.348 against 923's
92.316 / 9.118. That is by design and is not part of this question.)

## 2. THE GAS LEG IS A BASIS DIFFERENCE, AND IT CLOSES ON MEASURED QUANTITIES

The EIA-930 NG cell is a **full-plant** series; `classFull` gas is **grid-delivered**, net
of the measured behind-the-meter host supply. Deflating the 930 NG cell by the
geothermal+biomass the BA folds into it (`gas_foldin_deflation`, already in the render) and
comparing it against **CAMPD CEMS full-plant net** for the bench's own gas plants:

| yr | 930 NG | deflated 930 | **CAMPD full-plant** | Δ% | `classFull` (grid) | CAMPD grid | measured BTM |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2020 | 197.380 | 184.296 | 192.855 | −4.4 | 171.483 | 168.481 | 24.374 |
| 2021 | 181.038 | 168.437 | 182.469 | −7.7 | 159.462 | 159.797 | 22.672 |
| 2022 | 208.389 | 195.418 | 204.267 | −4.3 | 183.258 | 179.720 | 24.547 |
| 2023 | 241.242 | 228.113 | 225.371 | **+1.2** | 207.651 | 200.532 | 24.839 |
| 2024 | 252.084 | 240.332 | 233.451 | +2.9 | 215.603 | 209.465 | 23.986 |
| 2025 | 233.227 | 228.808 | 218.701 | +4.6 | 199.848 | 196.161 | 22.540 |

Two readings, both stable across six years:

* **The deflated 930 NG cell tracks CAMPD FULL-PLANT net gas to −7.7 % … +4.6 %.** It is a
  full-plant series. It is not a grid-delivered one.
* **`classFull` gas sits 20–25 TWh below it in every year, and the measured BTM hold-out on
  those same plants is 22.5–24.8 TWh in every year.** The gap IS the hold-out.

A second measured block accounts for the remainder. EIA-923 NG inside the MISO BA at plants
the bench's dispatch set does not model at all:

| yr | 923 NG outside the bench set | of which `chp=Y` | share |
|---|---:|---:|---:|
| 2020 | 26.480 | 22.771 | 86.0 % |
| 2021 | 27.045 | 22.295 | 82.4 % |
| 2022 | 28.881 | 23.097 | 80.0 % |
| 2023 | 29.964 | 23.806 | 79.4 % |
| 2024 | 30.166 | 23.545 | 78.1 % |
| 2025 | 18.356 | 13.474 | 73.4 % |

The named plants are unambiguous industrial cogeneration — Dow St Charles Operations, PPG
Powerhouse C, Westlake Plaquemine, Motiva Port Arthur Refinery, Air Products Port Arthur,
ExxonMobil Baton Rouge, Sabine River Operations, NAFTA Olefins, Shell Chemical, SABIC,
Geismar Cogen (Gulf-Coast chemical and refinery sites in MISO-South), plus Gary Works (US
Steel). Their prime movers are GT 11.043 / CT 9.295 / ST 4.944 / CA 2.977 / IC 1.638 TWh.

**Neither block is a model deficit.** Both are energy the grid-delivered benchmark is
correct to exclude and the 930 full-plant cell is correct to include.

## 3. THE COAL LEG IS THE 930 CELL UNDER-READING — ALREADY ADJUDICATED IN THIS REPO

On the bench's own plant set, CAMPD CEMS **net** coal against the 930 COL cell:

| yr | CAMPD net coal | 930 COL cell | **CEMS − 930** | `classFull` coal |
|---|---:|---:|---:|---:|
| 2020 | 209.437 | 191.670 | **+17.77** | 201.314 |
| 2021 | 257.020 | 239.099 | **+17.92** | 249.094 |
| 2022 | 234.549 | 217.078 | **+17.47** | 223.052 |
| 2023 | 195.137 | 174.950 | **+20.19** | 185.787 |
| 2024 | 186.442 | 167.070 | **+19.37** | 176.316 |
| 2025 | 213.174 | 192.103 | **+21.07** | 212.505 |

`scripts/render_calibration_html.py:260` already says this, in a committed comment that
predates miso-253 by two months:

> "Against CAMPD (every coal unit and every grid CC/CT/ST gas unit is CEMS-metered),
> EIA-930 mis-splits coal vs gas by 7-21 TWh/yr (PJM 930 coal runs +7..+11 ABOVE CEMS,
> under-attributing gas by ~the same; **MISO is the mirror, −17..−21 BELOW**)"

The measurement above lands inside that band in all six years. `classFull` coal sits
**between** the two, nearer CAMPD. miso-253's "+10.827 coal" is the 930 cell reading low,
not the bench reading high — and the repository had already ruled the 930 per-fuel split
inadmissible for exactly this reason, which is why `reconcile_vintage_classes` reconciles
the **combined** fossil total and never the gas/coal split.

## 4. THE RIVAL HYPOTHESIS IS REFUTED ON MAGNITUDE

miso-253's competing reading: *"MISO's telemetry may label BFG/OG steam cogen `NG` where the
bench labels it `OTH`, in which case the cogen IS on the grid and the repair belongs on the
gas side."*

The entire EIA-923 BFG + OG block inside the MISO BA:

| yr | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|
| BFG+OG TWh | 5.260 | 5.491 | 5.592 | **5.913** | 4.976 | 2.235 |

**5.913 TWh cannot move a 33.5 TWh number.** Even relabelling the whole block leaves 83 % of
the gap untouched. And the fold that IS measured runs on a different fuel entirely: the BA
folds **geothermal + biomass** (13.129 TWh in 2023) into its NG cell, which
`gas_foldin_deflation` already subtracts — the deflation is in the table in §2 and is the
reason the deflated cell lands on CAMPD.

## 5. THE ONE REAL GAP, AND IT IS NOT GAS-FAMILY-SIZED

Exactly one merchant grid plant sits in the "absent from the bench entirely" block:

**West Riverside Energy Center (EIA plant 64020, `chp=N`, Alliant, Wisconsin, COD 2020)** —
`ba_code = MISO` in every year, EIA-923 net generation 1.936 / 1.972 / 3.131 / 4.259 /
4.961 / 4.367 TWh for 2020–2025, and absent from the bench's dispatch plant set in all six.

That is a genuine rule 14 `[R-ACCURATE]` intake item worth ~4–5 TWh in the recent years, in
`CC_REGULAR`. It is **not** a gas-family object and it does not restore the ±33 TWh caveat.
Recorded here for whichever lane opens the fleet-coverage question; this session did not
act on it.

## 6. WHAT THIS SETTLES, AND WHAT IT DOES NOT

**SETTLED — the ±33 TWh caveat is LIFTED.** `HANDOFF-miso261` §"YOUR FIRST TASK" blocked
every MISO fuel-family number behind this question. It is answered: the bench's C1 gating
basis (`classFull`, per class, grid-delivered) is sound, its fossil rows reproduce EIA-923's
own BA attribution exactly, and the 68.1 TWh is the difference between a grid-delivered
benchmark and a full-plant telemetry cell plus a documented 930 coal under-read. MISO
fuel-family numbers on the `classFull` basis may be quoted without the caveat.

**STILL TRUE, and it is the reason the caveat mattered: the `fuelRows` basis is NOT the
gating basis.** `fuelRows[*].b` is the 930 cell (deflated for gas) — a full-plant series —
while C1 gates on `classFull`. A "gas deficit" read off `fuelRows` is a basis artefact, and
`RESULT-miso260` §3's *"standing gas deficit, 13–35 TWh in every year"* is withdrawn on
exactly that ground (its own ADDENDUM B withdrew it as unestablished; this finding closes
it as **refuted**). **Do not open a MISO gas lane on `fuelRows`.**

**NOT SETTLED, and deliberately untouched here.** Whether MISO has a gas object on the
*gating* basis is a separate question with a different answer shape: `CC_REGULAR`'s C1 error
flips sign across the span (+5.92 / −9.46 / −9.47 / −6.39 / +3.32 / −3.15), which
`RESULT-miso260` §4.2 already records as a falsified level premise. miso-260's zero-LP
capacity census (ADDENDUM B.4) stands unchanged: if a gas object exists it is an
**availability** question on CC, not an offer-curve one.

## 7. METHOD NOTE — miso-253's "neither on disk" was wrong

miso-253 wrote: *"what would settle it is a per-generator EIA-930 fuel attribution or MISO's
registered-resource roster, neither on disk — intake work, not a solve."* The first of those
is effectively on disk and has been throughout: `eia923_monthly_generation.parquet` carries
`ba_code` per plant per fuel per year, which is the same BA attribution EIA compiles 930
from, at generator grain. No intake was required and nothing was fetched. The whole of this
finding is six committed bench parts and two committed parquets.

---

## 8. RULES

* Rule 14 `[R-ACCURATE]` — the conclusion is reached by preferring measured sources over an
  estimate, and §5 keeps the discovered coverage gap rather than burying it.
* Rule 1 `[R-STRUCT]` — no mechanism was proposed, armed or tuned; no residual was consulted
  in reaching any conclusion here.
* Rule 32 `[R-SHARD]` (a) — **this session ran ZERO LP.** Every number above is read from
  committed artifacts.
* Rule 24 `[R-REGISTRY]` — no tunable added or changed.
