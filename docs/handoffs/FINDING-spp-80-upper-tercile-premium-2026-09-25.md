# FINDING — SPP-80: what owns SPP's 2022+ upper-tercile price premium (data intake, zero LP, 2026-09-25)

Charter: `docs/handoffs/CHARTER-spp-80-upper-tercile-premium-intake-2026-09-25.md`.
Parent: `docs/handoffs/FINDING-spp-79-c3a-is-a-cancellation-2026-09-25.md`.
Probe: `scripts/probes/_spp80_upper_tercile_premium.py`. Commits, from pin `e2eddfed`: the data,
the probe and this document. **No LP, no shard, no bundle, no `src/` edit, no `ScenarioConfig`
field, no multiplier touched.**

## 0. Headline

- **None of the four named drivers owns the 2022+ rise.** The whole premium sits in the hub's
  **marginal energy component outside scarcity hours**, and it shows at **every** net-load level.
  - **Congestion does not own it.** The hub's MCC + MLC in the upper tercile is −$1.6 to +$3.8/MWh,
    and it is *negative* in 2023.
  - **Scarcity does not own it; it moved the wrong way.** Hours carrying reserve scarcity fell from
    12–15 % of the upper tercile (2019–21) to 3–5 % (2023–25).
  - **Markup does not own it.** The MMU's marginal-resource markup reached its **most negative
    ever** in 2023–24 (on-peak −$12.27 / −$11.01).
  - **Supply tightness does not own it.** Upper-tercile net load is flat at 26.5–28.4 GW across all
    seven years.
- **Part of it is regional gas basis after all, and the model already carries that part.** On
  Henry Hub the premium is **+4.7 / +8.3 HR** (2023 / 2024). Against **delivered** gas to KS/OK/NE
  plants (EIA-923, ex-Feb), it shrinks to **+3.2 / +3.4 HR**, about **$9.5 / $10.6 per MWh**.
  Delivered-over-HH gas widened from 0.95–1.13 (2019–20) to 1.17 / 1.41 (2023 / 2024).
  SPP-79's basis check used annual state averages and did not separate the two.
- **What remains matches the model's own upper-tercile gap.** The residual is +3.2 / +3.4 HR on
  delivered gas, about $10–11/MWh. The keeper's upper-tercile gap (RT − model) is $10.5 / $13.5.
  No measured SPP input in this intake names that residual.
- **Coupling constraint (SPP-79 §2): no measured driver can carry the pairing.** A body-price lever
  still breaks the 2023–25 C3a pass unless an upper-tercile object is found. This intake closes four
  candidates and narrows the object to about 3.3 HR of marginal-energy cost that is not scarcity,
  congestion, markup, quantity or delivered fuel.

## 1. The decomposition (upper tercile = RT p67 ≤ RT < p99, February excluded, SPP-79's exact hours)

Hub RT (the committed system-hub sidecar) = MEC + MCC + MLC, measured per hour
(`actual_lmp_components_hourly_zonal_SPP.parquet`, new, §3). **HR** = $/MWh ÷ annual Henry Hub,
as in SPP-79. **Δ** = against the 2019–21 mean. The split is exact: the columns sum to the premium
to 1e-6.

| year | HH $ | up RT $ | up model $ | RT HR | **premium ΔHR** | congestion + loss ΔHR | scarcity ΔHR | **MEC ex-scarcity ΔHR** | delivered gas $ | MEC ex-scar HR on delivered gas | **Δ on delivered** |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2019 | 2.57 | 32.0 | 26.9 | 12.49 | −0.20 | +0.13 | +0.19 | −0.52 | 2.40 | 11.68 | +1.06 |
| 2020 | 2.03 | 27.9 | 25.0 | 13.71 | +1.02 | −0.00 | +0.10 | +0.93 | 2.30 | 10.93 | +0.31 |
| 2021 | 3.91 | 46.4 | 42.0 | 11.86 | −0.83 | −0.13 | −0.29 | −0.41 | 4.66 | 9.26 | −1.37 |
| 2022 | 6.42 | 88.9 | 67.5 | 13.85 | +1.17 | **+0.87** | −0.92 | +1.21 | 7.56 | 10.75 | +0.13 |
| 2023 | 2.54 | 41.6 | 31.1 | 16.40 | **+3.72** | −0.22 | **−0.78** | **+4.72** | 2.97 | 13.81 | **+3.19** |
| 2024 | 2.19 | 46.1 | 32.6 | 21.03 | **+8.35** | +0.74 | **−0.72** | **+8.33** | 3.09 | 14.05 | **+3.43** |
| 2025 | 3.53 | 47.6 | 35.4 | 13.48 | +0.79 | +0.03 | −0.88 | +1.64 | 3.70 | 12.49 | +1.87 |

