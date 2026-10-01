# FINDING nyiso-139b — the chartered joint Zone-K lever must be RE-SCOPED before it is written: the floor limb the decision card pairs with the transfer bound is **already disabled on the keeper**, and the limb that actually forces is a 24-hour base, not a peak-window one

**Session nyiso-139, 2026-08-16, after the D3(b) clock repair landed.** D1 was
GRANTED ("write, prereg, solve"). This is the identification that must precede
the writing — and it changes the arm's shape. **No solve spent, no mechanism
written, no `ScenarioConfig` field added.** Measured entirely from committed
artifacts of the designated keeper `2026-08-08-nyiso-133-cod-arm`.

---

## 1. WHAT THE CHARTER ASSUMED

`docs/DECISION-CARD-nyiso137-zone-k-charter-2026-08-16.md` asks to reconcile, as
ONE mechanism under rule 19 `[R-ONE-MECH]`:

> the mainland→Zone-K transfer bound **and** the downstate ST_GAS `min_gen`
> reliability floor

on nyiso-130's evidence that arming the published 940 MW transfer limit alone
fired kill gate **K6**, "the downstate ST_GAS reliability floor taking up the
slack at +0.22 / +0.42 / +0.23 TWh".

The natural arm that reading implies — *arm the 940 MW **and** stand down the
Long Island ST_GAS peak-window floor limb that duplicates it* — is the one a
session would write. **It would be a nullity on the floor side.**

## 2. THE PEAK-WINDOW LIMBS ARE ALREADY OFF ON THE KEEPER

`results/calibration/nyiso133_cod_arm/run_config.json`:

```
reliability_floor_overrides = {
  "NYC:ST_GAS:tmax:NYC_ST_ev":          {"enabled": false},
  "NYC:CT_PEAKER:tmax:NYC_CT_ev":       {"enabled": false},
  "Long_Island:CT_PEAKER:tmax:LI_CT_ev":{"enabled": false},
  "Long_Island:ST_GAS:tmax:LI_ST_ev":   {"enabled": false},
  "Capital_Hudson:ST_GAS:tmax:CH_ST_ev":{"enabled": false},
}
nyiso_gas_commitment_bridge = true
nyiso_gas_bridge_min_run   = true
nyiso_li_lcr_tsl           = true
nyiso_li_tsl_n11_security  = false
```

This is `iso_configs.NYISO_PEAK_WINDOW_FLOORS_OFF` applied in full. It is not an
accident: the `nyiso_gas_commitment_bridge` is the **replacement** for the
h14-21 peak-window limbs (owner directive 2026-07-27) and is armed *with* the
overrides, never stacked on them.

**So `Long_Island:ST_GAS:tmax:LI_ST_ev` — the HB14-21 evening ramp family, the
only ST_GAS limb whose window coincides with the transfer bound's own HB14-21
application window — is ALREADY disabled.** An arm that disables it changes
nothing. Rule 19's own instruction ("enumerate what already floors the same
class before adding or reconciling") is what catches this.

## 3. WHAT IS ACTUALLY FORCING: a 24-hour base, not a peak-window limb

`data/raw/reference/reliability_floor_coeffs_NYISO.csv`, Long_Island × ST_GAS —
three limbs, of which exactly **one** is live on the keeper:

| limb | threshold | floor_pct | hours | ramp_group | live on keeper? |
|---|---:|---:|---|---|---|
| persistent 24 h base | **−50.0 °C** | **0.262** | **all** | *(none)* | **YES** |
| evening ramp base knot | 25.0 °C | 0.35 | 14-21 | `LI_ST_ev` | no (overridden off) |
| evening ramp cap knot | 37.55 °C | 0.882 | 14-21 | `LI_ST_ev` | no (overridden off) |

The −50 °C threshold is never not met, so the live limb binds in **all 8,760
hours** at 26.2 % of available capacity. Its stated basis is *"persistent 24h
base: base_24h (when-available cool-day CF p25)"*, re-derived 2026-07-26 on the
guard-corrected outage extract under rule 23's source-data trigger.

The keeper's own D-4 row confirms the window independently:

| year | floor | window | floored TWh | off-window share |
|---|---|---|---:|---:|
| 2023 | `reliability_floor × ST_GAS` | **h0-23** | 2.7891 | 0.0 |
| 2024 | `reliability_floor × ST_GAS` | **h0-23** | 2.8025 | 0.0 |
| 2025 | `reliability_floor × ST_GAS` | **h0-23** | 2.3869 | 0.0 |

