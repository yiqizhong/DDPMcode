"""Authoring keyword registry for snapshot-match advisories.

The validator uses this as a warn-only heuristic for assembled functions whose
id/title appears to match an existing snapshot. It must not affect routing.
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
