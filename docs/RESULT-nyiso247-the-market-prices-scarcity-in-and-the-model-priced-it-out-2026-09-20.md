# RESULT — nyiso-247: the fuel-invariance limb is REFUTED on measured conduct, the disarm clears EVERY pre-registered gate, and the registered full span moves NOT-YET → CALIBRATED

**Session** nyiso-247 (ORCHESTRATOR — rule 32 `[R-SHARD]` (a); **zero LP in this container**).
**Date** 2026-09-20. **Base** `origin/main` at `f5b2356a`.
**PRECOMMIT** `docs/PRECOMMIT-nyiso247-fuel-invariance-limb-2026-09-20.md`, pushed at **`40316764`**
before any gated number existed. **Phase 0** `docs/ADDENDUM-nyiso247-phase0-gates-and-two-falsified-claims-2026-09-20.md`,
pushed at **`42d75053`** — the SHA all four shards were pinned to.
**Keeper (incumbent, UNCHANGED)** `2026-09-19-nyiso241-ct-committed-measured`.
**Arm (registered)** `2026-09-20-nyiso247-fuel-invariance-disarm`, bundle
`results/calibration/nyiso247_fuelinv_span`, years {2022, 2023, 2024, 2025}.

> ## HEADLINE
> 1. **THE MARKET PRICES SCARCITY INTO ITS IMPLIED OFFER HEAT RATE AND THE ARMED MODEL PRICES IT
>    OUT.** `gas_offer_net_revenue_margin` adds `markup_hr × (anchor − fuel)`, so the offer's
>    implied heat rate **falls** as delivered gas rises. NYISO MIS P-27 measures the market's
>    **rising +2.035 / +11.928 / +27.880** MMBtu/MWh at p50 / p75 / p90.
> 2. **IT LIVES ON THE PEAK BAND — the rung that sets the price in a scarcity hour.** Markup
>    multipliers there are **3.000** (CT_PEAKER) and **3.200** (ST_GAS) against 0.075–0.342 on
>    every econ band. Over 38 peak rows / 1,544.2 MW the armed term removes
>    **−$109.00 / −$49.20 / −$96.20 / −$141.08 /MWh** in each year's top gas decile.
> 3. **THE FORM IS THE DISARM** — revert to the family's *registered* multiplier form. **Zero new
>    code, zero new `ScenarioConfig` field, ZERO DOF MOVED** (verified mechanically, §4). The
>    markup **survives at full strength**; only its fuel basis moves.
> 4. **EVERY PRE-REGISTERED GATE CLEARS** (§3), and the registered full span 2022–2025 reads
>    **NOT-YET → CALIBRATED**. The ISO tier 2023–2025 stays **CALIBRATED**.
> 5. **AND IT IS STATED AGAINST ITSELF** (§5): the disarm closes the **SIGN** and no more, the
>    bottom sixth of the distribution gets **worse**, the PRECOMMIT's own level-neutrality claim was
>    **falsified before the solve**, and C1-2023 ST_GAS now sits **at** its share boundary.
> 6. **A PROMOTION DECISION IS OWED (§7)** — this re-opens a `K`-verdict keeper mechanism.

---

## 1. WHAT WAS FIXED BEFORE ANY NUMBER EXISTED

The PRECOMMIT fixed **the form** (and named the three alternatives it refused, on structure), the
rule-19 argument, the G-DRIFT audit, every gate and every bar, and the promotion criteria P1–P5.
The addendum then recorded phase 0 — including **two of my own claims that its gates falsified** —
**before a shard was launched**. Nothing below was chosen after seeing a result.

**The algebra the form follows from**, per tranche, `G(t)` delivered gas and `a` the anchor:

```
ARMED    :  mc/G = base_HR × phys  +  base_HR × (mult − phys) × a / G(t)   → FALLS as G rises
DISARMED :  mc/G = base_HR × mult                                          → FLAT in G
BOOK     :                                                                 → RISES in G
```

**The registered family has exactly two members.** The armed one is the *only* member whose
conditional implied-heat-rate response is strictly negative; the disarmed one is the *unique* member
whose response is exactly zero. The measured response is positive. The disarm is therefore the
family's closest admissible point to the measurement **and adds no free parameter**.

### 1.1 Why this is not what nyiso-195 or nyiso-167 refused

* **nyiso-195 killed removing the CC_REGULAR econ MARKUP** (`econ_low/econ_high := phys_*`). Under
  the disarm `mult` is **untouched** — the markup survives at full strength and only its fuel basis
  moves. Different change; and G-C (§3) tests it against that session's own killing margin anyway.
