"""Cityforge application: game loop, camera, input mapping and wiring."""

from __future__ import annotations

import os
from typing import Any, Optional

import pygame

from cityforge import content as C
from cityforge.audio import SoundEngine
from cityforge.config import GameConfig, user_log_path, user_save_path
from cityforge.disasters import DisasterSystem
from cityforge.input import InputHandler
from cityforge.logging import get_logger, setup_logging
from cityforge.model import HudSnapshot
from cityforge.persistence import load_game, save_game
from cityforge.rendering import IsometricRenderer
from cityforge.simulation import CitySimulation
from cityforge.traffic import TrafficSystem
from cityforge.ui import UIManager
from cityforge.world import World

logger = get_logger("app")


class CityForgeApp:
    """Wires simulation, renderer, input, UI and audio into a running game."""

    def __init__(self, config: Optional[GameConfig] = None) -> None:
        self.config = config or GameConfig()
        self.renderer = IsometricRenderer(1280, 720, self.config.tile_width, self.config.tile_height)
        self.input = InputHandler()
        self.ui = UIManager(self.renderer)
        self.sound_engine = SoundEngine()
        self.world = World(seed=1, size=self.config.map_size, tile_width=self.config.tile_width, tile_height=self.config.tile_height)
        self.traffic = TrafficSystem(self.world)
        self.disasters = DisasterSystem(self.world)
        self.sim = CitySimulation(config=self.config, world=self.world, traffic=self.traffic, disasters=self.disasters)
        self.snapshot: HudSnapshot = self.sim.snapshot
        self._cam_x = 0.0
        self._cam_y = 0.0
        self._cam_z = 1.0
        self._acc = 0.0
        self._last_ticks = pygame.time.get_ticks()
        self._running = False
        self._tool = "road"
        self._layer: Optional[str] = None
        self._save_path = str(user_save_path(self.config))
        self._painting = False
        self._panning = False
        self.sim.on_rank_up = self._on_rank_up
        self.sim.on_autosave = self._on_autosave
        self.sim.on_funds_warning = self._on_funds_warning
        self.ui.on_tool_changed = self._on_tool_changed
        self.ui.on_layer_changed = self._on_layer_changed
        self.ui.on_speed_changed = self._on_speed_changed
        self.ui.on_tax_changed = self._on_tax_changed
        self.ui.on_disasters_toggled = self._on_disasters_toggled
        self.ui.on_sound_toggled = self._on_sound_toggled
        self.ui.on_name_changed = self._on_name_changed
        self.ui.on_disaster_triggered = self._on_disaster_triggered

    # ------------------------------------------------------------------ lifecycle
    def run(self) -> None:
        setup_logging(level=self.config.log_level, log_file=str(user_log_path(self.config)))
        pygame.init()
        self.sound_engine.init()
        self.sound_engine.prepare_all()
        self.renderer.resize(1280, 720)
        clock = pygame.time.Clock()
        self._running = True
        try:
            while self._running:
                self._frame()
                for event in pygame.event.get():
                    self._on_event(event)
                self._frame()
                pygame.display.flip()
                clock.tick(60)
        finally:
            self.sound_engine.shutdown()

    def stop(self) -> None:
        """Request the main loop to exit."""
        self._running = False

    # ------------------------------------------------------------------ loop
    def _frame(self) -> None:
        now = pygame.time.get_ticks()
        dt = max(0.0, (now - self._last_ticks) / 1000.0)
        self._last_ticks = now
        time = now / 1000.0
        ms = self.config.speed_steps_ms[int(self.sim.speed)]
        if ms > 0:
            self._acc += dt
            while self._acc >= ms / 1000.0:
                self._acc -= ms / 1000.0
                self.sim.tick()
        self._apply_camera(dt)
        self.renderer.camera = {"x": self._cam_x, "y": self._cam_y, "z": self._cam_z}
        hover = self._pick()
        self.renderer.hover = hover.tile
        self.renderer.hover_tool = hover.tool
        self.renderer.layer = self._layer
        self.renderer.render(self.world, self.sim, hover.tile, hover.tool, self._layer, time, self.disasters.shake)
        self.snapshot = self.sim.refresh_snapshot()
        hover_text = self._describe(hover.tile, hover.tool)
        self.ui.draw(pygame.display.get_surface(), self.sim, self.snapshot, hover_text)

    def _apply_camera(self, dt: float) -> None:
        speed = 0.7 * dt
        keys = self.input.keys
        if "w" in keys or "arrowup" in keys:
            self._cam_y += speed
        if "s" in keys or "arrowdown" in keys:
            self._cam_y -= speed
        if "a" in keys or "arrowleft" in keys:
            self._cam_x += speed
        if "d" in keys or "arrowright" in keys:
            self._cam_x -= speed

    # ------------------------------------------------------------------ input
    def _on_event(self, event: Any) -> None:
        intent = self.input.on_event(event)
        if intent is None:
            return
        for action in self.ui.handle(intent):
            self._apply_action(action)

    # ------------------------------------------------------------------ actions
    def _apply_action(self, action: str) -> None:
        logger.debug("action: %s", action)
        if action == "zoom_in":
            self._cam_z = min(2.2, self._cam_z * 1.1)
        elif action == "zoom_out":
            self._cam_z = max(0.5, self._cam_z * 0.9)
        elif action == "paint_start":
            self._painting = True
            self._paint()
        elif action == "paint_end":
            self._painting = False
        elif action == "pan_start":
            self._panning = True
        elif action == "pan_end":
            self._panning = False
        elif action == "speed_toggle":
            self._set_speed(0 if self.sim.speed else 1)
        elif action.startswith("speed:"):
            self._set_speed(int(action.split(":", 1)[1]))

    # ------------------------------------------------------------------ helpers
    def _set_speed(self, speed: int) -> None:
        self.sim.speed = speed
        self.snapshot = self.sim.refresh_snapshot()
        self.ui.speed = speed

    def _set_tool(self, kind: str) -> None:
        self._tool = kind

    def _pick(self) -> HoverInfo:
        position = self.input.hover
        if position is None:
            return HoverInfo(tile=None, tool=C.TOOLS.get(self._tool), ok=False)
        x, y = self.renderer.pick(position[0], position[1], self.world.size)
        tile = self.world.tile_at(x, y) if x is not None else None
        tool = C.TOOLS.get(self._tool) if self._tool else None
        ok = False
        if tile is not None and tool is not None:
            if tool.kind == "bull":
                ok = tile.kind is not None or tile.tree
            else:
                ok = not tile.water and tile.kind is None and self.sim.money >= tool.cost
        return HoverInfo(tile=tile, tool=tool, ok=ok)

    def _describe(self, tile: Any, tool: Any) -> Optional[str]:
        if tile is None or tool is None:
            return "Pick a tool and start with a road."
        text = f"Tile {tile.x},{tile.y}: "
        if tile.water:
            text += "water"
        elif not tile.kind:
            text += "forest" if tile.tree else "open land"
        else:
            text += tool.name
            if tile.level:
                text += f" level {tile.level}"
            if not tile.road:
                text += " (no road nearby)"
            elif tile.kind in ("res", "com", "ind") and not tile.powered:
                text += " (no power)"
        return text + f"   |   {tool.name}: {tool.info}"

    def _paint(self) -> None:
        position = self.input.hover
        if position is None or self._tool not in C.DRAG_TOOLS:
            return
        x, y = self.renderer.pick(position[0], position[1], self.world.size)
        tile = self.world.tile_at(x, y) if x is not None else None
        tool = C.TOOLS.get(self._tool)
        if tile is None or tool is None:
            return
        if tool.kind == "bull":
            if not tile.kind and not tile.tree:
                return
            if self.sim.money < tool.cost:
                return
            self.sim.money -= tool.cost
            tile.kind = None
            tile.level = 0
            tile.tree = False
            self.sound_engine.play("bull")
            return
        if tile.water or tile.kind or self.sim.money < tool.cost:
            return
        self.sim.money -= tool.cost
        tile.kind = tool.kind
        tile.level = 0
        tile.tree = False
        self.sound_engine.play("build")

    # ------------------------------------------------------------------ ui callbacks
    def _on_rank_up(self, rank: int) -> None:
        self.ui.show_toast(f"Your settlement grew into a {C.RANKS[rank][1].lower()}!")

    def _on_autosave(self) -> None:
        save_game(self.sim, self._save_path)
        self.ui.show_toast("Autosaved")

    def _on_funds_warning(self) -> None:
        self.ui.show_toast("Funds are negative. Raise taxes or cut services.")

    def _on_tool_changed(self, kind: str) -> None:
        self._tool = kind

    def _on_layer_changed(self, layer: Optional[str]) -> None:
        self._layer = layer

    def _on_speed_changed(self, speed: int) -> None:
        self.sim.speed = speed
        self.snapshot = self.sim.refresh_snapshot()
        self.ui.speed = speed

    def _on_tax_changed(self, tax: float) -> None:
        self.sim.tax = tax

    def _on_disasters_toggled(self, enabled: bool) -> None:
        self.disasters.enabled = enabled

    def _on_sound_toggled(self, enabled: bool) -> None:
        self.sound_engine.enabled = enabled

    def _on_name_changed(self, name: str) -> None:
        self.sim.name = name

    def _on_disaster_triggered(self) -> None:
        self.disasters.trigger_random(self.sim)


def main(argv: Optional[list[str]] = None) -> int:
    """Entry point for ``python -m cityforge``."""
    app = CityForgeApp(GameConfig())
    app.run()
    return 0
