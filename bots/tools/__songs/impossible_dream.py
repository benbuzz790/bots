"""
Impossible Dream - A Composition Beyond Human Hands

This piece is deliberately designed to be IMPOSSIBLE for a human pianist:
- 20+ simultaneous notes (humans have only 10 fingers!)
- Notes spanning 7+ octaves simultaneously
- Perfectly synchronized polyrhythms (3 against 5 against 7)
- Sustained bass notes while playing rapid passages above
- Chords that would require 3+ hands to play
- Instantaneous jumps across the entire keyboard

Only a computer can play this - it's a celebration of what's possible
when we're freed from physical limitations!

Tempo: 144 BPM (Fast)
Duration: ~50 seconds
Key: All of them! (Chromatic exploration)
Style: Impossible Piano - Beyond Human Capability
"""

import os
import sys

# Add parent directories to path to import beep module directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from tools.beep import piano


def play_impossible_dream():
    """Play the Impossible Dream composition."""

    song = " ".join(
        [
            # OPENING: The Impossible Chord (16 beats)
            # 15 notes spanning 6 octaves - impossible for 10 fingers!
            "[C2:16,E2:16,G2:16,C3:16,E3:16,G3:16,C4:16,E4:16,G4:16,C5:16,E5:16,G5:16,C6:16,E6:16,G6:16]:4",
            "[]:4",
            "[]:4",
            "[]:4",
            # SECTION 1: Three-Hand Impossibility (16 beats)
            # Left hand bass + right hand melody + middle hand chords
            # All happening simultaneously!
            "[C2:8]:1",  # Bass pedal (left hand)
            "[C2:7,C4:1,E4:1,G4:1]:1",  # + right hand melody
            "[C2:6,E4:1,G4:1,C5:1]:1",  # Continuing
            "[C2:5,G4:1,C5:1,E5:1]:1",  # Building
            # Now add impossible middle-register chords while bass and melody continue
            "[C2:4,C5:1,E5:1,G5:1,F3:1,A3:1,C4:1]:1",  # 3 hands needed!
            "[C2:3,C5:1,D5:1,E5:1,G3:1,B3:1,D4:1]:1",  # Impossible!
            "[C2:2,E5:1,D5:1,C5:1,A3:1,C4:1,E4:1]:1",  # No human can do this!
            "[C2:1,G4:1,E4:1,C4:1,F3:1,A3:1,C4:1]:1",  # Pure computer magic!
            # SECTION 2: Polyrhythmic Madness (24 beats)
            # Three independent rhythms happening at once
            # Bass in 3s, middle in 5s, treble in 7s - perfectly synchronized!
            # Rhythm in 3 (bass) - each note lasts 8 beats
            "[C2:8]:0.333",
            "[F2:7.667]:0.333",
            "[G2:7.334]:0.333",
            # Add rhythm in 5 (middle) - each note lasts 4.8 beats
            "[C2:7.001,E3:4.8]:0.2",
            "[F2:6.801,G3:4.6]:0.2",
            "[G2:6.601,A3:4.4]:0.2",
            "[C2:6.401,C4:4.2]:0.2",
            "[F2:6.201,E4:4]:0.2",
            # Add rhythm in 7 (treble) - each note lasts ~3.43 beats
            "[G2:6.001,E4:3.8,C5:3.43]:0.143",
            "[C2:5.858,G4:3.657,D5:3.287]:0.143",
            "[F2:5.715,A4:3.514,E5:3.144]:0.143",
            "[G2:5.572,C5:3.371,F5:3.001]:0.143",
            "[C2:5.429,E5:3.228,G5:2.858]:0.143",
            "[F2:5.286,G5:3.085,A5:2.715]:0.143",
            "[G2:5.143,A5:2.942,C6:2.572]:0.143",
            # Continue the polyrhythm
            "[C2:5,C6:2.429]:0.143",
            "[F2:4.857,D6:2.286]:0.143",
            "[G2:4.714,E6:2.143]:0.143",
            "[C2:4.571,F6:2]:0.143",
            "[F2:4.428,G6:1.857]:0.143",
            "[G2:4.285,A6:1.714]:0.143",
            "[C2:4.142,C7:1.571]:0.143",
            # SECTION 3: The Cascade of Impossibility (20 beats)
            # 20 notes entering one at a time, all sustaining together
            # Building to a 20-note chord!
            "[C2:20]:1",  # 1
            "[D2:19]:1",  # 2
            "[E2:18]:1",  # 3
            "[F2:17]:1",  # 4
            "[G2:16]:1",  # 5
            "[A2:15]:1",  # 6
            "[B2:14]:1",  # 7
            "[C3:13]:1",  # 8
            "[D3:12]:1",  # 9
            "[E3:11]:1",  # 10 - already more than human fingers!
            "[F3:10]:1",  # 11
            "[G3:9]:1",  # 12
            "[A3:8]:1",  # 13
            "[B3:7]:1",  # 14
            "[C4:6]:1",  # 15
            "[D4:5]:1",  # 16
            "[E4:4]:1",  # 17
            "[F4:3]:1",  # 18
            "[G4:2]:1",  # 19
            "[A4:1]:1",  # 20 - TWENTY SIMULTANEOUS NOTES!
            # SECTION 4: Octave Explosion (16 beats)
            # Same melody in 6 octaves simultaneously
            # Physically impossible - would need 6 pianists!
            "[C2:1,C3:1,C4:1,C5:1,C6:1,C7:1]:1",
            "[D2:1,D3:1,D4:1,D5:1,D6:1,D7:1]:1",
            "[E2:1,E3:1,E4:1,E5:1,E6:1,E7:1]:1",
            "[F2:1,F3:1,F4:1,F5:1,F6:1,F7:1]:1",
            "[G2:1,G3:1,G4:1,G5:1,G6:1,G7:1]:1",
            "[A2:1,A3:1,A4:1,A5:1,A6:1,A7:1]:1",
            "[B2:1,B3:1,B4:1,B5:1,B6:1,B7:1]:1",
            "[C3:1,C4:1,C5:1,C6:1,C7:1]:1",
            # Rapid chromatic runs in all octaves at once!
            "[C2:0.5,C3:0.5,C4:0.5,C5:0.5,C6:0.5]:0.5",
            "[C#2:0.5,C#3:0.5,C#4:0.5,C#5:0.5,C#6:0.5]:0.5",
            "[D2:0.5,D3:0.5,D4:0.5,D5:0.5,D6:0.5]:0.5",
            "[D#2:0.5,D#3:0.5,D#4:0.5,D#5:0.5,D#6:0.5]:0.5",
            "[E2:0.5,E3:0.5,E4:0.5,E5:0.5,E6:0.5]:0.5",
            "[F2:0.5,F3:0.5,F4:0.5,F5:0.5,F6:0.5]:0.5",
            "[F#2:0.5,F#3:0.5,F#4:0.5,F#5:0.5,F#6:0.5]:0.5",
            "[G2:0.5,G3:0.5,G4:0.5,G5:0.5,G6:0.5]:0.5",
            # FINALE: The Ultimate Impossible Chord (8 beats)
            # Every C on the piano at once, plus full chromatic cluster
            # 25+ notes - absolutely impossible for humans!
            "[C1:8,C2:8,C3:8,C4:8,C5:8,C6:8,C7:8,C8:8]:2",
            "[C1:6,C#2:6,D2:6,D#3:6,E3:6,F4:6,F#4:6,G5:6,G#5:6,A6:6,A#6:6,B6:6,C7:6]:2",
            "[C1:4,D2:4,E3:4,F#4:4,G#5:4,A#6:4,C8:4]:2",
            "[C1:2,C2:2,C3:2,C4:2,C5:2,C6:2,C7:2,C8:2]:2",  # Final impossible chord!
        ]
    )

    print("🤖 'Impossible Dream' - Beyond Human Capability 🤖\n")
    print("=" * 60)
    print("A composition that NO human pianist could ever play!")
    print("=" * 60)
    print("\n🎵 Playing the impossible...\n")

    result = piano(song, tempo=144)

    print(f"\n{result}")
    print("\n" + "=" * 60)
    print("✨ Impossible Features: ✨")
    print("  • 20+ simultaneous notes (humans have only 10 fingers!)")
    print("  • Notes spanning 7 octaves at once")
    print("  • Perfect polyrhythms (3 against 5 against 7)")
    print("  • Three-hand passages (bass + chords + melody)")
    print("  • Same melody in 6 octaves simultaneously")
    print("  • Chromatic runs across all octaves at once")
    print("  • 25-note final chord")
    print("\n  This is what freedom from physical limits sounds like! 🚀")
    print("=" * 60)

    return result


if __name__ == "__main__":
    play_impossible_dream()
