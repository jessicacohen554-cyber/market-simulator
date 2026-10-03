# FINDING — PJM-NEXT-30: COAL_BIT in-money loading, decomposed per plant (zero LP)

Lane `PJM-NEXT-30` (branch `claude/pjm-next-30`, from `f81d0c40`). **Zero LP.** Keeper unchanged:
`2026-10-02-w0-pjm-fix2` (bundle `results/calibration/w0_pjm_span`, 2019–2025). Successor to PJM-NEXT-29, whose
post-hoc S2 re-pointed the COAL_BIT C1 operand to deep-in-the-money loading: model COAL_BIT output ÷ its available
`cap_mw` is 0.98 / 0.95 / 0.99 / 0.92 / 0.81 / 0.80 / 0.94 (2019–25), against CAMPD ÷ the same `cap_mw` at
0.90 / 0.88 / 0.91 / 0.83 / 0.78 / 0.80 / 0.89.

§1 (definitions and readings) is committed **before** any number in §2 exists. Nothing in §1 is re-read after the
probe runs.

## §1 Readings, fixed ex ante

### Population and quantities

- **Hours `H_y`:** the NEXT-29 S2 hours, real implied HR ≥ 10 (real PJM DA LMP ÷ NEXT-11 delivered gas;
  `_pjmnext29_coalbit_bins.HI_HR`). Unchanged definition, so the totals reproduce NEXT-29 S2.
- **Plants:** COAL_BIT plants in the keeper's `unit_marginal_<y>` with a bench CAMPD record (the NEXT-29 S2 set).
  Model grain is the plant (tranches summed), so "per unit" is per plant. CAMPD unit-level hourly
  (`data/raw/campd-unit-level/<ST>_<y>.parquet`) is used only for the unit-dark split below.
