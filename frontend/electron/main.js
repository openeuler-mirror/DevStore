/* Copyright (c) 2025 Huawei Technologies Co., Ltd.
 * oeDeploy is licensed under the Mulan PSL v2.
 * You can use this software according to the terms and conditions of the Mulan PSL v2.
 * You may obtain a copy of Mulan PSL v2 at:
 *     http://license.coscl.org.cn/MulanPSL2
 * THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
 * PURPOSE.
 * See the Mulan PSL v2 for more details.
 * Create: 2025-07-30
 * =================================================================================================================== */

const { app, BrowserWindow, shell, ipcMain } = require('electron')
const path = require('path')
const { registerIpcListeners } = require('./ipc.js')

app.disableHardwareAcceleration()

let mainWindow = null

function createWindow() {
  const win = new BrowserWindow({
    width: 1200,
    height: 800,
    backgroundColor: '#00000000',
    icon: path.join(__dirname, '../src/assets/logo.png'),
    frame: true,
    titleBarStyle: 'hidden',
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      webSecurity: false,
      allowRunningInsecureContent: true,
      devTools: true,
      additionalArguments: ['--enable-features=WebContentsForceDark'],
      preload: path.join(__dirname, 'preload.js')
    }
  })

  mainWindow = win

  registerIpcListeners();

  if (process.env.NODE_ENV === 'development') {
    const viteUrl = 'http://localhost:5173'
    win.loadURL(viteUrl, {
      extraHeaders: 'pragma: no-cache\n',
      httpReferrer: viteUrl
    })

    win.webContents.openDevTools()

    win.webContents.on('did-finish-load', () => {
      console.log('Page loaded successfully')
      win.webContents.executeJavaScript(`
        console.log('Checking scripts...');
        Array.from(document.scripts).forEach(script => {
          console.log('Script src:', script.src);
        });
      `)
    })

    win.webContents.on('did-fail-load', (_event, _errorCode, errorDesc) => {
      console.error('Failed to load page:', errorDesc)
    })

    win.webContents.session.webRequest.onBeforeRequest((_details, callback) => {
      callback({ cancel: false })
    })
  } else {
    console.log('Open file in dist')
    win.loadFile(path.join(__dirname, '../dist/index.html'))

    win.webContents.on('will-navigate', (event, url) => {
      if (url.startsWith('https://gitee.com/')) {
        // 阻止导航
        event.preventDefault()
        // 在外部浏览器中打开
        shell.openExternal(url)
      }
    })
  }
}

// 窗口控制 IPC 处理
ipcMain.on('minimize-window', () => {
  if (mainWindow) {
    mainWindow.minimize()
  }
})

ipcMain.on('toggle-maximize', () => {
  if (mainWindow) {
    if (mainWindow.isMaximized()) {
      mainWindow.unmaximize()
    } else {
      mainWindow.maximize()
    }
  }
})

ipcMain.on('close-window', () => {
  if (mainWindow) {
    mainWindow.close()
  }
})

app.whenReady().then(createWindow)

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})
