# FINDING — PJM-NEXT-31: COAL_BIT whole-unit dark hours the keeper's outage windows miss (zero LP)

Lane `PJM-NEXT-31` (branch `claude/pjm-next-31`, from `bd6516d7`). **Zero LP.** Keeper unchanged:
`2026-10-02-w0-pjm-fix2` (bundle `results/calibration/w0_pjm_span`, 2019–2025). Successor to PJM-NEXT-30, whose
§2 found that 62–89 % of the COAL_BIT derate + offline gap falls in plant-hours where at least one CAMPD unit is dark
(`opTime = 0`), outside the keeper's windows. Owner ruling (NEXT-30 §4): build the outage repair, kept on structure
even if 2023/24 regress.

§1 is committed **before** any number in §2 exists. Nothing in §1 is re-read after the probe runs.

## §1 Readings, fixed ex ante

### Keeper outage surface (from `w0_pjm_span/run_config.json`)

Three committed CAMPD unit extracts feed the keeper's COAL_BIT availability:

| layer | flag (keeper value) | file |
|---|---|---|
| long, ≥ 5 d | `unit_outage_full_rederive` + `_rederive_peaker_windows` + `_exit_cohort_repair` + `_unit_fuel_routing` (all on) | `campd-unit-outages-rederive-peakerkeep-exitfix-unitfuel-PJM.csv` |
| short, 1–5 d, coal, unit CF ≥ `SHORT_BASELOAD_CF` | `unit_outage_short_windows` (on) | `campd-unit-outages-short-rederive-PJM.csv` |
| short gas | `unit_outage_short_windows_gas` (on) | `campd-unit-outages-shortgas-PJM.csv` |

Every window passes `outage_detect.filter_revealed_outages` (PJM's EIA-930 key is present, so the net-load mask is
live): a span is kept iff it is down through ≥ `MIN_INMERIT_HOURS` local high-net-load hours, or is a full stop
(mean CF < `FULL_STOP_OVERRIDE_CF`) of ≥ `FULL_STOP_OVERRIDE_DAYS`. Windows are day-grain
(`unit_outage_window_hour_grain` off).

### Population and quantities

- **Years:** 2019–2025. **Hours:** all 8760 (or 8784), plus the NEXT-30 S2 subset `H_y` (real implied HR ≥ 10,
  `_pjmnext29_coalbit_bins.HI_HR`), so the S2 numbers line up with NEXT-30's pieces.
- **Plants:** COAL_BIT plants in the keeper's `unit_marginal_<y>`. **Units:** their CAMPD units
  (`data/raw/campd-unit-level/<ST>_<y>.parquet`, matched on `facilityId` = EIA plant code). A unit enters year `y`
  only if it has at least one hour with `grossLoad > 0` in `y`. Whole-year-dark units are excluded here; they belong to
  the exit and `campd_dark_unit_year_windows` question, which is counted separately.
- **Unit-dark hour:** `opTime = 0`, or no CAMPD row on the full-year clock (zero-filled, as the detector does).
- **Dark run:** a maximal run of consecutive unit-dark hours. Its length `L` classifies every hour in it.
- **Unit share:** `u` = the unit's annual max `grossLoad` ÷ the Σ of that over the plant's units in `y`.
- **Covered:** the unit-hour lies inside a window of any of the three committed extracts for that
  (`facility_id`, `unit_id`), expanded at day grain the way the loader expands it.
- **Reflected in model cap:** per plant-hour, `K(h)` = keeper `cap_mw` (Σ tranches), `K*` = its annual max.
  Dark MW = `K*` × Σ `u` over dark units. Model reduction = `K*` − `K(h)`. **Unreflected dark MW** =
  max(0, dark MW − model reduction). This is the dispatch-independent census quantity. It is comparable with the
  NEXT-30 `K`-twin derate + offline pieces, not with the `M` pieces.

### Classes for an uncovered unit-dark hour (ordered, first match wins)

