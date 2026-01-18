"""
Audio playback tools for playing piano notes and simple beeps.

Supports MIDI-based piano playback with TRUE polyphonic chords using
synthesized piano tones. Uses NumPy for synthesis and winsound for playback.
"""

import os
import sys
import tempfile
import wave

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
PIANO_VOICES = {
    "default": {
        # Inharmonicity coefficients (B values)
        "inharmonicity": {
            "bass": 0.0005,  # < 110 Hz
            "low_mid": 0.0002,  # 110-260 Hz
            "mid": 0.00005,  # 260-1000 Hz
            "treble_min": 0.00005,  # 1000+ Hz (start)
            "treble_max": 0.025,  # 1000+ Hz (end, at 5000 Hz)
        },
        # Harmonic count by frequency range
        "harmonics": {
            "bass": 20,  # < 110 Hz
            "low_mid": 15,  # 110-260 Hz
            "mid": 10,  # 260-1000 Hz
            "treble_min": 10,  # 1000+ Hz (start)
            "treble_max": 5,  # 1000+ Hz (end, at 4000 Hz)
        },
        # Amplitude scaling (1.0 = full volume)
        "amplitude": {
            "bass": 1.0,  # < 500 Hz
            "mid": 0.6,  # 500-2000 Hz
            "treble": 0.35,  # 2000+ Hz
        },
        # Decay times (seconds)
        "decay": {
            "bass": 6.0,  # < 110 Hz
            "low_mid": 4.0,  # 110-260 Hz
            "mid": 2.5,  # 260-1000 Hz
            "treble": 1.5,  # 1000+ Hz
        },
        # Hammer thunk intensity
        "hammer": {
            "bass": 0.15,  # < 500 Hz
            "mid": 0.05,  # 500-2000 Hz
            "treble": 0.05,  # 2000+ Hz
        },
        # String detuning (cents)
        "detuning": {
            "bass": [0],  # 1 string
            "low_mid": [-1.5, 1.5],  # 2 strings
            "mid_high": [-2, 0, 2],  # 3 strings
        },
        # Soundboard resonance
        "soundboard": {
            "comb_frequencies": [60, 100, 200, 500, 1000],  # Hz
            "comb_feedback": 0.4,
            "comb_mix": 0.15,
            "allpass_delays_ms": [5, 9, 13],  # milliseconds
            "allpass_gain": 0.5,
        },
        # Reverb settings
        "reverb": {
            "predelay_ms": 15,
            "echo_delays_ms": [25, 45, 70, 105, 150],
            "echo_gains": [0.3, 0.2, 0.13, 0.08, 0.05],
        },
        # Sympathetic resonance
        "sympathetic": {
            "harmonic_tolerance": 0.05,  # ±5%
            "base_amplitude": 0.02,
            "high_note_boost": 2.0,  # Multiplier for notes > 2000 Hz
            "high_note_threshold": 2000,  # Hz
            "mix": 0.3,
            "attack_time": 0.05,  # 50ms
            "decay_time": 2.0,
        },
        # Envelope
        "envelope": {
            "attack_time": 0.01,  # 10ms
            "initial_decay_time": 0.15,  # 150ms
            "initial_decay_level": 0.4,
            "sustain_decay_factor": 0.8,
        },
    },
    "bright_grand": {
        # Brighter, more brilliant sound - like a concert grand
        "inharmonicity": {
            "bass": 0.0003,  # Less inharmonicity = clearer
            "low_mid": 0.0001,
            "mid": 0.00003,
            "treble_min": 0.00003,
            "treble_max": 0.020,
        },
        "harmonics": {
            "bass": 25,  # More harmonics = brighter
            "low_mid": 20,
            "mid": 15,
            "treble_min": 12,
            "treble_max": 8,
        },
        "amplitude": {
            "bass": 1.0,
            "mid": 0.75,  # Louder mids and treble
            "treble": 0.55,
        },
        "decay": {
            "bass": 7.0,  # Longer sustain
            "low_mid": 5.0,
            "mid": 3.5,
            "treble": 2.0,
        },
        "hammer": {
            "bass": 0.12,
            "mid": 0.08,
            "treble": 0.06,
        },
        "detuning": {
            "bass": [0],
            "low_mid": [-1.0, 1.0],  # Less detuning = clearer
            "mid_high": [-1.5, 0, 1.5],
        },
        "soundboard": {
            "comb_frequencies": [80, 150, 300, 700, 1200],
            "comb_feedback": 0.35,
            "comb_mix": 0.12,
            "allpass_delays_ms": [4, 7, 11],
            "allpass_gain": 0.45,
        },
        "reverb": {
            "predelay_ms": 10,
            "echo_delays_ms": [20, 35, 55, 85, 120],
            "echo_gains": [0.25, 0.18, 0.12, 0.07, 0.04],
        },
        "sympathetic": {
            "harmonic_tolerance": 0.04,
            "base_amplitude": 0.025,
            "high_note_boost": 2.5,
            "high_note_threshold": 1800,
            "mix": 0.35,
            "attack_time": 0.04,
            "decay_time": 2.5,
        },
        "envelope": {
            "attack_time": 0.008,
            "initial_decay_time": 0.12,
            "initial_decay_level": 0.45,
            "sustain_decay_factor": 0.85,
        },
    },
    "warm_upright": {
        # Warmer, mellower sound - like an upright piano
        "inharmonicity": {
            "bass": 0.0008,  # More inharmonicity = warmer
            "low_mid": 0.0004,
            "mid": 0.0001,
            "treble_min": 0.0001,
            "treble_max": 0.030,
        },
        "harmonics": {
            "bass": 15,  # Fewer harmonics = mellower
            "low_mid": 12,
            "mid": 8,
            "treble_min": 7,
            "treble_max": 4,
        },
        "amplitude": {
            "bass": 1.0,
            "mid": 0.5,  # Quieter treble
            "treble": 0.25,
        },
        "decay": {
            "bass": 4.5,  # Shorter sustain
            "low_mid": 3.0,
            "mid": 2.0,
            "treble": 1.2,
        },
        "hammer": {
            "bass": 0.18,  # More mechanical noise
            "mid": 0.10,
            "treble": 0.08,
        },
        "detuning": {
            "bass": [0],
            "low_mid": [-2.0, 2.0],  # More detuning = warmer
            "mid_high": [-2.5, 0, 2.5],
        },
        "soundboard": {
            "comb_frequencies": [50, 90, 180, 450, 900],
            "comb_feedback": 0.45,
            "comb_mix": 0.18,
            "allpass_delays_ms": [6, 11, 16],
            "allpass_gain": 0.55,
        },
        "reverb": {
            "predelay_ms": 20,
            "echo_delays_ms": [30, 55, 85, 125, 180],
            "echo_gains": [0.35, 0.25, 0.16, 0.10, 0.06],
        },
        "sympathetic": {
            "harmonic_tolerance": 0.06,
            "base_amplitude": 0.018,
            "high_note_boost": 1.5,
            "high_note_threshold": 2200,
            "mix": 0.25,
            "attack_time": 0.06,
            "decay_time": 1.8,
        },
        "envelope": {
            "attack_time": 0.012,
            "initial_decay_time": 0.18,
            "initial_decay_level": 0.35,
            "sustain_decay_factor": 0.75,
        },
    },
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


PIANO_VOICES = {
    "default": {
        # Inharmonicity coefficients (B values)
        "inharmonicity": {
            "bass": 0.0005,  # < 110 Hz
            "low_mid": 0.0002,  # 110-260 Hz
            "mid": 0.00005,  # 260-1000 Hz
            "treble_min": 0.00005,  # 1000+ Hz (start)
            "treble_max": 0.025,  # 1000+ Hz (end, at 5000 Hz)
        },
        # Harmonic count by frequency range
        "harmonics": {
            "bass": 20,  # < 110 Hz
            "low_mid": 15,  # 110-260 Hz
            "mid": 10,  # 260-1000 Hz
            "treble_min": 10,  # 1000+ Hz (start)
            "treble_max": 5,  # 1000+ Hz (end, at 4000 Hz)
        },
        # Amplitude scaling (1.0 = full volume)
        "amplitude": {
            "bass": 1.0,  # < 500 Hz
            "mid": 0.6,  # 500-2000 Hz
            "treble": 0.35,  # 2000+ Hz
        },
        # Decay times (seconds)
        "decay": {
            "bass": 6.0,  # < 110 Hz
            "low_mid": 4.0,  # 110-260 Hz
            "mid": 2.5,  # 260-1000 Hz
            "treble": 1.5,  # 1000+ Hz
        },
        # Hammer thunk intensity
        "hammer": {
            "bass": 0.15,  # < 500 Hz
            "mid": 0.05,  # 500-2000 Hz
            "treble": 0.05,  # 2000+ Hz
        },
        # String detuning (cents)
        "detuning": {
            "bass": [0],  # 1 string
            "low_mid": [-1.5, 1.5],  # 2 strings
            "mid_high": [-2, 0, 2],  # 3 strings
        },
        # Soundboard resonance
        "soundboard": {
            "comb_frequencies": [60, 100, 200, 500, 1000],  # Hz
            "comb_feedback": 0.4,
            "comb_mix": 0.15,
            "allpass_delays_ms": [5, 9, 13],  # milliseconds
            "allpass_gain": 0.5,
        },
        # Reverb settings
        "reverb": {
            "predelay_ms": 15,
            "echo_delays_ms": [25, 45, 70, 105, 150],
            "echo_gains": [0.3, 0.2, 0.13, 0.08, 0.05],
        },
        # Sympathetic resonance
        "sympathetic": {
            "harmonic_tolerance": 0.05,  # ±5%
            "base_amplitude": 0.02,
            "high_note_boost": 2.0,  # Multiplier for notes > 2000 Hz
            "high_note_threshold": 2000,  # Hz
            "mix": 0.3,
            "attack_time": 0.05,  # 50ms
            "decay_time": 2.0,
        },
        # Envelope
        "envelope": {
            "attack_time": 0.01,  # 10ms
            "initial_decay_time": 0.15,  # 150ms
            "initial_decay_level": 0.4,
            "sustain_decay_factor": 0.8,
        },
    },
    "bright_grand": {
        # Brighter, more brilliant sound - like a concert grand
        "inharmonicity": {
            "bass": 0.0003,  # Less inharmonicity = clearer
            "low_mid": 0.0001,
            "mid": 0.00003,
            "treble_min": 0.00003,
            "treble_max": 0.020,
        },
        "harmonics": {
            "bass": 25,  # More harmonics = brighter
            "low_mid": 20,
            "mid": 15,
            "treble_min": 12,
            "treble_max": 8,
        },
        "amplitude": {
            "bass": 1.0,
            "mid": 0.75,  # Louder mids and treble
            "treble": 0.55,
        },
        "decay": {
            "bass": 7.0,  # Longer sustain
            "low_mid": 5.0,
            "mid": 3.5,
            "treble": 2.0,
        },
        "hammer": {
            "bass": 0.12,
            "mid": 0.08,
            "treble": 0.06,
        },
        "detuning": {
            "bass": [0],
            "low_mid": [-1.0, 1.0],  # Less detuning = clearer
            "mid_high": [-1.5, 0, 1.5],
        },
        "soundboard": {
            "comb_frequencies": [80, 150, 300, 700, 1200],
            "comb_feedback": 0.35,
            "comb_mix": 0.12,
            "allpass_delays_ms": [4, 7, 11],
            "allpass_gain": 0.45,
        },
        "reverb": {
            "predelay_ms": 10,
            "echo_delays_ms": [20, 35, 55, 85, 120],
            "echo_gains": [0.25, 0.18, 0.12, 0.07, 0.04],
        },
        "sympathetic": {
            "harmonic_tolerance": 0.04,
            "base_amplitude": 0.025,
            "high_note_boost": 2.5,
            "high_note_threshold": 1800,
            "mix": 0.35,
            "attack_time": 0.04,
            "decay_time": 2.5,
        },
        "envelope": {
            "attack_time": 0.008,
            "initial_decay_time": 0.12,
            "initial_decay_level": 0.45,
            "sustain_decay_factor": 0.85,
        },
    },
    "warm_upright": {
        # Warmer, mellower sound - like an upright piano
        "inharmonicity": {
            "bass": 0.0008,  # More inharmonicity = warmer
            "low_mid": 0.0004,
            "mid": 0.0001,
            "treble_min": 0.0001,
            "treble_max": 0.030,
        },
        "harmonics": {
            "bass": 15,  # Fewer harmonics = mellower
            "low_mid": 12,
            "mid": 8,
            "treble_min": 7,
            "treble_max": 4,
        },
        "amplitude": {
            "bass": 1.0,
            "mid": 0.5,  # Quieter treble
            "treble": 0.25,
        },
        "decay": {
            "bass": 4.5,  # Shorter sustain
            "low_mid": 3.0,
            "mid": 2.0,
            "treble": 1.2,
        },
        "hammer": {
            "bass": 0.18,  # More mechanical noise
            "mid": 0.10,
            "treble": 0.08,
        },
        "detuning": {
            "bass": [0],
            "low_mid": [-2.0, 2.0],  # More detuning = warmer
            "mid_high": [-2.5, 0, 2.5],
        },
        "soundboard": {
            "comb_frequencies": [50, 90, 180, 450, 900],
            "comb_feedback": 0.45,
            "comb_mix": 0.18,
            "allpass_delays_ms": [6, 11, 16],
            "allpass_gain": 0.55,
        },
        "reverb": {
            "predelay_ms": 20,
            "echo_delays_ms": [30, 55, 85, 125, 180],
            "echo_gains": [0.35, 0.25, 0.16, 0.10, 0.06],
        },
        "sympathetic": {
            "harmonic_tolerance": 0.06,
            "base_amplitude": 0.018,
            "high_note_boost": 1.5,
            "high_note_threshold": 2200,
            "mix": 0.25,
            "attack_time": 0.06,
            "decay_time": 1.8,
        },
        "envelope": {
            "attack_time": 0.012,
            "initial_decay_time": 0.18,
            "initial_decay_level": 0.35,
            "sustain_decay_factor": 0.75,
        },
    },
}


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

    LEGACY VERSION - kept for compatibility.
    Consider using _generate_realistic_piano_tone() for better sound quality.

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


def _generate_realistic_piano_tone(
    frequency: float, duration: float, sample_rate: int = 44100, voice: dict = None
) -> np.ndarray:
    """
    Generate a realistic piano tone with enhanced features:
    - INHARMONICITY: Partials stretched according to string stiffness (fixes synthetic high notes!)
    - Frequency-dependent decay (higher harmonics fade faster)
    - Three-string coupling with slight detuning for beating effect
    - Note-dependent decay times (bass sustains longer)
    - Hammer thunk transient (mechanical attack noise)
    - Soundboard resonance via comb filters
    - Diffusion via all-pass filters
    - Short reverb for wooden body time-smearing
    - Frequency-dependent harmonic count (treble has fewer harmonics)
    - Amplitude scaling (treble notes are naturally quieter)
    - Minimum tail duration (notes don't cut off too abruptly)

    Args:
        frequency: Fundamental frequency in Hz
        duration: Duration in seconds
        sample_rate: Sample rate in Hz
        voice: Piano voice preset dict (uses "default" if None)

    Returns:
        Audio samples as numpy array
    """
    # Use default voice if none specified
    if voice is None:
        voice = PIANO_VOICES["default"]

    # ========== MINIMUM TAIL DURATION (INTERPOLATED) ==========
    # Even staccato notes need ~100-200ms to sound natural
    # Smoothly interpolate minimum tail based on frequency
    if frequency < 500:
        min_tail = 0.3  # Bass: 300ms
    elif frequency < 2000:
        # Interpolate from 300ms to 150ms
        t_interp = (frequency - 500) / (2000 - 500)
        min_tail = 0.3 * (1 - t_interp) + 0.15 * t_interp
    else:
        # Interpolate from 150ms to 100ms for very high notes
        t_interp = min((frequency - 2000) / (2000), 1.0)
        min_tail = 0.15 * (1 - t_interp) + 0.1 * t_interp

    # Actual synthesis duration includes the tail
    synthesis_duration = max(duration, min_tail)
    # But we'll fade out starting at the requested duration
    requested_duration = duration

    num_samples = int(sample_rate * synthesis_duration)
    t = np.linspace(0, synthesis_duration, num_samples, False)

    # ========== INHARMONICITY COEFFICIENT ==========
    # Interpolate B coefficient based on frequency (smoother than steps)
    inh = voice["inharmonicity"]
    if frequency < 110:
        B = inh["bass"]
    elif frequency < 260:
        t_interp = (frequency - 110) / (260 - 110)
        B = inh["bass"] * (1 - t_interp) + inh["low_mid"] * t_interp
    elif frequency < 1000:
        t_interp = (frequency - 260) / (1000 - 260)
        B = inh["low_mid"] * (1 - t_interp) + inh["mid"] * t_interp
    else:
        t_interp = min((frequency - 1000) / (4000 - 1000), 1.0)
        B = inh["treble_min"] * (1 - t_interp) + inh["treble_max"] * t_interp

    # ========== FREQUENCY-DEPENDENT HARMONIC COUNT ==========
    harm = voice["harmonics"]
    if frequency < 110:
        num_harmonics = harm["bass"]
    elif frequency < 260:
        t_interp = (frequency - 110) / (260 - 110)
        num_harmonics = int(harm["bass"] * (1 - t_interp) + harm["low_mid"] * t_interp)
    elif frequency < 1000:
        t_interp = (frequency - 260) / (1000 - 260)
        num_harmonics = int(harm["low_mid"] * (1 - t_interp) + harm["mid"] * t_interp)
    else:
        t_interp = min((frequency - 1000) / (3000 - 1000), 1.0)
        num_harmonics = int(harm["treble_min"] * (1 - t_interp) + harm["treble_max"] * t_interp)

    num_harmonics = max(5, num_harmonics)

    # ========== AMPLITUDE SCALING ==========
    amp = voice["amplitude"]
    if frequency < 500:
        amplitude_scale = amp["bass"]
    elif frequency < 2000:
        t_interp = (frequency - 500) / (2000 - 500)
        amplitude_scale = amp["bass"] * (1 - t_interp) + amp["mid"] * t_interp
    else:
        t_interp = min((frequency - 2000) / (2000), 1.0)
        amplitude_scale = amp["mid"] * (1 - t_interp) + amp["treble"] * t_interp

    # ========== STRING DETUNING ==========
    det = voice["detuning"]
    if frequency < 110:
        num_strings = 1
        detuning_cents = det["bass"]
    elif frequency < 260:
        num_strings = 2
        detuning_cents = det["low_mid"]
    else:
        num_strings = 3
        detuning_cents = det["mid_high"]

    # ========== DECAY TIME ==========
    dec = voice["decay"]
    if frequency < 110:
        base_decay_time = dec["bass"]
    elif frequency < 260:
        base_decay_time = dec["low_mid"]
    elif frequency < 1000:
        base_decay_time = dec["mid"]
    else:
        base_decay_time = dec["treble"]

    # Initialize combined tone
    combined_tone = np.zeros(num_samples)

    # Generate each string with slight detuning
    for detune_cents in detuning_cents:
        # Calculate detuned frequency
        string_freq = frequency * (2 ** (detune_cents / 1200))

        # Generate harmonics with INHARMONICITY and frequency-dependent decay
        string_tone = np.zeros(num_samples)

        for n in range(1, num_harmonics + 1):
            # INHARMONIC partial frequency using Fletcher's formula
            # fn = n × f0 × sqrt(1 + B × n²)
            inharmonic_freq = n * string_freq * np.sqrt(1 + B * n * n)

            # Amplitude decreases with harmonic number (realistic rolloff)
            # Using 1/n^1.2 for more natural rolloff
            amplitude = 1.0 / (n**1.2)

            # Frequency-dependent decay: higher harmonics decay faster
            # tau_n = base_decay_time / n
            decay_factor = np.exp(-n * t / base_decay_time)

            # Generate harmonic with decay
            harmonic = amplitude * np.sin(2 * np.pi * inharmonic_freq * t) * decay_factor

            string_tone += harmonic

        # Add this string to the combined tone
        combined_tone += string_tone

    # Average the strings
    combined_tone = combined_tone / num_strings

    # Apply amplitude scaling
    combined_tone = combined_tone * amplitude_scale

    # ========== HAMMER THUNK (Attack Transient) ==========
    hammer_duration = 0.002  # 2ms contact time
    hammer_samples = int(hammer_duration * sample_rate)

    # Get hammer intensity from voice
    ham = voice["hammer"]
    if frequency < 500:
        hammer_intensity = ham["bass"]
    elif frequency < 2000:
        t_interp = (frequency - 500) / (2000 - 500)
        hammer_intensity = ham["bass"] * (1 - t_interp) + ham["mid"] * t_interp
    else:
        hammer_intensity = ham["treble"]

    if hammer_samples > 0 and hammer_samples < num_samples and hammer_intensity > 0:
        # Generate filtered noise for hammer thunk
        hammer_noise = np.random.randn(hammer_samples) * hammer_intensity

        # Lowpass filter the noise (hammer thunk is low frequency ~500 Hz)
        # Simple exponential smoothing filter
        alpha = 0.3
        for i in range(1, hammer_samples):
            hammer_noise[i] = alpha * hammer_noise[i] + (1 - alpha) * hammer_noise[i - 1]

        # Apply quick decay envelope to hammer noise
        hammer_envelope = np.exp(-np.linspace(0, 10, hammer_samples))
        hammer_noise *= hammer_envelope

        # Mix hammer noise into the beginning
        combined_tone[:hammer_samples] += hammer_noise

    # ========== ENVELOPE ==========
    env = voice["envelope"]
    attack_time = env["attack_time"]
    initial_decay_time = env["initial_decay_time"]

    attack_samples = min(int(attack_time * sample_rate), num_samples)
    initial_decay_samples = min(int(initial_decay_time * sample_rate), num_samples - attack_samples)

    envelope = np.ones(num_samples)

    # Attack phase (0 to 1)
    if attack_samples > 0:
        envelope[:attack_samples] = np.linspace(0, 1, attack_samples)

    # Initial decay phase (1 to decay_level)
    if initial_decay_samples > 0:
        start_idx = attack_samples
        end_idx = attack_samples + initial_decay_samples
        envelope[start_idx:end_idx] = np.linspace(1.0, env["initial_decay_level"], initial_decay_samples)

    # Sustain/release phase (decay_level to 0)
    sustain_start = attack_samples + initial_decay_samples
    if sustain_start < num_samples:
        t_sustain = t[sustain_start:] - t[sustain_start]
        envelope[sustain_start:] = env["initial_decay_level"] * np.exp(
            -t_sustain / (base_decay_time * env["sustain_decay_factor"])
        )

    # Apply envelope
    combined_tone = combined_tone * envelope

    # ========== NATURAL TAIL FADEOUT ==========
    # If the requested duration is shorter than synthesis duration,
    # add a natural fadeout starting at the requested duration
    if requested_duration < synthesis_duration:
        requested_samples = int(requested_duration * sample_rate)
        tail_samples = num_samples - requested_samples

        if tail_samples > 0 and requested_samples < num_samples:
            # Create exponential fadeout for the tail
            tail_fadeout = np.exp(-np.linspace(0, 5, tail_samples))
            combined_tone[requested_samples:] *= tail_fadeout

    # ========== COMB FILTERS (Soundboard Resonances) ==========
    sb = voice["soundboard"]
    comb_frequencies = sb["comb_frequencies"]
    comb_feedback = sb["comb_feedback"]

    for base_freq in comb_frequencies:
        # Add random 0.2% variation to each comb filter frequency
        freq_variation = 1.0 + (np.random.rand() - 0.5) * 0.004  # ±0.2%
        comb_freq = base_freq * freq_variation

        # Calculate delay in samples
        delay_samples = int(sample_rate / comb_freq)

        if delay_samples > 0 and delay_samples < num_samples:
            # Apply comb filter (feedforward + feedback)
            comb_output = np.zeros(num_samples)
            for i in range(delay_samples, num_samples):
                comb_output[i] = combined_tone[i] + comb_feedback * comb_output[i - delay_samples]

            # Mix comb filter output
            combined_tone = combined_tone * (1 - sb["comb_mix"]) + comb_output * sb["comb_mix"]

    # ========== ALL-PASS FILTERS (Diffusion) ==========
    allpass_delays_ms = sb["allpass_delays_ms"]
    allpass_gain = sb["allpass_gain"]

    for delay_ms in allpass_delays_ms:
        delay = int(delay_ms * sample_rate / 1000)
        if delay > 0 and delay < num_samples:
            allpass_output = np.zeros(num_samples)
            for i in range(delay, num_samples):
                # All-pass filter: y[n] = -g*x[n] + x[n-d] + g*y[n-d]
                allpass_output[i] = (
                    -allpass_gain * combined_tone[i] + combined_tone[i - delay] + allpass_gain * allpass_output[i - delay]
                )
            combined_tone = allpass_output

    # ========== SHORT REVERB (Soundboard Time-Smearing) ==========
    rev = voice["reverb"]
    predelay = int(rev["predelay_ms"] * sample_rate / 1000)
    echo_delays_ms = rev["echo_delays_ms"]
    echo_gains = rev["echo_gains"]

    reverb_output = combined_tone.copy()
    for delay_ms, gain in zip(echo_delays_ms, echo_gains):
        delay = int(delay_ms * sample_rate / 1000)
        total_delay = predelay + delay
        if total_delay < num_samples:
            # Add delayed and attenuated copy
            reverb_output[total_delay:] += combined_tone[:-total_delay] * gain

    combined_tone = reverb_output

    # Final fade-out at the very end to prevent speaker popping
    fadeout_samples = min(int(0.02 * sample_rate), num_samples)  # 20ms fadeout
    if fadeout_samples > 0:
        fadeout_envelope = np.linspace(1, 0, fadeout_samples)
        combined_tone[-fadeout_samples:] *= fadeout_envelope

    # Normalize to prevent clipping while maintaining dynamics
    if np.max(np.abs(combined_tone)) > 0:
        combined_tone = combined_tone / np.max(np.abs(combined_tone)) * 0.35

    return combined_tone


def _create_wav_file(parsed_notes: list, sample_rate: int = 44100, voice: dict = None) -> str:
    """
    Create a WAV file with polyphonic piano synthesis using timeline-based mixing.
    Now includes sympathetic resonance between harmonically-related notes.

    Args:
        parsed_notes: List of (midi_note, start_time_ms, duration_ms) tuples
        sample_rate: Sample rate in Hz
        voice: Piano voice preset dict (uses "default" if None)

    Returns:
        Path to created WAV file
    """
    if not parsed_notes:
        raise ValueError("No notes to play")

    # Use default voice if none specified
    if voice is None:
        voice = PIANO_VOICES["default"]

    # Calculate total duration needed
    # Add extra time for the natural tail of the last note(s)
    # Maximum tail is 300ms for bass notes, so add 500ms to be safe
    base_duration_ms = max(start_time + duration for _, start_time, duration in parsed_notes)
    tail_padding_ms = 500  # Extra time for natural decay tails
    total_duration_ms = base_duration_ms + tail_padding_ms

    total_samples = int((total_duration_ms / 1000.0) * sample_rate)

    # Create the full waveform buffer
    audio = np.zeros(total_samples)

    # Mix all notes into the timeline WITH SYMPATHETIC RESONANCE
    for midi_note, start_time_ms, duration_ms in parsed_notes:
        # Generate tone with context of all other notes for sympathetic resonance
        tone = _generate_piano_note_with_context(midi_note, start_time_ms, duration_ms, parsed_notes, sample_rate, voice)

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


def _generate_piano_note_with_context(
    midi_note: int,
    start_time_ms: float,
    duration_ms: float,
    all_notes: list,
    sample_rate: int = 44100,
    voice: dict = None,
) -> np.ndarray:
    """
    Generate a piano note with sympathetic resonance from other active notes.

    This layer adds the crucial sympathetic resonance effect where strings vibrate
    in response to other harmonically-related notes. The top ~18 notes (C7 and above)
    are undamped in real pianos and ring freely, contributing to the overall richness.

    Args:
        midi_note: MIDI note number of the note to generate
        start_time_ms: Start time of this note
        duration_ms: Duration of this note
        all_notes: List of all (midi_note, start_time_ms, duration_ms) tuples
        sample_rate: Sample rate in Hz
        voice: Piano voice preset dict (uses "default" if None)

    Returns:
        Audio samples as numpy array with sympathetic resonance added
    """
    # Use default voice if none specified
    if voice is None:
        voice = PIANO_VOICES["default"]

    freq = _midi_to_frequency(midi_note)
    duration_s = duration_ms / 1000.0

    # Generate the base tone
    base_tone = _generate_realistic_piano_tone(freq, duration_s, sample_rate, voice)

    # ========== SYMPATHETIC RESONANCE ==========
    symp = voice["sympathetic"]

    # Find notes that overlap in time with this note
    end_time_ms = start_time_ms + duration_ms

    # Collect frequencies of overlapping notes
    overlapping_freqs = []
    for other_midi, other_start, other_duration in all_notes:
        if other_midi == midi_note:
            continue  # Don't resonate with self

        other_end = other_start + other_duration

        # Check if notes overlap in time
        if not (other_end <= start_time_ms or other_start >= end_time_ms):
            other_freq = _midi_to_frequency(other_midi)
            overlapping_freqs.append(other_freq)

    # Add sympathetic resonance if there are overlapping notes
    if overlapping_freqs:
        num_samples = len(base_tone)
        t = np.linspace(0, duration_s, num_samples, False)

        sympathetic_signal = np.zeros(num_samples)

        for other_freq in overlapping_freqs:
            # Check if harmonics overlap between this note and the other note
            # Sympathetic resonance occurs where harmonics of two strings overlap

            # Check up to 10 harmonics of each note
            for n1 in range(1, 11):
                harmonic1 = freq * n1

                for n2 in range(1, 11):
                    harmonic2 = other_freq * n2

                    # If harmonics are close (within tolerance %), add resonance
                    ratio = harmonic1 / harmonic2 if harmonic2 > 0 else 0
                    tolerance = symp["harmonic_tolerance"]
                    if (1 - tolerance) < ratio < (1 + tolerance):
                        # Found overlapping harmonics - add subtle resonance

                        # Resonance amplitude depends on harmonic number (higher = weaker)
                        resonance_amplitude = symp["base_amplitude"] / (n1 * n2) ** 0.5

                        # Undamped high notes resonate more strongly
                        if other_freq > symp["high_note_threshold"]:
                            resonance_amplitude *= symp["high_note_boost"]

                        # Generate resonance at the overlapping frequency
                        # Use average of the two harmonics
                        resonance_freq = (harmonic1 + harmonic2) / 2

                        # Slower attack for sympathetic resonance (builds up gradually)
                        attack_samples = min(int(symp["attack_time"] * sample_rate), num_samples)
                        envelope = np.ones(num_samples)
                        if attack_samples > 0:
                            envelope[:attack_samples] = np.linspace(0, 1, attack_samples)

                        # Exponential decay
                        envelope *= np.exp(-t / symp["decay_time"])

                        # Add the resonance
                        resonance = resonance_amplitude * np.sin(2 * np.pi * resonance_freq * t) * envelope
                        sympathetic_signal += resonance

        # Mix sympathetic resonance into the base tone
        base_tone = base_tone + sympathetic_signal * symp["mix"]

    return base_tone


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
def piano(notation: str, tempo: int = 120, voice: str = "bright_grand") -> str:
    """
    Play piano notes with TRUE polyphonic chord support using realistic synthesized piano tones.

    ENHANCED SOUND QUALITY with:
    - Frequency-dependent decay (higher harmonics fade faster, like real pianos)
    - Three-string coupling with slight detuning for natural beating/chorus effect
    - Note-dependent decay times (bass notes sustain 6s, treble 1.5s)
    - Double-decay envelope (fast initial drop, slow exponential release)
    - Inharmonicity for realistic high notes
    - Sympathetic resonance between harmonically-related strings
    - Soundboard resonance and diffusion
    - Multiple piano voice presets

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

    Piano Voices:
        - "bright_grand": Brilliant, clear concert grand with longer sustain (DEFAULT)
        - "default": Balanced concert grand sound
        - "warm_upright": Mellow, warm upright piano with shorter decay

    This version uses NumPy to synthesize realistic piano tones with:
    - Multiple strings per note (1 for bass, 2 for low-mid, 3 for mid-high)
    - Slight detuning between strings creates natural beating and longer sustain
    - Frequency-dependent harmonic decay (high frequencies fade faster)
    - Note-dependent base decay (bass notes ring longer than treble)
    - Inharmonicity (Fletcher's formula) for realistic high notes
    - Sympathetic resonance between harmonically-related notes

    Chords are played with TRUE polyphony (all notes sounding simultaneously), not as
    arpeggios. Held notes allow individual notes within a chord to sustain for different
    durations, creating rich harmonic textures.

    The time advance feature allows notes to ring through subsequent chords - perfect
    for pedal tones, drones, and bell-like sustained notes. Use rests (R:1 or []:1) to
    advance time while notes continue to ring.

    Parameters:
    - notation (str): Music notation string
    - tempo (int): Beats per minute (default: 120)
    - voice (str): Piano voice preset: "bright_grand" (default), "default", or "warm_upright"

    Returns:
    str: Success message or error description

    cost: low
    """
    try:
        # Validate voice
        if voice not in PIANO_VOICES:
            available = ", ".join(PIANO_VOICES.keys())
            return f"Error: Unknown voice '{voice}'. Available voices: {available}"

        # Get voice preset
        voice_preset = PIANO_VOICES[voice]

        # Parse notation
        parsed_notes = _parse_music_notation(notation, tempo)

        if not parsed_notes:
            return "Error: No valid notes found in notation"

        # Use polyphonic synthesis if NumPy is available
        if NUMPY_AVAILABLE and WINSOUND_AVAILABLE:
            # Create WAV file with true polyphonic synthesis
            wav_path = _create_wav_file(parsed_notes, voice=voice_preset)

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
                f"{tempo} BPM using '{voice}' voice (ENHANCED REALISM: inharmonicity + sympathetic resonance!)"
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
