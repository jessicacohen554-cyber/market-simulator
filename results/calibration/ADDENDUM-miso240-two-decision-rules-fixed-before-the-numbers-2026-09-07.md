# ADDENDUM miso-240 — two decision rules the PREREG left under-specified, FIXED HERE BEFORE THE NUMBERS THEY GOVERN

Extends `PREREG-miso240-charter-or-refuse-the-external-bus-price-2026-09-07.md` (pushed
`5c503155`). On the miso-233 / miso-235 / miso-236 / miso-237 / miso-238 / miso-239 addendum
pattern: **pushed before the numbers it governs**, and it moves no bar the PREREG already fixed.

**NOTHING ELSE IS TOUCHED.** Zero LP, as declared. Keeper unchanged at
`2026-09-07-miso-233-spp-hourly` (CALIBRATED, C3c the single ledgered caveat, DOF 41/2). The
provenance gate (§1) and its bars, the tie tolerance `τ = $0.01` with its declared sensitivity
(§2), Q-A's ladder and readings (§3a), Q-B's placebo construction and its `0.25` / `0.50` bars
and `100 MW/z` floor (§3b), Q-D's `0.10` / `0.02` bars (§3d) and every §5 restriction stand
exactly as pushed. **No adjudicating quantity has been computed at the time this is written.**

---

## A. Q-B's DENOMINATOR — resolved to the STRICTER of the two readings

PREREG §3b writes the placebo bar as `|γ_np(p1|MERIT_p1)| ≤ 0.25·|γ(MERIT_p1)|` but does not
say which residualization `γ(MERIT_p1)` carries. Two readings are available and the PREREG
picks neither, so both are computed and the verdict must hold under **both**:

* **`γ_mirror`** — the exact mirror of `γ_MERIT`: `γ( ols_resid(MERIT_p1, s), s_own )`, i.e.
  the OTHER spread removed linearly, which is what `γ_MERIT = γ(ols_resid(MERIT, p1), s_own)`
  does with the roles of `s` and `p1` swapped.
* **`γ_raw`** — `γ( MERIT_p1, s_own )`, no spread removed at all.

**Rule, fixed here:** the §3b verdict is read on `γ_mirror` **and** on `γ_raw`. If the two give
different verdicts, the leg is published as **FRAGILE** and closes nothing. The `100 MW/z`
absolute floor applies to **both** denominators — below either, the leg reads **NOT
MEANINGFUL**. This is strictly stronger than the PREREG's single unnamed denominator, and it is
fixed before any of the four values exists.

## B. Q-C's LEG (iii) IS SPLIT OFF INTO ITS OWN GATED QUESTION, because the PREREG's wording would MISNAME its own failure

PREREG §3c makes three legs jointly necessary for **EXISTS**, the third being *"its
`MISO-Indiana` DA column reproduces the lane's own `da` series to ≤ $0.01/MWh in ≥ 99 % of `ok`
hours"*. That is a defect in this session's own instrument, disclosed before it is run: legs
(i) and (ii) are about the candidate parquet, while leg (iii) is about **which series the LANE's
`da` actually is**. A leg-(iii) failure would make the PREREG print "DOES NOT EXIST" about a
file that plainly exists.

**Fixed here, before any number:**

* **Q-C (GATED) keeps legs (i) and (ii) only.** **EXISTS** iff the parquet carries all four `B`
  zones in all three years **and** DA hourly coverage on the fixed 8,760 grid is `≥ 0.95` per
  zone-year; **DOES NOT EXIST** otherwise, with the failing leg named. Bars unchanged.
* **Q-C2 — BASIS IDENTITY (GATED), new, three outcomes fixed here.** Let `m` be the share of
  `ok` hours where the zonal parquet's `MISO-Indiana` DA equals the lane's `da`
  (`derive_miso_seam_ladders.load_joined`) to within `$0.01/MWh`.
  * **BASIS CONFIRMED** iff `m ≥ 0.99` in all three years ⇒ the lane's standing
    "Indiana-hub DA" label is correct as written.
  * **BASIS MISLABELLED** iff `m < 0.50` in any year **AND** some other series available from
    the same committed sources matches at `≥ 0.99` in all three years ⇒ that series is NAMED
    and the label is corrected. The candidate set is fixed **here**, before the numbers, and is
    closed: the zonal parquet's eight-hub simple mean DA, and each of the eight named hubs' own
    DA (`ARKANSAS`, `ILLINOIS`, `INDIANA`, `LOUISIANA`, `MICHIGAN`, `MINN`, `MS`, `TEXAS`).
    If more than one clears, the one with the highest minimum `m` across the three years is
    named and the runners-up are reported.
  * **BASIS INDETERMINATE** otherwise.

**WHAT Q-C2 CANNOT DO, fixed here before it is read.** Whatever it returns it **changes no
predecessor number and moves no verdict**: `da` is the series every predecessor from miso-232
onward actually computed with, `MISO_SEAM_LADDER_BY_YEAR` was Q-Q derived against that same
series, and the `ok` mask is built from the Indiana-hub **RT** column, which is unaffected.
A BASIS MISLABELLED outcome is a correction to a **LABEL**, exactly as miso-239 §0b withdrew a
label while its arithmetic stood — **not** a re-derive, not a re-basing, not a licence to touch
the frozen `δ_k` ladders (rule 23 `[R-FROZEN-DERIVE]`, PREREG §5.2, which binds whatever this
returns), and not a reason to re-run any predecessor. It also **licenses no lever**: no
mechanism may be proposed, sized or selected on it (rules 1 `[R-STRUCT]` / 13 `[R-MEASURED]`,
PREREG §5.3).

## C. Governance

Rule 1 `[R-STRUCT]`: no bar is moved and no rule is written after seeing a number; §A makes a
bar **stricter** and §B makes a failure **nameable**, both before the numbers. Rule 12: no LP.
Rule 13: measurement only. Rule 14 / 23: no input changed, no derive re-run — §B restates that
its own possible outcome licenses neither. Rule 15: no run produced, registered or pruned.
Rule 21 `[R-DOF]`: 41/2 unchanged; both rules here carry zero free parameters and the candidate
set in §B is closed before it is searched. Rule 22: 2023–2025 only. Rule 24: no field created.
Rule 25 `[R-ISO-SCOPE]`: MISO only. Rule 27: blobs verified after push. Rule 28(b):
evidence-append form only. Rule 29: clause 0, zero LP.
