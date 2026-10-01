# ADDENDUM 2 to PRECOMMIT — SCN-WS5A-POLICY-NYISO: the S15 bracketing leg, and the S16 shard fan-out

**Lane** SCN-WS5A-POLICY-NYISO (now a **COORDINATOR**) · **Model** Opus (`claude-opus-5`,
rule 27 `[R-PUSH]`) · **Date** 2026-09-07 · **Branch**
`claude/scn-ws5a-policy-nyiso-coord-cadsr0` · **Data profile** `nyiso` ·
**THE PIN** `bdfb3095e9fa0cd2bec3f4e843f320b42588c72b`, unmoved.

**PUSHED BEFORE THE FIRST CASE SOLVE** (rule 29 `[R-SCREEN]`). Zero of the nine surviving
policy legs have been solved. The only two entries under
`results/scn-campaign-policy-2026-09-06/NYISO/` are `REF` and `LOAD-HI` — the parent §8
**rematerializations**, which are **CONTROLS, not cases**, and which **PASSED gate G13** (§1
below). Every number in this addendum is zero-LP: a resolved config at THE PIN, a committed
artifact, or arithmetic on the two.

**Nothing in the parent PRECOMMIT or ADDENDUM 1 is revised.** Phase 0 stands; the four kills
stand on their proven identity; the eleven committed cache keys stand and are **re-verified
here, all eleven, byte-for-byte** (§2); gates G1–G13 stand; predictions P-1 … P-19 stand. This
addendum **adds**: the G13 result, one new case (`CES-P60`) with its key and its own gates
G-B1–G-B3 and predictions P-20 … P-22, the S15 threshold measurement that motivates it, and
the S16 shard partition.

---

## 0. Bottom line, before any case LP

1. **G13 PASSED, both control legs, in this container.** `REF` at key `f10cc93084b4c0db` and
   `LOAD-HI` at `c2ceaefa4afafcda` reproduce their committed `full_horizon_summary.json`
   trajectories **exactly**. The pin is reproducible; the lane proceeds (§1).
2. **THE S15 MASK IS TOTAL, AND IT IS MEASURED, NOT ARGUED.** NYISO's RPS row is at its
   Alternative Compliance Payment ceiling — `rps_dual = 40.0000` — in **all five years of the
   committed REF**, and `STATE_RPS_ACP["NYISO"] = 40.0`. The entry fold is
   `attr = max(EAC, rps_credit_for_zone, clean_credit)` with **no fuel gate**, so a CES premium
   below $40 adds **exactly nothing** to entry revenue. Measured at THE PIN: `attr` is
   **40.00 $/MWh in REF and in CES-P10, CES-P20 and CES-P30 alike**, for both eligible techs,
   in all five NYISO zones, in all five years — **15/15 ladder leg-years masked, 150/150
   tech-zone-years identical to REF** (§3).
3. **THE BRACKET CLEARS, WITH ROOM.** `CES-P60` — premium $60, **one common level for every
   ISO**, above the footprint's highest published ACP ($50), identified from published ACPs and
   **never from a residual** — lifts the entry fold to **60.00 $/MWh**, i.e.
   **+20.00 $/MWh strictly above REF's in every one of the 50 eligible tech-zone-years**.
   **Gate G-B1 PASSES pre-solve** (§4). Key **`c3013cc6087bd2aa`**.
4. **The ladder is nevertheless NOT inert, and that is the fuel gate, not the premium.** The
   *retirement/retrofit* leg IS fuel-gated — `rps_for_unit = rps_credit_for_zone(...) if
   g.fuel_type in _RPS_ELIGIBLE_FUELS else 0.0`, and `_RPS_ELIGIBLE_FUELS = {"wind", "solar"}`
   — so a `gas_cc_ccs` unit earns **0** from the RPS row and the premium × 0.95 ($9.50 /
   $19.00 / $28.50) is its **sole** attribute price there. The parent P-4 already named the CCS
   retrofit screen as the ladder's dominant channel; §3.3 now says **why** that is the *only*
   channel with an attribute term in it, which sharpens P-4 into a falsifiable split (§5).
