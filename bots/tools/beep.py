"""
Audio playback tools for playing piano notes and simple beeps.

Supports MIDI-based piano playback with TRUE polyphonic chords using
synthesized piano tones. Uses NumPy for synthesis and winsound for playback.
"""

import os
import sys
import tempfile
import wave
from typing import Optional

try:
    import numpy as np

    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

# Windows winsound - reliable and built-in
if sys.platform == "win32":
    import winsound

    WINSOUND_AVAILABLE = True
else:
    WINSOUND_AVAILABLE = False

from bots.dev.decorators import toolify

# Note name to MIDI number mapping
NOTE_MAP = {
    "C": 0,
    "C#": 1,
    "Db": 1,
    "D": 2,
    "D#": 3,
    "Eb": 3,
    "E": 4,
    "F": 5,
    "F#": 6,
    "Gb": 6,
    "G": 7,
    "G#": 8,
    "Ab": 8,
    "A": 9,
    "A#": 10,
    "Bb": 10,
    "B": 11,
}


def _parse_note(note_str: str) -> int:
    """
    Convert note string (e.g., 'C4', 'F#5', 'Bb3') to MIDI note number.

    Args:
        note_str: Note in scientific pitch notation (e.g., 'C4')

    Returns:
        MIDI note number (0-127)
    """
    note_str = note_str.strip()

    # Extract note name and octave
    if len(note_str) < 2:
        raise ValueError(f"Invalid note format: {note_str}")

    # Handle sharps/flats
    if note_str[1] in ["#", "b"]:
        note_name = note_str[:2]
        octave = int(note_str[2:])
    else:
        note_name = note_str[0]
        octave = int(note_str[1:])

    if note_name not in NOTE_MAP:
        raise ValueError(f"Invalid note name: {note_name}")

    # MIDI note number = (octave + 1) * 12 + note_offset
    # Middle C (C4) = 60
    midi_note = (octave + 1) * 12 + NOTE_MAP[note_name]

    if not 0 <= midi_note <= 127:
        raise ValueError(f"Note {note_str} out of MIDI range")

    return midi_note


def _midi_to_frequency(midi_note: int) -> float:
    """Convert MIDI note number to frequency in Hz."""
    # A4 (MIDI 69) = 440 Hz
    return 440.0 * (2.0 ** ((midi_note - 69) / 12.0))


