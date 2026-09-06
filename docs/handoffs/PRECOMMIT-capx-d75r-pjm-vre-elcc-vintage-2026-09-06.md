# PRECOMMIT — capx D75-R: the PJM VRE ELCC delivery-year vintage axis

**Lane:** capx D75-R. Charter: pack §D75-R + `FINDING-capx-d75-2026-09-06.md`
(§1 the superseded ratings, §2 the missing operand, §3 the per-year table, §5 the 2025/26 gap,
§6 the routes, §8 the recommendation) + `PRECOMMIT-capx-d75-pjm-vre-elcc-vintage-2026-09-06.md` §6
(the pre-declared per-DY signs) + `FINDING-capx-d66-2026-09-06.md` §8 card B (the origin).
Branch `claude/capx-d75r-pjm-vre-elcc-kxto0z`, fresh off `origin/main` **0336ccd8**.
**DATA PROFILE: pjm.** MODEL: Opus (rule 27 `[R-PUSH]` — the card writes `src/market_sim/`).

**PUSHED BEFORE THE FIRST SOLVE.** Every number below is measured from committed artifacts, from
the code at this branch's HEAD, or from a primary PJM publication whose sha256 is recorded. No LP
has been run in this lane at the time of writing. Instrument:
`docs/handoffs/d75r/vre-elcc-vintage-phase0-2026-09-06.{py,json}`.

---

## 0. The three director rulings this lane executes, and what each closes

D75 built nothing: it measured card B's object by hand and STOPPED on an operand PJM does not
publish. The director's rulings of 2026-09-06 (r#47 §0ar.1) close all three open questions, and
this lane executes them without re-litigating any of them.

* **(R1) The fixed/tracking split** = D75 §8 option (1): carry PJM's **OWN published Table-5 mix**
  (12.01 % fixed) as a documented **cross-vintage reconciliation** under rule 14 `[R-ACCURATE]`'s
  misalignment exception — a published PJM number on the wrong vintage, **stated as such** in the
  code comment and here — with D75 §3's bracket recorded as its sensitivity. Option (2) (the
  EIA-860 `Fixed Tilt?` / `Single-Axis Tracking?` derivation) is a **separate data-intake card**,
  not this lane's. **NEVER** a split sized to the position residual, and **never** one backed out of
  PJM's cleared solar UCAP (rule 13 `[R-MEASURED]` — that would derive an input from the very
  outcome the census is compared against).
* **(R2) Scope** = **THREE delivery years**: 2023/24, 2024/25, 2025/26. **2022/23 and earlier are
  out of scope** — PJM's ELCC construct first applied to the 2023/2024 BRA, so earlier years carry
  no published class rating of any kind. Stated, and measured inert (§3).
* **(R3) The phase-0 gate is PER YEAR and on the SIGN** (DOWN in every in-scope year), never on a
  magnitude band. D75 §3's per-year table replaces the superseded band, which had been derived from
  a rating set PJM re-studied and is no longer operative.

## 1. What is built (STEP 2), fixed here before any measurement is graded against it

* **Gate:** a new **default-OFF** `ScenarioConfig.pjm_vre_accreditation_vintage`, resolved through
  `retirements.vre_accreditation_vintage_armed`, which requires **three** conditions: the field,
  **`pjm_accreditation_design_vintage` (D48's own gate)**, and a registry entry for the ISO.
* **Why a SECOND key, said plainly** (the charter asks for this if a second key is unavoidable, and
  it is). D48's key is **ARMED for PJM by owner ruling**, through `iso_configs.py::_pjm_config`'s
  `default_scenario_overrides` (2026-09-05, on the D57 A/B). Keying the VRE axis off it **alone**
  would arm this untested mechanism **by default** in every PJM forecast run the moment it landed —
  a default flip nobody ruled on, and one that would move the shipped `pjm-t1h` recipe key. The
  charter's rule-19 concern is met by the **composition** instead: requiring D48's gate makes the
  two reachable states the only two coherent ones — D48 alone is HEAD's posture (thermal +
  requirement devintaged, VRE not: exactly the defect card B names), and D48 + this gate is the
  fully-vintaged basis. **The VRE half can never be vintaged while the thermal half is not.**
