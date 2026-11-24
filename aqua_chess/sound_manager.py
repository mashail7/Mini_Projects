"""
sound_manager.py — Procedural Coastal Audio & Sound Effects Manager for Aqua Chess.

Synthesizes self-contained, peak-normalized 16-bit PCM .wav sound effects into
`assets/sounds/` on first run (using Python's built-in wave, math, struct, and
random modules) and manages low-latency, non-blocking, overlapping playback via
PySide6.QtMultimedia.QSoundEffect.
"""

from __future__ import annotations

import math
import os
import random
import struct
import wave
from pathlib import Path
from typing import Callable

from PySide6.QtCore import QObject, QUrl, Signal

try:
    from PySide6.QtMultimedia import QMediaDevices, QSoundEffect

    _QT_MULTIMEDIA_AVAILABLE = True
except Exception:  # pragma: no cover - defensive fallback if multimedia plugin is absent
    QMediaDevices = None  # type: ignore[assignment]
    QSoundEffect = None  # type: ignore[assignment]
    _QT_MULTIMEDIA_AVAILABLE = False


# ---------------------------------------------------------------------------
# Audio Format & Volume Constants
# ---------------------------------------------------------------------------
SAMPLE_RATE = 44100
CHANNELS = 1
SAMPLE_WIDTH = 2  # 16-bit signed PCM
MAX_PCM_16 = 32767

DEFAULT_VOLUME = 0.45  # 45% master playback volume

SOUND_FILENAMES: dict[str, str] = {
    "move": "move.wav",
    "capture": "capture.wav",
    "check": "check.wav",
    "special": "special.wav",
    "win": "win.wav",
    "lose": "lose.wav",
}

# Pool size per sound effect enables overlapping playback for rapid moves/events
_POOL_SIZES: dict[str, int] = {
    "move": 3,
    "capture": 3,
    "check": 2,
    "special": 2,
    "win": 2,
    "lose": 2,
}

# Target peak levels strictly within -6 dBFS .. -3 dBFS (~50% - 70% full scale)
_TARGET_PEAK_DBFS: dict[str, float] = {
    "move": -4.5,
    "capture": -4.2,
    "check": -4.8,
    "special": -5.0,
    "win": -5.2,
    "lose": -5.5,
}

DEFAULT_SOUNDS_DIR = Path(__file__).resolve().parent / "assets" / "sounds"


# ---------------------------------------------------------------------------
# Low-level DSP & Envelope Helpers
# ---------------------------------------------------------------------------
def _raised_cosine_attack_decay(t: float, attack_s: float, decay_tau: float) -> float:
    """Smooth attack ramp followed by natural exponential decay."""
    if t < 0.0:
        return 0.0
    if attack_s > 0.0 and t < attack_s:
        attack = 0.5 * (1.0 - math.cos(math.pi * (t / attack_s)))
    else:
        attack = 1.0
    return attack * math.exp(-t / decay_tau)


