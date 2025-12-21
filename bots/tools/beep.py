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
    Parse music notation into list of (notes, duration_ms) tuples.

    Format:
        - Single note: "C4:1" (note:duration)
        - Chord: "[C4,E4,G4]:2" (notes in brackets, comma-separated)
        - Duration: 1 = quarter note, 2 = half note, 0.5 = eighth note, etc.
        - Space separates sequential notes/chords

    Args:
        notation: Music notation string
        tempo: Beats per minute (default 120)

    Returns:
        List of (note_list, duration_ms) tuples
    """
    # Calculate milliseconds per quarter note
    ms_per_quarter = (60.0 / tempo) * 1000

    result = []
    tokens = notation.strip().split()

    for token in tokens:
        if not token:
            continue

        # Split note(s) and duration
        if ":" not in token:
            raise ValueError(f"Invalid token format (missing duration): {token}")

        notes_part, duration_part = token.rsplit(":", 1)
        duration = float(duration_part)
        duration_ms = int(duration * ms_per_quarter)

        # Parse chord or single note
        if notes_part.startswith("[") and notes_part.endswith("]"):
            # Chord
            notes_str = notes_part[1:-1]
            notes = [_parse_note(n.strip()) for n in notes_str.split(",")]
        else:
            # Single note
            notes = [_parse_note(notes_part)]

        result.append((notes, duration_ms))

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
    Create a WAV file with polyphonic piano synthesis.

    Args:
        parsed_notes: List of (note_list, duration_ms) tuples
        sample_rate: Sample rate in Hz

    Returns:
        Path to created WAV file
    """
    # Generate audio for all notes
    audio_segments = []

    for notes, duration_ms in parsed_notes:
        duration_s = duration_ms / 1000.0

        # Generate audio for all notes in chord (TRUE POLYPHONY!)
        segment_length = int(sample_rate * duration_s)
        segment = np.zeros(segment_length)

        for note in notes:
            freq = _midi_to_frequency(note)
            tone = _generate_piano_tone(freq, duration_s, sample_rate)

            # Ensure tone and segment are the same length
            min_length = min(len(tone), len(segment))
            segment[:min_length] = segment[:min_length] + tone[:min_length]

        # Normalize mixed segment
        if np.max(np.abs(segment)) > 0:
            segment = segment / np.max(np.abs(segment)) * 0.7

        audio_segments.append(segment)

    # Concatenate all segments
    audio = np.concatenate(audio_segments)

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
    Chords are played as arpeggios (notes in quick succession).

    Args:
        parsed_notes: List of (note_list, duration_ms) tuples
    """
    for notes, duration_ms in parsed_notes:
        # For chords, play notes in quick succession
        if len(notes) > 1:
            chord_duration = duration_ms // len(notes)
            for note in notes:
                freq = int(_midi_to_frequency(note))
                freq = max(37, min(32767, freq))
                winsound.Beep(freq, chord_duration)
        else:
            freq = int(_midi_to_frequency(notes[0]))
            freq = max(37, min(32767, freq))
            winsound.Beep(freq, duration_ms)


@toolify()
def piano(notation: str, tempo: int = 120, soundfont: Optional[str] = None) -> str:
    """
    Play piano notes with TRUE polyphonic chord support using synthesized piano tones.

    Notation format:
        - Single note: "C4:1" (note name + octave : duration)
        - Chord: "[C4,E4,G4]:2" (notes in brackets, comma-separated : duration)
        - Duration: 1 = quarter note, 2 = half note, 0.5 = eighth note, 4 = whole note
        - Multiple notes/chords: separate with spaces

    Examples:
        piano("C4:1 E4:1 G4:1")              # Three quarter notes (C, E, G)
        piano("[C4,E4,G4]:2")                 # C major chord (TRUE POLYPHONY!)
        piano("C4:0.5 D4:0.5 E4:1 F4:1")     # Eighth, eighth, quarter, quarter
        piano("[C4,E4,G4]:1 [F4,A4,C5]:1")   # Two chords with real harmony

    Note names: C, C#/Db, D, D#/Eb, E, F, F#/Gb, G, G#/Ab, A, A#/Bb, B
    Octaves: 0-8 (C4 is middle C, A4 is 440Hz)

    This version uses NumPy to synthesize piano-like tones with harmonics and
    realistic ADSR envelopes. Chords are played with TRUE polyphony (all notes
    sounding simultaneously), not as arpeggios.

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
            chord_count = sum(1 for notes, _ in parsed_notes if len(notes) > 1)
            if chord_count > 0:
                return (
                    f"Successfully played {note_count} note(s)/chord(s) at "
                    f"{tempo} BPM (TRUE POLYPHONY with {chord_count} chords!)"
                )
            else:
                return f"Successfully played {note_count} note(s) at {tempo} BPM " f"(synthesized piano)"

        elif WINSOUND_AVAILABLE:
            # Fallback to simple beep method
            _play_with_winsound_simple(parsed_notes)
            note_count = len(parsed_notes)
            return (
                f"Successfully played {note_count} note(s)/chord(s) at {tempo} BPM "
                f"(simple beeps - install numpy for polyphony)"
            )

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
