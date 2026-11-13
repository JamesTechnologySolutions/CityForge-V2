# CityForge — 3D Development Roadmap

**Publisher:** James Technology Solutions (JTS)  
**Product:** CityForge  
**Target:** Windows 10/11, x64

## Product direction

Build an original, fully 3D city-building and urban-life simulation. CityRT is a feature benchmark only: CityForge must use original source code, interface design, models, textures, audio, names, and other creative assets.

## Architecture principles

- Keep the Electron main process small and secure; run the game in a renderer process.
- Use Three.js for real-time 3D rendering, scene management, lighting, cameras, picking, and asset loading.
- Separate simulation rules from rendering and UI.
- Use deterministic simulation ticks where practical so saves, replays, and multiplayer synchronization remain reliable.
- Use data-driven definitions for buildings, zones, services, vehicles, policies, and disasters.
- Use versioned save files and migrations; never make a single local save the only save slot.
- Profile large cities and use instancing, level of detail, spatial partitioning, and worker threads where appropriate.
- Preserve accessibility, scalable UI, keyboard/controller input, and configurable graphics settings.

## Feature roadmap

### Foundation
- Replace the fixed 56 × 56 2D canvas world with a scalable 3D world.
- Add orbit, pan, zoom, top-down, and street-level cameras.
- Add terrain generation, water bodies, vegetation, and map seeds.
- Add a world-coordinate/grid abstraction and robust placement/picking.
- Add an asset pipeline for original models, materials, textures, and audio.
- Add automated Windows installer and portable EXE builds.

### City construction
- Freeform and grid-aligned roads, curved roads, lane definitions, intersections, roundabouts, bridges, tunnels, and elevated roads.
- Residential, commercial, industrial, office, mixed-use, and specialist districts.
- Building catalog, architectural themes, procedural variants, lot sizing, upgrades, and individual building inspection.
- Electricity, water, sewage, waste, telecommunications, and service coverage networks.
- Parks, education, healthcare, emergency services, safety, and civic facilities.

### Simulation
- Households, citizens, jobs, education, commuting, and service demand.
- Road-network pathfinding, traffic signals, congestion, parking, pedestrians, and public transport.
- City finances, budgets, taxes, land value, happiness, pollution, noise, and crime.
- Weather, seasons, fires, floods, storms, earthquakes, and other configurable disasters.
- Scenarios, milestones, city policies, achievements, and sandbox mode.

### Exploration and social play
- First-person walking and third-person driving.
- Enterable/interior-ready buildings as a later modular feature.
- Multiple cities, map templates, save slots, autosave, backups, and import/export.
- Multiplayer rooms and collaborative city editing only after the single-player simulation and save model are stable.

## Quality gates

A feature is not complete merely because it renders. Each system needs:
- Functional interaction and clear UI feedback.
- Save/load persistence where applicable.
- Performance checks at representative city sizes.
- Automated tests for core simulation rules.
- Windows build verification.
- No broken references, missing assets, or fatal console errors.

## Release pipeline

The GitHub Actions workflow builds x64 Windows NSIS installer and portable EXE artifacts from the repository root. Pushes to the development branches and main run a build; version tags publish GitHub Releases. Local commands:

```powershell
npm install
npm start
npm run dist
```

Artifacts are written to `dist/\`.
