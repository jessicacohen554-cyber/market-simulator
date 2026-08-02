# FINDING — neiso-76: the chartered DA-bid lever is REFUTED at Phase-0 on BOTH limbs — the submitted book does not move within the day (it moves the WRONG WAY), and NEISO's virtual book is net-SHORT at the peak; the amplitude is a TRAVERSAL defect, and NEISO's reserve split is NOT NYISO's

**Date:** 2026-08-02 · **Scope:** NEISO, 2023–2025, the neiso-75 charter's
Phase-0 (§4) · **NO LP was solved, no keeper changed, no bundle produced, no
dashboard registration** (the neiso-71/73/74/75 disposition — rule 15 governs
completed runs and there is none). **Keeper:** `2026-07-31-neiso-72-hy-window`,
untouched.

**Probes (committed):**
`scripts/probes/_neiso76_dabid_phase0.py` (the frozen statistic + K1/K2/K4/K5
+ the price-free auxiliary),
`scripts/probes/_neiso76_demand_limb.py` (K3(ii), the miso-105 λ0-attractor
test on ISO-NE's own submitted demand book),
`scripts/probes/_neiso76_reserve_content.py` (task (b): the nyiso-110
reserve-content decomposition on NEISO's own posted AS prices).
**Records:** `PROBE-neiso76-dabid-phase0-2026-08-02.txt`,
`PROBE-neiso76-demand-limb-2026-08-02.txt`,
`PROBE-neiso76-reserve-content-2026-08-02.txt`.

The charter authorized measurement only and pre-registered five kills. Two
fired; one could not fire but its premise is measured FALSE with the sign
against the lane. The charter's own honest-outcome clause — "if the book does
NOT move, the supply-conduct limb is empty … and that kill is itself decisive
evidence (the amplitude then lives in demand-side depth, imports, or non-book
physics)" — is discharged, and the demand-side half of that sentence is
refuted in the same session on the same corpus.

---

## §0 — the verdict in one table

| # | charter question | measured result | verdict |
|---|---|---|---|
| **K1** | does the submitted non-fast-start book move within the day by ≥ $5/$5/$8? | fleet within-day movement **−$1.93 / −$1.84 / −$2.27** — negative, i.e. the body band is offered CHEAPER at the peak than overnight; **73–74 %** of 227,033 paired asset-days are bit-flat (\|move\| < $0.01) and the p25–p90 of the movement distribution is **exactly $0.00** in all three years | **FIRES — supply-conduct limb DEAD, with the sign against the theory of change** |
| **K2** | is the movement obtainable on admissible conditioning only (hour × net-load × month, never price)? | the whole surface is computed price-free; the **best** admissible conditioned cell is **−$0.39 / −$1.38 / −$1.49** — still negative, let alone under the bar | fires as well — no admissible conditioning rescues K1 |
| **K3(i)** | does ISO-NE publish a SUBMITTED priced DA demand/virtual book (the nyiso-94 blocker)? | **YES** — `hbdayaheaddemandbid`, Bid Types FIXED / PRICE / INC / DEC with up to 50 (price, MW) segments, 165–219 GWh/day of PRICED segment MW, present in every sampled 2023/2024/2025 day | **PASSES — NEISO is the third ISO with a submitted book (PJM, MISO, NEISO)** |
| **K3(ii)** | does the book's crossing price λ0 reproduce the posted DA price to ≤ $2 **and** supply ≥ 30 % of price displacement? | λ0 median error **$5.29** (only 27.3 % of hours inside $2); displacement share median **12.7 %** (≥ 30 % in 9.8 % of hours) | **does NOT fire — the limb is admissible** |
| **K3 materiality** (not a kill; the PJM premise) | is NEISO's net virtual position a peak DEC load like PJM's +7–11 GW? | net virtual is **−0.41 / −0.25 / −0.24 GW at the peak** and **+0.13 / +0.02 / +0.07 GW at the trough**; differential **−0.54 / −0.27 / −0.31 GW** ⇒ arming it faithfully **removes $2.9 / $1.4 / $1.7 of diurnal spread** | **premise FALSE and the sign is WRONG — the demand limb would make the defect worse** |
| **K4** | are the conduct statistics robust to the 34 Algonquin fuel-tail days (15 % bar)? | excluding them moves the movement **+10.7 % / +0.0 % / +24.1 %** | **FIRES on 2025 — moot: a robustness gate on a statistic that already failed K1, and it fires toward $0** |
| **K5** | is the statistic computable on the five 2025 event days? | Jun-23/24/25 and Jul-28/29 all present in the corpus and in the non-fast-start band | **PASSES** |
| **(b)** | does NEISO's amplitude decompose the way NYISO's did (reserve-dominated)? | **NO.** Reserve owns **33 / 43 / 32 %** of the missing RT swing (NYISO: 97–131 %), NEISO's RT reserve price is **$0.00 at the median hour** and > $1 in only **23 / 23 / 21 %** of peak hours (NYISO DA spin: 100 %), and there was **no day-ahead reserve product at all** before 2025-03-01 | **NEISO's amplitude is majority ENERGY-side, and it lives in the TROUGH** |
| **(c)** | pre-register a solve arm, or record the closure? | **CLOSURE.** Both chartered limbs are refuted on NEISO's own data; the successor identification the measurement names (stack traversal) is a different mechanism and needs its own charter | **no arm pre-registered; frontier routed to the owner** |

---

## §A — the supply-conduct limb: the book is flat, and where it moves it moves down

**Corpus.** 1,063 non-empty operating-day files — **359 / 351 / 353** of
365/366/365 (the endpoint's documented publication gaps; the caiso-154 refetch
saw 353/352/353, so this pull is one day better in 2023 and one worse in 2024).
7,397,341 offer rows; the **non-fast-start band** (the complement of neiso-58's
physics selection, `Claim 30 < 0.9 × EcoMax`) is 5,607,717 rows across **360
assets**, against 1,789,624 rows / 110 assets fast-start. **K5 passes:** all
five 2025 event days (Jun-23/24/25, Jul-28/29) are present in the corpus *and*
in the band.

### A1 — the frozen statistic

| year | movement | K1 bar | measured hod gap | share of gap | verdict | unpaired | HE16-19 windows | top rung | fast-start band |
|---|--:|--:|--:|--:|:--|--:|--:|--:|--:|
| 2023 | **−1.926** | 5.00 | 18.93 | −10.2 % | **FIRES** | −1.926 | −1.645 | −0.498 | −15.916 |
| 2024 | **−1.840** | 5.00 | 22.14 | −8.3 % | **FIRES** | −1.840 | −1.695 | −0.273 | −14.233 |
| 2025 | **−2.274** | 8.00 | 31.17 | −7.3 % | **FIRES** | −2.274 | −2.040 | +0.478 | −13.652 |

Every column agrees, and every one of them is on the wrong side of zero except
one $0.48 top-rung cell. The pairing requirement (an asset-day counts only if
it offers in BOTH windows) makes composition impossible as an explanation, and
the unpaired control is identical to three decimal places. The alternate window
reading (report HE 16–19 / 01–04 instead of hours-beginning) changes nothing.
The **fast-start band moves −$13.7 to −$15.9** — peakers offer *far* cheaper at
the peak than overnight, which is real conduct and is the opposite of what
raises a peak price.

### A2 — the distribution: three quarters of the book is bit-flat

| year | paired asset-days | flat (\|move\| < $0.01) | \|move\| < $1 | p10 | p25 | p50 | p75 | p90 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|
| 2023 | 74,779 | **72.8 %** | 81.5 % | −1.71 | 0.00 | 0.00 | 0.00 | 0.00 |
| 2024 | 75,553 | **72.9 %** | 82.3 % | −1.59 | 0.00 | 0.00 | 0.00 | 0.00 |
| 2025 | 76,701 | **73.9 %** | 81.5 % | −1.93 | 0.00 | 0.00 | 0.00 | 0.00 |

The p25 through p90 are **exactly zero**: the median NEISO asset submits the
identical curve at 03:00 and at 18:00. All of the movement lives in the bottom
decile, and it is negative. Controls: ECONOMIC-only (dropping MUST_RUN)
−1.732 / −1.701 / −2.733; unweighted −2.026 / −3.443 / −3.498; the five largest
capacity-weighted contributors in each year are all negative, none larger than
−$0.40 of the fleet aggregate, so this is a broad property of the book and not
a handful of units.

### A3 — the band's hour-of-day offer profile is INVERTED

Capacity-weighted mean incremental-segment price of the non-fast-start band, by
hour-ending:

| year | min | max | hod range | vs DA | vs model |
|---|---|---|--:|--:|--:|
| 2023 | $66.26 (HE20) | $68.47 (HE24) | **$2.20** | $25.96 | $7.03 |
| 2024 | $64.92 (HE20) | $67.43 (HE24) | **$2.51** | $28.96 | $6.82 |
| 2025 | $76.28 (HE9) | $79.95 (HE24) | **$3.67** | $44.47 | $13.30 |

The submitted book's own diurnal offer shape is **$2.20–3.67 wide and troughs
at the evening peak**. Against a measured DA price range of $25.96–44.47 there
is no version of "the marginal band offers dearer at the peak" in this data.

### A4 — K4 and K2, for completeness

K4 (exclude the 34 Algonquin ≥ $25.00 fuel-tail days, caiso-154's set; 32 of
them fall inside the corpus): the movement goes −1.926 → −1.721 (+10.7 %),
−1.840 → −1.840 (+0.0 %), −2.274 → −1.725 (+24.1 %). 2025 breaches the 15 %
bar, so K4 fires — but it fires by moving the statistic *closer to zero*, i.e.
the fuel-tail days were making the book look *more* negatively-moving than it
is. It changes no verdict.

K2: the conditioned surface (net-load percentile bins 0.80/0.90/0.97 × month,
never price) is negative in **11 of 12 year-bin cells**, and the single best
admissible cell per year is −0.391 / −1.378 / −1.487. The monthly extremes run
from −8.354 (Dec-2025) to −0.512 (Apr-2024): no month, no tightness bin, no
year gets the body band to move up within the day.

---

## §B — task (b): the reserve-content decomposition on NEISO's OWN posted prices

**Rule 25 basis.** nyiso-110 measured this construction on NYISO's market and
its verdict transfers nothing. The measured side here is ISO-NE's own posted
reserve clearing prices, pulled from two public reports and never fed to a
solve (rule 13):

* **real time** — *Final Hourly Reserve Zone Prices & Designations*
  (`transform/csv/finalhourlyreserveprice`), location `7000 = ROS` (the
  system-wide row the model's reserve requirement consumes), Ten-Minute
  Spinning (TMSR) clearing price — the top of ISO-NE's cascade and therefore
  the same conservative single-product opportunity-cost proxy `spin_10` was at
  NYISO. 26,275 ROS hours over 2023–25.
* **day ahead** — *Day-Ahead Hourly Reserve Requirements Prices Designations
  and Forecast* (`transform/csv/daasreservedata`), the DASI product.

Model side: the keeper's own `hourly/system_<year>.parquet` `reserve_price`
column, load-weighted on the C3a basis.

### B1 — the model's reserve pricing is dead here too, but the market's is NOT everywhere

| | 2023 | 2024 | 2025 |
|---|--:|--:|--:|
| model reserve dual > 0 (hours of 8,760) | **0** | **0** | **0** |
| model dual, peak-window mean | $0.00 | $0.00 | $0.00 |
| measured RT TMSR, peak-window mean | $4.21 | $6.73 | $6.21 |
| — share of peak-window hours > $1 | **23.4 %** | **23.4 %** | **20.7 %** |
| — $200-censored | $3.47 | $3.95 | $4.08 |
| measured RT TMSR, trough-window mean | $0.06 | $0.10 | $0.10 |
| measured RT TMSR, all-hours mean | $1.35 | $1.68 | $1.78 |
| measured RT TMSR, hours > $1 (of 8,760) | 1,113 | 1,070 | 934 |
| measured RT TMOR (30-min), all-hours mean | $0.46 | $0.76 | $0.94 |

The keeper's own dormancy is confirmed exactly as attested — **$0.00 in all
26,280 train hours** — so the model side matches NYISO's. **The market side
does not.** NEISO's RT reserve price is **$0.00 at the median hour** (p90
$1.21) and clears above $1 in only ~21–23 % of peak-window hours, against
NYISO's DA spin > $1 in **100 %** of them. And it is **materially event tail**
where it is non-zero: $200-censoring cuts the peak-window mean by 18–41 %
(NYISO: ≤ $1.2, i.e. ≤ 13 %). Reserve formation at NEISO is a scarcity
phenomenon, not an everyday one.

### B2 — the swing arithmetic: reserve owns a MINORITY, and NYISO's dominance does not reproduce

Reserve differential = measured peak-window minus trough-window TMSR; missing
swing = (actual peak−trough) − (model peak−trough), both on the charter's
hours-beginning 16–19 / 01–04 windows.

| basis | | 2023 | 2024 | 2025 |
|---|---|--:|--:|--:|
| DA | reserve differential (RT-price proxy) | 4.15 | 6.62 | 6.12 |
| | missing swing | 14.00 | 17.28 | 22.87 |
| | **share owned by reserve** | **29.6 %** | **38.3 %** | **26.7 %** |
| RT | reserve differential | 4.15 | 6.62 | 6.12 |
| | missing swing | 12.45 | 15.48 | 19.12 |
| | **share owned by reserve** | **33.3 %** | **42.8 %** | **32.0 %** |

Against NYISO's 64–89 % (DA) / 97–131 % (RT). Passthrough tells the same
story from the other side: regressing the hourly peak-window miss on the
$200-censored measured reserve price gives **RT slope +0.96 / +1.99 / +1.29
(r +0.39 / +0.57 / +0.51)** — the RT reserve component does pass through
roughly dollar-for-dollar where it exists, exactly as at NYISO — but **DA
slope +0.15 / +0.46 / +0.09 (r +0.12 / +0.30 / +0.05)**, essentially none.
Which is what the market design predicts:

### B3 — the structural asymmetry, measured not assumed: NEISO had NO day-ahead reserve product

ISO-NE's Day-Ahead Ancillary Services (DASI) went live **2025-03-01**. The
DAAS report returns a header-only response with **zero data rows** for
2025-01-01 and 2025-02-01 and its first data row is **2025-03-01** — so for
**100 % of 2023, 100 % of 2024 and the first 16 % of 2025** there is no
day-ahead reserve clearing price at all, and the DA LMP those years carries
**no reserve content to strip**. NYISO posted DA spin in every hour of every
year on record. The DA rows in B2 therefore use the RT differential as an
**upper-bound proxy** and the true DA reserve content in 2023–24 is **zero**:
**NEISO's DA amplitude gap in the two full pre-DASI years is 100 % energy-side
by market design.**

Where the DA product does exist (2025-03-01 → 12-31, 7,343 ROS hours) it is
large and everyday — DA TMSR > $1 in **83.8 %** of peak-window hours, peak
mean **$32.70** (median $17.89), trough mean $6.55, all-hours $15.25, and
$200-censoring moves the peak mean only $32.70 → $31.46, so it is *not* tail —
with a clean diurnal profile ($6.1 at HE04 → $37.5 at HE19). Over that window
the reserve differential ($26.16) exceeds the whole DA missing swing ($22.26),
**117.5 %**. Reported against interest and bounded honestly: the naive strip
**over-corrects** — subtracting the full DA TMSR flips the model to **150.9 %**
of the reserve-stripped actual swing — so DASI reserve prices do **not** enter
the DA LMP one-for-one (they are a co-optimized product with its own
settlement, not an additive LMP component). The passthrough slope **+0.60
(r +0.65)** is the better-identified number: ≈ 0.60 × $26.16 ≈ $15.7, or ~70 %
of that window's missing DA swing. **This is a post-2025-03 statement only and
cannot be extended backwards** — and the amplitude ratio barely moved across
the DASI seam (27.1 / 23.6 / 29.9 % of DA in 2023/24/25), which is itself
evidence that the DA reserve product is not what the model's gap is made of.

### B4 — the energy-basis restatement: NEISO's miss is in the TROUGH, not the peak

Strip the measured RT reserve content from the RT actual and the model's own
(zero) folded dual from the model price; compare energy-only to energy-only.
Bounding in the same direction nyiso-110 flagged (this strips *at most* the
true content).

| year | RT energy trough err | RT energy peak err | model RT energy swing as % of actual's |
|---|--:|--:|--:|
| 2023 | **+7.56** | −0.75 | **43.3 %** |
| 2024 | **+9.15** | +0.29 | **40.9 %** |
| 2025 | **+9.93** | −3.08 | **48.9 %** |

**This is the sharpest contrast with NYISO in the whole finding.** At NYISO the
model over-priced BOTH ends by $3–7 and its energy-only swing was ~100 % of the
reserve-stripped actual — the energy side was *fine* on amplitude and the whole
defect was reserve. At NEISO the model's **peak is right to ±$3** and its
**overnight trough is $7.6–9.9 too dear**, leaving the energy-only swing at
**41–49 %** of the actual's. NEISO's amplitude defect is an over-priced
overnight trough on the energy side. Rule 25 holds in both directions: this is
NEISO's answer, measured on NEISO's data, and it is not NYISO's.

---

## §C — the demand limb: admissible, unidentifiable in one respect, and wrong-signed

**K3(i) EXISTS — the nyiso-94 blocker does not bind at NEISO.** ISO-NE's
`hbdayaheaddemandbid` is a *submitted* book with a price axis: Bid Types
`FIXED` (price-insensitive physical MW, no price), `PRICE` (price-sensitive
physical demand), `DEC` (virtual load) and `INC` (virtual supply), up to 50
(price, MW) segments each. Measured on six probe days spanning all three years
— one of which (2023-01-17) is one of the endpoint's documented empty postings,
the other five carrying 10,873–14,967 bid-hour rows each, with all four bid
types present in every non-empty day and **165,558–219,140 MW of PRICED segment
MW** against 217,235–311,848 unpriced. NYISO's lane died at exactly this gate;
NEISO joins PJM and MISO as an ISO that publishes the curve.

**Ladder semantics IDENTIFIED, not assumed** (the miso-105 discipline). The
report carries no cleared-MW column, so MISO's identification route is
unavailable; instead all four readings were crossed against the *published*
hourly DA cleared demand (`hourlydayaheaddemand`). The **cumulative** readings
never bracket the cleared quantity in **any** of 900 sampled hours — refuted
outright — while **incremental with INC netted** brackets it in 898. The MW
columns are incremental block widths, the same convention the offer report
uses.

**K3(ii) does NOT fire.** On 39 sampled operating days (the 15th of every month
2023–25 plus the five 2025 event days):

| ladder reading | n hours | median \|λ0 − DA\| | mean | within $2 |
|---|--:|--:|--:|--:|
| incremental, INC netted | 898 | **$5.29** | $12.23 | 27.3 % |
| incremental, INC ignored | 901 | $539.00 | $481.41 | 3.3 % |
| cumulative (either) | **0** | — | — | — |

λ0 misses the posted price by a median $5.29 (bar: ≤ $2), and the book's
stiffness is **0.033 GW/$** against the submitted offer book's **0.196 GW/$**,
a displacement share of **12.7 % median / 15.8 % mean** (≥ 30 % in 9.7 % of
898 hours) against a 30 % bar. Both kill conditions fail, so **the demand limb
is admissible** — it would not turn the model's price into the book's price.

**But its premise is FALSE and its sign is WRONG.** PJM's lever runs on +7–11
GW of net DEC at the top summer hours. NEISO's net virtual position, evaluated
at the posted DA price on the same sample:

| year | peak-window net | trough-window net | differential | implied Δ diurnal spread |
|---|--:|--:|--:|--:|
| 2023 | **−0.41 GW** | +0.13 GW | −0.54 GW | **−$2.76** |
| 2024 | **−0.25 GW** | +0.02 GW | −0.27 GW | **−$1.37** |
| 2025 | **−0.24 GW** | +0.07 GW | −0.31 GW | **−$1.60** |

(at the measured supply-stack slope 5.09 $/GW). The hour-of-day profile is a
midday virtual-**supply** position — net −1.34 GW at HE13, the solar-hours
convergence play — recovering to ≈ 0 overnight. Arming a faithful DA-depth
mechanism at NEISO would **subtract $1.4–2.9 of diurnal spread** from a model
that already produces only 24–30 % of the measured amplitude. Physical demand
is 67.6 % price-insensitive (`FIXED` as a share of the published cleared
quantity, median hour), and the price-sensitive remainder is *elastic* — adding
it shaves peaks. Both channels push the same wrong way.

This is the third independent per-ISO refusal of the same family on three
different grounds — PJM's premise is true (`K`), MISO's book is an attractor
(`G`), NYISO's book is unidentifiable (`G`), and NEISO's book is identifiable,
non-attracting, and **short at the peak** (`R`). Rule 25 is doing real work
here: four ISOs, four different answers.

---

## §D — what the measurement DOES point at: the traversal, not the conduct

Report-only, price-free, **not a kill-rule input**: the same corpus, read as an
aggregate submitted supply ladder (every (price, ΔMW) segment of every offering
asset, sorted, cumulated) instead of as per-asset conduct.

**Conduct at constant quantity — inverted, in every read.** The marginal
submitted-offer price at a fixed *relative* depth (q = 80 % of the hour's own
offered capacity) has a hod range of $12.85 / $7.49 / $3.51, peaking at
**HE2 / HE3 / HE6** and troughing at **HE19 / HE19 / HE11**. At a fixed
*absolute* 18 GW the range is $10.75 / $6.78 / $7.66, peaking at
**HE1 / HE3 / HE1**. The hour's total offered capacity barely moves
(range 1,064 / 131 / 308 MW). Read together with §A: hold the quantity still
and the real book gets *cheaper* into the evening.

**Traversal at the real quantity — correctly phased, and larger than the
model's.** Crossing the same book at the measured hourly ISNE demand:

| year | book at demand | at demand − 3 GW | model | DA actual |
|---|--:|--:|--:|--:|
| 2023 | **$17.03** (max HE21 / min HE7) | $9.44 | $7.03 | $25.96 |
| 2024 | **$21.11** (max HE21 / min HE5) | $9.73 | $6.82 | $28.96 |
| 2025 | **$24.06** (max HE20 / min HE7) | $13.75 | $13.30 | $44.47 |

as a share of the measured DA hod range: **65.6 / 72.9 / 54.1 %** at demand,
**36.4 / 33.6 / 30.9 %** at demand − 3 GW, against the keeper's **27.1 / 23.6 /
29.9 %** (which the probe reproduces exactly — the xiso-1 NEISO row, recomputed
here from an independent path as a loader check).

**Stated with its own weakness.** The traversal read is **depth-sensitive**:
a flat 3 GW import allowance — roughly NEISO's HQ + NB net position — halves
it, and at that depth the real book's traversal is only ~4–7 pp above the
keeper's own. Published DA cleared demand is itself below metered load (the
sampled hours clear ~78 % of it), so the correct crossing quantity is *cleared
demand net of scheduled imports and cleared virtual supply*, which this Phase-0
did not reconcile. **What survives the sensitivity is the direction, not the
magnitude:** the real book's marginal price traverses at least as much as the
model's and probably substantially more, it peaks in the right hour (HE20–21),
and none of that amplitude comes from within-day offer movement — the movement
is negative. **The model's within-day offer surface is therefore not the
binding constraint on NEISO's amplitude; the shape of its stack in the QUANTITY
dimension is the live suspect.** That is a different mechanism from the one
this charter authorized (matrix family `use_campd_bins` / `plant_level_fleet` /
the tranche construction, not `da_virtual_bids`), it is a rule-14
`[R-ACCURATE]` comparison against a measured book rather than a residual fit,
and under §5.6 frontier discipline it needs **its own charter**. Named here,
not pre-registered, and explicitly routed to the owner (§E).

---

## §E — governance, DO-NOT-REDO, and what this licenses

**Governance.** Years 2023–2025 only; the holdout spend freeze is ACTIVE;
NEISO's locked test is SPENT and untouched; nothing outside the training window
was read (rule 22). No LP was solved, no `ScenarioConfig` field was added or
changed, no keeper moved, no bundle was written, no dashboard registration was
made (rule 15 binds bundles; there is none). Every measured price here is a
validation target and enters no solve (rule 13). Two new raw sources are
documented and gitignored with committed regenerators
(`data/raw/NEISO-AS/reserve-prices/`, `data/raw/NEISO-AS/da-demand-bids/`);
neither is read by any `data/` loader or any derive.

**Reported against interest.**
1. The charter's theory of change is not merely unsupported — the measured sign
   is **opposite** to it on both limbs. That is recorded as a refutation of the
   lane this session was sent to advance, not softened.
2. K3(ii) **did not fire**. The demand limb passes its own pre-registered kill
   and is closed on materiality instead, which is a weaker basis than a fired
   kill; a successor that disputes the materiality reading has a live route,
   and the sample is 39 days, not the full corpus.
3. §B3's post-DASI DA number (117.5 % of the missing swing) is the single
   largest reserve share measured anywhere in this finding, and it is quoted
   with its own over-strip disproof rather than as evidence for the reserve
   story.
4. The auxiliary traversal read is a **diagnostic**, not a mechanism, and the
   successor it names is unadjudicated.

**DO-NOT-REDO.** Do not re-measure the supply-conduct limb: the corpus is
regenerable and the probe re-runs it, but the answer (flat, negative,
73 % bit-flat) will not change, and re-conditioning it on anything price-shaped
is barred by K2. Do not re-open the DA-depth limb at NEISO without new evidence
that overturns the net-short measurement in §C. The neiso-74 storage
DO-NOT-REDO and the xiso-1 standing order are untouched by this session.

**Owner routing (task (c) — the closure, and what replaces the lane).**

1. **The neiso-75 charter's L1 is CLOSED at Phase-0.** No solve arm is
   pre-registered; the charter's Phase-1 gates G1–G5 are never reached because
   neither limb produced a mechanism to gate. `da_virtual_bids` NEISO
   `O → R` (tested & rejected, no solve spent) — distinct from MISO's and
   NYISO's `G`, which were refusals *ex ante*.
2. **C3c-2023 is unchanged and still routed to the owner** (charter §5, three
   options: accept the ledgered caveat / a winter-fidelity lane / a
   representation change). Nothing measured here touches it: the 2023 gate's
   ceiling is the real DA book's own 5 tail hours against a floor of 8, and
   §A shows that book is *flatter* than the model's, which if anything
   hardens charter §2.4.
3. **C3c-2025 loses its named lever.** neiso-75 sized the 2025 gate as
   closable by the amplitude lane (CF-A prints 25 h inside [10, 40] on the
   five real event days). That sizing stands; what this session removes is the
   *route* — the amplitude cannot be reached through DA-bid conduct or DA
   depth.
4. **NEW CHARTER REQUESTED, not opened: the stack-traversal identification**
   (§D). The one route the measurement points at is a rule-14 comparison of
   the model's own tranche offer curve against the real submitted book at
   matched quantities, with the crossing-quantity reconciliation (cleared
   demand net of scheduled imports and cleared virtual supply) as its first
   task and the depth sensitivity in §D as its first hazard. It is a different
   matrix family and §5.6 frontier discipline requires its own charter; this
   session opens none.
5. **The rubric diurnal-amplitude criterion** (owner call, filed neiso-74,
   re-filed xiso-1, sharpened nyiso-110, re-surfaced neiso-75) now has a
   second ISO's decomposition to weigh against NYISO's, and they **disagree**
   (§B4). That is the material new input: the owner is not choosing a
   criterion for one shared defect with one shared cause — at NYISO the
   defect is reserve formation, at NEISO it is an over-priced overnight
   energy trough. No scorer was changed here either.

**This licenses nothing.** No adder, multiplier, hinge or offer-shape parameter
sized to the amplitude gap or to the trough residual is admissible (rules
1/5/13/21/24), and the measurement's own finding — that the real book is FLATTER
within the day than the model's — removes the last argument that a within-day
offer-shape knob would be "measured".
