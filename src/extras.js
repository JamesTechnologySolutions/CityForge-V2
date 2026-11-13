'use strict';
// Cityforge 2: audio, traffic, disasters, building art, map layers.
let layer = null, shake = 0, AC = null, master = null;
const cars = [], carMap = new Map(), DIRS = [[1, 0], [-1, 0], [0, 1], [0, -1]];

// ---------- Audio (synthesized, no files) ----------
function initAudio() {
  if (AC) { if (AC.state === 'suspended') AC.resume(); return; }
  try { AC = new (window.AudioContext || window.webkitAudioContext)(); master = AC.createGain(); master.gain.value = .35; master.connect(AC.destination); } catch (e) { AC = null; }
}
function tone(f, d, type = 'sine', v = .3, slide = 0, delay = 0) {
  if (!AC || !$('snd').checked) return;
  const t = AC.currentTime + delay, o = AC.createOscillator(), g = AC.createGain();
  o.type = type; o.frequency.setValueAtTime(f, t);
  if (slide) o.frequency.exponentialRampToValueAtTime(Math.max(20, f + slide), t + d);
  g.gain.setValueAtTime(v, t); g.gain.exponentialRampToValueAtTime(.001, t + d);
  o.connect(g); g.connect(master); o.start(t); o.stop(t + d);
}
function noise(d, v = .3, f = 800, delay = 0) {
  if (!AC || !$('snd').checked) return;
  const t = AC.currentTime + delay, b = AC.createBuffer(1, Math.floor(AC.sampleRate * d), AC.sampleRate), a = b.getChannelData(0);
  for (let i = 0; i < a.length; i++) a[i] = Math.random() * 2 - 1;
  const s = AC.createBufferSource(), fl = AC.createBiquadFilter(), g = AC.createGain();
  s.buffer = b; fl.type = 'lowpass'; fl.frequency.value = f;
  g.gain.setValueAtTime(v, t); g.gain.exponentialRampToValueAtTime(.001, t + d);
  s.connect(fl); fl.connect(g); g.connect(master); s.start(t);
}
function sfx(n) {
  const m = {
    build: () => { tone(220, .09, 'square', .12, 160); tone(440, .08, 'triangle', .1, 0, .06); },
    bull: () => noise(.25, .35, 600),
    rank: () => [523, 659, 784, 1046].forEach((f, i) => tone(f, .3, 'triangle', .18, 0, i * .12)),
    siren: () => { for (let i = 0; i < 4; i++) tone(i % 2 ? 700 : 950, .28, 'sawtooth', .08, 0, i * .28); },
    quake: () => { noise(1.6, .6, 180); tone(55, 1.4, 'sine', .4, -25); },
    wind: () => noise(1.8, .3, 1400)
  };
  if (m[n]) m[n]();
}

