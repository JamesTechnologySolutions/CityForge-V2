"""UI composition root: input handling, panels, toasts and frame drawing."""

from __future__ import annotations

import math
import time as _time
from typing import Any, Optional

import pygame

from cityforge import content as C
from cityforge.model import HudSnapshot
from cityforge.ui.panels import SidePanel
from cityforge.ui.toolbar import ToolsPanel
from cityforge.ui.widgets import Button, Checkbox, Collapsible, Slider, TextField, Tooltip, draw_button, draw_checkbox, draw_slider, draw_text_field, draw_tooltip

ACCENT = (63, 208, 176)
TOAST_DURATION = 2.6


class UIManager:
    """Owns all UI state and renders the HUD chrome on top of the renderer."""

    def __init__(self, renderer: Any) -> None:
        self.renderer = renderer
        self.tools = ToolsPanel()
        self.side = SidePanel()
        self.tool = "road"
        self.layer: Optional[str] = None
        self.speed = 1
        self.tax = float(C.TAX_BASELINE)
        self.disasters = True
        self.sound = True
        self.toast_message: Optional[str] = None
        self.toast_until: float = 0.0
        self.name_field = TextField(rect=(150, 12, 90, 20), value="Newtown", on_commit="name_changed")
        self.tooltip: Optional[Tooltip] = None
        self.name_active = False

    # ------------------------------------------------------------------ state
    def sync_from_sim(self, sim: Any, snapshot: HudSnapshot) -> None:
        self.tax = float(snapshot.tax)
        self.speed = int(snapshot.speed)
        self.disasters = True  # disasters toggle lives in UI state; kept in sync via callbacks
        self.sound = True

    def show_toast(self, message: str) -> None:
        self.toast_message = message
        self.toast_until = _time.monotonic() + TOAST_DURATION

    # ------------------------------------------------------------------ input
    def handle(self, intent: Any, x: float, y: float) -> list[Any]:
        actions: list[Any] = []
        if intent.kind == "mouse_move":
            self._hover_pos = (x, y)
            return actions
        if intent.kind == "mouse_down":
            if intent.button == 0:
                self._pressed_button = "left"
            else:
                self._pressed_button = "right"
            return actions
        if intent.kind == "mouse_up":
            self._pressed_button = None
            return actions
        if intent.kind == "mouse_wheel":
            return [f"zoom_{intent.delta}"]
        if intent.kind == "key_down":
            key = intent.key
            if key == "escape":
                return ["tool_cancel"]
            if key == " ":
                return ["speed_toggle"]
            if key in ("1", "2", "3"):
                return [f"speed_{key}"]
            if key in ("w", "arrowup", "s", "arrowdown", "a", "arrowleft", "d", "arrowright"):
                return [f"key_{key}"]
            return actions
        if intent.kind == "key_up":
            return actions
        return actions

    def handle_key_down(self, key: str) -> list[Any]:
        if key == "escape":
            return ["tool_cancel"]
        if key == " ":
            return ["speed_toggle"]
        if key in ("1", "2", "3"):
            return [f"speed_{key}"]
        if key in ("w", "arrowup", "s", "arrowdown", "a", "arrowleft", "d", "arrowright"):
            return [f"key_{key}"]
        return []

    # ------------------------------------------------------------------ frame
    def draw(self, surface: pygame.Surface, sim: Any, snapshot: HudSnapshot, hover_text: Optional[str]) -> None:
        self._draw_top_bar(surface, snapshot)
        self.tools.draw(surface)
        self.side.draw(surface, snapshot)
        self._draw_toast(surface)
        self._draw_info(surface, hover_text)

    def _draw_top_bar(self, surface: pygame.Surface, snapshot: HudSnapshot) -> None:
        pygame.draw.rect(surface, (24, 48, 73), (0, 0, surface.get_width(), 58))
        pygame.draw.rect(surface, ACCENT, (0, 58, surface.get_width(), 2))
        font = pygame.font.Font(None, 20)
        brand = font.render("Cityforge 2", True, ACCENT)
        surface.blit(brand, (16, 12))
        stats = [
            ("City", snapshot.name),
            ("Rank", snapshot.rank_name),
            ("Funds", f"${round(snapshot.money)}"),
            ("Date", f"{snapshot.month_name} Y{snapshot.year}"),
            ("Pop", f"{round(snapshot.pop)}"),
            ("Jobs", f"{round(snapshot.jobs)}"),
            ("Happy", f"{round(snapshot.happy)}%"),
        ]
        x = 150
        for label, value in stats:
            small = pygame.font.Font(None, 10).render(label, True, (138, 163, 184))
            big = pygame.font.Font(None, 14).render(value, True, (228, 237, 245))
            surface.blit(small, (x, 8))
            surface.blit(big, (x, 20))
            x += 86
        # controls
        buttons = [
            (pygame.Rect(surface.get_width() - 260, 12, 46, 26), f"{self.speed}x"),
            (pygame.Rect(surface.get_width() - 206, 12, 46, 26), "Pause"),
            (pygame.Rect(surface.get_width() - 152, 12, 46, 26), "Save"),
            (pygame.Rect(surface.get_width() - 98, 12, 46, 26), "Load"),
            (pygame.Rect(surface.get_width() - 44, 12, 46, 26), "New"),
        ]
        for rect, label in buttons:
            button = Button(rect=rect, label=label, kind="accent" if label in ("Pause",) else "default", on_click=label)
            self._draw_button(surface, button, False)

    def _draw_info(self, surface: pygame.Surface, hover_text: Optional[str]) -> None:
        font = pygame.font.Font(None, 12)
        text = font.render(hover_text or "Pick a tool and start with a road.", True, (138, 163, 184))
        rect = text.get_rect()
        surface.blit(text, (16, surface.get_height() - 24, surface.get_width() - 32, 20))

    def _draw_toast(self, surface: pygame.Surface) -> None:
        if not self.toast_message:
            return
        now = _time.monotonic()
        if now > self.toast_until:
            self.toast_message = None
            return
        font = pygame.font.Font(None, 14)
        text = font.render(self.toast_message, True, (228, 237, 245))
        rect = text.get_rect()
        surface.blit(text, ((surface.get_width() - rect.width) // 2, surface.get_height() - 60, rect.width, rect.height))

    def _draw_button(self, surface: pygame.Surface, button: Button, hovered: bool) -> None:
        draw_button(surface, button, hovered, selected=button.kind == "accent")

    def _draw_checkbox(self, surface: pygame.Surface, checkbox: Checkbox, hovered: bool) -> None:
        draw_checkbox(surface, checkbox, hovered)
