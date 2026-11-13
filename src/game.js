'use strict';
const N = 56, TW = 64, TH = 32, SAVE = 'cityforge-save';
const TOOLS = {
  road:  { n: 'Road', c: 10, col: '#46515c', info: 'Connects zones. Costs 0.15/day.' },
  res:   { n: 'Residential', c: 20, col: '#58b86f', info: 'Homes. Need road + power.' },
  com:   { n: 'Commercial', c: 20, col: '#4f93e0', info: 'Shops and offices. Provide jobs.' },
  ind:   { n: 'Industrial', c: 20, col: '#e0a93f', info: 'Factories. Jobs, but unhappy neighbors.' },
  power: { n: 'Power plant', c: 900, up: 18, r: 16, h: 34, col: '#e2573f', info: 'Powers zones within 16 tiles.' },
  park:  { n: 'Park', c: 80, up: 1, r: 5, h: 0, col: '#2f9e57', info: 'Raises happiness within 5 tiles.' },
  school:{ n: 'School', c: 400, up: 7, r: 9, h: 24, col: '#a770dc', info: 'Raises happiness within 9 tiles.' },
  clinic:{ n: 'Clinic', c: 450, up: 8, r: 9, h: 24, col: '#eef1f6', info: 'Raises happiness within 9 tiles.' },
  police:{ n: 'Police', c: 400, up: 7, r: 10, h: 22, col: '#4a66e0', info: 'Raises happiness within 10 tiles.' },
  fire:  { n: 'Fire station', c: 450, up: 8, r: 10, h: 22, col: '#e8562f', info: 'Fights fires within 10 tiles.' },
  water: { n: 'Water tower', c: 500, up: 6, r: 12, h: 30, col: '#4fb7e0', info: 'Water within 12 tiles. Needed for level 3.' },
  solar: { n: 'Solar farm', c: 600, up: 4, r: 9, h: 3, col: '#27406b', cov: 'power', info: 'Clean power within 9 tiles.' },
  hospital: { n: 'Hospital', c: 1400, up: 20, r: 16, h: 36, col: '#f2f5fa', cov: 'clinic', info: 'Large medical coverage, 16 tiles.' },
  bull:  { n: 'Bulldoze', c: 2, col: '#b4503f', info: 'Clears a tile.' }
};
const GROUPS = [['Build', ['road']], ['Zones', ['res', 'com', 'ind']], ['Services', ['power', 'solar', 'water', 'park', 'school', 'clinic', 'hospital', 'police', 'fire']], ['Tools', ['bull']]];
const RANKS = [[0, 'Hamlet'], [100, 'Village'], [500, 'Town'], [1500, 'City'], [5000, 'Large city'], [15000, 'Metropolis']];
const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
const DRAG = ['road', 'res', 'com', 'ind', 'bull'];
const $ = id => document.getElementById(id);
const cv = $('c'), ctx = cv.getContext('2d');
let S, tool = 'road', cam = { x: 0, y: 0, z: 1 }, hover = null, painting = false, panning = false, acc = 0, last = 0, time = 0;
const keys = new Set();
const clamp = (v, a = -1, b = 1) => Math.max(a, Math.min(b, v));
const rng = s => () => (s = (s * 1664525 + 1013904223) >>> 0) / 4294967296;
const at = (x, y) => (x >= 0 && y >= 0 && x < N && y < N) ? S.t[y * N + x] : null;

