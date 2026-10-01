# FINDING — NWPP-13: the WEIM price index — **NO**. The series builds cleanly and WEIM clears 5.5–6.2 % of the footprint's energy, but the WEIM on-peak price sits 22.6–37.5 % below the Mid-C Peak index, every year, against a pre-registered 10 % bar. Nothing landed to `_validation-source`.

**Lane** NWPP-13 · **Model** Fable (`claude-fable-5-1`) · **Date** 2026-09-13 ·
**Branch** `claude/nwpp-13-weim-price-index-3pp1a8` · **Base** `4d9c3251` · **Data profile** `shared` ·
**PRECOMMIT** `docs/handoffs/PRECOMMIT-nwpp-13-2026-09-13.md` (pushed at `715fff9d` before any value was
read) · **Ruling** card N2, both limbs · **Raw store** `data/raw/nwpp-weim/` (README, SOURCES, SHA256SUMS,
`gate.json`, `d2_tie_reconciliation.json`) · **Builder** `scripts/data/build_nwpp_weim_price_index.py`.

## 0. Verdict and the volume share, first

**VERDICT: NO** — gate D3 (reconciliation against the independent Mid-C Peak index) fails in every year:
the NW-group WEIM on-peak price averages **−37.5 % / −22.6 % / −23.6 %** (2023 Jun–Dec / 2024 / 2025)
against the Mid-C single-day weighted-average price, with daily correlation **0.74 / 0.95 / 0.67**; the
pre-registered bars were ±10 % and ≥ 0.80. D1 (coverage), D2 (volume share) and D4 (sanity) pass.
No bar was moved after the series was seen.

**THE WEIM VOLUME SHARE** (the number the charter deliberately did not guess): WEIM's settled
cross-BAA transfer energy for the 11 footprint WEIM BAAs, as a share of the 17-BA footprint demand,
on the BAA net-position basis the PRECOMMIT declared —

| year | gross |net transfer|, 11 BAs | 17-BA footprint demand | **share** | share of 11-BA demand | bar |
|---|---:|---:|---:|---:|---:|
| 2023 (Jun 1 – Dec 31) | 9,411.7 GWh | 166,329.5 GWh | **5.66 %** | 5.90 % | ≥ 5 % ✓ |
| 2024 | 16,149.0 GWh | 291,343.6 GWh | **5.54 %** | 5.78 % | ≥ 5 % ✓ |
| 2025 | 18,035.5 GWh | 293,366.9 GWh | **6.15 %** | 6.41 % | ≥ 5 % ✓ |

