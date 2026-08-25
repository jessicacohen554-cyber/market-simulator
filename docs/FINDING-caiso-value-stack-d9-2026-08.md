# FINDING — CAISO storage AS revenue, measured (D-9); the RA/AS reconciliation; the gap that remains

_2026-08-25 · CAISO VALUE-STACK lane (charter: `docs/FINDING-entry-signal-disarm-2026-08.md`
§5.4/§6 — "CAISO's storage miss is not signal-bound, so the CAISO queue's next rung is the
value stack — D-9's missing AS credit"; parent `docs/FINDING-entry-screen-t1h-2026-08.md`
§4/§6 D-9) · **NO LP SOLVE, NO MECHANISM ARMED, NO ScenarioConfig OR constants CHANGE.**
Phase-0 measurement only: two new measured-data intakes (OASIS PRC_AS clearing prices; the
re-fetched Daily Energy Storage Report awards), one committed probe, and arithmetic on
committed artifacts. Identification method and decision rules were pushed BEFORE any
full-year rate existed (`docs/PRECOMMIT-caiso-value-stack-d9-2026-08.md` stage 1), and the
measured value was pushed (stage 2) BEFORE any effect-on-entry arithmetic was taken._

---

## 0. The one-paragraph answer

**CAISO storage really does earn AS revenue the model credits at $0 — and the honest
number is an order of magnitude too small to close the storage-entry gap.** Measured
from CAISO's own market data (Daily Energy Storage Report battery AS awards × OASIS
PRC_AS DAM clearing prices, over the measured EIA-860 battery fleet), the CAISO
battery fleet earned **$14.82/kW-yr from day-ahead AS in 2023** (bracket 12.65–16.99),
collapsing to **$7.41 (2024)** and **$5.68 (2025)** as the fleet grew 5.5 → 13.2 GW —
CAISO's own version of the ERCOT AS saturation crash, and ~11× below ERCOT's
$169/kW-yr 2023 calibration point (rule 25 working: CAISO's whole AS market cost
$151M in 2023). The identification was pushed before the effect was computed
(precommit stages 1–2), and the effect is a **decisive negative**: adding the full
credit to the committed dual-replay margins flips **no technology's sign in any year
under any bracket** — iron-air under the duals signal comes closest, −$3,388/MW-yr
(2.4 % of its annual cost) in 2025 — so the charter's stop rule applies: the value
stack with an honest AS credit still does not restore CAISO storage entry, and the
residual now sits in the entry signal's construction (the named forward-expectation
rung) and the storage cost basis (L-6 / D-4; iron-air's capex itself carries
`verified=0`), not in any missing revenue stream this lane may add. The measured rate
and reference fleet are delivered as the registry-ready CAISO row (owner's arming
decision); nothing is armed here.

---

## 1. What the model credits CAISO storage today — re-verified at HEAD