5. **REF's leakage line is closed for all five years, with zero LP.** The parent §6.1 left
   2028–2030 blank rather than fill them from a pre-D77 bundle. The committed
   `results/scn-campaign-load-2026-09-06/NYISO/report/nyiso_headline_deltas.csv` is built
   against the **re-solved** keys (its `bundle/meta.json` names `REF: f10cc93084b4c0db`) and
   carries `import_co2_mt_reported` for every year (§6). **No REF bundle and no REF re-solve is
   needed anywhere in this lane** — which is what lets S16's rule "a shard never solves REF"
   hold without dropping the charter's leakage duty.

---

## 1. Gate G13 — RESULT: **PASS**, both control legs

Parent §6.2 P-1 / gate G13, scored as written ("a hit only on an exact match").

| leg | key | `co2_mt` 2026–2030 | `lw_price` 2026–2030 | verdict |
|---|---|---|---|---|
| `REF` | `f10cc93084b4c0db` | 23.6923 · 24.5911 · 17.1630 · 13.7082 · 10.9030 | 50.193 · 49.184 · 50.921 · 49.276 · 54.953 | **exact — PASS** |
| `LOAD-HI` | `c2ceaefa4afafcda` | 25.3838 · 27.0653 · 20.2714 · 15.9861 · 14.0200 | 51.418 · 51.203 · 52.925 · 51.673 · 58.321 | **exact — PASS** |

Both carry 14/14 invariants, `unserved_mwh` 0.0 and 5/5 solved years; wall 1,461.9 s / 1,544.0 s,
peak RSS 3,501.3 / 3,868.9 MB. **These two are CONTROLS, not cases** — neither is registered
(parent §8: both ids already exist under `scn-campaign-load-2026-09-06`), and neither is
re-solved again by this lane or by any shard.

## 2. Every case at THE PIN — the eleven committed keys re-verified, plus `CES-P60`

Resolved through the identical chain the parent used (`matrix_configs` → `resolve_policy_bundle`
→ `set_caiso_fsno_partition(False)` → `apply_iso_scenario_defaults` → `cache_key()`), at THE
PIN's own code. Instrument + committed output:
`docs/handoffs/scn-ws5a-policy-nyiso/keys-at-pin-2026-09-07.{py,txt}`.

| case | key at THE PIN | status | shard |
|---|---|---|---|
| `REF` | `f10cc93084b4c0db` | **re-verified** — control, solved, never registered | — |
| `LOAD-HI` | `c2ceaefa4afafcda` | **re-verified** — control, solved, never registered | — |
| `CES-P10` | `3c96d694c18e5547` | **re-verified** — SOLVE | **A** |
| `CES-P20` | `9da7c76372c98406` | **re-verified** — SOLVE | **A** |
| `CES-P30` | `89a70dd1140c6731` | **re-verified** — SOLVE | **B** |
| **`CES-P60`** | **`c3013cc6087bd2aa`** | **NEW — SOLVE (S15 bracket)** | **B** |
| `CES-T80` | `eb1b0e1df942db47` | **re-verified** — SOLVE | **C** |
| `ALL-CLEAN` | `e13b0d801b1ffce1` | **re-verified** — SOLVE | **C** |
| `VOL-MID` | `9528d708b81b5074` | **re-verified** — SOLVE | **D** |
| `VOL-HI` | `893acae55a1a898f` | **re-verified** — SOLVE | **D** |
| `CES-P20+VOL-HI` | `566335c8ca37dc17` | **re-verified** — SOLVE | **E** |
| `CAP-STATE-TIGHT` | `76c60ac152400146` | **re-verified** — SOLVE | **E** |
| `CARB-LO` / `CARB-MID` / `CARB-HI` / `CARB-MID+LOAD-HI` | `68294f45fda64aed` / `91d435c848c57fb6` / `3608ca88c0a19d4e` / `80b8a2ec7406f75d` | **KILLED, parent §4.2 — not revisited** | — |

**Ten legs to solve, 50 solve-years.** Every key is distinct; none has ever been occupied.

### 2.1 How `CES-P60` is constructed — the registered `--set` channel, and the exact field diff

`CES-P60` is **not** a new matrix case and **the matrix YAML is not edited** (parent §10:
`configs/scenario_campaign_matrix.yaml` is consumed, never edited). It is the committed
`--set FIELD=VALUE` channel that `run_ces_leg.py` already carries — applied **after** the
ladder's case overrides so the command line is the last word, and **recorded in the leg's
summary and its `run_config.json`** (`run_ces_leg.run_leg` docstring), hence in the run's
sidecar `meta.set_overrides`. It is a registry-visible tunable, not an off-registry knob
(rule 24 `[R-REGISTRY]`).