* **Seam:** `resolve_renewable_vintage_credit` at **rung 0** of
  `resolve_renewable_capacity_credit`'s ladder, threaded on the **same** `config` /
  `accreditation_year` pair D48's thermal half already carries into
  `accredited_firm_capacity_mw` — so the CR-1 position, the reliability floor, the backstop, the
  D57 clearing stack's price-taking block and the ledger's `renewable_credits_applied` diagnostic
  all move together (rule 19 `[R-ONE-MECH]`), and no consumer can price one accreditation while
  another is counted.
* **Registry:** `RENEWABLE_ELCC_VINTAGE_RATINGS_BY_ISO["PJM"]`, keyed by the delivery-year label
  `resolve_delivery_year` builds — the same key D48's two halves use.
* **NO hold-last, at either edge.** Pre-ELCC years and every year from 2026/27 on fall **through**
  to the incumbent curve, which is digitized from precisely those later ratings and is the right
  basis there. Carrying a pre-reform class rating forward past the reform would rebuild the
  mixed-vintage error the axis removes.
* **ZERO scalar fields, ZERO free parameters beyond the ONE ruled reconciliation** (rules 5/21/24):
  every rating is a published PJM class rating reconciled **byte-for-byte** to
  `data/raw/capacity-market/elcc/pjm/pjm.csv` by test, and the fixed-tilt share is written as the
  arithmetic `1189/(1189+8713)` over the same committed rows, not as a rounded literal.
* **Cache key:** registered in `_CACHE_KEY_OPTIONAL_FIELDS` at `False`. Verified, not asserted: the
  default `ScenarioConfig().cache_key()` is **`547053bdfccd4264` on `origin/main` and
  `547053bdfccd4264` on this branch** — byte-identical. Coerced to the dataclass default in a plain
  backcast (a forecast-lane mechanism).
* **Scope (rule 25 `[R-ISO-SCOPE]`):** PJM-only by construction — the registry holds one ISO and the
  predicate requires an entry, so the flag armed on any other ISO's run cannot move a single MW.
  Locked by test across MISO / NYISO / NEISO / CAISO / ERCOT.

## 2. STEP 1 — the intake, which is a hard prerequisite and is already landed

`FINDING-capx-d75` §6 item 1, executed as commit `c6d1441e`: three new tranches in
`data/raw/capacity-market/elcc/pjm/pjm.csv`, each transcribed verbatim from the primary PJM
posting, with source doc + page + **sha256** per row; the Dec-2021 2024/25 tranche **relabelled**
PRELIMINARY/SUPERSEDED rather than replaced. All four documents were fetched in-session and their
hashes match the identities D75 recorded:

| document | sha256 (verified in-session) | what it gives |
|---|---|---|
| `elcc-class-ratings-for-2023-2024-bra.pdf` | `c50890fb…745f2f69` | DY 2023/24: wind 15 %, solar fixed 38 %, tracking 54 % |
| `elcc-class-ratings-for-2024-2025.pdf` | `f3fb54db…6a589fc94` | DY 2024/25 FINAL: 21 / 33 / 50 % |
| `elcc-report-december-2023.pdf` | `192ea596…a9152f53ea1f9` | Table 2 (report p.4, PDF p.7) + the *"only the 2024/2025 values are final"* language (report p.1, PDF p.4) |
| `2025-26-3ia-elcc-class-ratings.pdf` | `1d9d7e00…a05372983` | DY 2025/26: 38 / 10 / 14 %, and the thermal classes |

**Before this intake the repository's only 2024/25 rating set was the superseded one** — which is
why the intake had to precede the build, not follow it.