Recomputed on this hour set, SPP-79's RT-HR column (12.5 / 13.7 / 11.9 / 13.9 / 16.4 / 21.0 / 13.5) and
its up-model $ column both reproduce.

### 1.1 Congestion + losses: the hub MCC + MLC ($/MWh) and the binding-constraint witness

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| hub MCC, upper tercile | −0.38 | −0.62 | −1.59 | **+3.77** | −1.22 | +1.28 | −0.82 |
| hub MLC, upper tercile | −0.07 | −0.01 | −0.13 | −0.16 | −0.13 | −0.33 | −0.18 |
| RTBM binding shadow-price mass, $/interval (upper tercile) | 640 | 646 | 1,394 | 1,937 | 1,302 | 1,550 | 1,446 |
| binding constraints per interval | 2.8 | 2.8 | 3.8 | 4.6 | 3.5 | 4.4 | 4.1 |
| MMU DA+RT congestion payments, $ bn (SOM) | 0.457 | 0.442 | 1.2 | 2.0 | 1.4 | 1.8 | 1.6 |

Congestion **did** grow after 2020: binding mass rose about 2.2×, and MMU payments rose 3–4×. But it
**does not reach the hub price** in the upper tercile. The hubs sit on the unconstrained side often
enough that their MCC averages near zero, and it is negative in 2023. Congestion is a
spatial-spread object, not the hub-level premium. The two-zone model cannot, and need not, carry it
for this object.

### 1.2 Reserve / scarcity (RTBM MCP, BA-wide worst zone, upper-tercile hourly means)

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| hours with a scarcity-priced interval (share of upper tercile) | 12.5 % | 11.6 % | 15.2 % | 9.6 % | **4.7 %** | **3.4 %** | 3.1 % |
| MEC uplift those hours add to the tercile mean, $/MWh | 4.47 | 3.35 | 4.92 | 4.06 | 1.94 | 1.82 | 2.38 |
| spin MCP $/MW | 8.1 | 8.0 | 11.0 | 11.4 | 7.3 | 5.3 | 6.2 |
| reg-up MCP $/MW | 14.2 | 13.7 | 23.0 | 24.7 | 15.0 | 16.8 | 17.9 |
| ramp-up MCP $/MW | — | — | — | 4.6 | 3.7 | 2.8 | 3.6 |
| uncertainty MCP $/MW | — | — | — | — | 0.00 | 0.03 | 0.19 |

The scarcity flag is **Spin or Supp MCP > $100/MW**, or **Reg-Up MCP > $500/MW**. Those are the
Protocols r119 §8.2.5 offer caps: a price above a cap can only come from a Demand Curve. MMU RT
scarcity totals: 1,220 (2019), 1,346 (2020), about 3,700 (2021, including Uri). From 2022 the SOM
charts scarcity per product only.

**Scarcity-design dates, from SPP MMU's own reports (not from memory):**
- Ramp capability product: **2022-03-01** (2022 SOM PDF p.122).
- Fast-start pricing: **May 2022** (p.91).
- Uncertainty product: FERC-approved mid-August 2022 (p.170), implemented **2023-07-06**
  (2023 SOM p.120).
- Uncertainty design enhancement: **October 2024** (2024 SOM p.226).

The landed MCPs agree: the first non-zero ramp-up MCP is 2022-03-01, and the first non-zero
uncertainty MCP is 2023-10-09. **None of the three changes raised the upper tercile through
reserve prices.** The ramp MCP averages $3–5/MW, the uncertainty MCP is essentially zero, and
scarcity *fell* after the redesign.

