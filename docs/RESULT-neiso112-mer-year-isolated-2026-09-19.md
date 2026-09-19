# RESULT — neiso-112: NEISO's marginal emission rate, all six years, and the year-grouping defect does NOT reproduce here

```
SESSION : neiso-112 (parent = ORCHESTRATOR; it ran NO LP, rule 32 [R-SHARD] (a))
ISO     : NEISO        LP: SIX shards, ONE YEAR EACH (rule 36 [R-YEAR-ISOLATION])
PIN     : dd61092ced3ea42267c70f1a73194b513a26ac11
KEEPER  : 2026-09-16-neiso110-dualfuel-derate-scope — UNCHANGED. Nothing
          registered, no dashboard id minted, no keeper re-designated.
DELIVERED: marginal_emission_rate (tCO2/MWh, the emissions dual) for 2020-2025,
          43,800 zone-hours per year, ZERO nulls. Every bundle pushed in full.
HEADLINE: all six year-isolated solves reproduce the keeper's six-year single
          invocation with prices BIT-IDENTICAL (max |dPrice| 1.4e-14 to 5.7e-14,
          0 of 43,800 cells past 0.01 $/MWh) and annual class energy identical
          to ~1e-9 of total. The MISO year-grouping defect does NOT appear in
          NEISO.
```

---

## 1. THE MARGINAL-CARBON DATA — COMPLETE, ALL SIX YEARS

