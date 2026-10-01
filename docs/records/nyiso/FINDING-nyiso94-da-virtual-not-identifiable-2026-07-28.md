# FINDING — nyiso-94: the DA virtual-bid lever is NOT IDENTIFIABLE in NYISO, and could not reach C3c if it were (ex-ante, 2026-07-28)

**Verdict: `da_virtual_bids` is GOVERNANCE-REFUSED for NYISO — adjudicated
ex-ante, NO SOLVE SPENT.** The charter's own branch point fired at Step 1:
NYISO's published day-ahead grain cannot identify a PJM-form net virtual curve
without a fitted scalar, so no A/B was run and no run was registered.

Matrix cell `da_virtual_bids` × NYISO: **U → G**
(`docs/codebase-site/data/mechanism-matrix.js`, cat `offer`). Lever-queue
basis: `docs/mechanism-testing-matrix.md` §5.5 NYISO item **1** ("DA virtual
depth / DA demand formation … the only queue item aimed at where the misses
actually live") — this closes the queue head.

Reproduce: `uv run python scripts/probes/nyiso94_da_virtual_identifiability.py`
(fetches NYISO's public MIS at run time; `--biddata` adds the masked-archive
attempt).

**No keeper candidate. No dashboard registration** — rule 15 `[R-DASHBOARD]`
governs *completed runs*, and there is none (same posture as nyiso-93).

---

## 1. The one-line reason

**PJM's mechanism is admissible because PJM publishes the SUBMITTED bid curve.
NYISO publishes only the CLEARED volume, and publishes it without a price.**
One of those defects blocks identification (rule 21 `[R-DOF]`); the other
blocks admissibility (rule 13 `[R-MEASURED]`). They are independent, and each
is disqualifying on its own.

## 2. Source and vintage (Step 1 deliverable)

| feed | what it carries | grain | vintage |
|---|---|---|---|
| **NYISO MIS P-59 `zonalBidLoad`** | Energy Bid Load, Bilateral Load, Price Cap Load, **Virtual Load**, **Virtual Supply** | 11 NYISO load zones × hour | daily postings; monthly archives back to 2020. **26,301 h × 11 zones** pulled for 2023–2025 |
| **NYISO MIS P-27 `biddata_loadbids` / `_genbids`** | full bid curves incl. `Price cap N MW`/`N dollar` pairs | masked resource × hour | 3-month release lag (`NYISO 3 Month Bid Data Release Description_V1.pdf`) |
| **NYISO MIS P-58B `pal`** | actual load | 11 zones × 5 min | daily |
| **NYISO 2025 State of the Market** (in repo, `data/raw/NYISO/`) | published **cleared** virtual MW/h + IMM commentary | annual / by region | 2026-05-19 |

Everything below is measured from those feeds. **Nothing was committed under
`data/raw/`**: cleared virtual volume is a market *outcome*, and a measured
outcome parked in the input tree is a re-armable answer key (rule 26
`[R-DELETE]` in spirit). The probe re-fetches instead.

## 3. Blocker 1 — no price axis (rule 21 `[R-DOF]`)

`zonalBidLoad` gives **one MW number per zone-hour** for Virtual Load and one
for Virtual Supply. There is no price column. The PJM mechanism
(`src/market_sim/data/virtual_bids.py`) renders

> `net(λ) = Σ_{DEC bids ≥ λ} MW − Σ_{INC offers ≤ λ} MW`

and clears it endogenously against the model's own stack. Rendering `net(λ)`
from a price-free MW requires **assuming a price distribution** — a fitted
scalar whose only identification source would be the residual it is meant to
close. That is precisely rule 21's "a residual that can only be closed by a
tuned value is an open root-cause issue, not a parameter."

**The priced archive does not rescue it.** P-27 `biddata_loadbids` *does* carry
(MW, $) pairs — but NYISO's masking removes the resource-type flag, so virtual
load cannot be separated from physical price-capped load. Measured on June 2025
(1,099,217 bid rows):

| test | corr | level ratio |
|---|---|---|
| all price-cap MW vs published **Virtual Load** | 0.667 | 2.69× |
| all price-cap MW vs published **Price Cap Load** | 0.894 | 1.10× |
| all price-cap MW vs **their sum** | **0.912** | 0.78× |

The best correlate is the *sum* — i.e. the archive holds both categories mixed,
at neither category's level. A structural split was attempted and also fails:
834 sinks carry price caps with **no** `Forecast MW` and **no** `Fixed MW`
(a clean partition — **zero** overlap with the 1,350 physical sinks), but they
total **2.46×** the published Virtual Load, so that signature is a mixture too.
The archive additionally carries superseded submissions (its `Forecast MW`
total is 2.14× the official Energy Bid Load), so even the physical categories
do not reconcile.

## 4. Blocker 2 — the published series is CLEARED, not submitted (rule 13 `[R-MEASURED]`)

The `zonalBidLoad` virtual columns reproduce the NYISO IMM's published
**cleared** virtual volumes (2025 SOM Figure 24) to within 1–2 MW:

| year | measured VL | SOM cleared VL | measured VS | SOM cleared VS |
|---|---|---|---|---|
| 2024 | 1,090 | **1,089** | 1,275 | **1,275** |
| 2025 | 1,052 | **1,051** | 1,329 | **1,327** |

That settles the provenance question empirically: **these are outcomes.** PJM's
lever passes rule 13 precisely because `hrl_da_incs_decs` is the *submitted*
curve — participant input, with clearing left endogenous to the LP. NYISO
publishes no submitted-curve equivalent at any grain. Injecting cleared virtual
MW is feeding a measured *result* back into the model, which is the forbidden
class, not the admissible one.

## 5. Blocker 3 — the PJM premise is empirically FALSE in NYISO

PJM's mechanism exists because its DA market clears **more** than the physical
load the model serves (+7–11 GW net DEC at the top summer hours). NYISO's does
the opposite.

**Net virtual is negative in the mean hour** — virtuals make NYISO's DA
*shallower*, not deeper:

| year | Virtual Load | Virtual Supply | **net virtual** |
|---|---|---|---|
| 2023 | 1,207 | −1,437 | **−230 MW** |
| 2024 | 1,090 | −1,275 | **−186 MW** |
| 2025 | 1,052 | −1,329 | **−277 MW** |

**And the whole DA book sits below RT load.** DA total (physical + net virtual)
minus RT actual load: **−846 / −859 / −869 MW** on the annual mean, and
**−1,255 / −907 / −827 MW** in the measured RT>$300 tail hours. NYISO's own IMM
says the same thing in its own words (2025 SOM p.47): *"net scheduled load in
the day-ahead market was approximately 96 percent of actual NYCA load during
daily peak load hours in 2025."*

At the peak the net position does flip positive — but an order of magnitude too
small to be PJM's lever:

| year | net virtual in measured RT>$300 tail | as % of RT load | top-100 load hours |
|---|---|---|---|
| 2023 | +580 MW | 2.5 % | +1,387 MW |
| 2024 | +293 MW | 1.3 % | +868 MW |
| 2025 | +917 MW | 3.3 % | +1,340 MW |

PJM moved C3c on +7,000–11,000 MW. NYISO's is +0.3–0.9 GW — roughly a tenth.

## 6. Blocker 4 — roof-blocked, verified on the keeper's own output

Even granting the mechanism, it cannot produce a >$300 hour. From
`results/calibration/nyiso92_hydro_envfloor` (the current keeper,
`2026-07-28-nyiso-92-hydro-envelope`) — annual max zonal dual:

| zone | 2023 | 2024 | 2025 | hours >$258 | hours >$300 |
|---|---|---|---|---|---|
| Upstate_West | 149.9 | 194.5 | 255.1 | 0 / 0 / 0 | 0 / 0 / 0 |
| Capital_Hudson | 149.9 | 194.5 | 255.1 | 0 / 0 / 0 | 0 / 0 / 0 |
| Lower_Hudson | 149.9 | 194.5 | 255.1 | 0 / 0 / 0 | 0 / 0 / 0 |
| NYC | 149.9 | 194.5 | 255.1 | 0 / 0 / 0 | 0 / 0 / 0 |
| NYISO_external | 143.4 | 194.5 | 255.1 | 0 / 0 / 0 | 0 / 0 / 0 |
| **Long_Island** | 386.7 | 297.5 | 473.4 | 7 / 5 / 16 | **3 / 0 / 7** |

Three facts close it:

1. **All five mainland zones share one identical price** in every year — one
   uncongested marginal unit, topping out at the ~$258 dual-fuel oil-parity cap
   the LP documents (`model/lp/rows.py:211`; FINDING-nyiso-c3c §407–410:
   *0 mainland hours above $258 in all 26,280 hours*).
2. **Every model >$300 hour is Long Island**, and the whole C3c count (3/0/7)
   is LI's.
3. **Zero load-shed slack in all three years** — the model never exhausts
   supply, so added demand walks up a stack that simply has no rung above $255
   and never reaches the VOLL regime.

Adding +0.9 GW to a stack with nothing above $255 and GW of unused headroom
cannot make a >$300 mainland hour. And in the one zone that *can* exceed $300,
Long Island, the measured net virtual demand is only +211/+145/+249 MW. This is
the SRMC roof of nyiso-85 §7d, re-confirmed from the keeper's committed
sidecars rather than re-derived — C3c is roof-blocked, and a DA-depth lever
adds tightness, which is not what a roof-blocked tail is short of.

## 7. What the data DOES say — the zonal signature, and the successor lever

The one genuinely new structural fact this census produced: **NYISO's virtual
market is a congestion play, not a depth play.** In the measured tail hours,
net virtual by model zone (MW):

| zone | 2023 | 2024 | 2025 |
|---|---|---|---|
| NYC | +264 | +373 | **+872** |
| Lower_Hudson | +403 | +358 | +420 |
| Long_Island | +211 | +145 | +249 |
| Capital_Hudson | −255 | −400 | −403 |
| Upstate_West | −43 | −183 | −221 |

Net virtual **demand downstate, net virtual supply upstate** — which is
verbatim what the IMM describes (2025 SOM p.21): traders *"purchasing load
downstate and selling virtual energy upstate."* They are arbitraging the
downstate import constraint, not deepening system procurement.

**And that points at the actual missing mechanism.** The IMM's §D
(2025 SOM pp. 49–51) documents **Thunderstorm Alerts (TSAs)**: NYSRC rules
require NYISO to pre-secure the ConEd system as if the first contingency had
occurred, which *"routinely reduce[s] upstate-to-downstate transfer capability
by approximately 1 to 2 GW"* — **modeled in real-time only, never in the
day-ahead market.** The IMM's numbers:

* TSA events concentrate in **hours 13–21, May–September** — which is exactly
  where nyiso-92 dated NYISO's measured tail, and where the tail hours sit here
  (hour-of-day distribution 13–20 plus a winter-morning 6–8 cluster).
* On days with peak load > 26 GW, TSA congestion costs average
  **$300–$500/MWh** in hours with forecast TSA probability > 80 %.
* Of 1,377 hours evaluated, **50 hours carry 99 % of TSA congestion cost.**

The model has no TSA representation, and its own output shows the hole exactly
where the IMM predicts it: in the measured tail hours the keeper prices
**Lower_Hudson − Upstate_West at $0.5 / $0.0 / $0.0** and NYC − Upstate_West at
only $13 / $3 / $27. The model has essentially **no downstate congestion in the
very hours NYISO says downstate congestion runs $300–500/MWh** — a pocket the
IMM names (with NYC and LI) as *"prone to high real-time price spikes when
unforeseen transmission and/or generation outages occur."*

A TSA transfer-capability derate is a **physical availability event on a
transmission interface, driven by weather** — the same admissibility class as a
CAMPD outage window, and rule-13 forward-reproducible (the IMM built its own
forecast model from *publicly-available* weather data). It is a genuine
rule-1 `[R-STRUCT]` structural mechanism, it is aimed at the roof/congestion
that actually blocks C3c rather than at tightness the roof will swallow, and it
is **the recommended successor lever** for NYISO's queue head.

Two caveats, stated up front so the next session scopes it honestly: (a) it
needs a data intake (TSA event history, or a reconstruction from public
weather + NYISO's published GTDC/interface limits) that does not exist in-repo
today; and (b) NYISO's tail is RT scarcity while the model is scored on a
DA-expressible construction — a TSA lever must be argued on the RT side, not
smuggled in as a DA constraint.

## 8. DOF ledger

**No parameter added, no scalar fitted, no solve spent.** The keeper's DOF
ledger is untouched (20 entries / 6 residual). This finding's entire content is
that the candidate mechanism *would* have required a fitted scalar — which is
why it was refused rather than armed.

## 9. Rule 25 discipline

PJM's `K` was **not** ported and NYISO's `G` does not touch any other cell.
NEISO's cell stays `U`: it shares the two-settlement-DAM framing but is a
different market with different published grain, and per rule 25 it must derive
its own answer from its own data. Whether ISO-NE publishes a *submitted*
virtual curve is an open question this session did not test. The PJM `K` cell
is unaffected — PJM's data supports the mechanism; NYISO's does not.

## 10. DO-NOT-REDO

Do not re-open `da_virtual_bids` for NYISO on the current data grain. It would
be re-opened legitimately only by **new evidence of a submitted, priced NYISO
virtual curve** — i.e. NYISO beginning to publish a `hrl_da_incs_decs`
equivalent, or an authorized non-public data source. A price distribution
assumed onto the cleared MW is not new evidence; it is the fitted scalar this
finding refused.
