#!/usr/bin/env python
"""Register a capacity-hindcast result on the forecast-validation dashboard.

Writes the sidecar ``frontend/data/hindcast/<run_id>.json`` (a NEW namespace,
deliberately outside the backcast run-explorer registry and its CI gates — plan
§1.5) and regenerates the self-contained
``docs/codebase-site/forecast-validation.html`` page (hindcast scorecards +
invariant status), the forecast-side sibling of ``calibration-status.html``.

Each sidecar bundles: the run meta, the score.json metrics/bands, and the
forecast-invariant summary run over the hindcast cache. The HTML embeds every
registered sidecar directly as a JSON island, so it renders with no fetch/deploy
dependency.

Usage::

    python scripts/register_hindcast.py --bundle results/hindcast/ercot-2021-2025-realized
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
if _SRC.exists() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

SIDECAR_DIR = Path("frontend/data/hindcast")
PAGE_PATH = Path("docs/codebase-site/forecast-validation.html")


def build_sidecar(bundle_dir: Path, preserve_invariants: bool = False) -> dict:
    """Assemble the sidecar dict for one hindcast bundle.

    ``preserve_invariants`` re-uses the invariant summary already stored in the
    committed sidecar instead of recomputing it. Invariants depend on the
    persisted dispatch parquets, which are intentionally NOT committed (too
    large); recomputing them in a scoring-only session (e.g. the T-R8 IS-2020
    re-score, which touches only score.json) would silently flip parquet-derived
    invariants (I1/I9) to SKIP purely because the parquets are absent. Preserving
    them keeps the sidecar diff to the intended score change.
    """
    # Lazy import: the invariant summary needs numpy + market_sim constants,
    # which the Pages deploy runner (stdlib-only, --page-only path) does not
    # install. Importing here keeps page regeneration dependency-free.
    import check_forecast_invariants as CI  # noqa: PLC0415 (sibling script)

    meta = json.loads((bundle_dir / "meta.json").read_text())
    cache_dir = Path(meta["bundle"])
    if not cache_dir.exists():
        cache_dir = bundle_dir / meta["iso"] / meta["cache_key"]
    score_path = cache_dir / "score.json"
    score = json.loads(score_path.read_text()) if score_path.exists() else None
    run_id = bundle_dir.name
    existing = SIDECAR_DIR / f"{run_id}.json"
    if preserve_invariants and existing.exists():
        invariants = json.loads(existing.read_text()).get("invariants", [])
    else:
        # Forecast-invariant summary over the hindcast cache.
        invariants = [
            {"ident": r.ident, "name": r.name, "status": r.status, "detail": r.detail}
            for r in CI.run_single(cache_dir)
        ]
    return {
        "run_id": run_id,
        "meta": meta,
        "score": score,
        "invariants": invariants,
        "registered_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def _load_all_sidecars() -> list[dict]:
    out = []
    if SIDECAR_DIR.exists():
        for p in sorted(SIDECAR_DIR.glob("*.json")):
            out.append(json.loads(p.read_text()))
    return out


def render_page(sidecars: list[dict]) -> str:
    """Return the self-contained forecast-validation.html source."""
    data_json = json.dumps(sidecars, indent=2)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Forecast Validation — Codebase Explorer</title>
  <meta name="description" content="Capacity-hindcast scorecards and forecast-invariant status — the forecast-side sibling of Calibration Status.">
  <link rel="stylesheet" href="css/shared.css">
  <link rel="stylesheet" href="css/site.css">
  <link rel="stylesheet" href="css/bc-pages.css">
  <style>
    .fv-card{{border:1px solid var(--border,#334);border-radius:8px;padding:1rem 1.25rem;margin-bottom:1.5rem;background:var(--surface,#1b1f2a)}}
    .fv-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:.5rem;margin:.75rem 0}}
    .fv-metric{{padding:.5rem .75rem;border-radius:6px;background:var(--surface-2,#232838)}}
    .fv-metric .v{{font-size:1.25rem;font-weight:600}}
    .fv-metric .l{{font-size:.75rem;opacity:.75}}
    table.fv{{width:100%;border-collapse:collapse;margin:.5rem 0;font-size:.9rem}}
    table.fv th,table.fv td{{padding:.35rem .5rem;border-bottom:1px solid var(--border,#334);text-align:right}}
    table.fv th:first-child,table.fv td:first-child{{text-align:left}}
    .pass{{color:#3fb950}} .fail{{color:#f85149}} .warn{{color:#d29922}} .skip{{opacity:.6}}
    .fv-inv{{display:flex;flex-wrap:wrap;gap:.35rem;margin:.5rem 0}}
    .fv-inv span{{font-size:.72rem;padding:.15rem .45rem;border-radius:4px;border:1px solid var(--border,#334)}}
    .fv-empty{{opacity:.7;padding:2rem;text-align:center}}
  </style>
</head>
<body>
  <nav id="topNav"></nav>
  <div class="content-section" style="padding: var(--space-lg);">
    <div class="bc-page-header"><h1>Forecast Validation</h1></div>
    <p class="bc-page-sub">Capacity-hindcast scorecards &amp; forecast-invariant status — the
    forecast-side sibling of Calibration Status. A missed band is a root-cause
    investigation (rules&nbsp;1/11/14), never widened. Generated {stamp}.</p>
    <div id="cards"></div>
  </div>

  <script id="fvData" type="application/json">{data_json}</script>
  <script src="js/nav.js"></script>
  <script>
  (function(){{
    const data = JSON.parse(document.getElementById('fvData').textContent||'[]');
    const el = document.getElementById('cards');
    const cls = s => ({{PASS:'pass',FAIL:'fail',WARN:'warn',SKIP:'skip'}}[s]||'');
    if(!data.length){{ el.innerHTML='<div class="fv-empty">No hindcast runs registered yet.</div>'; return; }}
    el.innerHTML = data.map(function(d){{
      const m=d.meta||{{}}, sc=d.score||null;
      let body='';
      if(sc){{
        const tg=sc.retirements.total_gw, rr=sc.retirements.unit_recall_gt300;
        body += '<div class="fv-grid">'+
          metric(tg.model+' GW','thermal retired ('+cls2(tg.band)+')')+
          metric(tg.actual+' GW','actual retired')+
          metric((rr.recall==null?'—':(rr.recall*100).toFixed(0)+'%'),'unit recall &gt;300MW ('+cls2(rr.band)+')')+
          metric(sc.additions.model_total_gw+' GW','total additions')+
        '</div>';
        body += is2020Block(sc);
        body += addTable(sc.additions);
        body += co2Table(sc.co2);
      }} else {{ body += '<p class="skip">score.json not found — run score_capacity_hindcast.py.</p>'; }}
      body += '<div class="fv-inv">'+ (d.invariants||[]).map(function(i){{
        return '<span class="'+cls(i.status)+'" title="'+esc(i.detail)+'">'+i.ident+' '+i.status+'</span>';
      }}).join('') +'</div>';
      const arms=[];
      if(m.entry_lookahead_reprice) arms.push('lookahead');
      if(m.retirement_rule && m.retirement_rule!=='legacy') arms.push('r-new '+m.retirement_rule);
      if(m.limited_foresight_dispatch) arms.push('ltd-foresight');
      if(m.energy_only_floor) arms.push('energy-only-floor');
      const armStr = arms.length ? ' &middot; '+arms.join(' + ') : '';
      return '<div class="fv-card"><h2>'+ esc(d.run_id||m.iso||'?') +'</h2>'+
             '<p class="bc-page-sub">'+ (m.iso||'?') +' &middot; '+ (m.start_year||'') +'–'+ (m.end_year||'') +
             ' &middot; '+ (m.variant||'') +' fuel'+ armStr +'</p>'+
             '<p class="bc-page-sub">solved '+JSON.stringify(m.solved_years||[])+', bridged '+
             JSON.stringify(m.bridged_years||[])+' (rule 22) &middot; gas '+(m.gas_price_path||'')+'</p>'+ body +'</div>';
    }}).join('');
    function metric(v,l){{return '<div class="fv-metric"><div class="v">'+v+'</div><div class="l">'+l+'</div></div>';}}
    function cls2(b){{return '<span class="'+cls(b)+'">'+b+'</span>';}}
    function esc(s){{return (s||'').replace(/"/g,'&quot;');}}
    function addTable(a){{
      const techs=['wind','solar','gas_cc','gas_ct','storage'];
      let r='<table class="fv"><tr><th>tech</th><th>actual GW</th><th>model GW</th><th>err</th><th>band</th><th>Δshare pp</th></tr>';
      techs.forEach(function(t){{const d=a.by_tech[t],s=a.shares[t];if(!d)return;
        r+='<tr><td>'+t+'</td><td>'+d.actual_gw+'</td><td>'+d.model_gw+'</td><td>'+(d.err_frac==null?'—':(d.err_frac*100).toFixed(0)+'%')+
           '</td><td>'+cls2(d.band)+'</td><td>'+(s.delta_pp*100).toFixed(1)+'</td></tr>';}});
      return r+'</table>';
    }}
    function is2020Block(sc){{
      // RC-0B §c.5 / T-R8: raw vs IS-2020 retirement scoring, reversal exposure,
      // and per-channel decomposition. Only rendered for re-scored bundles.
      const ri=sc.retirements_is2020; if(!ri) return '';
      const raw=sc.retirements, fr=raw.false_retire, frI=ri.false_retire;
      const exp=(ri.reversal_exposure_gw!=null?ri.reversal_exposure_gw:0);
      let r='<table class="fv"><tr><th>IS-2020 ('+(sc.is2020_cutoff||'')+')</th><th>raw</th><th>IS-2020</th></tr>';
      r+='<tr><td>false-retire GW</td><td>'+fr.false_gw+' '+cls2(fr.band)+'</td><td>'+frI.false_gw+' '+cls2(frI.band)+'</td></tr>';
      r+='<tr><td>reversal exposure GW</td><td>—</td><td>'+exp+'</td></tr>';
      r+='</table>';
      if(ri.reversal_rows&&ri.reversal_rows.length){{
        const names=ri.reversal_rows.map(function(x){{return x.unit_name+' ('+x.unit_id+')';}}).join(', ');
        r+='<p class="bc-page-sub">Reversal-excluded (§c.5-1, information-set-correct, reality-reversed): '+esc(names)+'.</p>';
      }}
      const ch=sc.retirement_channels;
      if(ch){{
        const nbig=ch._n_big_actual||0;
        r+='<table class="fv"><tr><th>channel</th><th>retired GW</th><th>false-retire GW</th><th>recall</th></tr>';
        ['confirmed','announced','economic'].forEach(function(c){{
          const d=ch[c]; if(!d)return;
          r+='<tr><td>'+c+'</td><td>'+d.retired_gw+'</td><td>'+d.false_retire_gw+'</td><td>'+d.recall_matched+'/'+nbig+'</td></tr>';
        }});
        r+='</table>';
      }}
      return r;
    }}
    function co2Table(c){{
      if(!c)return'';let r='<table class="fv"><tr><th>year</th><th>model Mt</th><th>actual Mt</th><th>err</th></tr>';
      Object.keys(c.model||{{}}).sort().forEach(function(y){{
        const m=c.model[y],a=(c.actual||{{}})[y];
        const err=(a?(((m-a)/a)*100).toFixed(0)+'%':'—');
        r+='<tr><td>'+y+'</td><td>'+(m/1e6).toFixed(1)+'</td><td>'+(a?(a/1e6).toFixed(1):'n/a')+'</td><td>'+err+'</td></tr>';
      }});
      return r+'</table>';
    }}
  }})();
  </script>
</body>
</html>
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--bundle",
        type=Path,
        default=None,
        help="run_capacity_hindcast out-dir to register (omit with --page-only).",
    )
    parser.add_argument(
        "--preserve-invariants",
        action="store_true",
        help=(
            "Re-use the committed sidecar's invariants instead of recomputing "
            "them (scoring-only re-scores where the dispatch parquets are absent, "
            "e.g. T-R8 — avoids flipping parquet-derived invariants to SKIP)."
        ),
    )
    parser.add_argument(
        "--page-only",
        action="store_true",
        help=(
            "Regenerate forecast-validation.html from the committed sidecars "
            "only — no bundle, no invariant recompute, stdlib-only (the Pages "
            "deploy assembles the page with this, mirroring build_manifest.py, "
            "so a registered sidecar shows on the LIVE dashboard once the "
            "deploy runs; the committed page copy is preview-only)."
        ),
    )
    parser.add_argument(
        "--site-dir",
        type=Path,
        default=None,
        help=(
            "Write the page under <site-dir>/docs/codebase-site/ instead of "
            "the repo path (deploy staging, e.g. _site)."
        ),
    )
    args = parser.parse_args(argv)

    if not args.page_only:
        if args.bundle is None:
            parser.error("--bundle is required unless --page-only")
        SIDECAR_DIR.mkdir(parents=True, exist_ok=True)
        sidecar = build_sidecar(
            args.bundle, preserve_invariants=args.preserve_invariants
        )
        sidecar_path = SIDECAR_DIR / f"{sidecar['run_id']}.json"
        sidecar_path.write_text(json.dumps(sidecar, indent=2))
        print(f"[register] wrote sidecar {sidecar_path}")

    page_path = PAGE_PATH
    if args.site_dir is not None:
        page_path = args.site_dir / PAGE_PATH
        page_path.parent.mkdir(parents=True, exist_ok=True)
    page = render_page(_load_all_sidecars())
    page_path.write_text(page)
    print(f"[register] regenerated {page_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