On the published **pairwise-gross** basis (CAISO's Appendix 2, 2023-07 → 2025-12) the same flows are
**10.6 %** of footprint demand (the net basis over the same months: 5.78 %). Both bases exceed the bar;
the PRECOMMIT's declared quantity is the net one, and it is the lower bound (§2.2). WEIM is not a thin
market here — that was not the problem. The problem is what its price *is* (§3).

The gate is a STOP gate. It refused the series; it promoted nothing; it read no model residual (none
exists). A NO is a successful outcome of this lane, and card N2 limb (b) — a run reads a determination
naming its own basis, never a bare `CALIBRATED` — is the ruled fallback.

## 1. What was built (all committed under `data/raw/nwpp-weim/`)

| artifact | rows | what |
|---|---:|---|
| `weim_rtpd_lmp_15min.parquet` | 1,088,688 | `PRC_RTPD_LMP` at the 12 `DEPZ` nodes `ELAP_<BAA>-APND`, 2023-06-01 07:00 UTC → 2026-01-01 07:45 UTC, all four components (`lmp, mce, mcc, mcl`) |
| `weim_transfer_15min.parquet` | 2,083,676 | `ENE_EIM_TRANSFER` v2 RTPD, all 23 WEIM BAAs |
| `weim_hourly_by_ba.parquet` | 315,360 | the per-BA hourly LMP on the model's fixed-PST non-leap clock, 3 years × 8,760 × 12 — **the per-BA product** card N5's zones re-group |
| `midc_peak_daily.parquet` | 698 | `Mid C Peak` rows of the 2023/2024/2025 ICE workbooks (529 single-day) |
| `weim_benefits_appendix2_transfers.csv` | 4,922 | Appendix 2 of the 12 quarterly benefits reports, 2023-07 → 2025-12, per month × ordered pair, with report + page |
| `gate.json` / `d2_tie_reconciliation.json` | — | every measured cell; the D2 definitional reconciliation |

The fetch: OASIS retention edge measured at fetch time (walk-back probe) — **no data ≤ 2023-05-31, data
from 2023-06-01**, identical for both products. 31 monthly LMP windows, 12 nodes per call, **every one
returned exactly its expected row count** (nodes × days × 96 × 4; the multi-node truncation
`fetch_caiso_oasis.py` documents for `PRC_LMP` did not occur for this product). One grammar fact
learned and encoded: OASIS's "31 days only" limit (`ERR 1004`) counts **local** calendar days, so
windows are cut at Pacific-prevailing midnight. The raw pulls (916 MB) are not committed; the parquets
are the durable record, because an anonymous re-fetch after ~2026-10 cannot reproduce 2023 at all.

## 2. The gate table — PRECOMMIT §5, filled in

### 2.1 D1 — coverage: PASS (with 2023 partial by retention, as declared)

| leg | bar | measured | |
|---|---|---|:--:|
| D1.1 per-node coverage inside the served window | ≥ 95 % | **100.0 %** for all 12 nodes in all three years | ✓ |
| D1.2 footprint hours 2024 / 2025 (model clock) | ≥ 8,322 | **8,760 / 8,760** | ✓ |
| D1.3 footprint hours 2023 | ≥ 4,380 | **5,137** (58.6 % of the year; Jun 1 – Dec 31) | ✓ |

The 90 %-weight rule never fired (0 hours); no BA has a NaN hour inside the served window; the only NaN
in `weim_hourly_by_ba` is 2023's retention head (3,623 hours per BA). **2023 remains a PARTIAL year**
and is scoreable only on the scorer's masked path — moot now that nothing is landed.

### 2.2 D2 — the WEIM volume share: PASS, after the pre-declared reconciliation

Shares as in §0. The **cross-check** the PRECOMMIT required — OASIS-summed volume vs the reports'
published volume within ±10 % — **failed literally**: 42,123.5 GWh (OASIS, Σ|net|) vs 77,256.1 GWh
(Appendix 2, pairwise gross), ratio **0.545**. The PRECOMMIT said that a miss means *"the OASIS quantity
is not what this document says it is, and the lane stops to reconcile before D2 is scored"*. It was
reconciled, and the reconciliation is a measured identity, not an argument:

| identity (July 2024, one month of `ENE_EIM_TRANSFER_TIE`, per tie × direction × pair, 2,900,672 rows, 0 duplicates on the six-field key) | tie-level | comparator | ratio |
|---|---:|---:|---:|
| **gross**: Σ tie MW × 0.25 h per BA vs Appendix 2 (from = BA) + (to = BA), 11 BAs | 2,917.0 GWh | 2,789.2 GWh | **1.046** ✓ |
| **net**: Σ_intervals \|Σ I − Σ E\| × 0.25 h per BA vs the store's Σ\|EIM_XFER_MW\| × 0.25 h | 1,494.0 GWh | 1,471.4 GWh | **0.985** ✓ |

So `ENE_EIM_TRANSFER` is each BAA's **net transfer position per interval** and Appendix 2 is the
**pairwise gross per direction**; the 0.545 is Σ|net| / Σ gross, i.e. the netting of simultaneous imports
and exports across different ties. Per BA the gross identity holds within ±6 % for 10 of 11 (SCL 1.002,
TPWR 1.001, NWMT 1.004, PACE 1.016, NEVP 1.022, AVA 1.022, IPCO 1.025, PSEI 1.025, PACW 1.036, PGE
1.057); **BPAT reads 1.32 and is unexplained** — no wheel-through rows exist in the tie product to
account for it, so it is a BPAT-specific accounting difference between the two CAISO publications,
reported and not absorbed. The per-interval store-vs-tie-net correlation is 0.998 (store sign convention
is export-positive). D2 is therefore scored on the pre-declared net quantity and passes; the published
gross basis (10.6 %) would pass by more. Stated limitation, unchanged from the PRECOMMIT: neither basis
counts the intra-BAA imbalance energy WEIM dispatches, which is not published per BAA — the share is a
lower bound.

### 2.3 D3 — reconciliation against Mid-C Peak: **FAIL, every year**

Construction exactly as pre-registered: single-day `Mid C Peak` rows (185 / 171 / 172 per year; the
59 / 55 / 55 multi-day package rows excluded); per delivery day, the NW-group (`BPAT PSEI SCL TPWR`,
demand-weighted) simple mean over HE07–HE22 Pacific prevailing time, all 16 hours present; the anchor's
weekday census is Mon 134 · Tue 139 · Wed 140 · Thu 88 · Fri 4 · Sat 24 · **Sun 0** — an on-peak
product, as the definition says.

| year | n days | bar n | WEIM NW on-peak mean | Mid-C Peak mean | **level gap** | bar | daily corr | bar | MAE | |
|---|---:|---:|---:|---:|---:|---|---:|---|---:|:--:|
| 2023 (Jun–Dec) | 108 | ≥ 60 | $56.28 | $89.98 | **−37.5 %** | ±10 % | 0.737 | ≥ 0.80 | $35.42 | ✗ |
| 2024 | 171 | ≥ 100 | $43.94 | $56.77 | **−22.6 %** | ±10 % | **0.949** | ≥ 0.80 | $16.50 | ✗ (level) |
| 2025 | 172 | ≥ 100 | $36.74 | $48.08 | **−23.6 %** | ±10 % | 0.670 | ≥ 0.80 | $12.92 | ✗ |

Diagnostics (not gated): `ELAP_BPAT` alone −37.4 / −21.0 / −22.3 % (corr 0.78 / 0.95 / 0.66); the whole
footprint −43.7 / −30.2 / −30.8 %. The sign is the one the PRECOMMIT expected (RT imbalance below the DA
bilateral index); the magnitude is two to four times the bar.

**The defect screen — why this is a measurement and not a construction error.** (i) The prevailing-hour
diurnal profile of the NW-group price is physical: trough at 02:00 ($34.9), evening peak at HE20 ($49.7),
morning shoulder at HE07–08 ($41.5); the on-peak block averages $42.69 against $38.07 off-peak, so the
clock and the block are right. (ii) The gap is persistent, not event-driven: WEIM is below Mid-C on
**88.7 %** of delivery days; the daily ratio's quartiles are 0.62 / **0.75** / 0.90; dropping every
scarcity day (Mid-C ≥ $100, 39 days) leaves **$37.81 vs $49.32 = −23.3 %** over 412 days. (iii) It
is present in 29 of 31 months (exceptions Nov-2024 +9 %, Dec-2025 +4 %) and largest in summer:

| month | n | WEIM | Mid-C | gap | corr | month | n | WEIM | Mid-C | gap | corr |
|---|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|
| 2023-06 | 14 | 32.5 | 52.5 | −38 % | 0.67 | 2024-10 | 16 | 45.8 | 56.8 | −19 % | 0.68 |
| 2023-07 | 17 | 64.9 | 97.2 | −33 % | 0.23 | 2024-11 | 10 | 40.9 | 37.5 | +9 % | 0.74 |
| 2023-08 | 18 | 58.3 | 155.6 | −63 % | 0.98 | 2024-12 | 13 | 41.2 | 47.7 | −14 % | 0.83 |
| 2023-09 | 15 | 40.5 | 61.3 | −34 % | 0.63 | 2025-01 | 16 | 43.7 | 52.6 | −17 % | 0.70 |
| 2023-10 | 18 | 73.3 | 96.6 | −24 % | 0.87 | 2025-02 | 14 | 53.6 | 78.3 | −32 % | 0.55 |
| 2023-11 | 13 | 67.4 | 83.4 | −19 % | 0.93 | 2025-03 | 18 | 28.4 | 37.8 | −25 % | 0.82 |
| 2023-12 | 13 | 51.2 | 60.4 | −15 % | 0.82 | 2025-04 | 16 | 20.8 | 27.9 | −25 % | 0.15 |
| 2024-01 | 16 | 134.5 | 164.5 | −18 % | 0.96 | 2025-05 | 13 | 28.6 | 39.1 | −27 % | 0.81 |
| 2024-02 | 15 | 39.8 | 48.3 | −17 % | 0.78 | 2025-06 | 13 | 35.9 | 48.3 | −26 % | 0.64 |
| 2024-03 | 12 | 31.9 | 40.8 | −22 % | 0.90 | 2025-07 | 16 | 37.7 | 58.8 | −36 % | 0.45 |
| 2024-04 | 16 | 29.8 | 36.0 | −17 % | 0.25 | 2025-08 | 14 | 37.3 | 51.7 | −28 % | 0.35 |
| 2024-05 | 14 | 17.2 | 28.8 | −40 % | 0.81 | 2025-09 | 15 | 45.7 | 57.9 | −21 % | 0.56 |
| 2024-06 | 14 | 24.8 | 32.8 | −24 % | 0.72 | 2025-10 | 15 | 40.0 | 49.1 | −18 % | 0.49 |
| 2024-07 | 16 | 41.1 | 70.0 | −41 % | 0.38 | 2025-11 | 11 | 38.3 | 41.5 | −8 % | 0.94 |
| 2024-08 | 15 | 30.9 | 48.0 | −36 % | 0.87 | 2025-12 | 11 | 32.3 | 31.2 | +4 % | 0.83 |
| 2024-09 | 14 | 37.1 | 48.5 | −24 % | 0.70 | | | | | | |

### 2.4 D4 — structural sanity: PASS

Footprint load-weighted annual means **$46.29 / $42.32 / $32.41**; hourly range −$37.60 … $1,268.73 (the
January 2024 cold snap); every priced BA's annual mean positive (2024: BPAT 44.9 · PSEI 42.3 · SCL 42.3 ·
TPWR 41.8 · PGE 41.8 · PACW 41.8 · IPCO 35.7 · AVA 40.8 · NWMT 39.2 · PACE 31.1 · NEVP 29.5).

