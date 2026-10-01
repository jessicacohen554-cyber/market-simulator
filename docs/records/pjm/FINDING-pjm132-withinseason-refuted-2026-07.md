# FINDING — pjm-132: the authorized within-season re-conditioning is INERT at the price level — Lane 2 ends, and PJM is NOT frontier for a reason that is not the ledger

**Lane:** `docs/handoffs/pjm-frontier-path-2026-07.md` §3c — the last named
admissible mechanism.
**Authority:** the owner AUTHORIZED the re-conditioning memo on 2026-07-27 with
an amendment (`docs/handoffs/pjm-midcurve-reconditioning-memo-2026-07.md`
decision banner). Charter, committed before the re-derive and before any solve:
`docs/handoffs/pjm-132-midcurve-reconditioning-charter-2026-07.md`.
**Registered:** `2026-07-27-pjm-132-control` and
`2026-07-27-pjm-132-withinseason`, both 2023+2024+2025 in one bundle (rule 16),
both **rejected probes**. `keepers.json` untouched.

---

## §0 — verdict

| item | status |
|---|---|
| **Memo decision** | **AUTHORIZED** with the "keep the current config as default" amendment. Executed exactly as §4 pre-registered. |
| **Stage 1 (K1 gradient)** | **PASS 3/3** on bids — but the honesty bound fired in all three years. |
| **Stage 2 (A/B solve)** | **REFUTED.** The price effect is inert; C3a-2025 moves **−0.011 $/MWh** against a −4.54 gap and dispersion NARROWS in 2023/2024. |
| **Lane 2** | **ENDS.** The measured-offer-surface family has now been tried as a dispersion lever under BOTH conditioning definitions. |
| **PJM frontier** | **NOT YET — and the blocker is the KEEPER, not the ledger.** See §5. |
| **Shipped** | pjm-130's bench fix **actually landed** — it had been reading its trigger from the wrong file (§4). |

## §1 — Stage 1: the gradient passes on bids, the magnitude does not

The mid-curve surface re-derived within-season on the full 36-month corpus
(same edges, shares, segmentation and gas normalisation — only the ranking scope
changed). MW-weighted bid delta on the keeper fleet, reported in the **keeper's
own within-year bins** so the hour partition is held fixed across arms:

| year | bin0 | bin1 | bin2 | bin3 | gradient | tight-bin rise |
|---|---|---|---|---|---|---|
| 2023 | −0.087 | +0.272 | +0.550 | **+0.910** | **+0.997** | $0.910 |
| 2024 | −0.067 | +0.401 | +0.090 | +0.370 | **+0.437** | $0.370 |
| 2025 | +0.027 | +0.006 | **−0.354** | +0.152 | **+0.125** | $0.152 |

K1 (gradient > 0 in ≥2 of 3 years) **PASSES 3/3**, so Stage 2 was authorized.
But the **pre-registered honesty bound fired in every year** and worst in the
only year whose price gate fails: 2025's tight-bin rise is **$0.152/MWh**
against the ~$1/MWh noise floor. Reported to the owner *before* the chain was
spent, per memo §4, along with the prediction that Stage 2 would measure
approximately nothing. Only 2023's ladder is monotone; 2024 and 2025 are not.

## §2 — Stage 2: the price effect is inert

Six solve-years, rule-12 per-year chain, one fresh process each. Control =
keeper recipe replayed at HEAD; arm B = the same + the seasonal vintage.

| year | control | arm B | Δ price | disp A | disp B | Δ disp |
|---|---|---|---|---|---|---|
| 2023 | 30.724 | 30.736 | +0.013 | 13.903 | 13.858 | **−0.045** |
| 2024 | 30.246 | 30.252 | +0.006 | 15.865 | 15.721 | **−0.144** |
| **2025** | 40.932 | 40.921 | **−0.011** | 22.134 | 22.238 | +0.104 |

**The control validates itself:** 2025 lands at **40.932**, reproducing
pjm-129's guard-corrected A1 value (**40.93**) rather than the keeper's
pre-guard 41.53 — so the A/B is measured against the true current baseline, not
a stale one. That is why the control was run rather than comparing arm B to the
keeper's committed metrics.

**Against memo §4's PASS signature:** the 2025 C3a gain must be carried by the
tight strata (there is no gain — it moves fractionally the wrong way) AND
dispersion must widen toward actual (it *narrows* in two of three years). Both
fail. This is the **pre-registered refutation**, exactly as §1's $0.152/MWh
predicted.

**Consequence.** The measured-offer-surface family has now been tried as a
dispersion lever under **both** conditioning definitions and fails on prices
both times. **Lane 2 ends on record.**

## §3 — the artifact is real and ISO-wide, which is worth keeping separate

