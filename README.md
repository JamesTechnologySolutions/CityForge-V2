# Cityforge 2

A free, open, unlimited single-player city builder for Windows. Isometric graphics, zoning, utilities, public services, live traffic, disasters and synthesized sound.

## Run
```
npm install
npm start
```
## Build the Windows installer and portable .exe
```
npm run dist
```
Output appears in `dist/`.

## Put it on GitHub
```
git init && git add . && git commit -m "Cityforge 2"
git branch -M main
git remote add origin https://github.com/YOURNAME/cityforge.git
git push -u origin main
```

## What is in version 2
- Services with coverage radius: power plant, solar farm, water tower, police, fire station, clinic, hospital, school, park
- Layers: power, water, police, fire, health, traffic, happiness
- Traffic: cars drive the road network and slow in congestion, which hurts happiness and growth
- Disasters: fires that spread unless a fire station covers them, earthquakes, tornadoes. Toggle them or trigger one yourself
- Sound: built from the Web Audio API, no files needed. Toggle in Settings
- Building art: three styles per zone and a distinct look for each level and service

## Controls
Left-drag builds, right-drag pans, wheel zooms, WASD or arrows move, Space pauses, 1/2/3 set speed, Esc clears the tool.

## Structure
- `main.js` Electron window
- `src/index.html`, `src/style.css` interface
- `src/game.js` terrain, simulation, rendering, input
- `src/extras.js` audio, traffic, disasters, layers, building art

## Roadmap
Pollution, rail and transit, sewage, budgets per department, scenarios, more art, multiple saves.
