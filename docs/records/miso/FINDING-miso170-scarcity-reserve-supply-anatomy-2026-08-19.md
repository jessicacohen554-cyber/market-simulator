# FINDING miso-170 — why 2025 summer scarcity is still unreachable: the reserve requirement is met EXACTLY and priced at ZERO, on every family

**Session miso-170 (2026-08-19), addendum to the membership-repair result.**
**NO LP SPENT** — every number below is computed from the committed keeper's own
hourly sidecars (`results/calibration/miso170_membership_B/hourly/`). No
mechanism is tested, no cell verdict is minted, and the keeper
`2026-08-19-miso-170-membership` is unchanged.

This extends `FINDING-miso167-summer-scarcity-anatomy-2026-08-18.md` and
**partially supersedes its §4**, which is stated below.

---

## 1. The model is never scarce, in the physical sense

| | model 2025 | actual 2025 |
|---|---:|---:|
| hours > $200 (load-weighted hourly LMP) | **2** | **88** (RT) |
| hours > $150 | 7 | — |
| hours > $100 | 20 | — |
| max hourly LMP | **$227.34** | RT to $1,783 |
| p99 / p99.9 | $79.56 / $146.85 | — |
| **load shed (slack), whole year** | **0.0 MWh** | — |

In the 47 summer scarcity hours of `FINDING-miso167` §1 (mean load 115.4 GW):
model energy LMP **$72.74** + reserve adder **$10.81** = **$83.54**, against a
top-decile actual of **$110.42**.

Zero shed all year, against 11.5 GW of idle thermal capability at the peak
(miso-167 §2b). **Nothing in the LP is physically short in any hour of 2025**,
so no energy-balance dual can carry a scarcity signal.

## 2. The reserve requirement is met EXACTLY — and costs nothing

This is the correction to how the lane has described the reserve state. The
families are **not** slack. Across all three years and all four families the
median of `held_mw − requirement_mw` is **+0.00 %**, and the minimum is
**0.0 MW**: every family holds **exactly** its requirement, every hour.

What is zero is the **price**, not the slack:

**2025, the 47 summer scarcity hours** (total requirement 6,593 MW):

| family | requirement | dual > 0 (of 8,760 h) | mean dual, scarce h | max dual |
|---|---:|---:|---:|---:|
| `miso_rbdc` | 2,488 MW | **0** | $0.00 | $0.00 |
| `miso_subregional_or_midwest` | 2,073 MW | **0** | $0.00 | $0.00 |
| `miso_rbdc_regspin` *(gated at miso-169)* | 1,617 MW | 12 | $8.53 | $85.87 |
| `miso_zonal_or_miso_south` | 415 MW | 8 | $2.28 | $200.00 |

**4,561 MW — 69 % of the scarce-hour requirement — clears at a dual of exactly
zero in every hour of 2025.**

**The mechanism is FREE SUPPLY, not a loose constraint.** A tight constraint
whose supply has no alternative use has zero opportunity cost: reserves held on
idle, unsynchronised capacity displace nothing, so the shadow price collapses to
$0 even though the requirement is met to the megawatt. This is the miso-167 §4
diagnosis — *"an idle, unsynchronised CT's full pmax can satisfy MISO's
regulating and spinning requirement"* — measured at the price rather than the
quantity, and shown to apply to **every** family rather than only reg+spin.

**These families are not structurally incapable of pricing.** In 2024
`miso_rbdc` binds 6 h and `miso_subregional_or_midwest` 4 h. They price when
the free supply runs out; in 2025 it never does.

## 3. What miso-169 actually bought, and why it was small

`miso_reserve_online_gated` restricted reserve **supply** to synchronised
capacity for the Reg+Spin product. It worked, exactly as miso-167 predicted: the
`miso_rbdc_regspin` dual goes positive in **12 hours of 2025 (up to $85.87)**,
against **zero** hours for the two ungated families.

It moved C3a-2025 only +0.10 pp because **the gated family is 1,617 MW of a
6,593 MW requirement — 24.5 %**. The other 75 % is still backed by free supply,
so it still prices at zero, and the energy price is left carrying the entire
scarcity signal alone.

