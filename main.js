const { app, BrowserWindow, Tray, Menu } = require('electron');
const { session } = require('electron');
const path = require('path');
const { shell } = require('electron');
const StoreModule = require('electron-store');
const Store = StoreModule.default; // access the default export
const exePath = process.execPath;
const fs = require('fs');
const ws = require('windows-shortcuts');

//app.commandLine.appendSwitch('proxy-server', 'socks5://127.0.0.1:1080'); // specify socks5 proxy to connect through it 
app.commandLine.appendSwitch(
  'force-webrtc-ip-handling-policy',
  'default_public_interface_only'
);

Menu.setApplicationMenu(null);
const store = new Store({ name: 'protonmail-settings' });
let tray = null;
let mainWindow = null;
let windowShownOnce = false;
let startHidden = store.get('startHidden', false);
let startatBoot = store.get('startatBoot', false)

function addToStartup(appName, exePath, enable) {
  if (process.platform !== 'win32') return;

  // Get the Startup folder path
  const startupFolder = path.join(
    process.env.APPDATA,
    'Microsoft\\Windows\\Start Menu\\Programs\\Startup'
  );

  const shortcutPath = path.join(startupFolder, `${appName}.lnk`);
  if (enable) {
    // Create shortcut only if it doesn't exist
    if (!fs.existsSync(shortcutPath)) {
      ws.create(shortcutPath, {
        target: exePath,
        workingDir: path.dirname(exePath),
        runStyle: 1
      }, function(err) {
        if (err) {
          console.error('Failed to create startup shortcut:', err);
        } else {
          console.log('Startup shortcut created successfully!');
        }
      });
    }
  } else {
    // Remove shortcut if it exists
    if (fs.existsSync(shortcutPath)) {
      try {
        fs.unlinkSync(shortcutPath);
        console.log('Startup shortcut removed.');
      } catch (err) {
        console.error('Failed to remove startup shortcut:', err);
      }
    }
  }
}
function openInDefaultBrowser(url) {
  shell.openExternal(url);
  }
function createWindow() {
  mainWindow = new BrowserWindow({
    width: 900,
    height: 600,
    show: !startHidden, // start hidden, tray controls visibility
    icon: path.join(__dirname, 'assets', 'mail.ico'),
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      zoomFactor: 0.7, // Set zoom factor
      javascript: true, // JavaScript enabled by default
    }
  });
  mainWindow.webContents.setUserAgent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36") //specify user agent to use
  session.defaultSession.setPermissionRequestHandler((webContents, permission, callback) => {
    console.log('Permission requested:', permission);

    // Example: allow notifications permission
    if (permission === 'notifications') {
      return callback(true);
    }

    // Deny everything else
    return callback(false);
  });

  mainWindow.loadURL('https://mail.protonmail.com');

  mainWindow.on('close', (event) => {
    // Hide instead of closing (unless quitting)
    if (!app.isQuiting) {
      event.preventDefault();
      mainWindow.hide();
      windowShownOnce = false
    }
    return false;
  });
}
app.whenReady().then(() => {
  createWindow();
  tray = new Tray(path.join(__dirname, 'assets', 'mail.ico'));
  const contextMenu = Menu.buildFromTemplate([
    {
      label: 'Start at boot',
      type: 'checkbox',
      checked: store.get('startatBoot', false), // restore saved state
      click: (menuItem) => {
        startatBoot = menuItem.checked;
        console.log(startatBoot)
        addToStartup('ProtonMail', process.execPath, startatBoot); // save new state
        store.set('startatBoot',startatBoot);
      }
    },
    {
      label: 'Start Hidden',
      type: 'checkbox',
      checked: store.get('startHidden', false), // restore saved state
      click: (menuItem) => {
        startHidden = menuItem.checked;
        store.set('startHidden',startHidden); // save new state
      }
    },
    { type: 'separator' },
    { label: 'About', click: () => openInDefaultBrowser('https://github.com/7gxycn08/ProtonMailView') },
    { label: 'Quit', click: () => {
      app.isQuiting = true;
      app.quit();
    }}
  ]);
  tray.on('click', () => {
    if (!windowShownOnce && mainWindow) {
       mainWindow.show();
       windowShownOnce = true;
    }
  });
  tray.setToolTip('ProtonMail');
  tray.setContextMenu(contextMenu);
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) createWindow();
});

