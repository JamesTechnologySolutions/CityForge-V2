const { app, BrowserWindow, Menu } = require('electron');
function create() {
  const w = new BrowserWindow({ width: 1400, height: 860, backgroundColor: '#0b1822', title: 'Cityforge',
    webPreferences: { contextIsolation: true } });
  Menu.setApplicationMenu(null);
  w.loadFile('src/index.html');
}
app.whenReady().then(create);
app.on('window-all-closed', () => app.quit());