function newGame(seed = Math.floor(Math.random() * 1e9)) {
  const r = rng(seed), G = 8, g = Array.from({ length: G + 2 }, () => Array.from({ length: G + 2 }, r));
  const sm = t => t * t * (3 - 2 * t);
  const noise = (x, y) => {
    const fx = x / N * G, fy = y / N * G, ix = fx | 0, iy = fy | 0, tx = sm(fx - ix), ty = sm(fy - iy);
    const a = g[iy][ix], b = g[iy][ix + 1], c = g[iy + 1][ix], d = g[iy + 1][ix + 1];
    return a + (b - a) * tx + (c - a) * ty + (a - b - c + d) * tx * ty;
  };
  const t = [];
  for (let y = 0; y < N; y++) for (let x = 0; x < N; x++) {
    const w = Math.hypot(x - N / 2, y - N / 2) > 9 && noise(x, y) < 0.36;
    t.push({ w, k: null, lv: 0, tree: !w && r() < 0.12, pw: false });
  }
  S = { seed, t, money: 15000, day: 0, tax: 9, speed: 1, name: $('cname').value, pop: 0, jobs: 0, happy: 50,
        dem: { r: 1, c: 1, i: 1 }, inc: 0, exp: 0, rank: 0 };
  cover(); centerCam(); sync(); hud();
}
function centerCam() { cam.z = 1; cam.x = cv.width / 2; cam.y = cv.height / 2 - N * TH / 2 + 20; }

function cover() {
  const c = {}; for (const k of ['power', 'park', 'school', 'clinic', 'police', 'fire', 'water']) c[k] = new Uint8Array(N * N);
  for (let y = 0; y < N; y++) for (let x = 0; x < N; x++) {
    const tl = S.t[y * N + x], d = TOOLS[tl.k];
    if (!d || !d.r) continue;
    for (let dy = -d.r; dy <= d.r; dy++) for (let dx = -d.r; dx <= d.r; dx++)
      if (Math.abs(dx) + Math.abs(dy) <= d.r && at(x + dx, y + dy)) c[d.cov || tl.k][(y + dy) * N + x + dx] = 1;
  }
  S.cv = c;
}
function nearRoad(x, y) { for (let dy = -2; dy <= 2; dy++) for (let dx = -2; dx <= 2; dx++) { const a = at(x + dx, y + dy); if (a && a.k === 'road') return true; } return false; }
function nearInd(x, y) { for (let dy = -4; dy <= 4; dy++) for (let dx = -4; dx <= 4; dx++) { const a = at(x + dx, y + dy); if (a && a.k === 'ind' && a.lv > 0) return true; } return false; }

function tick() {
  S.day++; cover();
  let pop = 0, cj = 0, ij = 0, hs = 0, hn = 0, exp = 0;
  for (let y = 0; y < N; y++) for (let x = 0; x < N; x++) {
    const i = y * N + x, tl = S.t[i], d = TOOLS[tl.k];
    if (d && d.up) exp += d.up;
    if (tl.k === 'road') exp += 0.15;
    if (tl.k !== 'res' && tl.k !== 'com' && tl.k !== 'ind') continue;
    tl.road = nearRoad(x, y); tl.pw = !!S.cv.power[i]; tl.wt = !!S.cv.water[i];
    if (tl.lv > 0 && tl.road && tl.pw) {
      if (tl.k === 'res') {
        pop += tl.lv * 10;
        let h = 38 + (S.cv.school[i] ? 10 : 0) + (S.cv.clinic[i] ? 12 : 0) + (S.cv.police[i] ? 10 : 0) + (S.cv.park[i] ? 8 : 0) + (S.cv.fire[i] ? 6 : 0) + (S.cv.water[i] ? 12 : 0);
        if (nearInd(x, y)) h -= 15;
        h -= Math.max(0, S.tax - 9) * 3; h -= (S.cong || 0) * 15; tl.hp = h; hs += h * tl.lv; hn += tl.lv;
      } else if (tl.k === 'com') cj += tl.lv * 6; else ij += tl.lv * 8;
    }
  }
  updateTraffic(); const jobs = cj + ij; S.pop = pop; S.jobs = jobs; S.happy = hn ? clamp(hs / hn, 0, 100) : 50;
  const jd = (pop * 0.8 - jobs + 25) / (pop * 0.8 + jobs + 25), rd = (jobs * 1.1 + 25 - pop) / (jobs * 1.1 + pop + 25);
  const tp = (S.tax - 9) * 0.04, hp = (S.happy - 50) / 100 * 0.3;
  S.dem = { r: clamp(rd - tp + hp), c: clamp(jd - tp + (ij > cj * 1.5 ? 0.25 : -0.1)), i: clamp(jd - tp + (cj > ij * 0.8 ? 0.15 : -0.1)) };
  for (const tl of S.t) {
    if (tl.k !== 'res' && tl.k !== 'com' && tl.k !== 'ind') continue;
    const dm = S.dem[tl.k[0]];
    if (tl.road && tl.pw && !tl.fire && tl.lv < 3 && (tl.lv < 2 || tl.wt) && Math.random() < 0.12 * Math.max(0, dm) * (1 - (S.cong || 0) * 0.5)) tl.lv++;
    else if (tl.lv > 0 && ((!tl.road || !tl.pw) && Math.random() < 0.05 || dm < -0.3 && Math.random() < 0.03)) tl.lv--;
  }
  S.inc = (S.tax / 9) * (pop * 0.35 + cj * 0.6 + ij * 0.45); S.exp = exp; S.money += S.inc - exp;
  runDisasters(); let rk = 0; RANKS.forEach((r, i) => { if (pop >= r[0]) rk = i; });
  if (rk > S.rank) sfx('rank'), toast('Your settlement grew into a ' + RANKS[rk][1].toLowerCase() + '!');
  S.rank = rk;
  if (S.money < 0 && S.day % 30 === 0) toast('Funds are negative. Raise taxes or cut services.');
  if (S.day % 30 === 0) save(true);
  hud();
}

