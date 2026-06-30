#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
RENDERER="$ROOT/.agents/skills/headset-gen-subpage/render-content.py"
CSS="$ROOT/headset/headset.css"
TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

python3 "$RENDERER" "$ROOT/headset/models/WL527/device-settings.manifest" >"$TMPDIR/device-settings.html"
python3 "$RENDERER" "$ROOT/headset/models/WL527/automated-actions.manifest" >"$TMPDIR/automated-actions.html"
python3 "$RENDERER" "$ROOT/headset/models/WL527/audio-settings.manifest" >"$TMPDIR/audio-settings.html"

python3 - "$TMPDIR" "$CSS" <<'PY'
import pathlib
import sys

tmp = pathlib.Path(sys.argv[1])
css = pathlib.Path(sys.argv[2]).read_text()


def fail(message):
    print("FAIL: " + message, file=sys.stderr)
    raise SystemExit(1)


def card(markup, title):
    title_marker = f'<p class="function-title-text">{title}</p>'
    pos = markup.find(title_marker)
    if pos == -1:
        fail(f"{title}: missing function title")
    start = markup.rfind('<div class="function-container">', 0, pos)
    end = markup.find('<div class="function-container">', pos)
    if start == -1:
        fail(f"{title}: missing function container")
    if end == -1:
        end = len(markup)
    return markup[start:end]


def before_body(card_html):
    body_at = card_html.find('<div class="function-content"')
    if body_at == -1:
        fail("missing function-content")
    return card_html[:body_at]


def body(card_html):
    body_at = card_html.find('<div class="function-content"')
    if body_at == -1:
        fail("missing function-content")
    return card_html[body_at:]


def assert_hoisted(markup, title, dependent_text=None, needs_greyout=True):
    html = card(markup, title)
    head = before_body(html)
    content = body(html)
    if '<label class="switch">' not in head:
        fail(f"{title}: switch was not hoisted into the card title row")
    if needs_greyout and 'class="switch-input subfn-toggle"' not in head:
        fail(f"{title}: hoisted dependent toggle is not the grey-out controller")
    if 'class="switch-input subfn-toggle"' in content:
        fail(f"{title}: card-level toggle still rendered in the body")
    if dependent_text and dependent_text not in content:
        fail(f"{title}: dependent {dependent_text!r} missing from body")


device = (tmp / "device-settings.html").read_text()
automated = (tmp / "automated-actions.html").read_text()
audio = (tmp / "audio-settings.html").read_text()

assert_hoisted(device, "Auto Off", "Power off after")
assert_hoisted(device, "Audio Guidance", "Guidance Type")
assert_hoisted(device, "Busy Light", needs_greyout=False)
assert_hoisted(automated, "Wear Detection", "Sensor Sensitivity")
if "When Headset Removed" not in body(card(automated, "Wear Detection")):
    fail("Wear Detection: nested dependent card missing from body")

collaboration = card(audio, "Collaboration")
if '<label class="switch">' in before_body(collaboration):
    fail("Collaboration: multi-component card was incorrectly hoisted")
if "Mic Noise Cancellation" not in body(collaboration):
    fail("Collaboration: Mic Noise Cancellation body row missing")
if 'class="switch-input subfn-toggle"' not in body(collaboration):
    fail("Collaboration: Sidetone body grey-out toggle missing")

noise = card(audio, "Noise Control")
if '<label class="switch">' in before_body(noise):
    fail("Noise Control: segmented card was incorrectly hoisted")
if '<div class="segmented-group">' not in body(noise):
    fail("Noise Control: segmented body control missing")

selector = (
    ".function-top-section:has(> div > .function-header "
    ".subfn-toggle:not(:checked)) > div > .function-content > .subfn-child"
)
if selector not in css:
    fail("CSS is missing the card-level toggle grey-out selector")

if ".subfn-group:has(> .function-header .subfn-toggle:not(:checked)) > .subfn-child" not in css:
    fail("CSS lost the nested/named sub-function grey-out selector")
PY

echo "PASS card-level toggle hoist regressions"
