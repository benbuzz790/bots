# 🎹 Piano Compositions

This folder contains example compositions that showcase the advanced features of the `piano()` function in `beep.py`.

## Available Compositions

### Cathedral Bells (`cathedral_bells.py`)

A cascading piano composition featuring:
- **Cascading chords** - Notes build up and fade out one by one
- **Deep bass pedal tones** - Low notes anchor the harmony
- **Bell-like overtones** - High notes ring through multiple beats
- **11-note climactic chord** - Massive finale spanning 4+ octaves
- **Natural decay** - Notes fade organically

**Duration:** ~48 seconds
**Tempo:** 90 BPM
**Key:** C Major/A Minor

**Usage:**
```python
from bots.tools.__songs.cathedral_bells import play_cathedral_bells

play_cathedral_bells()
```

Or run directly:
```bash
python bots/tools/__songs/cathedral_bells.py
```

## Piano Function Features

These compositions demonstrate the advanced capabilities of the `piano()` function:

### 1. Held Notes
Individual notes within a chord can have different durations:
```python
piano("[C4:2,E4:1,G4:3]")  # C for 2 beats, E for 1, G for 3
```

### 2. Time Advance
Notes can sustain while time moves forward:
```python
piano("[C3:50]:1")  # C3 sustains 50 beats, time advances 1 beat
```

### 3. Rests
Advance time without playing new notes:
```python
piano("[C4:8]:1 [E4:7]:1 []:6")  # Notes ring out during rests
```

### 4. Timeline-Based Mixing
All notes are mixed into a complete waveform before playback, enabling true polyphony with unlimited simultaneous notes.

## Creating Your Own Compositions

Feel free to add your own compositions to this folder! Follow the pattern:

1. Create a new `.py` file with your composition name
2. Import the `piano` function from `bots.tools.beep`
3. Create a `play_your_song()` function
4. Add documentation about the piece
5. Make it runnable with `if __name__ == "__main__":`

## Musical Notation Reference

- **Note format:** `C4:1` (note name + octave : duration)
- **Rest:** `R:1` or `_:1` or `[]:1`
- **Chord:** `[C4,E4,G4]:2`
- **Held notes:** `[C4:2,E4:1,G4:3]`
- **Time advance:** `[C3:50]:1`
- **Duration:** 1 = quarter note, 2 = half, 0.5 = eighth, 4 = whole
- **Note names:** C, C#/Db, D, D#/Eb, E, F, F#/Gb, G, G#/Ab, A, A#/Bb, B
- **Octaves:** 0-8 (C4 is middle C, A4 is 440Hz)

---

*Compositions created to demonstrate the expressive capabilities of synthesized piano music with true polyphony and timeline-based mixing.*