| claim | verified |
|---|---|
| `as_revenue_enabled` defaults **False** | `scenarios.py:3157` |
| `AS_REVENUE_PER_KW_YR_BY_ISO` is populated for **ERCOT only**; a commented-out `"CAISO"` slot names the intended intake source | `capacity_market.py:2771-2775` |
| omitting AS "undervalues storage ~6x" is the module's own ERCOT statement | `ancillary.py:9-10` |
| in the registered CAISO T1-H posture, **nothing** prices storage AS: `caiso_reserve_coopt=False`, `energy_reserve_coopt=False`, `as_revenue_enabled=False`; the RA leg **is** armed (`storage_capacity_value=True`) | `results/hindcast/caiso-2021-2025-realized/run_config.json` |
| the RA leg mechanics reproduce: iron-air capacity value = 88,080 $/MW-yr at zero fleet (the committed break-even table) and 77,725 at a 2.0 GW screen-time fleet (the dual-replay artifact's 77,611 ↔ ~2.02 GW), annual cost 138,859 exact | `estimate_capacity_value` / `compute_storage_annual_cost`, re-executed at HEAD |

D-9 is confirmed as a **posture** finding: the registry is honest about being ERCOT-only,
and its own intake note (`capacity_market.py:2754-2775`) specifies exactly what a CAISO
entry requires — a measured AS-market revenue at a reference-fleet year plus the reference
fleet, which is what this lane produces.

## 2. The measurement

### 2.1 Data, all CAISO's own, all on this branch

* **Awards** — the 12 quarterly Daily Energy Storage Report xlsx re-fetched from caiso.com
  (BLOAT-S2 recovery route), **all 12 sha256-identical to the tracked `SHA256SUMS.txt`
  identity record**, curated through the frozen schema seam
  (`scripts/data/curate_storage_as_awards.py`). Hourly IFM/RTPD award MW by product
  (RU/RD/SR/NR) for battery (LESR) + hybrid (HYBD).
* **Prices** — NEW intake: OASIS `PRC_AS` DAM hourly clearing prices per AS region and
  product, 2023–2025 (`data/raw/CAISO-AS/asprc_ALL_*.csv`; OASIS caps this queryname at
  one trade day per request — measured, documented in the CAISO-AS README — hence 1,096
  day files). CAISO's nested AS regions publish per-constraint shadow-price
  *contributions*; a resource's settlement ASMP is the sum over its containing regions.
* **Requirement weights** — the sub-regional NP26/SP26 regional-minimum floors from the
  AS_REQ series already on disk. Measured to be exactly symmetric north/south
  (identical MW floors), so the CENTRAL bracket's adder weight is 0.5/0.5 — a measured
  symmetry, not a fallback.
* **Fleet denominator** — measured EIA-860 CAISO battery fleet via the model's own loader
  (monthly vintage ramps, li-ion only): average 5,517 MW (2023), 9,267 MW (2024),
  13,161 MW (2025) (year-end 7,492 / 11,131 / 15,448).

The award series reproduces the DMM-published battery AS procurement to ~1–3 %: DAM
all-product hourly mean 1,031 MW (2023, DMM ~1,040) and 1,501 MW (2024, DMM ~1,500).

### 2.2 The measured CAISO battery AS revenue

| year | DAM battery AS revenue ($M, central [low–high]) | fleet avg (MW) | **rate ($/kW-yr, central [low–high])** |
|---|---|--:|--:|
| **2023** | 81.8 [69.8–93.8] | 5,517 | **14.82 [12.65–16.99]** |
| 2024 | 68.7 [59.6–77.8] | 9,267 | 7.41 [6.43–8.40] |
| 2025 | 74.8 [48.4–101.2] | 13,161 | 5.68 [3.67–7.69] |

The product structure (artifact `results/calibration/caiso_storage_as_revenue_phase0.json`):
**regulation is the market** — reg-down is the largest line every year ($46.9M/$41.0M/$58.4M
central), reg-up second; spin+nonspin together are $5.7M/$8.9M/$2.6M. 2025's wider bracket
is the NP26 sub-regional adders (RU +$2.12, RD +$4.22 mean) — a north-side locational AS
premium emerging as south-heavy batteries saturate the south.

Bracket semantics (rule 14 `[R-ACCURATE]`, documented misalignment): the award series is
system-level, so the sub-regional adder an awarded MW earns is unobservable; LOW applies
the smaller of the NP26/SP26 adders to every MW, HIGH the larger, CENTRAL the
requirement-share weighting (measured to be exactly 0.5/0.5 — CAISO's regional-minimum
floors are north/south symmetric). The LOW→HIGH span is $1.97–4.34/kW-yr depending on
year — far below every remaining entry margin in §5.

Two omissions, both conservative (the true AS revenue can only be LARGER): the real-time
incremental leg (RTPD awards settle incrementally at RT prices; RTM award means sit
within ~3 % of DAM for both regulation products, while spin runs 10–56 % higher in RT at
$0.8–3.5/MW system prices — a small omitted increment) and regulation mileage (RMU/RMD
payments on top of capacity; no mileage award MW exists in the DESR).

### 2.3 Cross-validation against the DMM's own revenue accounting

The DMM Special Reports on Battery Storage give battery **net market revenue** of
$103/kW-yr (2022) → $78 (2023) → $53 (2024), with energy = ~62 % (2023) / ~82 % (2024)
of net revenue and real-time bid-cost-recovery = 7 % / 4 %. The non-energy, non-BCR
remainder — an UPPER bound on AS capacity revenue, since it also carries the "other"
settlement bucket — is ≈ **$24.1/kW-yr (2023)** and ≈ **$7.4/kW-yr (2024)**.

The measurement passes on both legs: 2023's central $14.82 sits comfortably below its
$24.1 bound (the gap is the "other" bucket, mileage, and the RT increment — the known
omissions); 2024's $7.41 equals its $7.4 bound within the rounding of the DMM
percentages; and the measured 2023→2024 collapse (rate ratio 0.50 at fleet ratio 1.68)
reproduces the DMM-reported decline. For 2025 no DMM special report exists yet;
Modo Energy's 2025 tracking (merchant revenues ~24 % below 2024 through Q3 on a fleet
that grew 11.2 → 14.7 GW) is directionally consistent with the measured $5.68.