* **nyiso-167 refused a PER-YEAR RE-ANCHOR**, explicitly *"DO-NOT-REDO absent new measured NYISO
  offer data."* The P-27 genbids corpus **is** that data, and a per-year re-anchor is **not**
  proposed here. The DO-NOT-REDO is satisfied on its own terms rather than argued around.

### 1.2 The three alternatives refused on structure, before any number

| form | refused because |
|---|---|
| **partial anchoring** `mk × (a + θ(G−a))`, θ∈[0,1] | θ is a new DOF with no identification inside the family, and the family **saturates at θ=1** — the measured response is above the whole family, so θ pins at its boundary. A boundary-pinned DOF buys nothing and is sweepable. |
| **one-sided floor** `mk × max(a, G)` | (a) the kink at the anchor is a shape the book does not support; (b) **decisive** — it removes only the negative half of a term whose annual mean is ≈0, so it is a **level increase with no measured level behind it**. This was the *more conservative* arm on §3's overshoot leg and was declined anyway. |
| **sign flip** `mc += mk × (G − a)` | the only candidate reaching the book's positive sign — and it uses a *heat-rate markup* as the coefficient of a *fuel-excess sensitivity*: nyiso-167's own "derivation-vs-dispatch basis mismatch", on an unidentified number, doubling the peak-band intervention. |

---

## 2. THE SOLVE — four year-isolated shards, one composite, zero LP in the parent

Rule 36 `[R-YEAR-ISOLATION]` (a): one year, one shard, one container, own `--out-dir`, all pinned to
`42d750537532c95d335286b63bca881e8a01c76b`. Each arm is a `replay_keeper.py --set` **single delta**
off the keeper's own committed bundle:
`gas_offer_margin=false`, `gas_offer_margin_zonal_anchor=false`,
`gas_offer_margin_zonal_anchor_vintage=false` (the latter two resolve the **same** mechanism's
identification point and hard-error without it — `data/fleet/assembly.py:210`).

| year | leg | signature | files pushed | load-wtd LMP keeper → arm |
|---|---|---|---:|---|
| 2022 | `nyiso247_fuelinv_2022` | **OK** | 17 | 72.3850 → **73.2938** (+1.26 %) |
| 2023 | `nyiso247_fuelinv_2023` | **OK** | 17 | 31.5148 → **31.5963** (+0.26 %) |
| 2024 | `nyiso247_fuelinv_2024` | **OK** | 17 | 37.9500 → **38.2250** (+0.72 %) |
| 2025 | `nyiso247_fuelinv_2025` | **OK** | 17 | 60.0224 → **60.4314** (+0.68 %) |

All four pushed **FULL** bundles including `dispatch/<year>_P1.parquet` (rule 34 `[R-SHARD-PROMOTABLE]`
(a)), by a `.gitignore` negation plus a plain `git add`. Composition is
`scripts/probes/nyiso247_compose_span.py` — nyiso-238's own recipe plus this lane's delta assertion
(all three fields False on every leg, read off the **resolved** `scenario_config`, before any file
is copied), so a leg that had silently solved the keeper's recipe could not compose in looking like
a null result. **No control solve was spent**: G-DRIFT over `83543f3c → f5b2356a` found 6 changed
files, every hunk INERT for a NYISO backcast (PRECOMMIT §5), so rule 29 `[R-SCREEN]` (b) form 4
holds and the committed keeper is the control.

---

## 3. THE GATES — every one pre-registered, every one clears

### G-A — IDENTITY: **PASS, EXACTLY.**
Keeper median armed-row `d(mc)/d(fuel)` **7.7475** MMBtu/MWh (`phys × base_HR`) → arm **9.5758**
(`mult × base_HR`), a difference of **1.8283** = the median `offer_markup_hr` to machine precision.
Max slope error **0.0**; **zero** movement on every row whose markup is 0. All four years.
(Bar was ≤ 1e-4 $/MWh.)

### G-B — THE SIGN GUARD: **PASS on all three legs.**

| rank | keeper | **arm** | book | gap keeper → arm |
|---|---:|---:|---:|---|
| p10 | −8.4273 | −3.0892 | −16.4739 | +8.0466 → **+13.3847** |
| **p50** | −0.8485 | **+0.4094** | +2.0352 | −2.8837 → **−1.6258** |
| **p75** | +0.5530 | **+2.0182** | +11.9281 | −11.3751 → **−9.9099** |
| **p90** | +2.8072 | **+5.4709** | +27.8803 | −25.0731 → **−22.4094** |
| p99 | +11.8388 | +23.9533 | +96.7097 | −84.8709 → −72.7564 |

* **S1 direction — PASS.** Up at every rank; **the median conditional response crosses NEGATIVE to
  POSITIVE.**