(D-2 shares of class: 20.5 / 22.1 / 15.6 %; the separate
`nyiso_gas_commitment_bridge × ST_GAS` adds 1.4 / 2.3 / 2.3 %. C8's 30 % cap is
not approached, and C8 PASSes.)

## 4. WHY THIS IS NOT THE SAME PHENOMENON AS THE TRANSFER BOUND

Under rule 19 the two live representations differ on every axis that matters:

| | Zone-K transfer bound | live LI ST_GAS floor |
|---|---|---|
| window | HB14-21 (design-cooling) | **all 24 h** |
| object | interface transfer capability | unit-level availability minimum |
| driver | NYISO's published N-1-1 Transmission Security Limit | measured CAMPD when-available cool-day p25 CF |
| what it represents | Zone-K import capability under contingency | cable-islanded in-city must-run baseline |

**They are not one phenomenon carried twice.** The pair that *would* have been —
an HB14-21 transfer bound and an HB14-21 evening floor limb — was already
separated, in the other direction, by the 2026-07-27 directive.

## 5. THEN WHY DID K6 FIRE AT nyiso-130?

Because **K6 as written is not robust to an import-relief lever.** Its text is
*"any D-2 mechanism's forced share **rises**"*, and "forced" means energy
dispatched **at a binding floor**. Relieving a transmission bound displaces the
in-zone fleet out of merit; a unit that was in-merit above its floor becomes
out-of-merit held **at** it. The floor then binds in more hours and its forced
TWh rises **even when the class generates the same or less**.

That is a mechanical consequence of the forced-share *definition* under any
import relief, and it is not, on its own, evidence that a security phenomenon is
represented twice. nyiso-130's K6 firing is therefore **ambiguous between**:

* (a) a genuine double representation — the reading the charter took; and
* (b) an artifact of scoring "forced" against a floor whose binding frequency
  necessarily increases when the zone is relieved.

§2-§4 make (b) the better-supported reading for the limbs that are *actually*
live, because the only limb that could have carried (a) is already off.

**This is not a licence to disarm K6.** Rule 19 and rule 17
`[R-FLOOR-WINDOW]` still demand that a floor binding across all 8,760 hours
justify its window — and an always-on 26.2 % floor on a downstate steam fleet is
a strong claim that deserves its own scrutiny. What it does mean is that
**K6 cannot adjudicate this lever as currently written**, and re-running the bare
swap to watch K6 fire again would learn nothing new.

## 6. DISPOSITION — what the next session must settle BEFORE writing an arm

The charter (D1) stands; its **floor-side object was mis-identified**, and the
arm must be re-scoped. Three questions, in order:

1. **Is the always-on LI ST_GAS 26.2 % base itself the right representation?**
   It is measured and rule-23-frozen, so it may not be re-derived against a
   residual. But rule 17 requires a *window* and a *driver*: an all-hours floor
   whose stated basis is a **cool-day** p25 CF is a candidate for re-scoping to
   the hours its own driver evidence supports — a rule-23 **source-data**
   question, not a tuning one.
2. **What replaces K6 for an import-relief lever?** A gate that fires on forced
   *share* is structurally biased against any lever that relieves a constraint.
   A defensible successor measures forced **TWh at constant class energy**, or
   compares forced share against the counterfactual merit order rather than
   against the control's. **This is a gate-design question and needs the owner.**
3. **Only then** is the joint arm writable, and it is very likely NOT
   "940 MW + disable a floor limb" but "940 MW + a re-scoped 24-hour base", with
   its own identification.

**Recommended: do not write the arm until (1) and (2) are answered.** Writing the
card's literal arm today produces a floor-side no-op plus a K6 firing that
§5 shows is uninformative — a spent solve that adjudicates nothing.

## 7. WHAT IS UNCHANGED

The D3(b) clock repair landed and is merged (main `f8c93afe7`); the keeper's
determination is **`CALIBRATED-WITH-CAVEATS`**, C3c the lone ledgered caveat,
scored against the corrected actual tail **10 / 13 / 42**. NYISO holds
`complete` (validation only), is ABSENT from `final`, its frontier is CLEARED
(2026-08-06, stays cleared), and the holdout spend freeze is ACTIVE and
untouched. The cross-ISO queue for NYISO has been CLOSED since nyiso-122.