| class | rule | what it names |
|---|---|---|
| **C0** | covered by an extract window | the window exists; any unreflected MW is a downstream routing/denominator loss |
| **C1** | `L` < 24 h | below every extract floor (the short layer's floor is 1 day) |
| **C2** | 24 ≤ `L` < 120 h, unit annual CF < `SHORT_BASELOAD_CF` | the short layer's baseload-eligibility guard |
| **C3** | 24 ≤ `L` < 120 h, eligible, and `filter_revealed_outages` (PJM mask, the committed constants) drops the run | the revealed-availability filter, short band |
| **C4** | `L` ≥ 120 h and the filter drops the run | the revealed-availability filter, long band |
| **C5** | anything else | detector-shape residue (for example, the averaged real-run rule folding < 24 h running spells into a window, or a unit-id mismatch). Reported, not chartered. |

### Forced vs economic (rule 13)

From CEMS alone a dark coal unit is either unavailable (forced/maintenance) or in an economic reserve shutdown.
The admissible discriminator is the one the committed filter already uses: **exogenous EIA-930 net load**. An
uncovered dark hour is **revealed-tight** if it falls in a local high-net-load hour (`high_load_mask("PJM", y)`).
A coal unit dark when the system is tight is revealed unavailable. The S2 flag (LMP-based) is reported as
information only. It never enters a detector rule, because the extract must stay price-free.

### Readings

| id | question | decision rule |
|---|---|---|
| Q1 | Does the census account for NEXT-30's unit-dark pieces? | Pooled 2019–21, `H_y`-mean unreflected dark MW ÷ the NEXT-30 `K`-twin (derate + offline) × its unit-dark share. **Accounts** if ≥ 0.5. Otherwise the shortfall is named: the NEXT-30 pieces are measured against revealed net output, not against unit status. |
| Q2 | Why do the extracts miss it? | Share of uncovered unit-dark MWh (unit-share weighted, `u` × `K*`) by class, in `H_y` and over all hours, pooled 2019–25 and 2019–21 separately. A class is **dominant** if ≥ 50 % in `H_y` pooled 2019–25. Otherwise the top two are named. |
| Q3 | Is the dominant (or larger) class admissible? | Its revealed-tight share (all hours). **Admissible** if ≥ 0.5: most of its dark hours fall where the unit would be called. If < 0.5, the class is mostly ambiguous with economic shutdown, and a window built on it would admit economic idling. NOT ADMISSIBLE at that grain. |
| Q4 | Is a repair chartered? | **Chartered** iff Q2's dominant (or larger) class is a detector gate (C1–C4) AND Q3 holds. The repair family follows the class: C1 → a sub-day tier under the same revealed test; C2 → the eligibility guard; C3/C4 → the in-merit test. The exact rule, its constants (none new if avoidable, each cited if not) and its ScenarioConfig field go into the PRECOMMIT after §2. If C0 dominates, the charter is a downstream routing repair instead. If C5 dominates, or Q3 fails, NOT CHARTERED, and the result goes to the owner. |
| Q5 | Which years does it move? | Per year, `H_y`-mean unreflected dark MW per MW of `K` in the Q4 class. Information only: it sizes the expected C1 delta per year (NEXT-30 expected 2023/24 to move with the fail years). |

Every Q4 branch is a routing statement. A solve follows only through a PRECOMMIT.

## §2 Result

Probe `scripts/probes/_pjmnext31_coalbit_dark_census.py` →
`results/phase0/pjm/_pjmnext31_coalbit_dark_census.json` (the fixed population). A post-hoc sensitivity,
`--coal-only` → `_coalonly.json`, restricts units to CAMPD `primaryFuelInfo` containing "Coal". It is labelled
post-hoc because §1's population takes every CAMPD unit of the facility, and gas CTs at coal facilities are dark most
of the year. The S2 hours reproduce NEXT-29/30 (`H_y` = 1368 / 976 / 1741 / 2852 / 2658 / 3721 / 3288). Of the
keeper's COAL_BIT plants, 23–39 per year carry CAMPD units with output. The rest have zero `cap_mw` all year
(retired) or are small non-CAMPD units.

**Unit-dark MWh by class, all hours, pooled 2019–25** (fixed population; coal-only in brackets):

| class | MWh | S2 fraction (base 0.271) | tight fraction (base 0.135) |
|---|---|---|---|
| C0 covered by a committed window | 945 M (960 M) | 0.236 | 0.117 |
| C1 run < 24 h | 2.7 M (2.5 M) | 0.228 | 0.094 |
| C2 1–5 d, unit below `SHORT_BASELOAD_CF` | 10.1 M (10.0 M) | 0.201 | 0.067 |
| C3 1–5 d, eligible, filter drops | 21.6 M (21.4 M) | 0.166 | 0.026 |
| C4 ≥ 5 d, filter drops | 0 (0) | — | — |
| C5 residue | 20.3 M (8.9 M) | 0.192 | 0.103 |

**Unreflected dark MW, `H_y`-mean** (fixed population; the part on uncovered units in brackets, information only):
1126 (781) / 1255 (941) / 557 (434) / 1051 (686) / 917 (268) / 502 (324) / 429 (357) for 2019–25, against `K` of
28.6 / 27.2 / 22.3 / 23.7 / 17.7 / 17.2 / 18.9 GW.

### Readings, applied as fixed

| reading | result | verdict |
|---|---|---|
| Q1 | 1.49 pooled (2019 1126 vs 661; 2020 1255 vs 580; 2021 557 vs 592). Coal-only 1.26. | **Accounts** |
| Q2 | `H_y` shares of uncovered MWh 2019–25: C5 0.385, C3 0.354, C2 0.200, C1 0.061, C4 0. In 2019–21: C5 0.472, C3 0.259. | **Mixed (C5, C3)**. Coal-only: C3 0.431, C5 0.256. |
| Q3 | Lead class C5: tight share 0.119. (C3 0.026, C2 0.067, C1 0.094.) | **NOT ADMISSIBLE** |
| Q4 | The lead class is C5, which is not a detector gate, and Q3 fails | **NOT CHARTERED** |
| Q5 | Lead-class `H_y` MW per MW of `K`: 0.023 / 0.021 / 0.011 / 0.015 / 0.004 / 0.008 / 0.005 | information |

### The Q3 threshold, and why the verdict does not hinge on it (interpretation)

Q3's 0.5 bar was set without the mask's base rate. `high_load_mask` flags 13–14 % of hours by construction, and even
the committed windows (C0) sit at 0.117, so no outage class could reach 0.5. The verdict holds under a
base-rate-relative reading as well:
- every uncovered class is *depleted* in tight hours against the 0.135 base rate, C3 most of all (0.026, a fifth of
  base);
- every uncovered class is also depleted in the S2 hours, the price-side view where coal is deepest in the money
  (0.17–0.24 against base 0.27).

Both exogenous signals, net load and price, say the same thing. The dark hours the extracts miss are where the system
does *not* need coal: slack nights, weekends and shoulder weeks. That is the economic reserve-shutdown signature, the
case the committed revealed-availability filter exists to exclude. A window built on them would remove capacity that
was economically idle, which rule 13 forbids as pinning a unit to observed operation. C3 (1–5 d stops of
`SHORT_BASELOAD_CF`-eligible units that the filter drops) is the largest coal-only class, and it is the most
slack-concentrated. So the filter is doing its job there, not missing outages.

### What the numbers say (interpretation)

- **The committed windows already carry the overwhelming majority of COAL_BIT unit-dark time.** C0 is about 95 % of
  all unit-dark MWh. The keeper's `cap_mw` already removes most of it (for example, Keystone 3136 in 2023 ran in
  about 25 % of hours, and its `cap_mw` is zero in about half of them).
