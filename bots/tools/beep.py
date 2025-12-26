"""
Audio playback tools for playing piano notes and simple beeps.

Supports MIDI-based piano playback with TRUE polyphonic chords using
synthesized piano tones. Uses NumPy for synthesis and winsound for playback.
"""

from __future__ import annotations

import os
import sys
import tempfile
import wave
from typing import TYPE_CHECKING, Optional

# Runtime import
try:
    import numpy as np

    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None  # type: ignore

if TYPE_CHECKING:
    import numpy as np

# Windows winsound - reliable and built-in
if sys.platform == "win32":
    import winsound
