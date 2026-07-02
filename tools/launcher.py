"""Local web launcher for the ERCOT calibration backcast.

Serves a small UI on localhost where you pick a per-plant tranche-config CSV
(the editable sheet from scripts/export_tranche_config.py), choose the years,
and click Run. It shells out to scripts/run_calibration_full.py with
``--plant-tranche-config`` so the chosen sheet drives every plant's tranche
shares + heat-rate multipliers, then regenerates the backcast data files
(frontend/data/backcast/) against the run10 baseline and links you to the
codebase-site run explorer (docs/codebase-site/backcast-runs.html), which
this server serves locally.

stdlib only (http.server + threads), so the bootstrap needs nothing beyond the
model's own dependencies. Launched by run-simulator.bat (Windows) /
run-simulator.sh; or directly: ``python tools/launcher.py``.
"""

from __future__ import annotations

import json
import subprocess
import sys
import threading
import webbrowser
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

REPO = Path(__file__).resolve().parent.parent
PORT = 8765
BASELINE_BUNDLE = REPO / "results" / "calibration" / "run10_peak85"

# Single-run job state, shared between the request handler and the worker
# thread. Only one run executes at a time (the LP is CPU-heavy).
JOB: dict = {"state": "idle", "log": [], "results_ready": False, "label": ""}
_LOCK = threading.Lock()

_CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".js": "text/javascript",
    ".css": "text/css",
    ".csv": "text/csv",
    ".json": "application/json",
    ".svg": "image/svg+xml",
    ".png": "image/png",
}


def _log(line: str) -> None:
    with _LOCK:
        JOB["log"].append(line.rstrip("\n"))


def _list_configs() -> list[dict]:
    """Return the candidate tranche-config CSVs under inputs/ (+ configs/)."""
    out = []
    for d in (REPO / "inputs", REPO / "configs"):
        if not d.is_dir():
            continue
        for p in sorted(d.glob("*.csv")):
            # Heuristic: only sheets that look like tranche configs.
            try:
                header = p.read_text(errors="ignore").split("\n", 1)[0]
            except OSError:
                continue
            # Distinctive columns of the export_tranche_config schema (the old
            # custom-bin-assignments.csv has Pct_Committed but not these).
            if "HR_Mult_Econ_Low" in header and "Pct_Econ_Low" in header:
                out.append(
                    {
                        "path": str(p.relative_to(REPO)),
                        "name": p.name,
                        "size_kb": round(p.stat().st_size / 1024, 1),
                    }
                )
    return out


def _run_job(csv_rel: str, years: list[int], label: str) -> None:
    """Worker: run the backcast with the chosen sheet, then render the report."""
    try:
        with _LOCK:
            JOB.update(state="running", log=[], results_ready=False, label=label)
        csv_path = (REPO / csv_rel).resolve()
        if REPO not in csv_path.parents or not csv_path.is_file():
            raise FileNotFoundError(f"config not found: {csv_rel}")
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        out_dir = REPO / "results" / "calibration" / f"ui_{stamp}"
        yrs = [str(y) for y in years]
        run_cmd = [
            sys.executable,
            str(REPO / "scripts" / "run_calibration_full.py"),
            "--year",
            *yrs,
            "--plant-tranche-config",
            str(csv_path),
            "--out-dir",
            str(out_dir),
            "--note",
            f"UI run from {csv_rel}",
        ]
        _log(f"$ {' '.join(run_cmd)}")
        if _stream(run_cmd) != 0:
            raise RuntimeError("dispatch run failed (see log above)")

        render_cmd = [
            sys.executable,
            str(REPO / "scripts" / "render_backcast.py"),
            f"run10 baseline={BASELINE_BUNDLE}",
            f"{label}={out_dir}",
            "--years",
            *yrs,
        ]
        _log("")
        _log(f"$ {' '.join(render_cmd)}")
        if _stream(render_cmd) != 0:
            raise RuntimeError("report render failed (see log above)")
        _log("")
        _log("Done. Open the results dashboard below.")
        with _LOCK:
            JOB.update(state="done", results_ready=True)
    except Exception as exc:  # surface any failure to the UI
        _log(f"ERROR: {exc}")
        with _LOCK:
            JOB.update(state="error")