`marginal_emission_rate` is a per-zone-hour tCO2/MWh column in
`hourly/system_<year>.parquet`: 5 nodes x 8760 h = **43,800 zone-hours per year,
zero nulls in every year** (the recipe solves 8760 h in 2024 too, so the leap day
is not represented — that is the keeper's own `hours: 8760`, not a defect here).

| year | load-weighted mean | p10 | median | p90 | min | max | exactly 0.0 |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2020 | **0.5182** | 0.3631 | 0.5738 | 0.6488 | 0.2769 | 1.0000 | 0.00 % |
| 2021 | **0.4967** | 0.3484 | 0.4610 | 0.6533 | −0.0000 | 1.0000 | 0.01 % |
| 2022 | **0.4893** | 0.3425 | 0.4541 | 0.6677 | 0.2336 | 1.0000 | 0.00 % |
| 2023 | **0.5417** | 0.3677 | 0.5800 | 0.6728 | 0.2793 | 1.1681 | 0.00 % |
| 2024 | **0.5588** | 0.3791 | 0.5805 | 0.6754 | 0.2732 | 1.3191 | 0.00 % |
| 2025 | **0.5296** | 0.3604 | 0.5752 | 0.6712 | 0.2821 | 1.5677 | 0.00 % |

**The shape is a gas-on-the-margin ISO, and it is the photographic negative of
MISO's.** Set beside the MISO control taken the same day
(`RESULT-miso262-…-2026-09-19.md` §1):

| | NEISO | MISO |
|---|---:|---:|
| p90 | **0.65 – 0.68** | **0.94 – 1.02** |
| zone-hours at exactly 0.0 | **0.00 – 0.01 %** | **13 – 23 %** |
| most negative value | **−0.0000** | **−1.33** |

MISO's p90 near 1.0 is coal setting the margin; NEISO's near 0.67 is a combined-
cycle doing it, and the tight 0.34–0.68 interquartile span is a fleet where
almost every marginal hour is some gas unit. The near-total absence of zero and
negative cells says the same thing from the other side: NEISO essentially never
has a non-emitting unit on the margin, and has no large curtailable VRE block
whose absorption would make a marginal MWh *lower* system CO2. The handful of
cells at exactly 1.0000 (5–200 per year) are hours with a single ~1.0 t/MWh unit
marginal; they are not a cap, since 2023–2025 run to 1.17 / 1.32 / 1.57.

### 1.1 Tech-weighted rates — what the abatement page's `mer_tech` needs

Hourly system MER (demand-weighted across the five nodes), re-weighted by that
hour's own wind or solar output:

| year | load-weighted | **wind-weighted** | wind TWh | **solar-weighted** | solar TWh |
|---|---:|---:|---:|---:|---:|
| 2020 | 0.5182 | **0.5144** | 3.539 | **0.5285** | 0.361 |
| 2021 | 0.4967 | **0.4848** | 3.576 | **0.5004** | 0.538 |
| 2022 | 0.4893 | **0.4849** | 3.831 | **0.4882** | 0.908 |
| 2023 | 0.5417 | **0.5285** | 3.248 | **0.5371** | 0.890 |
| 2024 | 0.5588 | **0.5476** | 3.452 | **0.5630** | 1.311 |
| 2025 | 0.5296 | **0.5157** | 4.533 | **0.5253** | 1.577 |

Wind's avoided rate sits **below** the load-weighted mean in all six years
(−0.4 % to −2.4 %): it blows in lower-margin hours. Solar's sits at or slightly
**above** it in five of six. Both gaps are small because the margin barely
changes fuel — which is the same fact the distribution above reports, and is why
a NEISO abatement number will be far less sensitive to hourly matching than a
MISO one.

## 2. THE KEEPER IS REPRODUCED — AND RULE 36's DEFECT IS ABSENT IN NEISO

Each year differenced against the committed keeper's own P1 sidecars, indices
aligned row-for-row:

| year | max abs dPrice ($/MWh) | price cells > 0.01 | max abs d demand | largest annual d class energy (TWh) | net system energy delta |
|---|---:|---:|---:|---:|---:|
| 2020 | 1.42e-14 | **0 / 43,800** | 0.00e+00 | < 5e-7 | −2.8e-03 MWh (−3.1e-09 %) |
| 2021 | 2.84e-14 | **0 / 43,800** | 0.00e+00 | < 5e-7 | +1.7e-03 MWh (+1.7e-09 %) |
| 2022 | 5.68e-14 | **0 / 43,800** | 0.00e+00 | < 5e-7 | +1.0e-03 MWh (+1.0e-09 %) |
| 2023 | 2.84e-14 | **0 / 43,800** | 0.00e+00 | < 5e-7 | +2.1e-03 MWh (+2.1e-09 %) |
| 2024 | 1.42e-14 | **0 / 43,800** | 0.00e+00 | < 5e-7 | +7.7e-04 MWh (+7.5e-10 %) |
| 2025 | 3.55e-14 | **0 / 43,800** | 0.00e+00 | < 5e-7 | +1.1e-03 MWh (+1.1e-09 %) |

Annual load-weighted price, keeper vs year-isolated, agrees to four decimals in
every year: 26.6733 / 50.2462 / 88.8026 / 37.5278 / 42.5402 / 70.7113 $/MWh.

**This is the pre-registered expectation of the PRECOMMIT §4 settling in the
strong direction, and it settles a question rule 36 (f) left open.** That clause
says the artifact's *"size is unmeasured outside MISO"*; for NEISO it is now
measured, and it is **nil at the price and annual-energy level**. Where MISO's
2022 moved 24.18 TWh off CC_REGULAR onto coal and repriced 43,160 of 70,080
cells — ~$500 M of objective, i.e. the multi-year solve was not at the optimum —
NEISO's worst year moves **zero** price cells. The PRECOMMIT predicted a smaller
effect because MISO's swap ran through a coal/CC margin NEISO does not have;
the outcome is stronger than the prediction, and the §1 distributions are the
mechanism: with no coal tranche to swap into, there is no second vertex to land
on.

### 2.1 What DOES move — stated rather than rounded away

At the **hourly** grain, **1.19 – 1.55 % of class-hours** (1,460 – 1,897 of
122,640) differ by more than 0.1 MW, the largest single class-hour by
**402.6 – 587.5 MW**, among CC_REGULAR / hydro / oil / CT_PEAKER / CC_CHP.
Objective, prices, demand and annual class energy are unchanged, so this is
**alternate-optimum reshuffling of a degenerate LP among columns tied at the
margin** — the same signature, at the same magnitude, that neiso-107 already
recorded against this keeper (426.95 / 371.44 / 442.34 MW) and root-caused there.

**The honest consequence for the MER, carried rather than buried:** the marginal
emission rate is a *basis-dependent* dual, so in those ~1.3 % of tied hours the
value reported is one of several valid one-sided derivatives, exactly as the
`_marginal_emission_rate` docstring says of a degenerate vertex. It is not
wrong; it is the down-side derivative at a vertex where the derivative is
genuinely one-sided. No keeper MER exists to difference it against, so the size
of that ambiguity is **unmeasured** — naming it is the point, and a successor
that wants it bounded can perturb the RHS on a sample of those hours at zero
additional solve of the full year.

## 3. G-DRIFT — form 4 held, no control solve spent

The PRECOMMIT §3 audit over `c0916408..HEAD` (30 files, 19 non-merge commits)
classified every backcast-path hunk INERT for NEISO except the MER emit itself,
which is solve-invariant by construction (basis frozen, objective swapped to the
CO2 rate vector, re-priced at **zero** simplex iterations, basis and iteration
limit restored). All seven `SURFACE_MODULES` were byte-identical, so the
keeper's recorded fingerprint `9d35c270c69e9eee` still held.

**§2 is that audit's independent confirmation.** A LIVE hunk misclassified as
INERT would have shown up as a moved price; zero of 262,800 price cells moved
across six years. The keeper's committed bundle was a valid control and no
control solve was spent.

## 4. CONFIG SIGNATURE — verified by the parent, not taken on the shards' word

All nine checked fields PASS in all six bundles, read from each bundle's own
`run_config.json`: `iso` NEISO · `passes` ["P1"] · `commitment` false ·
`outage_source` historic · `neiso_coldsnap_derate_dualfuel_unswitched` true ·
`CC_REGULAR.committed` 1.212469 · `CT_PEAKER.committed` 1.288845 ·
`ST_GAS.committed` 0.754213 · each year's own gas price
(2.03 / 3.72 / 6.45 / 2.54 / 2.19 / 3.52).

## 5. RETRIEVABILITY — every bundle, with its full SHA (rule 34 [R-SHARD-PROMOTABLE] (e))

All six pushed IN FULL — **17 files each**, verified by
`git ls-tree -r <sha> -- <path>`, then fetched and checked out on the parent.

| year | bundle path | branch | **full recovery SHA** |
|---|---|---|---|
| 2020 | `results/calibration/neiso112_mer_2020` | `claude/neiso112-mer-2020` | `c36b794b5b6363db3255edcca929ccf7d74768f4` |
| 2021 | `results/calibration/neiso112_mer_2021` | `claude/neiso112-mer-2021` | `5b4833a80833ac65ba2bd7554819a027b6d64e0b` |
| 2022 | `results/calibration/neiso112_mer_2022` | `claude/neiso112-mer-2022` | `a5f3a9a430249708448425d9459a6ec1f7b6cdb5` |
| 2023 | `results/calibration/neiso112_mer_2023` | `claude/neiso112-mer-2023` | `49c7022f48fac32952d4290980826fb8e8f85175` |
| 2024 | `results/calibration/neiso112_mer_2024` | `claude/neiso112-mer-2024` | `b67072908d9deaec03e8ff14d120eaada40fc1e6` |
| 2025 | `results/calibration/neiso112_mer_2025` | `claude/neiso112-mer-2025` | `165f1db0b25939e0d60215c15611edbd9a1464c2` |

`git checkout <sha> -- results/calibration/neiso112_mer_<year>`. **A promotion
from this state costs ZERO re-solves.** The bundles are also on the parent's
disk, gitignored rather than committed (rule 32 (d) keeps per-year dirs out of
`main`; rule 31 [R-RETAIN] forbids deleting them), and the `.gitignore` entry
carries these same recovery lines. **The shard branches are deliberately NOT
deleted** (rule 33 [R-SHARD-ARCHIVE] (f)(3)): they hold bundles a promotion would
register and the owner has not ruled.

These bundles also carry two artifacts **no NEISO keeper has**, because a shard
pushes its full bundle while a keeper gitignores them: `hourly/network_<y>.parquet`
and `hourly/unit_hourly_<y>.parquet`, plus `dispatch/<y>_P1.parquet` and
`btm.parquet`.

## 6. COST

Six containers, ~3–4 minutes of LP each (2021 3.1 min · 2022 2.6 min · 2023
2.9 min · 2024 3.9 min; 2020 and 2025 did not report wallclock separately), peak
cgroup 4.74–4.84 GiB against the 13.34 GiB ceiling — no shard came near the
20-minute stop or needed swap. All six archived after their bytes were fetched,
checked out and verified (rule 33 (a)/(e)).

## 7. WHAT IS OPEN — THE PROMOTION QUESTION (rule 31 [R-RETAIN])

**Nothing was registered and the keeper was not re-designated.** The six bundles
are per-year and would have to be composed into one span bundle before
registration (rule 32 (d)); that composition is **zero-LP** but needs a NEISO
analogue of `scripts/probes/_miso260_compose_span.py`, which is hardcoded to
MISO's partition fields.

The case for promoting the composed span as NEISO's keeper is that it is a
**strict superset at identical numbers**: same recipe, same prices to 1e-14,
same annual energy, plus the MER column and the network / unit-hourly /
dispatch sidecars the incumbent lacks. It covers exactly the incumbent's year
set 2020–2025, so rule 35 [R-PROMOTE] (c) is satisfied. The case against is that
it is not needed for the abatement page — the MER data is usable from these
bundles as they stand — and a promotion re-keys the ISO's registered set.

**That is the owner's call, not this session's.** Until it is made, nothing is
deleted.
