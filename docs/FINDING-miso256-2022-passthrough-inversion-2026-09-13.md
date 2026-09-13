# FINDING — miso-256: MISO's gas passthrough is 55 % of the real market's, and the two "unpriceable" years are the proof

```
SESSION : miso-256          ISO: MISO          KEEPER: 2026-09-12-miso-255-sil-measured
ASK     : (1) can 2020/2021 be priced at all?  (2) diagnose the 2022 passthrough inversion.
RESULT  : (1) YES — the block was never real. Three route audits swept two report families;
              MISO's pre-2023 record lives in a THIRD, uncredentialed and live back to 2015.
              2020 and 2021 are now STAGED, DERIVED and SCORED (§0).
          (2) The defect is a PASSTHROUGH SLOPE and it is now MEASURED, not inferred:
              4.63 $/MWh per $/MMBtu against the real market's 8.41 — 55 % — propped up by a
              fixed intercept, with corr(gas, error) = -0.841. 2022 is the far end of that
              slope, not a special year. The coal findings in §3-§4 are the same defect at
              its extreme and stand.
LP SPENT: ZERO. No solve was launched (rule 29 [R-SCREEN]); this is a data intake and a re-score.
```

> **READ §0 FIRST.** It was written after the rest of this document and supersedes §1's
> conclusion and §2's framing. The superseded text is kept in place, marked, because how an
> exhaustive-looking audit reached the wrong answer is the more useful record.

## 0. ADDENDUM (same session, after the owner asked "why do we still not have it")

**We have it. The block was never real** — three route audits searched two report
families and MISO's pre-2023 record was in a third.

| family | 2020 | 2021 | 2022 | 2023+ |
|---|---|---|---|---|
| `YYYYMMDD_da_expost_lmp.csv` (audited ×3) | 404 | 404 | 404 | **200** |
| `{YYYYMM}_da_pr_xls.zip` / `_rt_pr_xls.zip` | **200** | **200** | **200** | 404 |

A **format changeover, not a retention cutoff**: the two families are exact mirror
images, live back to at least 2015, and need no credential. Found via the source-URL
table of Zenodo deposit `10.5281/zenodo.17676746` (CC-BY-4.0), whose MISO series was
pulled from this family in November 2020.

**Verified, not assumed.** Over 2022-06 — the one month both families cover on disk —
the monthly route reproduces the committed API-sourced staging **exactly on DA
(5,760/5,760 hub-hours, max diff $0.0000)** and **5,721/5,760 (99.32%) on RT**, the 39
exceptions being five slots the report publishes as 0.0 at all eight hubs at once
(missing data, staged blank). Two conventions are handled in `fetch_miso_hub_lmp.py`
and covered by tests: the RT member is named for its **publish** date (so it carries
the prior day's market, and month-end ships in the next month's zip), and the family
is **LMP-only** (complete for every consumer — `derive_miso_hub_lmp` selects
`value == "LMP"`).