**This partially SUPERSEDES `FINDING-miso167` §4.** That section's diagnosis is
confirmed and its mechanism validated — but its implicit scope ("gate reserve
supply to online capacity and the constraint stops being dormant") was written
about the reg+spin family, and the measurement now shows the same free-supply
pathology on **3,000+ MW more requirement in two other families**. Gating one
family of four was always going to be a quarter of the available effect.

## 4. The RHO_CLIP band is NOT what throttles this — my own prior hypothesis, falsified

The standing nyiso-144 escalation is that MISO's arms solve at the uncited
`RHO_CLIP` floor **0.5** rather than the CAMPD-measured **0.1764**, a gate 2.83×
looser than MISO's own conduct supports. It was natural to suspect this was
throttling the mechanism. **It is not**, at least not at the grain the committed
artifacts expose:

| rho | market-wide coupling cap, 47 scarce h | vs the 1,617 MW requirement |
|---|---:|---:|
| 0.5 (solved) | 36.94 GW | **+35.33 GW of headroom** |
| 0.1764 (measured) | 13.03 GW | **+11.42 GW of headroom** |

At **both** values the coupling row sits **8–23× above** the requirement, so
tightening rho to the measurement would not, by itself, make the row bind more
often.

**Stated limitation, because it bounds the claim:** the coupling row is
per-pool (zone × fuel-class) and the committed `reserve_family` sidecar carries
family-level rows only, so this is an **aggregate** bound rather than a
pool-level proof. For the conclusion to flip, pool-level tightness would have to
be extraordinarily concentrated against an 8–23× aggregate cushion. **A
pool-grain re-measurement is the way to close it properly**, and it needs the
per-pool R columns that no committed MISO bundle carries.

Resolving the band remains worth doing on rule-21 grounds — an uncited
guardrail should not be choosing a keeper's coefficient — but it should **not**
be sold as the scarcity fix.

## 5. The lever this points at, and the prerequisite that may kill it

**Candidate:** extend online-gating to `miso_subregional_or_midwest`
(2,073 MW, zero-priced all of 2025), and possibly to the Reg+Spin component
inside `miso_rbdc`.

**THE PREREQUISITE, WHICH MUST BE SETTLED FIRST AND MAY END THE LANE.**
Supplemental reserve is, by MISO's own product definition, legitimately
providable by **offline quick-start** resources. Gating a supplemental
requirement to synchronised capacity would be **structurally wrong** — a
rule-1 `[R-STRUCT]` violation that would reach the right number through a
mechanism that is not real, which is exactly what this program forbids.

So before anything is armed, the sub-regional and RBDC requirements must be
**decomposed into their synchronised (regulating + spinning) and
non-synchronised (supplemental) components from MISO's published product
definitions** (BPM-002; Schedule 28). Three outcomes:

* **Mostly Reg+Spin** → the lever is real and sized at up to ~2 GW of
  additional gated requirement, roughly doubling to tripling miso-169's gated
  base.
* **Mostly supplemental** → **the lever does not exist**, the DA-foreseen half
  of the miss is closed along with the RT-only half, and MISO's C3a-2025 becomes
  a documented model-class limit end to end. That is a legitimate and valuable
  outcome; it must be reported as readily as a positive one.
* **Mixed** → only the synchronised share is gateable, and the prize scales down
  proportionally.

**No solve is justified until that decomposition is on paper**, because arming a
gate on a supplemental requirement would be a rule-1 breach whatever it did to
the residual.

## 6. What this finding does NOT change

* The keeper is unchanged; no mechanism was tested and no cell verdict minted.
* The **RT-only half** of the C3a-2025 miss (miso-167 §5: 27 of 47 hours, spikes
  at 98.7 GW that MISO's own DA market priced at $80) remains the model-class
  limit the miso-163 owner ruling closed. Nothing here reopens it.
* The `ordc_scarcity_overlay` refusal (MISO cell `G`) is untouched — this is the
  reserve **supply** side, not the demand curve.
* The honest ceiling stays miso-167 §5's **~+3.3 pp on C3a-2025** against the
  2.5 pp needed. miso-169 captured +0.10 pp of it.

## 7. Reproduction

Every number is a query over `results/calibration/miso170_membership_B/hourly/`
(`system_<year>.parquet`, `reserve_family_<year>.parquet`,
`class_hourly_<year>.parquet`), P1 rows only, plus `frontend/data/backcast/tail/
actual_tail.json` for the actual RT>$200 counts (2025: `rt_gt` = 88,
`rt_coverage` = 1.0). The 47-hour scarce set is the top-47 by system load within
Jun–Sep (hours 3624–6551), matching `FINDING-miso167` §1.