```
--case CES-P30 --set federal_ces_premium_usd_per_mwh=60.0
```

Verified by a **full `dataclasses.fields` diff** of the two resolved configs, not by
inspection:

* `CES-P60` **vs `REF`** → `{federal_ces_enabled: False→True,
  federal_ces_premium_usd_per_mwh: 0.0→60.0}` — **exactly the two fields the `CES-P*` legs
  set**, which is what ruling S15 specifies.
* `CES-P60` **vs `CES-P30`** → `{federal_ces_premium_usd_per_mwh: 30.0→60.0}` — the single
  field, nothing else.

**Why $60 and why it is not a fitted number.** $60 is **one common level for every ISO in the
footprint**, chosen to sit above the highest **published** ACP anywhere in it ($50 — CAISO and
NEISO, `STATE_RPS_ACP`), and it is deliberately **not** per-ISO. A level picked to clear
NYISO's own $40 would be exactly the per-ISO fitting rule 25 `[R-ISO-SCOPE]` forbids, and a
level picked because it moved a residual would be the fitted-mechanism selection rule 1
`[R-STRUCT]` and rule 29's screen gate both forbid. Its identification source is the published
ACP table; **DOF ledger: still zero free parameters** — $60 is a scenario axis level, not an
identified parameter, and it is declared here, ex ante, and never swept.

---

## 3. S15 STEP 1 — the mask, measured per year (zero LP)

Instrument + committed output:
`docs/handoffs/scn-ws5a-policy-nyiso/s15-entry-fold-2026-09-07.{py,txt}`.

### 3.1 The fold, quoted from THE PIN

`model/capacity_evolution/new_entry.py` (the entry screen, `_zone_revenue`):

```python
attr = max(
    effective_eac_price_for_tech(config, tech, year),      # = premium x credit fraction
    rps_credit_for_zone(rps_shadow_price, zi),             # NO fuel gate here
    _clean_credit_for_tech(tech, iso_config, zone_names,
                           clean_attribute_price_by_fuel, zone_override=zname),
)
```

`model/capacity_evolution/retirements.py` (the retirement/retrofit screen) — the **contrast**:

```python
rps_for_unit = (
    rps_credit_for_zone(rps_shadow_price, zone)
    if g.fuel_type in _RPS_ELIGIBLE_FUELS       # frozenset({"wind", "solar"})
    else 0.0
)
```

### 3.2 The per-year answer S15 asks for

**REF's `rps_dual`, from the committed REF bundle's own trajectory** — not re-derived:

| | 2026 | 2027 | 2028 | 2029 | 2030 |
|---|---|---|---|---|---|
| REF `rps_dual` ($/MWh) | **40.0000** | **40.0000** | **40.0000** | **40.0000** | **40.0000** |
| `STATE_RPS_ACP["NYISO"]` | 40.0 | 40.0 | 40.0 | 40.0 | 40.0 |
| row state | **escape (at the ACP ceiling)** | escape | escape | escape | escape |

**Does it sit ≥ the CES dual each ladder leg carries? YES, in all five years, for all three legs:**

| leg | CES dual it carries | 2026 | 2027 | 2028 | 2029 | 2030 |
|---|---|---|---|---|---|---|
| `CES-P10` | $10 | **MASKED** | MASKED | MASKED | MASKED | MASKED |
| `CES-P20` | $20 | **MASKED** | MASKED | MASKED | MASKED | MASKED |
| `CES-P30` | $30 | **MASKED** | MASKED | MASKED | MASKED | MASKED |
| `CES-P60` | $60 | **LIVE** | LIVE | LIVE | LIVE | LIVE |

The resolved fold, measured (identical in all five zones — the RPS dual resolves as a scalar,
so `rps_credit_for_zone` returns the same 40.0 at every zone index):

| case | EAC leg (wind & solar) | **`attr` = the fold** | Δ vs REF |
|---|---|---|---|
| `REF` | 0.00 | **40.00** | — |
| `CES-P10` | 10.00 | **40.00** | **0.00** |
| `CES-P20` | 20.00 | **40.00** | **0.00** |
| `CES-P30` | 30.00 | **40.00** | **0.00** |
| **`CES-P60`** | **60.00** | **60.00** | **+20.00** |

