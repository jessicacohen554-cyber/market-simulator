# ERCOT-102 — the measured AS holdout is ALREADY in the keeper and NON-BINDING; the 2023–2025 scarcity-tail bound is confirmed, not overturned

**Session 2026-07-24. Keeper: `2026-07-23-ercot100-netrev-margin-keeper`
(NOT-YET, C6 unattested). Successor to ERCOT-101, which the owner REOPENED to
test the hypothesis that the 2023–2025 scarcity under-pricing is a structural
AS-holdout (energy-supply) miss rather than an RT-conduct bound.** This lane
changes NO solve input and produces NO new keeper — every number is from the
committed `ercot100` keeper sidecars + committed measured corpora + code (all
no-LP).

Probes (all no-LP): `scripts/probes/ercot102_reserve_slack.py` (the HIT/MISSED
reserve-binding split — the decisive diagnostic), `ercot102_as_holdout_
attribution.py` (the co-opt requirement IS the measured plan; the "504" is a
net-of-credit residual), reusing `ercot101_price_decomp.py`.

## 0. Verdict

**The AS-holdout thesis is refuted as a repricing lever — because the model is
ALREADY doing it.** The keeper co-optimization requires the full measured
ERCOT ASPLANNP433 plan every hour (RegUp + RRS + ECRS + NonSpin), and holds
RegUp/RRS/ECRS **rigidly at VOLL** (the `ercot_nonreleasable_as_withholding` +
`ercot_ecrs_conservative_deployment` withheld families — the exact energy-supply
carve-out the charter asks for). At the 2023 missed tail hours that holdout is
**SLACK (reserve dual ≈ $0)**, not deficient: the model carries enough spare
responsive headroom (phantom online capability) that neither the measured-AS
families nor the ORDC total-reserve span tighten. Holding *more* measured AS out
cannot lift the missed-hour energy dual when the AS already held there has slack.
Forcing it to bind by capping the headroom **over-fires** — separately built,
identified, and rejected as ercot41/ercot43 (`docs/handoffs/ercot-online-
capacity-envelope-2026-07.md`). The 2023 tail residual therefore stays what
ERCOT-101 found: RT re-offer conduct with no 2023 SCED source. **This SHARPENS
the ERCOT-101 attributed bound; it does not supersede it.**

Keeper UNCHANGED. No solve, no dashboard run, no tuning (rules 1/11/13).

## 1. The charter premise is factually incorrect: the co-opt uses the MEASURED plan, not a formula

