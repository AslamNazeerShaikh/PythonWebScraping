#!/usr/bin/env bash
# Download + prepare uBlock Origin Lite for Chromium (unpacked dir).
# Source of truth: https://github.com/uBlockOrigin/uBOL-home
# (Chrome Web Store item ddkjiahejlhfcafbddmgiahcphecmpfh ships this build;
#  the release publishes only the signed .xpi, which is the same MV3 package
#  — we convert its Firefox-style manifest to Chrome-style service_worker).
set -euo pipefail
cd "$(dirname "$0")"

UBOL_TAG="2026.914.1325"
XPI_URL="https://github.com/uBlockOrigin/uBOL-home/releases/download/${UBOL_TAG}/uBOLite_${UBOL_TAG}.firefox.signed.xpi"
curl -sL --max-time 180 -A "Mozilla/5.0" "$XPI_URL" -o ubol.xpi
python3 - <<'EOF'
import json, shutil, zipfile
from pathlib import Path

shutil.rmtree("ubol-chrome", ignore_errors=True)
with zipfile.ZipFile("ubol.xpi") as z:
    z.extractall("ubol-chrome")

p = Path("ubol-chrome/manifest.json")
m = json.loads(p.read_text())
m["background"] = {"service_worker": "js/background.js", "type": "module"}
m.pop("browser_specific_settings", None)  # Firefox-only key
p.write_text(json.dumps(m, indent=2))
print("prepared ubol-chrome:", m["name"], m["version"])
EOF