## 3. PHASE 0 (STEP 3) — zero LP, and it **PASSES** the ruled gate

Instrument: `docs/handoffs/d75r/vre-elcc-vintage-phase0-2026-09-06.{py,json}`. It calls the
**shipped code path** (`renewable_credits_applied` → `resolve_renewable_capacity_credit`) under a
control config and an armed one differing in exactly one field, on the D57 arm-A committed pools —
so what is gated is the mechanism as it will actually run, not a paper restatement of it.

**No `fleet_only` rebuild was needed, and the reason is measured rather than assumed:** every
arm-A ledger's own `fleet_by_fuel_after` carries **no wind or solar key in any year 2021-2025**, so
PJM's persistent fleet holds no VRE units, the penetration axis is the zonal pool alone, and
accredited VRE = pool × credit exactly. A rebuild could only reproduce that at the cost of minutes.

| DY | model yr | pools W / S (MW) | credit W / S: incumbent → vintaged | accredited VRE MW | **Δ MW** | gate |
|---|---:|---:|---|---:|---:|---|
| 2022/23 | 2022 | 10,153.9 / 4,549.8 | 0.41 / 0.1064 → *unchanged* | 4,647.198 → 4,647.198 | **0.000** | out of scope, **inert** |
| **2023/24** | 2023 | 10,153.9 / 4,549.8 | 0.41 / 0.1064 → **0.15 / 0.520788** | 4,647.198 → 3,892.565 | **−754.633** | **DOWN ✓** |
| **2024/25** | 2024 | 10,153.9 / 4,549.8 | 0.41 / 0.1064 → **0.21 / 0.479587** | 4,647.198 → 4,314.344 | **−332.854** | **DOWN ✓** |
| **2025/26** | 2025 | 11,653.9 / 6,990.4 | 0.41 / 0.1064 → **0.38 / 0.135197** | 5,521.878 → 5,373.563 | **−148.315** | **DOWN ✓** |
| | | | | **window total** | **−1,235.802** | **PASS** |

**The sign gate PASSES per year, which is the ruled test (R3).**

**INDEPENDENT CHECK — the built code against D75's hand arithmetic.** Two lanes, two constructions,
one number: the max absolute difference across the three in-scope years is **0.046 MW**, i.e. the
rounding of D75's published one-decimal figures (−754.6 / −332.9 / −148.3). A miss here would have
been a build defect, not a disagreement about PJM's ratings.

**A structural fact worth stating, because it is not a uniform derate.** The two classes move in
**opposite** directions: wind DOWN hard (−2,640.0 MW in 2023/24) and solar UP (+1,885.4 MW), because
PJM's pre-reform class-average solar ratings (38/54 %) are far **above** the post-reform marginal
ratings the incumbent curve carries (8/11 %). Net down. That is what a real vintage change did; a
mechanism that moved both classes the same way would be a derate wearing a vintage's clothes.

## 4. G-DRIFT / the control — **form 4 is VOID by measurement; a control is solved at HEAD**

The charter fixes this and the measurement confirms it rather than resting on it: the D57 arm-A
bundle was solved at `a30696a0` and carries key **`f0e050e820c1159a`**, while the SAME bare
`pjm-t1h` recipe resolved at this branch's HEAD keys **`15a723ba3b6dc856`**. The key itself has
moved, so the committed bundle is not this HEAD's control under any audit, and no hunk
classification can rescue it. **A matched cache key is not a G-DRIFT verdict, and an unmatched one
is dispositive the other way.** Same-HEAD controls are what D60-R4 / D67 / D74 / D78-R all bought;
this lane does the same.

The arm-A ledgers remain valid as a **read** of what the model accredited under the incumbent
registry — a read of committed artifacts, not a differencing of two solves — which is all §3 uses
them for.

## 5. Keys, resolved through the harness path BEFORE any solve

