# RESULT caiso-280 — the import envelope binds **above** the actuals: the 2022 miss is not reachable through import quantity

**Lane:** CAISO calibration · **Date:** 2026-09-13 · **LP spent: ZERO** · **Keeper unchanged**
(`2026-09-12-caiso-275-gascoupling`) · **Nothing promoted, no cell verdict moved.**
**Charter:** `docs/PRECOMMIT-caiso280-does-the-import-envelope-understate-2026-09-13.md`
(committed and pushed **before** any number was computed).
**Predecessor:** `docs/RESULT-caiso279-the-binding-object-is-the-import-envelope-2026-09-12.md`.

---

## §1 — THE ANSWER

> **Did CAISO's measured actual imports on 2022-12-23..31 exceed the model's cap?**
>
> **No — and not marginally. The model imports 1,773.3 MW MORE than CAISO actually did.**

The hypothesis was that the envelope *understates* deliverable import and so starves the model of
cheap energy on the hours carrying the miss. **The measurement inverts it.** Over the 216 window
hours:

| | mean MW | 9-day energy |
|---|--:|--:|
| **model import** (both corridors, the LP's own flow) | **7,337.9** | **1,585.0 GWh** |
| actual CAISO **gross** import (Σ importing legs) | 6,098.4 | 1,317.2 GWh |
| actual CAISO **net** import | 5,564.6 | 1,202.0 GWh |
| **model − actual net** | **+1,773.3 (+31.9 %)** | **+383.0 GWh** |
| **model − actual gross** | **+1,239.5** | **+267.7 GWh** |

- The model imports **more than actual net in 182 of 216 hours (84.3 %)** and **more than actual
  gross in 164 of 216 (75.9 %)**.
- On the **binding** hours — 201/216 = **93.1 %**, where the envelope's dual sets λ — the model
  carries **7,528.7 MW** against an actual **5,814.5 MW**: **+1,714.1 MW**.
- Window hours where the model is genuinely short: **34/216 (15.7 %)**, mean shortfall 566.5 MW,
  **19.26 GWh** total — against **402.29 GWh** of over-import. **A 21:1 ratio.**

**The model is clearing 358–432 $/MWh against a 99–119 $/MWh benchmark while importing a third
more energy than the market did.** Import quantity is not the constraint. It is not a near miss
that a better envelope would close; the residual sits on the other side of the ledger.

---

## §2 — THE PRE-REGISTERED GATES, AS THEY READ

The charter fixed both gates before measuring, and §2.1 fixed the bar the construction sets for
itself. **Neither was moved afterwards.**

| gate | threshold | measured | verdict |
|---|---|--:|---|
| **T1(a)** window exceedance rate | ≥ 20 % of 216 h | **31.02 %** (67 h) | **PASS** |
| **T1(b)** vs Dec 1–22 control | ≥ 2× control (1.52 %) | **31.02 %** vs 0.76 % = **41×** | **PASS** |
| **T2** mean unserved import capability | ≥ 500 MW | **115.8 MW** | **FAIL** |

**Gates are conjunctive → VERDICT: NOT MATERIALLY UNDERSTATED → the lane closes on 2022 with no
LP spent.**

**T1 is real and worth recording, and it is also worth exactly what it is.** Dec 23–31 genuinely
is December's high-import stretch: **all 48** of December's PNW cap exceedances and **43 of 47**
DSW exceedances fall inside those 9 days, against a 0.76 % control rate. A pooled-December p95
*does* clip the cold-snap tail, roughly one hour in five. **But T2 sizes that clipping at 115.8 MW
on a 7,482.8 MW block — 1.5 % — while the same window runs +1,773.3 MW over actual.** The shape is
imperfect in a direction that is swamped, twenty-fold, by a level that is generous. Reporting T1's
pass without T2's magnitude beside it would be the misleading half of a true statement.

---

## §3 — THE OBJECT IS FULLY IDENTIFIED (exact cross-check, not inference)

`market_sim.data.eia930.envelopes.measured_corridor_flow_envelope`: per corridor, the **p95 of
that year's own measured net import, bucketed by (month × hour-of-day)**, clipped at 0.

- **12 × 24 = 288 buckets ⇒ caiso-279's 286 distinct limit values.** That arithmetic identified it.
- **Independent re-derivation from the raw EIA-930 extract reproduces the LP's `limit_up` to
  `max |Δ| = 0.000 MW` across all 8,760 hours, on both corridors.** The object is not inferred; it
  is reproduced exactly. That also validates the clock mapping (`_caiso_interchange_model_clock`,
  −1 h in standard time) hour-for-hour, since matching p95s require matching buckets.
- Corridor membership (`CAISO_CORRIDOR_DIBA`, split at Path-15): **WECC_PNW** = BPAT, PACW, BANC,
  TIDC · **WECC_DSW** = AZPS, SRP, WALC, NEVP, IID, LDWP, CEN. All 11 CISO DIBAs are mapped, so
  the two corridors **partition the seam** — corridor total ≡ CISO total interchange.
- **Reconciles with caiso-279 to the hundredth**: Dec 29/30/31 model PNW **1,157.58** = cap
  1,157.58, DSW **6,325.21** = cap 6,325.21, total **7,482.79**.

---

## §4 — THE PER-DAY TABLE, WHICH IS WHERE THE INVERSION IS PLAINEST

Hourly means, MW. `Δ` = model − actual (positive = the model imports more than the market did).

| day | actual tot | model tot | **Δ** | exceed h/24 |
|---|--:|--:|--:|--:|
| Dec 23 | 2,094.9 | 7,426.4 | **+5,331.5** | 0 |
| Dec 24 | 4,158.3 | 7,110.3 | **+2,951.9** | 1 |
| Dec 25 | 6,364.3 | 7,093.8 | **+729.5** | 6 |
| Dec 26 | 7,162.8 | 7,482.8 | **+320.0** | 12 |
| **Dec 27** | 8,190.3 | 7,482.8 | **−707.5** | **24** |
| Dec 28 | 5,569.2 | 6,996.6 | **+1,427.3** | 8 |
| Dec 29 | 5,438.1 | 7,482.8 | **+2,044.7** | 2 |
| Dec 30 | 4,378.3 | 7,482.8 | **+3,104.5** | 0 |
| Dec 31 | 6,725.3 | 7,482.8 | **+757.5** | 14 |

**Dec 30 — one of the two days caiso-279 measured as carrying 1.59 $/MWh of the annual gap on its
own — is the single most over-imported day in the window: +3,104.5 MW, with ZERO exceedance
hours.** The model had 3.1 GW more import than the market on the day it most overpriced. **Dec 27
is the only genuinely import-short day of the nine**, and it is the one day whose cap binds all 24
hours. One day in nine is not a mechanism.

---

## §5 — THE §4 TRAP HELD, AND IT DID NOT NEED TO

The charter's §4 warned that `caiso_firm_selfsched_floor`'s standing annotation (caiso-150) makes
this envelope an **outcome series used as a capability cap** — a real methodological defect in
kind, with the direction-splitting replacement adjudicated **unreachable from the public feed** at
caiso-150 §H. The trap was that a lane could reach for a cap multiplier "because the source object
is admittedly wrong".

**The annotation's concern is now quantified for this window, and it does not bind.** Its whole
content is that a NET envelope understates GROSS capability. The measured gross−net wedge over the
window is **533.7 MW** — and the model is **+1,239.5 MW above actual GROSS**. Crediting CAISO with
every megawatt of simultaneous counter-flow the record can support still leaves the model importing
more than the market. **The standing annotation is methodologically real and materially inert
here.** It was not necessary to invoke the trap, because the measurement removed the motive.

**No cap multiplier was considered, and none is admissible.** Widening the envelope would move the
model *further* from measured reality on quantity in order to chase a price residual — the exact
rule 1 `[R-STRUCT]` / rule 13 `[R-MEASURED]` forbidden move, now measured rather than argued.

---

## §6 — WHAT THIS MEANS FOR THE RESIDUAL (a consequence, not a new lever)

The LP sits **at** its cap in 93.1 % of window hours while already carrying a third more import
than the market. Read plainly: **at the prices the internal fleet offers, the model would import
even more than the market did.** That is a statement about **internal marginal-cost formation**,
not about the seam — and it corroborates, from an independent direction, what the DO-NOT-REDO
record already says: the flat ×0.92 fossil offer multiplier (caiso-267/268) is the one channel
measured to move C3a (+4.4/+8.9/+8.3 → −0.9/+4.3/+3.2), and the owner ruled **DO NOT PROMOTE** on
2026-09-09 because it fails C4-2025 gas NRMSE (0.298 → 0.308).

**This is not a proposal to re-open it.** Rule 1 condition (c) forbids selecting a multiplier by
sweeping for one that passes, and "then use 5 %" is the move it names. It is recorded because the
corroboration is genuinely new evidence about *where* the residual lives, and because the honest
summary of this lane is now:

> **CAISO 2022's C3a miss is identified and not currently repairable by any admissible lever
> available to this lane.** The import-quantity route is closed and inverted. The price-side routes
> are spent (charter §5 items 1–7). The only channel measured to move it is owner-blocked and
> cannot be swept.

That is a finding, not a failure — and under rule 30 `[R-TOUCHPOINT-FOLD]` (c) the 2022 rung
**never downgrades the ISO**: CAISO's determination is its train-tier verdict, and it reads
**CALIBRATED**.

---

## §7 — ARTIFACT RETRIEVABILITY (rule 34 `[R-SHARD-PROMOTABLE]` (e)) — and a charter correction

- **Arm B (the 2023–2025 span) was never lost.** The charter states its 272 MB push did not land
  and that `36ce217` does not resolve. **Both claims are false.**
  `results/calibration/caiso279_ablate_dswcouple_span/` is **tracked on `main`** with all 34 files
  **including the per-plant `dispatch/` layer**, added by commits `14081e9c` … `36ce2170`, which
  resolve. The shard's incremental per-file push strategy worked; only its final report was wrong.
  **Nothing needs re-solving and its container need not be woken** — the ~35–55 min re-solve the
  charter budgets is **not owed**. Recorded because a false "lost" costs exactly as much as a false
  "retrievable".
- **Arm A** (2022 ablation) is retrievable with zero re-solve at the immutable SHA
  **`b17ac9d0f8b505d542f279356d5300888c69a70f`** (branch `claude/caiso279-arm-2022`):
  `git checkout b17ac9d0f8b505d542f279356d5300888c69a70f -- results/calibration/caiso279_ablate_dswcouple_2022`.
  This session checked out **only** `hourly/network_2022.parquet` (partial-clone discipline: never
  resolve a blob you do not intend to download). Already covered by `.gitignore` lines 2061–2064.
  **Nothing was deleted** (rule 31 `[R-RETAIN]`).
- **The caiso-279 record was recovered, not rebuilt**: `e24c0d90` is merged into `main` via
  PR #6082.
- **This session solved nothing, so there is no promotion question to put** (rule 31). The open
  owner item is §8.

---

## §8 — THE ONE ITEM THAT NEEDS THE OWNER (unchanged from caiso-279's charter §6, not acted on)

C3a on the **DA basis**, committed bench `da_lw` vs `rt_lw`:

| year | vs RT | vs DA | spread |
|---|--:|--:|--:|
| 2022 | +11.34 % | **+2.09 %** | +9.05 % |
| 2023 | +3.18 % | −9.39 % | +13.86 % |
| 2024 | +8.37 % | −1.11 % | +9.58 % |
| 2025 | +7.70 % | +4.72 % | +2.85 % |
| **mean \|gap\|** | **7.65 %** | **4.33 %** | |

**DA is not a rescue** — 2023 over-corrects to −9.4 % and 2025 is not explained by basis at all.
The rubric's own OUT-OF-REPRESENTATION row calls the DA–RT premium something "the test must not
demand", and caiso-272 measured **70.2 %** of the 2022 dollar miss as exactly that. **This is a
rubric ruling for the owner, not a solve, and it was not acted on unilaterally.**

---

## §9 — METHOD

Zero-LP, in the parent (rule 32 `[R-SHARD]` (a)); no shard launched, so rule 33
`[R-SHARD-ARCHIVE]` has nothing to sweep. Sources: `data/raw/eia-930-interchange/CISO interchange
hourly.parquet` (EIA sign: + = CISO exports to the DIBA) and arm A's
`hourly/network_2022.parquet`. Model hour *h* → `2022-01-01 00:00 + h` (2022 is non-leap, so the
model's fixed 8,760 frame is the real calendar); actual stamps → model clock by the committed
−1 h standard-time lag. Comparison is **net-to-net** throughout, as the charter §3.1 pre-registered:
the model's corridor flow variable is net, so gating on a gross actual against a net cap would
manufacture an exceedance out of a unit mismatch. Gross is **reported** (§1, §5), never gated on.
