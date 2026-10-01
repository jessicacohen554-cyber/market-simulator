# FINDING — miso-164: the GADS data ask (candidate 1) is RESOLVED ON EVIDENCE and it FAILS. No browser was ever needed; the brochures are year-specific after all, but they are ANNUAL and NERC-WIDE, and the model already consumes them as `constants.py::EFORD`. Candidate 4 is the only route left, and it is not a session

**Session** miso-164 · **ISO** MISO · **Date** 2026-08-17 ·
**Keeper** `2026-08-16-miso-160-wefor-shape`, **UNCHANGED**.

**NO SOLVE. NO RUN REGISTERED. NO `ScenarioConfig` FIELD. NO CELL VERDICT
MINTED. NO CORPUS CREATED** — this is a no-intake closure, so nothing lands
under `data/raw/`. Rule 15 `[R-DASHBOARD]` is not engaged.

**Rule 22 `[R-HOLDOUT]`:** no year was solved or scored. MISO holds neither
`complete` nor `final`; the spend freeze is untouched. (The brochure family
spans 2014–2025, but nothing here reads a model output against any year's
actuals — the finding is about a candidate input's *grain*, not about any
year's result.)

**Charter.** The owner re-chartered MISO after the miso-163 closure ("needs more
work"). miso-163's own record named exactly three grounds on which MISO is not
at frontier; ground (c) was the pair of standing data asks, of which the
outage-grain ask's **candidate 1 (NERC GADS)** was the one item flagged
*"UNRESOLVED, explicitly not refuted"* and carrying a scheduling warning that a
session pursuing it *"needs working browser egress."* This session tested that.

---

## 1. The stated blocker was real but IRRELEVANT

The ask recorded candidate 1 as blocked on an environment limitation:
*"Chromium cannot traverse the session's agent proxy at all (`example.com` fails
with `ERR_CONNECTION_RESET`)."*

**Re-tested 2026-08-17 — the Chromium blocker is REAL and UNCHANGED.** Launching
the pre-installed browser (`/opt/pw-browsers/chromium-1194/chrome-linux/chrome`)
with `--proxy-server=http://127.0.0.1:40483 --ignore-certificate-errors` against
`https://example.com` returns Chromium's network-error page carrying
`ERR_CONNECTION_RESET`, not the document. Plain HTTPS through the same proxy is
healthy (`example.com` → 200; `nerc.com` GADS Reports → 301 → 200, 69,131 bytes).

**But the browser was never required.** The Reports page ships its file listing
as a JSON payload embedded in the served HTML, so a single `curl` enumerates
**47 brochure URLs** without executing any JavaScript. The files then download
directly from
`https://www.nerc.com/globalassets/programs/rapa/gads/{conventional,reports}/`.

**⇒ The scheduling note is WITHDRAWN.** No session needs browser egress for this
ask. (The Chromium/proxy defect itself remains, and is worth knowing for any
*other* JS-dependent target — but it did not block this one.)

## 2. §3's stated reason was HALF-WRONG; its conclusion stands

§3's prior held that the brochures *"are multi-year rolling class averages and
therefore fail C."* Measured:

| product | grain | verdict on the "rolling" claim |
|---|---|---|
| **Brochure 1** — Units Reporting Events | **single year**, one file per year, 2014–**2025** | **REFUTED** |
| **Brochure 2** — All Units Reporting | **single year**, 2014–**2025** | **REFUTED** |
| Brochure 3 — Units Reporting Events | 5-year rolling (2019–2023, 2021–2025) | confirmed |
| Brochure 4 — All Units Reporting | 5-year rolling (2018–2022, 2021–2025) | confirmed |

Brochures 1 and 2 cover **2023, 2024 and 2025** individually — MISO's exact
training window. Verified on `brochure-1-2023`: sheet `2023-01`, 76 data rows,
`Start` and `End` both `2023`, a single distinct year value across the file.

So the objection as *written* does not apply to the products that matter. The
ask's conclusion is nonetheless correct, for the reasons in §3 below.

## 3. Why it still FAILS — C on seasonality, D on footprint

Scored against the ask's §2 A–D:

| criterion | requirement | verdict |
|---|---|---|
| **A** | capability, not output | **CLEARS** — GADS event reporting is capability-grain, not inferred from generation |
| **B** | unit or fuel-class grain | **CLEARS** — prime mover × primary fuel × size band (below) |
| **C** | year-specific **AND season-resolved** | **FAILS** — year-specific yes; **season-resolved NO** |
| **D** | MISO footprint | **FAILS** — NERC-wide North-America aggregates, no regional cut |

**C is the load-bearing failure.** The brochures are **annual**: statistics keyed
on `Unit-Years`, `Start` = `End` = the year, with no month, season or
summer/winter split of any kind. §1(a) is entirely a *summer change between
years*, so an annual rate is blind to it by construction — exactly what the
ask's own §2 note anticipated.

**What it would have delivered had C and D held** — recorded so no successor
re-opens it hoping for more:

* **Classes** (× 8 size bands `001-099` … `1000 Plus`):
  `FOSSIL {All Fuel Types, Coal Primary, Gas Primary, Lignite Primary, Oil
  Primary, Oil/Gas Primary}`, `COMBINED CYCLE`, `GAS TURBINE`, `JET ENGINE`,
  `DIESEL`, `MULTIBOILER/MULTI-TURBINE`, `HYDRO`, `PUMPED STORAGE`,
  `NUCLEAR {All Types, BWR, PWR, CANDU}`, `GEOTHERMAL`. This maps cleanly onto
  the model's taxonomy (`COAL_PRB`/`COAL_LIGNITE`/`CC_*`/`CT_PEAKER`).
* **Cause separation** (clears the ask's cause requirement):
  `FOH/POH/MOH/SEPO/SEMO/UAH/EFDH/ESDH/EDOH` plus counts.
* **Rate family:** `FOR, EFOR, EFORd, EAF, AF, POF, MOF, SOF, FOF, UOF, EUOF,
  EUOR` and the weighted `WFOR, WEFOR, WEAF, WSF, WAF, WSOF, WFOF` — note
  **`WEFOR` is literally the quantity this ask's §2a parameter
  (`SUMMER_WEFOR_SHARE`) is named for**, which is why the candidate looked
  promising and why closing it needed measurement rather than assertion.

## 4. The decisive corroboration — intake would be INERT

**The model already consumes this exact product.**
`src/market_sim/config/constants.py::EFORD` (currently lines 2279–2286, comment
*"Source: NERC GADS"*) carries the annual class EFORs:

```
gas_cc 0.05 · gas_ct 0.06 · gas_st 0.07 · coal 0.08 · nuclear 0.03 · oil 0.10 · biomass 0.08
```

Intaking Brochure 1/2 therefore re-imports the statistical fallback already in
place, at a **coarser** footprint (NERC-wide vs the MISO cut D asks for), with
**no seasonal content**. The ask's §2 note predicted this outcome in advance:
*"Re-importing another static class average would satisfy B and D but fail C and
would move nothing."* The only correction to that sentence is that GADS fails D
too, on footprint.

## 5. Consequences

1. **The outage-grain ask's candidate 1 is CLOSED ON EVIDENCE, against.**
   Candidate 2 was already closed, candidate 3 downgraded. **Candidate 4 — the
   MISO stakeholder data request — is the only route left standing, and it is a
   human/owner action, not a session that can be chartered here.** This is a
   **hard data blocker** on any further MISO summer-availability work.
2. **Frontier is still NO, on narrower grounds.** miso-163 named three grounds;
   this session **closes ground (c)** for candidate 1 (it is now resolved, not
   unresolved). Frontier still fails on the other two, which are untouched:
   **(a)** the RCPF/ORDC intake was *declined as predicted-inert*, and
   declined-not-tested is not "tested everything we could have"; **(b)** the
   C3a-2025 closure was explicitly *"a budget decision, not a rubric
   decision."* Candidate 4 also remains an open, untested named object. Do not
   read this finding as movement toward a frontier claim.
3. **Nothing about the determination changes.** MISO stays `NOT-YET` on
   C3a-2025 alone (−12.5 %), reported at full magnitude as a `[MODEL MISS]`;
   C3c stays the single ledgered caveat; the keeper is unchanged.

---

**Reproduction.** Enumerate:
`curl -sSL https://www.nerc.com/pa/RAPA/gads/Pages/Reports.aspx` and read the
embedded JSON file listing (no browser). Fetch:
`https://www.nerc.com/globalassets/programs/rapa/gads/conventional/generating-unit-statistical-brochure-{1,2}-2023---{units-reporting-events,all-units-reporting}.xlsx`.
Identities of the two files inspected (sha256, 2026-08-17):

```
758501f59e6e8d579f8f9c7b53c1a98a560edf5e8a51b702efe4b97e208eeb7f  brochure-1-2023---units-reporting-events.xlsx   (48,000 B)
634bcb76426baf58942c3c23dc4923418bf78ba2445961348ce60df825cb0874  brochure-2-2023---all-units-reporting.xlsx      (49,362 B)
```

Both were inspected in the session scratchpad via `zipfile` + the
SpreadsheetML XML (no pandas/openpyxl dependency) and **deliberately not
committed** — the closure is no-intake, so no corpus, README or `SHA256SUMS.txt`
is created. The hashes above are the identity record.

**Surfaces stamped:** `docs/handoffs/miso-outage-grain-data-ask-2026-07.md`
(status header, candidate 1 section, §8 Net) and
`docs/calibration-log/miso.md` (miso-164). Keeper untouched; no dashboard
mutation; no matrix cell minted (no mechanism was tested).
Predecessor: `FINDING-miso163-c3a-lane-closure-2026-08-17.md`.
