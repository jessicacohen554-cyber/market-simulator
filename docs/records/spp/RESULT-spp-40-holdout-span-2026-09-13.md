# RESULT — SPP-40: keeper 11 on held-out years 2019–2022

**Lane** SPP-40 · **Date** 2026-09-13 · **Run** `2026-09-13-spp-40-holdout-span`
· **Keeper** `2026-09-13-spp-38-vintage-cache` (keeper 11) · **Bundle**
`results/calibration/spp40_holdout` · DATA PROFILE `spp`

SPP's **first out-of-training price coverage**. Keeper 11's recipe, replayed with
**no `--set` at all**, on 2019–2022 — one `--years 2019 2020 2021 2022`
invocation, one shard, one bundle (rules 12 / 16 `[R-ALLYEARS]` / 32(b)
`[R-SHARD]`). Ordered by the owner in the same instruction that declared SPP
`complete` ("Complete then run").

**SPP's headline determination is unchanged: `CALIBRATED`** on the 2023–2025
train-tier verdict. Rule 30 `[R-TOUCHPOINT-FOLD]` (c) — a held-out year reports
but can neither certify nor decertify. The run is stamped to keeper 11 and folds
into its Run Explorer report; the per-year ladder is on the Calibration Status
page (rule 30 (a)/(b)).

## 1. Retrievability (rule 34 `[R-SHARD-PROMOTABLE]` (e))

The bundle is **on the parent's disk and in this commit** (slim set + `hourly/`
sidecars + `legitimacy_diagnostics.json`, 3.6 MB). The **full** bundle — 42 files
including `dispatch/<year>_P1{,_fleet}.parquet` and `floors/<year>_P1.npz`, which
registration and the per-plant D-1/D-2/D-4 diagnostics need — was pushed by the
shard per rule 34 `[R-SHARD-PROMOTABLE]` (a) and is recoverable by **immutable
SHA** (rule 33 `[R-SHARD-ARCHIVE]` (d)):

```
git checkout 2fa060dafd0c2d23265949599816974d65f062d3 -- results/calibration/spp40_holdout
git reset HEAD -- results/calibration/spp40_holdout   # the checkout STAGES gitignored paths
```

(branch `claude/spp-40-holdout-v2`; the first shard, `claude/spp-40-holdout`
@ `6d39c179`, stopped before spending any LP on the SWPP vintage gap and carries
no bundle.) **A promotion needs no re-solve.** Per rule 33 (f)(3) that branch
**stays** until the owner has ruled — and branch deletion returns HTTP 403 for
this session's credential in any case (rule 33 (f)(5)).

## 2. The ladder

| year | tier | gas $/MMBtu | determination | failing criteria |
|---|---|---|---|---|
| 2019 | validation | 2.57 | NOT-YET | forced_share |
| 2020 | validation | 2.03 | NOT-YET | price_shape, forced_share |
| 2021 | validation | 3.72 | NOT-YET | fuelmix, price_mean, price_shape, dispatch_corr, forced_share |
| 2022 | validation | 6.45 | NOT-YET | fuelmix, price_mean, price_shape, dispatch_corr, forced_share |
| 2023 | training | 2.54 | CALIBRATED | — (ledgered C3c) |
| 2024 | training | 2.19 | CALIBRATED | — (ledgered C3c) |
| 2025 | training | 3.52 | CALIBRATED-WITH-CAVEATS | — (unscored fuelmix, sysvol; ledgered C3c) |

C6 governance **PASSES** on all four held-out years. C2 `sysvol` passes on all
four. C3c carries as a ledgered caveat on all four, exactly as in-sample.

## 3. The finding: ONE defect, four symptoms, keyed to delivered gas price

The offer bands were set on 2023–2025, where delivered gas ran **$2.19–$3.52**.
Sorted by gas price rather than by year, the model's coal-versus-gas split is
monotone — and it **saturates**:

