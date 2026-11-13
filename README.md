# CityForge

**A 3D city-building game by James Technology Solutions.**

CityForge is a standalone Windows desktop city builder with a real-time 3D world, freely orbiting camera, terrain, roads, zoning, municipal services, a growing economy, and local city saves.

## Run from source
Requires Node.js 20 or newer.
\`\`\`bash
npm install
npm start
\`\`\`

## Build Windows applications
\`\`\`bash
npm install
npm test
npm run dist
\`\`\`
The \`dist\` folder contains the Windows NSIS installer and portable executable. GitHub Actions builds both on Windows and publishes them as a workflow artifact.

## Controls
- Left-click a tile to place the selected building or zone.
- Right-drag to orbit the camera; middle-drag to pan.
- Mouse wheel zooms; WASD or arrow keys move the view; Q/E rotate.
- Space pauses simulation. Select 1×, 2× or 4× to change simulation speed.
- Use Save / Load to manage the local city. Autosave runs every in-game month.

## Gameplay
Lay roads, establish residential, commercial and industrial zones, and supply electricity. Expand water, education, healthcare, parks, police and fire coverage to improve growth and happiness. Balance tax revenue against service upkeep. Disasters can be disabled in settings or triggered manually.

## Data and privacy
Cities are saved locally in the application's browser storage. The game makes no network requests during play. No account or online service is required.

## Attribution
Made by **James Technology Solutions (JTS)**. CityForge is an independent project and is not affiliated with other city simulation games.

## Current scope
This release is a playable 3D city-builder foundation with functioning construction, camera, zoning growth, service coverage, treasury, taxation, disasters, and local persistence. It is not represented as a complete simulation of every system in larger commercial city-building games; advanced transport networks, pedestrians, detailed utilities, terrain sculpting, scenarios, and mod support remain future expansion areas.