Resolution: `run_capacity_hindcast.build_config("PJM", …, vintage=2020, entry_screen_diagnostics=True)`
→ `apply_iso_scenario_defaults` → `cache_key()` — the D45-R / D48 / D57 known-answer path.

| leg | span | posture | **key** |
|---|---|---|---|
| screen control | 2021–2023 | bare `pjm-t1h` at HEAD (D48 ×2 + clearing armed by `_pjm_config`; VRE vintage OFF) | **`afda79ba04cbfdbf`** |
| **screen arm** | 2021–2023 | + `--pjm-vre-accreditation-vintage` | **`a998596db59e5ce7`** |
| full control | 2021–2025 | as above | **`15a723ba3b6dc856`** |
| **full arm** | 2021–2025 | + `--pjm-vre-accreditation-vintage` | **`33041553d7541538`** |

The two arm keys occur nowhere under `results/`, `frontend/`, `docs/`, `scripts/` or `src/` (grep at
this HEAD) — no collision with any committed bundle. The two control keys are the values the D78-R
lane independently resolved at HEAD (`docs/handoffs/d78/keys_probe.json`), which is a cross-lane
confirmation that the harness path is being driven the same way. **No committed bundle at either
control key is reused**: this lane solves its own controls (§4).

Recipe otherwise D45-R's, unchanged:
`run_capacity_hindcast.py --iso PJM --start-year 2021 --end-year <2023|2025> --vintage 2020
--fuel-variant realized --entry-screen-diagnostics [--pjm-vre-accreditation-vintage]`,
years sequential within a run, PJM solo (rule 12).

## 6. STEP 4 — the SCREEN (rule 29 `[R-SCREEN]`)

**Screen year = DY 2023/24 (model year 2023), named HERE before the screen runs.** It is the year
the mechanism's own measured footprint is **largest** (§3: −754.6 MW, more than double either other
year) — **never** the year with the biggest residual, which would make the choice a residual-driven
one. Span 2021–2023 so the screen year's history is byte-identical to the full window's through
2023.

**The gate is STRUCTURAL and it is a STOP gate only.** It may kill the arm; it may never promote
one; it is not read against the target residual. Four legs, all pre-declared:

1. **IDENTITY.** The solved arm's accredited VRE equals phase 0's arithmetic **to the MW**: the
   2023 screen must accredit wind at **0.15** and solar at **0.520788**, i.e. 3,892.565 MW against
   the control's 4,647.198 MW, and the ledger's `renewable_credit_applied` must read those two
   credits. A miss is a threading defect between the resolver and the screen.
2. **CONFINEMENT.** In the 2023 screen the **requirement** is byte-identical between arms (the
   mechanism touches supply only); the **thermal** accreditation is byte-identical (the D48 half is
   armed in BOTH arms and must not move); and **storage** firm MW is byte-identical.
3. **NO NON-TARGET LOAD-BEARING FLIP.** No load-bearing criterion outside the target flips
   PASS → FAIL.
4. **INERTNESS OUT OF SCOPE.** The 2022 screen (DY 2022/23) is byte-identical between arms — the
   pre-ELCC year the registry has no row for.

**Pre-declared expected direction for the screen year** (rule 14's sign, stated so it cannot be
written to fit): accredited VRE DOWN 754.6 MW ⇒ census position DOWN ≈ 0.47 pt (1.08814 → 1.08345)
⇒ capacity revenue UP or unchanged ⇒ PJM retirements **harder or unchanged** in 2023. Because
2023/24 is the one year where the model sits **above** the published position, the residual
**narrows** here (frame B −3.642 → −3.174 pt; frame A −3.293 → −2.825). That is the two-sided
signature of a basis repair, and it is **not** the reason to arm: had it moved the other way the
mechanism would be identical.

**Whether the position moves as arithmetic predicts is a DIAGNOSTIC, not the gate.** The screen's
census is the solve's own, so a second-order difference from the fixed-pool arithmetic is expected
wherever the arm's own decisions change the standing fleet — the channel D62's STOP 5 recorded.

