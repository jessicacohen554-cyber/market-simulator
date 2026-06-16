# PJM ORDC curve — parameter provenance

Every value in `inputs/calibration/pjm_ordc_curve.csv` traced to its primary
source. Source PDFs are committed in `inputs/raw-data/PJM-AS/`. Nothing here is
fitted to a price residual (claude.md #4).

## The in-force curve (2023–2025 backcast)

PJM clears energy and reserves jointly against a **stepped Operating Reserve
Demand Curve (ORDC)** — a vertical/step demand curve, *not* ERCOT's smooth LOLP.
For each reserve product in each Reserve Zone / Sub-Zone the curve is:

| step | penalty factor ($/MWh) | desired-reserve breakpoint (MW) |
|---|---|---|
| 1 | **850** | locational reserve **Requirement** |
| 2 | **300** | Requirement **+ 190 MW** (+ any heavy-load extension) |
| (beyond) | 0 | — |

The penalty factor "represents the price at which reserves will be valued if
the desired reserve MW cannot be met … and also acts as a price cap beyond
which reserves will not be procured" (Manual 11, sec 4.3.3).

### Per-value citations

| value | source (PDF in `inputs/raw-data/PJM-AS/`) | exact location |
|---|---|---|
| Step 1 penalty = $850/MWh | `m11.pdf` (Rev 136, 2025-10-01) | sec 4.3.3 "Step 1: Penalty Factor = $850/MWh; Desired Reserve MW = locational Reliability Requirement" |
| Step 2 penalty = $300/MWh | `m11.pdf` | sec 4.3.3 "Step 2: Penalty Factor = $300/MWh; Desired Reserve MW = … Requirement … plus 190 MW …" |
| Step 2 width = +190 MW | `m11.pdf` | sec 4.3.3 Step 2 ("plus 190 MW plus any additional reserves … carried in anticipation of heavy load") |
| same penalty factors across all 6 product×zone curves | `m11.pdf` | sec 4.3.3 ("share the same penalty factors on the Y axis; however, the desired reserve levels on the X axis differ") |
| plain-language confirmation ("two-step ORDC … first step … $850 … second step … $300") | `shortage-pricing-fact-sheet.pdf` (PJM, dated 2024-01-03) | p. 2 |
| reform that established the consolidated reserve products / joint optimization / ASO | `E-3-052120.pdf` — FERC *Order on Proposed Tariff and Operating Agreement Revisions*, Docket EL19-58-000 / ER19-1486-000, issued 2020-05-21 | ¶1–2 (PJM filed 2019-03-29; FERC "largely adopt[s] PJM's proposed replacement rate … subject to certain modifications"); implemented **2022-10-01** |

### Date-gating the revisions

The two-step `$850 / $300 / +190 MW` curve is **identical** across the three
committed Manual 11 vintages, so no parameter changes within the backcast
window:

| vintage | file | sec 4.3.3 Step 1 / Step 2 |
|---|---|---|
| Rev 127, eff 2023-11-15 | `m11v127-…-11-15-2023.pdf` | $850 at requirement / $300 at +190 MW |
| Rev 129, eff 2024-02-22 | `m11v129-…-02-22-2024.pdf` | $850 / $300 / +190 MW (unchanged) |
| Rev 136, eff 2025-10-01 | `m11.pdf` | $850 / $300 / +190 MW (unchanged) |

So `effective_date` in the CSV is set to the reform go-live `2022-10-01` for
every row: the curve is stable from the reform through the entire 2023–2025
backcast. Pre-reform (before 2022-10-01) is **out of scope** — the backcast does
not reach it — and is deliberately not encoded.

> **Citation honesty note on the FERC order.** `E-3-052120.pdf` (2020-05-21) is
> the order in the proceeding where PJM argued its *then-existing* $850/$300
> ORDCs were unjust and proposed raising penalty factors to $2,000/MWh on a
> probabilistic curve (order ¶133). That $2,000 figure is the *proposal text*,
> **not** what governs 2023–2025: the operative, in-force curve across the
> backcast is the two-step $850/$300/+190 MW specified by the Manual 11
> revisions above. We therefore take the numeric parameters from Manual 11
> (primary operating document) and cite the FERC order only for the regulatory
> regime (consolidated Synchronized/Primary/Secondary products, the Ancillary
> Services Optimizer, and DA/RT joint optimization) it established effective
> 2022-10-01. Hardcoding the order's $2,000 proposal would be wrong.

## The cascade (how penalty factors become reserve clearing prices)

PJM's three reserve products are nested by capability (Manual 11 sec 4.4.1):
Synchronized (10-min, online) ⊆ Primary (10-min, incl. non-synchronized) ⊆
30-Minute (Secondary). A megawatt that meets a higher-quality requirement also
meets the lower ones, so each reserve clearing price is the **sum of the nested
requirement shadow prices**:

```
SRMCP  (Synchronized) = SP_SR + SP_PR + SP_30      (data service "SR")
NSRMCP (Primary)      =          SP_PR + SP_30      (data service "PR")
SecRMCP(Secondary)    =                  SP_30      (data service "30MIN")
```

where `SP_x` is the step price of product `x`'s demand curve at the cleared
reserve level (0, $300, or $850). This is confirmed by the measured RT maxima
in `reserve_market_results_*.parquet`: 2025 max SR = **$2,550** = 3 × $850,
PR = **$1,700** = 2 × $850, 30MIN = **$850** = 1 × $850 — i.e. all three nested
constraints at Step 1 simultaneously. (The "capped at 2× / 1.5× Penalty Factor"
language in Manual 11 sec 2.5 / 4.4.5 is the *voltage-reduction / manual-load-
dump emergency* cap, a different condition from normal co-optimized clearing.)

## Requirement (the X-axis breakpoint)

- **Backcast:** use the **measured** `as_req_mw` directly from
  `reserve_market_results_{yr}.parquet` (RT) / `da_reserve_market_results_{yr}`
  (DA), per `locale` × `service`. No reconstruction — the requirement is data.
- **Forecast rule** (Manual 11 sec 4.3): the requirement is driven by the
  **Largest Single Contingency (LSC)** — "the greatest MW loss of all potential
  Largest Single Contingencies on the system":
  - Synchronized Reserve Requirement = LSC (RT: the higher of the largest online
    generator's output/EcoMax or an active reserve group's sum).
  - Primary Reserve Requirement ≈ 1.5 × LSC — the measured RTO `PR/SR`
    requirement ratio in the parquets is **1.45** (2023), consistent with the
    150%-of-contingency convention.
  - 30-Minute (Secondary) Requirement is based on the largest **gas**
    contingency (sum of EcoMax of the identified gas resources), Manual 11
    sec 4.3.
  - On-peak heavy-load / Hot- or Cold-Weather-Alert hours **extend** all three
    requirements by the additional MW dispatch brings online (sec 4.3).