Measured from EIA-930 net load only (no LP, no surface), the seasonal
composition of each ISO's annual top-3 % net-load bin, 2023–2025:

| ISO | peak season | dominant share | hours/yr reallocated |
|---|---|---|---|
| MISO | summer | **100.0 %** | 175 |
| NYISO | summer | **100.0 %** | 175 |
| NEISO | summer | 95.7 % | 164 |
| PJM | summer | 95.2 % | 162 |
| CAISO | summer | 91.4 % | 152 |
| ERCOT | summer | 83.8 % | 132 |

**All six ISOs carry the artifact and PJM is mid-pack.** MISO and NYISO contain
**zero winter hours** in their annual tight bin in all three years — their
winter scarcity is structurally incapable of registering as tight. The
definitional case (memo §1) therefore stands on its own and is *not* PJM-
specific; what pjm-132 refutes is only its use as a PJM **backcast dispersion
lever**. Acting on it elsewhere is each ISO's own decision on its own evidence
and needs its own memo (rules 23 / 25). Nothing was touched outside PJM.

**Forecast side, untested here:** ~162 PJM hours/year of tight-state pricing
currently cannot fire outside summer. Whether removing that helps a forecast is
scored by a different program (the forecast dashboard / FF-2D) that this session
did not run, so the owner's "make it the default if it helps the forecast"
condition is **unverified and the flip did not fire**. The gate stays
default-off; runtime cost measured at **2.85 ms/solve-year** (0.0003 % of a
15-minute solve), so keeping it costs nothing.

## §4 — shipped: pjm-130's bench fix was inert and now actually lands

pjm-130 reported the negative committed metered volume
(`bench/PJM/2025.json.gz` `classFull.CT_CHP = −0.3726 TWh`) as **fixed**. It was
not. The benchmark mirror `_backfill_chp_eia923_from_donor` is gated on a
`btm_backfill_year` recovered from **`run_config.json`** — and **no bundle in
the tree records it there** (checked pjm-121 / pjm-129 / pjm-132). It lives in
**`meta.json`**, which is written from the solve kwargs and is exactly where the
BTM side reads it. So on an armed keeper the subtrahend was repaired and the
minuend was not: **the same one-sided repair pjm-130 diagnosed and believed it
had closed.** The fix was correct in substance and inert in practice because it
looked for its trigger in the wrong file.

`rebuild_benchmark` now checks `meta.json` first, `run_config.json` as fallback.
The mirror fires on the four CHP plants missing from the thin 2025 EIA-923
vintage but active in CAMPD (10805 CC_CHP; 50463 / 52149 / 54785 CT_CHP).

| PJM 2025 `classFull` | before | after |
|---|---|---|
| **CT_CHP** | **−0.3726** | **+1.3724** |
| CC_CHP | 6.2811 | 6.4446 |

2023 and 2024 are byte no-ops (complete vintages), so only
`bench/PJM/2025.json.gz` moves. The `btm ≤ e923` invariant now holds for all
three CHP classes; `test_btm_benchmark_symmetry.py` 6/6 pass.

**Recorded honestly:** pjm-130 predicted **+1.4653** from its reconstruction
probe; the live registration path yields **+1.3724**. The sign and the invariant
are what matter; the ~0.09 offset between the probe and the live path is *not*
chased here and is left as an open discrepancy rather than quoted away.

**Provenance of the find:** the owner questioned why a CHP plant's BTM would not
simply be measured from the backcast year's own EIA-923. It is — the backfill
only repairs plants missing *entirely* from a thin vintage, and that question is
what exposed the wrong-file lookup.

## §5 — PJM frontier: NOT YET, and the blocker is the keeper, not the ledger

The bar (`calibration-rubric.html` §frontier, quoted in the frontier handoff §1):

> Every named admissible mechanism for the ISO's residual caveat family has been
> tried **on record**, and what remains is either **inadmissible to close** or
> **blocked on data that does not exist publicly**.

…and the handoff's own gloss on how both current holders earned it: *"every hard
and volume criterion in band, the entire remaining residual is the C3c price
scarcity tail."*

**The mechanism-ledger half is now essentially complete.** Lane 1 closed
(pjm-124/125), Lane 2's commitment-status half terminal (pjm-128), the season
half settled (pjm-126/127) and now *tried and refuted* (this session), gate 1
closed (pjm-131: κ = 0.023, CC_CHP clears on price, the same stratum as gate 2),
gate 3 ledgered as out of reach. No named admissible mechanism remains untried.

**But the calibration half is NOT met, and that is new since the handoff was
written.** The handoff says "PJM clears the first half of that bar already
(10/10)". That is **no longer true on corrected data**:

