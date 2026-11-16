"""Cityforge 2 - a free, open, unlimited city-building game.

The Python rewrite of the original JavaScript (Electron + canvas) prototype.

Architecture overview
--------------------
``cityforge`` is organised so the *simulation* never knows that a renderer,
an audio engine or a UI toolkit exists, and the *presentation* layers only
read from simulation state:

* :mod:`cityforge.model`        - plain data classes (tiles, cars, disasters)
* :mod:`cityforge.content`      - data-driven game content (tools, services, ...)
* :mod:`cityforge.rng`           - deterministic seeded generators
* :mod:`cityforge.noise`         - value-noise terrain generator
* :mod:`cityforge.world`         - tile grid, terrain, coverage queries
* :mod:`cityforge.simulation`   - economy, demand, growth, happiness, ranks
* :mod:`cityforge.traffic`       - traffic network, congestion, cars
* :mod:`cityforge.disasters`     - fire, earthquake, tornado
* :mod:`cityforge.persistence`   - save / load
* :mod:`cityforge.audio`         - synthesized sound effects
* :mod:`cityforge.rendering`    - isometric renderer (pygame-ce backend)
* :mod:`cityforge.input`         - input abstraction
* :mod:`cityforge.ui`             - pygame-ce based user interface
* :mod:`cityforge.webui`         - optional thin JavaScript webview UI bridge
* :mod:`cityforge.app`           - application wiring / game loop
"""

from __future__ import annotations

__version__ = "0.3.0"

__all__ = ["__version__"]
