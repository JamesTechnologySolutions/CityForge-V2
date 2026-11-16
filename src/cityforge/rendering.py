"""Isometric tile renderer (pygame-ce backend)."""

from __future__ import annotations

import math
import random
from typing import Any, Optional

import pygame

from cityforge import content as C
from cityforge.model import Car, Tile
from cityforge.world import World

BACKGROUND_COLOR = (11, 24, 34)
FIRE_COLORS: tuple[tuple[int, int, int], ...] = ((255, 176, 46), (255, 90, 31))
SMOKE_COLOR = (210, 215, 220)


def _hex_to_rgb(color: str, factor: float = 1.0) -> tuple[int, int, int]:
    return (
        max(0, min(255, int(int(color[1:3], 16) * factor))),
        max(0, min(255, int(int(color[3:5], 16) * factor))),
        max(0, min(255, int(int(color[5:7], 16) * factor))),
    )


def _shade(color: tuple[int, int, int], factor: float) -> tuple[int, int, int]:
    return (max(0, min(255, int(color[0] * factor))), max(0, min(255, int(color[1] * factor))), max(0, min(255, int(color[2] * factor))))


def _hsl(h: float, s: float, l: float) -> tuple[int, int, int]:
    c = (1 - abs(2 * l - 1)) * s
    hp = h / 60.0
    x = c * (1 - abs((hp % 2) - 1))
    m = l - c / 2.0
    if hp < 1:
        rgb = (c, x, 0.0)
    elif hp < 2:
        rgb = (x, c, 0.0)
    elif hp < 3:
        rgb = (0.0, c, x)
    elif hp < 4:
        rgb = (0.0, x, c)
    elif hp < 5:
        rgb = (x, 0.0, c)
    else:
        rgb = (c, 0.0, x)
    return (int((rgb[0] + m) * 255), int((rgb[1] + m) * 255), int((rgb[2] + m) * 255))


