# FINDING — SCN-WS5B-NYISO Stage-B full horizon (2026–2050), five legs solved, five registered, **five identity gates exact**

**Lane:** SCN-WS5B-NYISO, coordinator under ruling S16, authorised by **ruling S18**
("Narrow: 6 legs × NEISO+NYISO").
**Parent:** `docs/handoffs/PRECOMMIT-scn-ws5b-nyiso-2026-09-07.md` + ADDENDUM 1–4.
**THE PIN:** `bdfb3095e9fa0cd2bec3f4e843f320b42588c72b`. **Shard checkout pin:** `4e4ad90d`
(ADDENDUM 3 — not a re-pin of THE PIN; the audited PRECOMMIT HEAD).

---

## 0. The one-paragraph result

**A quantity instrument and a price instrument are not two settings of one dial in this model, and
the campaign measured why.** NYISO's mass cap (`CAP-STATE-TIGHT`) binds **to the ton in all 25
years** and the model meets it by **shedding 31.13 % of load by 2050** rather than by
decarbonising supply — because `resolve_carbon_price()` hands the capacity-evolution screens
**0.0 $/t in every year** while the LP's own cap dual runs **$4,130–5,381/t**. The instrument
prices *dispatch* and never prices *investment*. Meanwhile the CES **premium** (`CES-P60`) reaches
the CCS retrofit screen and builds **+5,156.6 MW of nuclear and −73.7 Mt of CO2**, while the CES
**target** (`CES-T80`) — a *larger* attribute price by 2050 — moves the retrofit **not at all in 23
of 25 years and backwards in the other two**, exactly as the `ccs.py:475-476` coverage seam
predicts. Both seams were **pre-registered before the first solve** (P-6, P-3), both are
**structural**, both are **ROUTED to SCN-DESK** and **nothing under `src/market_sim/**` was
edited**.

---

## 1. Campaign status — the deliverable

**REGISTRATION IS THE DELIVERABLE, and it is complete for every leg S18 authorised.**

| leg | run id | cache key | vs PRECOMMIT §4 | solve surface | identity gate | registered | declared FAILs |
|---|---|---|---|---|---|---|---|
| `REF` | `nyiso-2026-2050-…-ref` | `f1a2ef17634b0467` | **match** | `48353917f7510af3` / 206 | **PASS** 232 sc, 0.000e+00 | ✓ | I3 |
| `CAP-STATE-TIGHT` | `…-cap-state-tight` | `462d197ef1f9e023` | **match** | `48353917f7510af3` / 206 | **PASS** 226 sc, 0.000e+00 | ✓ | I3, I12 |
| `CES-P60` | `…-ces-p60` | `ddff74e2738eaf96` | **match** | `48353917f7510af3` / 206 | **PASS** 233 sc, 0.000e+00 | ✓ | I3, I9, I12 |
| `CES-T80` | `…-ces-t80` | `fc3ad07981d95d84` | **match** | `48353917f7510af3` / 206 | **PASS** 232 sc, 0.000e+00 | ✓ | I3 |
| `ALL-CLEAN` | `…-all-clean` | `774db75da9f4d95a` | **match** | `48353917f7510af3` / 206 | **PASS** 232 sc, 0.000e+00 | ✓ | I3 |
| `CARB-MID` | — | — | — | — | — | **killed at phase 0** | — |

Every leg: 25/25 years, `error: null`. Every declared FAIL was written into
`frontend/data/hindcast/invariant-failures.json` **in the same commit as its sidecar** (the Y-24
ratchet), and after each registration:

```
scripts/check_forecast_invariants.py --sidecar-dir frontend/data/hindcast
  -> EXIT 0     (final: 188 sidecars / 2,632 records / 232 declared FAILs)
```

**Six cases exactly, no seventh leg, no rider.** `CARB-MID` was killed at **phase 0** on a proven
25-year LP-input identity with `REF` (`Σ|Δcarbon price| = 0.000000000000 $/t` over 2026–2050;
PRECOMMIT §3): under `carbon_price_path="mid"` the RFF path is dominated inside
`carbon.py:187`'s `max(program, rff_path_price(...))` by the NYISO RGGI adder in every year, so
the leg is a byte-identical re-solve of `REF`. **25 solve-years were not spent.** The substitution
question (`CARB-HI` *is* live 2031–2047) is **routed to SCN-DESK**, not actioned here — §2.1b(3)
forbids a rider, and substituting a case is the desk's call.