| | committed keeper `pjm121_ccbelt` | same recipe, corrected envelope (`pjm129_meritguard_a1`) |
|---|---|---|
| determination | **CALIBRATED** 10/10 | **NOT-YET** |
| C1 fuel-mix | PASS, 16/16 (free 12/12) | **FAIL**, 15/16 (free 11/12) |
| C3a mean LMP | PASS | **FAIL** |
| C3c tail | PASS | **FAIL** |

The keeper scores CALIBRATED only on the **pre-guard inflated outage envelope**
— data the project has since corrected and kept (rules 1 / 14). Re-solved on the
corrected envelope it is NOT-YET, and this session's control arm independently
reproduces that baseline (40.932 ≈ A1's 40.93).

**So PJM fails the bar on two counts that frontier explicitly requires:** a
**volume** criterion is out of band (C1-2023 CC_REGULAR), and the residual is
**not confined to the C3c scarcity tail** — C3a, a price-*level* criterion,
fails too. Both current holders had every hard and volume criterion in band with
only the tail left. PJM does not.

**Recommendation: do NOT declare frontier.** Declaring it on the committed
keeper's 10/10 would be declaring on numbers produced with an outage envelope
the project itself has superseded and rejected. The honest state is: *PJM's
mechanism ledger is complete, and its keeper is CALIBRATED only on superseded
data.*

**The real open item is upstream of frontier and is an owner call nobody has
made** — the one pjm-129 flagged and miso-88's precedent reserves to the owner:
what to do about the keeper designation on the corrected envelope. Three routes,
none of them a session's to take:

1. **Leave it.** PJM stays CALIBRATED on the dashboard on superseded data, and
   frontier stays undeclared. Honest but stale.
2. **Re-audit the designation** onto the corrected envelope, accepting NOT-YET.
   Truthful, and it makes the frontier question well-posed — but it needs a
   re-tune to get back in band, and pjm-130/131/132 have now closed every named
   mechanism for all three failing gates.
3. **Governance route:** if the three misses are genuinely *accepted
   measured-input limitations* rather than model misses, attest them in the
   bundle's `calibration_attestation.json` exceptions ledger and they become
   CAVEATs, restoring CALIBRATED-WITH-CAVEATS. This is legitimate **only** if
   each is truly a measured-input limitation — C1-2023 CC_REGULAR is 0.10 TWh
   over an 8.00 TWh band (1.2 %), which is arguably one; C3a-2025 at −10.6 %
   against ±10 % is a harder case. **Not a session's call, and it must not be
   used as a convenience to reach a badge.**

## §6 — rule compliance

* **Rule 22 `[R-HOLDOUT]`:** 2023–2025 only; freeze untouched, not lifted.
* **Rule 15 `[R-DASHBOARD]`:** both arms registered in-session, win or lose;
  parity check clean; `audit_keepers.py --iso PJM` PASS, 0 failures.
* **Rule 16 `[R-ALLYEARS]`:** both bundles are 2023+2024+2025 in one bundle.
* **Rule 25 `[R-ISO-SCOPE]`:** PJM only; the §3 cross-ISO measurement is
  descriptive and authorizes nothing elsewhere.
* **Rules 1 / 20 / 23 / 24 / 26:** the re-derive changed the ranking scope and
  nothing else — no edge, share-grid, segmentation or free-parameter change. The
  gate is registry-visible and registered in `_CACHE_KEY_OPTIONAL_FIELDS`, so
  the pinned default cache key stays `edbc1b103207170a` and an armed run gets a
  distinct key.
* **Rule 27 `[R-PUSH]`:** every ≥300-line file edited in place and blob-verified
  byte-identical after push.
* **Keeper** `2026-07-25-pjm-121-cc-belt` untouched; `keepers.json` not edited;
  the default gate NOT flipped (its condition is unverified).

## Reproduction

```
uv sync
PYTHONPATH=. .venv/bin/python scripts/regenerate_clean.py \
    transfer-interface-limits ramp-capability lmp
PYTHONPATH=. .venv/bin/python scripts/data/fetch_pjm_energy_offers.py   # 36 months
PYTHONPATH=. .venv/bin/python scripts/data/derive_pjm_offer_midcurve.py \
    --years 2023 2024 2025 --conditioning within-season
PYTHONPATH=. .venv/bin/python scripts/probes/pjm132_withinseason_precheck.py \
    results/calibration/pjm121_ccbelt --years 2023 2024 2025 \
    --json-out results/calibration/pjm132_stage1_k1.json
PYTHONPATH=. .venv/bin/python scripts/probes/pjm132_conditioning_artifact_by_iso.py \
    --json-out results/calibration/pjm132_artifact_by_iso.json
```