All values are constant across 2026–2030 and across all five zones, so the table above is the
whole 5-year × 5-zone × 2-tech surface.

### 3.3 What this does and does not say — stated before the solve

It says the **entry** screen cannot distinguish `CES-P10`, `CES-P20` or `CES-P30` from `REF`
**through the attribute term**. It does **not** say the ladder is inert, and the three legs are
correctly still solved, because two other channels carry the premium and neither is masked:

* **the retirement / CCS-retrofit screen**, whose RPS leg is fuel-gated to `{wind, solar}` — a
  `gas_cc_ccs` unit's RPS credit is **0**, so its attribute price is the premium × 0.95 alone
  ($9.50 / $19.00 / $28.50), with nothing to mask it. This is the parent P-4 channel;
* **dispatch**, through `apply_eac_to_mc`, where the parent §1.1 already measured every
  `eac_price_*` as `None` so the premium *is* the effective EAC.

A residual entry response in the ladder can therefore only arrive through the **energy-price**
term of `_zone_revenue`, never the attribute term — which is the falsifiable split §5 registers.

`CES-T80` is unaffected by the mask and needs no bracket: it carries an **ACP of $50** into
`clean_attribute_price_by_fuel`, so its entry fold is `max(0, 40, 50) = 50.00 > 40.00` — live
in every year, **conditional on gate G4's pre-registered `dual = $50.0000 exactly`**. That is
why S15 adds exactly one leg and not two.

---

## 4. S15 STEP 2 — gate **G-B1**, computed BEFORE the solve

> **G-B1.** At a $60 premium, `attr` strictly exceeds REF's for at least one eligible
> tech-zone-year.

**Arithmetic:** `attr(CES-P60) = max(60.00, 40.00, 0.00) = 60.00`;
`attr(REF) = max(0.00, 40.00, 0.00) = 40.00`; **Δ = +20.00 $/MWh**, in `{wind, solar}` ×
`{Upstate_West, Capital_Hudson, Lower_Hudson, NYC, Long_Island}` × `{2026…2030}` =
**50 of 50 eligible tech-zone-years**.

**G-B1 CLEARS.** The leg is authorized to solve. (Had it not cleared, the parent lane would
have STOPPED and routed rather than solving — the gate is a STOP gate and may never promote.)

### 4.1 The two further bracket gates, defined here, structural and STOP-only

> **G-B2 — bracket footprint confinement.** `CES-P60` moves eligible-class rows, the thermal
> rows they displace, the CCS-retrofit ledger and the entry ledger — nothing else — **and
> REF's RPS row dual stays at $40.0000 in every year**. A moved `rps_dual` is the **STOP**: it
> would mean the premium is reaching the RPS *row* rather than outbidding it inside the fold,
> which is not what §3 measured and not what the bracket claims.

> **G-B3 — bracket monotonicity, as a DIRECTION.** `|ΔCO2|` and `Δclean_share` at $60 are at
> least as large as at $30 in every year, and `builds_renew_mw` at $60 is ≥ `CES-P30`'s in
> every year. **A REVERSAL is the STOP** — a strictly higher attribute price buying strictly
> less clean deployment would falsify the fold as the channel. **A NULL IS NOT A FAILURE:**
> per ruling S15, *a leg that clears G-B1 and still shows no entry response is a REPORTABLE
> FINDING, not a gate failure*. If `CES-P60`'s `builds_renew_mw` equals `CES-P30`'s, G-B3
> passes on its degenerate leg and the null is reported **at full magnitude** in the FINDING as
> evidence against the entry fold's elasticity — never explained away, and never used to
> re-tune anything.

No bracket gate reads a target residual (rules 1 / 29).

### 4.2 Predictions for the bracket — pre-registered, scored as written