## 7. STEP 5 — the full window, and what is reported

If the screen clears: one `--start-year 2021 --end-year 2025` invocation, ONE bundle, differenced
against the same-HEAD full control. Reported at **full magnitude on BOTH of D66 §1.2's frames**
(B = RPM + committed FRR over the RTO Reliability Requirement; A = RPM only over
`RelReq adj FRR + EE add-back`), plus FC-2 / FC-3, whatever they do.

Fixed-pool expectations, from §3, stated ex ante (the solve will differ where its own decisions
move the census — that difference is reported, not smoothed):

| DY | model pos before → after | gap B before → after (pt) | gap A before → after (pt) | |
|---|---|---:|---:|---|
| 2023/24 | 1.08814 → 1.08345 | −3.642 → **−3.174** | −3.293 → **−2.825** | **narrows** |
| 2024/25 | 1.03206 → 1.03007 | +2.188 → **+2.388** | +2.345 → **+2.544** | **widens** |
| 2025/26 | 0.96613 → 0.96513 | +4.379 → **+4.479** | +3.877 → **+3.976** | **widens** |

## 8. The pre-declared signs, carried VERBATIM from `PRECOMMIT-capx-d75` §6

Recorded there before any lane measured against them, and reproduced here **unaltered** so this
lane's grading cannot be written to fit:

> * **DOWN in all three in-scope delivery years, at every candidate mix**, and DY 2024/25's sign is
>   not mix-contingent at all (break-even fixed share −0.310, outside the admissible range).
> * Magnitudes at PJM's own published solar mix: **2023/24 −754.6**, **2024/25 −332.9**,
>   **2025/26 −148.3 MW**; window total **−1,235.8 MW** (bracket −2,803.0 … −1,021.9).
> * **The position residual WIDENS in 2024/25 and 2025/26** — the two years where the model's census
>   position sits *below* PJM's published — and **NARROWS in 2023/24**, where it sits above. Card B's
>   rule-14 point stands in the years the card is about.
> * The effect is roughly **half** what the charter pre-declared, and the whole of that difference is
>   the superseded rating set (§0(a)).

Measured in §3 above: **every one of them holds**, to 0.046 MW.

## 9. STOPs — this lane halts and routes rather than absorbing

1. **Phase 0 sign gate fails in any in-scope year** → the arm is killed, the remaining years are
   never spent, and the kill is the session's result. *(Not fired: §3 PASSES.)*
2. **Screen identity leg misses** (the solved accredited VRE ≠ phase 0's arithmetic to the MW) →
   a threading defect; diagnose before any full-window solve, never absorb.
3. **Screen confinement leg misses** (requirement / thermal / storage move between arms) → the
   mechanism is reaching beyond its declared footprint; stop and diagnose.
4. **The full window's position moves in a direction §7 does not predict, beyond the census channel
   §6 names** → report the miss at full magnitude and diagnose; do NOT re-tune anything.
5. **Anything would need a new scalar** → refused outright (rules 21/24). There is no offer adder,
   blend weight, haircut or per-class cap in this mechanism and none may be added.

## 10. What this lane does NOT do

* **Nothing arms.** The gate ships default-OFF; arming is an owner card on the measured A/B.
* **No board write, no registration, no keeper, no re-score.** D65-B-R is the sole board writer
  until its batch lands (charter collision note).
* **No fix to `evolution_2022.json`'s missing adequacy block** — D75 §6 item 3, **routed** (it
  forced this lane's DY 2023/24 pool reconstruction too, and the instrument says so in the row's
  own `provenance`).
* **No EIA-860 fixed/tracking derivation** — ruling R1 makes it a separate card.
* **No touch of the D78-R / D81 clearing path or the D67-ARM lane's `iso_configs._pjm_config`
  region** (charter collisions).
* **Screen and control bundles are DELETED before merge** (rule 29(c)): this document and the
  FINDING carry every number the lane will ever cite from them.
