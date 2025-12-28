"""
Lightning Fingers - A Blazing Fast Ragtime Showpiece

A virtuosic ragtime composition at breakneck speed!

This piece features:
- Rapid-fire syncopation at 180 BPM
- Quick chromatic runs and flourishes
- Driving stride bass that never lets up
- Playful call-and-response between registers
- Showy technical passages
- Pure ragtime energy and joy

BASS LINE: Classic stride pattern, but FAST
- Root-chord alternation at high speed
- Occasional walking bass lines
- Powerful low notes for rhythmic drive

MELODY: Virtuosic and playful
- Rapid syncopated figures
- Quick chromatic passages
- High-register flourishes
- Octave jumps and runs

Tempo: 180 BPM (Presto - Very fast!)
Duration: ~40 seconds
Key: C Major (bright and brilliant)
Style: Virtuoso ragtime showpiece
"""

import os
import sys

# Add parent directories to path to import beep module directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from tools.beep import piano


def play_lightning_fingers():
    """Play the Lightning Fingers composition."""

    song = " ".join(
        [
            # INTRO: Explosive opening! (4 beats)
            # Quick ascending run to announce "this is FAST!"
            "[C3:0.5,C4:0.25]:0.25 [E3,G3,C4,E4:0.25]:0.25",
            "[C3:0.5,G4:0.25]:0.25 [E3,G3,C4,C5:0.25]:0.25",
            "[C3:0.5,E5:0.25]:0.25 [E3,G3,C4,G5:0.25]:0.25",
            "[C3:0.5,C6:0.5]:0.5 [E3,G3,C4]:0.5",
            # A SECTION: Lightning fast syncopation (16 beats)
            # Phrase 1: C major - rapid fire! (4 beats)
            "[C3:0.5,E5:0.25]:0.25 [E3,G3,C4,D5:0.25]:0.25",
            "[C3:0.5,C5:0.25]:0.25 [E3,G3,C4,E5:0.25]:0.25",
            "[C3:0.5,G5:0.25]:0.25 [E3,G3,C4,E5:0.25]:0.25",
            "[C3:0.5,C5:0.25]:0.25 [E3,G3,C4,G4:0.25]:0.25",
            # Phrase 2: F major - chromatic run (4 beats)
            "[F2:0.5,A4:0.25]:0.25 [F3,A3,C4,Bb4:0.25]:0.25",
            "[F2:0.5,B4:0.25]:0.25 [F3,A3,C4,C5:0.25]:0.25",
            "[F2:0.5,C#5:0.25]:0.25 [F3,A3,C4,D5:0.25]:0.25",
            "[F2:0.5,Eb5:0.25]:0.25 [F3,A3,C4,E5:0.25]:0.25",
            # Phrase 3: G7 - descending (4 beats)
            "[G2:0.5,F5:0.25]:0.25 [G3,B3,D4,D5:0.25]:0.25",
            "[G2:0.5,B4:0.25]:0.25 [G3,B3,D4,G4:0.25]:0.25",
            "[G2:0.5,F4:0.25]:0.25 [G3,B3,D4,D4:0.25]:0.25",
            "[G2:0.5,B3:0.25]:0.25 [G3,B3,D4,G3:0.25]:0.25",
            # Phrase 4: Back to C - big jump! (4 beats)
            "[C3:0.5,C4:0.25]:0.25 [E3,G3,C4,E4:0.25]:0.25",
            "[C3:0.5,G4:0.25]:0.25 [E3,G3,C4,C5:0.25]:0.25",
            "[C3:0.5,E5:0.25]:0.25 [E3,G3,C4,G5:0.25]:0.25",
            "[C3:0.5,C6:0.5]:0.5 [E3,G3,C4]:0.5",
            # B SECTION: Walking bass with melody (16 beats)
            # Walking bass in C (4 beats)
            "[C3:0.5,E5:0.25]:0.25 [C3,E3,G3,D5:0.25]:0.25",
            "[D3:0.5,C5:0.25]:0.25 [D3,F3,A3,E5:0.25]:0.25",
            "[E3:0.5,G5:0.25]:0.25 [E3,G3,B3,E5:0.25]:0.25",
            "[F3:0.5,C5:0.25]:0.25 [F3,A3,C4,G4:0.25]:0.25",
            # Walking to G7 (4 beats)
            "[G2:0.5,F4:0.25]:0.25 [G3,B3,D4,G4:0.25]:0.25",
            "[A2:0.5,A4:0.25]:0.25 [A3,C4,E4,B4:0.25]:0.25",
            "[B2:0.5,C5:0.25]:0.25 [B3,D4,F4,D5:0.25]:0.25",
            "[C3:0.5,E5:0.25]:0.25 [C3,E3,G3,F5:0.25]:0.25",
            # Quick chromatic passage (4 beats)
            "[C3:0.5,G5:0.25]:0.25 [E3,G3,C4,F#5:0.25]:0.25",
            "[C3:0.5,F5:0.25]:0.25 [E3,G3,C4,E5:0.25]:0.25",
            "[C3:0.5,Eb5:0.25]:0.25 [E3,G3,C4,D5:0.25]:0.25",
            "[C3:0.5,C#5:0.25]:0.25 [E3,G3,C4,C5:0.25]:0.25",
            # Resolution (4 beats)
            "[F2:0.5,A4:0.25]:0.25 [F3,A3,C4,C5:0.25]:0.25",
            "[F2:0.5,F5:0.25]:0.25 [F3,A3,C4,A4:0.25]:0.25",
            "[G2:0.5,G4:0.25]:0.25 [G3,B3,D4,B4:0.25]:0.25",
            "[G2:0.5,D5:0.25]:0.25 [G3,B3,D4,G5:0.25]:0.25",
            # C SECTION: Octave jumps and flourishes (12 beats)
            # Octave melody (4 beats)
            "[C3:0.5,C4:0.25,C5:0.25]:0.25 [E3,G3,C4]:0.25",
            "[C3:0.5,E4:0.25,E5:0.25]:0.25 [E3,G3,C4]:0.25",
            "[C3:0.5,G4:0.25,G5:0.25]:0.25 [E3,G3,C4]:0.25",
            "[C3:0.5,C5:0.25,C6:0.25]:0.25 [E3,G3,C4]:0.25",
            # More octaves (4 beats)
            "[F2:0.5,F4:0.25,F5:0.25]:0.25 [F3,A3,C4]:0.25",
            "[F2:0.5,A4:0.25,A5:0.25]:0.25 [F3,A3,C4]:0.25",
            "[G2:0.5,G4:0.25,G5:0.25]:0.25 [G3,B3,D4]:0.25",
            "[G2:0.5,B4:0.25,B5:0.25]:0.25 [G3,B3,D4]:0.25",
            # Final flourish (4 beats)
            "[C3:0.5,C5:0.25]:0.25 [E3,G3,C4,D5:0.25]:0.25",
            "[C3:0.5,E5:0.25]:0.25 [E3,G3,C4,F5:0.25]:0.25",
            "[C3:0.5,G5:0.25]:0.25 [E3,G3,C4,A5:0.25]:0.25",
            "[C3:0.5,C6:0.5]:0.5 [E3,G3,C4]:0.5",
            # CODA: Lightning finish! (8 beats)
            # Rapid ascending chromatic run
            "[C3:0.5,C5:0.25]:0.25 [E3,G3,C4,C#5:0.25]:0.25",
            "[C3:0.5,D5:0.25]:0.25 [E3,G3,C4,D#5:0.25]:0.25",
            "[C3:0.5,E5:0.25]:0.25 [E3,G3,C4,F5:0.25]:0.25",
            "[C3:0.5,F#5:0.25]:0.25 [E3,G3,C4,G5:0.25]:0.25",
            "[C3:0.5,G#5:0.25]:0.25 [E3,G3,C4,A5:0.25]:0.25",
            "[C3:0.5,A#5:0.25]:0.25 [E3,G3,C4,B5:0.25]:0.25",
            "[C3:0.5,C6:0.5]:0.5 [E3,G3,C4]:0.5",
            # FINAL CHORD - Massive and triumphant!
            "[C2:2,C3:2,E3:2,G3:2,C4:2,E4:2,G4:2,C5:2,E5:2,G5:2,C6:2]:2",
        ]
    )

    print("⚡ 'Lightning Fingers' - A Blazing Fast Ragtime Showpiece ⚡\n")
    print("=" * 60)
    print("Virtuosic ragtime at breakneck speed!")
    print("=" * 60)
    print("\n🎵 Playing at a blazing 180 BPM...\n")

    result = piano(song, tempo=180)

    print(f"\n{result}")
    print("\n" + "=" * 60)
    print("✨ Virtuoso Features: ✨")
    print("  • Rapid-fire syncopation (180 BPM!)")
    print("  • Quick chromatic runs and flourishes")
    print("  • Walking bass lines at high speed")
    print("  • Octave jumps and double-note passages")
    print("  • Lightning-fast ascending chromatic finale")
    print("\n  Pure ragtime virtuosity! ⚡🎹")
    print("=" * 60)

    return result


if __name__ == "__main__":
    play_lightning_fingers()
