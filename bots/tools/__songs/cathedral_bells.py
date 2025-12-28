"""
Cathedral Bells - A Cascading Piano Composition

This piece showcases the advanced features of the piano() function:
- Cascading chords that build and release naturally
- Deep bass pedal tones that anchor the harmony
- Bell-like overtones that ring through multiple beats
- A climactic build to an 11-note chord
- Natural decay as notes fade one by one

Tempo: 90 BPM
Duration: ~48 seconds
Key: C Major/A Minor
"""

import os
import sys

# Add parent directories to path to import beep module directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from tools.beep import piano


def play_cathedral_bells():
    """Play the Cathedral Bells composition."""

    # Create the composition using advanced piano features
    song = " ".join(
        [
            # Opening: Rising C major chord (8 beats)
            # Each note enters one beat apart and sustains
            "[C4:8]:1 [E4:7]:1 [G4:6]:1 [C5:5]:1 []:1 []:1 []:1 []:1",
            # Rising A minor chord (8 beats)
            # Creates a darker, more mysterious color
            "[A3:8]:1 [C4:7]:1 [E4:6]:1 [A4:5]:1 []:1 []:1 []:1 []:1",
            # Rising F major chord (8 beats)
            # Warm and consonant
            "[F3:8]:1 [A3:7]:1 [C4:6]:1 [F4:5]:1 []:1 []:1 []:1 []:1",
            # Rising G major chord with longer sustain (8 beats)
            # Building tension toward the finale
            "[G3:8]:1 [B3:7]:1 [D4:6]:1 [G4:5]:1 []:1 []:1 []:1 []:1",
            # Big finale: C major with bass pedal tone (16 beats)
            # Massive 11-note chord builds from bottom to top
            "[C2:16]:1",  # Deep bass enters - foundation
            "[C3:15]:1",  # Bass octave - power
            "[E3:14]:1",  # Third - color
            "[G3:13]:1",  # Fifth - stability
            "[C4:12]:1",  # Middle C - center
            "[E4:11]:1",  # Third up - brightness
            "[G4:10]:1",  # Fifth up - fullness
            "[C5:9]:1",  # High C - clarity
            "[E5:8]:1",  # High third - sparkle
            "[G5:7]:1",  # High fifth - brilliance
            "[C6:6]:1",  # Very high C - peak of the cathedral!
            "[]:1 []:1 []:1 []:1 []:1",  # Let it all ring out majestically
        ]
    )

    print("🎹 'Cathedral Bells' - A Cascading Composition 🎹\n")
    print("=" * 60)
    print("Featuring cascading chords, pedal tones, and ringing bells")
    print("=" * 60)
    print("\n🎵 Playing...\n")

    result = piano(song, tempo=90)

    print(f"\n{result}")
    print("\n" + "=" * 60)
    print("✨ Musical Features: ✨")
    print("  • Cascading chords that build and release naturally")
    print("  • Deep bass pedal tones that anchor the harmony")
    print("  • Bell-like overtones that ring through multiple beats")
    print("  • A climactic build to an 11-note chord!")
    print("  • Natural decay as notes fade one by one")
    print("=" * 60)

    return result


if __name__ == "__main__":
    play_cathedral_bells()