### 2.4 The saturation shape — CAISO reproduces the ERCOT crash, from its own data

The per-kW rate halves as the fleet grows 1.68× (2023→2024) and falls another 23 % as
it grows 1.42× more (2024→2025). The implied decline exponents are **1.34** and
**0.76** — real saturation, but milder than the shared
`ERCOT_AS_SATURATION_EXPONENT = 2.5`. Per the pre-registered decision rule this is
**reported and escalated, not refit**: keeping the shared 2.5 under-credits AS for any
model fleet past the 5.52 GW reference (conservative in exactly the direction that
cannot manufacture storage entry), and a CAISO-specific exponent would be a new DOF
needing its own identification. **Owner question, stated once:** whether to keep the
shared exponent (conservative) or intake a CAISO-measured one from these three points
(2 DOF spent on 3 observations — thin). This lane recommends keeping 2.5 until a
longer CAISO series exists.

## 3. Rule-13 admissibility

The proposed input is `{"CAISO": {"storage": <rate>}}` + `AS_SATURATION_REF_GW_BY_ISO["CAISO"]`
— a measured AS-market revenue rate at a measured reference fleet, exactly the ERCOT
pattern. The admissibility test (could this quantity be produced for a forward year from
forward drivers, and would it respond to changed conditions?): **yes on both** — the
forward value regenerates as `base × (ref / max(fleet, ref))^k` from the model's own
evolving AS-eligible fleet, collapses as the fleet grows (the measured 2023→2025 CAISO
behaviour), and no measured *outcome* of any backcast year enters any solve path. What
would NOT be admissible — and is not done — is choosing the rate to close the 15,147 MW
storage gap: the rate was identified from AS market data alone and pushed (precommit
stage 2) before the entry-gap arithmetic below was computed.

Rule 25 `[R-ISO-SCOPE]`: nothing is scaled from or anchored to ERCOT's $169/kW-yr. The
CAISO rate is ~an order of magnitude smaller, from CAISO's own market — that divergence
is itself the headline (CAISO's AS market is shallow: total AS cost $151M in 2023, all
resources, per DMM 2023 annual report).

## 4. Rule-19 reconciliation — what already credits CAISO storage, and where the seams are

Enumeration of every mechanism crediting storage in the CAISO T1-H entry screen
(`apply_storage_new_entry`, margin = arbitrage + capacity_value + as_revenue − cost):

