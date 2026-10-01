# ADDENDUM to PREREG-nyiso210 — the sidecar's band vocabulary is finer than the PREREG's, and the partition is repaired in CONSTRUCTION with no threshold moved

**Session:** nyiso-210. **Date:** 2026-09-06. **Written BEFORE any P1/P2/P3 verdict value was
read**, and committed and pushed before the repaired probe was run.

## What was found

PREREG §4 names the four **registered `offer_curve_by_group` bands** —
`committed` / `econ_low` / `econ_high` / `peak` — because those are the bands the offer-curve
registry carries. The committed `class_band_hourly_<year>.parquet` sidecar does **not** use that
vocabulary. Its CC_REGULAR band set, identical in every one of the four years, is:

```
committed, econc00, econc01, econc02, econc03, econc04, econc05, peak
```

i.e. the economic region is emitted as **six continuous sub-tranches** spanning the
`econ_low`→`econ_high` span, not as two named bands. The probe's first run therefore summed the
economic region as **zero** (it looked for band names that do not exist in the artifact), so no
P1/P2/P3 value it produced is meaningful and none was read as a verdict.

## The repair — construction only

The partition becomes the **three-way** one the PREREG's §2 mechanism argument actually rests on,
with the economic region reassembled from the tranches the artifact does carry:

| PREREG band | repaired definition |
|---|---|
| `committed` | `committed` — unchanged |
| **economic** | `econc00 + econc01 + econc02 + econc03 + econc04 + econc05` |
| `peak` | `peak` — unchanged |

**No threshold moves, and none may.** P2 still fires on `committed` exceeding its in-sample mean
by **> +0.5 TWh**; P1 still fires on the **economic share** exceeding its in-sample mean share by
**>= 3.0 pp** (the PREREG's `econ_low + econ_high` share *is* this share — the two names sum to
the same region); P3 still fires on a **CV < 0.35** of the bands' percentage changes, now computed
over the three-way partition rather than a four-way one. P4 and P5 are untouched (neither reads a
band). The evaluation order P2 → P1 → P3 is unchanged.

## Why this cannot be a result-selected repair

1. It was found by the economic region reading **exactly 0.0000 TWh in all four years** — an
   arithmetic impossibility for a dispatched class, not a marginal judgement.
2. The repair is forced: the six `econc*` tranches are the *only* CC_REGULAR bands besides
   `committed` and `peak`, so there is exactly one way to reassemble the economic region. No
   alternative partition exists to choose between.
3. **No P1/P2/P3 input value had been read when this was written.** What the defective run did
   emit and this session had seen is the `class_month_gap` table (a monthly model-minus-measured
   series built from the plant payloads, which never touch the band axis). The month axis enters
   **none** of P2, P1 or P3 — those read the `committed` absolute delta, the economic share, and
   the CV of band percentage changes respectively — so no gate can have been tuned to it. The
   monthly winter/summer split remains what the PREREG declared it to be: a **corroborator,
   reported and never part of a firing test**.

*(nyiso-210, addendum, 2026-09-06.)*
