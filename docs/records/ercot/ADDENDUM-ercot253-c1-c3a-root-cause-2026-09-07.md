# ADDENDUM — the 2021 C1/C3a root cause is CC_REGULAR's OFFER LEVEL, not missing EIA-860 capacity (ercot-253)

> Zero-LP, from the committed bundles' own fleet reconstructions. Raised by the
> owner on two challenges: first that the class substitution (not Uri) drives the
> +28.2 % C3a, then that CC_REGULAR capacity might be missing from EIA-860. The
> first is **confirmed** (`RESULT §2a`). The second is **ruled out**, and the
> measurement points somewhere sharper.

## 1. The capacity is NOT missing

`reconstruct_bundle_fleet` on each year's own committed bundle:

| class | 2021 | 2022 | 2023 |
|---|---|---|---|
| **CC_REGULAR** | **33,120 MW / 643 units** | **33,120 MW / 643** | **33,120 MW / 643** |
| CT_PEAKER | 8,172 MW / 683 | 8,172 / 683 | 8,469 / 700 |
| ST_GAS | 12,597 MW / 222 | 12,597 / 222 | 12,300 / 205 |
| CC_CHP | 5,714 MW / 258 | 5,714 / 258 | 5,714 / 258 |

CC_REGULAR is **byte-identical across all three years**. Nothing is missing on the
capacity side, and 114.47 TWh (the EIA-923 actual) is a 39.5 % capacity factor on
33,120 MW — entirely reachable. The model produces 97.23 TWh = 33.5 % CF. **The
fleet can make the energy; the merit order does not call on it.**

## 2. What IS wrong: CC_REGULAR's 2021 marginal cost is ~2.7× what its gas price implies

Capacity-weighted marginal cost by class, from each bundle's own `mc_base`:

| year | HH gas ($/MMBtu) | **CC_REGULAR p50** | CT_PEAKER p50 | ST_GAS p50 | **CT − CC** | **CC MC / gas** |
|---|---|---|---|---|---|---|
| 2023 | 2.54 | **$18.95** | $42.13 | $33.25 | **+$23.18** | 7.5 |
| 2022 | 6.45 | **$42.67** | $73.60 | $71.82 | **+$30.93** | 6.6 |
| **2021** | **3.72** | **$73.85** | **$80.15** | **$120.97** | **+$6.30** | **19.9** |

Two things fall out and they are the whole story:

1. **2022 and 2023 track gas cleanly** (CC MC / gas = 6.6 and 7.5, a ~7× heat-rate-
   like ratio). **2021 is 19.9×.** On the 2022/2023 relationship, 2021's $3.72 gas
   implies a CC_REGULAR marginal cost of roughly **$25-28/MWh**. It is **$73.85** —
   about **$46/MWh, or 2.7×, too high**.
2. **The CT − CC spread collapses from $23-31 to $6.30.** That is precisely the
   mechanism behind C1: with almost no cost separation left, CT_PEAKER runs 2.16×
   its actual energy (+115.5 %) and CC_REGULAR falls −14.0 %. And a merit order
   whose gas fleet all sits near $74-80 sets non-scarcity prices at exactly the
   level `RESULT §2a` measured: **+144 % across the eleven non-Uri months**.

This single defect explains **both** load-bearing failures. C1 and C3a are not two
problems.

## 3. A lead I named in the RESULT and am now WITHDRAWING

`RESULT §7` item 0 proposed `gas_offer_margin_anchor_vintage` (pjm-169 F4) as the
prime candidate. **The arithmetic does not support it.** `gas_offer_margin_anchor`
is **2.2494 in all three bundles**, and the term is `markup_hr × (anchor − fuel)`.
Every year's delivered gas sits *above* $2.2494, so the term is negative — it
*lowers* offers — and it is **most** negative in 2022 ($6.45), the year whose CC
marginal cost is well-behaved. A mechanism that should depress 2022's offers hardest
cannot be what lifts 2021's. The lead is withdrawn rather than left standing
because a plausible-sounding candidate that the numbers contradict is worse than no
candidate.

## 4. Where to look instead — and it is a ZERO-LP job

The object is: **which term adds ~$46/MWh to CC_REGULAR's offer in 2021 and not in
2022 or 2023?** Every input needed is in the three committed bundles, so this is an
offer-array census, not a solve. Ranked by what the 2021 fleet-build log already
shows firing:

1. **The ERCOT zonal gas basis and the West net-load gas step.** The 2021 build logs
   both (`ERCOT zonal gas basis (2021)`, `ERCOT West net-load gas step (2021)`).
   Compare the delivered $/MMBtu each unit actually pays against the $3.72 hub, per
   year — if 2021's delivered gas lands near $10/MMBtu at a ~7 heat rate, that alone
   is the $73.85 and the search ends there.
2. **F923 delivered fuel costs for 2021.** The 2021 build prices a subset of units
   from their own plant's F923 rows and gap-fills the rest; a bad 2021 F923 vintage
   would hit CC hardest (it is the largest class).
3. **The CC committed-block offer margin** (`CC committed-block offer margin: … level
   10.3540 $/MWh / shared gas anchor 2.2494`) and the **gas offer net-revenue
   margin** (`1687 tranches compressed at anchor 2.2494`), which are the two terms
   that add a fixed $/MWh on top of fuel. Check whether either is year-invariant in
   $/MWh where it should scale, or is being applied twice.
4. **ST_GAS is the tell that something is also forced.** Its 2021 marginal cost is
   **$120.97 — the highest of any gas class — yet it over-produces +38.6 %.** An
   expensive class that runs anyway is running on a floor, and the 2021 build arms
   one: `ST_GAS net-load reliability-drag floor … frac = clip(0.00906×netGW − 0.1376,
   0, 0.34)`, whose coefficients were identified on the training window's net-load
   levels. A forced $121/MWh unit setting price in ordinary hours is a direct second
   route to the +144 %.

## 5. Governance

Nothing here changes any registered number, and nothing was tuned. The measurements
are read-only reconstructions of committed bundles. **Identification belongs on
2023-2025** (rule 22 step 3) even though the *symptom* is visible only in 2021: the
question "what is year-invariant that should scale with gas" is answerable in-sample.
`RESULT §7` item 0 is superseded by §4 above.