1. **Arbitrage** (`estimate_storage_revenue` on the entry price signal) — energy only.
   Currently ≈ $0 for CAISO (D-8's shapeless signal; the L-1 duals replay closes 63–85 %
   of iron-air's requirement and still falls short).
2. **RA capacity value** (`estimate_capacity_value`) — the CPM-soft-offer-cap anchor
   (88.08 $/kW-yr) × duration-ELCC × penetration derate. **This is a payment for the RA
   attribute, not for AS**: CAISO's RA design is a bilateral obligation market in which
   the seller retains all market revenues — the DMM's own battery revenue accounting
   treats RA contract revenue as a *separate, additive* stream to market (energy + AS)
   revenue, and the anchor object itself (the CPM soft offer cap) is a going-forward
   fixed-cost construction, not an E&AS-netted CONE. No dollar of the measured AS revenue
   in §2 flows through an RA contract: §2's numerator is exclusively the four AS products'
   capacity awards at their ASMPs. **There is no shared dollar between legs 2 and 3.**
3. **AS revenue** (`as_revenue_per_mw_yr`) — currently $0 for CAISO (no registry row).
   The §2 rate is the honest value of this leg. With no reserve co-optimization of any
   kind in the CAISO forecast lane (§1), this exogenous credit would be **THE single AS
   pricing** for CAISO storage entry; the module's endogenous-flag suppression seam
   (`ancillary.py` docstring) already reconciles any future co-opt arming, exactly as it
   does for ERCOT.

The one genuine overlap is **legs 1↔3** (a MW-hour reserved for AS cannot simultaneously
arbitrage), and it is bounded and second-order: the measured DA upward-product awards
average 446 / 745 / 844 MW (2023/24/25) — 8.1 % / 8.0 % / 6.4 % of fleet power — and by
the market's own co-optimization a battery clears AS only when the AS price weakly
exceeds its energy opportunity cost, so the arbitrage forgone on those MW is bounded
above by the AS revenue itself. (Reg-down, the largest award line, reserves charge-side
headroom and does not displace discharge arbitrage at all.) At the current gap
magnitudes (required arbitrage $50.8–212k/MW-yr vs a credit of order $15k), the
compound error cannot change any sign below.

**Not re-tested (DO-NOT-REDO):** the backcast dispatch-side AS-award family —
`caiso_storage_as_reservation`, probe-adjudicated INERT at caiso-74 and refuted by
arithmetic at caiso-127/129 — is a *different phenomenon* (withholding measured award MW
from backcast dispatch headroom) in a *different lane* (backcast dispatch overlay). This
lane touches neither that flag nor its adjudication; a forecast-lane revenue credit and a
backcast dispatch reservation share data, not a mechanism.

## 5. The gap that remains — computed only after the stage-2 precommit was pushed

The committed CAISO dual-replay ledger
(`results/calibration/entry_signal_l1_dual_replay_caiso.json`) already carries the
missing leg explicitly — `as_revenue_per_mw_yr: 0.0` on every tech row. Adding the
identified credit **A = 14,820 $/MW-yr** (the §2 CENTRAL rate × 1000; at the
screen-time fleet of 2,022 MW, below the 5.517 GW reference, the saturation factor is
exactly 1.0, so the full base applies) to the committed margins:

| tech | arm | margin ($/MW-yr), committed | + AS credit | sign |
|---|---|--:|--:|:--|
| iron_air | shipped 2024 | −61,248 | −46,428 | − |
| iron_air | duals 2024 | −29,230 | −14,410 | − |
| iron_air | shipped 2025 | −59,285 | −44,465 | − |
| iron_air | duals 2025 | −18,208 | **−3,388** | − (2.4 % of cost) |
| li_ion_4hr | duals 2024 / 2025 | −72,757 / −77,330 | −57,937 / −62,510 | − / − |
| compressed_air | duals 2024 / 2025 | −52,579 / −46,262 | −37,759 / −31,442 | − / − |

**No sign flips — in any year, under any arm, at any bracket.** At HIGH
(A = 16,990) iron-air-under-duals-2025 is still −1,218; at LOW (12,650) it is −5,558.
Even at the DMM AS+other CEILING ($24.1k — deliberately overstated, it includes
non-AS settlement buckets), exactly one cell would flip (iron-air, duals, 2025,
+5,892) and nothing else moves. Under the SHIPPED signal — the configuration the
T1-H lane actually runs — every tech remains $44–97k/MW-yr short. **Per the
charter's stop rule, that is the result: the honestly-identified AS credit does not
restore CAISO storage entry, and this lane stops here.**

Two structural notes that belong to this result rather than to any future lane:

* **The credit is self-limiting in exactly the right way.** The screen's saturation
  driver is the model's own AS-eligible fleet; had the model built the real fleet
  (9.3 GW average 2024, 13.2 GW 2025), the credit would collapse to
  base × (5.517/13.2)^2.5 ≈ 11 % of base — the same collapse the real market
  delivered (§2.4). An entry loop that builds storage kills the AS credit for later
  entrants, so this lever can never become a perpetual-motion storage builder.
* **The bracket does not matter at gap scale.** The LOW→HIGH span of §2.2 is
  $1,970–4,340/MW-yr — far below every remaining margin above.

## 6. The next rung, named and NOT run

Unchanged from the disarm finding §6, now with its missing quantity measured: **the
forward-expectation object — an entry signal that is locational AND forward-looking —
carrying the §2 AS credit as the third leg of the stack.** The measured decomposition
of iron-air's stack (RA 77,611 + duals-arbitrage 32,018–43,040 + AS 14,820 against
cost 138,859) says CAISO's frontier storage tech is within **2.4 % (2025) / 10.4 %
(2024)** of break-even under a real price signal and the honest value stack — and it
still does not clear. What now separates iron-air from entry is smaller than the
declared uncertainty of its own cost basis: its $2,000/kW capex carries `verified=0`
(primary source unreachable at citation time), and the L-6/D-4 cost-specification
repairs (per-tech life, `resolve_real_discount_rate`) move long-duration costs by more
than the residual — **which is why the cost basis, not another revenue stream, is
where the remaining distance lives.** The decision to intake the CAISO AS row
(registry entry + reference fleet, default-off behind `as_revenue_enabled`) is the
owner's; this lane delivers the identification and recommends the row be added so the
forward-expectation rung can test the full stack rather than re-deriving the AS leg
mid-lane. What this measurement does NOT license: any CAISO signal disarm (a later
rung, per the charter), any arbitrage-term adder (L-4 stays an open root-cause issue,
rule 21), and any reordering of L-3 before L-6 (L-3 must still land first — L-6 makes
long-duration storage cheaper and would push further toward iron-air/flow without the
availability-year gate).