### 1.3 Offer markup (SPP MMU SOM, $/MWh, MW-weighted marginal resource; `som-competitive-conduct`)

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| on-peak | −8.48 | −8.70 | −1.73ᵈ (ex-Feb −2.97) | +12.03ᵈ / +6.35ᵈ | **−12.27** | **−11.01** | −3.15 |
| off-peak | −8.78 | −9.54 | −3.37ᵈ (ex-Feb −3.99) | +4.22ᵈ / +4.24ᵈ | −8.58 | −14.66 | −5.94 |
| coal | — | — | 6.02 | **21.12** | 6.88 | 4.29 | 5.81 |
| wind | — | — | −29.03 | −38.75 | −41.50 | −37.99 | −37.81 |

ᵈ digitized from the chart marker, bias-corrected; the 2023 and 2022 SOM vintages disagree on
2022 on-peak.

**Markup owns 2022's excess**, which was coal rail-deliverability (+$21/MWh coal markup) and summer
on-peak markups above $40. **It cannot own 2023–24**: those are the lowest markups SPP has recorded.
Markup is measured against the *mitigated* offer, so a cost-based offer that rose above Henry Hub
would show up in the MEC ex-scarcity column with a flat markup. That is where the rise sits.

### 1.4 Supply tightness

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| upper-tercile net load, GW (GenMix load − wind − solar) | 27.8 | 26.8 | 26.5 | 28.4 | 27.6 | 27.2 | 27.4 |
| its percentile within the year | 0.79 | 0.81 | 0.80 | 0.82 | 0.81 | 0.79 | 0.80 |

**At matched net load the price still rose, in every band** (median MEC ÷ HH, ex-Feb, all hours):

| net load | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| ≤ 15 GW | 3.6 | 3.5 | 2.9 | 2.7 | **4.9** | 3.7 | 3.2 |
| 20–25 GW | 7.4 | 8.5 | 6.6 | 7.2 | **9.9** | **10.4** | 7.7 |
| 25–30 GW | 8.4 | 9.7 | 7.9 | 9.8 | **11.6** | **12.8** | 8.8 |
| 30–35 GW | 9.1 | 10.8 | 10.0 | 13.3 | **13.5** | **14.7** | 10.5 |
| > 35 GW | 10.4 | 13.6 | 12.1 | 15.9 | **18.5** | **18.4** | 12.7 |

The 2023–24 lift of about +2 to +4 HR appears at 20 GW net load as much as at 35 GW. **The residual
therefore raises the cost level of the whole stack, not its quantity.**

### 1.5 Delivered fuel (EIA-923, ex-Feb, quantity-weighted, $/MMBtu)

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| gas delivered to KS/OK/NE plants | 2.40 | 2.30 | 4.66 | 7.56 | 2.97 | 3.09 | 3.70 |
| ÷ annual Henry Hub | 0.94 | 1.13 | 1.19 | 1.18 | **1.17** | **1.41** | 1.05 |
| coal delivered to SWPP-BA plants | 1.61 | 1.58 | 1.62 | 1.92 | 1.80 | 1.69 | n/a (2025 receipts not landed) |

- **Coal is not it.** Delivered coal is flat, and coal/HH in 2023–24 (0.71 / 0.77) matches 2019–20
  (0.63 / 0.78).
- **Gas basis is about 59 % of 2024's HH-denominated MEC ex-scarcity rise (4.90 of 8.33 HR) and
  about 32 % of 2023's (1.53 of 4.72 HR).**
- Caveat: the delivered-gas split is on a different denominator, so it is reported **beside** the
  HH split and never differenced into it.
- SPP-74 measured that the model's gas tracks EIA N3045 KS within $0.1–0.7 (below it), so **the
  model already carries this part.** It is not the model's missing object.

## 2. Which driver owns the 2022+ rise, at full magnitude

| year | premium on HH | owned by | on delivered gas |
|---|---|---|---|
| 2022 | +1.17 HR | congestion +0.87 plus MEC +1.21 (markup: coal rail-deliverability, summer on-peak markups); scarcity −0.92 | +0.13, **nothing left** |
| 2023 | **+3.72 HR** | **none of the four.** MEC ex-scarcity +4.72, of which gas basis about 1.5; scarcity −0.78; congestion −0.22; markup negative | **+3.19 HR ≈ $9.5/MWh unexplained** |
| 2024 | **+8.35 HR** | **none of the four.** MEC ex-scarcity +8.33, of which gas basis about 4.9; congestion +0.74; scarcity −0.72; markup negative | **+3.43 HR ≈ $10.6/MWh unexplained** |
| 2025 | +0.79 HR | small; MEC ex-scarcity +1.64; scarcity −0.88 | +1.87 HR |

