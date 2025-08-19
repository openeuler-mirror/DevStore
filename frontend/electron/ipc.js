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
const os = require('os')

function registerIpcListeners() {
  ipcMain.on('close-app', () => {
    app.quit()
  })

  // 获取当前系统用户名
  ipcMain.handle('get-username', () => {
    try {
      // 优先使用 os.userInfo() 获取用户信息
      const userInfo = os.userInfo()
      return { success: true, username: userInfo.username }
    } catch (error) {
      try {
        // 如果 os.userInfo() 失败，尝试使用环境变量
        const username = process.env.USER || process.env.USERNAME || process.env.LOGNAME
        if (username) {
          return { success: true, username }
        }
        // 最后尝试使用 whoami 命令
        const whoami = execSync('whoami', { encoding: 'utf8' }).trim()
        return { success: true, username: whoami }
      } catch (fallbackError) {
        return { 
          success: false, 
          error: fallbackError instanceof Error ? fallbackError.message : 'Unknown error',
          username: 'unknown'
        }
      }
    }
  })

  // 用户管理
  ipcMain.handle('create-user', (_event, { username, password }) => {
    try {
      execSync(`useradd -m ${username}`)
      execSync(`echo "${username}:${password}" | chpasswd`)
      return { success: true }
    } catch (error) {
      return { success: false, error: error instanceof Error ? error.message : 'Unknown error' }
    }
  })

  // 磁盘分区
  ipcMain.handle('partition-disk', (_event, { disk: _disk, partitions: _partitions }) => {
    try {
      // 实现分区逻辑
      return { success: true }
    } catch (error) {
      return { success: false, error: error instanceof Error ? error.message : 'Unknown error' }
    }
  })

  // 挂载镜像
  ipcMain.handle('mount-image', (_event, { imagePath, mountPoint }) => {
    try {
      execSync(`mkdir -p ${mountPoint}`)
      execSync(`mount -o loop ${imagePath} ${mountPoint}`)
      return { success: true }
    } catch (error) {
      return { success: false, error: error instanceof Error ? error.message : 'Unknown error' }
    }
  })

  // 文件复制
  ipcMain.handle('copy-files', (_event, { source, destination }) => {
    try {
      execSync(`cp -r ${source} ${destination}`)
      return { success: true }
    } catch (error) {
      return { success: false, error: error instanceof Error ? error.message : 'Unknown error' }
    }
  })

  // GRUB配置
  ipcMain.handle('configure-grub', (_event, { disk }) => {
    try {
      execSync(`grub-install ${disk}`)
      execSync(`update-grub`)
      return { success: true }
    } catch (error) {
      return { success: false, error: error instanceof Error ? error.message : 'Unknown error' }
    }
  })
}

module.exports = {
  registerIpcListeners
}