---

## 2. Predictions, scored as written

### P-1 (identity gate) — **CONFIRMED, 5/5 EXACT**

| leg | scalars | worst \|rel\| | verdict |
|---|---|---|---|
| REF | 232 | 0.000e+00 | PASS |
| CAP-STATE-TIGHT | 226 | 0.000e+00 | PASS |
| CES-P60 | 233 | 0.000e+00 | PASS |
| CES-T80 | 232 | 0.000e+00 | PASS |
| ALL-CLEAN | 232 | 0.000e+00 | PASS |

**1,155 scalars, worst relative deviation 0.000e+00, on all five legs.** The pre-registered WARN
band (1e-9 < |rel| ≤ 1e-6) was **never used**. Every Stage-B leg reproduces its committed Stage-A
leg's 2026–2030 sub-trajectory **bit for bit** — which is the control (G-CTRL form 4) doing its
job, and is the reason every full-horizon number below can be read as the horizon's effect and
not as drift.

### P-2 (`CES-T80` is the case the horizon transforms) — **SPLIT: the interior-year limb CONFIRMED, the "interior in every subsequent year" limb REFUTED, and the transformation is much weaker than predicted**

`CES-T80`'s `clean_region_duals`, all 25 years:

| 2026–28 | **2029** | 2030 | 2031 | 2032 | 2033 | **2034–2050** |
|---|---|---|---|---|---|---|
| 50.0 (ACP) | **10.455** | 7.049 | 14.880 | 13.832 | 20.312 | **50.0 (ACP), 17 consecutive years** |

- **First interior year is 2029** — exactly as pre-registered from Stage A G4. **CONFIRMED.**
- **"Interior in every subsequent year" is REFUTED.** The row is interior for **five years only**
  and then returns to the `federal_ces_acp_usd_per_mwh = 50.0` escape at 2034 and **stays there
  for the remaining seventeen years, including 2050 where the target is 1.00.** A 100 %-clean
  standard does not bind; it is bought out.
- **The separation from `REF` is real in fleet mix and ~nil in emissions:**

| year | ΔCO2 Mt | Δ`lw_price` | ΔVRE MW | Δnuclear MW | Δ`gas_cc_ccs` MW | Δtotal cap MW |
|---|---|---|---|---|---|---|
| 2030 | −1.60 | −2.40 | +156.6 | 0.0 | 0.0 | +156.6 |
| 2035 | −1.18 | −8.93 | +2,000.0 | 0.0 | 0.0 | +1,000.0 |
| 2040 | −0.23 | −10.21 | +2,000.0 | +1,000.0 | 0.0 | +2,000.0 |
| 2045 | **+0.06** | −10.15 | +2,000.0 | +2,500.0 | 0.0 | +2,500.0 |
| 2050 | **+0.24** | −14.49 | +2,000.0 | +3,500.0 | **−3,000.0** | +2,500.0 |

At 2050 `CES-T80` emits **18.59 Mt against REF's 18.35** — *more*. The prediction that it
"separates from REF far more than Stage A's +156.6 MW of 2030 solar" is true of **capacity**
(+2,500 MW, +3,500 MW nuclear) and **false of the thing the standard exists to change**. Reported
at full magnitude.

### P-3 (`CES-P60` and `CES-T80` are NOT one instrument at two levels) — **CONFIRMED, and more sharply than predicted**

`gas_cc_ccs` MW, all 25 years, the retrofit channel:

| year | REF | `CES-P60` | `CES-T80` |
|---|---|---|---|
| 2028 | 2,984.4 | **2,999.5** | 2,984.4 |
| 2030 | 6,255.9 | **7,890.3** | 6,255.9 |
| 2034 | 7,255.9 | **10,890.3** | 7,255.9 |
| 2040 | 7,255.9 | **10,890.3** | 7,255.9 |
| 2047 | 9,255.9 | 10,890.3 | **7,255.9** |
| 2050 | 10,255.9 | 10,890.3 | **7,255.9** |

- **`CES-P60`'s retrofit build exceeds `CES-T80`'s in every one of the 25 years** — as predicted.
- **`CES-T80`'s incremental `gas_cc_ccs` over `REF` is exactly 0.0 MW in 23 of 25 years** — as
  predicted — **and NEGATIVE (−2,000 / −3,000 MW) in 2047–2050**, which the prediction did not
  reach. The target row does not merely fail to pull the retrofit; by displacing gas-CC hosts
  with nuclear it leaves *fewer* retrofits than the reference case.