def _stream(cmd: list[str]) -> int:
    """Run ``cmd`` from the repo root, streaming each output line to the log."""
    proc = subprocess.Popen(
        cmd,
        cwd=str(REPO),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    assert proc.stdout is not None
    for line in proc.stdout:
        _log(line)
    return proc.wait()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):  # quiet the default stderr access log
        pass

    def _send(self, code: int, body: bytes, ctype: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json(self, obj, code: int = 200) -> None:
        self._send(code, json.dumps(obj).encode(), "application/json")

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path in ("/", "/index.html"):
            self._send(200, PAGE.encode(), "text/html; charset=utf-8")
        elif path == "/api/configs":
            self._json(
                {"configs": _list_configs(), "baseline": BASELINE_BUNDLE.is_dir()}
            )
        elif path == "/api/status":
            with _LOCK:
                self._json(
                    {
                        "state": JOB["state"],
                        "label": JOB["label"],
                        "results_ready": JOB["results_ready"],
                        "log": "\n".join(JOB["log"]),
                    }
                )
        else:
            self._serve_static(path)

    def do_POST(self) -> None:
        if urlparse(self.path).path != "/api/run":
            self._json({"error": "not found"}, 404)
            return
        with _LOCK:
            if JOB["state"] == "running":
                self._json({"error": "a run is already in progress"}, 409)
                return
        length = int(self.headers.get("Content-Length", 0))
        try:
            req = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            self._json({"error": "bad request"}, 400)
            return
        csv_rel = req.get("csv")
        years = [int(y) for y in req.get("years", [2023, 2024])]
        label = (req.get("label") or "my run").strip()[:40] or "my run"
        if not csv_rel:
            self._json({"error": "no config selected"}, 400)
            return
        threading.Thread(
            target=_run_job, args=(csv_rel, years, label), daemon=True
        ).start()
        self._json({"ok": True})

    def _serve_static(self, path: str) -> None:
        target = (REPO / path.lstrip("/")).resolve()
        if REPO not in target.parents and target != REPO:
            self._json({"error": "forbidden"}, 403)
            return
        if not target.is_file():
            self._json({"error": "not found"}, 404)
            return
        ctype = _CONTENT_TYPES.get(target.suffix, "application/octet-stream")
        self._send(200, target.read_bytes(), ctype)


PAGE = r"""<!doctype html><html lang=en><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>Market Simulator — Run Launcher</title><style>
:root{--bg:#f6f7f9;--card:#fff;--bd:#e3e7ec;--ink:#1a1f29;--mut:#6b7480;--accent:#2f6df0;--accent2:#1f53c4;--ok:#0f7d3d;--bad:#c01c28}
*{box-sizing:border-box}body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;background:var(--bg);color:var(--ink);margin:0;padding:24px;line-height:1.5}
.wrap{max-width:860px;margin:0 auto}h1{font-size:22px;margin:0 0 4px}.sub{color:var(--mut);margin:0 0 18px;font-size:14px}
.card{background:var(--card);border:1px solid var(--bd);border-radius:12px;padding:18px 20px;margin:14px 0;box-shadow:0 1px 2px rgba(0,0,0,.03)}
label{font-weight:600;font-size:13px;display:block;margin:0 0 6px}
select,input{font-size:15px;padding:9px 11px;border:1px solid var(--bd);border-radius:8px;background:#fff;width:100%;color:var(--ink)}
.row{display:flex;gap:16px;flex-wrap:wrap}.row>div{flex:1;min-width:200px}
.yrs{display:flex;gap:14px;align-items:center}.yrs label{display:inline-flex;align-items:center;gap:6px;font-weight:500;margin:0}
.yrs input{width:auto}
button{font-size:15px;font-weight:600;padding:11px 20px;border:0;border-radius:9px;background:var(--accent);color:#fff;cursor:pointer}
button:hover{background:var(--accent2)}button:disabled{opacity:.5;cursor:default}
.hint{color:var(--mut);font-size:12.5px;margin-top:6px}
#log{background:#0e1320;color:#cdd6e4;font-family:ui-monospace,Menlo,Consolas,monospace;font-size:12.5px;
 padding:12px 14px;border-radius:8px;white-space:pre-wrap;max-height:360px;overflow:auto;margin-top:10px}
.state{display:inline-block;font-size:12px;font-weight:700;padding:3px 10px;border-radius:20px;text-transform:uppercase;letter-spacing:.04em}
.s-idle{background:#eef1f4;color:#6b7480}.s-running{background:#fff5d6;color:#9a6700}.s-done{background:#e3f5ea;color:var(--ok)}.s-error{background:#fde7e9;color:var(--bad)}
a.btn{display:inline-block;text-decoration:none;margin-top:12px}
.hide{display:none}
</style></head><body><div class=wrap>
<h1>Market Simulator — Run Launcher</h1>
<p class=sub>Pick a per-plant tranche-config sheet, choose years, and run the ERCOT backcast. Edit the sheet in Excel (inputs/plant-tranche-config.csv) to reshape each plant's tranches.</p>

<div class=card>
 <div class=row>
  <div><label for=cfg>Tranche-config CSV</label><select id=cfg></select>
   <div class=hint id=cfgHint></div></div>
  <div><label for=label>Run label</label><input id=label value="my run" maxlength=40>
   <div class=hint>Shown next to the run10 baseline on the results page.</div></div>
 </div>
 <div style="margin-top:14px"><label>Years</label>
  <div class=yrs>
   <label><input type=checkbox class=yr value=2023 checked> 2023</label>
   <label><input type=checkbox class=yr value=2024 checked> 2024</label>
   <span class=hint>(2025 EIA data is incomplete.)</span>
  </div></div>
 <div style="margin-top:18px;display:flex;align-items:center;gap:14px">
  <button id=run>Run backcast</button>
  <span id=state class="state s-idle">idle</span>
  <a id=view class="btn hide" href="/docs/codebase-site/backcast-runs.html#iso=ERCOT" target=_blank><button>View results ↗</button></a>
 </div>
 <div class=hint id=warn style="color:#c01c28;margin-top:10px"></div>
</div>

<div class=card>
 <label>Run log</label>
 <div id=log>Idle. Select a config and click Run.</div>
</div>
</div>
<script>
const $=s=>document.querySelector(s);
let polling=null;
async function loadConfigs(){
 const r=await fetch('/api/configs');const d=await r.json();
 const sel=$('#cfg');sel.innerHTML=d.configs.map(c=>`<option value="${c.path}">${c.name} (${c.size_kb} KB)</option>`).join('')||'<option value="">— no tranche CSVs in inputs/ —</option>';
 if(!d.baseline)$('#warn').textContent='Warning: results/calibration/run10_peak85 baseline bundle not found — the report will only show your run.';
 updHint();
}
function updHint(){const o=$('#cfg').selectedOptions[0];$('#cfgHint').textContent=o&&o.value?('Using '+o.value):'';}
$('#cfg').addEventListener('change',updHint);
function years(){return [...document.querySelectorAll('.yr:checked')].map(c=>+c.value);}
async function start(){
 const csv=$('#cfg').value;if(!csv){$('#warn').textContent='Pick a config CSV first.';return;}
 const yrs=years();if(!yrs.length){$('#warn').textContent='Pick at least one year.';return;}
 $('#warn').textContent='';$('#run').disabled=true;$('#view').classList.add('hide');
 const r=await fetch('/api/run',{method:'POST',headers:{'Content-Type':'application/json'},
  body:JSON.stringify({csv,years:yrs,label:$('#label').value})});
 if(!r.ok){const e=await r.json();$('#warn').textContent=e.error||'failed to start';$('#run').disabled=false;return;}
 if(!polling)polling=setInterval(poll,1500);poll();
}
async function poll(){
 const r=await fetch('/api/status');const d=await r.json();
 const st=$('#state');st.className='state s-'+d.state;st.textContent=d.state;
 $('#log').textContent=d.log||'(starting…)';$('#log').scrollTop=$('#log').scrollHeight;
 if(d.state==='done'){$('#run').disabled=false;$('#view').classList.remove('hide');clearInterval(polling);polling=null;}
 else if(d.state==='error'){$('#run').disabled=false;clearInterval(polling);polling=null;}
}
$('#run').addEventListener('click',start);
loadConfigs();poll();
</script></body></html>"""


def main() -> None:
    global PORT
    if "--port" in sys.argv:
        PORT = int(sys.argv[sys.argv.index("--port") + 1])
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    url = f"http://127.0.0.1:{PORT}/"
    print(f"Market Simulator launcher running at {url}")
    print("Leave this window open; close it to stop the server.")
    if "--no-browser" not in sys.argv:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopping…")
        server.shutdown()


if __name__ == "__main__":
    main()
