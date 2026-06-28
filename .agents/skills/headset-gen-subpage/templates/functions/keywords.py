"""Snapshot-match keyword registry for the manifest gate.

When an assembled function (one with no snapshot id) has an id/title matching one
of these keywords, validate-manifest HALTs and tells the author to use the snapshot
id instead. A valid `snapshot-opt-out` + `opt-out-reason` downgrades it to an
advisory. This only guards against mis-authoring — it never changes routing
(routing is id -> functions/<id>.html only).
"""

SNAPSHOT_KEYWORDS = {
    "eq-audio": [
        "audio equalizer",
        "equalizer",
        "sound eq",
        "eq curve",
        "frequency eq",
    ],
    "promotion-download": [
        "download dell audio",
        "download app",
        "promotion",
        "qr code",
        "mobile app download",
    ],
    "single-control": [
        "exactly one boolean parameter",
    ],
}