- The mechanism is the seam this lane measured in Stage A and pre-registered here:
  `ccs.py:475-476` prices the retrofit uplift as
  `effective_eac_price_for_unit = max(legacy eac, premium × credit)` and **never reads
  `clean_attribute_price_by_fuel`**, where a target-row dual lives. **The premium reaches the
  retrofit screen; the target dual cannot.**

**Ruled D-15 / S19: this lane REPORTS and does not edit `ccs.py`.** It is not edited. **The two
legs are never presented as one instrument at two levels** — that framing is refuted by this
table, and any synthesis that ranks "$60 premium" against "80 %→100 % target" as levels of one
policy is reading a coverage seam as an economic result.

### P-4(a) (`CAP-STATE-TIGHT` quantity crossing) — **CONFIRMED, inside the pre-registered band**

Pre-registered: **crossing back to a tightening at 2044, band [2041, 2050]**, "no crossing" allowed.

The cap binds exactly, so its own `co2_mt` **is** the budget. Against `REF`:

| year | budget (Mt) | REF CO2 (Mt) | posture |
|---|---|---|---|
| 2026 | 23.16 | 23.69 | tightening |
| 2027 | 22.42 | 24.59 | tightening |
| **2028** | 21.68 | 17.16 | **→ loosening** |
| 2040 | 12.80 | 11.03 | loosening |
| 2041 | 11.98 | 11.57 | loosening (0.41 Mt margin) |
| **2042** | 11.16 | 12.26 | **→ tightening** |
| 2050 | 4.60 | 18.35 | tightening (−13.75 Mt) |

**The measured crossing back to a tightening is 2042** — two years earlier than the point
estimate, **inside the band**. `REF`'s emissions turn upward at 2041 under DC load growth while
the budget keeps gliding, and the two cross the following year.

### P-4(b) (price crossing: cap dual vs the RGGI adder it replaces) — **CONFIRMED, all 25 years**

The NYISO RGGI adder is `STATE_CARBON_PRICE_BY_ISO["NYISO"][2025] = 22.09` escalated at
`RGGI_RESERVE_ESCALATION = 0.07`: **23.64 (2026) → 119.89 (2050)**. The cap dual:

| 2026 | 2027 | 2028 | 2029 | **2030** | 2040 | **2050** |
|---|---|---|---|---|---|---|
| 26.98 | 47.16 | 186.31 | 70.45 | **4,130.35** | 5,120.13 | **5,381.18** |

**Above the adder in every one of the 25 years**, as predicted, and **super-linear**: a 5.1×
step at 2030 when the budget first bites hard, then a two-decade plateau at $5,000–5,400/t —
about **45× the adder it replaces at 2050**. This is the **opposite** of the NEISO sibling's
reading (below in every year), and it is why the two ISOs' cap results must never be pooled.

### P-5 (the reliability trajectory) — **CONFIRMED on both limbs**

Pre-registered: `unserved_mwh > 0` in every year 2030→2050, non-decreasing in trend;
`gas_cc_ccs` 0.0 MW in every year of the capped case.

| year | 2030 | 2032 | 2035 | 2040 | 2045 | **2050** |
|---|---|---|---|---|---|---|
| slack, % of load | 0.97 | 3.82 | 7.09 | 14.62 | 22.89 | **31.13** |
| slack hours | 1,089 | 3,760 | 6,477 | 8,607 | 8,760 | **8,760** |
| slack GWh | 1,566.9 | 6,327.2 | 12,180.8 | 26,769.9 | 44,651.3 | **64,672.3** |
| `lw_price` $/MWh | 1,687.5 | 1,862.2 | 1,854.2 | 1,700.1 | 1,574.9 | **1,571.9** |
| `gas_cc_ccs` MW | **0.0** | **0.0** | **0.0** | **0.0** | **0.0** | **0.0** |

**Strictly increasing in all 21 years, from 1,089 hours to every hour of the year.** Stage A's
five-year measurement of `gas_cc_ccs = 0.0` under the cap **holds for the full 25** — the question
this leg was launched to answer. From 2041 the LP is short in **all 8,760 hours**, and from 2045
it is simultaneously **dumping 2.7–7.9 % of renewable potential** while shedding a quarter of
load: a pure intertemporal/deliverability signature, not a fuel shortage.

