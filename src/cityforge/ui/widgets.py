"""Reusable pygame based UI widgets (buttons, sliders, checkboxes, collapsibles)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

import pygame

COLORS = {
    "bg": (21, 39, 58),
    "panel": (21, 39, 58),
    "line": (39, 66, 90),
    "text": (228, 237, 245),
    "muted": (138, 163, 184),
    "accent": (63, 208, 176),
    "warn": (240, 182, 74),
    "bad": (229, 96, 77),
    "surface": (29, 55, 80),
    "input": (14, 28, 42),
}


@dataclass
class Button:
    rect: tuple[int, int, int, int]
    label: str
    on_click: Optional[Any] = None
    kind: str = "default"

    def contains(self, x: float, y: float) -> bool:
        px, py = int(x), int(y)
        cx, cy, cw, ch = self.rect
        return cx <= px < cx + cw and cy <= py < cy + ch


@dataclass
class Checkbox:
    rect: tuple[int, int, int, int]
    label: str
    checked: bool = False
    on_change: Optional[Any] = None


@dataclass
class Slider:
    rect: tuple[int, int, int, int]
    value: float
    min_value: float = 0.0
    max_value: float = 1.0
    on_change: Optional[Any] = None

    @property
    def fraction(self) -> float:
        span = self.max_value - self.min_value
        if span <= 0:
            return 0.0
        return (self.value - self.min_value) / span


@dataclass
class Collapsible:
    rect: tuple[int, int, int, int]
    title: str
    open: bool = True
    on_toggle: Optional[Any] = None


@dataclass
class Tooltip:
    text: str
    x: float
    y: float


@dataclass
class TextField:
    rect: tuple[int, int, int, int]
    value: str = ""
    active: bool = False
    on_commit: Optional[Any] = None


def draw_button(surface: pygame.Surface, button: Button, hovered: bool, selected: bool = False) -> None:
    x, y, w, h = button.rect
    accent = button.kind == "accent" or selected
    pygame.draw.rect(surface, COLORS["accent"] if accent else (COLORS["surface"] if hovered else COLORS["surface"]), button.rect, border_radius=5)
    pygame.draw.rect(surface, COLORS["accent"] if accent else COLORS["line"], button.rect, 1, border_radius=5)
    font = pygame.font.Font(None, 13)
    text_color = (6, 36, 29) if accent else COLORS["text"]
    text_surf = font.render(button.label, True, text_color)
    surface.blit(text_surf, (x + 6, y + 4, w - 12, h - 8))


def draw_checkbox(surface: pygame.Surface, checkbox: Checkbox, hovered: bool) -> None:
    x, y, w, h = checkbox.rect
    pygame.draw.rect(surface, COLORS["input"], checkbox.rect, border_radius=3)
    pygame.draw.rect(surface, COLORS["accent"] if checkbox.checked else COLORS["line"], checkbox.rect, 1, border_radius=3)
    if checkbox.checked:
        font = pygame.font.Font(None, 12)
        surface.blit(font.render("x", True, (6, 36, 29)), (x + 2, y + 1, w - 4, h - 4))
    font = pygame.font.Font(None, 12)
    surface.blit(font.render(checkbox.label, True, COLORS["muted"]), (x + 16, y + 2, w - 16, h - 2))


def draw_slider(surface: pygame.Surface, slider: Slider, hovered: bool) -> None:
    x, y, w, h = slider.rect
    pygame.draw.rect(surface, COLORS["input"], slider.rect, border_radius=4)
    pygame.draw.rect(surface, COLORS["accent"], (x, y, max(0, int(w * slider.fraction)), h), border_radius=4)
    pygame.draw.rect(surface, COLORS["line"], slider.rect, 1, border_radius=4)


def draw_collapsible(surface: pygame.Surface, section: Collapsible, hovered: bool) -> None:
    x, y, w, h = section.rect
    pygame.draw.rect(surface, COLORS["input"], section.rect, border_radius=5)
    pygame.draw.rect(surface, COLORS["line"], section.rect, 1, border_radius=5)
    font = pygame.font.Font(None, 13)
    marker = "v" if section.open else ">"
    surface.blit(font.render(marker + "  " + section.title, True, COLORS["text"]), (x + 6, y + 5, w - 12, h - 6))


def draw_tooltip(surface: pygame.Surface, tooltip: Optional[Tooltip]) -> None:
    if tooltip is None:
        return
    font = pygame.font.Font(None, 12)
    text = font.render(tooltip.text, True, COLORS["text"])
    rect = text.get_rect()
    x = min(tooltip.x + 14, surface.get_width() - rect.width - 8)
    y = tooltip.y + 18
    panel = pygame.Rect(x - 6, y - 6, rect.width + 12, rect.height + 12)
    pygame.draw.rect(surface, (11, 24, 34), panel, border_radius=6)
    pygame.draw.rect(surface, COLORS["line"], panel, 1, border_radius=6)
    surface.blit(text, (x, y))


def draw_text_field(surface: pygame.Surface, field: TextField, hovered: bool) -> None:
    x, y, w, h = field.rect
    pygame.draw.rect(surface, COLORS["input"], field.rect, border_radius=4)
    pygame.draw.rect(surface, COLORS["accent"] if field.active else COLORS["line"], field.rect, 1, border_radius=4)
    font = pygame.font.Font(None, 12)
    surface.blit(font.render(field.value, True, COLORS["text"]), (x + 6, y + 2, w - 12, h - 4))
