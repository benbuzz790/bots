"""
Beyond Reach - An Impossible Yet Beautiful Composition

This piece uses impossible techniques in service of musical expression:
- Sustained bass pedal tones through entire sections (one hand holding forever)
- Melody doubled in multiple octaves simultaneously (superhuman reach)
- Rich 12-15 note chords (more than 10 fingers)
- Cascading entries that build to impossible density

Unlike "Impossible Dream" which is pure spectacle, this piece uses
impossibility to create something hauntingly beautiful - like a music box
that never winds down, or a choir of pianos playing as one.

Tempo: 96 BPM (Andante - Walking pace, contemplative)
Duration: ~60 seconds
Key: E minor → E major (darkness to light)
Style: Impossible Beauty
"""

import os
import sys

# Add parent directories to path to import beep module directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from tools.beep import piano


def play_beyond_reach():
    """Play the Beyond Reach composition."""

    song = " ".join(
        [
            # OPENING: The Eternal Bass (16 beats)
            # A low E that will sustain for the ENTIRE piece (60+ beats!)
            # Impossible - no human can hold a note that long while playing above it
            "[E2:64]:1",  # The eternal foundation begins
            # Simple melody enters, doubled in 3 octaves
            # (Impossible - would need 6 hands)
            "[E3:2,E4:2,E5:2]:2",
            "[G3:2,G4:2,G5:2]:2",
            "[B3:2,B4:2,B5:2]:2",
            "[D4:2,D5:2,D6:2]:2",
            "[C4:2,C5:2,C6:2]:2",
            "[B3:2,B4:2,B5:2]:2",
            "[A3:2,A4:2,A5:2]:2",
            "[G3:2,G4:2,G5:2]:2",
            # DEVELOPMENT: Harmonic Richness (24 beats)
            # Add middle voices - building to 12-note chords
            # The bass E is STILL sustaining!
            # 6-note chords (melody in 3 octaves)
            "[E3:3,G3:3,E4:3,G4:3,E5:3,G5:3]:3",
            "[D3:3,F#3:3,D4:3,F#4:3,D5:3,F#5:3]:3",
            "[C3:3,E3:3,C4:3,E4:3,C5:3,E5:3]:3",
            "[B2:3,D3:3,B3:3,D4:3,B4:3,D5:3]:3",
            # 9-note chords (add inner harmonies)
            "[E3:2,G3:2,B3:2,E4:2,G4:2,B4:2,E5:2,G5:2,B5:2]:2",
            "[D3:2,F#3:2,A3:2,D4:2,F#4:2,A4:2,D5:2,F#5:2,A5:2]:2",
            "[C3:2,E3:2,G3:2,C4:2,E4:2,G4:2,C5:2,E5:2,G5:2]:2",
            "[B2:2,D3:2,F#3:2,B3:2,D4:2,F#4:2,B4:2,D5:2,F#5:2]:2",
            # 12-note chords (full impossibility!)
            "[E3:2,G3:2,B3:2,D4:2,E4:2,G4:2,B4:2,D5:2,E5:2,G5:2,B5:2,D6:2]:2",
            "[A2:2,C3:2,E3:2,G3:2,A3:2,C4:2,E4:2,G4:2,A4:2,C5:2,E5:2,G5:2]:2",
            # CLIMAX: Cascading Impossible Chord (16 beats)
            # 15 notes enter one by one, all sustaining
            # Like a cathedral organ with infinite sustain
            "[E3:16]:1",  # 1st voice
            "[G3:15]:1",  # 2nd voice
            "[B3:14]:1",  # 3rd voice
            "[D4:13]:1",  # 4th voice
            "[E4:12]:1",  # 5th voice
            "[G4:11]:1",  # 6th voice
            "[B4:10]:1",  # 7th voice
            "[D5:9]:1",  # 8th voice
            "[E5:8]:1",  # 9th voice
            "[G5:7]:1",  # 10th voice - more than human fingers!
            "[B5:6]:1",  # 11th voice
            "[D6:5]:1",  # 12th voice
            "[E6:4]:1",  # 13th voice
            "[G6:3]:1",  # 14th voice
            "[B6:2]:1",  # 15th voice - peak!
            "[]:1",  # Let it resonate
            # TRANSFORMATION: Minor to Major (16 beats)
            # The eternal bass E is STILL going!
            # Now we shift from E minor to E major
            # Gentle major chords, still in 3 octaves
            "[E3:3,G#3:3,E4:3,G#4:3,E5:3,G#5:3]:3",  # E major!
            "[B2:3,E3:3,B3:3,E4:3,B4:3,E5:3]:3",
            "[A2:3,C#3:3,A3:3,C#4:3,A4:3,C#5:3]:3",
            "[G#2:3,B2:3,G#3:3,B3:3,G#4:3,B4:3]:3",
            # Building to final impossible chord
            "[E3:4,G#3:4,B3:4,E4:4,G#4:4,B4:4,E5:4,G#5:4,B5:4]:4",
            # RESOLUTION: The Eternal Chord (8 beats)
            # Final 15-note E major chord with the eternal bass
            # Everything resolves into pure light
            "[E2:8,E3:8,G#3:8,B3:8,E4:8,G#4:8,B4:8,E5:8,G#5:8,B5:8,E6:8,G#6:8,B6:8]:8",
        ]
    )

    print("🌌 'Beyond Reach' - Impossible Yet Beautiful 🌌\n")
    print("=" * 60)
    print("Using impossibility in service of musical expression")
    print("=" * 60)
    print("\n🎵 Playing...\n")

    result = piano(song, tempo=96)

    print(f"\n{result}")
    print("\n" + "=" * 60)
    print("✨ The Journey: ✨")
    print("  • Opening: Eternal bass note (sustains entire piece)")
    print("  • Development: Melody in 3 octaves simultaneously")
    print("  • Climax: 15-note cascading chord (impossible density)")
    print("  • Transformation: Minor to major (darkness to light)")
    print("  • Resolution: Final 13-note chord of pure light")
    print("\n  Like a music box that never winds down,")
    print("  or a choir of pianos playing as one... 🎹✨")
    print("=" * 60)

    return result


if __name__ == "__main__":
    play_beyond_reach()