**P-20.** `CES-P60`'s `builds_renew_mw` **exceeds REF's in at least one year of 2027–2030**,
and exceeds `CES-P30`'s in at least one year. Mechanism: a **+20.00 $/MWh** attribute uplift
applied to `attr × cf_mean × 8760` in `_zone_revenue` — for a NYISO wind site at
`cf_mean ≈ 0.30` that is ≈ **+$52.6 k/MW-yr** of screened revenue, which is not a rounding term
against a ~$50/MWh energy price.
**P-21 — the falsifiable split §3.3 sets up.** `CES-P10/P20/P30`'s Δ`builds_renew_mw` vs REF
arrives through the **energy-price term alone**, so I predict it is **small and NON-monotone in
the premium**, while `CES-P60`'s is **monotone-positive** through the attribute term. A
*monotone* renewable-build ladder across P10→P20→P30 would falsify §3.2's masking arithmetic
and is a finding against **this addendum**, reported as such.
**P-22.** `CES-P60`'s ΔCO2 is **more negative than `CES-P30`'s in every year**: its retrofit
credit is **$57.00/MWh** (0.95 × 60) against P30's $28.50, on the elastic `gas_cc_ccs` margin
the parent P-4 named, *and* it is the only ladder leg with a live entry term.

---

## 5. The REF control side, closed for all five years — zero LP

Source: `results/scn-campaign-load-2026-09-06/NYISO/report/nyiso_headline_deltas.csv`,
committed at `86062a0a`, built against `bundle/meta.json`'s `REF: f10cc93084b4c0db` — i.e.
the **re-solved, post-D77** REF, not the pre-fix one. This **supersedes the parent §6.1's two
blank cells** without a single solve-year, and it is the anchor every shard and the FINDING
difference against.

| year | `emissions_mt` | **`import_co2_mt_reported`** | import / in-ISO | `clean_share` | `avg_price` | `peak_price` | `curtailment_twh` | `neg_price_hours` | `gen_twh` | `unserved_mwh` | `backstop_mw` |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026 | 23.6923 | **10.4548** | **44.1 %** | 0.3924 | 49.24 | 68.97 | 0.0 | 0 | 154.1237 | 0.0 | 0 |
| 2027 | 24.5911 | **10.1556** | **41.3 %** | 0.3879 | 48.28 | 67.01 | 0.0 | 0 | 155.9434 | 0.0 | 0 |
| 2028 | 17.1630 | **10.5393** | **61.4 %** | 0.5205 | 50.02 | 69.39 | 0.0 | 0 | 157.7805 | 0.0 | 0 |
| 2029 | 13.7082 | **9.8112** | **71.6 %** | 0.5863 | 48.19 | 72.40 | 0.0 | 0 | 159.6652 | 0.0 | 0 |
| 2030 | 10.9030 | **11.0746** | **101.6 %** | 0.6227 | 53.78 | 80.83 | 0.0 | 0 | 161.5534 | 0.0 | 0 |

**The leakage caveat is WORSE than the parent stated, and it is disclosed, not discounted.**
Parent gate G2 recorded imports at "≈41 % of scored in-ISO CO2" from the two years it could
see. Measured across all five: **44 % → 102 %**. The ratio climbs because D77 + D65-B cut the
*in-ISO* denominator (23.69 → 10.90 Mt) while the import line is flat at 9.8–11.1 Mt. **By 2030
NYISO's imported CO2 exceeds its own.** Every CO2 number this lane reports carries its
`import_co2_mt_reported` beside it (charter duty; parent G2), and no CO2 delta is quoted
without it. Routed to SCN-DESK as §8 item 3.

**G8's object is re-confirmed dead on the re-solved REF:** `curtailment_twh = 0.0` in all five
years. Parent §3.4 / gate G8 stands unchanged, in its degenerate form.

---

## 6. S16 — THE SHARD PARTITION: **five shards, two legs each**

**Owner ruling S16, verbatim:** *"the per iso session should launch shards itself"* +
*"target <1 hr of lp solve per session."*

NYISO measures **4.06 min/solve-year** (Stage A-LOAD synthesis §8), so one 5-year leg is
**≈20 min** and a **2-leg shard is ≈40 min of LP** — inside the <1 h target with margin for the
heavier `ALL-CLEAN` (DC-high) leg. Ten legs ⇒ **five shards**, launched **all at once** via
`mcp__Claude_Code_Remote__create_session`.