### P-6 (the seam I expect P-5 to expose) — **CONFIRMED, pre-registered and measured**

`CAP-STATE-TIGHT`'s own committed `run_config.json` reads:

```
mass_cap_enabled           True
mass_cap_program           "co2"
mass_cap_tons_by_year      NYISO: {2026: 23.16 Mt, 2030: 20.20, 2040: 12.80, 2050: 4.60}
carbon_price               0.0
carbon_price_path          "zero"
carbon_program_price_path  None
```

So `resolve_carbon_price(config, driver_year)` (`carbon.py:187`,
`max(program, rff_path_price("zero", y))`) returns **0.0 in every one of the 25 years**, and
`runner.py:2337` passes that 0.0 to `evolve_fleet` at `:2354`. **Every capacity-evolution screen —
the CCS retrofit screen, the economic-retirement screen and the new-entry screen — sees a carbon
price of ZERO, in the same year the LP's own dispatch pays a $5,381/t row dual.**

That is the whole of P-5's explanation, and it was written down before the leg solved:

- The retrofit screen values avoided CO2 at **$0/t** ⇒ `gas_cc_ccs` **0.0 MW, 25/25 years**.
- The entry screen sees no carbon scarcity ⇒ nuclear stays **flat at 3,325.9 MW for 25 years**,
  while `CES-P60` — a *price* instrument the screens can read — builds **+5,156.6 MW**.
- The fleet therefore never acquires the abatement that would let it meet the budget, and the LP,
  which *can* see the dual, satisfies the constraint the only way left to it: **it stops serving
  load.**

**A quantity instrument in this model prices dispatch and does not price investment.** That is a
structural statement about the model, not about New York policy, and it means **no `mass_cap_*`
result on any ISO should be read as a decarbonisation forecast until the seam is closed** — the
capped case's fleet is the *uncapped* fleet, operated against a binding constraint.

**ROUTED to SCN-DESK / the capx director. `runner.py` and `policy/carbon.py` are outside this
lane's regions and were not touched.**

### P-7 (`ALL-CLEAN` vs `LOAD-HI`) — **CONFIRMED as a method requirement, and the netting is now measured**

`ALL-CLEAN` bundles four arms against `REF`: `carbon_price_path` mid, `demand_growth_path` high,
`datacenter_load_path` high, `voluntary_clean_demand_path` high, plus the `CES-T80` target row.
Its correct comparator is `LOAD-HI`, which S18 does not grant at Stage B — so, exactly as
pre-registered, the netting is reported **against committed Stage-A `LOAD-HI` at the T1-F window
only**:

| year | ALL-CLEAN CO2 | LOAD-HI CO2 | **ALLC − LOAD-HI** | ALLC − REF |
|---|---|---|---|---|
| 2026 | 25.39 | 25.38 | **+0.00** | +1.69 |
| 2027 | 27.07 | 27.07 | **+0.00** | +2.48 |
| 2028 | 20.26 | 20.27 | **−0.01** | +3.10 |
| 2029 | 12.95 | 15.99 | **−3.04** | −0.76 |
| 2030 | 11.29 | 14.02 | **−2.73** | +0.39 |

`ALL-CLEAN`'s peak demand is **identical to `LOAD-HI`'s to 0.1 MW in all five years**, which is
the independent confirmation that `LOAD-HI` is the right comparator. **The clean limb's real
effect is −3.04 / −2.73 Mt at 2029–2030**; measured against `REF` it would read **−0.76 / +0.39**,
i.e. the load limb would swamp and even invert it.

**The 2031–2050 tail has no Stage-B `LOAD-HI` and is therefore reported against `REF` with the
load limb NAMED as an unnetted confound**, not silently netted: at 2050 `ALL-CLEAN` emits
**34.73 Mt vs REF's 18.35** on a peak demand of **47,576.8 MW vs 38,339.1 (+24.1 %)**. **That
+16.4 Mt is not a policy result** — it is dominated by 9.2 GW of unnetted load growth, and this
lane does not have the instrument to separate them. **No implicit netting anywhere in this
document.**

### P-8 (cost) — **REFUTED on both limbs; reported at full magnitude and as a LOWER BOUND**

Predicted ≈15–17 h total, `CAP-STATE-TIGHT` ≈5.4 h.

