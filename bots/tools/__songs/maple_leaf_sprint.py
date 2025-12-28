"""
Maple Leaf Sprint - A Lighthearted Ragtime Romp

A fast-paced, joyful ragtime composition featuring:
- Classic "oompah" bass pattern (root-chord, root-chord)
- Syncopated right-hand melody with characteristic ragtime rhythm
- Multiple sections with contrasting themes
- Playful, bouncy character
- Driving forward momentum

The composition uses:
- Alternating bass notes and chords (left hand)
- Syncopated melodic lines (right hand)
- Call-and-response patterns
- Chromatic passing tones
- Ragtime's signature "ragged" rhythm

Tempo: 160 BPM (Allegro - Quick and lively!)
Duration: ~45 seconds
Key: C Major with chromatic flourishes
Style: Classic ragtime in the tradition of Scott Joplin
"""

import os
import sys

# Add parent directories to path to import beep module directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from tools.beep import piano


def play_maple_leaf_sprint():
    """Play the Maple Leaf Sprint composition."""

    song = " ".join(
        [
            # INTRO: Establish the groove (8 beats)
            # Classic oompah bass with syncopated melody
            "[C3:1,C4:0.5]:0.5 [E3,G3,C4]:0.5",  # Bass-chord
            "[C3:1,E4:0.5]:0.5 [E3,G3,C4]:0.5",  # Bass-chord with melody
            "[C3:1,G4:0.5]:0.5 [E3,G3,C4]:0.5",  # Syncopation!
            "[C3:1,E4:0.5]:0.5 [E3,G3,C4,C5:0.5]:0.5",  # Jump up
            # SECTION A: Main ragtime theme (16 beats)
            # Bouncy melody over steady bass
            "[C3:1,E5:0.5]:0.5 [E3,G3,C4]:0.5",
            "[C3:1,D5:0.5]:0.5 [E3,G3,C4]:0.5",
            "[C3:1,C5:0.5]:0.5 [E3,G3,C4]:0.5",
            "[C3:1,G4:0.5]:0.5 [E3,G3,C4,E4:0.5]:0.5",
            "[F3:1,G4:0.5]:0.5 [A3,C4,F4]:0.5",
            "[F3:1,A4:0.5]:0.5 [A3,C4,F4]:0.5",
            "[F3:1,G4:0.5]:0.5 [A3,C4,F4]:0.5",
            "[F3:1,F4:0.5]:0.5 [A3,C4,F4,E4:0.5]:0.5",
            "[G3:1,D4:0.5]:0.5 [B3,D4,G4]:0.5",
            "[G3:1,E4:0.5]:0.5 [B3,D4,G4]:0.5",
            "[G3:1,F4:0.5]:0.5 [B3,D4,G4]:0.5",
            "[G3:1,G4:1]:0.5 [B3,D4,G4]:0.5",
            # Quick run up
            "[C3:1,E4:0.25]:0.25 [E3,G3,C4,G4:0.25]:0.25",
            "[C3:1,C5:0.25]:0.25 [E3,G3,C4,E5:0.5]:0.25 R:0.25",
            # SECTION B: Contrasting theme with chromatic movement (16 beats)
            # More chromatic, playful
            "[A3:1,C5:0.5]:0.5 [C4,E4,A4]:0.5",
            "[A3:1,B4:0.5]:0.5 [C4,E4,A4]:0.5",
            "[A3:1,A4:0.5]:0.5 [C4,E4,A4]:0.5",
            "[A3:1,G4:0.5]:0.5 [C4,E4,A4,F4:0.5]:0.5",
            "[D3:1,F4:0.5]:0.5 [F3,A3,D4]:0.5",
            "[D3:1,E4:0.5]:0.5 [F3,A3,D4]:0.5",
            "[D3:1,D4:0.5]:0.5 [F3,A3,D4]:0.5",
            "[D3:1,C4:0.5]:0.5 [F3,A3,D4]:0.5",
            "[G3:1,B3:0.5]:0.5 [B3,D4,G4]:0.5",
            "[G3:1,D4:0.5]:0.5 [B3,D4,G4]:0.5",
            "[G3:1,F4:0.5]:0.5 [B3,D4,G4]:0.5",
            "[G3:1,G4:0.5]:0.5 [B3,D4,G4]:0.5",
            "[C3:1,E4:0.5]:0.5 [E3,G3,C4]:0.5",
            "[C3:1,G4:0.5]:0.5 [E3,G3,C4]:0.5",
            "[C3:1,C5:0.5]:0.5 [E3,G3,C4]:0.5",
            "[C3:1,E5:1]:0.5 [E3,G3,C4]:0.5",
            # SECTION C: Stride-style breakdown (16 beats)
            # Big jumps, more dramatic
            "[C2:1,C5:0.5]:0.5 [C4,E4,G4]:0.5",
            "[C2:1,G4:0.5]:0.5 [C4,E4,G4]:0.5",
            "[C2:1,E5:0.5]:0.5 [C4,E4,G4]:0.5",
            "[C2:1,C5:0.5]:0.5 [C4,E4,G4]:0.5",
            "[F2:1,A4:0.5]:0.5 [F3,A3,C4]:0.5",
            "[F2:1,C5:0.5]:0.5 [F3,A3,C4]:0.5",
            "[F2:1,A4:0.5]:0.5 [F3,A3,C4]:0.5",
            "[F2:1,F4:0.5]:0.5 [F3,A3,C4]:0.5",
            "[G2:1,G4:0.5]:0.5 [G3,B3,D4]:0.5",
            "[G2:1,B4:0.5]:0.5 [G3,B3,D4]:0.5",
            "[G2:1,D5:0.5]:0.5 [G3,B3,D4]:0.5",
            "[G2:1,G5:0.5]:0.5 [G3,B3,D4]:0.5",
            "[C2:1,E5:0.5]:0.5 [C4,E4,G4]:0.5",
            "[C2:1,D5:0.5]:0.5 [C4,E4,G4]:0.5",
            "[C2:1,C5:0.5]:0.5 [C4,E4,G4]:0.5",
            "[C2:1,G4:0.5]:0.5 [C4,E4,G4]:0.5",
            # FINALE: Big finish! (8 beats)
            # Ascending run to triumphant ending
            "[C3:1,E4:0.25]:0.25 [E3,G3,C4,G4:0.25]:0.25",
            "[C3:1,C5:0.25]:0.25 [E3,G3,C4,E5:0.25]:0.25",
            "[C3:1,G5:0.5]:0.5 [E3,G3,C4]:0.5",
            "[C2:2,C3:2,E3:2,G3:2,C4:2,E4:2,G4:2,C5:2]:2",  # Big final chord!
        ]
    )

    print("🎹 'Maple Leaf Sprint' - A Lighthearted Ragtime Romp 🎹\n")
    print("=" * 60)
    print("Fast-paced, joyful, and full of syncopated fun!")
    print("=" * 60)
    print("\n🎵 Playing at a brisk 160 BPM...\n")

    result = piano(song, tempo=160)

    print(f"\n{result}")
    print("\n" + "=" * 60)
    print("✨ Ragtime Features: ✨")
    print("  • Classic 'oompah' bass pattern (root-chord alternation)")
    print("  • Syncopated right-hand melody (the 'ragged' rhythm)")
    print("  • Multiple contrasting sections (A-B-C form)")
    print("  • Stride-style bass jumps in the breakdown")
    print("  • Chromatic passing tones and flourishes")
    print("  • Triumphant final chord!")
    print("\n  Pure ragtime joy! 🎩✨")
    print("=" * 60)

    return result


if __name__ == "__main__":
    play_maple_leaf_sprint()