## 3. What the NO means, and what it does not

**What it says.** The WEIM 15-minute imbalance price at this footprint's load aggregation points is a
systematically lower price than the one at which the footprint's bulk energy trades day-ahead — by about a
quarter in ordinary conditions and more in summer. Scoring an NWPP model's LP duals (the marginal cost of
serving *all* load) against it would hold the model to a number that is, by measurement, not the price of
that quantity. That is precisely the misalignment the charter suspected in plan §2.6 and the reason the
gate existed. The volume share did *not* diagnose it (5.5–6.2 % is a working imbalance layer); the
independent anchor did.

**What it does not say.** It does not say the WEIM series is wrong, and it does not say why the gap exists.
One candidate explanation, flagged as untested: WEIM prices the residual of a heavily self-scheduled
hydro-thermal system, so its margin often sits on a low-cost unit while the day-ahead bilateral price
carries the firm-delivery and scarcity premium of a market with no organized DA counterpart. The 2024
correlation of 0.95 says the two series move together when prices move; the level does not close.
Explaining it is not this lane's charter and no explanation was fitted.

**Rule 14 `[R-ACCURATE]` read correctly here.** The rule says accurate data is kept and a worse fit is a
bug elsewhere. The WEIM data *is* accurate — for the quantity it prices. Rule 14's own misalignment
exception ("defined on a different boundary than our zones … a different aggregation") is what applies: the
object is real and the object is not the model's object. The series is kept, in the raw store, as what it
is; it is not promoted to the benchmark of a different quantity.

