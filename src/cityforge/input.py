"""Input abstraction: translates host events into game intents."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

MouseMove = tuple[float, float]
MouseButtonDown = tuple[float, float, int]
MouseButtonUp = tuple[Optional[int], ...]
MouseWheel = tuple[float, float, int]
KeyEvent = tuple[str, bool]

MOUSEBUTTONDOWN = 1
MOUSEBUTTONUP = 2
MOUSEMOTION = 3
MOUSEWHEEL = 4
KEYDOWN = 5
KEYUP = 6


@dataclass(frozen=True)
class Intent:
    """A single normalised input action."""

    kind: str
    x: float = 0.0
    y: float = 0.0
    button: Optional[int] = None
    delta: int = 0
    key: str = ""


class InputHandler:
    """Collects raw host input and emits normalised intents."""

    def __init__(self) -> None:
        self.keys: set[str] = set()
        self.painting: bool = False
        self.panning: bool = False
        self.hover: Optional[tuple[float, float]] = None

    # ------------------------------------------------------------------ events
    def on_event(self, event: Any) -> Optional[Intent]:
        """Translate a single host event into an intent (``None`` when unused)."""
        etype = int(getattr(event, "type", -1))
        if etype == MOUSEBUTTONDOWN:
            return Intent(kind="mouse_down", x=float(getattr(event, "pos", (0, 0))[0]), y=float(getattr(event, "pos", (0, 0))[1]), button=int(getattr(event, "button", 0)))
        if etype == MOUSEBUTTONUP:
            return Intent(kind="mouse_up", button=int(getattr(event, "button", 0)))
        if etype == MOUSEMOTION:
            x, y = (float(getattr(event, "pos", (0, 0))[0]), float(getattr(event, "pos", (0, 0))[1]))
            self.hover = (x, y)
            return Intent(kind="mouse_move", x=x, y=y)
        if etype == MOUSEWHEEL:
            return Intent(kind="mouse_wheel", x=float(getattr(event, "pos", (0, 0))[0]), y=float(getattr(event, "pos", (0, 0))[1]), delta=int(getattr(event, "y", 0)))
        if etype == KEYDOWN:
            key = str(getattr(event, "key", ""))
            self.keys.add(key)
            return Intent(kind="key_down", key=key)
        if etype == KEYUP:
            key = str(getattr(event, "key", ""))
            self.keys.discard(key)
            return Intent(kind="key_up", key=key)
        return None

    def text_char(self, char: str) -> None:
        """Feed a text character into the active text field (UI concern)."""
        if char:
            self.keys.add(char)