function place(x, y, quiet) {
  const tl = at(x, y), d = TOOLS[tool]; if (!tl || !d) return;
  if (tool === 'bull') {
    if (!tl.k && !tl.tree) return;
    if (S.money < d.c) return quiet || toast('Not enough funds');
    S.money -= d.c; tl.k = null; tl.lv = 0; tl.tree = false; tl.fire = 0; sfx('bull');
  } else {
    if (tl.w) return quiet || toast('Cannot build on water');
    if (tl.k) return quiet || toast('Tile is occupied. Bulldoze it first.');
    if (S.money < d.c) return quiet || toast('Need $' + d.c);
    S.money -= d.c; tl.k = tool; tl.lv = 0; tl.tree = false; sfx('build');
  }
  cover(); hud();
}

function shade(h, f) { const n = parseInt(h.slice(1), 16), c = v => Math.max(0, Math.min(255, Math.round(v * f))); return `rgb(${c(n >> 16)},${c((n >> 8) & 255)},${c(n & 255)})`; }
function poly(p, fill) { ctx.beginPath(); ctx.moveTo(p[0][0], p[0][1]); for (let i = 1; i < p.length; i++) ctx.lineTo(p[i][0], p[i][1]); ctx.closePath(); ctx.fillStyle = fill; ctx.fill(); }
function dia(cx, cy, fill, f = 1) { const a = TW / 2 * f, b = TH / 2 * f; poly([[cx, cy - b], [cx + a, cy], [cx, cy + b], [cx - a, cy]], fill); }
function box(cx, cy, f, h, col, win) {
  const a = TW / 2 * f, b = TH / 2 * f;
  poly([[cx - a, cy], [cx, cy + b], [cx, cy + b - h], [cx - a, cy - h]], shade(col, .78));
  poly([[cx, cy + b], [cx + a, cy], [cx + a, cy - h], [cx, cy + b - h]], shade(col, .6));
  poly([[cx, cy - b - h], [cx + a, cy - h], [cx, cy + b - h], [cx - a, cy - h]], shade(col, 1.1));
  if (win) for (let j = 0; j * 8 + 10 < h; j++) for (const [u0, u1] of [[.2, .4], [.6, .8]]) {
    const v0 = 5 + j * 8, v1 = v0 + 4, f2 = 'rgba(255,233,168,.55)';
    poly([[cx - a + u0 * a, cy + u0 * b - v0], [cx - a + u1 * a, cy + u1 * b - v0], [cx - a + u1 * a, cy + u1 * b - v1], [cx - a + u0 * a, cy + u0 * b - v1]], f2);
    poly([[cx + u0 * a, cy + b - u0 * b - v0], [cx + u1 * a, cy + b - u1 * b - v0], [cx + u1 * a, cy + b - u1 * b - v1], [cx + u0 * a, cy + b - u0 * b - v1]], f2);
  }
}
function tree(cx, cy, s = 1) { ctx.fillStyle = '#5b3d26'; ctx.fillRect(cx - 1, cy - 4, 2, 5); ctx.fillStyle = '#1f6b3a'; ctx.beginPath(); ctx.ellipse(cx, cy - 8 * s, 6 * s, 7 * s, 0, 0, 7); ctx.fill(); ctx.fillStyle = '#2f8c4e'; ctx.beginPath(); ctx.ellipse(cx - 1, cy - 10 * s, 3.5 * s, 4 * s, 0, 0, 7); ctx.fill(); }
function smoke(cx, cy) { for (let i = 0; i < 3; i++) { const p = (time * .6 + i / 3) % 1; ctx.fillStyle = `rgba(210,215,220,${.5 * (1 - p)})`; ctx.beginPath(); ctx.arc(cx + p * 6, cy - p * 22, 3 + p * 4, 0, 7); ctx.fill(); } }

