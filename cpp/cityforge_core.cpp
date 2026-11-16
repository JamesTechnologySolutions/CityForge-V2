// Cityforge C++ hot paths - exposed to Python through pybind11.
//
// The Python simulation owns the authoritative game state.  This module
// implements the numerically hot loops that Python cannot push at 60 FPS on
// large maps:
//   * uniform grid spatial hash over the tile grid (broad phase queries)
//   * road congestion aggregation
//   * traffic car advancement
//
// The Python layer wraps these bindings via `cityforge/accel.py` and
// transparently falls back to pure Python when the extension is not built.

#include <cmath>
#include <cstdint>
#include <unordered_map>
#include <vector>

#include <pybind11/pybind11.h>

namespace py = pybind11;

using TileMap = std::unordered_map<int64_t, std::vector<int32_t>>;

// Build a uniform grid spatial hash over ``size * size`` tile kinds.
// ``cell`` is the grid cell size in tiles (e.g. 8).  Empty tiles (kind == 0)
// are skipped because they are the common case.
void build_tile_hash(const std::vector<int32_t>& kinds, int32_t size, int32_t cell, TileMap& out) {
    out.clear();
    const int32_t cols = (size + cell - 1) / cell;
    for (int32_t i = 0; i < static_cast<int32_t>(kinds.size()); ++i) {
        const int32_t kind = kinds[static_cast<size_t>(i)];
        if (kind == 0) { continue; }
        const int32_t x = i % size;
        const int32_t y = i / size;
        const int64_t key = static_cast<int64_t>(y / cell) * cols * 1000003LL + (y / cell) * 31 + (x / cell);
        out[key].push_back(i);
    }
}

py::dict build_tile_hash_dict(const std::vector<int32_t>& kinds, int32_t size, int32_t cell) {
    TileMap map;
    build_tile_hash(kinds, size, cell, map);
    py::dict result;
    for (auto& entry : map) {
        py::list keys = py::list();
        keys.append(entry.first);
        py::list values = py::list();
        for (int32_t value : entry.second) { values.append(value); }
        result[py::str(std::to_string(entry.first))] = values;
    }
    return result;
}

// Average capped congestion over all road tiles.  ``loads`` holds the raw
// traffic load per tile, ``roads`` a 0/1 occupancy mask.
double compute_congestion(const std::vector<double>& loads, const std::vector<int>& roads, double capacity) {
    double sum = 0.0;
    int32_t count = 0;
    for (size_t i = 0; i < roads.size(); ++i) {
        if (roads[static_cast<size_t>(i)] == 0) { continue; }
        sum += std::min(1.0, loads[static_cast<size_t>(i)] / capacity);
        ++count;
    }
    return count == 0 ? 0.0 : sum / static_cast<double>(count);
}

// Advance traffic cars by ``dt`` seconds.  Car layout is flat with 7 doubles
// per car: x, y, nx, ny, p, px, py.  ``roads`` is a 0/1 occupancy mask the same
// size as the world, ``loads`` holds the traffic load per road tile.
void advance_cars(std::vector<double>& cars, const std::vector<int>& roads, const std::vector<double>& loads,
                 int32_t size, double dt, double speed, std::vector<double>& out) {
    out.clear();
    out.reserve(cars.size());
    const double kVelocityPerStep = 1.3;
    const double kCongestionDecay = 0.65;
    const double kCongestionThreshold = 14.0;
    const int kDirs[4][2] = {{1, 0}, {-1, 0}, {0, 1}, {0, -1}};
    for (size_t i = 0; i < cars.size(); i += 7) {
        double x = cars[i];
        double y = cars[i + 1];
        double nx = cars[i + 2];
        double ny = cars[i + 3];
        double p = cars[i + 4];
        double px = cars[i + 5];
        double py = cars[i + 6];
        double factor = 1.0;
        const int32_t road_id = static_cast<int32_t>(static_cast<int>(y) * size + static_cast<int>(x));
        if (road_id >= 0 && road_id < static_cast<int>(roads.size()) && roads[static_cast<size_t>(road_id)] != 0) {
            factor = 1.0 - std::min(1.0, loads[static_cast<size_t>(road_id)] / kCongestionThreshold) * kCongestionDecay;
        }
        p += speed * kVelocityPerStep * factor * dt;
        while (p >= 1.0) {
            p -= 1.0;
            px = x;
            py = y;
            if (nx >= 0) {
                const int32_t next_id = static_cast<int32_t>(static_cast<int>(ny) * size + static_cast<int>(nx));
                if (next_id >= 0 && next_id < static_cast<int>(roads.size()) && roads[static_cast<size_t>(next_id)] != 0) {
                    x = nx;
                    y = ny;
                }
            }
            bool hopped = false;
            for (const auto& dir : kDirs) {
                const int32_t next_x = static_cast<int32_t>(x) + dir[0];
                const int32_t next_y = static_cast<int32_t>(y) + dir[1];
                const int32_t next_id = next_y * size + next_x;
                if (next_x >= 0 && next_x < size && next_y >= 0 && next_y < size && roads[static_cast<size_t>(next_id)] != 0) {
                    nx = next_x;
                    ny = next_y;
                    p = 0.0;
                    hopped = true;
                    break;
                }
            }
            if (!hopped) { break; }
        }
        out.push_back(x);
        out.push_back(y);
        out.push_back(nx);
        out.push_back(ny);
        out.push_back(p);
        out.push_back(px);
        out.push_back(py);
    }
}

PYBIND11_MODULE(cityforge_core, m) {
    m.doc() = "Cityforge C++ hot paths (spatial hash, congestion, traffic).";
    m.def("build_tile_hash", &build_tile_hash_dict, "Build a spatial hash dict over tile kinds.");
    m.def("compute_congestion", &compute_congestion, "Compute average capped congestion.");
    m.def("advance_cars", &advance_cars, "Advance traffic cars by dt seconds.");
}
