"""Left hand tool palette."""

from __future__ import annotations

from typing import Any, Optional

import pygame

from cityforge import content as C

TOOLBAR_RECT = pygame.Rect(12, 72, 188, 420)
BUTTON_HEIGHT = 24
BUTTON_GAP = 4
GROUP_GAP = 10


class ToolsPanel:
    """Builds the grouped tool palette from :data:`cityforge.content.GROUPS`."""

    def __init__(self) -> None:
        self.buttons: list[Any] = []
        self.build()

    def build(self) -> None:
        self.buttons = []
        y = TOOLBAR_RECT.y + 8
        font = pygame.font.Font(None, 11)
        for group, kinds in C.GROUPS:
            group_height = font.size(group)[1]
            self.buttons.append(("group", group, pygame.Rect(TOOLBAR_RECT.x + 10, y, TOOLBAR_RECT.width - 20, group_height), None))
            y += group_height + 2
            for kind in kinds:
                definition = C.TOOLS[kind]
                rect = pygame.Rect(TOOLBAR_RECT.x + 8, y, TOOLBAR_RECT.width - 16, BUTTON_HEIGHT)
                self.buttons.append(("button", kind, rect, definition))
                y += BUTTON_HEIGHT + BUTTON_GAP
            y += GROUP_GAP

    def hit(self, x: float, y: float) -> Optional[str]:
        """Return the tool kind hit by the pointer, if any."""
        for entry in self.buttons:
            if entry[0] != "button":
                continue
            _, kind, rect, _definition = entry
            if rect.collidepoint(int(x), int(y)):
                return kind
        return None

    def active_button(self, tool: str) -> bool:
        for entry in self.buttons:
            if entry[0] != "button":
                continue
            _, kind, _rect, _definition = entry
            if kind == tool:
                return True
        return False
