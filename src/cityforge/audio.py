"""Synthesized sound effects (Web Audio API compatible waveforms, pygame mixer)."""

from __future__ import annotations

import array
import math
import random
from typing import Any

SAMPLE_RATE: int = 44100


class SoundEngine:
    """Small synthesized sound player.

    The original prototype synthesized every effect with the Web Audio API.
    This port renders equivalent waveforms (tones and noise bursts) into raw
    mono 16-bit PCM buffers and plays them through the pygame mixer, so no
    audio assets are required.
    """

    def __init__(self) -> None:
        self.enabled: bool = True
        self.available: bool = True
        self._sounds: dict[str, Any] = {}
        self._mixer: Any = None
        self._initialized: bool = False
        self.sample_rate: int = SAMPLE_RATE

    # ------------------------------------------------------------------ lifecycle
    def init(self) -> None:
        """Initialise the mixer (idempotent)."""
        if self._initialized:
            return
        self._initialized = True
        try:
            import pygame

            pygame.mixer.pre_init(frequency=SAMPLE_RATE, size=-16, channels=1, buffer=512)
            pygame.mixer.init()
            self._mixer = pygame.mixer
            self.available = True
        except Exception:
            self.available = False

    def shutdown(self) -> None:
        if self._mixer is not None:
            try:
                import pygame

                pygame.mixer.quit()
            except Exception:  # pragma: no cover - defensive
                pass
            self._mixer = None

    # ------------------------------------------------------------------ playback
    def play(self, name: str) -> None:
        """Play the named synthesized effect."""
        if not self.enabled or not self.available:
            return
        sound = self._sounds.get(name)
        if sound is None:
            return
        try:
            sound.play()
        except Exception:
            self.available = False

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable the sound engine."""
        self.enabled = bool(enabled)

    def prepare_all(self) -> None:
        """Synthesize and cache every known effect."""
        self._sounds["build"] = self._make(self._parts_build())
        self._sounds["bull"] = self._make(self._parts_bull())
        self._sounds["rank"] = self._make(self._parts_rank())
        self._sounds["siren"] = self._make(self._parts_siren())
        self._sounds["quake"] = self._make(self._parts_quake())
        self._sounds["wind"] = self._make(self._parts_wind())

    # ------------------------------------------------------------------ synthesis
    def _parts_build(self) -> list[list[float]]:
        tone_a = self._tone_samples(220.0, 0.09, "square", 0.12, slide=160.0)
        tone_b = self._tone_samples(440.0, 0.08, "triangle", 0.1, delay=0.06)
        silence = [0.0] * int(self.sample_rate * 0.06)
        return [tone_a, silence, tone_b]

    def _parts_bull(self) -> list[list[float]]:
        return [self._noise_samples(0.25, 0.35)]

    def _parts_rank(self) -> list[list[float]]:
        tones = []
        for index, freq in enumerate((523.0, 659.0, 784.0, 1046.0)):
            tones.append(self._tone_samples(freq, 0.3, "triangle", 0.18, delay=index * 0.12))
        return tones

    def _parts_siren(self) -> list[list[float]]:
        parts: list[list[float]] = []
        for index in range(4):
            delay = index * 0.28
            tone = self._tone_samples(700.0 + (200.0 if index % 2 else 0.0), 0.28, "sawtooth", 0.08, delay=delay)
            parts.append([0.0] * int(self.sample_rate * delay) + tone if delay else tone)
        return parts

    def _parts_quake(self) -> list[list[float]]:
        tone = self._tone_samples(55.0, 1.4, "sine", 0.4, slide=-25.0)
        noise = self._noise_samples(1.6, 0.6)
        return [tone, noise]

    def _parts_wind(self) -> list[list[float]]:
        return [self._noise_samples(1.8, 0.3)]

    def _tone_samples(self, freq: float, duration: float, wave: str, volume: float, slide: float = 0.0, delay: float = 0.0) -> list[float]:
        count = max(1, int(self.sample_rate * duration))
        freq_end = freq + slide if slide else freq
        slope = math.log(freq_end / freq) / duration if freq_end != freq else 0.0
        samples: list[float] = []
        for index in range(count):
            local = index / self.sample_rate
            freq_here = freq * math.exp(slope * local) if slope else freq
            env = min(1.0, local / (0.005 * self.sample_rate)) if local < 0.005 * self.sample_rate else (
                min(1.0, (duration - local) / (0.01 * self.sample_rate)) if local > duration - 0.01 * self.sample_rate else 1.0
            )
            phase = math.sin(2 * math.pi * freq_here * local)
            if wave == "square":
                phase = math.copysign(abs(phase), math.sin(2 * math.pi * freq_here * local) or 1.0)
            elif wave == "sawtooth":
                phase = 2 * (local * freq_here - math.floor(local * freq_here + 0.5)) - 1
            elif wave == "triangle":
                phase = (2 / math.pi) * math.asin(math.sin(2 * math.pi * freq_here * local))
            samples.append(phase * volume * env)
        if delay:
            samples = [0.0] * int(self.sample_rate * delay) + samples
        return samples

    def _noise_samples(self, duration: float, volume: float, freq: float = 0.0, delay: float = 0.0) -> list[float]:
        count = max(1, int(self.sample_rate * duration))
        samples: list[float] = []
        for index in range(count):
            local = index / self.sample_rate
            env = min(1.0, local / (0.005 * self.sample_rate)) if local < 0.005 * self.sample_rate else (
                min(1.0, (duration - local) / (0.01 * self.sample_rate)) if local > duration - 0.01 * self.sample_rate else 1.0
            )
            samples.append((random.random() * 2 - 1) * volume * env)
        if delay:
            samples = [0.0] * int(self.sample_rate * delay) + samples
        return samples

    def _make(self, parts: list[list[float]]) -> Any:
        samples: list[float] = []
        for part in parts:
            samples.extend(part)
        raw = array.array("h", [int(max(-1.0, min(1.0, value)) * 32767) for value in samples])
        try:
            import pygame

            return pygame.mixer.Sound(buffer=bytes(raw))
        except Exception:
            self.available = False
            return None
