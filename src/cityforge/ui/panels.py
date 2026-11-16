"""Right hand side panels: demand, budget, layers and settings."""

from __future__ import annotations

from typing import Any

import pygame

from cityforge import content as C
from cityforge.ui.widgets import Button, Checkbox, Collapsible, Slider, Tooltip

PANEL_RECT = pygame.Rect(12, 72, 232, 600)


class SidePanel:
    """Demand / budget / layers / settings panel."""

    def __init__(self) -> None:
        self.rect = pygame.Rect(PANEL_RECT.x, PANEL_RECT.y, PANEL_RECT.width, 560)
        self.collapsibles: list[Collapsible] = [
            Collapsible(rect=pygame.Rect(16, 8, 200, 30), title="Demand"),
            Collapsible(rect=pygame.Rect(16, 46, 200, 30), title="Budget"),
            Collapsible(rect=pygame.Rect(16, 82, 200, 30), title="Layers"),
            Collapsible(rect=pygame.Rect(16, 118, 200, 30), title="Settings"),
        ]
        self.layers_buttons: list[Any] = []
        self.disaster_button = Button(rect=pygame.Rect(16, 152, 200, 28), label="Trigger a disaster", kind="accent", on_click="trigger_disaster")
        self.tax_slider = Slider(rect=pygame.Rect(16, 180, 200, 16), value=float(C.TAX_BASELINE), min_value=float(C.TAX_BASELINE), max_value=float(C.TAX_BASELINE))
        self.disaster_checkbox = Checkbox(rect=pygame.Rect(16, 212, 200, 22), label="Disasters", checked=True, on_change="toggle_disasters")
        self.sound_checkbox = Checkbox(rect=pygame.Rect(16, 240, 200, 22), label="Sound", checked=True, on_change="toggle_sound")

    def draw(self, surface: pygame.Surface, snapshot: Any) -> None:
        self.rect.height = max(300, surface.get_height() - 130)
        pygame.draw.rect(surface, (21, 39, 58), self.rect, border_radius=8)
        pygame.draw.rect(surface, (39, 66, 90), self.rect, 1, border_radius=8)
        y = self.rect.y + 10
        for section in self.collapsibles:
            section.rect.y = y
            section.rect.height = 30
            self._draw_section(surface, section)
            y += 34
        self.disaster_button.rect.y = y + 6
        self._draw_button(surface, self.disaster_button, False)
        self.sound_checkbox.rect.y = self.disaster_button.rect.bottom + 18
        self._draw_checkbox(surface, self.sound_checkbox, False)
        self.disaster_checkbox.rect.y = self.sound_checkbox.rect.bottom + 18
        self._draw_checkbox(surface, self.disaster_checkbox, False)


def _draw_section(surface: pygame.Surface, section: Collapsible) -> None:
    from cityforge.ui.widgets import draw_collapsible

    draw_collapsible(surface, section, False)


def _draw_button(surface: pygame.Surface, button: Button, hovered: bool) -> None:
    from cityforge.ui.widgets import draw_button

    draw_button(surface, button, hovered, selected=button.kind == "accent")


def _draw_checkbox(surface: pygame.Surface, checkbox: Checkbox, hovered: bool) -> None:
    from cityforge.ui.widgets import draw_checkbox

    draw_checkbox(surface, checkbox, hovered)
