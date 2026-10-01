# ADDENDUM 1 to PRECOMMIT-scn-ws5a-policy-neiso-2026-09-06 — the $50 RPS escape masks the whole policy axis on NEISO's ENTRY screen

**Lane** SCN-WS5A-POLICY-NEISO · **Date** 2026-09-06 · **Written after legs 1–2 (`VOL-MID`,
`VOL-HI`) and BEFORE any CES or cap leg has been solved anywhere**, so every expectation below
is a pre-registration and not a retrofit. Commits: `7500e656` (VOL-MID), `fd12502e` (VOL-HI).

**Nothing in the parent PRECOMMIT is withdrawn.** Its predictions P-8, P-9 and P-11 stand
exactly as written and are scored as written; this addendum records that, on the evidence legs
1–2 produced, **I now expect P-11 to MISS and P-8 to be RIGHT FOR THE WRONG REASON**, and says
so before the deciding legs run rather than after.

---

## 1. What legs 1–2 measured

`VOL-HI` and `VOL-MID` are **byte-identical in every reported scalar, fuel column and capacity
column in all five years**; the only difference between the arms anywhere is the voluntary dual
itself ($7.00 vs $4.50 in the three binding years, $-0.0 in both slack years). Because `E_DC` is
exactly zero on NEISO the two arms carry the identical volume, so the pair was a **pure WTP-ceiling
ladder with no volume confound** — and it produced no response of any kind.

## 2. The mechanism, read off the code and confirmed by the runs

NEISO's **state RPS row escapes at its own $50/MWh ACP in every year of every arm** —
`rps_dual = 50.0` in 5 of 5 years in `REF`, `VOL-MID` and `VOL-HI` alike (and SCN-WS2a measured
the same $50 on its own 2026 T0, in both arms of that pair). The **entry** screen folds attribute
prices as

```
attr = max(effective_eac_price_for_tech(config, tech, year),
           rps_credit_for_zone(rps_shadow_price, zi),
           _clean_credit_for_tech(...))          # new_entry.py:1132-1143
```

and **that RPS leg is applied to every candidate technology with no fuel gate at all.** So on
NEISO `attr = 50` for every tech in every zone whenever the competing attribute price is below
$50 — which is true of **every level this campaign carries**: the voluntary ceilings $4.50 and
$7.00, and the CES premiums $10, $20 and $30.

This is rule 19 `[R-ONE-MECH]`'s `max()` attribute doctrine working exactly as designed. It is
not a defect and nothing here proposes changing it.

## 3. Pre-registered consequences, before the legs that test them

- **`CES-P10` / `CES-P20` / `CES-P30` (leg group B): ZERO entry difference across the ladder**,
  because $10, $20 and $30 all sit under the $50 RPS escape and the entry fold is fuel-blind.
  Parent **P-8** predicted P20 and P30 within 1 % of each other with P10 separating, on
  `iso_budget_exhausted`. I now expect all **three** to be indistinguishable on commissioned
  capacity, and the binding cap to be **irrelevant** because the screen never gets a different
  number to screen. If that is what lands, P-8's *prediction* is a hit on P20-vs-P30 and a
  **MISS on "CES-P10 separates"**, and its *stated reason* (queue saturation) is wrong.
- **Any response those arms do show must come through the RETIREMENT and CCS-RETROFIT screens**,
  not entry: the retirement screen's RPS leg **is** fuel-gated to `_RPS_ELIGIBLE_FUELS =
  {wind, solar}` (`retirements.py:3509-3516`), so a premium paid to `gas_cc_ccs` (credited 0.95)
  or to nuclear is **not** masked there. That is precisely the shape SCN-WS2b measured on NEISO
  in July — *"adds ZERO economic entry (commissioned builds byte-identical across arms — the
  whole response is dispatch)"*, all of it `gas_cc_ccs`.
- **`CES-T80` (leg group C): parent P-11 is now expected to MISS.** Its ACP is **$50.00/MWh —
  exactly equal to NEISO's RPS escape** — so `max(50, 50) = 50` and the target row's dual, even
  in the escape regime where it equals the ACP exactly, adds **nothing** to what the entry screen
  already saw in REF. P-11 predicted `CES-T80` would exhaust the 4 GW/yr ISO queue budget from
  2027 and be the campaign's largest NEISO deployment response; on this seam I expect it to
  produce **no incremental entry at all**, and offshore wind not to enter. Gate **G4** (dual =
  ACP exactly where the target is unmet) is untouched by this and is still the discriminating
  test for that arm.
- **The `CAP-STATE-TIGHT` expectations are NOT affected.** That case does not act through the
  attribute-price fold at all — it removes a $26–34/t carbon adder from marginal cost and from
  `evolve_fleet`'s `carbon_price` argument (parent §4.3), neither of which is masked by anything.
  P-3, P-12 and P-13 stand unmodified.

## 4. Why this is worth a document rather than a sentence in the FINDING

If it holds, the campaign's whole NEISO policy axis — carbon (killed at phase 0 by the RGGI
floor), CES premium, CES target and voluntary — turns out to be **invisible to the deployment
screen for one shared reason**, and that reason is a $50 state ACP the campaign never set and
never varied. That is a statement about what this ISO can and cannot be used to measure, not
about any instrument's merit, and it is the kind of thing that must be on the record **before**
the confirming runs rather than assembled from them afterwards. Whether the RPS escape at $50
in every forecast year is itself the right posture for NEISO is **not** this lane's question and
is not asserted either way here; it is routed to SCN-DESK in the lane FINDING.

## 5. Duties

No default moved, no knob moved, no `ScenarioConfig` field added, no gate rewritten, no
prediction withdrawn. DOF ledger: still **zero**. Everything under `src/`, `scripts/` and
`configs/` remains read-only to this lane.