// ---------- Traffic ----------
function updateTraffic() {
  let tot = 0, n = 0;
  for (const t of S.t) if (t.k === 'road') { t.tr = 0; n++; }
  for (let y = 0; y < N; y++) for (let x = 0; x < N; x++) {
    const tl = S.t[y * N + x];
    if (!(tl.k === 'res' || tl.k === 'com' || tl.k === 'ind') || !tl.lv) continue;
    const near = [];
    for (let dy = -2; dy <= 2; dy++) for (let dx = -2; dx <= 2; dx++) { const a = at(x + dx, y + dy); if (a && a.k === 'road') near.push(a); }
    const load = tl.lv * (tl.k === 'com' ? 4 : 3);
    near.forEach(a => a.tr += load / near.length);
  }
  for (const t of S.t) if (t.k === 'road') tot += Math.min(1, t.tr / 14);
  S.cong = n ? tot / n : 0;
}
const roadN = (x, y) => { const a = at(x, y); return !!(a && a.k === 'road'); };
function spawnCar() {
  const r = []; for (let i = 0; i < S.t.length; i++) if (S.t[i].k === 'road') r.push(i);
  if (!r.length) return false;
  const i = r[Math.random() * r.length | 0];
  cars.push({ x: i % N, y: (i / N) | 0, nx: -1, ny: 0, p: 1, px: -1, py: -1, c: ['#e8e8e8', '#d9453d', '#3d7bd9', '#e0b43f', '#2b2f36', '#4cae6a'][Math.random() * 6 | 0] });
  return true;
}
function nextHop(c) {
  const opts = DIRS.map(([dx, dy]) => [c.x + dx, c.y + dy]).filter(([x, y]) => roadN(x, y));
  if (!opts.length) return false;
  const fwd = opts.filter(([x, y]) => !(x === c.px && y === c.py)), pool = fwd.length ? fwd : opts, p = pool[Math.random() * pool.length | 0];
  c.nx = p[0]; c.ny = p[1]; c.p = 0; return true;
}
function updateCars(dt) {
  if (!S || !S.speed) return;
  const want = Math.min(160, Math.floor(S.pop / 10 + S.jobs / 16));
  while (cars.length < want) if (!spawnCar()) break;
  if (cars.length > want) cars.length = want;
  const sp = [0, 1, 2.2, 4][S.speed] * dt;
  for (let k = cars.length - 1; k >= 0; k--) {
    const c = cars[k], cur = at(c.x, c.y);
    if (!cur || cur.k !== 'road') { cars.splice(k, 1); continue; }
    c.p += sp * 1.3 * (1 - Math.min(1, (cur.tr || 0) / 14) * .65);
    while (c.p >= 1) {
      c.p -= 1; c.px = c.x; c.py = c.y;
      if (c.nx >= 0 && roadN(c.nx, c.ny)) { c.x = c.nx; c.y = c.ny; }
      if (!nextHop(c)) { c.p = 0; c.nx = -1; break; }
    }
    if (c.nx < 0 && !nextHop(c)) c.p = 0;
  }
}
function bucketCars() {
  carMap.clear();
  for (const c of cars) { const k = (c.nx >= 0 && c.p >= .5) ? c.ny * N + c.nx : c.y * N + c.x; if (!carMap.has(k)) carMap.set(k, []); carMap.get(k).push(c); }
}
function drawCars(x, y) {
  const l = carMap.get(y * N + x); if (!l) return;
  for (const c of l) {
    const nx = c.nx >= 0 ? c.nx : c.x, ny = c.ny >= 0 ? c.ny : c.y, fx = c.x + (nx - c.x) * c.p, fy = c.y + (ny - c.y) * c.p;
    box((fx - fy) * TW / 2, (fx + fy) * TH / 2 + TH / 2, .16, 3, c.c);
  }
}

// ---------- Disasters ----------
function runDisasters() {
  for (let i = 0; i < S.t.length; i++) {
    const t = S.t[i]; if (!t.fire) continue;
    const x = i % N, y = (i / N) | 0, covered = S.cv.fire[i];
    if (covered && Math.random() < .5) { t.fire = 0; if (t.lv > 0) t.lv--; continue; }
    for (let dy = -2; dy <= 2; dy++) for (let dx = -2; dx <= 2; dx++) {
      const a = at(x + dx, y + dy); if (!a || !a.k || a.k === 'road' || a.fire) continue;
      const p = (Math.abs(dx) <= 1 && Math.abs(dy) <= 1 ? .2 : .07) * (S.cv.fire[(y + dy) * N + x + dx] ? .15 : 1);
      if (Math.random() < p) a.fire = 6;
    }
    if (--t.fire <= 0) { t.k = null; t.lv = 0; }
  }
  if (!$('dis').checked || S.pop < 40) return;
  const r = Math.random();
  if (r < .012) startFire(); else if (r < .0135) quake(); else if (r < .015) tornado();
}
function startFire() {
  const b = []; S.t.forEach((t, i) => { if (t.k && t.k !== 'road') b.push(i); });
  if (!b.length) return false;
  const i = b[Math.random() * b.length | 0]; S.t[i].fire = 6; sfx('siren');
  toast(S.cv.fire[i] ? 'Fire reported. A fire station is responding.' : 'Fire! No station covers it. Build a fire station nearby.');
  return true;
}
function quake() {
  shake = 14; sfx('quake'); let n = 0;
  for (const t of S.t) {
    if (!t.k || t.k === 'road') continue;
    const z = t.k.length === 3;
    if (Math.random() < (z ? .12 : .03)) { if (z && t.lv > 1) t.lv--; else { t.k = null; t.lv = 0; t.fire = 0; } n++; }
  }
  toast('Earthquake! ' + n + ' buildings were damaged.');
}
function tornado() {
  let x = Math.random() * N | 0, y = Math.random() * N | 0, n = 0; sfx('wind'); shake = 6;
  for (let i = 0; i < 16; i++) {
    for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) { const a = at(x + dx, y + dy); if (a && a.k && a.k !== 'road' && Math.random() < .6) { a.k = null; a.lv = 0; a.fire = 0; n++; } }
    x += Math.random() * 3 | 0; y += (Math.random() * 3 | 0) - 1;
  }
  toast(n ? 'A tornado cut through the city and destroyed ' + n + ' buildings.' : 'A tornado touched down in open land.');
}
function triggerDisaster() { if (!S.t.some(t => t.k && t.k !== 'road')) return toast('Build something first.'); [startFire, quake, tornado][Math.random() * 3 | 0](); }

