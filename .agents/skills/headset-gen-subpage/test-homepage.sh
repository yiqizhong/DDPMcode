#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
RENDERER="$ROOT/.agents/skills/headset-gen-subpage/render-home.py"
TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT

# Positive fixture: HS-DEMO (always clean).
MODELS=(
  "HS-DEMO"
)

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

check_structure() {
  local model="$1"
  local out="$2"

  ROOT="$ROOT" MODEL="$model" OUT="$out" python3 - <<'PY'
import html
import importlib.util
import os
import re
import sys

root = os.environ["ROOT"]
model = os.environ["MODEL"]
out_path = os.environ["OUT"]
skill_dir = os.path.join(root, ".agents", "skills", "headset-gen-subpage")

def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

parse_manifest = load_module(
    "validate_home",
    os.path.join(skill_dir, "validate-home.py"),
).parse_manifest

def read_manifest(path):
    with open(path, "r", encoding="utf-8") as f:
        return parse_manifest(f.read())

def require(condition, message):
    if not condition:
        print("FAIL: " + message, file=sys.stderr)
        sys.exit(1)

home = read_manifest(os.path.join(root, "headset", "models", model, "home.manifest"))
with open(out_path, "r", encoding="utf-8") as f:
    doc = f.read()

features = home.get("features") or []
name = html.escape(str(home["marketing-name"]), quote=False)
model_number = html.escape(str(home["model-number"]), quote=False)
firmware = html.escape(str(home.get("firmware", "")), quote=False)

require(doc.lstrip().startswith("<!DOCTYPE html>"), "output is not a full HTML document")
require("<html" in doc and "</html>" in doc, "output is missing html root")
require(f'<h1 class="page-title">{name}</h1>' in doc, "device h1 missing or wrong")
require(f'<span class="model-number">{model_number}</span>' in doc, "device model missing or wrong")
require(f"Firmware Version <span>{firmware}</span>" in doc, "firmware value missing or wrong")
require('<a class="back-link"' not in doc, "home page has an anchor back link")
require('href="index.html"' not in doc, "home page has a navigable back link")

require('<link rel="stylesheet" href="../../../shared/tokens.css">' in doc, "missing output-depth tokens.css href")
require('<link rel="stylesheet" href="../../../shared/shell.css">' in doc, "missing output-depth shell.css href")
require('<link rel="stylesheet" href="../../headset.css">' in doc, "missing output-depth headset.css href")
require("../../../../shared/tokens.css" not in doc and "../../../../shared/shell.css" not in doc and "../../../../headset/headset.css" not in doc, "preview-depth CSS href remains")
require("<style" not in doc.lower(), "inline style block present")

ctype = home["connectionType"]
if ctype == "bluetooth":
    battery = str(home.get("battery", "—")) + "%"
    require('class="bluetooth-icon"' in doc, "bluetooth connection block missing")
    require(f'<span class="battery-text">{battery}</span>' in doc, "bluetooth battery value missing")
    require('class="unpair-button"' in doc and "Unpair" in doc, "bluetooth Unpair is missing")
elif ctype == "wired":
    require('class="wired-icon"' in doc, "HS-DEMO wired connection block missing")
    require('<span class="battery-text">USB-C</span>' in doc, "HS-DEMO USB-C label missing")
    require('class="unpair-button"' not in doc and "Unpair" not in doc, "HS-DEMO rendered Unpair")
else:
    require(False, "test case has unsupported connectionType " + ctype)

require("feature-button--collapsed" not in doc, "home page rendered collapsed feature button variant")
buttons = re.findall(r'<a class="feature-button" href="[^"]+">', doc)
require(len(buttons) == len(features), "feature button count %d != manifest count %d" % (len(buttons), len(features)))
for feature in features:
    label = html.escape(str(feature["label"]), quote=False)
    link = html.escape(str(feature["link"]), quote=True)
    icon_path = os.path.join(root, ".agents", "skills", "headset-shared", "icons", feature["icon"] + ".svg")
    with open(icon_path, "r", encoding="utf-8") as f:
        icon = f.read().strip()
    require(f'href="{link}"' in doc, "feature link missing: " + link)
    require(f'<span class="feature-text">{label}</span>' in doc, "feature label missing: " + label)
    require(icon in doc, "feature icon markup missing for " + feature["icon"])

require("{label}" not in doc and "{link}" not in doc and "{id}" not in doc, "leftover named placeholder exists")
require(not re.search(r"\{[A-Za-z0-9_-]+\}", doc), "leftover brace placeholder exists")
require(not re.search(r"data-(property|slot|instruction)=", doc), "template marker attribute remains")
PY
}

for model in "${MODELS[@]}"; do
  first_hash=""
  first_out=""

  for i in $(seq 1 10); do
    out="$TMPDIR/$model-$i.html"
    err="$TMPDIR/$model-$i.err"
    if ! python3 "$RENDERER" "$model" >"$out" 2>"$err"; then
      cat "$err" >&2
      fail "$model render failed on run $i"
    fi
    hash="$(shasum -a 256 "$out" | awk '{print $1}')"
    if [[ -z "$first_hash" ]]; then
      first_hash="$hash"
      first_out="$out"
    elif [[ "$hash" != "$first_hash" ]]; then
      fail "$model run $i sha256 $hash != first run $first_hash"
    fi
  done

  check_structure "$model" "$first_out"
  echo "PASS $model 10x byte-identical sha256=$first_hash"
done
