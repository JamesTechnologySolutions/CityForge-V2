# CityForge

**A 3D city-building and urban simulation game by James Technology Solutions (JTS).**

CityForge is being developed as a Windows desktop game focused on deep city construction, believable urban simulation, and immersive 3D exploration.

## Development status

The current mainline prototype is an isometric 2D proof of concept. The `development/3d-foundation` branch begins the transition to a modular 3D architecture. The full 3D feature set is a roadmap, not a claim that all systems are already implemented.

## Run locally

Requirements: Node.js 22 or newer and Windows (for Windows packaging).

```powershell
npm install
npm start
```

## Build Windows executables

```powershell
npm run dist
```

This creates:
- NSIS Windows installer
- Portable Windows executable

Build output: `dist/\`

Individual targets:

```powershell
npm run dist:installer
npm run dist:portable
```

## Project structure

- `main.js` — Electron main process
- `src/index.html` — game shell
- `src/style.css` — interface styling
- `src/game.js` — current prototype simulation and rendering
- `src/extras.js` — current prototype traffic, disasters, audio, and visual extras

## Roadmap

See [docs/3D-ROADMAP.md](docs/3D-ROADMAP.md) for the planned engine architecture, gameplay systems, milestones, and quality gates.

## Project identity

Product: **CityForge**  
Publisher: **Made by James Technology Solutions (JTS)**

CityRT is used only as a functional reference point. CityForge will have its own implementation, game identity, assets, interface, and creative direction.
