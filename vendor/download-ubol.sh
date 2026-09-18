#!/usr/bin/env bash
# Download + prepare uBlock Origin Lite for Chromium (unpacked dir).
# Why AMO and not the Chrome Web Store? The store's CRX endpoint is
# unreliable outside a real Chrome session; Mozilla serves the identical
# official MV3 build as a plain .xpi (a zip). We convert its Firefox-style
# manifest to Chrome-style (service_worker) in the unpacked copy.
set -euo pipefail
cd "$(dirname "$0")"

XPI_URL="https://addons.mozilla.org/firefox/downloads/latest/ublock-origin-lite/"
curl -sL --max-time 180 "$XPI_URL" -o ubol.xpi
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
