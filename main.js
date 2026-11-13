const { app, BrowserWindow, Menu } = require('electron');
const path = require('path');
const icon = path.join(__dirname, 'src', 'assets', 'logo.png');
if (!app.requestSingleInstanceLock()) app.quit();
function create() {
  const splash = new BrowserWindow({ width: 520, height: 320, frame: false, resizable: false, alwaysOnTop: true,
    center: true, backgroundColor: '#0b1822', icon, skipTaskbar: true });
  splash.loadFile('src/splash.html');
  const w = new BrowserWindow({ width: 1400, height: 860, show: false, backgroundColor: '#0b1822', title: 'Cityforge 2',
    icon, webPreferences: { contextIsolation: true } });
  Menu.setApplicationMenu(null);
  w.loadFile('src/index.html');
  const t0 = Date.now();
  w.once('ready-to-show', () => setTimeout(() => { if (!splash.isDestroyed()) splash.destroy(); w.show(); }, Math.max(0, 2600 - (Date.now() - t0))));
}
app.whenReady().then(create);
app.on('window-all-closed', () => app.quit());