| gas $/MMBtu | year | model CC% of (CC+PRB) | actual CC% | error (pp) |
|---|---|---|---|---|
| 2.03 | 2020 | 0.438 | 0.402 | **+3.6** |
| 2.19 | 2024 | 0.420 | 0.434 | −1.4 |
| 2.54 | 2023 | 0.400 | 0.412 | −1.2 |
| 2.57 | 2019 | 0.387 | 0.363 | **+2.4** |
| 3.52 | 2025 | 0.318 | 0.364 | **−4.6** |
| 3.72 | 2021 | 0.138 | 0.301 | **−16.3** |
| 6.45 | 2022 | 0.135 | 0.315 | **−18.0** |

Below ~$2.6 the error is small and sign-mixed. Above ~$3.5 the model flips
essentially the whole CC fleet behind PRB coal: CC_REGULAR falls to 15.8 TWh in
both 2021 and 2022 against 34.6 / 35.8 TWh actual, while COAL_PRB rises to
98.8 / 101.3 TWh against 80.2 / 78.0 actual. **The plateau is the signature**:
gas rises 74 % from 2021 to 2022 and the model's split barely moves (0.138 →
0.135), because there is nothing left to displace. The real market's split
barely moves either (0.301 → 0.315) — but at more than **twice** the model's CC
share. The model's coal↔gas crossover is far too sharp.

Four of the five degraded criteria are that one defect:

- **C1 fuelmix** — the substitution itself: CC_REGULAR −18.9 / −20.1 TWh,
  COAL_PRB +18.6 / +23.3 TWh in 2021 / 2022. Near 1:1.
- **C3a price_mean** — −21.3 % / −23.5 %. Coal sets the margin in hours gas
  should, so the clearing price is too low.
- **C3b price_shape / C4 dispatch_corr** — NRMSE 0.640 / 0.342; gas-fleet NRMSE
  0.52 / 0.57. Correlation stays high (r ≈ 0.90) — the model gets the *timing*
  right and the *level* wrong, which is what a merit-order error looks like.