function draw() {
  ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.fillStyle = '#0b1822'; ctx.fillRect(0, 0, cv.width, cv.height);
  ctx.setTransform(cam.z, 0, 0, cam.z, cam.x, cam.y); if (shake) ctx.translate((Math.random() - .5) * shake, (Math.random() - .5) * shake);
  const x0 = -cam.x / cam.z, y0 = -cam.y / cam.z, x1 = (cv.width - cam.x) / cam.z, y1 = (cv.height - cam.y) / cam.z; bucketCars();
  for (let y = 0; y < N; y++) for (let x = 0; x < N; x++) {
    const sx = (x - y) * TW / 2, sy = (x + y) * TH / 2;
    if (sx < x0 - TW || sx > x1 + TW || sy > y1 + 100 || sy + TH < y0) continue;
    const tl = S.t[y * N + x], cx = sx, cy = sy + TH / 2, d = TOOLS[tl.k];
    if (tl.w) { dia(cx, cy, `hsl(200,55%,${34 + 4 * Math.sin(time * 1.2 + x * .7 + y * .5)}%)`); continue; }
    const h = (((x * 73856093) ^ (y * 19349663)) >>> 0) % 100 / 100;
    dia(cx, cy, `hsl(${95 + h * 12},38%,${42 + h * 6}%)`);
    if (tl.tree) { tree(cx, cy + 3); continue; }
    if (!tl.k) continue;
    if (tl.k === 'road') {
      dia(cx, cy, '#46515c', .98); ctx.strokeStyle = '#d8c46a'; ctx.lineWidth = 1.5; ctx.setLineDash([4, 4]); ctx.beginPath();
      for (const [dx, dy, ex, ey] of [[1, 0, 1, 1], [-1, 0, -1, -1], [0, 1, -1, 1], [0, -1, 1, -1]]) { const n = at(x + dx, y + dy); if (n && n.k === 'road') { ctx.moveTo(cx, cy); ctx.lineTo(cx + ex * TW / 4, cy + ey * TH / 4); } }
      ctx.stroke(); ctx.setLineDash([]);
    } else drawBuilding(tl, x, y, cx, cy, d);
    if (tl.k === 'road') drawCars(x, y);
    if (tl.fire) { drawFire(cx, cy); smoke(cx, cy - 12); }
    if (layer) overlay(tl, y * N + x, cx, cy);
  }
  if (hover && tool) {
    const tl = at(hover.x, hover.y), d = TOOLS[tool], cx = (hover.x - hover.y) * TW / 2, cy = (hover.x + hover.y) * TH / 2 + TH / 2;
    const ok = tool === 'bull' ? (tl.k || tl.tree) : (!tl.w && !tl.k && S.money >= d.c);
    if (d.r) { ctx.globalAlpha = .12; for (let dy = -d.r; dy <= d.r; dy++) for (let dx = -d.r; dx <= d.r; dx++) if (Math.abs(dx) + Math.abs(dy) <= d.r) dia(cx + (dx - dy) * TW / 2, cy + (dx + dy) * TH / 2, '#fff', .95); ctx.globalAlpha = 1; }
    dia(cx, cy, ok ? 'rgba(63,208,176,.45)' : 'rgba(229,96,77,.5)');
  }
}

