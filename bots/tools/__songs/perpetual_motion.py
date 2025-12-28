"""
Perpetual Motion - A Continuous Sixteenth Note Study

This piece features an almost unbroken stream of sixteenth notes (0.25 beats)
in the melody, creating a flowing, perpetual motion effect, while the bass
moves more slowly and deliberately to provide harmonic support.

MELODY: Continuous sixteenth notes (hemisemiquavers)
- Flowing, unbroken stream of 0.25 beat notes
- Scalar passages, arpeggios, and patterns
- Never stops moving - perpetual motion!

BASS: Slower, deliberate (half notes and quarter notes)
- Provides harmonic foundation
- Moves in 1.0 or 2.0 beat increments
- Reacts to and supports the melody's harmony

The contrast between the rushing melody and steady bass creates
a hypnotic, mechanical beauty - like a music box or clockwork.

Tempo: 120 BPM (Moderate - so the 16ths are clear but flowing)
Duration: ~60 seconds
Key: D Major (bright and clear)
Style: Perpetual motion study / Toccata
"""

import os
import sys

# Add parent directories to path to import beep module directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from tools.beep import piano


def play_perpetual_motion():
    """Play the Perpetual Motion composition."""

    song = " ".join(
        [
            # SECTION 1: D major scale patterns (16 beats)
            # Bass: D pedal (whole notes), Melody: continuous 16ths
            # D major ascending (4 beats = 16 sixteenth notes)
            "[D2:4]:0.25 D4:0.25 E4:0.25 F#4:0.25",
            "G4:0.25 A4:0.25 B4:0.25 C#5:0.25",
            "D5:0.25 E5:0.25 F#5:0.25 G5:0.25",
            "A5:0.25 B5:0.25 C#6:0.25 D6:0.25",
            # D major descending (4 beats)
            "[D2:4]:0.25 D6:0.25 C#6:0.25 B5:0.25",
            "A5:0.25 G5:0.25 F#5:0.25 E5:0.25",
            "D5:0.25 C#5:0.25 B4:0.25 A4:0.25",
            "G4:0.25 F#4:0.25 E4:0.25 D4:0.25",
            # Pattern variation (4 beats)
            "[D2:4]:0.25 D4:0.25 F#4:0.25 A4:0.25",
            "D5:0.25 F#5:0.25 A5:0.25 D6:0.25",
            "A5:0.25 F#5:0.25 D5:0.25 A4:0.25",
            "F#4:0.25 D4:0.25 A3:0.25 F#3:0.25",
            # Arpeggio pattern (4 beats)
            "[D2:4]:0.25 D4:0.25 F#4:0.25 A4:0.25",
            "D5:0.25 A4:0.25 F#4:0.25 D4:0.25",
            "D4:0.25 F#4:0.25 A4:0.25 D5:0.25",
            "F#5:0.25 A5:0.25 D6:0.25 F#6:0.25",
            # SECTION 2: Moving to A major (16 beats)
            # Bass moves to A
            # A major arpeggio (4 beats)
            "[A2:4]:0.25 A4:0.25 C#5:0.25 E5:0.25",
            "A5:0.25 C#6:0.25 E6:0.25 A6:0.25",
            "E6:0.25 C#6:0.25 A5:0.25 E5:0.25",
            "C#5:0.25 A4:0.25 E4:0.25 C#4:0.25",
            # Flowing pattern (4 beats)
            "[A2:4]:0.25 E4:0.25 A4:0.25 C#5:0.25",
            "E5:0.25 A5:0.25 C#6:0.25 E6:0.25",
            "C#6:0.25 A5:0.25 E5:0.25 C#5:0.25",
            "A4:0.25 E4:0.25 C#4:0.25 A3:0.25",
            # Scalar run (4 beats)
            "[A2:4]:0.25 A4:0.25 B4:0.25 C#5:0.25",
            "D5:0.25 E5:0.25 F#5:0.25 G#5:0.25",
            "A5:0.25 G#5:0.25 F#5:0.25 E5:0.25",
            "D5:0.25 C#5:0.25 B4:0.25 A4:0.25",
            # Wave pattern (4 beats)
            "[A2:4]:0.25 A4:0.25 C#5:0.25 E5:0.25",
            "C#5:0.25 A4:0.25 C#5:0.25 E5:0.25",
            "A5:0.25 E5:0.25 C#5:0.25 E5:0.25",
            "A5:0.25 C#6:0.25 E6:0.25 A6:0.25",
            # SECTION 3: G major (16 beats)
            # Bass moves to G
            # G major scale (4 beats)
            "[G2:4]:0.25 G4:0.25 A4:0.25 B4:0.25",
            "C5:0.25 D5:0.25 E5:0.25 F#5:0.25",
            "G5:0.25 F#5:0.25 E5:0.25 D5:0.25",
            "C5:0.25 B4:0.25 A4:0.25 G4:0.25",
            # Broken chord pattern (4 beats)
            "[G2:4]:0.25 G4:0.25 B4:0.25 D5:0.25",
            "G5:0.25 D5:0.25 B4:0.25 G4:0.25",
            "B4:0.25 D5:0.25 G5:0.25 B5:0.25",
            "D6:0.25 B5:0.25 G5:0.25 D5:0.25",
            # Chromatic approach (4 beats)
            "[G2:4]:0.25 G4:0.25 G#4:0.25 A4:0.25",
            "A#4:0.25 B4:0.25 C5:0.25 C#5:0.25",
            "D5:0.25 D#5:0.25 E5:0.25 F5:0.25",
            "F#5:0.25 G5:0.25 G#5:0.25 A5:0.25",
            # Return pattern (4 beats)
            "[G2:4]:0.25 B5:0.25 A5:0.25 G5:0.25",
            "F#5:0.25 E5:0.25 D5:0.25 C5:0.25",
            "B4:0.25 A4:0.25 G4:0.25 F#4:0.25",
            "E4:0.25 D4:0.25 C4:0.25 B3:0.25",
            # SECTION 4: Back to D major with bass movement (16 beats)
            # Bass becomes more active
            # D major with bass quarter notes (4 beats)
            "[D2:1]:0.25 D5:0.25 F#5:0.25 A5:0.25",
            "[A2:1]:0.25 D6:0.25 A5:0.25 F#5:0.25",
            "[F#2:1]:0.25 D5:0.25 F#5:0.25 A5:0.25",
            "[D2:1]:0.25 D6:0.25 A5:0.25 F#5:0.25",
            # A major with bass movement (4 beats)
            "[A2:1]:0.25 E5:0.25 A5:0.25 C#6:0.25",
            "[E2:1]:0.25 E6:0.25 C#6:0.25 A5:0.25",
            "[C#3:1]:0.25 E5:0.25 A5:0.25 C#6:0.25",
            "[A2:1]:0.25 E6:0.25 C#6:0.25 A5:0.25",
            # G major with walking bass (4 beats)
            "[G2:1]:0.25 D5:0.25 G5:0.25 B5:0.25",
            "[A2:1]:0.25 D6:0.25 B5:0.25 G5:0.25",
            "[B2:1]:0.25 D5:0.25 G5:0.25 B5:0.25",
            "[C3:1]:0.25 E5:0.25 G5:0.25 C6:0.25",
            # Resolution to D (4 beats)
            "[D3:1]:0.25 F#5:0.25 A5:0.25 D6:0.25",
            "[A2:1]:0.25 F#6:0.25 D6:0.25 A5:0.25",
            "[D2:1]:0.25 F#5:0.25 A5:0.25 D6:0.25",
            "[D2:1]:0.25 F#6:0.25 A6:0.25 D7:0.25",
            # CODA: Final perpetual motion cascade (16 beats)
            # Descending cascade (4 beats)
            "[D2:2]:0.25 D7:0.25 A6:0.25 F#6:0.25",
            "D6:0.25 A5:0.25 F#5:0.25 D5:0.25",
            "A4:0.25 F#4:0.25 D4:0.25 A3:0.25",
            "F#3:0.25 D3:0.25 A2:0.25 F#2:0.25",
            # Ascending cascade (4 beats)
            "[D2:2]:0.25 D3:0.25 F#3:0.25 A3:0.25",
            "D4:0.25 F#4:0.25 A4:0.25 D5:0.25",
            "F#5:0.25 A5:0.25 D6:0.25 F#6:0.25",
            "A6:0.25 D7:0.25 F#7:0.25 A7:0.25",
            # Final swirl (4 beats)
            "[D2:2]:0.25 A7:0.25 F#7:0.25 D7:0.25",
            "A6:0.25 F#6:0.25 D6:0.25 A5:0.25",
            "F#5:0.25 D5:0.25 A4:0.25 F#4:0.25",
            "D4:0.25 F#4:0.25 A4:0.25 D5:0.25",
            # Final chord - the motion stops!
            "[D2:4,D3:4,F#3:4,A3:4,D4:4,F#4:4,A4:4,D5:4]:4",
        ]
    )

    print("⚙️ 'Perpetual Motion' - A Continuous Sixteenth Note Study ⚙️\n")
    print("=" * 60)
    print("Unbroken stream of 16th notes with slower bass support")
    print("=" * 60)
    print("\n🎵 Playing at 120 BPM...\n")

    result = piano(song, tempo=120)

    print(f"\n{result}")
    print("\n" + "=" * 60)
    print("✨ Perpetual Motion Features: ✨")
    print("  • Continuous sixteenth notes (0.25 beats) in melody")
    print("  • Flowing scalar passages and arpeggios")
    print("  • Slower, supportive bass (1.0-4.0 beat notes)")
    print("  • Hypnotic, mechanical beauty")
    print("  • Like clockwork or a music box that never stops")
    print("\n  The melody never rests until the final chord! ⚙️🎹")
    print("=" * 60)

    return result


if __name__ == "__main__":
    play_perpetual_motion()
