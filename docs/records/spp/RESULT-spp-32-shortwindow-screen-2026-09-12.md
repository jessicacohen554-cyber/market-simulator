# RESULT — SPP-32: the measured sub-5-day unit-availability family, screened on 2025.

## ARM B (COAL + GAS) IS KILLED on two pre-registered gates. ARM A (COAL) clears four of five and fails the fifth on a gate this lane wrote badly — and says so rather than rewriting it.

**Lane** SPP-32 · **PRECOMMIT** `docs/handoffs/PRECOMMIT-spp-32-shortwindow-availability-2026-09-12.md`
(every gate, bound and screen year sealed there **before** either solve) · **Base / pinned shard
revision** `dce9398314b146d9110baad6b3e3adcc999b0c5f` (merged to `main` as PR #6024) ·
**Control** `2026-09-10-spp-27-commitment-grain`, bundle `results/calibration/spp27_span`, COMMITTED,
differenced and **never re-solved** (rule 29(b) form 4; the G-DRIFT audit is PRECOMMIT §3) ·
**Parent LP: ZERO** (rule 32 `[R-SHARD]` (a)) · **Shard LP: 202 s + 138 s = 340 s across two
containers** · **Keeper UNCHANGED. Nothing registered. No marker touched.**

Shard records, pushed by the shards themselves and the only artifact that left their containers:
`docs/handoffs/SHARDREPORT-spp32-A-2025.md`, `docs/handoffs/SHARDREPORT-spp32-B-2025.md`.

---

## 1. THE GATE TABLE

Scored by the parent against the keeper's committed 2025, on the five gates exactly as the PRECOMMIT
wrote them. The C3a / C3b instrument is validated first: replaying the parent's own arithmetic on the
**control's** committed sidecar reproduces the scorer to 4 decimals — load-weighted mean **28.7893**
(scorer 28.79) and monthly NRMSE **0.1638** (scorer 0.164) — so the arm numbers below are on the
scorer's own footing.

| gate | arm A (coal) | arm B (coal + gas) |
|---|---|---|
| **G1 direction** | coal −2.5714 TWh · **PASS** | coal −1.4608, gas-scope classes −2.3567 TWh · **PASS** |
| **G2 confinement** | 23 COAL plant-groups, no gas / CT / VRE availability moved · **PASS** | 55 plant-groups = COAL 23 + CC_REGULAR 18 + ST_GAS 13 + CC_CHP 1, exactly the two extracts' declared groups · **PASS** |
| **G3 magnitude bound** | 2.5714 < 3.857 TWh and > 0 · **PASS** | 3.8175 < 9.43 TWh and > 0 · **PASS** |
| **G4 identity** | demand Δ0.0000 ✓ · dump 0.0000 ✓ · **slack 240.5966 MWh** ✗ · **FAIL** | demand Δ0.0000 ✓ · dump 0.0000 ✓ · **slack 10,911.0219 MWh** ✗ · **FAIL** |
| **G5 no non-target regression** | C3a +5.15 % PASS · C3b 0.1878 PASS · **PASS** | C3a **+15.97 % PASS→FAIL** · C3b **0.2619 PASS→FAIL** · **FAIL** |

**Every load-bearing 2025 C1 row and all of C2 are SKIPPED by the scorer on the preliminary EIA-923
vintage**, so on the screen year G5 reduces to C3a and C3b. That is a property of 2025, recorded so
nobody later reads G5 as a broader clearance than it is.

| | control | arm A | arm B | gate |
|---|---:|---:|---:|---|
| C3a load-weighted mean LMP (\$/MWh) | 28.7893 (+0.66 %) | 30.0737 (**+5.15 %**) | 33.1683 (**+15.97 %**) | ±10 % |
| C3b monthly LW NRMSE | 0.1638 | 0.1878 | **0.2619** | ≤ 0.20 |
| slack (MWh) | 0.0000 | 240.5966 | **10,911.0219** | — |
| max zonal dual (\$/MWh) | 73.7731 | 2000.0000 | 2000.0000 | — |
| hours > \$200 | 0 | 2 | 18 | — |
| actual RT hours > \$200 | 68 | 68 | 68 | — |

---

## 2. ARM B IS KILLED — and this lane predicted the failure mode before the solve

PRECOMMIT §7 named, in advance, what would make this lane report against itself:

> *"if arm B's response exceeds G3's bound, or slack appears under G4, the honest reading is that
> 2,838 gas windows over three years is too many for a merit-order guard to have filtered — SPP's CC
> fleet runs at ~49 % CF, and a 1–5 day dead span at that CF can be economics rather than an outage."*

That is what happened, and worse than the sealed text anticipated: **G3 held** (the response is
inside its bound), but **G4 blew out** — 10,911.0219 MWh of unserved energy in 12 hours, all in
SPP-South, in three clusters (2025-09-15, 2025-10-06, 2025-12-21), every hour priced at VOLL \$2,000
— and **G5 failed on BOTH load-bearing price criteria**, C3a to +15.97 % and C3b to 0.2619.

**The entire price move is scarcity, not merit order.** The 18 hours above \$200 are all exactly
\$2,000, i.e. the slack penalty; the annual mean rises 28.7893 → 33.1683 because the LP is short in
three afternoons, not because the stack re-ranked. Arm B does not price SPP better; it makes SPP
infeasible.

**Rule 28(d), demonstrated rather than asserted.** `unit_outage_short_windows` is `K` (keeper) in PJM
and MISO. Its gas limb, derived for SPP with an invocation **byte-identical to PJM's on every knob**,
takes SPP's LP to 10.9 GWh of unserved energy. The verdict does not transfer, and the reason is
fleet conduct: the coal detector's `SHORT_BASELOAD_CF` guard is a baseload test, and the gas
detector's merit-order substitute does not separate a forced dead span from economic idling on a
fleet whose CC classes run at ~49 % CF. **SPP's cell is `R`, on SPP's own evidence.**

The gas extract itself (`data/raw/campd-unit-outages-shortgas-SPP.csv`, 2,838 windows) **stays
committed**. It is a correctly-derived measured artifact; what this lane rejects is arming it in
SPP's LP, not the data.

---

## 3. ARM A — four gates clear, and the fifth is a gate THIS LANE WROTE BADLY

G1, G2, G3 and G5 all pass. The coal overlay fires (`short unit-outage derate (SPP 2025): 94
plant-tranches derated`), removes 2.5714 TWh of coal, and hands 2.3710 TWh of it to gas — the
direction, confinement and magnitude a coal-scoped availability derate must produce.

**G4 fails as written, and this lane applies it as written.** The PRECOMMIT says `slack` stays
**0.0000 MWh**; arm A produces **240.5966 MWh**, in 2 hours, in SPP-South, at VOLL.

**But the gate is defective, and the measurement that shows it is the control's own span:**

| keeper 9, committed | slack | slack hours | zone | max zonal dual | hours > \$200 |
|---|---:|---:|---|---:|---:|
| 2023 | 0.0000 MWh | 0 | — | 59.3126 | 0 |
| **2024** | **370.1017 MWh** | **2** | **SPP-South** | **2000.0000** | **5** |
| 2025 | 0.0000 MWh | 0 | — | 73.7731 | 0 |

**The incumbent keeper carries a LARGER slack event than arm A introduces** — 370.1017 MWh against
240.5966 MWh — in the same number of hours, in the same zone, at the same VOLL price. "Slack stays
0.0000" is therefore a standard the designated keeper does not meet on its own three-year span. This
lane wrote G4 after looking only at 2025, where the control happens to be zero, and generalised a
one-year accident into a gate.

**The gate is NOT being rewritten.** Re-reading a pre-registered gate after seeing the number it
returns is exactly the fitted-mechanism selection rule 1 `[R-STRUCT]` (c) forbids, and a screen is a
STOP gate whose whole value is that it binds. **Arm A is therefore STOPPED at the screen**, and the
defect in the gate's construction is reported to the owner as a fact about this lane's instrument
rather than used as a licence to pass the arm.

What arm A also does, reported at full magnitude and **not** as a reason to reject it (rule 1: a
structurally-correct mechanism is never judged by the residual): C3a degrades +0.66 % → +5.15 % and
C3b 0.1638 → 0.1878. Both still pass. Neither is a criterion this arm was chartered against.

---

## 4. WHAT THE SCREEN SETTLES ABOUT CARD R-bf — nothing new, and that was predicted too

PRECOMMIT §4 recorded, before either solve, that this family removes a mean **557.6 MW** per hour
across 2024's 35 DA-tail hours against a model holding a median **8,233 MW** of headroom — **6.8 %** —
so it cannot reach C3c. The screens are consistent: neither arm produces a scarcity **curve**. Arm A's
2 hours and arm B's 18 hours above \$200 are **all exactly \$2,000**, the VOLL slack penalty, against
an actual 68 hours distributed across a real price distribution. **`FINDING-spp-29`'s conclusion is
untouched: SPP's absent tail is an offer markup of 7.3–9.5× marginal cost, and no availability
mechanism reaches it.**

---

## 5. MECHANISM MATRIX (rule 28(b), SPP's shard only)

| mechanism | before | after | basis |
|---|---|---|---|
| `unit_outage_short_windows` | `U` | **`O`** | screened on 2025; G1/G2/G3/G5 clear, G4 stopped it on 240.5966 MWh of slack against a gate the control's own 2024 (370.1017 MWh) shows is mis-set. Not adjudicated; **promotion is the owner's act** (the posture SPP-52a's producing lane set). |
| `unit_outage_short_windows_gas` | `U` | **`R`** | killed on two pre-registered gates: G4 slack 10,911.0219 MWh in 12 hours at VOLL, and G5 flipping **both** load-bearing price criteria (C3a +15.97 %, C3b 0.2619). Rule 28(d) non-transfer from PJM/MISO `K`, on SPP's own fleet conduct. |

No other cell moves. No verdict is minted for any mechanism this lane did not solve.

---

## 6. RULES

- **Rule 29 `[R-SCREEN]`** — screen year **2025**, named in the PRECOMMIT on the mechanism's own
  largest measured footprint (coal 7,050.714 GWh, gas 11,354.227 GWh, total 18,404.941 GWh — largest
  on every basis), never on a residual. One year per arm. **The full span was NOT spent**: arm B is
  killed and arm A is stopped, so 2023 and 2024 were never solved for either. Gates were STOP-only
  and none read C3c.
- **Rule 29(b) / G-DRIFT** — all six changed solve-path files between the keeper's `basis_sha`
  `09d9fc00` and the pinned base classify INERT (PRECOMMIT §3), so form 4 held and **no control
  solve was spent**.
- **Rule 29(c) + rule 31 `[R-RETAIN]`** — the screen bundles are kept out of `main` by
  `.gitignore` (`results/calibration/spp32_*/`, added in this commit — the seam the arm-B shard
  correctly flagged and correctly declined to fix itself), **never by `rm`. No `rm` was issued by
  the parent or by either shard.**
- **Rule 32 `[R-SHARD]`** — the parent solved nothing. Two shards, one year each, pinned to a full
  40-character SHA, each committing exactly ONE markdown file and nothing under `results/`. Both
  reported their hard stops PASS and neither edited `src/` or `scripts/`.
- **Rule 21 `[R-DOF]`** — zero free parameters added; SPP's ledger stays **n_entries 3 /
  n_residual 2**. The derive invocation is byte-identical to PJM's committed sidecar on every knob.
- **Rule 1 `[R-STRUCT]` / 13 `[R-MEASURED]`** — `offer_curve_by_group` byte-identical at a uniform
  0.93 in **both** arms, verified by the shards with `json.dumps(sort_keys=True)` over the whole
  mapping. No adder, offset, haircut, proxy or rescaled input.
- **`[R-HOLDOUT]` removed 2026-09-09** — no number here is a certified out-of-sample skill claim.
- **No `complete` or `frontier` declaration is added, requested or implied.**

---

## 7. RETENTION AND THE PROMOTION QUESTION (rule 31 `[R-RETAIN]`)

**Both screen bundles are already gone.** They were written on the shards' ephemeral containers,
which have been reclaimed; nothing was deleted by anyone. This document and the two SHARDREPORTs
carry **every number this lane will ever cite**, which is what rule 29(c) asks the record to be.

**The promotion question, put explicitly rather than left unasked:**

> **Arm A (`unit_outage_short_windows` for SPP) is a rule-14 `[R-ACCURATE]` measured input on an
> untested cell that cleared four of five pre-registered gates and was stopped by the fifth, which
> this lane has shown to be mis-set against the control's own span. Should it go to the full
> 2023–2025 span?**
>
> Cost if yes: **3 shards, ~166 s of LP each** (SPP's measured 499 s / 3 years), plus a re-solve of
> 2025 because the screen bundle did not survive its container. Nothing else is needed — the extract
> is committed, the flag exists, and zero code changes.
>
> This lane does **not** recommend arming arm B under any conditions.

**Successor for arm A if it is not promoted:** the object is not the flag but G4's real question —
whether SPP-South's 2 slack hours are a genuine adequacy signal (as the keeper's own 2024 event
suggests) or a topology artifact of a 2-zone SPP. That is card **R-bb**'s territory
(`FINDING-spp-64` §5), not this family's.

**Next shorthand: spp-33.**