| shard | legs | keys | LP | grouped by |
|---|---|---|---|---|
| **A** | `CES-P10`, `CES-P20` | `3c96d694c18e5547`, `9da7c76372c98406` | ~40 min | the masked ladder, lower rungs |
| **B** | `CES-P30`, **`CES-P60`** | `89a70dd1140c6731`, **`c3013cc6087bd2aa`** | ~40 min | **the bracket pair** — the two arms G-B3 differences are in ONE container |
| **C** | `CES-T80`, `ALL-CLEAN` | `eb1b0e1df942db47`, `e13b0d801b1ffce1` | ~45 min | the two **target-row** legs (both carry the $50 ACP row) |
| **D** | `VOL-MID`, `VOL-HI` | `9528d708b81b5074`, `893acae55a1a898f` | ~40 min | the voluntary axis, both WTP ceilings |
| **E** | `CES-P20+VOL-HI`, `CAP-STATE-TIGHT` | `566335c8ca37dc17`, `76c60ac152400146` | ~40 min | the combined leg + the cap row |

Grouping is by **mechanism**, so each shard's pair is the pair a gate actually differences —
most sharply in **B**, where G-B3 compares $30 against $60 and both are solved on the same box,
at the same pin, with the same rebuilt `data/clean`.

### 6.1 The division of labour, and what a shard may never do

A shard does **solve → register → declare**, and nothing else. It **writes no docs, scores no
gates, draws no conclusions, and makes no decisions** — phase 0, the case set, the keys, the
kills and the gates are committed and belong to this coordinator. It never solves `REF`,
`LOAD-HI`, `LOAD-HI-ORGANIC`, any case outside its own two, or any year past 2030; it never
edits `src/`, `configs/`, `scripts/`, `.github/`, the PRECOMMIT, the matrix, the plan or the
desk ledger; it never creates a CI workflow, moves a default, adds a `ScenarioConfig` field,
re-runs phase 0, or parallelises years.

