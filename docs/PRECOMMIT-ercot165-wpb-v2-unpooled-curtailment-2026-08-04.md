# PRE-COMMIT — ercot-165: WP-B v2, unpooled diurnal-family curtailment shares + the Panhandle interface's ONE owner

**Written and pushed BEFORE either arm solved.** Keeper at time of writing:
`2026-08-03-ercot158-pool-arm` (NOT-YET; open gates C3a 2023-only, C3b
2023-only, C3c, C7 2023-lignite cv-leg). Charter: `results/calibration/
FINDING-ercot164-wpb-nodal-identification-2026-08-04.md` §6, authorized by the
ercot-165 dispatch prompt (the ercot-159/162 structural-arm precedent).

Rule 22: years **2023 2024 2025 only**, one bundle per arm, years sequential
within each invocation (rule 12). No holdout year is solved, scored or read.

---

## 1. What is built (and what is deliberately NOT)

### 1.1 Built — the unpooled share (`ercot_wtx_curtail_unpooled`, default off)

The armed driver applies ONE pooled `congestion_share` that is a **union** over
every West-corridor element. It saturates (2025 mean 0.64) and therefore
inherits the diurnal shape of whichever family carries the most binding weight
— measured 0.70–0.77 **overnight**. Its hod profile is anti-correlated with the
mid-afternoon curtailment mode it exists to close (2025 gap-shape corr −0.67,
worsening as West solar grows), and the same overnight-shaped ceiling is
broadcast to the **Panhandle** zone in ~8,750 h/yr on top of the endogenous
Panhandle→North tie (FINDING-ercot164 §3–§4).

The unpooled driver splits that union on the **same** (net-load decile × hod ×
season) axis and from the **same** sources (NP6-86 + the NP4-160-SG spine):

| family | membership | measured character |
|---|---|---|
| **D** | daytime / solar-flood elements, **+ WESTEX** (its own lift is 1.074–1.216 → D in every year) | hod peak h14–15; corr vs ACTUAL solar curtailment **+0.775 / +0.959 / +0.775** |
| **N** | overnight / wind-export tail | hod peak h21–23; corr vs actual solar **−0.961 / −0.945 / −0.838** |
| **PNHNDL** | held OUT of the split — its owner is a mechanism choice, not a family | 2025 hod peak h10, day share 0.541, lift 1.424 |

**The membership rule is threshold-free** (rule 23 `[R-FROZEN-DERIVE]`): an
element joins family D exactly when its own binding weight in h9–17 exceeds the
year's **measured SCED-execution exposure** in those hours. The boundary is the
null (lift = 1.0). No cutoff, no minimum-n, no per-year tuning — this replaces
the ercot-164 probe's exploratory `aft>0.30 & n>=200` heuristic.

Per-zone assignment: **West takes D + N additively**, not the saturating OR.
Saturation is precisely what made the union inherit the overnight shape.

### 1.2 Built — the Panhandle owner (`ercot_wtx_panhandle_owner`, default `"tie"`)

The pre-registered A/B, on rule 19 `[R-ONE-MECH]`:

* **Arm A — `panhandle_owner="tie"`.** The endogenous Panhandle→North tie at
  measured PNHNDL limits is the **sole** Panhandle mechanism; the driver applies
  **no ceiling** to the Panhandle zone, and PNHNDL leaves the West share too.
  Depths (re-identified): wind **0.1507**, solar **0.1627**.
* **Arm B — `panhandle_owner="share"`.** A Panhandle-scoped ceiling shaped by the
  measured PNHNDL enforcement incidence owns the **sub-limit** pressure; the tie
  keeps the network limit, so the two bind in different hours (the tie
  overnight, the ceiling in the solar-flood hours). Depths: wind **0.1354**,
  solar **0.1614**.

Never both on the same hours, in either arm.

### 1.3 DOF: still exactly TWO

The two per-tech depths, and nothing else. They are re-identified per arm on the
**capacity-weighted** corridor share, with the weights measured from the EIA-860
operable fleet through the model's own `zone_assignment._ercot_zone` boundaries
(wind 0.630 West / 0.370 Panhandle; solar 0.969 / 0.031). Every corridor zone is
counted — including one whose share an arm sets to zero — so **both arms are
centred on the same measured curtailment total** and differ only in how they
distribute it. No per-family weight, no third scalar. Family membership and the
zone weights are source-data derives, not fitted values.

