# ADDENDUM neiso-104 — CORRECTION: the replay environment did NOT match the keeper's, and "bit-identical" overstated what was measured

**2026-09-06, session neiso-104.** Corrects two claims in
`FINDING-neiso104-offer-level-screen-2026-09-06.md` §0/§4(b) and in the NEISO mechanism-matrix
stamp. **Zero LP spent on this correction.** No gate verdict moves; the screen's STOP stands.

---

## 1. What was claimed, and what is true

**Claimed (in-session, and carried into the FINDING's framing):** the solve environment was
restored to the pinned `requirements.txt` set and therefore matched the keeper's recorded
environment exactly, so any control-vs-keeper difference would be attributable to code drift
alone.

**True:** it did not match. Both replay logs printed the mismatch as their **first four lines**,
before either solve began, and the claim was made without reading them:

```
WARNING: replay environment differs from the bundle's recorded environment —
byte-identity is not guaranteed:
  platform: bundle 'Linux-6.18.5-fc-v20-x86_64-with-glibc2.39'
         != now 'Linux-6.18.44-fc-v24-x86_64-with-glibc2.39'
  highspy:  bundle '1.14.0'  != now '1.15.1'
  pandas:   bundle '3.0.3'   != now '3.0.5'
  pydantic: bundle '2.13.4'  != now '2.13.5'
```

**Root cause of the error, stated precisely because it will recur:** the version check used
`highspy.Highs().version()`, which returns the **bundled HiGHS solver** version string
(`1.14.0`) — *not* the **Python package** version (`1.15.1`, from
`importlib.metadata.version("highspy")` and `pip show`). The two differ, the solver string
happened to equal the keeper's recorded package version, and the coincidence read as a match.
**`Highs().version()` is not the package version and must not be used to verify an environment
pin.**

## 2. Effect on the screen — none

The arm and the control ran in the **same** environment, so the arm-vs-control differencing the
screen gates on is unaffected. **G1 STOP stands** (−2.38 % delivered vs −3.47 % pre-registered,
realized pass-through 0.525), as do G2 PASS and G3 PASS, and PREREG §7's stop-and-re-derive
trigger. Nothing about the arm's verdict changes.

## 3. Effect on the collateral reproduction result — it STRENGTHENS, and it is restated more weakly

The reproduction held **across four environment deltas as well as the code drift** — a HiGHS
minor-version bump, pandas and pydantic patch bumps, and a kernel change. That is a *more*
robust statement about the keeper's stability than the one originally written, not a weaker one.

**But the wording is corrected in the other direction.** The FINDING and the matrix stamp say the
control reproduced the keeper **"BIT-IDENTICALLY"**. That overstates the measurement. What was
actually measured, and all that was measured:

| quantity | control at HEAD | committed keeper | agreement |
|---|---|---|---|
| load-weighted mean LMP, 2025, P1 | $71.3866 | $71.3866 | to 4 dp (< $0.00005/MWh) |
| summed absolute class-energy delta | — | — | 0.0000 TWh at 4 dp; no class differed by > 0.001 TWh |

That is **consistent with** bit-identity and does not **establish** it: no per-cell comparison of
the hourly sidecars was run. **The correct claim is "reproduced to 4 dp on load-weighted price and
to 0.001 TWh on every class", not "bit-identical".**

**This cannot now be tightened without a re-solve**, because both screen bundles were deleted
before merge under rule 29(c). That is a genuine cost of this session's own sequencing — the
stronger verification was available while the bundles existed and was not run — and it is
recorded rather than quietly left as the looser claim standing in stronger words.

## 4. What does NOT change

- The G-DRIFT conclusion of §4(b): the 111 live-candidate files are empirically inert for NEISO's
  backcast, G-CTRL form 4 would have been valid, and the control was unnecessary in hindsight
  though correct to spend ex ante. Reproduction across a *larger* perturbation than assumed
  supports this more strongly.
- **NEISO's keeper is not stale**, and its determination is untouched: train-tier **CALIBRATED**.
- 2020 at +11.00 % on the measured move; rule 30(c) untouched.
- No keeper change, no registration, no holdout year touched, no `ScenarioConfig` default moved.

## 5. Standing note for any lane using `replay_keeper.py`

The driver **already prints an environment-mismatch warning before solving** and states
"byte-identity is not guaranteed". It did its job here; the reader did not. A lane that intends to
compare a replay against a bundle's committed numbers should read those four lines and record them
in its finding, and should verify package pins with `importlib.metadata.version`, never with a
library's own internal version accessor.
