"""Tests for the input abstraction."""

from types import SimpleNamespace

from cityforge.input import InputHandler


def _key_event(key: str, down: bool, event_type: int) -> SimpleNamespace:
    return SimpleNamespace(type=event_type, key=key)


def test_input_handler_starts_idle() -> None:
    handler = InputHandler()
    assert handler.hover is None
    assert not handler.painting
    assert not handler.panning


def test_input_handler_key_tracking() -> None:
    handler = InputHandler()
    intent = handler.on_event(_key_event("w", down=True, event_type=5))
    assert intent is not None and intent.key == "w"
    handler.on_event(_key_event("w", down=False, event_type=6))
    assert "w" not in handler.keys


def _key_event(key: str, down: bool, event_type: int) -> object:
    return type("KeyEvent", (), {"type": event_type, "key": key})()
