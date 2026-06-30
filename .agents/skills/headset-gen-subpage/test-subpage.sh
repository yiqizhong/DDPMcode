#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
RENDERER="$ROOT/.agents/skills/headset-gen-subpage/render-subpage.py"
TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT

# Positive fixture: HS-DEMO (always clean).
CASES=(
  "HS-DEMO audio-settings"
)

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

check_structure() {
  local model="$1"
  local subpage="$2"
  local out="$3"

  ROOT="$ROOT" MODEL="$model" SUBPAGE="$subpage" OUT="$out" python3 - <<'PY'
import html
import importlib.util
import os
import re
import sys

root = os.environ["ROOT"]
model = os.environ["MODEL"]
subpage = os.environ["SUBPAGE"]
out_path = os.environ["OUT"]
skill_dir = os.path.join(root, ".agents", "skills", "headset-gen-subpage")

def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

parse_manifest = load_module(
    "validate_manifest",
    os.path.join(skill_dir, "validate-manifest.py"),
).parse_manifest

def read_manifest(path):
    with open(path, "r", encoding="utf-8") as f:
        return parse_manifest(f.read())

def require(condition, message):
    if not condition:
        print("FAIL: " + message, file=sys.stderr)
        sys.exit(1)

home = read_manifest(os.path.join(root, "headset", "models", model, "home.manifest"))
page = read_manifest(os.path.join(root, "headset", "models", model, subpage + ".manifest"))
with open(out_path, "r", encoding="utf-8") as f:
    doc = f.read()

features = home.get("features") or []
functions = page.get("functions") or []
name = html.escape(str(home["marketing-name"]), quote=False)
title = html.escape(str(page["title"]), quote=False)
model_number = html.escape(str(home["model-number"]), quote=False)

require(doc.lstrip().startswith("<!DOCTYPE html>"), "output is not a full HTML document")
require("<html" in doc and "</html>" in doc, "output is missing html root")
require('<link rel="stylesheet" href="../../../shared/tokens.css">' in doc, "missing output-depth tokens.css href")
require('<link rel="stylesheet" href="../../../shared/shell.css">' in doc, "missing output-depth shell.css href")
require('<link rel="stylesheet" href="../../headset.css">' in doc, "missing output-depth headset.css href")
require("../../../../shared/tokens.css" not in doc and "../../../../shared/shell.css" not in doc and "../../../../headset/headset.css" not in doc, "preview-depth CSS href remains")
require("<style" not in doc.lower(), "inline style block present")

require(f"<title>{title}</title>" in doc, "sub-page title was not filled in <title>")
require(f'<h2 class="feature-title">{title}</h2>' in doc, "sub-page title was not filled in <h2>")
require(f'<h1 class="page-title">{name}</h1>' in doc, "device h1 missing or wrong")
require(f'<span class="model-number">{model_number}</span>' in doc, "device model missing or wrong")
require('class="back-link" href="index.html"' in doc, "back link to index.html missing")

ctype = home["connectionType"]
if ctype == "bluetooth":
    battery = str(home.get("battery", "—")) + "%"
    require('class="bluetooth-icon"' in doc, "bluetooth connection block missing")
    require(f'<span class="battery-text">{battery}</span>' in doc, "bluetooth battery value missing")
elif ctype == "wired":
    require('class="wired-icon"' in doc, "wired connection block missing")
    require('<span class="battery-text">USB-C</span>' in doc, "wired USB-C label missing")
else:
    require(False, "test case has unsupported connectionType " + ctype)

require("Unpair" not in doc and "unpair-button" not in doc, "sub-page rendered Unpair")
require("{label}" not in doc and "{link}" not in doc and "{id}" not in doc, "leftover placeholder exists")
require(not re.search(r"\{[A-Za-z0-9_-]+\}", doc), "leftover brace placeholder exists")
require(not re.search(r"data-(property|slot|instruction)=", doc), "template marker attribute remains")

collapsed = re.findall(r'class="[^"]*\bfeature-button\b[^"]*\bfeature-button--collapsed\b[^"]*"', doc)
require(len(collapsed) == len(features), "collapsed feature button count %d != manifest count %d" % (len(collapsed), len(features)))
for feature in features:
    label = html.escape(str(feature["label"]), quote=False)
    link = html.escape(str(feature["link"]), quote=True)
    icon_path = os.path.join(root, ".agents", "skills", "headset-shared", "icons", feature["icon"] + ".svg")
    with open(icon_path, "r", encoding="utf-8") as f:
        icon = f.read().strip()
    require(f'href="{link}"' in doc, "feature link missing: " + link)
    require(f'<span class="feature-text">{label}</span>' in doc, "feature label missing: " + label)
    require(icon in doc, "feature icon markup missing for " + feature["icon"])

if functions:
    require(doc.count('class="function-container"') >= len(functions), "content cards missing")
else:
    require("Sub-feature content TBD" in doc, "empty functions placeholder note missing")
PY
}

for case in "${CASES[@]}"; do
  read -r model subpage <<<"$case"
  first_hash=""
  first_out=""

  for i in $(seq 1 10); do
    out="$TMPDIR/$model-$subpage-$i.html"
    err="$TMPDIR/$model-$subpage-$i.err"
    if ! python3 "$RENDERER" "$model" "$subpage" >"$out" 2>"$err"; then
      cat "$err" >&2
      fail "$model $subpage render failed on run $i"
    fi
    hash="$(shasum -a 256 "$out" | awk '{print $1}')"
    if [[ -z "$first_hash" ]]; then
      first_hash="$hash"
      first_out="$out"
    elif [[ "$hash" != "$first_hash" ]]; then
      fail "$model $subpage run $i sha256 $hash != first run $first_hash"
    fi
  done

  check_structure "$model" "$subpage" "$first_out"
  echo "PASS $model $subpage 10x byte-identical sha256=$first_hash"
done