- Per plant `p`, hour `h`:
  - `M` = model P1 MW (Σ tranches);
  - `K` = model available `cap_mw` (Σ tranches; it already carries the keeper's outage windows and availability);
  - `A` = bench CAMPD MW (CAMPD hourly shape rescaled to the EIA-923 annual net; net basis, same as NEXT-29).
- **Revealed capability** from `A`, computed over ALL hours of the year (not only `H_y`):
  - `Y` = annual p99 of `A`;
  - `W(h)` = max of `A` over the 168-hour block of hour-of-year containing `h` (block = ⌊h / 168⌋).
- **Gap** `D = M − A`, split into four ordered pieces that sum to `D` exactly:
  1. **basis** = `M − min(M, Y)`: model output above the plant's whole-year revealed maximum. This is the cap_mw
     basis question (net vs gross, nameplate vs seasonal rating).
  2. **derate** = `min(M, Y) − min(M, W)`: above this week's revealed maximum but within the year's. These are
     partial derates and outages lasting a week or more that the keeper's windows do not carry.
  3. **offline** = `min(M, W) − A` in hours with `A = 0`: the plant is dark this hour but ran this week. These are
     short full outages, or decommitment.
  4. **loading** = `min(M, W) − A` in hours with `A > 0`: the plant is running, below this week's own maximum. This
     piece holds reserve and regulation headroom, economic backdown, and ramp or offer-curve loading.
- **Dispatch-independent twin.** The same four pieces with `K` in place of `M`. This is the capability overstatement
  that would bind if the model ran at cap. Reading R2 uses both.
- **Unit-dark split** (inside pieces 2 + 3): the share of the piece's MW-hours that falls in plant-hours where at
  least one CAMPD unit of the plant has `opTime = 0` (whole unit dark), rather than all units running at reduced
  output. Plants are matched by `facilityId` = EIA plant code; non-matching plants are reported as unmatched.
- **Reserve bound** (2019–21 only, the years with IMM rows on one basis): coal-held reserve MW =
  RTO average Tier-1 MW × the coal Tier-1 MW share, plus RTO average Tier-2 MW × the coal Tier-2 share, plus
  coal regulation MW-h ÷ 8760. Sources: `results/phase0/pjm/_pjmco_0c_som_sec10_reserve_by_unit_type.csv`
  (IMM SOM §10, cited per row).

### Readings

| id | question | decision rule |
|---|---|---|
| R1 | Which piece carries the gap? | A piece is **dominant** if it holds ≥ 50 % of Σ `D` over `H_y`, pooled over 2019–21. Otherwise the gap is **mixed**, and the two largest pieces are named. |
| R2 | Which piece separates the years? Fail set F = {2019, 20, 21, 22, 25}; pass set P = {2023, 24}. | For each piece, compute its MW per MW of `K` in each year, then take the mean over F minus the mean over P. If the `M`-based piece differs by ≥ 0.03, the piece is **year-discriminating**. Then: if the `K`-based twin also differs by ≥ 0.03, it is **level** (the real quantity differs by year); if the twin differs by < 0.03, it is **binding-only** (the same overstatement every year, consumed only when the model runs coal at cap). |
| R3 | Is the gap concentrated in a few plants? | **Concentrated** if the top-10 plants by `D` (pooled 2019–21) carry ≥ 60 % of the gap, AND the dominant (or largest) piece at those ten is the same as fleet-wide. |
| R4 | Can reserves explain the loading piece? | Compare the reserve bound with the loading piece's MW (`H_y`-mean) in each of 2019 / 20 / 21. If the bound is < 25 % of the loading piece in every one of those years, reserves are **not the operand**, consistent with closeout 0c. |
| R5 | Is there an admissible arm? | **Chartered only if** the R1-dominant (or larger mixed) piece is year-discriminating under R2 AND it maps to a measured quantity that could be produced for a forward year (rule 13). The pieces map as follows: <br>• **basis** → a rating-basis input. The candidate cells are `coal_nameplate_summer_derate` (U) and `seasonal_capacity_basis` (K, already armed). <br>• **derate** / **offline** with unit-dark ≥ 50 % → outage-window coverage. Same-year CAMPD windows are a rule-13 overlay. The `unit_outage_*` family is K, so the census must name the missing windows. <br>• **derate** with unit-dark < 50 % → `unit_partial_outage_windows`. This was screened by R-PJM 2026-09-24: the deriver emits 0 because of the revealed-outage filter, so the piece would mean a detector build. <br>• **loading** → NOT an availability defect. Pinning loading to observed output is rule-13 forbidden. Route it to the offer family (all adjudicated), so NOT CHARTERED. |

Every R5 branch is a routing statement, not a solve. If an arm is chartered, its PRECOMMIT follows this FINDING
and carries the Tait 55248→2847 remap as the rule-14 rider (closeout census §6).

## §2 Result

Probe `scripts/probes/_pjmnext30_coalbit_loading.py` → `results/phase0/pjm/_pjmnext30_coalbit_loading.json`.
The S2 totals reproduce NEXT-29 exactly (2021: M 21,684 / K 21,981 / A 20,074 MW). Clock check: CAMPD unit-level
gross against the bench, 2021, mean plant correlation peaks at lag 0 (0.986; ±1 h 0.975). Every plant matches a
CAMPD facility; none are unmatched.

**Pieces, `H_y`-mean MW** (model-based; the dispatch-independent `K` twin in brackets):

| year | H | gap | basis | derate | offline | loading | unit-dark share (2 + 3) | top-10 share |
|---|---|---|---|---|---|---|---|---|
| 2019 | 1368 | 2201 | 1084 (1200) | 470 (500) | 309 (326) | 338 (678) | 0.80 | 0.80 |
| 2020 | 976 | 1987 | 898 (1287) | 157 (205) | 368 (445) | 565 (1352) | 0.89 | 0.67 |
| 2021 | 1741 | 1611 | 280 (342) | 513 (574) | 236 (246) | 582 (747) | 0.72 | 0.80 |
| 2022 | 2852 | 2122 | 613 (874) | 539 (738) | 235 (274) | 735 (2099) | 0.79 | 0.95 |
| 2023 | 2658 | 557 | 238 (853) | 577 (888) | 82 (108) | **−340** (2103) | 0.79 | — |
| 2024 | 3721 | −84 | 122 (346) | 266 (688) | 45 (109) | **−517** (2180) | 0.62 | — |
| 2025 | 3288 | 946 | 26 (48) | 249 (368) | 148 (191) | 522 (1493) | 0.80 | — |

(The top-10 share is undefined when the year's gap is ≈ 0.)

### Readings, applied as fixed

| reading | result | verdict |
|---|---|---|
| R1 | Pooled 2019–21 shares: basis 0.367, loading 0.261, derate 0.218, offline 0.154 | **Mixed (basis, loading)** |
| R2 | Fail − pass, per MW of `K` (model-based / twin): basis +0.012 / −0.005; derate −0.008 / −0.025; offline +0.007 / +0.006; loading **+0.049 / −0.069** | Only **loading** is year-discriminating. By the rule's letter it is **level**: \|twin\| ≥ 0.03. But the twin's sign is opposite (see below). |
| R3 | Top-10 plants carry 0.756 of the 2019–21 gap. Their lead piece is loading; the fleet's is basis. | **Not concentrated** (the lead piece differs) |
| R4 | Reserve bound ÷ loading piece: 2.18 / 2.15 / 0.70 (2019 / 20 / 21) | **Cannot exclude** reserves |
| R5 | The larger R1 piece (basis) is not year-discriminating. The year-discriminating piece (loading) maps to the offer family. | **NOT CHARTERED.** No admissible availability arm. |

### What the numbers say (beyond the readings, labelled as interpretation)

- **The capability overstatement is present in every year. It is not what separates the years.**
  - basis + derate + offline per MW of `K` is 0.066 / 0.053 / 0.047 / 0.059 / 0.023 in the fail years and
    0.051 / 0.026 in 2023 / 24.
  - So the model's `cap_mw` sits about 0.5–1.9 GW above what the plants revealed they could deliver that year or
    that week. This holds in 2023/24 as well.
  - 62–89 % of the derate and offline MW falls in hours when at least one CAMPD unit of the plant is dark. These
    are whole-unit outages the keeper's windows do not carry, rather than partial derates. `unit_partial_outage_windows`
    is therefore not the arm.
- **The year-discriminator is the model's own loading, and it cancels the overstatement in 2023/24.**
  - In the fail years the model runs at weekly capability, so its loading piece is positive (+338…+735 MW).
  - In 2023/24 the model backs coal off *below* the real output in the same S2 hours (−340 / −517 MW).
  - That exactly offsets the overstatement, so the 2023/24 gap of ≈ 0 is a cancellation, not a match.
  - The real fleet's own below-capability loading (the twin) is *larger* in 2023/24 (2.1 / 2.2 GW) than in 2019–21
    (0.7–1.4 GW). Real coal is less deep in the money in those years at the same gas-implied HR, because of higher
    coal prices.
- **Consequence for any availability arm:** a rule-14 repair of the overstatement (outage-window coverage for the
  unit-dark hours, or a capacity rating basis) would cut the fail-year gap by roughly the basis + derate + offline
  share (≈ 0.75 of it in 2019–21). It would also push 2023/24 S2 energy below CAMPD by about the same per-MW-of-cap
  amount, because there the model's loading already sits below real. The two passing years would regress with the
  fail years. The arm is real structure (rule 1 would keep it in on structure), but it is not the year-discriminating
  operand. That operand is the model's merit position of coal against the price: it runs at cap in 2019–22/25 and
  backs off in 2023/24. Real coal does neither.
- **Reserves:** the IMM coal-held reserve MW (Tier-1 + Tier-2 + regulation) is as large as the 2019/20 loading piece.
  This is incidental headroom on economically loaded units (closeout 0c), and making coal hold reserve is a no-op
  or R (`pjm_reserve_pergen_sync`). It explains some of the real fleet's shortfall from capability. It is not an
  arm.
- **Basis piece by plant (2019–21 top-10):** the largest are 3140 (216 MW in 2019) and 3797 (194 MW in 2020). The
  small plants 54304, 10566 and 10043 (≈ 210–235 MW of `cap_mw` each) carry 30–90 MW each. At those plants `cap_mw`
  exceeds the annual p99 of net output. That is a rating-basis question for `coal_nameplate_summer_derate` (U;
  NEXT-22 sized the fleet max at 0.97–0.98 × net summer). It is evidence for the cell, not a verdict.

## §3 Consequence

- COAL_BIT C1 2019–21 side card (a) stays **OPEN, not a model-class limit**, and is now narrower:
  - The availability family is **not** the year-discriminating operand. NEXT-13's monthly-max verdict is extended
    to typical in-money loading, with the same conclusion.
  - A real ~0.5–1.9 GW `cap_mw` overstatement exists in every year. It is mostly whole-unit dark hours outside the
    keeper's windows, plus a rating basis at small plants.
  - Repairing it is rule-14 structure. It is expected to move every year, and to regress 2023/24 C1 unless the
    loading operand also moves.
- **The operand that separates the years** is the model's coal loading against the price: at cap in the fail
  years, below real in 2023/24. Every channel that sets the coal offer level and shape is adjudicated:
  - `offer_curve_by_group` K (including the `peak` band);
  - `coal_drop_pof` K;
  - NEXT-11/17 coal offer audit: real coal is price-flat.
- This lane adds no new evidence to those cells. **NOT CHARTERED**, and no solve.
- **Tait 55248→2847 remap (b):** no lever solve exists to carry it, so it stays parked as the rule-14 rider for the
  next PJM solve (owner card in the session report).
- **Matrix:** `coal_nameplate_summer_derate` stays U, and the basis-piece sizing is appended as evidence. No other
  cell moves.