## 4. What is landed, what is not, and what is routed to NWPP-DESK

- **Landed:** the raw store (§1), the builder, this FINDING, the PRECOMMIT. **Not landed:**
  `data/raw/_validation-source/actual_lmp_hourly_NWPP.parquet` (`gate --land` refuses on NO).
- **Card N2 limb (b) applies** to any NWPP run: a determination naming its own basis, never a bare
  `CALIBRATED`, with the price gap at full magnitude. This lane does not choose the wording.
- **Routed, for the desk to rule — not decided here.** Two honest options exist. **(i)** Score no price
  criterion; C3a/C3b/C3c read unscored and the determination says so (the plan's example wording). **(ii)**
  Use the WEIM series as an explicitly-labelled *imbalance-price* benchmark — it is buildable at zero cost
  from the committed store and would give C3b/C3c an hourly RT object that Mid-C never can — with the
  measured −23 % on-peak discount to Mid-C named on the determination basis of every NWPP run. Option (ii)
  is **a new owner ruling (an N2 amendment), not a re-run of this gate**: the gate was pre-registered,
  it read NO, and re-cutting it to admit the series is the fitted benchmark the PRECOMMIT refused in
  writing. A third option — anchoring the WEIM level to Mid-C by a DA/RT relation — is refused by this lane
  as the tuned adjustment rule 13 forbids. This lane's recommendation, labelled as such: (i) for the first
  keeper, so that NWPP's first number is honest about what it is; (ii) only if the owner wants price
  *shape* evidence and accepts the labelled basis.
- **Gate G6** (`TAIL_THRESHOLD["NWPP"]` + `actual_tail.json`): the three edits are **deliberately skipped**
  — N2 yielded no series — and the skip is documented here as the plan requires.
- **NWPP-31 / `actual_lmp.json`:** no NWPP block and no `rt_cov.mon` is needed now. Should option (ii) ever
  be ruled, 2023's partial coverage (Jun–Dec, 58.6 %) must ride the scorer's masked path via `rt_cov.mon`.
- **Timezone (card N6 / NWPP-10):** no `claude/nwpp-10-*` branch existed on the remote during this lane, so
  the fixed-PST convention was taken from card N6's desk recommendation and the repo's sidecar precedent
  (PRECOMMIT §4). The 15-minute stores keep the UTC instant, so any other canonical hour is a re-index.
- **Card N5:** the store is per BA; the N5-recommended zonal load-weighted means, for the record
  (2024: NW 50.68 · OR 46.66 · INLAND 42.21 · EAST 32.12 · SNV 30.98 $/MWh; 2025: 34.97 · 33.68 · 32.27 ·
  28.92 · 29.50) — a real west-to-east gradient the topology card can see.
- **`_validation-source/README.md`:** no row needed (nothing landed).
- **Matrix shard:** `docs/codebase-site/data/mechanism-matrix/NWPP.js` does not exist at this base sha
  (NWPP-21 is HELD), so the rule-28(b) cell duty is vacuous for this lane; no mechanism was tested.
- **Shards:** none launched — this lane ran no LP (rule 32 is not engaged; nothing to archive).

## 5. Reproducibility, rule 13's forward test, and identity

`fetch-lmp → fetch-transfer → fetch-midc → transcribe-benefits → reconcile-ties → build → gate`
regenerates every committed artifact from the three sources in `SOURCES.md`; every number above is in
`gate.json` / `d2_tie_reconciliation.json`. A forward year regenerates from the same OASIS query with no
change (rule 13's test is met by construction); the backcast years are retention-limited and the parquets
are their record. `SHA256SUMS.txt` carries the hash of every tracked artifact and of every untracked pull.
The two LMP-component facts worth knowing before anyone reuses the store: the published LMP does not equal
`MCE + MCC + MCL` in 56.5 % of intervals (p99 of the gap $27/MWh) — the index uses the published `LMP_PRC`
as declared — and NEVP's 2025 demand is non-positive in 17 hours, leaving the N5-SNV zone price undefined
there (the footprint price is unaffected).

## 6. Rules, files, verification

Rules 1 / 13 / 14 / 23 / 25 / 27 / §8.0 as the PRECOMMIT §9 states them, each honoured: no residual read;
every input a regenerable market quantity; the accurate series kept as what it is; the builder re-runs only
on source change; nothing CAISO-priced entered (the `CASP` and `TH_*` nodes were never read into an
artifact); every pushed file ≥ 300 lines fetch-back verified by hash and line count; no shared record
edited. **Files touched:** `docs/handoffs/PRECOMMIT-nwpp-13-2026-09-13.md`, this FINDING,
`scripts/data/build_nwpp_weim_price_index.py`, `data/raw/nwpp-weim/**` (with its own `.gitignore` for
`_pulls/`). Nothing under `src/`, `tests/`, any other `_validation-source` file, the plan, the ledger,
`nwpp.md`, or any `soco*` file.

## Log entry

## nwpp-13 — 2026-09-13

**WEIM price index (card N2 option a): NO.** PRECOMMIT pushed before any value was read; STOP gate
D1/D2/D4 pass, **D3 fails every year** — NW-group WEIM on-peak price −37.5 / −22.6 / −23.6 % vs the
Mid-C Peak single-day index (bar ±10 %), corr 0.74 / 0.95 / 0.67 (bar 0.80); persistent (88.7 % of days,
median daily ratio 0.75, −23.3 % excluding scarcity days). **WEIM volume share 5.66 / 5.54 / 6.15 %** of
17-BA demand on the net-position basis (10.6 % pairwise gross; bar 5 %). Retention edge 2023-06-01, so
2023 is Jun–Dec (5,137 h). Raw store `data/raw/nwpp-weim/` committed (12 `DEPZ` nodes, 1.09 M LMP rows,
2.08 M transfer rows, per-BA hourly product, Mid-C rows, Appendix-2 transcription, tie-level D2
reconciliation: `ENE_EIM_TRANSFER` = net position, Appendix 2 = pairwise gross). **Nothing landed to
`_validation-source`**; N2 limb (b) applies; G6 edits skipped by design. Routed: option (i) unscored price
vs option (ii) labelled imbalance benchmark = a new owner ruling, never a re-cut gate.
`FINDING-nwpp-13-2026-09-13.md`.