Staged: 2020 DA 366/366, 2020 RT 366/366, 2021 RT 365/365, 2021 DA **364/365**
(MISO's own October-2021 archive omits the 28th — a publisher gap).

### What the two new years show — this SUPERSEDES §2's framing

C3a by year, model vs measured, against measured MISO delivered gas:

| | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|
| gas $/MMBtu | 2.27 | 5.26 | 6.45 | 2.54 | 2.55 | 3.57 |
| model $/MWh | 28.24 | 39.57 | 53.61 | 34.63 | 32.99 | 42.87 |
| actual $/MWh | 22.99 | 40.63 | 69.87 | 32.85 | 32.30 | 45.46 |
| **C3a** | **+22.9 % FAIL** | **−2.6 % PASS** | −23.4 % FAIL | +5.4 % | +2.1 % | −5.7 % |

**The defect is a PASSTHROUGH SLOPE, and it is now measurable rather than inferred:**

```
implied slope   MODEL  4.63 $/MWh per $/MMBtu   (intercept 21.17)
implied slope   ACTUAL 8.41 $/MWh per $/MMBtu   (intercept  8.95)
                MODEL IS 55 % OF ACTUAL
corr( gas price , model error % ) = -0.841
```

The model's price is barely half as responsive to gas as the real market, and it
carries a large fixed intercept to compensate — so it **over**-prices cheap-gas years
(+22.9 % in 2020, the cheapest) and **under**-prices dear ones (−23.4 % in 2022, the
dearest). 2022 is not a special year; it is the far end of a slope error that runs
through all six.

This **unifies** with §3's coal finding rather than replacing it: a flat, gas-insensitive
coal cost sitting on the margin too often is exactly what flattens the slope and lifts
the intercept. §3's +4.3 GW coal block is the same defect at its 2022 extreme.

Two consequences for the record:
* The 2023–2025 window could not have revealed this — its gas range is 2.54–3.57, too
  narrow to identify a slope. **The two "unscoreable" years carried most of the signal.**
* One registered determination moved: `2026-09-10-miso-251-tp2020`
  **CALIBRATED-WITH-CAVEATS → NOT-YET**, which is exactly the artifact §1 predicted —
  2020 read clean *because* its price could not be checked. No non-MISO run moved.

---

## 1. Item 1 — 2020/2021 cannot be priced, and the dashboard now says so

> **SUPERSEDED BY §0 THE SAME DAY.** The conclusion below was correct about the two
> report families it examined and wrong about the world: the data was recoverable.
> Kept as written, because the reasoning that produced the wrong answer — trusting an
> exhaustive-looking audit of an incomplete search space — is the lesson.

`data/raw/lmp-data/MISO/` census: **2022, 2023, 2024, 2025, 2026 only.** No 2020/2021 partition
exists, and miso-254's exhaustive route audit
(`docs/FINDING-miso254-lmp-2020-2021-route-audit-2026-09-12.md`, 12 routes) closed every public
route the day before. `MISO_PRICING_API_KEY` — the single unblocker it names — is **not set in
this environment**. Re-confirmed, not inherited. **No proxy was synthesised.**

The real defect was in how this was *presented*:

| field | was | meaning |
|---|---|---|
| `data_blocked_years` | `[]` | means "run has no payload" — 2020/21 solved fine, so they never qualified |
| `scorable_years` | `[2020…2025]` | claims all six are scorable |
| C3a/C3b skip reason | "no model **or** actual mean LMP" | blames both sides jointly |

The model **has** a 2020/2021 price (load-weighted $28.24 / $39.57). Only the *reference* is
absent. Because the skip read as an ordinary one, **2020 reads `CALIBRATED-WITH-CAVEATS` partly
BECAUSE its price criteria could not be scored at all** — an unverifiable year presenting as
cleaner than 2022, which could be checked and missed.

Fixed, display-only:
* `calibration_verdict._no_price_reason()` names which side is absent →
  *"no measured LMP reference on disk for MISO 2020 — C3a UNSCOREABLE (reference absent, not passing)"*.
* New **reported-only** `price_reference_blocked_years`, fed by no gate, no caveat budget, no
  determination. Across all 15 registered runs it selects **exactly MISO 2020 + 2021** — the only
  price-reference-blocked years in the program.
* Status page gains a factual **Price ref** column (`none`/`yes`) + one line. No prose panel
  (rule 30 [R-TOUCHPOINT-FOLD] (a)).

**Verified: 0 of 15 runs move** on determination, reasons, grade or `data_blocked_years`.
341 scorer tests pass. The 14 failures in `tests/scoring` reproduce identically on a clean tree
(inherited, not this change).

## 2. Item 2 — it is NOT a level shift. It is a variance collapse.

RT price percentiles, model vs actual ($/MWh):

| pct | 2022 model/actual | 2023 | 2024 | 2025 |
|---|---|---|---|---|
| p1  | **34.0 / 22.8** | 22.2/12.4 | 19.0/10.9 | 27.7/16.7 |
| p25 | **44.8 / 44.4** | 30.1/22.8 | 26.4/20.2 | 35.3/26.5 |
| p50 | 51.2 / 59.1 | 34.0/27.1 | 31.0/24.6 | 39.4/32.7 |
| p75 | 59.7 / 82.8 | 37.5/33.8 | 35.2/31.5 | 44.9/43.6 |
| max | **89.4 / 1082.6** | 264.9/585.1 | 500.0/704.1 | 832.7/1782.5 |

2022's p25 matches to 1%. The bottom is **too high**, the top is **absent** — the model's entire
8,760-hour 2022 price range is $29–89 in the most expensive year on record, while 2023/24/25
reach $265/$500/$833. Reserve scarcity in 2022: **0 of 8,760 hours** (2023/24/25: 40/112/328).
Decomposition of the $18.5 mean gap: ≈ $7.9 median (merit order) + ≈ $9.3 tail (scarcity).

## 3. The cause: a flat +4.3 GW coal block, present in every hour

Model minus CAMPD coal, by decile of *actual* coal output:

| decile | 0 | 2 | 4 | 6 | 8 | 9 |
|---|---|---|---|---|---|---|
| **2021** | +7.6% | +1.4% | −0.9% | −0.8% | +0.2% | +0.5% |
| **2022** | **+25.5%** | +18.6% | +18.9% | +16.7% | +13.5% | +9.4% |
| **2023** | −4.0% | −8.5% | −11.7% | −12.4% | −11.6% | −10.9% |

2021 tracks within ±1.5%. 2022 is a **near-constant +4.3 GW additive offset across the whole
duration curve** — not a shape error, not an economics gradient. Implied coal fleet CF:

| | 2020 | 2021 | **2022** | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|
| model | 0.511 | 0.616 | **0.668** | 0.503 | 0.522 | 0.638 |
| actual | 0.517 | 0.625 | **0.562** | 0.478 | 0.550 | 0.641 |

**The model runs the 2022 coal fleet harder than that fleet has run in any year of the record.**
Direction is the tell: into the gas spike the model's coal **rose** +19.8 TWh while actual **fell**
16.7 (CAMPD gross) / 26.0 (bench net).

### What this is NOT — eliminated from committed data, zero LP

| hypothesis | killed by |
|---|---|
| coal priced too cheap | F923 per-plant receipts overwrite coal; measured MISO 2022 = **$2.248/MMBtu**, gas $6.45 model vs **$6.61** measured. Both correct. |
| a floor/must-run over-forces coal | **D-2: coal forced share 0.0016** (0.4249 of 266.01 TWh). 2021 0.0020, 2023 0.0031. The surplus is **purely economic**. |
| outage overlay missed 2022 outages | overlay declares **less** coal outage in 2022 (12.43 GW-equiv) than 2021 (12.96) or 2023 (15.46). CAMPD: 2022 online fraction **0.6536 ≈ 2021's 0.6582**; loading-when-on only −3.8%. Units were **online and backed down** — invisible to a zero-output-window derivation **by construction**. |
| the seam-price proxy | MISO's seam HR tables cover **only 2023–2025**, so 2020–22 use the forward gas-elastic proxy. But **2021 carries the largest proxy error (+$24.25, +65%) and has no coal error**, while 2022's is +$5.76 (+8%). Wrong ordering — a real defect (§6), not this one. |

## 4. The mechanism: coal has floors but no CEILING

There is **no coal fuel-supply, inventory or conservation mechanism anywhere in the model.** Coal
carries take-or-pay and must-run **floors**; nothing caps its energy. The only fuel-inventory
mechanism in the codebase is NEISO winter **oil** (`data/winter_fuel_inventory.py`). Rule 19
[R-ONE-MECH] is therefore clean: this is a missing limb, not a competing mechanism.

**2021 is not a counterexample — it is the CAUSE.** US electric-power coal stocks (MER T06.03):

| | 2020 | **2021** | **2022** | 2023 | 2024 |
|---|---|---|---|---|---|
| Jan 1 stock (Mt) | 128.1 | 131.4 | **91.9** ← record low | 88.9 | 133.0 |
| annual change (Mt) | +3.3 | **−39.5** | −3.0 | +44.2 | −5.2 |
| min days-of-burn | 79 | **45** | **48** | 81 | 90 |

2021 funded its high burn out of inventory (−39.5 Mt) and left the fleet opening 2022 at the
lowest stock in the series; 2022 could then burn only what it received (Δ ≈ 0). The model has **no
inventory state**, so it cannot represent "2021 borrowed from the stockpile and 2022 repaid it."
That single fact reproduces the whole pattern — 2021 matches, 2022 over-burns, 2023–25 match once
stocks rebuild and gas is cheap.

This is also a genuine **forecast** defect, not a backcast curiosity: a model that cannot deplete a
coal stockpile will over-predict coal in exactly the high-gas scenarios a decarbonization study cares
about.

## 5. Why NO LP was spent — the honest gate

The admissible construction (rule 13 [R-MEASURED], following the NEISO oil precedent, which
explicitly **rejected** F923 receipts as a delivered-quantity *outcome*) needs **opening stock +
delivery rate**. Setting a 2022 budget from observed 2022 burn is pinning to the actual and is
forbidden absolutely.

| need | status |
|---|---|
| MISO-footprint coal stocks, monthly | **not on disk** (`eia923_monthly_fuel_costs.parquet` carries price + receipts only; no `*stock*` file anywhere) |
| EIA API v2 | **blocked** from this session; no `EIA_API_KEY` |
| MER T06.03 national stocks | **reachable and verified** (used for §4) — but **national ≠ MISO footprint**, a rule 14 [R-ACCURATE] misalignment needing a reconciled construction, not a literal one |

So phase 0 **named** a mechanism but did not produce a **buildable** one. Per rule 29 [R-SCREEN]
nothing reached a solve. **That is the result.**

## 6. Pre-registered STOP gates for the successor (write these into its PRECOMMIT before solving)

**Screen year = 2022**, selected by the mechanism's own measured footprint census — the coal-CF gap
(0.106 in 2022; next largest 0.025 in 2023) and the stock table in §4, **both computed from fuel and
generation quantities with no reference to any price residual** (rule 29). Stated plainly: 2022 is
also the largest price residual. The selection does not use it, and the gates below are not price gates.

1. **G-FOOTPRINT** — the constraint binds in 2022 and is **inert** in 2023/24/25 (stocks rebuilt).
   Binding in a loose-stock year kills the arm.
2. **G-DIRECTION** — coal falls toward CF ≤ 0.641 (the fleet's best demonstrated year) and the
   flat +4.3 GW decile offset compresses. Overshoot below actual kills it.
3. **G-DISPLACE** — the released MWh land on gas and imports, not on slack/dump.
4. **G-NOFLIP** — no non-target load-bearing criterion goes PASS → FAIL; C1 2023–25 must not move.
5. **G-PIN** — the budget must be reconstructible from (opening stock, delivery rate) **alone**.
   If any step reads observed 2022 burn, the arm is inadmissible regardless of its gates.

The gate is a **STOP gate only** — it may kill the arm, never promote it, and it is **never scored on
C3a/C3b**.

**Prerequisite (a data-intake task, not a solve):** plant- or region-level coal stocks for the MISO
footprint. Either an `EIA_API_KEY` (EIA-923 Schedule 5 carries plant-level stocks) or a reconciled
national-shape × MISO-level anchor built through the `data-intake` contract.

## 7. Two defects found in passing — reported, NOT actioned

1. **Rule 35 [R-PROMOTE] (a) violation, inherited.** `audit_keepers --iso MISO` → **E13 × 4**: the
   miso-255 promotion left `2026-09-09-miso-250-ep-gas` and its three folded runs registered behind
   the new keeper. The keeper covers 2020–2025, which is a superset of all four, so rule 35 (c)'s
   year-union condition is met and the prune is safe:
   `python scripts/prune_iso_runs.py --iso MISO` (it will need `--force-uncite`).
   **Not run — it deletes registered runs and bundles and changes the live dashboard.**
2. **E3 warning** on the keeper bundle: `meta.json` years `[2020…2025]` vs `calibration_flags`
   years `[2023]`.

Also confirmed for the record: rule 31's claim that `check_registry_payload_parity.py` "only ever
sees committed dirs" is **false** — it enumerates via `calib_root.iterdir()`, a filesystem scan.
CI is unaffected (a fresh clone has no gitignored bundles).