function pick(px, py) {
  const wx = (px - cam.x) / cam.z, wy = (py - cam.y) / cam.z;
  const x = Math.round(((wy - 16) / 16 + wx / 32) / 2), y = Math.round(((wy - 16) / 16 - wx / 32) / 2);
  return at(x, y) ? { x, y } : null;
}
function describe() {
  if (!hover) return;
  const tl = at(hover.x, hover.y); let s = `Tile ${hover.x},${hover.y}: `;
  if (tl.w) s += 'water'; else if (!tl.k) s += tl.tree ? 'forest' : 'open land';
  else { s += TOOLS[tl.k].n; if (tl.lv) s += ' level ' + tl.lv; if (tl.road === false) s += ' (no road nearby)'; else if (tl.pw === false && 'rci'.includes(tl.k[0]) && tl.k.length === 3) s += ' (no power)'; }
  $('info').textContent = s + (tool ? '   |   ' + TOOLS[tool].n + ': ' + TOOLS[tool].info : '');
}

let tt; function toast(m) { const e = $('toast'); e.textContent = m; e.classList.add('show'); clearTimeout(tt); tt = setTimeout(() => e.classList.remove('show'), 2600); }
function hud() {
  $('money').textContent = '$' + Math.round(S.money).toLocaleString(); $('money').className = S.money < 0 ? 'neg' : '';
  $('date').textContent = MONTHS[Math.floor(S.day % 360 / 30)] + ' Y' + (1 + Math.floor(S.day / 360));
  $('pop').textContent = S.pop.toLocaleString(); $('jobs').textContent = S.jobs; $('happy').textContent = Math.round(S.happy) + '%'; $('rank').textContent = RANKS[S.rank][1];
  for (const k of 'rci') $('d_' + k).style.width = ((S.dem[k] + 1) * 50) + '%';
  const net = S.inc - S.exp; $('inc').textContent = '$' + S.inc.toFixed(0); $('exp').textContent = '$' + S.exp.toFixed(0);
  $('net').textContent = (net >= 0 ? '+$' : '-$') + Math.abs(net).toFixed(0); $('net').className = net >= 0 ? 'pos' : 'neg';
}
function sync() { $('tax').value = S.tax; $('taxv').textContent = S.tax + '%'; document.querySelectorAll('.sp').forEach(b => b.classList.toggle('on', +b.dataset.s === S.speed)); }
function save(auto) { localStorage.setItem(SAVE, JSON.stringify({ seed: S.seed, money: S.money, day: S.day, tax: S.tax, speed: S.speed, name: S.name, pop: S.pop, jobs: S.jobs, happy: S.happy, dem: S.dem, inc: S.inc, exp: S.exp, rank: S.rank, t: S.t.map(a => [+a.w, a.k, a.lv, +a.tree]) })); toast(auto ? 'Autosaved' : 'City saved'); }
function load() {
  try { const s = localStorage.getItem(SAVE); if (!s) return false; const d = JSON.parse(s);
    S = { ...d, t: d.t.map(a => ({ w: !!a[0], k: a[1], lv: a[2], tree: !!a[3], pw: false })) };
    $('cname').value = S.name; cover(); sync(); hud(); return true; } catch (e) { return false; }
}

