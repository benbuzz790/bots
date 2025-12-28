"""
Syncopation Station - A Highly Detailed Ragtime Composition

This piece uses fine rhythmic resolution (eighth and sixteenth notes)
to capture the true "ragged" syncopated feel of classic ragtime.

RHYTHMIC DETAIL:
- Quarter notes: 1.0
- Eighth notes: 0.5 (main subdivision)
- Sixteenth notes: 0.25 (for quick runs and ornaments)
- Dotted rhythms: 0.75 (for swing feel)

This creates the authentic ragtime "bounce" with:
- Syncopated melodies (notes between the beats)
- Quick grace notes and turns
- Swung eighth notes
- Precise rhythmic placement

Tempo: 130 BPM (Allegro moderato - Lively but controlled)
Duration: ~60 seconds
Key: Eb Major (warm and rich)
Style: Authentic syncopated ragtime
"""

import os
import sys

# Add parent directories to path to import beep module directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from tools.beep import piano


def play_syncopation_station():
    """Play the Syncopation Station composition."""

    song = " ".join(
        [
            # INTRO: Establishing the syncopated groove (8 beats)
            # Notice the off-beat accents!
            "[Eb2:0.5]:0.5 [Eb3,G3,Bb3]:0.5",
            "[Eb2:0.5,Bb4:0.5]:0.5 [Eb3,G3,Bb3]:0.5",
            "[Eb2:0.5]:0.5 [Eb3,G3,Bb3,Eb5:0.5]:0.5",
            "[Eb2:0.5,G4:0.5]:0.5 [Eb3,G3,Bb3]:0.5",
            "[Ab2:0.5]:0.5 [Ab3,C4,Eb4]:0.5",
            "[Ab2:0.5,C5:0.5]:0.5 [Ab3,C4,Eb4]:0.5",
            "[Bb2:0.5]:0.5 [Bb3,D4,F4]:0.5",
            "[Bb2:0.5,D5:0.25]:0.25 [Bb3,D4,F4,Eb5:0.25]:0.25",  # Quick turn!
            # A SECTION: Main syncopated theme (32 beats)
            # Phrase 1: Eb major with detailed syncopation (8 beats)
            "[Eb2:0.5,Eb5:0.5]:0.5 [Eb3,G3,Bb3]:0.5",
            "[Eb2:0.5]:0.5 [Eb3,G3,Bb3,D5:0.25]:0.25 R:0.25",  # Syncopation!
            "[Eb2:0.5,Eb5:0.5]:0.5 [Eb3,G3,Bb3]:0.5",
            "[Eb2:0.5,G5:0.5]:0.5 [Eb3,G3,Bb3]:0.5",
            "[Eb2:0.5,Bb5:0.75]:0.5 [Eb3,G3,Bb3]:0.5",  # Dotted rhythm
            "[Eb2:0.5,G5:0.25]:0.25 [Eb3,G3,Bb3,Eb5:0.5]:0.25",
            "[Eb2:0.5,D5:0.5]:0.5 [Eb3,G3,Bb3]:0.5",
            "[Eb2:0.5,Eb5:0.25]:0.25 [Eb3,G3,Bb3,C5:0.25]:0.25",
            # Phrase 2: Ab major with sixteenth note runs (8 beats)
            "[Ab2:0.5,Bb4:0.5]:0.5 [Ab3,C4,Eb4]:0.5",
            "[Ab2:0.5,C5:0.25]:0.25 [Ab3,C4,Eb4,D5:0.25]:0.25",  # Quick run
            "[Ab2:0.5,Eb5:0.5]:0.5 [Ab3,C4,Eb4]:0.5",
            "[Ab2:0.5,Ab5:0.5]:0.5 [Ab3,C4,Eb4]:0.5",
            "[Ab2:0.5,C6:0.5]:0.5 [Ab3,C4,Eb4]:0.5",
            "[Ab2:0.5,Ab5:0.25]:0.25 [Ab3,C4,Eb4,G5:0.25]:0.25",
            "[Ab2:0.5,F5:0.5]:0.5 [Ab3,C4,Eb4]:0.5",
            "[Ab2:0.5,Eb5:0.25]:0.25 [Ab3,C4,Eb4,C5:0.25]:0.25",
            # Phrase 3: Bb7 with chromatic approach (8 beats)
            "[Bb2:0.5,D5:0.5]:0.5 [Bb3,D4,F4]:0.5",
            "[Bb2:0.5]:0.5 [Bb3,D4,F4,Eb5:0.25]:0.25 R:0.25",  # Syncopated!
            "[Bb2:0.5,D5:0.5]:0.5 [Bb3,D4,F4]:0.5",
            "[Bb2:0.5,F5:0.5]:0.5 [Bb3,D4,F4]:0.5",
            "[Bb2:0.5,Ab5:0.5]:0.5 [Bb3,D4,F4]:0.5",
            "[Bb2:0.5,G5:0.25]:0.25 [Bb3,D4,F4,F5:0.25]:0.25",  # Chromatic descent
            "[Bb2:0.5,E5:0.25]:0.25 [Bb3,D4,F4,Eb5:0.25]:0.25",
            "[Bb2:0.5,D5:0.25]:0.25 [Bb3,D4,F4,Db5:0.25]:0.25",
            # Phrase 4: Resolution to Eb (8 beats)
            "[Eb2:0.5,C5:0.5]:0.5 [Eb3,G3,Bb3]:0.5",
            "[Eb2:0.5,Bb4:0.5]:0.5 [Eb3,G3,Bb3]:0.5",
            "[Eb2:0.5,G4:0.5]:0.5 [Eb3,G3,Bb3]:0.5",
            "[Eb2:0.5,Eb4:0.5]:0.5 [Eb3,G3,Bb3]:0.5",
            "[Ab2:0.5,C5:0.5]:0.5 [Ab3,C4,Eb4]:0.5",
            "[Bb2:0.5,Bb4:0.5]:0.5 [Bb3,D4,F4]:0.5",
            "[Eb2:0.5,Eb5:0.5]:0.5 [Eb3,G3,Bb3]:0.5",
            "[Eb2:0.5,G4:0.25]:0.25 [Eb3,G3,Bb3,Bb4:0.25]:0.25",  # Pickup
            # B SECTION: Contrasting theme with more detail (32 beats)
            # Phrase 1: C minor (8 beats)
            "[C3:0.5,Eb5:0.5]:0.5 [C3,Eb3,G3]:0.5",
            "[C3:0.5,D5:0.25]:0.25 [C3,Eb3,G3,C5:0.25]:0.25",
            "[C3:0.5,Eb5:0.5]:0.5 [C3,Eb3,G3]:0.5",
            "[C3:0.5,G5:0.5]:0.5 [C3,Eb3,G3]:0.5",
            "[C3:0.5,C6:0.75]:0.5 [C3,Eb3,G3]:0.5",  # Dotted
            "[C3:0.5,G5:0.25]:0.25 [C3,Eb3,G3,Eb5:0.5]:0.25",
            "[C3:0.5,C5:0.5]:0.5 [C3,Eb3,G3]:0.5",
            "[C3:0.5,G4:0.25]:0.25 [C3,Eb3,G3,Eb4:0.25]:0.25",
            # Phrase 2: F7 (8 beats)
            "[F2:0.5,A4:0.5]:0.5 [F3,A3,Eb4]:0.5",
            "[F2:0.5,C5:0.25]:0.25 [F3,A3,Eb4,Eb5:0.25]:0.25",
            "[F2:0.5,F5:0.5]:0.5 [F3,A3,Eb4]:0.5",
            "[F2:0.5,A5:0.5]:0.5 [F3,A3,Eb4]:0.5",
            "[F2:0.5,C6:0.5]:0.5 [F3,A3,Eb4]:0.5",
            "[F2:0.5,A5:0.25]:0.25 [F3,A3,Eb4,F5:0.25]:0.25",
            "[F2:0.5,Eb5:0.25]:0.25 [F3,A3,Eb4,C5:0.25]:0.25",
            "[F2:0.5,A4:0.25]:0.25 [F3,A3,Eb4,F4:0.25]:0.25",
            # Phrase 3: Bb major (8 beats)
            "[Bb2:0.5,D5:0.5]:0.5 [Bb3,D4,F4]:0.5",
            "[Bb2:0.5]:0.5 [Bb3,D4,F4,F5:0.25]:0.25 R:0.25",
            "[Bb2:0.5,Bb5:0.5]:0.5 [Bb3,D4,F4]:0.5",
            "[Bb2:0.5,F5:0.5]:0.5 [Bb3,D4,F4]:0.5",
            "[Bb2:0.5,D5:0.5]:0.5 [Bb3,D4,F4]:0.5",
            "[Bb2:0.5,Bb4:0.25]:0.25 [Bb3,D4,F4,F4:0.25]:0.25",
            "[Bb2:0.5,D4:0.5]:0.5 [Bb3,D4,F4]:0.5",
            "[Bb2:0.5,F4:0.25]:0.25 [Bb3,D4,F4,Bb4:0.25]:0.25",
            # Phrase 4: Back to Eb (8 beats)
            "[Eb2:0.5,G4:0.5]:0.5 [Eb3,G3,Bb3]:0.5",
            "[Eb2:0.5,Bb4:0.25]:0.25 [Eb3,G3,Bb3,Eb5:0.25]:0.25",
            "[Eb2:0.5,G5:0.5]:0.5 [Eb3,G3,Bb3]:0.5",
            "[Eb2:0.5,Bb5:0.5]:0.5 [Eb3,G3,Bb3]:0.5",
            "[Ab2:0.5,C6:0.5]:0.5 [Ab3,C4,Eb4]:0.5",
            "[Bb2:0.5,Bb5:0.5]:0.5 [Bb3,D4,F4]:0.5",
            "[Eb2:0.5,Eb5:0.5]:0.5 [Eb3,G3,Bb3]:0.5",
            "[Eb2:0.5,Bb4:0.25]:0.25 [Eb3,G3,Bb3,G4:0.25]:0.25",
            # CODA: Detailed finish with runs (16 beats)
            # Quick ascending sixteenth note run (4 beats)
            "[Eb2:0.5,Eb4:0.25]:0.25 [Eb3,G3,Bb3,G4:0.25]:0.25",
            "[Eb2:0.5,Bb4:0.25]:0.25 [Eb3,G3,Bb3,Eb5:0.25]:0.25",
            "[Eb2:0.5,G5:0.25]:0.25 [Eb3,G3,Bb3,Bb5:0.25]:0.25",
            "[Eb2:0.5,Eb6:0.5]:0.5 [Eb3,G3,Bb3]:0.5",
            # Descending with syncopation (4 beats)
            "[Eb2:0.5,Bb5:0.5]:0.5 [Eb3,G3,Bb3]:0.5",
            "[Eb2:0.5]:0.5 [Eb3,G3,Bb3,G5:0.25]:0.25 R:0.25",
            "[Eb2:0.5,Eb5:0.5]:0.5 [Eb3,G3,Bb3]:0.5",
            "[Eb2:0.5,Bb4:0.25]:0.25 [Eb3,G3,Bb3,G4:0.25]:0.25",
            # Final cadence (8 beats)
            "[Ab2:0.5,C5:0.5]:0.5 [Ab3,C4,Eb4]:0.5",
            "[Ab2:0.5,Eb5:0.5]:0.5 [Ab3,C4,Eb4]:0.5",
            "[Bb2:0.5,D5:0.5]:0.5 [Bb3,D4,F4]:0.5",
            "[Bb2:0.5,F5:0.5]:0.5 [Bb3,D4,F4]:0.5",
            "[Eb2:0.5,Eb5:0.5]:0.5 [Eb3,G3,Bb3]:0.5",
            "[Eb2:0.5,Bb4:0.5]:0.5 [Eb3,G3,Bb3]:0.5",
            "[Eb2:0.5,G4:0.5]:0.5 [Eb3,G3,Bb3]:0.5",
            # Final chord with all the detail!
            "[Eb1:2,Eb2:2,G2:2,Bb2:2,Eb3:2,G3:2,Bb3:2,Eb4:2,G4:2,Bb4:2,Eb5:2]:2",
        ]
    )

    print("🎼 'Syncopation Station' - Highly Detailed Ragtime 🎼\n")
    print("=" * 60)
    print("Using eighth and sixteenth notes for authentic ragtime feel")
    print("=" * 60)
    print("\n🎵 Playing at 130 BPM...\n")

    result = piano(song, tempo=130)

    print(f"\n{result}")
    print("\n" + "=" * 60)
    print("✨ Rhythmic Detail: ✨")
    print("  • Eighth notes (0.5) for main syncopation")
    print("  • Sixteenth notes (0.25) for quick runs and turns")
    print("  • Dotted rhythms (0.75) for swing feel")
    print("  • Off-beat accents for true 'ragged' rhythm")
    print("  • Chromatic passing tones")
    print("\n  This is authentic ragtime syncopation! 🎹✨")
    print("=" * 60)

    return result


if __name__ == "__main__":
    play_syncopation_station()
