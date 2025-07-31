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

const { app, ipcMain } = require('electron')
const { execSync } = require('child_process')
const fs = require('fs')
const path = require('path')

function registerIpcListeners() {
  ipcMain.on('close-app', () => {
    app.quit()
  })

  // 用户管理
  ipcMain.handle('create-user', (event, { username, password }) => {
    try {
      execSync(`useradd -m ${username}`)
      execSync(`echo "${username}:${password}" | chpasswd`)
      return { success: true }
    } catch (error) {
      return { success: false, error: error.message }
    }
  })

  // 磁盘分区
  ipcMain.handle('partition-disk', (event, { disk, partitions }) => {
    try {
      // 实现分区逻辑
      return { success: true }
    } catch (error) {
      return { success: false, error: error.message }
    }
  })

  // 挂载镜像
  ipcMain.handle('mount-image', (event, { imagePath, mountPoint }) => {
    try {
      execSync(`mkdir -p ${mountPoint}`)
      execSync(`mount -o loop ${imagePath} ${mountPoint}`)
      return { success: true }
    } catch (error) {
      return { success: false, error: error.message }
    }
  })

  // 文件复制
  ipcMain.handle('copy-files', (event, { source, destination }) => {
    try {
      execSync(`cp -r ${source} ${destination}`)
      return { success: true }
    } catch (error) {
      return { success: false, error: error.message }
    }
  })

  // GRUB配置
  ipcMain.handle('configure-grub', (event, { disk }) => {
    try {
      execSync(`grub-install ${disk}`)
      execSync(`update-grub`)
      return { success: true }
    } catch (error) {
      return { success: false, error: error.message }
    }
  })
}

module.exports = {
  registerIpcListeners
}