* **S2 no overshoot — PASS with margin.** Max positive excursion over every rank ≥ p50 is
  **−1.6258**; the arm never crosses the book.
* **S3 net closure — PASS.** Full-grid rank-mean `|Q_mod − Q_book|` **12.1646 → 11.9268**.

### G-C — LOADING SHAPE (nyiso-195's exact prior): **PASS 4 of 4.**
CC_REGULAR class MW-weighted 80–90 % loading share, both legs read out of the one payload encoder.
**Bar: keeper + 0.5 pp** — nyiso-195's own measured killing margin (33.0 → 33.5), adopted unchanged.

| year | keeper | arm | bar | move |
|---|---:|---:|---:|---:|
| 2022 | 31.84 | 32.15 | 32.34 | **+0.31** |
| 2023 | 29.00 | 28.68 | 29.50 | **−0.32** |
| 2024 | 34.37 | 34.44 | 34.87 | **+0.07** |
| 2025 | 30.53 | 30.76 | 31.03 | **+0.23** |

### G-D — C1 / C2: **PASS. No per-year status moved in any year.**

### G-F — RULE 19: **PASS.** The arm **removes** one of the five armed non-base writers and adds
nothing. `nyiso_st_gas_econ_bands_deleaked` and `nyiso_ct_peaker_committed_measured` both stay armed
and untouched; the ST_GAS markup that routes to OPEN ROOT CAUSE **#1344** reverts to the multiplier
form rather than being removed, so that issue is **neither closed nor stacked upon**.

### The determination

| scope | keeper | **arm** |
|---|---|---|
| registered full span 2022–2025 | **NOT-YET** | **CALIBRATED** |
| ISO tier 2023–2025 (rule 30(c)) | CALIBRATED | **CALIBRATED** |

C3a-2022 **FAIL −10.8 % → PASS −9.6 %**; C3b-2022 **FAIL 0.201 → PASS 0.187**. Per PRECOMMIT **P4
these are REPORTED and are NOT the promotion criterion** — the case is P1, the gates.

---

## 4. ZERO DOF, VERIFIED MECHANICALLY RATHER THAN ASSERTED

`build_dof_ledger.py` on the arm yields **8 entries / 6 residual**, against the keeper's *committed*
14 / 6 — which looks like a six-entry drop. It is not. Re-running the builder at HEAD on **the
keeper's own `run_config.json`** yields the **identical 8-entry / 6-residual ledger**, entry name for
entry name. The difference is a HEAD change in the builder, not an effect of the disarm: **the arm
and the keeper have byte-identical DOF ledgers.** `authorized_price_tuning` stays `null` — no band
multiplier moved, so rule 1 `[R-STRUCT]`'s carve-out is **not** invoked.