// UI
const tb = $('tools');
for (const [g, ids] of GROUPS) {
  tb.insertAdjacentHTML('beforeend', `<h4>${g}</h4>`);
  for (const id of ids) { const d = TOOLS[id], b = document.createElement('button'); b.dataset.t = id; b.title = d.info;
    b.innerHTML = `<i class="sw" style="background:${d.col}"></i><span>${d.n}</span><span>$${d.c}</span>`;
    b.onclick = () => { tool = id; mark(); }; tb.appendChild(b); }
}
function mark() { tb.querySelectorAll('button').forEach(b => b.classList.toggle('on', b.dataset.t === tool)); }
document.querySelectorAll('.sp').forEach(b => b.onclick = () => { S.speed = +b.dataset.s; sync(); });
$('tax').oninput = e => { S.tax = +e.target.value; $('taxv').textContent = S.tax + '%'; };
$('cname').oninput = e => S.name = e.target.value;
$('save').onclick = () => save(); $('load').onclick = () => toast(load() ? 'City loaded' : 'No saved city found');
$('new').onclick = () => { if (confirm('Start a new city? Unsaved progress is lost.')) newGame(); };
cv.addEventListener('contextmenu', e => e.preventDefault());
cv.addEventListener('mousedown', e => { initAudio(); if (e.button === 0) { painting = true; if (hover && tool) place(hover.x, hover.y); } else panning = true; });
addEventListener('mouseup', () => { painting = panning = false; });
addEventListener('mousemove', e => {
  if (panning) { cam.x += e.movementX; cam.y += e.movementY; }
  hover = pick(e.clientX, e.clientY); describe();
  if (painting && hover && DRAG.includes(tool)) place(hover.x, hover.y, true);
});
cv.addEventListener('wheel', e => {
  const o = cam.z, z = clamp(o * (e.deltaY < 0 ? 1.1 : .9), .5, 2.2);
  cam.x = e.clientX - (e.clientX - cam.x) * z / o; cam.y = e.clientY - (e.clientY - cam.y) * z / o; cam.z = z;
}, { passive: true });
addEventListener('keydown', e => {
  if (e.target.tagName === 'INPUT' && e.target.type === 'text') return;
  const k = e.key.toLowerCase(); keys.add(k);
  if (k === ' ') { S.speed = S.speed ? 0 : 1; sync(); e.preventDefault(); }
  if ('123'.includes(k) && k) { S.speed = +k; sync(); }
  if (k === 'escape') { tool = null; mark(); }
});
addEventListener('keyup', e => keys.delete(e.key.toLowerCase()));
addEventListener('resize', () => { cv.width = innerWidth; cv.height = innerHeight; });

const LAYERS = [[null, 'Off'], ['power', 'Power'], ['water', 'Water'], ['police', 'Police'], ['fire', 'Fire'], ['clinic', 'Health'], ['traffic', 'Traffic'], ['happy', 'Happiness']];
LAYERS.forEach(([id, n]) => {
  const b = document.createElement('button'); b.textContent = n; if (!id) b.classList.add('on');
  b.onclick = () => { layer = id; document.querySelectorAll('#layers button').forEach(x => x.classList.toggle('on', x === b)); };
  $('layers').appendChild(b);
});
$('boom').onclick = () => { initAudio(); triggerDisaster(); };

function frame(t) {
  const dt = Math.min(100, t - last || 16); last = t; time = t / 1000;
  const ms = [0, 1000, 450, 150][S.speed];
  if (ms) { acc += dt; while (acc >= ms) { acc -= ms; tick(); } }
  const sp = 0.7 * dt;
  if (keys.has('w') || keys.has('arrowup')) cam.y += sp; if (keys.has('s') || keys.has('arrowdown')) cam.y -= sp;
  if (keys.has('a') || keys.has('arrowleft')) cam.x += sp; if (keys.has('d') || keys.has('arrowright')) cam.x -= sp;
  updateCars(dt / 1000); shake *= 0.9; if (shake < .3) shake = 0; draw(); requestAnimationFrame(frame);
}
cv.width = innerWidth; cv.height = innerHeight;
if (!load()) newGame(); else centerCam();
mark(); requestAnimationFrame(frame);
