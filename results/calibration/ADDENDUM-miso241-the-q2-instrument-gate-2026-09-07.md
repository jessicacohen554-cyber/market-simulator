# ADDENDUM miso-241 — two gate legs and two reported columns, declared BEFORE they are computed

Extends `PREREG-miso241-the-spp-quantity-side-charter-2026-09-07.md` (pushed `6fbc5e83`), on the
miso-233 / miso-235 / miso-236 / miso-237 / miso-240 addendum pattern.

**Pushed before the probe is run and before any number in it exists.** No pre-registered decision
rule is touched and **no pre-registered verdict can move**: the PREREG's Q-0, Q-1, Q-2 and Q-3
rules, bars and candidate enumeration stand exactly as written. Nothing here arms a mechanism,
charters a lever, moves a matrix cell, mints a field or touches the keeper
(`2026-09-07-miso-233-spp-hourly`, CALIBRATED, C3c the single ledgered caveat, DOF 41/2). Zero LP,
as the PREREG declared.

---

## A — `G-P6`, an EIGHTH provenance leg on THIS session's own Q-2 instrument (GATING)

**Why it is owed.** PREREG §4 measures the candidate partition with *the envelope's own p90
estimator*. That claim is only true if this session's Q-2 grid is the envelope's grid — same source
rows, same `hour_ending_key` shift, same DIBA→seam map, same sign convention, same
`np.percentile(·, 90)`, same `clip(·, 0, None)`. If it is not, Q-2 measures a lookalike and its
verdict is worthless. So the claim is made **falsifiable** rather than asserted.

**The leg.** With the neighbour join switched OFF (all rows retained), this session's per-
`(month × hod)` unconditional p90, mapped onto the model's fixed non-leap clock and clipped at 0,
must reproduce `measured_seam_import_envelope("MISO", year, 8760, None, direction=…,
hour_ending_key=True)` for **all four seams × three years × both directions**.

* **Bar: ≤ 1e-6 MW** (an exactness bar, not a tolerance — the two computations should be the same
  arithmetic on the same rows). Buckets this session's grid leaves empty are excluded from the
  comparison and their count is reported; the committed function fills them from the month max, a
  fill this session does not replicate and does not need.
* **If G-P6 FAILS the Q-2 instrument is declared BROKEN and Q-2 is NOT read** — Q-0, Q-1 and the
  charter's other legs are unaffected, because none of them touches this grid. The failure is
  published first, at full magnitude, and any repair is declared in a further ADDENDUM before the
  repaired numbers exist, with no bar moved.

## B — `G-P2` is recomputed FROM SCRATCH, not read (GATING, and this sharpens the PREREG)

PREREG §1's G-P2 says only that miso-236's gated `delta_r2_A_nohydro` is reproduced "in miso-236's
own metric". Fixed here, so the leg cannot be satisfied by reading the predecessor's file: the
value is **recomputed on this session's own code path** — this session's `ok` mask, its own
`ols_resid` of the measured seam flow on that seam's pre-registered regressor, MISO's own-state
block z-scored over the `ok` set, the neighbour block z-scored over the finite-neighbour subset,
plain (un-adjusted) `R²` — and only then compared to the committed JSON. The bar is unchanged at
**≤ 0.005**, and the leg now covers **all four seams** (Manitoba reports
`NO NEIGHBOUR-STATE INSTRUMENT`, miso-236's own answer-by-data-absence) rather than three.

## C — two REPORTED columns, declared here before they are computed

Neither is gated and neither can move a verdict.

1. **The SPP envelope's clip census.** The committed envelope clips each `(month × hod)` p90 at
   zero (`np.clip(tab, 0.0, None)`), so a bucket whose measured p90 net import is negative caps
   that direction at **exactly zero**. Reported per seam-year: the share of model hours at
   `env^eff ≤ 0` in each direction, and the envelope's mean and σ against the model's and the
   measured seam's σ. It is the scale context Q-1's verdict sits in.
2. **miso-235 §5's contribution-to-correlation table, on BOTH export variants.** PREREG §2.3
   already requires miso-235 §4's SPP row on both; this adds §5's per-seam contribution to
   `corr(imports, P_RT)` and its measured counterpart, plus the committed solve's own total, so a
   reader can see whether the Q-0 repair moves the lane's **cancellation** reading (PJM 4–9× too
   negative, South wrong-signed, Manitoba ~2× too positive, committed system ratio
   1.99 / 3.12 / 5.56×). **Declared UN-TARGETABLE before it is computed** (rules 1 `[R-STRUCT]` /
   13 `[R-MEASURED]`): it is a description of what the repair does to an instrument, never a target
   and never a licence to change anything.

## D — governance

Rule 1 `[R-STRUCT]`: nothing is judged by a residual and nothing is proposed; §C is declared
un-targetable before it is computed. Rule 13 `[R-MEASURED]`: measurement only; miso-236 PREREG
§2c's inadmissible-forms list binds here unchanged. Rule 14 `[R-ACCURATE]` / rule 23
`[R-FROZEN-DERIVE]`: no input, envelope, ladder, percentile or interface limit changes; §A
*reproduces* the committed envelope, it does not build one. Rule 15 `[R-DASHBOARD]`: no run
produced. Rule 19 `[R-ONE-MECH]`: no mechanism added. Rule 21 `[R-DOF]`: 41/2, unchanged. Rule 22
`[R-HOLDOUT]`: 2023–2025 only. Rule 24 `[R-REGISTRY]`: no field created. Rule 25 `[R-ISO-SCOPE]`:
MISO only. Rule 28(b): evidence-append form; no cell verdict moves. Rule 29 `[R-SCREEN]`: still
clause 0, zero LP.