// ---------- Layers ----------
function overlay(tl, i, cx, cy) {
  if (tl.w) return; let col = null;
  if (['power', 'water', 'police', 'fire', 'clinic'].includes(layer)) col = S.cv[layer][i] ? 'rgba(63,208,176,.25)' : (tl.k && tl.k !== 'road' ? 'rgba(229,96,77,.45)' : null);
  else if (layer === 'traffic' && tl.k === 'road') col = `hsla(${120 - 120 * Math.min(1, (tl.tr || 0) / 14)},85%,50%,.75)`;
  else if (layer === 'happy' && tl.k === 'res' && tl.lv) col = `hsla(${clamp((tl.hp || 0) / 100, 0, 1) * 120},80%,50%,.6)`;
  if (col) dia(cx, cy, col);
}

// ---------- Building art ----------
function cyl(x, y, r, h, col) {
  ctx.fillStyle = shade(col, .8); ctx.fillRect(x - r, y - h, 2 * r, h); ctx.beginPath(); ctx.ellipse(x, y, r, r / 2, 0, 0, 7); ctx.fill();
  ctx.fillStyle = shade(col, 1.1); ctx.beginPath(); ctx.ellipse(x, y - h, r, r / 2, 0, 0, 7); ctx.fill();
}
function roof(cx, cy, f, h, col, r) {
  const a = TW / 2 * f, b = TH / 2 * f, T = [cx, cy - b - h], R = [cx + a, cy - h], B = [cx, cy + b - h], L = [cx - a, cy - h];
  const M1 = [cx - a / 2, cy - b / 2 - h - r], M2 = [cx + a / 2, cy + b / 2 - h - r];
  poly([T, R, M2, M1], shade(col, .75)); poly([L, B, M2, M1], shade(col, 1)); poly([B, R, M2], shade(col, .6));
}
function mast(x, y, h) { ctx.strokeStyle = '#cfd6dd'; ctx.lineWidth = 1.5; ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x, y - h); ctx.stroke(); }
function cross(cx, ty) { ctx.fillStyle = '#d9382e'; ctx.fillRect(cx - 5, ty - 1.5, 10, 3); ctx.fillRect(cx - 1.5, ty - 5, 3, 10); }
function service(k, d, cx, cy) {
  if (k === 'solar') { for (let i = -1; i <= 1; i++) box(cx + i * 10, cy + i * 5, .32, 4, '#2c4a7c'); return; }
  if (k === 'water') { ctx.strokeStyle = '#6b7480'; ctx.lineWidth = 2; ctx.beginPath(); for (const o of [-7, 7]) { ctx.moveTo(cx + o, cy + 2); ctx.lineTo(cx + o * .6, cy - 14); } ctx.stroke(); cyl(cx, cy - 14, 10, 13, d.col); return; }
  box(cx, cy, .85, d.h, d.col, k !== 'power');
  const ty = cy - d.h;
  if (k === 'power') { box(cx + 9, cy - 4, .16, d.h + 12, '#6b7480'); box(cx - 9, cy - 2, .16, d.h + 6, '#6b7480'); smoke(cx + 9, cy - d.h - 14); }
  else if (k === 'fire') { poly([[cx, cy + 13.6], [cx + 27, cy], [cx + 27, cy - 14], [cx, cy - 0.4]], '#2b2f36'); if (S.t.some(t => t.fire) && Math.floor(time * 4) % 2) { ctx.fillStyle = '#ff3b30'; ctx.beginPath(); ctx.arc(cx, ty - 3, 4, 0, 7); ctx.fill(); } }
  else if (k === 'police') { ctx.fillStyle = Math.floor(time * 3) % 2 ? '#4a8bff' : '#ff4a4a'; ctx.fillRect(cx - 4, ty - 4, 8, 3); }
  else if (k === 'school') { mast(cx, ty, 14); poly([[cx, ty - 14], [cx + 9, ty - 11], [cx, ty - 8]], '#e0b43f'); }
  else if (k === 'clinic' || k === 'hospital') cross(cx, ty);
}
function drawBuilding(tl, x, y, cx, cy, d) {
  const v = (((x * 31) ^ (y * 17)) >>> 0) % 3, l = tl.lv, k = tl.k;
  if (k === 'park') { dia(cx, cy, '#3da85f', .9); tree(cx - 9, cy + 1, .7); tree(cx + 8, cy + 2, .8); tree(cx, cy + 6, .6); return; }
  if (d.up) return service(k, d, cx, cy);
  ctx.globalAlpha = .35; dia(cx, cy, d.col, .92); ctx.globalAlpha = 1;
  if (!l) return;
  if (k === 'res') {
    const c = ['#e6c9a0', '#d98c74', '#a9c0d6'][v];
    if (l === 1) { box(cx, cy, .62, 9, c, true); roof(cx, cy, .62, 9, ['#a4472f', '#5f6f86', '#7a5a3a'][v], 8); }
    else if (l === 2) { box(cx, cy, .72, 26, c, true); box(cx + 8, cy - 22, .2, 6, '#7d8791'); }
    else { box(cx, cy, .7, 34, c, true); box(cx, cy - 34, .46, 18, ['#cfae83', '#c07a62', '#8fa8c0'][v], true); mast(cx, cy - 52, 12); }
  } else if (k === 'com') {
    if (l === 1) { const c = ['#6aa3e0', '#e08a6a', '#7cc59a'][v]; box(cx, cy, .78, 12, c, true); const a = TW / 2 * .78, b = TH / 2 * .78; poly([[cx - a, cy - 3], [cx, cy + b - 3], [cx, cy + b - 7], [cx - a, cy - 7]], '#e24b4b'); }
    else if (l === 2) box(cx, cy, .78, 32, ['#5f8fc4', '#6a9fa8', '#7a8fcf'][v], true);
    else { box(cx, cy, .8, 36, '#4d7cb0', true); box(cx, cy - 36, .55, 26, '#6f9fd1', true); box(cx, cy - 62, .3, 12, '#8db4de'); mast(cx, cy - 74, 12); }
  } else {
    if (l === 1) box(cx, cy, .85, 11, ['#c9a45a', '#b8935a', '#c4a070'][v]);
    else if (l === 2) { box(cx, cy, .82, 16, '#b88f46', true); box(cx - 8, cy - 16, .2, 6, '#8a6a2f'); box(cx + 12, cy - 4, .12, 28, '#6b7480'); smoke(cx + 12, cy - 32); }
    else { box(cx, cy, .85, 12, '#a98342'); cyl(cx - 9, cy + 2, 7, 26, '#c9ced4'); cyl(cx + 9, cy + 4, 6, 20, '#c9ced4'); box(cx + 2, cy - 6, .12, 34, '#6b7480'); smoke(cx + 2, cy - 38); }
  }
  if (!(tl.road && tl.pw)) { ctx.font = '14px sans-serif'; ctx.textAlign = 'center'; ctx.fillStyle = tl.road ? '#f0b64a' : '#e5604d'; ctx.fillText(tl.road ? '\u26A1' : '!', cx, cy - 12 - l * 14); }
}
function drawFire(cx, cy) {
  for (let i = 0; i < 4; i++) {
    const t = time * 6 + i * 1.7, h = 10 + 8 * Math.abs(Math.sin(t)), ox = (i - 1.5) * 7;
    ctx.fillStyle = i % 2 ? '#ffb02e' : '#ff5a1f'; ctx.beginPath(); ctx.moveTo(cx + ox - 4, cy - 2); ctx.quadraticCurveTo(cx + ox, cy - 2 - h * 1.2, cx + ox + 4, cy - 2); ctx.fill();
  }
}