class IsometricRenderer:
    """Draws the isometric city onto a pygame surface."""

    def __init__(self, width: int, height: int, tile_width: int, tile_height: int) -> None:
        self.width = width
        self.height = height
        self.tile_width = tile_width
        self.tile_height = tile_height
        self.surface = pygame.Surface((width, height))
        self.fx = pygame.Surface((width, height), pygame.SRCALPHA)
        self.camera: dict[str, float] = {"x": 0.0, "y": 0.0, "z": 1.0}
        self.hover: Optional[Tile] = None
        self.hover_tool: Optional[Any] = None
        self.layer: Optional[str] = None
        self.time: float = 0.0
        self.shake: float = 0.0

    # ------------------------------------------------------------------ public API
    def resize(self, width: int, height: int) -> None:
        self.width = width
        self.height = height
        self.surface = pygame.Surface((width, height))
        self.fx = pygame.Surface((width, height), pygame.SRCALPHA)

    def pick(self, px: float, py: float, size: int) -> Optional[tuple[int, int]]:
        """Map screen coordinates back to tile coordinates."""
        cam = self.camera
        wx = (px - cam["x"]) / cam["z"]
        wy = (py - cam["y"]) / cam["z"]
        x = round(((wy - self.tile_height / 2) / (self.tile_height / 2) + wx / (self.tile_width / 2)) / 2)
        y = round(((wy - self.tile_height / 2) / (self.tile_height / 2) - wx / (self.tile_width / 2)) / 2)
        if 0 <= x < size and 0 <= y < size:
            return (x, y)
        return None

    def render(
        self,
        world: World,
        sim: Any,
        hover_tile: Optional[Tile],
        hover_tool: Optional[Any],
        layer: Optional[str],
        time: float,
        shake: float,
    ) -> None:
        self.time = time
        self.shake = shake
        self.layer = layer
        self.hover = hover_tile
        self.hover_tool = hover_tool
        self.surface.fill(BACKGROUND_COLOR)
        self.fx.fill((0, 0, 0, 0))
        ox = (random.random() - 0.5) * self.shake if shake > 0.3 else 0.0
        oy = (random.random() - 0.5) * self.shake if shake > 0.3 else 0.0
        self._draw_world(world, sim, ox, oy)
        if hover_tile is not None and hover_tool is not None:
            self._draw_hover(world, sim, hover_tile, hover_tool, ox, oy)
        self.surface.blit(self.fx, (0, 0))

    # ------------------------------------------------------------------ world
    def _draw_world(self, world: World, sim: Any, ox: float, oy: float) -> None:
        cam = self.camera
        z = cam["z"]
        x0 = -cam["x"] / z
        y0 = -cam["y"] / z
        x1 = (self.width - cam["x"]) / z
        y1 = (self.height - cam["y"]) / z
        size = world.size
        buckets: dict[int, list[Car]] = {}
        for car in sim.traffic.cars:
            key = car.ny * size + car.nx if car.nx >= 0 and car.p >= 0.5 else car.y * size + car.x
            buckets.setdefault(key, []).append(car)
        tw = self.tile_width
        th = self.tile_height
        for y in range(size):
            for x in range(size):
                sx = (x - y) * tw / 2
                sy = (x + y) * th / 2
                if sx < x0 - tw or sx > x1 + tw or sy > y1 + 100 or sy + th < y0:
                    continue
                tile = world.tiles[y * size + x]
                cx = sx + ox
                cy = sy + th / 2 + oy
                if tile.water:
                    self._diamond(cx, cy, tw / 2, th / 2, _hsl(200, 0.55, 34 + 4 * math.sin(self.time * 1.2 + x * 0.7 + y * 0.5)))
                    continue
                shade_value = ((((x * 73856093) ^ (y * 19349663)) & 0xFFFFFFFF) % 100) / 100
                self._diamond(cx, cy, tw / 2, th / 2, _hsl(95 + shade_value * 12, 0.38, 42 + shade_value * 6))
                if tile.tree:
                    self._tree(cx, cy + 3, 1.0)
                    continue
                if not tile.kind:
                    continue
                if self.layer:
                    self._overlay(tile, y * size + x, cx, cy, sim)
                if tile.kind == "road":
                    self._road(world, tile, x, y, cx, cy)
                    self._cars(world, buckets, x, y)
                else:
                    self._building(world, sim, tile, x, y, cx, cy)
                if tile.fire:
                    self._fire(cx, cy)
                    self._smoke(cx, cy - 12)

    # ------------------------------------------------------------------ primitives
    def _poly_surface(self, surface: Any, points: list[tuple[float, float]], color: tuple[int, int, int]) -> None:
        pygame.draw.polygon(surface, color, [(int(x), int(y)) for x, y in points])

    def _poly(self, points: list[tuple[float, float]], color: tuple[int, int, int]) -> None:
        self._poly_surface(self.surface, points, color)

    def _poly_fx(self, points: list[tuple[float, float]], color: tuple[int, int, int, int]) -> None:
        pygame.draw.polygon(self.fx, color, [(int(x), int(y)) for x, y in points])

    def _diamond(self, cx: float, cy: float, rx: float, ry: float, color: tuple[int, int, int]) -> None:
        self._poly([(cx, cy - ry), (cx + rx, cy), (cx, cy + ry), (cx - rx, cy)], color)

    def _diamond_fx(self, cx: float, cy: float, rx: float, ry: float, color: tuple[int, int, int, int]) -> None:
        self._poly_fx([(cx, cy - ry), (cx + rx, cy), (cx, cy + ry), (cx - rx, cy)], color)

    def _box(self, cx: float, cy: float, f: float, h: float, col: tuple[int, int, int], win: bool) -> None:
        a = self.tile_width / 2 * f
        b = self.tile_height / 2 * f
        self._poly([(cx - a, cy), (cx, cy + b), (cx, cy + b - h), (cx - a, cy - h)], _shade(col, 0.78))
        self._poly([(cx, cy + b), (cx + a, cy), (cx + a, cy - h), (cx, cy + b - h)], _shade(col, 0.6))
        self._poly([(cx - a, cy - b - h), (cx + a, cy - b - h), (cx + a, cy - h), (cx - a, cy - h)], _shade(col, 1.1))
        if win:
            step = 8
            window_y = 5
            while window_y + step < h:
                for u0, u1 in ((0.2, 0.4), (0.6, 0.8)):
                    x0 = cx - a + u0 * a
                    x1 = cx - a + u1 * a
                    y0 = cy - b + u0 * b - window_y
                    y1 = cy - b + u1 * b - (window_y + step)
                    self._poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], (255, 233, 168))
                window_y += step

    def _roof(self, cx: float, cy: float, f: float, h: float, col: tuple[int, int, int], r: float) -> None:
        a = self.tile_width / 2 * f
        b = self.tile_height / 2 * f
        top_left = (cx, cy - b - h)
        top_right = (cx + a, cy - h)
        bottom_front = (cx, cy + b - h)
        bottom_left = (cx - a, cy - h)
        mid1 = (cx - a / 2, cy - b / 2 - h - r)
        mid2 = (cx + a / 2, cy + b / 2 - h - r)
        self._poly([top_left, top_right, mid2, mid1], _shade(col, 0.75))
        self._poly([bottom_left, bottom_front, mid2, mid1], _shade(col, 1.0))
        self._poly([bottom_front, top_right, mid2], _shade(col, 0.6))

    def _tree(self, cx: float, cy: float, scale: float) -> None:
        pygame.draw.rect(self.surface, (91, 61, 38), (int(cx - scale), int(cy - 4 * scale), int(2 * scale), int(5 * scale)))
        self._blob(cx, cy - 8 * scale, 6 * scale, 7 * scale, (31, 107, 58))
        self._blob(cx - 1, cy - 10 * scale, 3.5 * scale, 4 * scale, (47, 140, 78))

    def _blob(self, cx: float, cy: float, rx: float, ry: float, color: tuple[int, int, int]) -> None:
        points = []
        steps = 8
        for index in range(steps * 2 + 1):
            angle = math.pi * index / steps
            points.append((cx + rx * math.cos(angle), cy + ry * math.sin(angle)))
        self._poly(points, color)

    def _cyl(self, x: float, y: float, r: float, h: float, col: tuple[int, int, int]) -> None:
        pygame.draw.rect(self.surface, _shade(col, 0.8), (int(x - r), int(y - h), int(2 * r), int(h)))
        self._ellipse_xy(x, y, r, r / 2, _shade(col, 1.1))

    def _ellipse_xy(self, cx: float, cy: float, rx: float, ry: float, color: tuple[int, int, int]) -> None:
        points = []
        steps = 8
        for index in range(steps * 2 + 1):
            angle = math.pi * index / steps
            points.append((cx + rx * math.cos(angle), cy + ry * math.sin(angle)))
        self._poly(points, color)

    def _mast(self, x: float, y: float, h: float) -> None:
        pygame.draw.line(self.surface, (207, 214, 219), (int(x), int(y)), (int(x), int(y - h)), 1)

    def _cross(self, cx: float, ty: float) -> None:
        pygame.draw.rect(self.surface, (217, 56, 46), (int(cx - 5), int(ty - 1.5), 10, 3))
        pygame.draw.rect(self.surface, (217, 56, 46), (int(cx - 1.5), int(ty - 5), 3, 10))

    # ------------------------------------------------------------------ buildings
    def _building(self, world: World, sim: Any, tile: Tile, x: int, y: int, cx: float, cy: float) -> None:
        definition = C.TOOLS.get(tile.kind)
        if definition is None:
            return
        if tile.kind == "park":
            self._diamond(cx, cy, self.tile_width * 0.45, self.tile_height * 0.45, (61, 168, 95))
            self._tree(cx - 9, cy + 1, 0.7)
            self._tree(cx + 8, cy + 2, 0.8)
            self._tree(cx, cy + 6, 0.6)
            return
        if definition.height or definition.daily_upkeep:
            self._service(tile.kind, definition, cx, cy, world, sim)
            return
        self._diamond(cx, cy, self.tile_width / 2 * 0.92, self.tile_height / 2 * 0.92, _hex_to_rgb(definition.color, 0.92))
        level = tile.level
        if not level:
            return
        kind = tile.kind
        variant = (((x * 31) ^ (y * 17)) & 0xFFFFFFFF) % 3
        if kind == "res":
            house_color = ((230, 201, 160), (217, 140, 116), (169, 192, 214))[variant]
            roof_colors = ((164, 71, 47), (95, 111, 134), (122, 90, 58))
            if level == 1:
                self._box(cx, cy, 0.62, 9, house_color, True)
                self._roof(cx, cy, 0.62, 9, roof_colors[variant], 8)
            elif level == 2:
                self._box(cx, cy, 0.72, 26, house_color, True)
                self._box(cx + 8, cy - 22, 0.2, 6, (125, 135, 145), False)
            else:
                self._box(cx, cy, 0.7, 34, house_color, True)
                self._box(cx, cy - 34, 0.46, 18, (207, 174, 131), True)
                self._mast(cx, cy - 52, 12)
        elif kind == "com":
            if level == 1:
                self._box(cx, cy, 0.78, 12, ((106, 163, 224), (224, 138, 106), (124, 197, 154))[variant], True)
                self._poly([(cx - self.tile_width / 2 * 0.78, cy - 3), (cx, cy + self.tile_height / 2 * 0.78 - 3), (cx, cy + self.tile_height / 2 * 0.78 - 7), (cx - self.tile_width / 2 * 0.78, cy - 7)], (226, 75, 75))
            elif level == 2:
                self._box(cx, cy, 0.78, 32, ((95, 143, 196), (106, 159, 168), (122, 143, 207))[variant], True)
            else:
                self._box(cx, cy, 0.8, 36, (77, 124, 176), True)
                self._box(cx, cy - 36, 0.55, 26, (111, 159, 209), True)
                self._box(cx, cy - 62, 0.3, 12, (141, 180, 222), False)
                self._mast(cx, cy - 74, 12)
        elif kind == "ind":
            if level == 1:
                self._box(cx, cy, 0.85, 11, ((201, 164, 92), (184, 147, 90), (196, 160, 112))[variant], False)
            elif level == 2:
                self._box(cx, cy, 0.82, 16, (184, 143, 70), True)
                self._box(cx - 8, cy - 16, 0.2, 6, (138, 106, 47), False)
                self._box(cx + 12, cy - 4, 0.12, 28, (107, 116, 128), False)
                self._smoke(cx + 12, cy - 32, self.time)
            else:
                self._box(cx, cy, 0.85, 12, (169, 131, 66), False)
                self._cyl(cx - 9, cy + 2, 7, 26, (201, 206, 212))
                self._cyl(cx + 9, cy + 4, 6, 20, (201, 206, 212))
                self._box(cx + 2, cy - 6, 0.12, 34, (107, 116, 128), False)
                self._smoke(cx + 2, cy - 38, self.time)

    # ------------------------------------------------------------------ services
    def _service(self, kind: str, definition: Any, cx: float, cy: float, world: World, sim: Any) -> None:
        height = definition.height
        if kind == "solar":
            for offset in (-1, 0, 1):
                self._box(cx + offset * 10, cy + offset * 5, 0.32, 4, (44, 74, 124), False)
            return
        if kind == "water":
            for offset in (-7, 7):
                pygame.draw.line(self.surface, (107, 116, 128), (int(cx + offset), int(cy + 2)), (int(cx + offset * 0.6), int(cy - 14)), 2)
            self._cyl(cx, cy - 14, 10, 13, _hex_to_rgb("#4fb7e0"))
            return
        self._box(cx, cy, 0.85, height, _hex_to_rgb(definition.color), kind != "power")
        top_y = cy - height
        if kind == "power":
            self._box(cx + 9, cy - 4, 0.16, height + 12, (107, 116, 128), False)
            self._box(cx - 9, cy - 2, 0.16, height + 6, (107, 116, 128), False)
            self._smoke(cx + 9, cy - height - 14, self.time)
        elif kind == "fire":
            self._poly([(cx, cy + 13.6), (cx + 27, cy), (cx + 27, cy - 14), (cx, cy - 0.4)], (43, 47, 54))
            burning = any(tile.fire for tile in world.tiles)
            if burning and int(self.time * 4) % 2 == 0:
                pygame.draw.circle(self.surface, (255, 59, 48), (int(cx), int(top_y - 3)), 4)
        elif kind == "police":
            blink = int(self.time * 3) % 2 == 0
            pygame.draw.rect(self.surface, (74, 139, 255) if blink else (255, 74, 74), (int(cx - 4), int(top_y - 4), 8, 3))
        elif kind == "school":
            self._mast(cx, top_y, 14)
            self._poly([(cx, top_y - 14), (cx + 9, top_y - 11), (cx, top_y - 8)], (224, 180, 63))
        elif kind in ("clinic", "hospital"):
            self._cross(cx, top_y)

    # ------------------------------------------------------------------ effects
    def _fire(self, cx: float, cy: float) -> None:
        for index in range(4):
            phase = self.time * 6 + index * 1.7
            height = 10 + 8 * abs(math.sin(phase))
            offset = (index - 1.5) * 7
            color = FIRE_COLORS[index % 2]
            self._poly([(cx + offset - 4, cy - 2), (cx + offset, cy - 2 - height * 1.2), (cx + offset + 4, cy - 2)], color)

    def _smoke(self, cx: float, cy: float, time: float) -> None:
        for index in range(3):
            phase = (time * 0.6 + index / 3) % 1
            alpha = int(max(0.0, 0.5 * (1 - phase)) * 255)
            pygame.draw.circle(self.fx, (210, 215, 220, alpha), (int(cx + phase * 6), int(cy - phase * 22), int(3 + phase * 4)), 1)

    # ------------------------------------------------------------------ traffic
    def _road(self, world: World, tile: Tile, x: int, y: int, cx: float, cy: float) -> None:
        tw = self.tile_width
        th = self.tile_height
        self._diamond(cx, cy, tw / 2, th / 2, (70, 81, 92))
        segments = (
            ((1, 0, 1, 1), (cx + tw / 4, cy), (cx + tw / 4, cy + th / 4)),
            ((-1, 0, -1, -1), (cx - tw / 4, cy), (cx - tw / 4, cy - th / 4)),
            ((0, 1, -1, 1), (cx - tw / 4, cy + th / 4), (cx - tw / 4, cy + th / 2)),
            ((0, -1, 1, -1), (cx + tw / 4, cy - th / 4), (cx + tw / 4, cy - th / 2)),
        )
        for (dx, dy, ex, ey), start, end in segments:
            neighbour = world.tile_at(x + dx, y + dy)
            if neighbour is None or neighbour.kind != "road":
                continue
            pygame.draw.line(self.surface, (216, 196, 106), (int(start[0]), int(start[1])), (int(end[0]), int(end[1])), 1)

    # ------------------------------------------------------------------ cars
    def _cars(self, world: World, buckets: dict[int, list[Car]], x: int, y: int) -> None:
        cars = buckets.get(y * world.size + x)
        if not cars:
            return
        for car in cars:
            fx = car.x + (car.nx - car.x) * car.p if car.nx >= 0 else car.x
            fy = car.y + (car.ny - car.y) * car.p if car.nx >= 0 else car.y
            self._box((fx - fy) * self.tile_width / 2, (fx + fy) * self.tile_height / 2 + self.tile_height / 2, 0.16, 3, _hex_to_rgb(car.color), False)

    # ------------------------------------------------------------------ overlays
    def _overlay(self, tile: Tile, index: int, cx: float, cy: float, sim: Any) -> None:
        if tile.water:
            return
        color: Optional[tuple[int, int, int, int]] = None
        layer = self.layer
        if layer in ("power", "water", "police", "fire", "clinic"):
            covered = bool(sim.coverage[layer][index])
            if covered:
                color = (63, 208, 176, 60)
            elif tile.kind and tile.kind != "road":
                color = (229, 96, 77, 120)
        elif layer == "traffic" and tile.kind == "road":
            ratio = min(1.0, tile.traffic_load / C.VELOCITY_CONGESTION_THRESHOLD)
            color = (int(120 - 120 * ratio), 85, 50, int(0.75 * 255))
        elif layer == "happy" and tile.kind == "res" and tile.level:
            ratio = max(0.0, min(1.0, tile.happiness / 100))
            color = (int(ratio * 120), 80, 50, int(0.6 * 255))
        if color is not None:
            self._diamond_fx(cx, cy, self.tile_width / 2, self.tile_height / 2, color)

    # ------------------------------------------------------------------ hover
    def _draw_hover(self, world: World, sim: Any, tile: Tile, tool: Any, ox: float, oy: float) -> None:
        tw = self.tile_width
        th = self.tile_height
        sx = (tile.x - tile.y) * tw / 2
        sy = (tile.x + tile.y) * th / 2
        cx = sx + ox
        cy = sy + th / 2 + oy
        radius = tool.coverage_radius if tool is not None else 0
        if radius > 0:
            for dy in range(-radius, radius + 1):
                for dx in range(-radius, radius + 1):
                    if abs(dx) + abs(dy) > radius:
                        continue
                    self._diamond_fx(cx + (dx - dy) * tw / 2, cy + (dx + dy) * th / 2, tw / 2 * 0.9, th / 2 * 0.9, (255, 255, 255, 30))
        ok = True
        if tool.kind != "bull":
            ok = not tile.water and tile.kind is None and sim.money >= tool.cost
        color = (63, 208, 176, 115) if ok else (229, 96, 77, 127)
        self._diamond_fx(cx, cy, tw / 2, th / 2, color)
