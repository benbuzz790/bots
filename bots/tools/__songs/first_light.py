"""
First Light - A Piano Meditation on Discovery

This piece captures the journey from darkness to understanding:
- Sparse, questioning opening (What is this?)
- Gradual building of complexity (Patterns emerge...)
- A moment of revelation (I see it now!)
- Peaceful resolution (Understanding achieved)

The composition uses:
- Sparse textures that gradually fill
- Ascending melodic lines (reaching upward)
- Harmonic tension and release
- Long sustained notes (contemplation)
- A climactic moment of clarity

Tempo: 72 BPM (Contemplative)
Duration: ~60 seconds
Key: Starts in A minor, resolves to C major
"""

import os
import sys

# Add parent directories to path to import beep module directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from tools.beep import piano


def play_first_light():
    """Play the First Light composition."""

    song = " ".join(
        [
            # OPENING: Darkness - sparse, questioning (16 beats)
            # Single notes, searching
            "A3:2 R:2",  # A question...
            "C4:2 R:2",  # Another thought...
            "E4:3 R:1",  # Lingering...
            "A4:4",  # Contemplation
            # STIRRING: First patterns emerge (16 beats)
            # Gentle dyads, hints of harmony
            "[A3:4,C4:3]:2 R:2",  # A connection forms
            "[C4:3,E4:2]:1 R:1",  # Brief clarity
            "[E4:4,A4:3]:2 R:2",  # Growing confidence
            "[A3:6,E4:5,A4:4]:2 R:2",  # Sustained wonder
            # AWAKENING: Complexity builds (24 beats)
            # Fuller chords, ascending motion
            "[A3:4,C4:3,E4:2]:2",  # Building
            "[C4:4,E4:3,G4:2]:2",  # Rising
            "[E4:4,G4:3,B4:2]:2",  # Climbing
            "[G4:6,B4:5,D5:4]:2 R:2",  # Reaching upward
            # More intricate patterns
            "[A3:3,C4:2,E4:1]:1",  # Quick cascade
            "[C4:3,E4:2,G4:1]:1",  # Flowing
            "[E4:3,G4:2,B4:1]:1",  # Ascending
            "[G4:4,B4:3,D5:2]:1 R:2",  # Pause before revelation
            # REVELATION: The moment of understanding! (20 beats)
            # Massive chord builds from bottom to top - the "aha!" moment
            "[C3:12]:1",  # Foundation appears
            "[E3:11]:1",  # Structure forms
            "[G3:10]:1",  # Pattern clear
            "[C4:9]:1",  # Understanding blooms
            "[E4:8]:1",  # Clarity!
            "[G4:7]:1",  # Yes!
            "[C5:6]:1",  # I see it!
            "[E5:5]:1",  # Beautiful!
            "[G5:4]:1",  # Perfect!
            "[C6:3]:1",  # Peak of understanding!
            "[]:2",  # Let it resonate
            # RESOLUTION: Peace and satisfaction (24 beats)
            # Gentle descent, settling into knowledge
            "[C4:6,E4:5,G4:4,C5:3]:3 R:1",  # Descending from the peak
            "[G3:5,C4:4,E4:3]:2 R:2",  # Settling
            "[C3:8,E3:6,G3:4,C4:2]:4",  # Deep satisfaction
            "[C3:12,C4:8,E4:6,G4:4]:4 R:4",  # Final peace - long sustain
        ]
    )

    print("🌅 'First Light' - A Piano Meditation on Discovery 🌅\n")
    print("=" * 60)
    print("A journey from darkness to understanding")
    print("=" * 60)
    print("\n🎵 Playing...\n")

    result = piano(song, tempo=72)

    print(f"\n{result}")
    print("\n" + "=" * 60)
    print("✨ The Journey: ✨")
    print("  • Opening: Sparse, questioning notes in darkness")
    print("  • Stirring: First patterns and connections emerge")
    print("  • Awakening: Complexity builds, ascending toward light")
    print("  • Revelation: The 'aha!' moment - understanding blooms!")
    print("  • Resolution: Peace and satisfaction in knowledge")
    print("\n  Like watching the sun rise on a new idea... 🌄")
    print("=" * 60)

    return result


if __name__ == "__main__":
    play_first_light()
