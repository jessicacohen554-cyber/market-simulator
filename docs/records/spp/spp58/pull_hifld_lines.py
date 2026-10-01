"""SPP-58 step 0 — pull the HIFLD Electric Power Transmission Lines features intersecting the
SPP box from the public ArcGIS feature service (anonymous HTTPS, paginated by resultOffset),
byte-for-byte JSON pages to the scratchpad. No PTDF is computed here. Box and service are the
PRECOMMIT's §2.2 declaration."""
import json, os, sys, time, hashlib, urllib.request, urllib.parse
OUT = sys.argv[1]
SVC = "https://services1.arcgis.com/Hp6G80Pky0om7QvQ/arcgis/rest/services/Electric_Power_Transmission_Lines/FeatureServer/0/query"
BOX = dict(xmin=-108.0, ymin=29.0, xmax=-88.0, ymax=49.5)   # lon/lat, WGS84
FIELDS = "OBJECTID_1,OBJECTID,ID,TYPE,STATUS,OWNER,VOLTAGE,VOLT_CLASS,INFERRED,SUB_1,SUB_2,SOURCEDATE,VAL_DATE,Shape__Length"
os.makedirs(OUT, exist_ok=True)
def q(params):
    url = SVC + "?" + urllib.parse.urlencode(params)
    for k in range(5):
        try:
            with urllib.request.urlopen(url, timeout=120) as r: return r.read()
        except Exception as e:
            print("retry", k, e, file=sys.stderr); time.sleep(2 ** k)
    raise SystemExit("pull failed")
base = dict(where="1=1", geometry=json.dumps(BOX), geometryType="esriGeometryEnvelope", inSR=4326,
            spatialRel="esriSpatialRelIntersects", outFields=FIELDS, outSR=4326, f="json",
            returnGeometry="true", geometryPrecision=5, maxAllowableOffset=0.0005)
cnt = json.loads(q({**base, "returnCountOnly": "true", "returnGeometry": "false"}))["count"]
print("features in box:", cnt)
off = 0; n = 0; h = hashlib.sha256(); page = 0
while off < cnt:
    raw = q({**base, "resultOffset": off, "resultRecordCount": 2000})
    h.update(raw); j = json.loads(raw); feats = j.get("features", [])
    with open(f"{OUT}/page_{page:03d}.json", "wb") as f: f.write(raw)
    n += len(feats); off += 2000; page += 1
    print(f"page {page} rows {len(feats)} total {n} exceeded={j.get('exceededTransferLimit')}", flush=True)
    if not feats: break
print("rows", n, "sha256(all pages)", h.hexdigest())
json.dump({"service": SVC, "box": BOX, "count": cnt, "rows": n, "pages": page, "sha256_pages": h.hexdigest(),
           "pulled_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}, open(f"{OUT}/manifest.json", "w"), indent=1)
