# 0017 — Storage charge policy: optional excess-clean-only provenance

- **Status:** accepted
- **Date:** 2026-07-04
- **Session:** storage-modeling audit 2026-07 (`docs/storage-modeling-audit-2026-07.md` in the repo root)
- **Implemented by:** `config.py` (`storage_charge_policy`), `lp.py`, `cli.py` (`--storage-charge-policy`)

## Context

In the PP-02 formulation storage charges from the aggregate node: the energy
balance lets `chg` be sourced from grid purchases, and discharge can be
exported as `excess` at LMP. The optimizer can therefore operate storage as a
merchant arbitrage asset (buy cheap grid energy, sell into peaks) whenever the
matching constraint leaves headroom. The accounting stays honest — grid
purchases count as unmatched at purchase time and carry residual CO₂ (ADR
0007/0013) — but the *portfolio decision* can then be shaped by trading rents
rather than clean-energy matching, and the stored energy has mixed provenance.

CFE accounting conventions for storage require charge-source attribution:
EnergyTag's granular-certificate rules and the 24/7 CFE compacts treat storage
discharge as carbon-free only to the extent it was charged from certified
clean generation; system studies (Riepin & Brown 2022; Xu et al. 2021,
Princeton 24/7) model participant storage as charging from the contracted CFE
portfolio, not the grid. A buyer whose storage is inside the Scope 2 boundary
typically cannot claim grid-charged discharge as matched, and many do not want
their matching tool recommending a trading book.

## Options considered

1. **Keep arbitrage-only (status quo).** Realistic merchant co-optimization,
   but the portfolio mix can be distorted by trading rents and stored energy
   has no clean provenance guarantee.
2. **Per-hour "charge ≤ clean generation minus load" (strict excess).**
   `chg_t ≤ max(0, Σgen_t − load_t)` is nonconvex (the max sits on the RHS of
   a ≤), so it cannot be expressed in the LP without integers — forbidden by
   the tool's LP-only design (ADR 0003; market-sim rule "no MIP").
3. **Per-hour provenance rows `Σ_s chg[s,t] + excess[t] ≤ Σ_r gen[r,t]`,
   optional.** Linear, one `T`-row block. Guarantees: charging is covered by
   contracted clean generation net of exports; exports come only from clean
   generation (grid buys and discharge can never be re-sold); via the energy
   balance, `grid_buy_t ≤ load_t − dis_t` and `dis_t ≤ load_t − grid_buy_t`,
   i.e. grid purchases and discharge serve load only.

## Decision

Option 3, as a config toggle: `storage_charge_policy = "arbitrage"` (default,
bit-identical to the historical behavior) or `"excess_clean_only"`. The rule
the code follows: when the policy is `excess_clean_only`, add the `T` rows
`Σ_s chg[s,t] + excess[t] − Σ_r gen[r,t] ≤ 0` to the LP, in both modes.

## Consequences

- Under `excess_clean_only`, storage is a pure clean-shifting matching device:
  no grid charging, no discharge export, no re-sold grid purchases. Frontier
  premiums will generally be equal or higher than under `arbitrage` at the
  same matching (arbitrage rents are given up); matching at a given premium
  can only fall or stay equal.
- Known residual (documented, accepted): "divert-and-backfill" — charging
  from clean generation in an hour where the grid still serves some load — is
  LP-representable because the strict per-hour excess bound is nonconvex
  (option 2). It remains honestly penalized: the induced grid purchase counts
  as unmatched and carries residual CO₂ at purchase time, so the optimizer
  only chooses it when the cost saving beats the matching/carbon cost it
  books. There is no accounting laundering in either policy.
- New config field flows into run metadata automatically (`asdict(config)`);
  CLI flag `--storage-charge-policy` overrides a config file (CL-1 pattern).
- Defers: per-technology policies (e.g. arbitrage batteries alongside
  provenance-bound LDES) and an iterated clean-fraction attribution of stored
  energy (the Riepin & Brown CFE-share approach) — add only if a use case
  demands them.