def _parse_music_notation(notation: str, tempo: int = 120) -> list:
    """
    Parse music notation into list of (note, start_time_ms, duration_ms) tuples.

    Format:
        - Single note: "C4:1" (note:duration)
        - Rest/silence: "R:1" or "_:1" (advances time without playing)
        - Chord (same duration): "[C4,E4,G4]:2" (notes in brackets, comma-separated)
        - Chord (held notes): "[C4:2,E4:1,G4:3]" (each note with its own duration)
        - Chord (with time advance): "[C4:100]:1" (C4 sustains 100 beats, time advances 1 beat)
        - Duration: 1 = quarter note, 2 = half note, 0.5 = eighth note, etc.
        - Space separates sequential notes/chords

    Args:
        notation: Music notation string
        tempo: Beats per minute (default 120)

    Returns:
        List of (midi_note, start_time_ms, duration_ms) tuples
    """
    # Calculate milliseconds per quarter note
    ms_per_quarter = (60.0 / tempo) * 1000

    result = []
    current_time_ms = 0

    tokens = notation.strip().split()

    for token in tokens:
        if not token:
            continue

        # Check for rest/silence
        if token.startswith("R:") or token.startswith("_:"):
            # Rest - just advance time
            duration_part = token.split(":", 1)[1]
            duration = float(duration_part)
            duration_ms = int(duration * ms_per_quarter)
            current_time_ms += duration_ms
            continue

        # Parse chord or single note
        if token.startswith("["):
            # Chord - can have individual durations or shared duration
            if "]:" in token:
                # Format: [notes]:time_advance
                # Notes can be: C4,E4,G4 (shared) or C4:2,E4:1,G4:3 (individual)
                bracket_end = token.index("]:")
                notes_part = token[1:bracket_end]
                time_advance_part = token[bracket_end + 2 :]
                time_advance = float(time_advance_part)
                time_advance_ms = int(time_advance * ms_per_quarter)

                # Check for empty chord (just a rest with explicit time advance)
                if not notes_part or notes_part.strip() == "":
                    current_time_ms += time_advance_ms
                    continue

                # Parse individual notes
                notes_str_list = notes_part.split(",")

                for note_str in notes_str_list:
                    note_str = note_str.strip()
                    if not note_str:
                        continue

                    if ":" in note_str:
                        # Individual duration: C4:2
                        note_name, duration_part = note_str.rsplit(":", 1)
                        duration = float(duration_part)
                        duration_ms = int(duration * ms_per_quarter)
                    else:
                        # No duration specified, use time_advance as duration
                        note_name = note_str
                        duration_ms = time_advance_ms

                    midi_note = _parse_note(note_name)
                    result.append((midi_note, current_time_ms, duration_ms))

            elif token.endswith("]"):
                # Individual durations without time advance: [C4:2,E4:1,G4:3]
                # Time advances by the longest note
                notes_part = token[1:-1]

                # Check for empty chord
                if not notes_part or notes_part.strip() == "":
                    # Empty chord with no time advance specified - skip it
                    continue

                notes_str_list = notes_part.split(",")
                max_duration = 0

                for note_str in notes_str_list:
                    note_str = note_str.strip()
                    if not note_str:
                        continue
                    if ":" not in note_str:
                        raise ValueError(f"Invalid note format in chord (missing duration): {note_str}")

                    note_name, duration_part = note_str.rsplit(":", 1)
                    duration = float(duration_part)
                    duration_ms = int(duration * ms_per_quarter)
                    max_duration = max(max_duration, duration_ms)

                    midi_note = _parse_note(note_name)
                    result.append((midi_note, current_time_ms, duration_ms))

                time_advance_ms = max_duration
            else:
                raise ValueError(f"Invalid chord format: {token}")

            # Advance time by the specified amount (or max duration if not specified)
            current_time_ms += time_advance_ms

        else:
            # Single note: C4:1
            if ":" not in token:
                raise ValueError(f"Invalid token format (missing duration): {token}")

            note_part, duration_part = token.rsplit(":", 1)
            duration = float(duration_part)
            duration_ms = int(duration * ms_per_quarter)

            midi_note = _parse_note(note_part)
            result.append((midi_note, current_time_ms, duration_ms))

            # Advance time
            current_time_ms += duration_ms

    return result


def _generate_piano_tone(frequency: float, duration: float, sample_rate: int = 44100) -> np.ndarray:
    """
    Generate a piano-like tone using additive synthesis with harmonics.

    Args:
        frequency: Fundamental frequency in Hz
        duration: Duration in seconds
        sample_rate: Sample rate in Hz

    Returns:
        Audio samples as numpy array
    """
    num_samples = int(sample_rate * duration)
    t = np.linspace(0, duration, num_samples, False)

    # Piano-like harmonic structure with realistic amplitudes
    harmonics = [
        (1.0, 1.0),  # Fundamental
        (2.0, 0.5),  # 2nd harmonic
        (3.0, 0.25),  # 3rd harmonic
        (4.0, 0.15),  # 4th harmonic
        (5.0, 0.1),  # 5th harmonic
        (6.0, 0.05),  # 6th harmonic
        (7.0, 0.025),  # 7th harmonic
    ]

    # Generate tone with harmonics
    tone = np.zeros(num_samples)
    for harmonic_num, amplitude in harmonics:
        tone += amplitude * np.sin(2 * np.pi * frequency * harmonic_num * t)

    # Apply realistic ADSR envelope for piano
    attack_time = 0.01  # Very fast attack
    decay_time = 0.1  # Quick decay
    release_time = min(0.2, duration * 0.3)  # Gradual release

    attack_samples = min(int(attack_time * sample_rate), num_samples)
    decay_samples = min(int(decay_time * sample_rate), num_samples - attack_samples)
    release_samples = min(int(release_time * sample_rate), num_samples - attack_samples - decay_samples)
    sustain_samples = max(0, num_samples - attack_samples - decay_samples - release_samples)

    envelope = np.ones(num_samples)

    # Attack (0 to 1)
    if attack_samples > 0:
        envelope[:attack_samples] = np.linspace(0, 1, attack_samples)

    # Decay (1 to 0.6)
    if decay_samples > 0:
        start_idx = attack_samples
        end_idx = attack_samples + decay_samples
        envelope[start_idx:end_idx] = np.linspace(1, 0.6, decay_samples)

    # Sustain (0.6 constant)
    if sustain_samples > 0:
        start_idx = attack_samples + decay_samples
        end_idx = start_idx + sustain_samples
        envelope[start_idx:end_idx] = 0.6

    # Release (0.6 to 0)
    if release_samples > 0:
        start_idx = num_samples - release_samples
        envelope[start_idx:] = np.linspace(0.6, 0, release_samples)

    # Apply envelope
    tone = tone * envelope

    # Normalize to prevent clipping
    if np.max(np.abs(tone)) > 0:
        tone = tone / np.max(np.abs(tone)) * 0.3

    return tone