- **The NEXT-30 "unit-dark share" (0.62–0.89) is not a missed-outage share.**
  - It flagged a plant-hour when *any* CAMPD unit at the facility was dark, gas CTs included. The coal-only
    sensitivity cuts C5 by 56 %.
  - The derate + offline pieces it marked are mostly ordinary partial-plant economics on top of correctly windowed
    outages.
- **Unreflected MW splits two ways.**
  - The uncovered-unit part is 270–940 MW. It is economic, per the above.
  - The covered-but-unreflected part is 120–650 MW, largest in 2023 (649 MW). That part has a window, but the model
    removes less than the unit's peak-gross share of the plant. Part of it is basis: the extract shares capacity by
    EIA-860 nameplate over the dispatched bin denominator, while this census shares it by observed peak gross. It is
    largest in a passing year, so a repair would regress 2023. It is not chartered here.
- **Where the year-discriminating operand sits.** The real fleet decommits coal across multi-day slack periods and
  the pure-LP keeper does not. That fits NEXT-30's finding that model loading sits at cap in the fail years. It is a
  commitment-economics question (rule 18: start cost and min-down by parameters), not an availability one. The
  closest adjudicated cells are `coal_sync_window_commitment_grain` (K) and `tranche_startup_amortization` (K);
  `coal_committed_nested_on_mustrun` and `commitment_floor_window_netload` are U. This lane tests none of them.

## §3 Consequence

- **NOT CHARTERED. No extract repair is built and no solve runs.** The owner's NEXT-31 ruling assumed the census
  would find forced outages the extracts miss. It finds instead that:
  - the extracts already carry about 95 % of COAL_BIT unit-dark MWh;
  - the uncovered remainder is concentrated in slack hours on both exogenous signals.

  Building a window for that remainder would admit economic shutdowns as outages (rule 13).
- **Tait 55248→2847 remap** stays parked as the rule-14 rider for the next PJM solve with a real lever.
- **Matrix:** no cell is tested and no verdict moves. The `unit_outage_*` U cells stay U: this census measures
  coverage, not those mechanisms. This lane edits no `PJM.js` cell.
- **COAL_BIT C1 2019–21 side card (a)** stays open. The availability family is now exhausted on two independent
  censuses (NEXT-13 monthly max, NEXT-30/31 hourly unit status). The remaining structural candidate is coal
  commitment economics over multi-day slack periods. The frontier text is closeout-PJM-2's.

## §4 Owner ruling (2026-10-03, decision card)

- **NEXT-32 = commitment census.** A zero-LP census of real vs keeper coal multi-day slack decommitment, testing whether
  the real fleet shuts coal across slack weeks that the pure LP keeps at cap. Candidate U cells:
  `coal_committed_nested_on_mustrun`, `commitment_floor_window_netload`. The Tait remap rides any resulting solve.