The charter's Lane A rests on "the co-opt uses a FORMULA (`ERCOT_AS_ECRS_BASE_MW
=950`, capped [500,3300]) that under-holds ECRS ~1,400 MW … the flag that feeds
the MEASURED ASPLANNP433 plan — `ercot_ecrs_requirement` — is OFF." Reading the
code, that is not how the keeper is wired:

* The keeper is `ercot_multiproduct_as_coopt=True`, so `get_reserve_design`
  dispatches to **`_ercot_multiproduct_design`** (`reserves/spec.py:483`), never
  the single-product `_ercot_design`.
* In the multiproduct builder, each product's requirement is
  `req_t = ercot_as_forward_requirement_mw(config, code, …)`; that returns
  **`None`** whenever `ercot_as_forward_requirement=False` (the keeper/backcast
  value — the forward formula is the *forecast* path only), so the code falls
  through to `req_t = ercot_as_plan_requirement_mw(year, T, code)` — **the
  measured ASPLANNP433 plan** (`spec.py:1007-1011`).
* The forward formula (`ERCOT_AS_ECRS_BASE_MW` etc.) is therefore **never
  evaluated** in the keeper.

`ercot102_as_holdout_attribution.py` confirms the requirement the co-opt demands
equals the measured plan, Jun–Sep means (MW):

| product | 2023 | 2024 | 2025 |
|---|---|---|---|
| REGUP | 389 | 399 | 426 |
| RRS | 2629 | 2383 | 2381 |
| ECRS | 1918 | 2054 | 1571 |
| NSPIN | 2656 | 2431 | 2640 |
| **ONLINE held out (RegUp+RRS+ECRS)** | **4936** | **4837** | **4378** |

Those `4936 / 4837 / 4378` are *exactly* the charter's own "measured ONLINE AS
held out" figures — because they are the same measured series. The co-opt is not
under-holding the plan; it **is** the plan.

**Where the charter's "co-opt holds RegUp 177 + RRS 859 + ECRS 504 ≈ 1,540 MW"
comes from:** those are the **net-of-credit THERMAL residuals**, not the total
held. The measured 60-Day-DAM battery AS award (`ercot_storage_as_product_credit`
— 1.5 / 2.2 / 3.1 GW in 2023/24/25) and the Load-Resource RRS credit
(`ercot_load_resource_reserve`) net off the requirement, because batteries and
load resources really do supply that AS in the real market. What is left for the
*thermal* fleet to hold (~2.6 GW in 2024 before the LR credit, ~0.9 GW RRS after)
is smaller than the plan — but that is a **correct** representation, not a
deficit. The full measured plan is required and held; the credited part is
supplied by the resources that supply it in reality.

## 2. Lane A (decisive): the measured holdout is present, rigid at VOLL, and NON-BINDING at the missed hours

`_ercot_multiproduct_design` builds `RegUp_withheld` / `RRS_withheld` /
`ECRS_withheld` families with `ordc_penalties = [VOLL]` over their published
non-releasable windows (RegUp/RRS through RTC+B go-live 2025-12-05; ECRS through
the 2024-08-01 release reform) — capacity SCED cannot release at any price, i.e.
the measured AS carved out of the SCED-dispatchable range. That is the
energy-supply holdout the charter describes, and it is already on.

`ercot102_reserve_slack.py` splits the actual `>$300` tail into HIT (model also
priced scarcity) and MISSED (model priced sub-scarcity) and reads the reserve
dual (`reserve_price` = **sum of every co-opt family's balance dual**, incl. the
rigid VOLL withheld families) from the committed keeper sidecar:

| year | actual>$300 | MISSED (model<$200) | reserve binds at MISSED | HIT (model≥$200) | reserve binds at HIT |
|---|---|---|---|---|---|
| 2023 | 147 h | 88 h, model $104 / act $862 | **2/88, mean $0.1** | 59 h, model $1443 | 52/59, mean **$4,088** |
| 2024 | 28 h | 23 h, model $79 / act $922 | 3/23, mean $2.9 | 5 h, model $1985 | 4/5, mean $6,616 |
| 2025 | 18 h | 18 h, model $73 / act $576 | 0/18, mean $0.0 | 0 h | — |

And the clean control: **in the hours the model DOES price scarcity (>$300), the
reserve co-opt binds 41/42 (98%) in 2023 and 4/4 in 2024.** The mechanism is the
model's own scarcity-price-former, and it works — *when the headroom is scarce
enough for it to bind.* At the MISSED hours it is slack. The ORDC settlement
adder is likewise ≈ $0 there (`ordc_adder` mean $0.0). So the missed tail is
priced low **not** because the measured AS is un-held, but because the model
carries spare responsive headroom the real 2023 grid did not, so the (fully
held) AS reserve sits with slack.

This is the same object seen from the reserve-demand side: the model's ORDC
total-reserve span (~10.7 GW) and the measured-AS families are BOTH met with
slack at the missed hours, i.e. the model has ≳ the full ORDC span of spare
eligible headroom there, where the real 2023 system retained only ~5.7 GW
(PRC). The mismatch (too much phantom headroom **and** — separately — an ORDC
demand span larger than the market held) currently cancels into "slack + high
demand = slack = under-price."

## 3. Lane A1 no-op proof: `ercot_ecrs_requirement` is dead on the keeper

The charter's Lane A1 ("`ercot_ecrs_requirement=true` adds the measured ECRS
plan to the reserve-balance RHS") was launched last session as
`results/calibration/ercot101_ecrs_req_probe` (bundle lost with the bare
container). It does not need re-running: `ercot_ecrs_requirement` is read **only
in the single-product `_ercot_design`** (`spec.py:904`) — never in
`_ercot_multiproduct_design`. On the multiproduct keeper the flag is
byte-identical (the CLI path at `run_calibration_full.py:3121` only records it in
`run_config.json`). Running the probe would burn ~30 min of billed per-plant
solve to reproduce the keeper exactly; the code trace is the answer. (And it
would in any case be redundant with §1: ECRS is *already* required at the
measured `ercot_as_plan_requirement_mw` level in the ECRS product family.)

## 4. Lane B: no double-count; the composition is already sound

The existing AS stack composes correctly and leaves no room for an additive
holdout without double-counting:

* **Per-product families** hold RegUp/RRS/ECRS/NonSpin at the measured plan;
  RegUp/RRS/ECRS are the VOLL-withheld carve-out (§2). **NonSpin** is held via
  the normal ramp, not the VOLL families (correct — NonSpin is largely offline,
  not part of the online energy stack; the charter agrees it must not be carved
  out of energy).
* **Supply credits** (measured battery award, Load-Resource RRS) net the
  requirement down so the co-opt does not pull the batteries'/LRs' AS from
  thermal headroom — the measured AS→energy relationship, not a fit.
* **`ercot_storage_as_deployment`** returns awarded battery AS to energy at the
  ramp — the mirror of the holdout; holdout (credit) and return net to the
  measured battery net position.
* **`ercot_ordc_total_reserve`** (the RTORPA lumped ORDC on total online
  reserves) is layered on top as an all-class family and explicitly does NOT
  re-add ECRS (`spec.py:1351`).

Adding `ercot_ecrs_requirement` (single-product ECRS add-on) on top of the
multiproduct ECRS family would double-count the ECRS demand — which is exactly
why the multiproduct builder does not read it.

## 5. Why forcing the holdout to bind over-fires — the ercot41/ercot43 convergence

To make the (already-held) measured AS actually tighten the missed hours you
must remove the phantom headroom so the reserve competes with energy for the
real online capability. That is the on-line-capacity envelope, and it was built,
identification-gated to the measured RTOLCAP band (±2%), and A/B-solved full-span
in two variants — **both REJECTED** (`docs/handoffs/ercot-online-capacity-
envelope-2026-07.md`):

* base grain (ercot41): 2023 hub $46.5 → **$347**, C3a +797%, C3c 0.30×→2.29×.
* extreme-peak-resolved (ercot43): 2023 → **$455**, C3a +708%; lifts 2024
  (+61.4%), a current-design year → rejection on the §6.1 rule alone.

The recorded root cause (§7.4 there): *no supply-side cap that reproduces the
measured on-line capability can price the 2023 tail correctly while the co-opt
demands energy + the full ORDC total-reserve span (~10.7 GW) inside it, because
the real 2023 market operated ~5 GW below that span and priced scarcity through
ENERGY offers ($1.84 mean RTORPA), not the reserve adder.* That is the same
finding this lane reaches from the reserve-slack side, and the same wall
ERCOT-101 reached from the offer side (no 2023 SCED re-offer source).

## 6. The genuine frontier — reserve-DEMAND right-sizing (owner-sanctioned round, NOT this session)

Both the ercot43 §7.4 conclusion and this lane point at the reserve-**demand**
representation, not offer heights and not on-line capability. The untested lever
is to right-size BOTH sides of the current cancellation to what the 2023 market
actually held (~5.7 GW PRC): cap the responsive headroom at the measured RTOLCAP
**and** reduce the reserve demand from the ~10.7 GW ORDC total-reserve span
toward the measured AS plan, so the holdout binds at the measured level instead
of the ORDC span. This **re-opens the ORDC-family design that rule 26 froze**,
so it needs its own owner-sanctioned design round (rule 1: real market
structure; the change is not a probe to launch unilaterally). A first-order check
tempers even that path: after the correct battery + LR credits, the *thermal*
AS demand is only ~1.5 GW, well below the envelope's collapsed room (~5.4 GW),
so a naive envelope+demand-swap likely lands inert (under) rather than on target
— the demand-side redesign has to be done carefully, not by flag composition.

## 7. What was NOT done, and why

* **No new keeper, no solve, no dashboard run.** The charter's Lane A1/A2 knobs
  are a code-proven no-op (§3) / already-in-place (§1); the bind-forcing path is
  already-rejected (§5). There is nothing to solve that is not either inert or
  rule-26-gated.
* **No tuning.** The measured AS plan is the honest input and it stays (rule 11);
  the residual is not closed by an adder (rule 13), a residual-motivated
  requirement inflation (the holdout MW is the measured plan, never a swept
  knob), or a headroom cap that over-fires (rules 1/11).
* **The C6 governance route is unchanged from ERCOT-101.** If anything, this lane
  strengthens the exceptions ledger: the 2023/2025 price gates are accepted
  measured-input limitations, now independently confirmed from the reserve side.
  Owner sign-off still required (governance is not self-attested).

Next number: ercot-103.