def _create_wav_file(parsed_notes: list, sample_rate: int = 44100) -> str:
    """
    Create a WAV file with polyphonic piano synthesis using timeline-based mixing.

    Args:
        parsed_notes: List of (midi_note, start_time_ms, duration_ms) tuples
        sample_rate: Sample rate in Hz

    Returns:
        Path to created WAV file
    """
    if not parsed_notes:
        raise ValueError("No notes to play")

    # Calculate total duration needed
    total_duration_ms = max(start_time + duration for _, start_time, duration in parsed_notes)
    total_samples = int((total_duration_ms / 1000.0) * sample_rate)

    # Create the full waveform buffer
    audio = np.zeros(total_samples)

    # Mix all notes into the timeline
    for midi_note, start_time_ms, duration_ms in parsed_notes:
        freq = _midi_to_frequency(midi_note)
        duration_s = duration_ms / 1000.0

        # Generate the tone
        tone = _generate_piano_tone(freq, duration_s, sample_rate)

        # Calculate where to place it in the timeline
        start_sample = int((start_time_ms / 1000.0) * sample_rate)
        end_sample = start_sample + len(tone)

        # Ensure we don't go past the buffer
        if end_sample > total_samples:
            end_sample = total_samples
            tone = tone[: end_sample - start_sample]

        # Mix the tone into the audio buffer
        audio[start_sample:end_sample] += tone

    # Normalize final audio
    if np.max(np.abs(audio)) > 0:
        audio = audio / np.max(np.abs(audio)) * 0.8

    # Convert to 16-bit PCM
    audio_int16 = (audio * 32767).astype(np.int16)

    # Write to WAV file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    temp_file.close()

    with wave.open(temp_file.name, "w") as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_int16.tobytes())

    return temp_file.name


def _play_with_winsound_simple(parsed_notes: list) -> None:
    """
    Play notes using Windows winsound (simple beep method).
    Note: This fallback method plays notes sequentially and cannot handle overlapping notes.

    Args:
        parsed_notes: List of (midi_note, start_time_ms, duration_ms) tuples
    """
    # Group notes by start time to identify chords
    from collections import defaultdict

    notes_by_time = defaultdict(list)

    for midi_note, start_time, duration in parsed_notes:
        notes_by_time[start_time].append((midi_note, duration))

    # Play notes in chronological order
    for start_time in sorted(notes_by_time.keys()):
        notes_at_time = notes_by_time[start_time]

        # For chords, play notes in quick succession (arpeggio)
        if len(notes_at_time) > 1:
            # Use the shortest duration for the arpeggio timing
            min_duration = min(dur for _, dur in notes_at_time)
            chord_duration = min_duration // len(notes_at_time)

            for midi_note, _ in notes_at_time:
                freq = int(_midi_to_frequency(midi_note))
                freq = max(37, min(32767, freq))
                winsound.Beep(freq, chord_duration)
        else:
            midi_note, duration = notes_at_time[0]
            freq = int(_midi_to_frequency(midi_note))
            freq = max(37, min(32767, freq))
            winsound.Beep(freq, duration)