## 7. Rule compliance

- **Rule 1 `[R-STRUCT]`** — no number is reached through an unreal mechanism; the credit
  is a real revenue stream measured from the real market, and its failure to close the
  li-ion gap is reported as the result, not repaired.
- **Rule 5/24 `[R-NO-MAGIC]`/`[R-REGISTRY]`** — nothing lands in this lane; the proposed
  landing shape is the existing registry (`AS_REVENUE_PER_KW_YR_BY_ISO` +
  `AS_SATURATION_REF_GW_BY_ISO`), cited values, no new channel.
- **Rule 13/21 `[R-MEASURED]`/`[R-DOF]`** — §3; method and decision rules pre-registered
  (precommit stage 1), value pushed before effect (stage 2).
- **Rule 14 `[R-ACCURATE]`** — measured data used throughout; the two genuine
  misalignments (system-level awards vs regional prices; DA-only leg) are documented and
  bracketed/bounded, never buried in an estimate.
- **Rule 19 `[R-ONE-MECH]`** — §4: one AS pricing, no RA/AS shared dollar, the 1↔3
  overlap bounded.
- **Rule 22 `[R-HOLDOUT]`** — no solve of any kind; all data intake is train-years
  2023–2025; no out-of-training year touched, no marker consulted, nothing scored.
- **Rule 25 `[R-ISO-SCOPE]`** — no ERCOT value reused, scaled, or anchored to.
- **Rule 26 `[R-MECH-MATRIX]`** — no mechanism tested, no cell verdict moves; the
  phase-0 evidence is appended to the CAISO shard's `storage_entry_value_stack` cell note
  in this session (measurement-evidence append, the caiso-218 pattern).
- **Rule 27 `[R-PUSH]`** — every ≥300-line file pushed was blob-verified (line count +
  sha256) after push.
- **Out of scope, untouched:** every keeper shard, `calibration-complete.json`,
  `holdout-freeze.json`, both dashboards' registries, `results/calibration/caiso217_crosswalk`
  (the documented registration debt — deprioritized by owner decision, not touched),
  L-2/L-3/L-4/L-6, and `.github/workflows/`.

## 8. Reproduction

```
# raw price intake (OASIS caps PRC_AS at 1 day/request; ~1,096 requests, resumable)
python3 scripts/data/fetch_caiso_oasis.py --datasets asprc --years 2023 2024 2025 --window 1

# awards: re-fetch the 12 DESR xlsx (see data/raw/storage-as-awards/CAISO/README.md),
# verify against SHA256SUMS.txt, then curate
PYTHONPATH=. uv run python scripts/data/curate_storage_as_awards.py --isos CAISO

# the measurement
PYTHONPATH=. uv run python scripts/probes/caiso_storage_as_revenue_phase0.py \
    --out results/calibration/caiso_storage_as_revenue_phase0.json
```

The probe hard-fails on incomplete price coverage (no partial-year rate can be reported),
and the committed artifact `results/calibration/caiso_storage_as_revenue_phase0.json`
carries every number in §2.