The unexplained object is **cost-level, stack-wide, and outside every measured channel**. Neither
this intake nor any committed SPP source can yet separate what is left:
- the heat-rate mix of the marginal gas units (more CT/ST on the margin);
- intra-day and daily gas purchases above the monthly delivered average;
- ramp-product dispatch holding back cheaper units (the ramp MCP is small, but procurement changes
  who is marginal);
- an unmeasured cost component inside the mitigated offer (fuel adders, gas-day nomination costs).

**The measurement is "none", stated at full magnitude.**

## 3. What landed (paths, sizes)

| corpus | years added | files | bytes |
|---|---|---|---|
| `data/raw/spp-binding-constraints/` | 2019–2022 | `RTBM-BC-YEARLY-{2019,2020,2021}.csv.zip`, `RTBM-BC-YEARLY-2022.zip` | 13,068,192 · 10,882,285 · 17,249,564 · 20,481,650 |
| `data/raw/spp-or-mcp/` | 2019–2022 | `RTBM_MCP_{2019..2022}.csv.zip` | 2,768,789 · 2,796,437 · 2,787,862 · 2,413,800 |
| `data/raw/spp-or-mcp/` | 2019–2022 | `da-mcp-{2019..2022}.zip` | 364,665 · 386,866 · 463,733 · 418,932 |
| `data/raw/_validation-source/actual_lmp_components_hourly_zonal_SPP.parquet` | 2019–2025, NEW | hub LMP/MCC/MLC/MEC, RT + DA | 4,611,777 |
| `data/raw/som-competitive-conduct/som_competitive_conduct.csv` | 2019–2025 | +50 SPP rows (MMU SOM, page-cited) | +~8 KB |

- **Hub parquet: no extension was needed.** The charter's §3 said
  `actual_lmp_hourly_zonal_SPP.parquet` was 2023–25 only. It has carried 2019–2025 since SPP-30
  (2026-09-12, `_validation-source/README.md`). What it lacked was the component split, now landed
  beside it via `scripts/data/fetch_spp_hub_lmp_components.py`, which reuses the builder
  unmodified. Its `lmp` column matches the committed sidecar **bit-exactly** (max |Δ| 0.000000).
- `SOURCES.md` and `SHA256SUMS.txt` are extended in both corpora, and every landed checksum
  verifies.
- The SOM PDFs are **not** committed. URLs and sha256 are in `som-competitive-conduct/README.md`.

## 4. Sources that failed or fell short

- **Nothing was egress-blocked.** `portal.spp.org` (anonymous HTTPS) and `www.spp.org` (SOM PDFs)
  answered on every call.
- **Chart-only SOM values.** The 2021 full-year and 2022 annual markups have no data label. They
  were digitized from the vector geometry, bias-corrected against printed years, and carry
  `_digitized_` in the metric code. The 2022 and 2023 vintages disagree on 2022 on-peak
  (+6.35 vs +12.03).
- **SOM 2022–2025 scarcity is per-product monthly charts only**, with no annual total, so the
  MCP-based count in §1.2 stands in.
- **Scarcity-design dates come from the SPP MMU's SOMs**, which cite SPP's filings. The FERC
  dockets themselves were not fetched.
- **EIA-923 2025 coal receipts are not landed**, so 2025 coal is n/a.

## 5. Rules and state

- Zero LP (rule 32 was not engaged: nothing solved). No cell verdict changes.
- Evidence was added without a verdict change to `energy_reserve_coopt` (I),
  `internal_congestion_split` (U) and `offer_curve_by_group` (K) in
  `docs/codebase-site/data/mechanism-matrix/SPP.js`. A DO-NOT-REDO note is in
  `docs/mechanism-testing-matrix.md` §5.7, above SPP-79's.
- Rule 13: every landed series is a measured market input that regenerates each year. None is
  wired, and nothing is armed.
- Rule 1: no multiplier was re-tuned. The residual is **not** offered as a reason to move
  `offer_curve_by_group`. The carve-out allows one ex-ante, year-invariant value, and the object
  here is year-specific (+3.2 / +3.4 HR in 2023–24, ≈ 0 in 2022).
- Retrievability (rule 34(e)): no bundle was produced, so there is nothing to promote.
