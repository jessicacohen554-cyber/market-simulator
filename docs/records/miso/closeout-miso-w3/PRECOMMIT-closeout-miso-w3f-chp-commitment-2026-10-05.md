# PRECOMMIT — closeout-MISO-w3f: steam-host CHP commitment (`chp_startup_covered`) on the w3e arm, with and without the w3c holdout

Written and pushed **before any solve**. Shards launch only after the desk's go on the 5-line summary. This is structure vs gates, not a slot request.

```
CONTROL : the w3e arm (keeper recipe + seam full span + miso_chp_btm_measured), reconciled bench (#7210)
ARM A   : control + chp_startup_covered=true                                   (7 legs)
ARM B   : control + chp_startup_covered=true + mustrun_chp_btm_holdout=true    (7 legs)
EVIDENCE: FINDING-closeout-miso-w3f-chp-commitment-phase0-2026-10-05.md
REGISTRY: chp_startup_covered registered literally on its commitment-markup family row in this commit (it was a gap-baseline field)
```

## Predictions (first-order static; reconciled basis)

**Arm A.**
- **C1 CC_CHP:** every year PASS (2019 ≈ −0.2, 2022 ≈ −0.8).
- **C1 CC_REGULAR:** PASS→FAIL in 2019, 2020 and 2022 (about −8.5 / −8.8 / −10.4, **declared**); 2021 fails deeper (about −14.8).
- **C1 ST_GAS:** 2019 about −10.6, 2020 about −9.1 (both FAIL).
- **C3a:** every year moves down by about 0.3–0.6 pt; 2020 stays in band.
- **Net:** fails go from 5 to about 6 records. **A is a trade; it is not expected to beat the w3e arm.**

**Arm B.**
- **C1 CC_CHP:** every year PASS, at about +0.2 to +5.9.
- **C1 CC_REGULAR:** 2021 about −9.6 FAIL; the other years about −4.9 to +2.6, in band.
- **C1 ST_GAS:** 2019 about −9.9 FAIL; 2020 about −8.0, on the line.
- **C1 COAL_PRB:** in band in every year (2019 about −0.7).
- **C3a 2020:** about +10.5 % (holdout +3.0 pt, w3e −2.3, commitment about −0.5). **Declared borderline FAIL.**
- **Net:** 3–4 failing records against the w3e arm's 5.

**Also declared:** ST_GAS forced share (C8) rises further in both arms. The gated years were ≤ 0.287 on the w3e arm.

## Reading rule

Report every moving record:
- control → A → B, at full magnitude;
- the prediction error for each row above;
- the CEMS-vs-model commitment census on each arm, in online share and starts;
- C8 / D-2 and unserved energy.

A prediction missed by more than 2× is a model-of-the-model failure, not a gate. **Stop conditions:** a shard fails, or a leg's `run_config` lacks the flags.

## Addendum: desk bars for arm B (2026-10-05 05:22Z, fixed before any solve)

On the reconciled basis, arm B is scored against these bars:

1. **Failing records:** at most 4.
2. **C8 forced share:** still PASSES.
3. **D-4 window:** clean for any new CHP commitment.
4. **C3a 2020:** no worse than +10.5 %.

**Kill:** any CHP class whose forced share exceeds 30 %.

Arm A has no bars. It supplies the attribution for B (rule 19): the commitment lever's effect on its own, before the holdout is stacked on it.