**Rule 12 `[R-PARALLEL]`, as it applies here.** Its ~2-concurrent cap is a **per-container
memory** property (the charter's own sizing note is about one shared 15 GB box); five shards
are five separate containers with five separate allowances, so the cap does not compose across
them — this is the same reading ADDENDUM 1 §3 recorded for the four-container fan-out, now
standardised by ruling S16. **The within-invocation half is untouched and is honoured without
exception in every shard: one LP at a time, YEARS ALWAYS SEQUENTIAL.**

### 6.2 Why no shard solves `REF` — and how the charter's delta duty is still met

ADDENDUM 1 §3.2 had every group re-solve `REF` because `report_scenario_deltas.py` reads each
case's **cached bundle**. That is now **unnecessary and is dropped**, saving ~25 min of LP per
shard (≈2 h across the fan-out):

* the **absolute** columns of `report_scenario_deltas` — `import_co2_mt_reported`,
  `curtailment_twh`, `clean_share`, `avg_price`, by-fuel, by-zone, evolution — are built by
  `collect_case_year_frames` **per case, from that case's own parquets**, before any
  differencing (`add_reference_deltas` is a separate step). A shard can therefore emit its own
  two cases' absolutes with **no `REF` bundle in its container at all**;
* **`REF`'s absolutes are already committed** (§5), for all five years, against the
  re-solved key. The differencing happens **here**, at the coordinator, on committed numbers.

Each shard emits its cases' absolute frames into `…/<CASE>/report/` on a best-effort basis
(the registration is the load-bearing deliverable; if the extraction errors the shard reports
the error and proceeds). G13 is unaffected — it is a **control-leg** gate, already **PASSED**
in §1, and ADDENDUM 1 §3.2's four-container replication reading lapses with the REF re-solves
it described.

### 6.3 Registration — one seam, unchanged

Each shard registers its own legs (kind `scenario`, campaign `scn-campaign-policy-2026-09-06`,
run id `nyiso-2026-2030-scn-campaign-policy-2026-09-06-<slug>`, label
`scn-campaign-policy-2026-09-06-<slug>`, `reference_case: REF`) and **declares any invariant
FAIL in `frontend/data/hindcast/invariant-failures.json` in the SAME commit** — the Y-24
ratchet at the registration seam. The audit is **EXIT 0** on `main`; no undeclared run is added,
and no line is added for a run that passes 14/14 (a stale declaration fails the checker too).

Slugs, fixed here so no shard invents one: `ces-p10`, `ces-p20`, `ces-p30`, **`ces-p60`**,
`ces-t80`, `all-clean`, `vol-mid`, `vol-hi`, **`ces-p20-vol-hi`**, `cap-state-tight`.

For `CES-P60` the shard passes `"case": "CES-P60"` in `--extra-meta`; the summary's own `case`
field will read `CES-P30` because the leg is the `--set` construction of §2.1, and the sidecar's
`meta.set_overrides` records `federal_ces_premium_usd_per_mwh=60.0` — the run is self-describing
either way, and the FINDING states the construction.

---

## 7. Carried forward to the FINDING — the NYISO ↔ NEISO bracket on the voluntary axis

The parent §3.2 recorded NYISO as **"the structural inverse"** of the ERCOT voluntary reading.
It is also, and more usefully, **the structural inverse of NEISO** on the *volume* limb, and the
FINDING will carry it as the cross-ISO reading it is rather than as a per-ISO curiosity:

* **NEISO** measured a **byte-identical `VOL-HI` / `VOL-MID` pair** — it is a **zero-`E_DC`**
  ISO, so `V = s_base·w_ISO·E_nonDC + f_commit·E_DC` loses its second term entirely and the
  `mid`→`high` step (which moves **only** `f_commit`, 0.5 → 1.0, both paths sharing
  `s_base = 0.08`) moves **nothing**;
* **NYISO** has a real, large and *growing* `E_DC` (3.641 → 12.777 TWh at DC-mid; 5.443 →
  19.114 at DC-high), so the same `f_commit` step is the whole difference between
  **V = 13.86 → 18.29** and **15.68 → 24.68 TWh**.

The two ISOs therefore **bracket the `f_commit` axis**: one where the parameter is provably
inert by construction, one where it is the dominant term. That is a far stronger statement
about ruling S9's `VOLUNTARY_COMMITTED_DC_FRACTION` cell than either ISO makes alone, and it is
routed to open card **D-3c** beside the parent §9 item 2 (which brackets the *eligibility*
convention from the opposite tail to ERCOT's). Neither reading is a level transfer across ISOs
(rule 25 `[R-ISO-SCOPE]`): each ISO's numbers stay its own, and only the *axis behaviour* is
compared.

---

## 8. Routed to SCN-DESK — not executed, outside this lane's regions

Parent §9 items 1–4 stand. Added:

5. **The S15 mask is a FOOTPRINT-WIDE question, not a NYISO one.** The entry fold has no fuel
   gate while the retirement fold does, so on **any** ISO whose RPS row sits at its ACP, a CES
   premium below that ACP is invisible to the entry screen. `STATE_RPS_ACP` reads CAISO 50,
   NEISO 50, PJM 45, NYISO 40, MISO 30 — so the chartered ladder {10, 20, 30} is **entirely
   below every one of them**, and is at or above only MISO's $30 at its top rung. The five
   other policy lanes should each run S15 step 1 against their own REF's `rps_dual` before
   reading a null entry response as a CES result. **The asymmetry between the two folds is
   itself worth an owner look** — it is not obviously a defect (an RPS REC and a CES credit
   are one certificate sold once, which is the house no-stack doctrine), but the *entry* screen
   crediting a wind build at the RPS dual while the *retirement* screen credits the same fuel
   only inside `{wind, solar}` and gives `gas_cc_ccs` zero is a seam worth stating out loud.
6. **REF's import CO2 exceeds its in-ISO CO2 by 2030 (101.6 %).** Beyond the disclosure duty,
   this says the campaign's NYISO CO2 deltas are measuring roughly half of the emissions the
   ISO's consumption is responsible for. Carries to the leakage card with a hard number.
7. **ADDENDUM 1 §3.2's "four-container G13 replication" lapses**, because no shard now solves
   `REF`. G13 is PASSED on the two control legs in one container (§1); the replication reading
   should not be quoted from ADDENDUM 1 as if it had happened.

## 9. Duties — unchanged

* **No default moved, no knob moved, no `ScenarioConfig` field added.** **DOF ledger: ZERO free
  parameters** — `CES-P60`'s $60 is a scenario axis level identified from the published ACP
  table, declared ex ante, common to every ISO, and never swept against a gate.
* No `authorized_price_tuning` block (a backcast offer-curve channel; untouched).
* Backcast byte-identity: untouched by construction — every leg is `mode="forecast"`.
* Rule 29(c): this lane produces **no screen bundle and no control bundle**. `REF` and
  `LOAD-HI` are **rematerializations of committed, registered configs**, not screens or
  controls in rule 29's bundle-retention sense, and neither is registered.
* Rule 27: no existing source file ≥300 lines is rewritten; every push touching one is verified
  by fetch-back.
