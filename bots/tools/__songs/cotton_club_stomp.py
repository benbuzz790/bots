"""
Cotton Club Stomp - A Classic Ragtime Composition

A proper ragtime piece with carefully composed bass and melody lines.

BASS LINE PATTERN (Classic stride/ragtime):
- Alternates between root notes (low) and chord (mid)
- "Oom-pah, oom-pah" rhythm
- Provides harmonic foundation and rhythmic drive

MELODY LINE:
- Syncopated (off-beat accents)
- Playful, bouncy character
- Call-and-response phrases
- Chromatic passing tones

FORM: Classic ragtime structure
- Intro (4 bars)
- A section (16 bars) - Main theme
- B section (16 bars) - Contrasting theme
- A section return (8 bars) - Main theme returns
- Coda (4 bars) - Big finish

Tempo: 120 BPM (Moderate ragtime tempo)
Duration: ~48 seconds
Key: F Major (bright and cheerful)
Style: Classic ragtime in the tradition of Scott Joplin
"""

import os
import sys

# Add parent directories to path to import beep module directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from tools.beep import piano


def play_cotton_club_stomp():
    """Play the Cotton Club Stomp composition."""

    # Let me think through the parts:
    #
    # BASS PATTERN in F major:
    # F (root) - F,A,C (chord) - F (root) - F,A,C (chord)
    # Then moves through: Bb, C7, F progression
    #
    # MELODY: Syncopated, playful, with characteristic ragtime "ragged" rhythm

    song = " ".join(
        [
            # INTRO: Establish the groove (8 beats)
            # Just bass and chords to set up the rhythm
            "[F2:1]:0.5 [F3,A3,C4]:0.5",  # Oom-pah
            "[F2:1]:0.5 [F3,A3,C4]:0.5",  # Oom-pah
            "[F2:1]:0.5 [F3,A3,C4]:0.5",  # Oom-pah
            "[F2:1]:0.5 [F3,A3,C4,F4:0.5]:0.5",  # With pickup note
            # A SECTION: Main ragtime theme (16 beats)
            # Bass + syncopated melody
            # Phrase 1: F major (4 beats)
            "[F2:1,A4:0.5]:0.5 [F3,A3,C4]:0.5",  # Syncopated melody on A
            "[F2:1,C5:0.5]:0.5 [F3,A3,C4]:0.5",  # Jump to C
            "[F2:1,A4:0.5]:0.5 [F3,A3,C4]:0.5",  # Back to A
            "[F2:1,F4:0.5]:0.5 [F3,A3,C4,G4:0.5]:0.5",  # Down to F, pickup G
            # Phrase 2: Bb major (4 beats)
            "[Bb2:1,A4:0.5]:0.5 [Bb3,D4,F4]:0.5",  # A over Bb
            "[Bb2:1,Bb4:0.5]:0.5 [Bb3,D4,F4]:0.5",  # Bb
            "[Bb2:1,D5:0.5]:0.5 [Bb3,D4,F4]:0.5",  # D up high
            "[Bb2:1,Bb4:0.5]:0.5 [Bb3,D4,F4,A4:0.5]:0.5",  # Bb, pickup A
            # Phrase 3: C7 (4 beats)
            "[C3:1,G4:0.5]:0.5 [C3,E3,Bb3]:0.5",  # G over C7
            "[C3:1,E4:0.5]:0.5 [C3,E3,Bb3]:0.5",  # E
            "[C3:1,G4:0.5]:0.5 [C3,E3,Bb3]:0.5",  # G again
            "[C3:1,Bb4:1]:0.5 [C3,E3,Bb3]:0.5",  # Bb sustained
            # Phrase 4: Back to F (4 beats)
            "[F2:1,A4:0.5]:0.5 [F3,A3,C4]:0.5",
            "[F2:1,C5:0.5]:0.5 [F3,A3,C4]:0.5",
            "[F2:1,F5:0.5]:0.5 [F3,A3,C4]:0.5",
            "[F2:1,C5:0.5]:0.5 [F3,A3,C4,A4:0.5]:0.5",  # Pickup for B section
            # B SECTION: Contrasting theme (16 beats)
            # More chromatic, different character
            # Phrase 1: D minor (4 beats)
            "[D3:1,F4:0.5]:0.5 [D3,F3,A3]:0.5",
            "[D3:1,E4:0.5]:0.5 [D3,F3,A3]:0.5",
            "[D3:1,F4:0.5]:0.5 [D3,F3,A3]:0.5",
            "[D3:1,A4:0.5]:0.5 [D3,F3,A3,G4:0.5]:0.5",
            # Phrase 2: G7 (4 beats)
            "[G2:1,F4:0.5]:0.5 [G3,B3,D4]:0.5",
            "[G2:1,D4:0.5]:0.5 [G3,B3,D4]:0.5",
            "[G2:1,B3:0.5]:0.5 [G3,B3,D4]:0.5",
            "[G2:1,G3:0.5]:0.5 [G3,B3,D4,F4:0.5]:0.5",
            # Phrase 3: C7 (4 beats)
            "[C3:1,E4:0.5]:0.5 [C3,E3,Bb3]:0.5",
            "[C3:1,G4:0.5]:0.5 [C3,E3,Bb3]:0.5",
            "[C3:1,Bb4:0.5]:0.5 [C3,E3,Bb3]:0.5",
            "[C3:1,G4:0.5]:0.5 [C3,E3,Bb3,E4:0.5]:0.5",
            # Phrase 4: F major (4 beats)
            "[F2:1,F4:0.5]:0.5 [F3,A3,C4]:0.5",
            "[F2:1,A4:0.5]:0.5 [F3,A3,C4]:0.5",
            "[F2:1,C5:0.5]:0.5 [F3,A3,C4]:0.5",
            "[F2:1,F5:1]:0.5 [F3,A3,C4]:0.5",
            # A SECTION RETURN: Main theme comes back (8 beats)
            "[F2:1,A4:0.5]:0.5 [F3,A3,C4]:0.5",
            "[F2:1,C5:0.5]:0.5 [F3,A3,C4]:0.5",
            "[F2:1,A4:0.5]:0.5 [F3,A3,C4]:0.5",
            "[F2:1,F4:0.5]:0.5 [F3,A3,C4]:0.5",
            "[Bb2:1,D5:0.5]:0.5 [Bb3,D4,F4]:0.5",
            "[Bb2:1,Bb4:0.5]:0.5 [Bb3,D4,F4]:0.5",
            "[C3:1,G4:0.5]:0.5 [C3,E3,Bb3]:0.5",
            "[C3:1,E4:0.5]:0.5 [C3,E3,Bb3]:0.5",
            # CODA: Big finish! (8 beats)
            # Ascending run
            "[F2:1,F4:0.25]:0.25 [F3,A3,C4,A4:0.25]:0.25",
            "[F2:1,C5:0.25]:0.25 [F3,A3,C4,F5:0.25]:0.25",
            "[F2:1,A5:0.5]:0.5 [F3,A3,C4]:0.5",
            "[F2:1,C6:0.5]:0.5 [F3,A3,C4]:0.5",
            # Final chord - big and triumphant!
            "[F2:2,F3:2,A3:2,C4:2,F4:2,A4:2,C5:2,F5:2]:2",
        ]
    )

    print("🎩 'Cotton Club Stomp' - A Classic Ragtime Composition 🎩\n")
    print("=" * 60)
    print("Carefully crafted bass and melody in true ragtime style")
    print("=" * 60)
    print("\n🎵 Playing at a swinging 120 BPM...\n")

    result = piano(song, tempo=120)

    print(f"\n{result}")
    print("\n" + "=" * 60)
    print("✨ Ragtime Structure: ✨")
    print("  • Intro: Establishing the 'oom-pah' groove")
    print("  • A Section: Main syncopated theme in F major")
    print("  • B Section: Contrasting chromatic theme")
    print("  • A Return: Main theme comes back")
    print("  • Coda: Triumphant ascending finish")
    print("\n  Classic stride bass + syncopated melody = Pure ragtime! 🎹")
    print("=" * 60)

    return result


if __name__ == "__main__":
    play_cotton_club_stomp()