| leg | wall | note |
|---|---|---|
| `REF` | 116.2 min (1.94 h) | per-year 2.8–7.4 min |
| `CES-P60` | 78.7 min (1.31 h) | per-year 2.3–4.3 min — the cheapest leg |
| `ALL-CLEAN` | 205.1 min (3.42 h) | per-year 3.4–19.1 min |
| `CES-T80` | 295.0 min (4.92 h) | per-year 4.6–**36.1** min |
| `CAP-STATE-TIGHT` | **579.4 min (9.66 h)** | **this is the FINAL 5 YEARS ONLY** |
| **campaign** | **21.24 h / 125 solve-years** | **a lower bound** |

**The `CAP-STATE-TIGHT` number needs stating precisely rather than quoted flat.** Its
`per_year_perf` carries **five** rows, not 25 — 2046–2050 — and those five sum to exactly the
579.4 min total (11.5 / 141.4 / 134.2 / **171.1** / 121.2). The first twenty years came back from
cache on a resumed invocation and are not perf-recorded, **so the leg's true LP cost is materially
higher than 9.66 h and the campaign's 21.24 h is a lower bound.** Said plainly: the prediction
under-called the most expensive leg by at least 1.8×, and a single year of it (2049) cost
**171.1 minutes — more than the entire `REF` leg's 25 years**.

**Why**: a binding mass cap is a coupling constraint across all 8,760 hours, and as it tightens
the LP degenerates. This is the concrete cost basis for the charter's declared exception — a
full-horizon leg cannot be sharded by year (rule 10 `[R-ONE-PASS]` + rule 12 `[R-PARALLEL]`), so
**a leg like this cannot be made to fit rule 32 `[R-SHARD]`'s 20-minute commit**; see §4.

### P-9 (`rps_dual`) — **CONFIRMED across 125 leg-years**

`rps_dual` = **40.0000**, the `STATE_RPS_ACP["NYISO"]` escape, in **every year of every one of the
five legs** — the distinct-value set is `{40.0}` for all five. It holds **even in `CES-P60` with
+5,156.6 MW of new nuclear, +2,156.6 MW of VRE and +24.3 TWh of clean generation over `REF`**, and
**even in `CES-T80`/`ALL-CLEAN` at a 1.00 clean target in 2050**. The pre-registered exception —
"unless the target row reaching 1.00 drives the clean fleet past the RPS requirement" — **did not
occur**. The RPS row never becomes interior on NYISO at any horizon, under any arm this campaign
ran. **The campaign has measured no RPS-row response at all.**

---

## 3. The two structural findings, and the one model defect — all ROUTED, none repaired

**Nothing under `src/market_sim/**`, `scripts/**`, `configs/**` or `tests/**` was edited by this
lane.**

1. **The mass cap does not price investment (P-6).** `resolve_carbon_price` → 0.0 for every
   capacity screen under `mass_cap_enabled`. Consequence measured: 0.0 MW of CCS in 25 years, flat
   nuclear, and 31.13 % unserved load at 2050. **Affects every ISO's `mass_cap_*` scenarios, not
   just NYISO.** → SCN-DESK / capx director.
2. **The CES target dual cannot reach the CCS retrofit screen (P-3).** `ccs.py:475-476` reads only
   `max(legacy eac, premium × credit)` and never `clean_attribute_price_by_fuel`. Consequence
   measured: `CES-T80`'s retrofit is REF's in 23/25 years and *below* REF's in the other two.
   **Ruled D-15/S19 — reported, not edited.** → capx director.
3. **I9 (storage integrity) is a MODEL finding, not a scenario result** (ADDENDUM 4 §2, carried
   here verbatim in substance). `CES-P60` reaches **19.46 % of storage throughput in simultaneous
   charge+discharge from 2032**. Rule 9 `[R-EPSILON]`'s ε = 0.001 $/MWh tiebreaker exists to
   prevent exactly that and is **overwhelmed once prices go deeply negative** — when charging is
   paid more than ε, cycling against itself is profitable and the LP takes it. Trigger condition,
   stated so the owning lane can size a fix against evidence: **negative-price share above roughly
   10 % of hours** (`CES-P60` reaches 16.55 %). **ε is a registered constant and changing it moves
   every ISO's keys**, so this lane reports and routes. **It is a caution for any high-VRE or
   high-premium scenario on ANY ISO — nothing about it is NYISO-specific.** → SCN-DESK.