- **C8 forced_share** — ST_GAS forced share 50.4 % / 55.6 % against a 30 % cap.
  Two contributions, and both are measured: the floor is genuinely larger in
  these years (4.78–5.49 TWh vs 2.18–2.50 in 2023–2025 — more gas steam in the
  SPP fleet before the period's retirements), **and** the denominator collapses
  (14.7 / 15.9 → 10.8 / 9.9 TWh) as the crossover pushes economic ST_GAS out.
  Rule 19 `[R-FORCED-BUDGET]`'s conditional-pass escalation does not rescue
  2021/2022: D-1 off-peak `cv_ratio` reads 0.429 / 0.391 against a 0.50 gate
  (model CV 0.112 / 0.106 vs actual 0.262 / 0.271) — the class runs **flat**
  because all that is left of it is the floor. In 2019/2020 D-1 **passes**
  (0.765 / 0.809) and the breach is marginal (34.2 % / 30.1 %), i.e. driven by
  the larger floor alone.

**The defect is visible in the training window too.** 2025, at $3.52, is already
−4.6 pp — inside the tuned span and breaking the same way, just not far enough
to fail a gate. This is not a holdout artifact.

## 4. What this run does NOT establish

Stated at the gate, not absorbed.

1. **The crossover's location is bracketed, not located** — between $2.57
   (passes) and $3.72 (fails). 2025 at $3.52 would decide it, but **its fuelmix
   and sysvol are unscored** (2025 CAMPD/EIA-923 not yet complete). Closing that
   bracket is the cheapest next measurement and costs no LP.
2. **No counterfactual gas price was solved.** The association between gas price
   and the miss is measured across seven years; the *causal* claim that the
   delivered-gas operand is the lever is a hypothesis. An A/B that re-solves 2022
   at a 2023-like gas price would test it directly and is a rule-29 `[R-SCREEN]`
   phase-0-then-one-year job.
3. **The mechanism is not identified.** Candidates, none tested here: a missing
   coal supply / stockpile / take-or-pay **maximum** (the model has the
   take-or-pay minimum, not a cap); PRB steam ramp and sustained-output limits;
   or the `coal_prb_passthrough_sigmoid` being extrapolated far outside the
   $2.19–$3.52 range its anchors were identified in (a rule 23
   `[R-FROZEN-DERIVE]` object — its **anchors** are frozen, but whether its
   **functional form** extrapolates is an open structural question). These go on
   SPP's lever queue as `U`; no cell verdict is claimed from this run.
4. **These are not certified out-of-sample numbers.** `[R-HOLDOUT]` was removed
   2026-09-09, so no year in this program is protected from being iterated
   against (rule 22 coda). What they are is model-SELECTION evidence **this lane
   did not tune on**: keeper 11's recipe was fixed on 2023–2025 and applied here
   unrevised, no `--set`, no re-cut parameter, `offer_curve_by_group`
   byte-identical (SHA-256 `090abd79…62f65`).
5. **2021 is Winter Storm Uri**, whose tail is 121 % of that year's full-year
   price gap — so 2021's C3a/C3c are partly a scarcity-event measurement. Uri is
   **not** what drives its fuelmix miss: 2022 shows the same substitution at the
   same magnitude with no Uri.

## 5. Two defects found in shared infrastructure — REPORTED, not patched

Neither is this lane's object (rule 25 `[R-ISO-SCOPE]`); both are recorded so the
owning lane can decide.

- **`scripts/stamp_touchpoint_holdout.py` hardcodes NEISO-specific,
  `[R-HOLDOUT]`-era caveat text** (lines ~53–60) onto *every* ISO's touchpoint:
  a CAMPD availability-envelope parity story that is not SPP's, and the claim
  that "the touch-once locked test (2019 / H1-2026) is NOT spent here" — when
  2019 is one of this bundle's four years and the touch-once regime no longer
  exists. Both fields now have **zero consumers** (the Run Explorer panels that
  rendered them were deleted by the rule 30 (a) amendment of 2026-09-06), so this
  is inert-but-false committed prose. SPP's own sidecar carries corrected text;
  **a re-stamp resets it**, so re-apply after any re-registration.
- **`scripts/gen_touchpoint_attestation.py` refuses a bundle whose years "span
  more than one tier"** — here `['locked_test', 'validation']`, because
  `holdout_policy.tier_for_year` classifies 2019 `locked_test`. That guard is
  **stale**: rule 22's coda records `tier_for_year` as a pure year classifier
  carrying no authorization meaning. Splitting the bundle to satisfy it would
  violate rules 16 and 32(b). This lane used the established per-lane generator
  pattern instead (`scripts/gen_spp40_attestation.py`).

## 6. One correction to this lane's own record

An earlier draft of the C6 repair **widened** `authorized_price_tuning.years_held`
to `[2019…2025]` on the reading that rule 1 (b) wants the config's full reach.
That was wrong about the check: `calibration_verdict._authorized_tuning_finding`
tests **exact set equality against the run's own scored years**, and
`score_governance`'s docstring says so explicitly. `years_held` is now
`[2019, 2020, 2021, 2022]`, read off the bundle's `dispatch/<year>_P1.parquet` so
it cannot drift from what was actually solved; the stronger fact — that 0.93 was
fixed ex ante on 2023–2025 and applied here unrevised — is recorded in
`years_held_basis`, where it belongs. The widened value never reached a committed
doc. C6 now **PASSES**.

## 7. Next

SPP's queue, in cost order:

1. **Score 2025 fuelmix/sysvol when the source data lands** — zero LP, and it
   closes the $2.57–$3.72 bracket to $2.57–$3.52 or better.
2. **Gas-price counterfactual A/B on 2022** — rule 29 `[R-SCREEN]`: phase 0
   (offer-array delta at both gas prices, ~90 s) before any solve; if it clears,
   one screen year.
3. **Coal supply-side maximum** as the named structural successor, if (2)
   confirms the operand. Enters SPP's matrix column as `U` until tested.
