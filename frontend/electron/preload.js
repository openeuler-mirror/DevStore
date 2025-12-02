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

const { contextBridge, ipcRenderer } = require('electron')

contextBridge.exposeInMainWorld('electronAPI', {
  invoke: (channel, ...args) => ipcRenderer.invoke(channel, ...args),
  closeApp: () => ipcRenderer.send('close-app'),
  getUsername: () => ipcRenderer.invoke('get-username'),
  minimizeWindow: () => ipcRenderer.send('minimize-window'),
  toggleMaximize: () => ipcRenderer.send('toggle-maximize'),
  closeWindow: () => ipcRenderer.send('close-window')
})