**Also carried forward, from ADDENDUM 3 §4** — three questions this lane deliberately did **not**
answer for itself:

4. **Should Stage-B be re-solved on the 209-row solve surface?** All five legs would have to move
   together (≈21 h+ of LP), and the 2026–2030 identity gate would then score against a Stage A
   that is itself on the 206-row surface — a gate miss would become *expected* rather than
   diagnostic. **Campaign-scope call.** → SCN-DESK.
5. **Are `F923_GAS_PRICE_PLAUSIBILITY_BAND`, `EGRID_CT_HR_PHYSICAL_FLOOR` and
   `HYDRO_BUDGET_PERIOD_HOURS_BY_PLANT` in fact INERT for NYISO?** Answering it costs a paired
   solve. **This lane has not spent one and is not asking to.** → SCN-DESK.
6. **Is a NEW registry row supposed to move a cache key at all?** capx D79's own design note says
   *"adding a table moves no key"*, because a name enters the key only when its live hash differs
   from its **frozen registration-time declaration** — and these three rows have no declaration
   yet, so the fingerprint moved and **every NYISO key moved with it**, including the committed
   Stage-A control. Either they need a `solve_surface_declared` entry (in which case this is a
   registration gap that will re-key every ISO on every future registry addition), or the
   behaviour is intended and the design note is loose. **Capx-director question**, and it affects
   **every lane holding a pin — including the NEISO Stage-B sibling.**
   `config/solve_surface*.py` was not touched.

**And one resolved against this lane's own prior work:** Stage-A §9 item 5 asked whether
`meta.set_overrides` lands as `null` on a `--set`-constructed leg. It does **not** at HEAD — it is
**absent** on the Stage-A sidecar and reads `{'federal_ces_premium_usd_per_mwh': 60.0}` on
Stage-B's `CES-P60`. **The defect is fixed at HEAD**; `SCN-FIX3` needs no action.

---

## 4. Rule-32 `[R-SHARD]` conformance — stated plainly, including where this lane did not conform

Rule 32 landed **mid-campaign** (owner, 2026-09-09), after every leg here had been launched. This
lane's position, so the desk can act on it rather than infer it:

- **(a) The parent never solved. CONFORMED.** All five legs ran in S16 shard containers; this
  coordinator ran only phase 0, the identity gates, scoring, registration and this document.
- **(c)(1) `source_revision` must be a FULL 40-CHARACTER SHA, never a branch. NOT CONFORMED, and
  the rule's stated failure mode was reproduced live.** Legs were pinned by **branch**, and
  `claude/scn-ws5b-nyiso-all-clean-pinned` was observed at `05a94743` by `git ls-remote` and then
  **gone seconds later** ("couldn't find remote ref") — auto-merged and tombstoned, exactly as
  rule 32 warns. It was recoverable only because the merge to `main` had already landed. **Rule 32
  is correct and this lane's method was not.**
- **(c)(6) forbidden actions.** Shards did **not** touch `src/`, `scripts/`, the dashboard scripts
  or the backcast namespace, and deleted nothing. But **every shard merged its own branch to
  `main`** despite instructions not to; scope was verified clean each time (two files, its own
  directory, nothing else).
- **(b) ONE SHARD = ONE COMMIT = ≤ 20 MINUTES. CANNOT BE CONFORMED FOR THIS WORK, and this is the
  measurement that says so.** A full-horizon leg is **indivisible**: rule 10 `[R-ONE-PASS]` makes
  year *Y+1*'s fleet a function of year *Y*'s solve, and rule 12 `[R-PARALLEL]` forbids parallel
  years inside an invocation — so rule 32(b)'s own remedy ("a multi-year span shards **per
  year**") is unavailable here, and its fallback ("shards launch shards") has no seam to cut on.
  `CAP-STATE-TIGHT` spent **171.1 minutes on the single year 2049** — 8.6× the 20-minute commit
  budget **for one indivisible unit of work**. **This lane raises it as a rule-collision for the
  desk and does not resolve it unilaterally**; the honest statement is that the SCN full-horizon
  track cannot satisfy rule 32(b) as written, and needs either an exemption or a different
  decomposition than "per year".

---

## 5. Retention — **THE PROMOTION QUESTION, ASKED EXPLICITLY (rule 31 `[R-RETAIN]`)**

