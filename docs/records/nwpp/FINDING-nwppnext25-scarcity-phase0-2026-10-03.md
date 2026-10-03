# FINDING — NWPP-NEXT-25 phase 0: no admissible lever for the C3a tail days (zero LP)

Probe: `scripts/probes/_nwppnext25_scarcity_phase0.py`. It reads keeper `2026-10-03-nwpp-next-24-head`
(`results/calibration/nwppnext24_span/hourly`), the WEIM 15-minute ELAP components
(`data/raw/nwpp-weim/weim_rtpd_lmp_15min.parquet`), EIA-930 seam legs, the measured seam limits
(`nwpp_seam_limits_hourly`) and the measured hydro envelope. Handoff task 1: HANDOFF-nwppnext24 /
FINDING-nwppnext24 §D. No LP was run.

## A. What the benchmark carries on the tail days

NW ELAP price, as the mean over the nine Northwest BAAs (BPAT, PACW, PGE, PSEI, SCL, TPWR, AVA, NWMT, IPCO):

| days | lmp | MCE (WEIM-wide energy) | MCC (NW congestion) |
|---|---:|---:|---:|
| 2024-01-13 … 01-16 | 542–931 | 204–426 | **352–608** |
| 2023-10-25 … 10-31 | 89–136 | 55–73 | 28–77 |
| 2023-07-25/26, 08-15/16 | 62–112 | 168–228 | **−87 to −128** |

- **Jan 2024.** The NW price is two scarcities stacked: the WEIM-wide energy price at 4–8× its normal level, plus
  an NW import-congestion premium of $350–600. The bilateral market saw the same scarcity: ICE Mid-C Peak
  `wavg` was $879 / 934 / 798 for Jan 11–16 delivery, so this is not a WEIM-imbalance artifact. MALIN (CAISO
  intertie) was $184–218. The model's COI external price was $45–51.
- **Summer 2023.** The tail is CAISO's: MCE is $168–228 while NW is congested **below** it. NW exports into a
  scarce CAISO.

## B. Quantities match; the seams are near their measured limits

Jan 12–17 2024, daily mean MW, positive = into NWPP:

| seam | model | measured | measured import cap |
|---|---|---|---|
| COI | 713–2,132 | 1,239–1,975 | 2,224–2,495 (CAISO OTC(E); ETC/TOR use ≈ 900) |
| NEVP | −691 to +502 | −1,258 to −897 | — |
| BC | −1,312 to −688 | −540 to +930 | 2,400 |

- Net interchange agrees to within about 0.5 GW.
- COI S→N runs at its operating limit, net of ETC/TOR use, in both model and measurement.
- The model exports to BC throughout the event; measured BC flows into NWPP from Jan 13. The BCHA ELAP was $89–129
  against the model's $50–58 on the BC external node, which accounts for about 1.5 GW.

## C. Candidate 1 — WEIM RSE failures / power-balance penalty pricing (rule 13)

The RSE failure flag and the penalty-priced intervals are **outcomes**: a BAA fails because it is short. The forward
instrument is the RSE capacity test, which compares a BAA's bid-in resources and **base-schedule** imports with its
forecast load, contingency reserve and uncertainty. The bilateral base schedules are not in the corpus, so this
instrument cannot be built. Reading the failure flags would pin the answer. **Not admissible.**

## D. Candidate 2 — an NW contingency-reserve requirement with a shortage curve (rule-19 census first)

**Census.** No reserve or scarcity mechanism prices NWPP's tail today:

- `energy_reserve_coopt` is off;
- `get_reserve_design` has **no NWPP branch** (it would raise);
- `scarcity_pricing_enabled`, `scarcity_price_overlay` and every `*_ordc_*` key are off or ERCOT-scoped;
- `reserve_price` is 0 in every 2019–2025 hour;
- the only tail is VOLL slack at $5,000, which never binds.

The mechanism is structurally real. NW BAAs carry BAL-002-WECC-3 contingency reserve (3 % of load + 3 % of net
generation) through the NWPP reserve-sharing group.

**Zero-LP adequacy on the keeper dispatch.** Eligible headroom is online thermal headroom, plus offline
quick-start CT and oil, plus hydro headroom up to the measured envelope:

| year | hours short (internal only) | hours short incl. seam import headroom at measured limits | min margin |
|---|---:|---:|---:|
| 2019–2022 | 280–526 | 0 | 3,132 MW |
| 2023 | 1,000 | 0 | 716 MW |
| 2024 | 1,359 | 0 | 3,136 MW |
| 2025 | 932 | 0 | 4,502 MW |

In the LP the requirement is met in every hour by importing more at the seam reference ($45–60 in the event) and
freeing internal capacity. The reserve shadow price is therefore bounded by the spread between the import band and
the displaced internal unit, at most about $15/MWh. The **expected C3a effect is ≈ 0** on the tail days, and
roughly the same off them.

A price-taker that ignores the seams and prices every "internal-only short" hour on CAISO's tariff curves gives
C3a 2023/24/25 of +268/+287/+265 %. That shows the internal-only reading is not the market structure. **Estimated
inert on C3a.** The mechanism is real but absent, and would be a structural-integrity addition only.

## E. Candidate 3 — hydro capability in the cold snap

`hydro_dispatch_envelope` is already armed: a measured per-(month × hour-of-day) p95 of EIA-930 NG:WAT. In the
event hours the model's hydro sits **at** the envelope (0 MW headroom) and within 0.8 GW of the EIA-930 hydro
output. There is no capability slack left to tighten. **Inert.**

## F. The daily-fuel route on the CAISO side

CA citygate daily is a measured input of the admissible delivered-fuel class. It differs materially from its month
mean on one tail day only: Jan 12 2024, $17.34 against $4.79, the weekend strip. Every other tail day is within
$1.6. At most about +1–2 pp on C3a 2024. **Immaterial.**

## Reading

The 2023/24 C3a tail is **neighbor-side scarcity** (WEIM-wide MCE and MALIN) **stacked on NW import congestion at
COI's measured S→N limit**. The model reproduces the quantities. Its seam reference prices are a cost-based
neighbor supply curve (HR × monthly gas), and that curve cannot carry a neighbor's scarcity rent. None of the
three handoff candidates is both admissible and material:

- RSE failures are an outcome, and the instrument needs unmeasured base schedules;
- a contingency reserve is real but inert, because the seams cover it;
- hydro is already at its measured capability.

Ex-tail, C3a 2023/24 sits at −6 / −7 % (FINDING-nwppnext24 §D), inside the band. The open records are the tail
days alone. A neighbor-scarcity driver would need the neighbor's own scarcity instrument, CAISO's reserve and
RA position, which is a cross-ISO coupling outside this lane. Routed to the owner card.
