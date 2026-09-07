# ADDENDUM nyiso-218 — the three `*_INTERMEDIATE` groups leave the override: 13 groups → 10, MEASURED byte-identical

**Written and pushed BEFORE the screen solve ran**, because it changes a gate declared in
`PREREG-nyiso218-fossil-energy-band-lift.md` §6 (S-1's expected band count). Nothing else in the
PREREG moves — the value stays frozen at 1.03, the band scope stays the three energy bands, every
`peak` stays frozen, and the screen year stays 2023.

## What happened

The launch of the screen arm was **refused by the driver's own validator**:

```
--offer-curve-json: unknown fleet class 'CC_INTERMEDIATE' — the offer-curve router only reads
['CC_CHP', 'CC_REGULAR', 'COAL', 'COAL_BIT', 'COAL_LIGNITE', 'COAL_PRB', 'COAL_WC', 'CT_CHP',
 'CT_PEAKER', 'ST_CHP', 'ST_GAS'].
```

`CC_INTERMEDIATE`, `CT_INTERMEDIATE` and `ST_GAS_INTERMEDIATE` are groups the **router cannot
resolve**: they exist in `offer_curve_by_group` only as targets of the `cc_intermediate_split` /
`ct_intermediate_split` / `st_gas_intermediate_split` gates, **all three of which are `false` in
this keeper** (PREREG §3 C-9). The validator is a guard, not a defect, and **routing around it —
writing values through the generic `--set` channel that the router provably cannot read — is
exactly the off-registry manoeuvre rule 24 `[R-REGISTRY]` exists to discourage.** So they come out
of the override.

## The equivalence is MEASURED, not argued

Instrument: two `fleet_only` rebuilds of the keeper's 2023 fleet (zero LP), one carrying the
13-group override, one carrying the 10-group override; `mc_base` compared row-for-row.
Record: `results/calibration/_nyiso218_intermediate_drop_equivalence.json`.

| | |
|---|---|
| unit ids identical | **true** |
| `mc_base` shape equal | **true** (812 rows) |
| `mc_base` max abs diff | **0.0** |
| **bitwise identical** | **true** |

This corroborates phase-0 Part A independently: Part A measured the moved set as exactly
`{CC_CHP, CC_REGULAR, CT_CHP, CT_PEAKER, ST_GAS}` in every year, i.e. the three `*_INTERMEDIATE`
groups and the five COAL groups contributed **zero** moved rows. The 10-group override therefore
solves the same LP as the 13-group one, to the bit.

## What changes, exactly

* The lift is applied to **10 groups × 3 bands = 30 band values**, not 39.
  `CC_CHP`, `CC_REGULAR`, `COAL`, `COAL_BIT`, `COAL_LIGNITE`, `COAL_PRB`, `COAL_WC`, `CT_CHP`,
  `CT_PEAKER`, `ST_GAS`. The five COAL groups stay in (NYISO coal is 0.0 TWh in every year — they
  are lifted for config uniformity and are inert, exactly as the PREREG says).
* **S-1's expected count changes 39 → 30.** Every other limb of S-1 is unchanged and still binds:
  no non-`offer_curve_by_group` live field, no moved `peak` / `phys_*` / structural share, and
  every moved ratio exactly 1.03 to within 1e-9.
* No prediction in §5 changes, because the solved fleet does not change.

## A refinement to PREREG §3 C-8, in place

C-8 said `ST_CHP` "has NO `offer_curve_by_group` entry, so the authorized channel provably does not
reach it". The validator's list shows `ST_CHP` **is** a class the router reads — so the sharper
statement is: **the router would resolve `ST_CHP`, but this keeper's `offer_curve_by_group` carries
no entry for it, so there is nothing to lift.** Adding one would be *creating* a channel, not
lifting an existing band, and is outside owner ruling R1's scope. `ST_CHP` is therefore still
unreached, and S-3 still tests it as the unreached-fossil control.