**Nothing was deleted.** Every leg's full bundle is on local disk under
`results/scn-campaign-stageb-2026-09-07/NYISO/<CASE>/`, which is **gitignored** (`.gitignore:1441`)
— rule 31's prescribed discharge of rule 29(c), `.gitignore` and not `rm`. The committed record is
the five sidecars plus the two-file mirrors under `docs/handoffs/scn-ws5b-nyiso/<CASE>/`.

**THE DECISION IS OWED BEFORE THIS SESSION ENDS, and it will not keep.** These shard containers
are ephemeral. The bundles' `hourly/` sidecars, per-unit dispatch and duals **do not survive
reclamation**, and reproducing them costs **≥21.24 h of LP** (`CAP-STATE-TIGHT` alone ≥9.66 h).

**The question, stated so it can be answered yes/no:**

> Should any Stage-B NYISO bundle be preserved beyond its sidecar — in particular
> `CAP-STATE-TIGHT`, whose hourlies are the only artifact in which the 8,760-hour
> shed-load pattern and the cap dual's hourly formation are observable?

**This lane recommends nothing and has deleted nothing.** "Not needed in my judgement" is not a
licence to destroy evidence (rule 31, the ercot-255 incident), so the bundles stay until the owner
rules. **If no ruling arrives before the session ends, the bundles are lost with the containers**
— that is stated here rather than tidied away.

**On "keeper": there is nothing to promote, and that is not a judgement call.** A *keeper* is a
**backcast-calibration** object (rules 15 `[R-DASHBOARD]` / 22). This is a **forecast scenario
campaign**; its deliverable is registration on the **forecast** dashboard
(`docs/codebase-site/forecast-runs.html` over `frontend/data/forecast/`), which is **done for all
five legs**. `frontend/data/backcast/keepers/NYISO.json` and `calibration-complete.json` are
**outside this lane's write scope** and are untouched.

---

## 6. What this campaign changes about how Stage A should be read

This lane's own Stage-A finding is titled *"the CES premium is entry-masked at every committed
rung and reaches NYISO only through the CCS retrofit."* **Over 2026–2030 that is correct and is
not withdrawn. Over 2026–2050 it is false, and the mechanism it named is the transitional one.**

| | Stage A (2026–2030, $60) | **Stage B (2026–2050, $60)** |
|---|---|---|
| Δ VRE | +156.6 MW, at 2030 only | **+2,000 to +2,156.6 MW**, every year from 2031 |
| Δ nuclear | +500.4 MW at 2030 | **0 → +5,156.6 MW by 2050** |
| Δ `gas_cc_ccs` | +1,634.4 MW at 2030, "the channel" | peaks **+3,634.4 MW** (2034–46), **falls to +634.4** by 2050 |
| Δ CO2 | small | **−73.702 Mt cumulative**, −18.0 % at 2050 |
| Δ `lw_price` | −$13.79 at 2030 | **−$39.55/MWh at 2050** |

**The entry response was never absent — it was not yet delivered.** A five-year window ends before
COD lag, queue caps and per-tech growth limits can put steel in the ground, so Stage A measured the
**lag**, not a **mask**. **And the channel inverts**: CCS is what a premium reaches *quickly* (a
retrofit on an existing host) and dominates the first two decades; nuclear is what it reaches
*eventually*, and once it arrives it **displaces** the retrofit (Δ`gas_cc_ccs` +3,634.4 → +1,634.4
→ +634.4 MW across 2046→2047→2049 while Δnuclear runs +4,500 → +5,156.6 MW). **Reading the 5-year
window as "the premium's real channel is CCS" gets the long-run answer exactly backwards** — and
this is the strongest argument the campaign produced for why ruling S18 authorised a full horizon
at all.

**Stated without paradox:** a $60/MWh clean-attribute premium **lowers** the energy price by
$39.55/MWh at 2050, because the premium is paid on *attributes*, not into the energy market, and
the capacity it induces displaces gas on the margin. Any welfare reading must net the attribute
payment against the energy saving — **this lane does not attempt that and does not have the
instrument for it.**

---

*Parent: `docs/handoffs/PRECOMMIT-scn-ws5b-nyiso-2026-09-07.md` + ADDENDUM 1–4. THE PIN
`bdfb3095e9fa0cd2bec3f4e843f320b42588c72b`; shard checkout pin `4e4ad90d` (ADDENDUM 3). Five legs
solved, five registered, five identity gates exact, `check_forecast_invariants` EXIT 0.*