### 1.4 NOT built — the gtc.py stand-in change (charter §6.2's rule-14 half)

The charter asked for the tie's non-active-hour stand-in to be re-examined
against the measured enforcement structure, on the hypothesis that the static
2,680 MW fill over-constrains the corridor overnight. **Measurement refutes the
hypothesis**: the measured active-hour p50 limit over static rating is

| GTC → link | 2023 | 2024 | 2025 |
|---|---|---|---|
| PNHNDL → Panhandle→North | 0.963 | 1.209 | 1.048 |
| WESTEX → West→North | 1.000 | 1.024 | 1.000 |
| WESTEX → West→South_Central | 1.014 | 1.038 | 1.014 |
| NE_LOB → Northeast→North | 0.966 | 0.969 | 1.191 |

The level is right (within ~5 % for PNHNDL in 2023 and 2025; the 2024 +21 % is
the outlier, and the direction is mixed, not one-way). So the manufactured
overnight binding is **not** a data error: it is the reduced network's
*aggregate* flow reaching a correct cap in hours the real *nodal* system had
headroom. That is a topology-resolution limit, and the West/Panhandle topology
split stays CLOSED (scope fence). Releasing the cap on non-active hours would be
a fabricated relaxation with no forward analogue (rule 13) — refused. **No
`data/gtc.py` change is built, and no NE_LOB confound enters the A/B.**

---

## 2. Phase-0 results, declared before the LP (identification, no solve)

Probe `scripts/probes/ercot165_family_split_phase0.py` →
`results/calibration/ercot165_family_split_phase0.json`.

**Vintage duty — this session's OWN match rate, on this session's OWN
population, on the production curate path's spine
(`data/raw/ercot-settlement-points`):** stations resolved **633/693 (91.3 %) /
644/713 (90.3 %) / 689/765 (90.1 %)** for 2023/2024/2025, endpoint weight
**92.5 / 94.4 / 93.0 %**. ERCOT-164's and ERCOT-160's rates are NOT inherited.

**PASS — the split is identifiable and generalizes.** LOYO (membership trained
on two years, applied to the held-out year): binding-weighted membership
agreement **0.755 / 0.942 / 0.968**; held-out family-share hod corr **+0.744 to
+0.999**, hourly corr +0.548 to +0.902. The per-family share table's LOYO shape
correlation **beats the pooled table in every year** (D +0.388/+0.424/+0.419,
N +0.400/+0.473/+0.473 vs pooled +0.347/+0.380/+0.338), and the arms' LOYO level
predictions match the pooled table's.

**HONEST PHASE-0 NEGATIVE (declared here, not discovered after the fact).**
Unpooling **by itself does not fix the West zone's imposed shape** at the
two-depth budget. On the HSL-weighted bound reduction — `share(t) × HSL(t)`, what
the ceiling actually removes, and the depth's own denominator — the 2025 wind
profile's correlation with actual curtailment goes pooled **−0.001** → D+N
**−0.076** → D+N+PNHNDL **+0.012**. The additive sum is still dominated by
family N's weight, and any re-weighting is exactly the extra DOF the charter
fences. The shape lever that IS available at two depths is the **per-zone
assignment**: the Panhandle zone's ceiling shape goes from the pooled overnight
profile (2025 wind bite corr −0.001) to the PNHNDL profile (**+0.729**).

Phase 0 therefore **structurally indicates arm B**. Both arms still solve, and
both are judged on the gates below — the indication is recorded so it cannot be
retro-fitted.

**Known confound, bounded.** The committed pooled share table is a 2026-07
vintage that does not byte-reproduce from today's archives (870 vs 872 cells,
mean |Δ| 0.019). The keeper solved on the committed vintage; both arms solve on
tables derived from today's sources. The effect is negligible: re-deriving the
pooled table from current sources gives hourly corr 0.992–0.993 and **hod corr
0.9997–0.9999** against the committed one, with mean share moving < 0.002. The
committed pooled CSV is left **untouched** (rule 23 — no source-data change to
cite), and `derive_ercot_wtx_curtailment_share.py` gains `--family-only` so it
cannot be clobbered incidentally.

---

## 3. Judgment criteria — pre-registered