def _apply_edge_fades(samples: list[float], fade_in_s: float, fade_out_s: float) -> None:
    """Apply smooth raised-cosine fade-in and fade-out in-place (zero clicks)."""
    n = len(samples)
    if n == 0:
        return

    fade_in_n = min(n // 2, max(1, int(fade_in_s * SAMPLE_RATE)))
    for i in range(fade_in_n):
        samples[i] *= 0.5 * (1.0 - math.cos(math.pi * i / fade_in_n))

    fade_out_n = min(n // 2, max(1, int(fade_out_s * SAMPLE_RATE)))
    for i in range(fade_out_n):
        idx = n - 1 - i
        samples[idx] *= 0.5 * (1.0 - math.cos(math.pi * i / fade_out_n))


def _bandpass_filter(
    samples: list[float], low_hz: float, high_hz: float
) -> list[float]:
    """Simple one-pole high-pass + low-pass filter for shaping organic noise."""
    if not samples:
        return []
    dt = 1.0 / SAMPLE_RATE

    # High-pass stage
    rc_hp = 1.0 / (2.0 * math.pi * low_hz)
    alpha_hp = rc_hp / (rc_hp + dt)
    hp_out = [0.0] * len(samples)
    prev_x = samples[0]
    prev_y = 0.0
    for i, x in enumerate(samples):
        y = alpha_hp * (prev_y + x - prev_x)
        hp_out[i] = y
        prev_x = x
        prev_y = y

    # Low-pass stage
    rc_lp = 1.0 / (2.0 * math.pi * high_hz)
    alpha_lp = dt / (rc_lp + dt)
    lp_out = [0.0] * len(samples)
    y = 0.0
    for i, x in enumerate(hp_out):
        y = y + alpha_lp * (x - y)
        lp_out[i] = y

    return lp_out


def _normalize_and_quantize(
    samples: list[float], target_dbfs: float, fade_in_s: float, fade_out_s: float
) -> list[int]:
    """
    Apply smooth boundary fades, remove residual DC offset without disturbing
    zero endpoints, peak-normalize to target_dbfs, and quantize to 16-bit PCM.
    """
    n = len(samples)
    if n == 0:
        return []

    faded = list(samples)
    _apply_edge_fades(faded, fade_in_s=fade_in_s, fade_out_s=fade_out_s)

    # Windowed DC removal: subtract c * window so sum == 0 while endpoints stay 0
    window = [1.0] * n
    _apply_edge_fades(window, fade_in_s=fade_in_s, fade_out_s=fade_out_s)
    w_sum = sum(window)
    if w_sum > 1e-12:
        c = sum(faded) / w_sum
        dc_free = [x - c * w for x, w in zip(faded, window)]
    else:
        dc_free = faded

    peak = max(abs(s) for s in dc_free)
    if peak <= 1e-12:
        return [0] * n

    target_linear = 10.0 ** (target_dbfs / 20.0)
    scale = target_linear / peak

    pcm: list[int] = []
    for s in dc_free:
        val = int(round(s * scale * MAX_PCM_16))
        if val > MAX_PCM_16:
            val = MAX_PCM_16
        elif val < -MAX_PCM_16:
            val = -MAX_PCM_16
        pcm.append(val)
    return pcm


def _write_wav_file(path: Path, pcm_samples: list[int]) -> None:
    """Write mono 16-bit PCM WAV data atomically via a temporary file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(".wav.tmp")
    raw_bytes = struct.pack(f"<{len(pcm_samples)}h", *pcm_samples)
    with wave.open(str(tmp_path), "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(SAMPLE_WIDTH)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(raw_bytes)
    os.replace(tmp_path, path)


# ---------------------------------------------------------------------------
# Procedural Beach / Aqua Sound Synthesizers
# ---------------------------------------------------------------------------
def _synthesize_move() -> list[int]:
    """Standard Move (~105 ms): soft wooden/shell-on-sand tactile tap."""
    duration = 0.105
    n = int(duration * SAMPLE_RATE)

    rng = random.Random(101)
    raw_noise = [rng.uniform(-1.0, 1.0) for _ in range(n)]
    sand_noise = _bandpass_filter(raw_noise, low_hz=700.0, high_hz=2600.0)

    samples = [0.0] * n
    tau_sweep = 0.010
    for i in range(n):
        t = i / SAMPLE_RATE
        # Pitch-dropping warm wooden body (270 Hz -> 140 Hz)
        phi_body = 2.0 * math.pi * (140.0 * t + 130.0 * tau_sweep * (1.0 - math.exp(-t / tau_sweep)))
        body = (
            math.sin(phi_body) * math.exp(-t / 0.020)
            + 0.30 * math.sin(2.15 * phi_body) * math.exp(-t / 0.011)
        )
        # Gentle shell transient & sand-grain click
        shell_click = 0.22 * math.sin(2.0 * math.pi * 920.0 * t) * math.exp(-t / 0.007)
        sand_tap = 0.28 * sand_noise[i] * math.exp(-t / 0.006)
        samples[i] = body + shell_click + sand_tap

    return _normalize_and_quantize(
        samples,
        target_dbfs=_TARGET_PEAK_DBFS["move"],
        fade_in_s=0.002,
        fade_out_s=0.018,
    )


def _synthesize_capture() -> list[int]:
    """Capture (~165 ms): deeper driftwood impact + subtle water-droplet splash."""
    duration = 0.165
    n = int(duration * SAMPLE_RATE)

    rng = random.Random(202)
    raw_noise = [rng.uniform(-1.0, 1.0) for _ in range(n)]
    splash_noise = _bandpass_filter(raw_noise, low_hz=900.0, high_hz=3100.0)

    samples = [0.0] * n
    tau_wood = 0.014
    drop_delay = 0.016
    tau_drop = 0.022

    for i in range(n):
        t = i / SAMPLE_RATE
        # Deeper resonant driftwood thud (223 Hz -> 98 Hz)
        phi_wood = 2.0 * math.pi * (98.0 * t + 125.0 * tau_wood * (1.0 - math.exp(-t / tau_wood)))
        wood = (
            math.sin(phi_wood) * math.exp(-t / 0.034)
            + 0.34 * math.sin(2.42 * phi_wood) * math.exp(-t / 0.018)
            + 0.14 * math.sin(3.85 * phi_wood) * math.exp(-t / 0.010)
        )

        # Crisp water splash snap
        splash = 0.24 * splash_noise[i] * math.exp(-t / 0.018)

        # Subtle upward water-droplet bubble chirp (540 Hz -> 1060 Hz)
        droplet = 0.0
        dt = t - drop_delay
        if dt >= 0.0:
            phi_drop = 2.0 * math.pi * (
                540.0 * dt + 520.0 * (dt - tau_drop * (1.0 - math.exp(-dt / tau_drop)))
            )
            drop_env = _raised_cosine_attack_decay(dt, attack_s=0.005, decay_tau=0.028)
            droplet = 0.38 * math.sin(phi_drop) * drop_env

        samples[i] = wood + splash + droplet

    return _normalize_and_quantize(
        samples,
        target_dbfs=_TARGET_PEAK_DBFS["capture"],
        fade_in_s=0.002,
        fade_out_s=0.025,
    )


def _synthesize_check() -> list[int]:
    """Check (~250 ms): soft, clear sonar / sea-glass alert chime."""
    duration = 0.250
    n = int(duration * SAMPLE_RATE)

    samples = [0.0] * n
    f0 = 783.99  # G5: clear yet non-fatiguing
    for i in range(n):
        t = i / SAMPLE_RATE
        env_main = _raised_cosine_attack_decay(t, attack_s=0.006, decay_tau=0.085)
        env_shimmer = _raised_cosine_attack_decay(t, attack_s=0.004, decay_tau=0.045)
        env_glass = _raised_cosine_attack_decay(t, attack_s=0.002, decay_tau=0.020)

        sonar = (
            math.sin(2.0 * math.pi * f0 * t)
            + 0.25 * math.sin(2.0 * math.pi * (f0 + 2.5) * t)
            + 0.30 * math.sin(2.0 * math.pi * (f0 * 0.5) * t)
        ) * env_main
        fifth = 0.18 * math.sin(2.0 * math.pi * (f0 * 1.498) * t) * env_shimmer
        glass = 0.10 * math.sin(2.0 * math.pi * (f0 * 2.50) * t) * env_glass
        samples[i] = sonar + fifth + glass

    return _normalize_and_quantize(
        samples,
        target_dbfs=_TARGET_PEAK_DBFS["check"],
        fade_in_s=0.005,
        fade_out_s=0.045,
    )


def _synthesize_special() -> list[int]:
    """Castle / Promotion (~300 ms): smooth two-tone ascending coastal marimba/chime slide."""
    duration = 0.300
    n = int(duration * SAMPLE_RATE)

    f1 = 523.25  # C5
    f2 = 783.99  # G5
    t2_start = 0.105
    slide_start = 0.040
    slide_end = 0.130

    samples = [0.0] * n
    slide_phase = 0.0
    dt_step = 1.0 / SAMPLE_RATE

    for i in range(n):
        t = i / SAMPLE_RATE

        # Tone 1: warm C5 marimba bar
        env1 = _raised_cosine_attack_decay(t, attack_s=0.004, decay_tau=0.075)
        tone1 = (
            math.sin(2.0 * math.pi * f1 * t)
            + 0.24 * math.sin(2.0 * math.pi * (f1 * 0.5) * t)
            + 0.08 * math.sin(2.0 * math.pi * (f1 * 4.0) * t) * math.exp(-t / 0.010)
        ) * env1

        # Smooth ascending chime slide bridge from C5 -> G5
        if slide_start <= t <= slide_end:
            u = (t - slide_start) / (slide_end - slide_start)
            smooth_u = 0.5 * (1.0 - math.cos(math.pi * u))
            f_inst = f1 + (f2 - f1) * smooth_u
            slide_phase += 2.0 * math.pi * f_inst * dt_step
            slide_env = math.sin(math.pi * u) * 0.24
            slide = math.sin(slide_phase) * slide_env
        else:
            slide = 0.0

        # Tone 2: bright G5 marimba/chime arrival
        tone2 = 0.0
        dt2 = t - t2_start
        if dt2 >= 0.0:
            env2 = _raised_cosine_attack_decay(dt2, attack_s=0.005, decay_tau=0.095)
            tone2 = (
                1.05 * math.sin(2.0 * math.pi * f2 * dt2)
                + 0.25 * math.sin(2.0 * math.pi * (f2 * 0.5) * dt2)
                + 0.12 * math.sin(2.0 * math.pi * (f2 * 2.0) * dt2) * math.exp(-dt2 / 0.035)
            ) * env2

        samples[i] = tone1 + slide + tone2

    return _normalize_and_quantize(
        samples,
        target_dbfs=_TARGET_PEAK_DBFS["special"],
        fade_in_s=0.004,
        fade_out_s=0.055,
    )


def _synthesize_win() -> list[int]:
    """Victory (~1.35 s): warm, uplifting Cmaj7 coastal arpeggio (C5-E5-G5-B5)."""
    duration = 1.35
    n = int(duration * SAMPLE_RATE)

    # (onset_s, freq_hz, decay_tau_s, gain)
    notes = [
        (0.00, 523.25, 0.44, 0.90),  # C5
        (0.13, 659.25, 0.44, 0.88),  # E5
        (0.26, 783.99, 0.46, 0.92),  # G5
        (0.40, 987.77, 0.56, 1.00),  # B5
    ]

    samples = [0.0] * n
    for i in range(n):
        t = i / SAMPLE_RATE
        val = 0.0

        # Gentle C4 warm ocean-pad cushion under the arpeggio
        pad_env = _raised_cosine_attack_decay(t, attack_s=0.025, decay_tau=0.58)
        val += 0.24 * math.sin(2.0 * math.pi * 261.63 * t) * pad_env

        for onset, freq, tau, gain in notes:
            dt = t - onset
            if dt < 0.0:
                continue
            env = _raised_cosine_attack_decay(dt, attack_s=0.009, decay_tau=tau)
            env_h2 = _raised_cosine_attack_decay(dt, attack_s=0.007, decay_tau=tau * 0.45)
            env_h3 = _raised_cosine_attack_decay(dt, attack_s=0.005, decay_tau=tau * 0.25)
            note_sig = (
                math.sin(2.0 * math.pi * freq * dt) * env
                + 0.20 * math.sin(2.0 * math.pi * (2.0 * freq) * dt) * env_h2
                + 0.06 * math.sin(2.0 * math.pi * (3.0 * freq) * dt) * env_h3
            )
            val += gain * note_sig

        samples[i] = val

    return _normalize_and_quantize(
        samples,
        target_dbfs=_TARGET_PEAK_DBFS["win"],
        fade_in_s=0.008,
        fade_out_s=0.200,
    )


def _synthesize_lose() -> list[int]:
    """Defeat / Draw (~1.20 s): calm, reflective descending minor/suspended cadence."""
    duration = 1.20
    n = int(duration * SAMPLE_RATE)

    # Descending reflective cadence: A4 -> G4 -> E4 (+ soft A3/C4 resolution cushion)
    notes = [
        (0.00, 440.00, 0.34, 0.86),  # A4
        (0.24, 392.00, 0.34, 0.84),  # G4
        (0.48, 329.63, 0.48, 0.96),  # E4
    ]

    samples = [0.0] * n
    for i in range(n):
        t = i / SAMPLE_RATE
        val = 0.0

        for onset, freq, tau, gain in notes:
            dt = t - onset
            if dt < 0.0:
                continue
            env = _raised_cosine_attack_decay(dt, attack_s=0.014, decay_tau=tau)
            env_h2 = _raised_cosine_attack_decay(dt, attack_s=0.010, decay_tau=tau * 0.40)
            val += gain * (
                math.sin(2.0 * math.pi * freq * dt) * env
                + 0.14 * math.sin(2.0 * math.pi * (2.0 * freq) * dt) * env_h2
            )

        # Warm low resolution cushion on final note
        dt_res = t - 0.48
        if dt_res >= 0.0:
            res_env = _raised_cosine_attack_decay(dt_res, attack_s=0.030, decay_tau=0.50)
            val += (
                0.32 * math.sin(2.0 * math.pi * 220.00 * dt_res)
                + 0.18 * math.sin(2.0 * math.pi * 261.63 * dt_res)
            ) * res_env

        samples[i] = val

    return _normalize_and_quantize(
        samples,
        target_dbfs=_TARGET_PEAK_DBFS["lose"],
        fade_in_s=0.010,
        fade_out_s=0.220,
    )


_SYNTHESIZERS: dict[str, Callable[[], list[int]]] = {
    "move": _synthesize_move,
    "capture": _synthesize_capture,
    "check": _synthesize_check,
    "special": _synthesize_special,
    "win": _synthesize_win,
    "lose": _synthesize_lose,
}


def ensure_sound_assets(sounds_dir: Path | str | None = None) -> dict[str, Path]:
    """
    Generate any missing coastal .wav sound effects inside *sounds_dir*
    (defaults to `<project_root>/assets/sounds/`). Existing non-empty files
    are preserved. Returns a mapping from sound key to file Path.
    """
    target_dir = Path(sounds_dir) if sounds_dir is not None else DEFAULT_SOUNDS_DIR
    target_dir.mkdir(parents=True, exist_ok=True)

    paths: dict[str, Path] = {}
    for key, filename in SOUND_FILENAMES.items():
        wav_path = target_dir / filename
        if not wav_path.exists() or wav_path.stat().st_size == 0:
            synth_fn = _SYNTHESIZERS[key]
            pcm_samples = synth_fn()
            _write_wav_file(wav_path, pcm_samples)
        paths[key] = wav_path

    return paths


# ---------------------------------------------------------------------------
# SoundManager — QSoundEffect Pool & Playback Controller
# ---------------------------------------------------------------------------
class SoundManager(QObject):
    """
    Manages procedural coastal .wav asset generation and low-latency,
    overlapping audio playback via PySide6.QtMultimedia.QSoundEffect.
    """

    volume_changed = Signal(float)
    muted_changed = Signal(bool)

    def __init__(
        self,
        parent: QObject | None = None,
        sounds_dir: Path | str | None = None,
        initial_volume: float = DEFAULT_VOLUME,
    ):
        super().__init__(parent)
        self._volume = max(0.0, min(1.0, float(initial_volume)))
        self._muted = False
        self._sound_paths: dict[str, Path] = {}
        self._pools: dict[str, list[QSoundEffect]] = {}
        self._pool_indices: dict[str, int] = {}
        self._media_devices = None
        self._has_audio_output = False
        self._multimedia_ready = False

        # Always generate missing WAV assets on first run
        try:
            self._sound_paths = ensure_sound_assets(sounds_dir)
        except Exception:
            self._sound_paths = {}

        self._init_audio_backend()

    def _init_audio_backend(self) -> None:
        """Initialize QMediaDevices tracking and preloaded QSoundEffect pools safely."""
        if not _QT_MULTIMEDIA_AVAILABLE or QSoundEffect is None:
            self._multimedia_ready = False
            self._has_audio_output = False
            return

        try:
            if QMediaDevices is not None:
                self._media_devices = QMediaDevices(self)
                self._has_audio_output = len(QMediaDevices.audioOutputs()) > 0
                self._media_devices.audioOutputsChanged.connect(self._on_audio_outputs_changed)
            else:
                self._has_audio_output = True
        except Exception:
            self._media_devices = None
            self._has_audio_output = False

        # Preload QSoundEffect pools and keep strong references in self._pools
        try:
            for key, wav_path in self._sound_paths.items():
                pool_size = _POOL_SIZES.get(key, 2)
                effects: list[QSoundEffect] = []
                url = QUrl.fromLocalFile(str(wav_path))
                for _ in range(pool_size):
                    effect = QSoundEffect(self)
                    effect.setSource(url)
                    effect.setVolume(self._volume)
                    effect.setMuted(self._muted)
                    effects.append(effect)
                self._pools[key] = effects
                self._pool_indices[key] = 0
            self._multimedia_ready = True
        except Exception:
            self._pools.clear()
            self._pool_indices.clear()
            self._multimedia_ready = False

    def _on_audio_outputs_changed(self) -> None:
        """Update cached availability when audio devices are connected/disconnected."""
        if QMediaDevices is None:
            return
        try:
            self._has_audio_output = len(QMediaDevices.audioOutputs()) > 0
        except Exception:
            self._has_audio_output = False

    @property
    def sound_paths(self) -> dict[str, Path]:
        """Mapping of sound effect keys to generated .wav paths."""
        return dict(self._sound_paths)

    @property
    def has_audio_output(self) -> bool:
        """Whether at least one system audio output device is currently present."""
        return self._has_audio_output

    @property
    def volume(self) -> float:
        """Current playback volume in [0.0, 1.0]."""
        return self._volume

    @property
    def muted(self) -> bool:
        """Whether audio output is currently muted."""
        return self._muted

    def set_volume(self, volume: float) -> None:
        """Set master playback volume in [0.0, 1.0] across all sound effects."""
        clamped = max(0.0, min(1.0, float(volume)))
        if abs(clamped - self._volume) < 1e-6:
            return
        self._volume = clamped
        for effects in self._pools.values():
            for effect in effects:
                try:
                    effect.setVolume(self._volume)
                except Exception:
                    pass
        self.volume_changed.emit(self._volume)

    def set_muted(self, muted: bool) -> None:
        """Mute or unmute all sound effects."""
        muted_bool = bool(muted)
        if muted_bool == self._muted:
            return
        self._muted = muted_bool
        for effects in self._pools.values():
            for effect in effects:
                try:
                    effect.setMuted(self._muted)
                except Exception:
                    pass
        self.muted_changed.emit(self._muted)

    def toggle_mute(self) -> bool:
        """Toggle mute state and return the new muted value."""
        self.set_muted(not self._muted)
        return self._muted

    def play(self, sound_key: str) -> None:
        """
        Play the named sound effect without blocking the UI thread.
        Safely no-ops when muted, volume is zero, or no audio output is active.
        """
        if self._muted or self._volume <= 0.0:
            return
        if not self._multimedia_ready or not self._has_audio_output:
            return

        pool = self._pools.get(sound_key)
        if not pool:
            return

        idx = self._pool_indices.get(sound_key, 0)
        effect = pool[idx % len(pool)]
        self._pool_indices[sound_key] = (idx + 1) % len(pool)

        try:
            if effect.status() == QSoundEffect.Status.Error:
                return
            effect.setVolume(self._volume)
            effect.setMuted(False)
            effect.play()
        except Exception:
            pass

    def play_move_outcome(
        self,
        *,
        is_capture: bool = False,
        is_special: bool = False,
        is_check: bool = False,
        is_game_over: bool = False,
        is_victory: bool = False,
    ) -> str | None:
        """
        Play exactly one sound effect for a single chess ply based on strict event priority:
        Game Over (win / lose) > Check > Special (castle/promotion) > Capture > Standard Move.

        Returns the played sound key (or None if skipped/invalid).
        """
        if is_game_over:
            key = "win" if is_victory else "lose"
        elif is_check:
            key = "check"
        elif is_special:
            key = "special"
        elif is_capture:
            key = "capture"
        else:
            key = "move"

        self.play(key)
        return key
