"""Home manifest contract — machine-readable source of truth for `home.manifest`.

This mirrors the role `archetypes.py` plays for sub-page manifests: one small
contract that the validator and future renderer can consume instead of
re-reading prose from the SKILL inputs.
"""

import os

SKILL_DIR = os.path.dirname(os.path.abspath(__file__))
SHARED_DIR = os.path.normpath(os.path.join(SKILL_DIR, "..", "headset-shared"))

CONNECTION_SNIPPET_DIR = os.path.join(SHARED_DIR, "connection")
FEATURE_ICON_DIR = os.path.join(SHARED_DIR, "icons")

BATTERY_SLOT_MARKER = 'data-property="battery-level"'

HOME_SCHEMA = {
    "fields": {
        "marketing-name": {
            "required": True,
            "type": "str",
            "drives": "device name header",
            "absent": "HALT",
        },
        "model-number": {
            "required": True,
            "type": "str",
            "drives": "model number",
            "absent": "HALT",
        },
        "connectionType": {
            "required": True,
            "type": "enum:file",
            "registry": "connection",
            "drives": "connection snippet",
            "absent": "HALT",
        },
        "firmware": {
            "required": False,
            "type": "str",
            "drives": "firmware tooltip row",
            "absent": "omit firmware row",
        },
        "ppid": {
            "required": False,
            "type": "str",
            "drives": "PPID tooltip row",
            "absent": "omit PPID row",
        },
        "image": {
            "required": True,
            "type": "path|none",
            "drives": "device image",
            "absent": "HALT; use `image: none` plus `opt-out-reason` for an explicit no-image page",
        },
        "opt-out-reason": {
            "required": False,
            "type": "str",
            "drives": "required explanation when `image: none` explicitly opts out of a device image",
            "absent": "HALT only when `image: none`; otherwise omit",
        },
        "battery": {
            "required": False,
            "type": "int:0-100",
            "conditional": {
                "field": "connectionType",
                "snippet_marker": BATTERY_SLOT_MARKER,
            },
            "drives": "battery value in snippets that expose a battery slot",
            "absent": "render dash percent when the chosen snippet has a battery slot; otherwise ignore",
        },
        "features": {
            "required": False,
            "type": "list",
            "item_required": ("label", "icon", "link"),
            "drives": "home feature buttons and sub-page build obligations",
            "absent": "homepage only",
            "empty": "homepage only",
        },
    },
    "registries": {
        "connection": {
            "field": "connectionType",
            "dir": CONNECTION_SNIPPET_DIR,
            "extension": ".html",
            "path_display": "connection/{id}.html",
        },
        "feature-icon": {
            "field": "features[].icon",
            "dir": FEATURE_ICON_DIR,
            "extension": ".svg",
            "path_display": "icons/{id}.svg",
        },
    },
}

REQUIRED_FIELDS = tuple(
    name for name, spec in HOME_SCHEMA["fields"].items() if spec["required"]
)
OPTIONAL_FIELDS = tuple(
    name for name, spec in HOME_SCHEMA["fields"].items() if not spec["required"]
)
ALLOWED_FIELDS = frozenset(HOME_SCHEMA["fields"])
FEATURE_REQUIRED_FIELDS = HOME_SCHEMA["fields"]["features"]["item_required"]
FEATURE_ALLOWED_FIELDS = frozenset(FEATURE_REQUIRED_FIELDS)


def registry_path(registry, key):
    spec = HOME_SCHEMA["registries"][registry]
    return os.path.join(spec["dir"], "%s%s" % (key, spec["extension"]))


def registry_display(registry, key):
    return HOME_SCHEMA["registries"][registry]["path_display"].format(id=key)


def render_table():
    lines = [
        "# Home manifest contract — DERIVED from home-schema.py",
        "",
        "| Field | Required | Type | Absence rule |",
        "|---|---|---|---|",
    ]
    for name, spec in HOME_SCHEMA["fields"].items():
        lines.append("| `%s` | %s | %s | %s |" % (
            name,
            "yes" if spec["required"] else "no",
            spec["type"],
            spec["absent"],
        ))
    return "\n".join(lines)


if __name__ == "__main__":
    print(render_table())
