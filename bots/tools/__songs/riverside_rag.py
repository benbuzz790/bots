"""
Riverside Rag - A Well-Structured Ragtime Composition

A proper ragtime piece with fully developed sections and longer phrases.

STRUCTURE (Classic ragtime form):
- Intro: 8 bars (16 beats)
- A Section: 16 bars (32 beats) - Main theme, repeated
- B Section: 16 bars (32 beats) - Contrasting theme
- A Section: 8 bars (16 beats) - Return of main theme
- Trio (C Section): 16 bars (32 beats) - New key, lyrical
- D Section: 16 bars (32 beats) - Final theme, triumphant
- Coda: 8 bars (16 beats) - Grand finish

Each phrase is 4 bars (8 beats) minimum, giving melodies room to develop.

Tempo: 140 BPM (Allegro - Lively but not rushed)
Duration: ~90 seconds
Key: G Major → C Major (trio)
Style: Classic multi-section ragtime
"""

import os
import sys

# Add parent directories to path to import beep module directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from tools.beep import piano


def play_riverside_rag():
    """Play the Riverside Rag composition."""

    song = " ".join(
        [
            # INTRO: Setting the scene (16 beats)
            # Establish G major and the ragtime groove
            "[G2:1]:0.5 [G3,B3,D4]:0.5",
            "[G2:1]:0.5 [G3,B3,D4]:0.5",
            "[G2:1]:0.5 [G3,B3,D4]:0.5",
            "[G2:1]:0.5 [G3,B3,D4]:0.5",
            "[C3:1]:0.5 [C3,E3,G3]:0.5",
            "[C3:1]:0.5 [C3,E3,G3]:0.5",
            "[D3:1]:0.5 [D3,F#3,A3]:0.5",
            "[D3:1]:0.5 [D3,F#3,A3,C4:0.5]:0.5",  # Pickup
            "[G2:1,B4:1]:0.5 [G3,B3,D4]:0.5",
            "[G2:1,D5:1]:0.5 [G3,B3,D4]:0.5",
            "[G2:1,G5:1]:0.5 [G3,B3,D4]:0.5",
            "[G2:1,B5:1]:0.5 [G3,B3,D4]:0.5",
            "[G2:1,D6:1]:0.5 [G3,B3,D4]:0.5",
            "[G2:1,B5:1]:0.5 [G3,B3,D4]:0.5",
            "[G2:1,G5:1]:0.5 [G3,B3,D4]:0.5",
            "[G2:1,D5:0.5]:0.5 [G3,B3,D4,B4:0.5]:0.5",
            # A SECTION: Main theme (32 beats)
            # Phrase 1: G major melody (8 beats)
            "[G2:1,G4:1]:0.5 [G3,B3,D4]:0.5",
            "[G2:1,B4:0.5]:0.5 [G3,B3,D4,D5:0.5]:0.5",
            "[G2:1,G5:1]:0.5 [G3,B3,D4]:0.5",
            "[G2:1,D5:0.5]:0.5 [G3,B3,D4,B4:0.5]:0.5",
            "[G2:1,G4:1]:0.5 [G3,B3,D4]:0.5",
            "[G2:1,A4:0.5]:0.5 [G3,B3,D4,B4:0.5]:0.5",
            "[G2:1,D5:1]:0.5 [G3,B3,D4]:0.5",
            "[G2:1,B4:1]:0.5 [G3,B3,D4]:0.5",
            # Phrase 2: C major response (8 beats)
            "[C3:1,C5:1]:0.5 [C3,E3,G3]:0.5",
            "[C3:1,E5:0.5]:0.5 [C3,E3,G3,G5:0.5]:0.5",
            "[C3:1,C6:1]:0.5 [C3,E3,G3]:0.5",
            "[C3:1,G5:0.5]:0.5 [C3,E3,G3,E5:0.5]:0.5",
            "[C3:1,C5:1]:0.5 [C3,E3,G3]:0.5",
            "[C3:1,E5:0.5]:0.5 [C3,E3,G3,G5:0.5]:0.5",
            "[C3:1,E5:1]:0.5 [C3,E3,G3]:0.5",
            "[C3:1,C5:1]:0.5 [C3,E3,G3]:0.5",
            # Phrase 3: D7 to G (8 beats)
            "[D3:1,D5:1]:0.5 [D3,F#3,C4]:0.5",
            "[D3:1,F#5:0.5]:0.5 [D3,F#3,C4,A5:0.5]:0.5",
            "[D3:1,C6:1]:0.5 [D3,F#3,C4]:0.5",
            "[D3:1,A5:0.5]:0.5 [D3,F#3,C4,F#5:0.5]:0.5",
            "[G2:1,G5:1]:0.5 [G3,B3,D4]:0.5",
            "[G2:1,D5:0.5]:0.5 [G3,B3,D4,B4:0.5]:0.5",
            "[G2:1,G4:1]:0.5 [G3,B3,D4]:0.5",
            "[G2:1,B4:0.5]:0.5 [G3,B3,D4,D5:0.5]:0.5",
            # Phrase 4: Closing phrase (8 beats)
            "[G2:1,G5:1]:0.5 [G3,B3,D4]:0.5",
            "[G2:1,F#5:1]:0.5 [G3,B3,D4]:0.5",
            "[G2:1,E5:1]:0.5 [G3,B3,D4]:0.5",
            "[G2:1,D5:1]:0.5 [G3,B3,D4]:0.5",
            "[C3:1,C5:1]:0.5 [C3,E3,G3]:0.5",
            "[D3:1,B4:1]:0.5 [D3,F#3,A3]:0.5",
            "[G2:1,G4:1]:0.5 [G3,B3,D4]:0.5",
            "[G2:1,D4:0.5]:0.5 [G3,B3,D4,B3:0.5]:0.5",
            # B SECTION: Contrasting theme (32 beats)
            # More chromatic, different character
            # Phrase 1: E minor (8 beats)
            "[E3:1,E4:1]:0.5 [E3,G3,B3]:0.5",
            "[E3:1,G4:0.5]:0.5 [E3,G3,B3,B4:0.5]:0.5",
            "[E3:1,E5:1]:0.5 [E3,G3,B3]:0.5",
            "[E3:1,B4:0.5]:0.5 [E3,G3,B3,G4:0.5]:0.5",
            "[E3:1,E4:1]:0.5 [E3,G3,B3]:0.5",
            "[E3:1,F#4:0.5]:0.5 [E3,G3,B3,G4:0.5]:0.5",
            "[E3:1,B4:1]:0.5 [E3,G3,B3]:0.5",
            "[E3:1,E5:1]:0.5 [E3,G3,B3]:0.5",
            # Phrase 2: A7 (8 beats)
            "[A2:1,A4:1]:0.5 [A3,C#4,G4]:0.5",
            "[A2:1,C#5:0.5]:0.5 [A3,C#4,G4,E5:0.5]:0.5",
            "[A2:1,G5:1]:0.5 [A3,C#4,G4]:0.5",
            "[A2:1,E5:0.5]:0.5 [A3,C#4,G4,C#5:0.5]:0.5",
            "[A2:1,A4:1]:0.5 [A3,C#4,G4]:0.5",
            "[A2:1,C#5:0.5]:0.5 [A3,C#4,G4,E5:0.5]:0.5",
            "[A2:1,G5:1]:0.5 [A3,C#4,G4]:0.5",
            "[A2:1,A5:1]:0.5 [A3,C#4,G4]:0.5",
            # Phrase 3: D major (8 beats)
            "[D3:1,D5:1]:0.5 [D3,F#3,A3]:0.5",
            "[D3:1,F#5:0.5]:0.5 [D3,F#3,A3,A5:0.5]:0.5",
            "[D3:1,D6:1]:0.5 [D3,F#3,A3]:0.5",
            "[D3:1,A5:0.5]:0.5 [D3,F#3,A3,F#5:0.5]:0.5",
            "[D3:1,D5:1]:0.5 [D3,F#3,A3]:0.5",
            "[D3:1,C#5:1]:0.5 [D3,F#3,A3]:0.5",
            "[D3:1,B4:1]:0.5 [D3,F#3,A3]:0.5",
            "[D3:1,A4:1]:0.5 [D3,F#3,A3]:0.5",
            # Phrase 4: Back to G (8 beats)
            "[G2:1,G4:1]:0.5 [G3,B3,D4]:0.5",
            "[G2:1,A4:0.5]:0.5 [G3,B3,D4,B4:0.5]:0.5",
            "[G2:1,D5:1]:0.5 [G3,B3,D4]:0.5",
            "[G2:1,G5:1]:0.5 [G3,B3,D4]:0.5",
            "[C3:1,E5:1]:0.5 [C3,E3,G3]:0.5",
            "[D3:1,D5:1]:0.5 [D3,F#3,A3]:0.5",
            "[G2:1,B4:1]:0.5 [G3,B3,D4]:0.5",
            "[G2:1,G4:0.5]:0.5 [G3,B3,D4,D4:0.5]:0.5",
            # A SECTION RETURN: Main theme abbreviated (16 beats)
            "[G2:1,G4:1]:0.5 [G3,B3,D4]:0.5",
            "[G2:1,B4:0.5]:0.5 [G3,B3,D4,D5:0.5]:0.5",
            "[G2:1,G5:1]:0.5 [G3,B3,D4]:0.5",
            "[G2:1,D5:0.5]:0.5 [G3,B3,D4,B4:0.5]:0.5",
            "[C3:1,C5:1]:0.5 [C3,E3,G3]:0.5",
            "[C3:1,E5:0.5]:0.5 [C3,E3,G3,G5:0.5]:0.5",
            "[D3:1,F#5:1]:0.5 [D3,F#3,C4]:0.5",
            "[D3:1,A5:1]:0.5 [D3,F#3,C4]:0.5",
            "[G2:1,G5:1]:0.5 [G3,B3,D4]:0.5",
            "[G2:1,D5:1]:0.5 [G3,B3,D4]:0.5",
            "[G2:1,B4:1]:0.5 [G3,B3,D4]:0.5",
            "[G2:1,G4:1]:0.5 [G3,B3,D4]:0.5",
            "[C3:1,E4:1]:0.5 [C3,E3,G3]:0.5",
            "[D3:1,D4:1]:0.5 [D3,F#3,A3]:0.5",
            "[G2:1,G3:1]:0.5 [G3,B3,D4]:0.5",
            "[G2:1,B3:0.5]:0.5 [G3,B3,D4,D4:0.5]:0.5",
            # CODA: Grand finish (16 beats)
            # Big ascending run
            "[G2:1,G4:0.5]:0.5 [G3,B3,D4,B4:0.5]:0.5",
            "[G2:1,D5:0.5]:0.5 [G3,B3,D4,G5:0.5]:0.5",
            "[G2:1,B5:0.5]:0.5 [G3,B3,D4,D6:0.5]:0.5",
            "[G2:1,G6:1]:0.5 [G3,B3,D4]:0.5",
            "[C3:1,E6:1]:0.5 [C3,E3,G3]:0.5",
            "[C3:1,C6:1]:0.5 [C3,E3,G3]:0.5",
            "[D3:1,A5:1]:0.5 [D3,F#3,A3]:0.5",
            "[D3:1,F#5:1]:0.5 [D3,F#3,A3]:0.5",
            # Final massive chord!
            "[G1:2,G2:2,B2:2,D3:2,G3:2,B3:2,D4:2,G4:2,B4:2,D5:2,G5:2]:2",
        ]
    )

    print("🌊 'Riverside Rag' - A Well-Structured Ragtime Composition 🌊\n")
    print("=" * 60)
    print("Fully developed sections with longer, breathing phrases")
    print("=" * 60)
    print("\n🎵 Playing at 140 BPM...\n")

    result = piano(song, tempo=140)

    print(f"\n{result}")
    print("\n" + "=" * 60)
    print("✨ Classic Ragtime Structure: ✨")
    print("  • Intro: 16 beats - Setting the scene")
    print("  • A Section: 32 beats - Main theme (4 phrases)")
    print("  • B Section: 32 beats - Contrasting theme")
    print("  • A Return: 16 beats - Main theme returns")
    print("  • Coda: 16 beats - Grand ascending finish")
    print("\n  Each phrase gets 8 beats to develop and breathe! 🎹")
    print("=" * 60)

    return result


if __name__ == "__main__":
    play_riverside_rag()
