# ADDENDUM A2 (nyiso-249) — G-6: test the counter-argument to G-3 instead of dismissing it

**Added to `docs/PRECOMMIT-nyiso249-upper-tail-offer-dispersion-2026-09-20.md` BEFORE the gate is
run.** Zero LP. Nothing in G-6 has been measured yet.

## What G-3 and G-4 established, and the one objection they invite

**G-3 (run, reported in full in the RESULT):** the P-27 book's registered TIGHT window contains
**7 of 153** missed hours across 2022–2025 — coverage **2.2 % / 0.0 % / 0.0 % / 12.8 %**, against a
pre-registered bar of 25 % in at least two years. **0 of 4 years clear it.** Exposure runs
**95–100 %**: nearly every tight hour is one where the market had no tail at all.

**G-4 (run):** the missed hours sit at the top of the **LOAD** distribution and not the gas one —
2024 load-percentile p50 **0.99** (69 % at or above p90) against **0.0 %** of those hours reaching
the gas p90; 2025 load p50 **1.00** (92 % at or above p90) against 15 % on gas. And **136 of 153**
carry the model's maximum in **Long Island**.

**The objection this invites is obvious and deserves a measurement, not a dismissal:**

> *"Then condition the form on LOAD alone, where the deficit actually is."*

## Why the objection cannot rescue THIS lane's form — and what is still open

**It cannot reuse these numbers.** `τ` is identified *inside* the gas-tight window; applying
magnitudes measured there to load-tight hours is the "measured here, applied there" error the
derive's own PRECOMMIT §1.1 rules on (and which nyiso-245's pooled-gas-tercile refusal turns on).
So the objection does not save the pre-registered form, and this lane's §3 form is decided by G-3
regardless of what G-6 finds.

**But it says nothing about whether the OBJECT exists under a load conditioner**, and that is a
measurement. Refusing to make it would be choosing not to look.

## The gate

`scripts/probes/nyiso249_window_variants.py`. Denominator held at nyiso-248's corrected **daily**
array throughout; **only the conditioner changes**; each variant's ordinary window is its own
complement on its own axes.

| variant | tight | role |
|---|---|---|
| **W1** | `gas ≥ p90 AND load ≥ p90` | the registered window (must reproduce ladder arm D) |
| **W2** | `load ≥ p90` alone | the coordinate the **deficit** lives on |
| **W3** | `gas ≥ p90` alone | the gas leg alone, for attribution |

Each variant also reports its own **coverage of the missed hours**, so a measured object and the
window that could carry it are read together rather than separately.

## WHAT THIS LANE WILL AND WILL NOT DO WITH IT — fixed here

* **W1 must reproduce ladder arm D.** It is the same construction; a mismatch means the harness is
  wrong and nothing else may be read.
* **THIS LANE DOES NOT BUILD ON W2, WHATEVER IT SHOWS.** A form conditioned on load needs its own
  PRECOMMIT, its own identification and its own gates. A form chosen in the session that found the
  evidence is exactly the selection discipline nyiso-246 §6 declined to breach, and this lane
  declines it on the same terms. **G-6 produces a ROUTING number for a successor and nothing else**
  — no arm is solved off it in this session, and no gate in this session reads it.
* **A large W2 tail is not a promise.** The book is masked, so W2 would give a magnitude and never
  an attribution; and G-5 measured that Long Island is **import-dependent** in these hours (demand
  3,032–4,470 MW mean against 2,601–3,249 MW of its own available thermal), so a locational
  constraint may bind before any offer does. That is the successor's problem to size, not a
  conclusion available here.
* **A small or absent W2 tail is equally informative** and will be reported as plainly: it would
  say the measured dispersion object is specific to gas-tight hours and is not a general
  scarcity-conduct object at all.
