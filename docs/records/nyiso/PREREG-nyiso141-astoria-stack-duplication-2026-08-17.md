# PRE-REGISTRATION nyiso-141 — the Astoria stack-duplication correction

**Written BEFORE any solve**, per the nyiso-141 binding discipline. Identification
is complete and independent of this A/B: see
`FINDING-nyiso141-astoria-stack-duplication-2026-08-17.md`. Nothing below can
retract the correction — it is a rule 14 `[R-ACCURATE]` data-correctness fix
justified by the measurement's own internal contradiction and by an independent
metered source (EIA-923), and under rule 1 `[R-STRUCT]` it stands whatever the
residual does. The A/B exists to **measure and disclose** the fix's effect, not
to adjudicate whether it is kept.

---

## 1. THE ARM

`2026-08-17-nyiso-141-astoria-stackdup` — the nyiso-140 keeper recipe, unchanged,
against a corrected CAMPD intake. Control: `2026-08-17-nyiso-141-control`, the
same recipe replayed at HEAD.

**There is no `ScenarioConfig` field and no flag.** The correction is a
row-identity fix inside the data layer (`campd.CAMPD_STACK_DUPLICATE_UNITS`), so
control and arm differ by **commit, not by config**. This is a deliberate
departure from the usual K1 shape and is stated up front:

* **K1 (config isolation) is inapplicable as normally written** — `run_config.json`
  will be IDENTICAL between the two runs, because no tunable moved. K1 is
  therefore replaced by a **diff-scope check**: the only source difference
  between control and arm commits is the stack-duplicate table and its two
  call sites, verified by `git diff --stat`.

## 2. WHAT MOVES, AND WHY — mechanism stated before the numbers

Two channels change, in opposite directions for the residual:

1. **The BENCHMARK falls in 2025 only.** `_backfill_eia923_with_campd` fired for
   Astoria in 2025 (EIA-923 has not published it), so the scored ST_GAS actual
   carries the doubled 2.672 TWh. Corrected, it becomes ~1.359. 2023 and 2024
   used metered EIA-923 and do not move.
2. **Astoria's marginal cost RISES.** Its unit-level CEMS CO₂ intensity doubles
   (279–322 → ~560–585 kg/MWh), which under RGGI raises its offer by roughly
   $6/MWh. It should therefore dispatch **less**.

Both push 2025 ST_GAS **model output down and the target down**.

## 3. EX-ANTE PREDICTIONS — stated even where unflattering

| # | prediction | direction |
|---|---|---|
| P1 | 2025 ST_GAS **benchmark** falls by ≈1.31 TWh (Astoria 2.672 → ~1.359). | high confidence — arithmetic, not behaviour |
| P2 | 2023 / 2024 ST_GAS benchmarks are **unchanged** (EIA-923 present, no backfill). | high confidence |
| P3 | Model ST_GAS **falls slightly in all three years** as Astoria's carbon-adjusted offer rises. Expected small: Astoria is ~1.3 TWh of a ~12 TWh class, and it is well inside the money in most hours. | moderate |
| P4 | **2025 |error| improves** (−3.737 → roughly −2.4), because the target falls ~1.31 while the model falls only slightly. | moderate |
| P5 | **2023 |error| gets WORSE** (+2.263 → slightly larger is possible only via P3's small model fall, so more likely marginally BETTER; the benchmark does not move). Stated explicitly: 2023's over-production is **not** addressed by this fix and I predict it stays ≈ +2.2. | moderate |
| P6 | System LMP moves negligibly (< 0.3 $/MWh mean, any year). One ~1.3 TWh plant repricing by ~$6/MWh is rarely marginal ISO-wide. | moderate |
| P7 | **CO₂ metrics for NYISO rise** — the class emission total was understated by construction. This is a REPORTED-ONLY stream (C5a, demoted at rubric v2.9) and gates nothing. | high confidence |

**The honest headline prediction:** most of the 2025 improvement comes from the
**target moving**, not the model improving. I expect the model's own ST_GAS to be
nearly unchanged. That is a weaker claim than "the fix closes the residual", and
it is the claim I am pre-committing to.

## 4. KILL GATES

Because the correction is not a mechanism, no gate can reject it — a gate can
only reveal that the *implementation* is wrong. Each is therefore a
**correctness** check with a defined failure action:

| gate | pass condition | if it fails |
|---|---|---|
| **K1′** diff scope | source diff = the stack-duplicate table + its two call sites only; `run_config.json` byte-identical between runs | implementation error — fix, do not proceed |
| **K2** feasibility | slack and dump identically 0.0, both runs, all three years | implementation error |
| **K3** liveness | Astoria's benchmark entry falls 2.672 → ~1.359 in 2025 and is unchanged in 2023/24; its unit CO₂ rates land in 520–600 kg/MWh | the fix did not reach the artifacts |
| **K4** scope | no NON-NYISO ISO's committed artifacts change; no plant other than 8906 moves | rule 25 breach — revert and re-scope |
| **K5** gated-criterion regression | no criterion goes PASS → FAIL on the arm | **does not kill the fix.** A regression is a DISCOVERED BUG under rule 14, to be root-caused, exactly as nyiso-140's worse fit was |
| **K6′** provenance + shape | no D-2 mechanism's forced share rises without clearing D-4 and D-1 | as K5 — reported, not fatal |

**K5/K6′ are explicitly declawed here and that is deliberate.** nyiso-140 is the
precedent: a structurally correct change was promoted *with a worse fit*. A
correction to a measurement cannot be vetoed by the score computed from that
measurement.

## 5. ADVERSE CASES I WILL REPORT IF THEY OCCUR

* Model ST_GAS falls by **more** than the benchmark does, so 2025 |error| gets
  *worse* — possible if Astoria is marginal more often than I expect. Would mean
  the model's downstate steam under-production is **larger** than the −2.4 TWh
  §6 of the finding estimates, not smaller.
* 2023 or 2024 benchmarks move at all — would mean the backfill fires in a year
  the sidecars say it does not, and P2 is wrong.
* Any non-NYISO artifact changes — a rule 25 breach that stops the session.
* CO₂ metrics move enough to flip C5a's reported number materially — reported,
  not gated, but must be disclosed since it is a benchmark change.

## 6. WHAT THIS A/B CANNOT SETTLE

It cannot close the successor object. After the correction, ≈ −2.4 TWh of 2025
ST_GAS under-production, the +2.26 TWh 2023 over-production, and the
CC-for-steam substitution of finding §1 all remain open. Any reading of the
result as "the downstate ST_GAS residual is explained" is unsupported and I will
say so in the report.

## 7. HOLDOUT

`--year 2023 2024 2025` in ONE bundle each, sequential within the run (rules 12,
16). No year outside the training window is solved, scored or registered. The
holdout spend freeze is untouched.