**This is a QUANTITY object (rule 1).** A ceiling-clipped variable is never
marginal, so this is **NOT** a C3a/C3b/C3c lever and *"the price residual didn't
move"* is not a verdict on it. Judged on:

1. **[3e] curtailment VOLUME** — model wind and solar curtailment TWh vs
   reported (`HSL − delivered`), all three years.
2. **The §4 SHAPE** — model wind curtailment hod correlation vs actual. The
   keeper is **+0.645 / +0.462 / −0.077** (2023/24/25). The 2025 leg going
   **positive** is the headline shape target; afternoon (h13–17) and overnight
   (h21–02) mass shares are reported alongside.
3. **C2-adjacent gas displacement** — curtailing corridor VRE re-dispatches gas;
   the gas classes' volume must not degrade.
4. **D-1 wind/solar diurnal shape** (`profile_r` / `cv_ratio`).
5. **LOYO within 2023–2025** before any promotion (rule 22).

**Kill gates (a breach fails the arm outright, whatever else improves):**

* **K1 — over-curtailment.** Either tech's model curtailment exceeding reported
  by > 25 % in any year.
* **K2 — shape regression.** 2025 model wind curtailment hod corr **below the
  keeper's −0.077** (the arm must not make the documented inversion worse).
* **K3 — zonal starvation.** A corridor zone's annual wind or solar dispatch
  falling > 40 % below the keeper's (the ceiling is commitment scaffolding for a
  bound, not a fleet deletion).
* **K4 — C2 collapse.** Any material gas class's annual volume error degrading
  by more than 3 pp vs the keeper in any year.
* **K5 — spurious scarcity.** New model > $300 hours outside the actual tail
  exceeding the keeper's by more than 10 in any year.

**Level guard (reported, not a kill gate):** C3a analyzer-basis level error is
recorded for both arms with the keeper's `−24.5 % / +10.2 % / −0.7 %` as the
reference. Under the owner's standing keeper standard for this dispatch,
structural fidelity governs: an arm that is the more structurally faithful run
and passes LOYO **may** be promoted even if some open gates regress (rule 1).

**Refusal condition.** If both arms breach a kill gate, or LOYO fails, the
outcome is recorded honestly, the matrix cell takes the refuting verdict, and
the keeper stays `2026-08-03-ercot158-pool-arm`. No forcing, no re-tuning to
rescue an arm.

---

## 4. The exact recipe

Both arms are single-delta replays off the keeper bundle
(`results/calibration/ercot158_poolarm_B`) via the sanctioned
`scripts/replay_keeper.py --set` path, so every other keeper setting is
reproduced from `meta.json` and both arms differ from the keeper only in the
listed keys.

```
# Arm A — the tie owns the Panhandle interface
python scripts/replay_keeper.py results/calibration/ercot158_poolarm_B \
  --out-dir results/calibration/ercot165_unpooled_tie_A \
  --set ercot_wtx_curtail_unpooled=true \
  --set ercot_wtx_panhandle_owner='"tie"' \
  --set ercot_wtx_curtail_depth_wind=0.1507 \
  --set ercot_wtx_curtail_depth_solar=0.1627 \
  --note "ercot-165 arm A: unpooled diurnal-family curtailment shares; PNHNDL owned by the endogenous tie (no driver ceiling on Panhandle)."

# Arm B — a Panhandle-scoped share owns the sub-limit pressure
python scripts/replay_keeper.py results/calibration/ercot158_poolarm_B \
  --out-dir results/calibration/ercot165_unpooled_share_B \
  --set ercot_wtx_curtail_unpooled=true \
  --set ercot_wtx_panhandle_owner='"share"' \
  --set ercot_wtx_curtail_depth_wind=0.1354 \
  --set ercot_wtx_curtail_depth_solar=0.1614 \
  --note "ercot-165 arm B: unpooled diurnal-family curtailment shares; PNHNDL sub-limit pressure owned by a Panhandle-scoped measured share."
```

Data layer (already run, committed with this doc):

```
python scripts/data/curate_ercot_wtx_congestion.py          # schema v2, family columns
python scripts/data/derive_ercot_wtx_curtailment_share.py --family --family-only
```

Both arms are registered on the backcast dashboard whatever the verdict
(rule 15), the tested matrix cell is updated in this session (rule 28b), and the
session is logged in `docs/calibration-log/ercot.md`.