*Noted, not fixed (it is a pre-existing condition and not this lane's to rewrite):* the incumbent
keeper's **committed** attestation carries the stale 14-entry ledger.

---

## 5. STATED AGAINST ITSELF — the four things a reader must not be allowed to miss

1. **The disarm closes the SIGN and no more.** It moves the model's conditional response from
   negative to **zero**; the book's is **positive**. The remaining rise belongs to the conditional
   level-dispersion object (nyiso-246 refused it **on form**, `r_anchor = 0.145`, while measuring
   the object itself at **25.845** MMBtu/MWh, clearing 4 of 4 years) and to the **daily-citygate**
   successor. An arm landing `Q_mod ≈ 0` has captured what this PRECOMMIT named and nothing beyond.
2. **Below p50 the fit WORSENS** — rank-mean `|Q_mod − Q_book|` **6.9868 → 9.0060**, driven by p10
   (+8.05 → +13.38). S3 passes because the gain above p50 exceeds that loss, **narrowly**: a 2.0 %
   full-grid closure.
3. **The PRECOMMIT's level-neutrality claim was FALSIFIED by its own gate, before the solve.** The
   removed term's capacity-weighted annual mean is **−1.49 / −2.01 / −2.77 / −1.59 $/MWh** ISO-wide
   and **−4.36 to −5.73 in NYC**, because the per-zone anchors are not each zone's own delivered mean
   once `nyiso_zonal_gas_basis` applies. **The disarm IS a level intervention in a load pocket**, not
   the pure redistribution §2.2 asserted.
4. **C1-2023 ST_GAS is now AT its boundary and it moved the wrong way**: **+3.15 → +3.59 TWh**
   against ±3.82, and **share +2.6 → +3.0 pp against a ±3 pp band**. It reads PASS with essentially
   no room left. C4 correlation also slips marginally in every year (2022 r 0.865 → 0.862), and
   C3c-2022's model tail roughly doubles (7 h → 16 h) against **101 h** actual — nowhere near closed.
   C8 forced shares all improve slightly (2022 ST_GAS 22.2 % → 20.5 %).

---

## 6. RETRIEVABILITY (rule 34 `[R-SHARD-PROMOTABLE]` (e))

**The registered composite is on this lane's branch and lands on `main` when the PR merges** — the
slim bundle (`meta`/`run_config`/`metrics`/`legitimacy_diagnostics`/`calibration_attestation` +
twenty `hourly/` sidecars), the registry sidecar and the 776 KB run payload, blob-verified identical
after push (rule 27). **That is what a promotion needs and it is durable.**

The four per-year legs are **`.gitignore`d, not deleted** (rule 31 `[R-RETAIN]`), and live on shard
branches recorded by immutable SHA in the `.gitignore` comment as **provenance, not a recovery
route** — those refs are cut when this lane's PR merges (rule 33 `[R-SHARD-ARCHIVE]` (f)(1)). The
composite does **not** carry `dispatch/` (gitignored repo-wide), so a *re-registration from scratch*
would cost a re-solve: **~5 min/year, ~20 min wall across four parallel shards.** Re-scoring,
re-gating and the dashboard need only what is committed.

## 7. THE DECISION OWED — the owner's, and it is open

Rule 31 `[R-RETAIN]`: **nothing was deleted**, and the promotion question is put here rather than
acted on. This arm re-opens `gas_offer_net_revenue_margin`, a **`K`-verdict keeper mechanism** that
three prior sessions (nyiso-167, -182, -195) each declined to move.

**The case FOR promotion is structural, and it is the PRECOMMIT's own P1:** every pre-registered
gate clears; the basis is a measured offer book rather than a residual; it **removes** a mechanism
and a free-parameter-free one at that (zero DOF moved); it satisfies both prior DO-NOT-REDOs on
their own terms; and it repairs a **sign error** on the price-setting rung worth $49–141/MWh in each
year's tightest gas decile. Rule 1 `[R-STRUCT]` is the frame: the run is a keeper for being
structurally faithful, and the CALIBRATED headline is a consequence, not the argument.

**The case AGAINST, stated as plainly:** it is a **level intervention in NYC** that the PRECOMMIT
wrongly predicted would be neutral; it makes the bottom sixth of the conditional distribution
**worse**; its net closure is only **2.0 %**; it leaves C1-2023 ST_GAS **at** its share boundary with
no headroom; and it closes only the sign, so the object nyiso-245/246 identified remains open.

**My recommendation: PROMOTE.** The gates were fixed before the numbers, all of them clear, the
basis is measured conduct, and the change *removes* a mechanism the measurement contradicts rather
than adding one. The costs in §5 are real and are reported at full magnitude; none of them is a
gate, and none is repaired by keeping a mechanism that prices scarcity out.

**If promoted**, rule 35 `[R-PROMOTE]` applies in full and the year union is already enumerated
**before** any prune (rule 35(b)): the NYISO registry carries exactly one run, the incumbent keeper,
with years **{2022, 2023, 2024, 2025}** — covered **exactly** by this arm, so no year is lost.
Sequence: re-key `frontend/data/backcast/keepers/NYISO.json` and `calibration-complete.json` →
`audit_keepers.py` (E1/E13) → `prune_iso_runs.py --iso NYISO --force-uncite` → `build_status.py
--iso NYISO` → re-stamp the matrix shard.

**If not promoted**, the arm stays registered as an adjudicated candidate, the incumbent keeper is
untouched, and the NYISO cell stays `K` with this session's refutation recorded in it.

## 8. ARTIFACTS

| path | what |
|---|---|
| `docs/PRECOMMIT-nyiso247-fuel-invariance-limb-2026-09-20.md` | the pre-registration, at `40316764` |
| `docs/ADDENDUM-nyiso247-phase0-gates-and-two-falsified-claims-2026-09-20.md` | phase 0 + the two falsified claims, at `42d75053` |
| `scripts/probes/nyiso247_fuelinv_phase0.py` → `results/calibration/_nyiso247_fuelinv_phase0.json` | G-A / G-B / G-E / G-F |
| `scripts/probes/nyiso247_loading_shape.py` → `results/calibration/_nyiso247_loading_shape.json` | G-C, both legs |
| `scripts/probes/nyiso247_gate_table.py` | G-D, the per-year delta table |
| `scripts/probes/nyiso247_compose_span.py` | the composer + this lane's delta assertion |
| `scripts/gen_nyiso247_attestation.py` | the arm's C6 attestation |
| `results/calibration/nyiso247_fuelinv_span` · run `2026-09-20-nyiso247-fuel-invariance-disarm` | the registered arm |
