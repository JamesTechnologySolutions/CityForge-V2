"""Optional thin JavaScript webview bridge for the Cityforge UI.

The desktop runtime renders the UI with pygame.  For the modern, responsive
web based UI (``web/``) the Python engine exposes a small JSON friendly API
that a plain HTML/CSS/vanilla-JS frontend can drive through a webview such as
``pywebview`` or Qt WebEngine.
"""

from __future__ import annotations

from typing import Any, Optional


class WebUiBridge:
    """JS -> Python bridge object used by the optional web frontend."""

    def __init__(self, app: Any) -> None:
        self.app = app

    def get_state(self) -> dict[str, Any]:
        """Return the current HUD snapshot as a JSON friendly dict."""
        return {
            "money": self.app.sim.money,
            "day": self.app.sim.day,
            "tax": self.app.sim.tax,
            "speed": self.app.sim.speed,
            "name": self.app.sim.name,
            "pop": self.app.sim.pop,
            "jobs": self.app.sim.jobs,
            "happy": self.app.sim.happy,
            "dem": dict(self.app.sim.dem),
            "inc": self.app.sim.inc,
            "exp": self.app.sim.exp,
            "rank": self.app.sim.rank,
        }

    def set_tool(self, kind: str) -> bool:
        """Select a tool from the web frontend. Returns True on success."""
        from cityforge import content as C

        if kind not in C.TOOLS and kind != "bull":
            return False
        self.app._tool = kind
        self.app._on_tool_changed(kind)
        return True

    def place_tile(self, x: int, y: int, kind: Optional[str]) -> bool:
        """Place or remove a tile from the web frontend."""
        from cityforge import content as C

        tile = self.app.world.tile_at(x, y)
        if tile is None:
            return False
        if kind == "bull":
            if not tile.kind and not tile.tree:
                return False
            if self.app.sim.money < C.TOOLS["bull"].cost:
                return False
            self.app.sim.money -= C.TOOLS["bull"].cost
            tile.kind = None
            tile.level = 0
            tile.tree = False
            self.app.sound_engine.play("bull")
            return True
        definition = C.TOOLS.get(kind)
        if definition is None or tile.water or tile.kind or self.app.sim.money < definition.cost:
            return False
        self.app.sim.money -= definition.cost
        tile.kind = kind
        tile.level = 0
        tile.tree = False
        self.app.sound_engine.play("build")
        return True
