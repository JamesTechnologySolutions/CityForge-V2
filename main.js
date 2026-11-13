const { app, BrowserWindow, Menu, shell } = require('electron');
const path = require('path');
const icon = path.join(__dirname, 'icon.ico');
if (!app.requestSingleInstanceLock()) app.quit();
function createWindow() {
  const win = new BrowserWindow({
    width: 1600, height: 980, minWidth: 1024, minHeight: 700,
    show: false, backgroundColor: '#101c28', title: 'CityForge',
    icon, autoHideMenuBar: true,
    webPreferences: { contextIsolation: true, nodeIntegration: false, sandbox: true }
  });
  Menu.setApplicationMenu(null);
  win.loadFile(path.join(__dirname, 'src', 'index.html'));
  win.once('ready-to-show', () => win.show());
  win.webContents.setWindowOpenHandler(({ url }) => { if (url.startsWith('https:')) shell.openExternal(url); return { action: 'deny' }; });
}
app.whenReady().then(() => { createWindow(); app.on('activate', () => { if (BrowserWindow.getAllWindows().length===0) createWindow(); }); });
app.on('window-all-closed', () => { if (process.platform !== 'darwin') app.quit(); });