@toolify()
def piano(notation: str, tempo: int = 120, soundfont: Optional[str] = None) -> str:
    """
    Play piano notes with TRUE polyphonic chord support using synthesized piano tones.

    Notation format:
        - Single note: "C4:1" (note name + octave : duration)
        - Rest/silence: "R:1" or "_:1" (advances time without playing)
        - Chord (same duration): "[C4,E4,G4]:2" (notes in brackets, comma-separated : duration)
        - Chord (held notes): "[C4:2,E4:1,G4:3]" (each note with its own duration)
        - Chord (with time advance): "[C4:100]:1" (C4 sustains 100 beats, time advances 1 beat)
        - Empty chord (rest): "[]:1" (advances time by 1 beat without playing)
        - Duration: 1 = quarter note, 2 = half note, 0.5 = eighth note, 4 = whole note
        - Multiple notes/chords: separate with spaces

    Examples:
        piano("C4:1 E4:1 G4:1")                    # Three quarter notes (C, E, G)
        piano("C4:1 R:1 G4:1")                     # C, rest, G
        piano("[C4,E4,G4]:2")                       # C major chord (all notes same duration)
        piano("[C4:2,E4:1,G4:3]")                   # Held notes - C for 2 beats, E for 1, G for 3
        piano("[C3:50]:1 [E4,G4]:1")                # C3 pedal tone for 50 beats, time advances by 1
        piano("[C4:8]:1 [E4:6]:1 [G4:4]:1 []:5")   # Cascading chord with rests at end
        piano("C4:0.5 D4:0.5 E4:1 F4:1")           # Eighth, eighth, quarter, quarter
        piano("[C4,E4,G4]:1 [F4,A4,C5]:1")         # Two chords with real harmony
        piano("[C3:8,C4:1,E4:1,G4:1]:1")           # Bass holds 8 beats, melody moves every beat

    Note names: C, C#/Db, D, D#/Eb, E, F, F#/Gb, G, G#/Ab, A, A#/Bb, B
    Octaves: 0-8 (C4 is middle C, A4 is 440Hz)

    This version uses NumPy to synthesize piano-like tones with harmonics and
    realistic ADSR envelopes. Chords are played with TRUE polyphony (all notes
    sounding simultaneously), not as arpeggios. Held notes allow individual notes
    within a chord to sustain for different durations, creating rich harmonic textures.

    The time advance feature allows notes to ring through subsequent chords - perfect
    for pedal tones, drones, and bell-like sustained notes. Use rests (R:1 or []:1) to
    advance time while notes continue to ring.

    Parameters:
    - notation (str): Music notation string
    - tempo (int): Beats per minute (default: 120)
    - soundfont (str): Optional path to .sf2 soundfont file (not used)

    Returns:
    str: Success message or error description

    cost: low
    """
    try:
        # Parse notation
        parsed_notes = _parse_music_notation(notation, tempo)

        if not parsed_notes:
            return "Error: No valid notes found in notation"

        # Use polyphonic synthesis if NumPy is available
        if NUMPY_AVAILABLE and WINSOUND_AVAILABLE:
            # Create WAV file with true polyphonic synthesis
            wav_path = _create_wav_file(parsed_notes)

            # Play WAV file
            winsound.PlaySound(wav_path, winsound.SND_FILENAME)

            # Cleanup
            try:
                os.remove(wav_path)
            except Exception:
                pass

            note_count = len(parsed_notes)
            # Count unique start times to identify chords/groups
            unique_times = len(set(start_time for _, start_time, _ in parsed_notes))

            return (
                f"Successfully played {note_count} note(s) in {unique_times} group(s) at "
                f"{tempo} BPM (TRUE POLYPHONY with timeline mixing!)"
            )

        elif WINSOUND_AVAILABLE:
            # Fallback to simple beep method
            _play_with_winsound_simple(parsed_notes)
            note_count = len(parsed_notes)
            return f"Successfully played {note_count} note(s) at {tempo} BPM " f"(simple beeps - install numpy for polyphony)"

        else:
            return "Error: No audio backend available. This tool requires Windows."

    except Exception as e:
        return f"Error playing piano: {str(e)}"


@toolify()
def beep(frequency: int = 440, duration: float = 0.5) -> str:
    """
    Play a simple beep tone.

    Parameters:
    - frequency (int): Frequency in Hz (default: 440 = A4, range: 37-32767)
    - duration (float): Duration in seconds (default: 0.5)

    Returns:
    str: Success message or error description

    cost: low
    """
    try:
        if WINSOUND_AVAILABLE:
            # Clamp frequency to winsound's range
            frequency = max(37, min(32767, frequency))
            duration_ms = int(duration * 1000)
            winsound.Beep(frequency, duration_ms)
            return f"Played {frequency}Hz beep for {duration}s"
        else:
            return "Error: No audio backend available. This tool requires Windows."

    except Exception as e:
        return f"Error playing beep: {str(e)}"
