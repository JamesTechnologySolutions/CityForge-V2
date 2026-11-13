const { app, BrowserWindow, Menu } = require('electron');
const path = require('node:path');
function createWindow(){const win=new BrowserWindow({width:1600,height:950,minWidth:1100,minHeight:700,backgroundColor:'#9bc9d9',title:'CityForge',autoHideMenuBar:true,webPreferences:{contextIsolation:true,nodeIntegration:false,sandbox:true}});Menu.setApplicationMenu(null);win.loadFile(path.join(__dirname,'src','index.html'));}
app.whenReady().then(()=>{createWindow();app.on('activate',()=>{if(BrowserWindow.getAllWindows().length===0)createWindow()})});
app.on('window-all-closed',()=>{if(process.platform!=='darwin')app.quit()});