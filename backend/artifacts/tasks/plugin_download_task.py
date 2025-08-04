#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2025 Huawei Technologies Co., Ltd.
# oeDeploy is licensed under the Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#     http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v2 for more details.
# Create: 2025-07-18
# ======================================================================================================================

import os
import shutil
import logging
from typing import Any, Dict

from tasks.base_task import BaseTask, TaskExecuteError
from tasks.models import Task
from utils.cmd_executor import CommandExecutor
from artifacts.models import OEDPPlugin
from artifacts.utils import update_plugin_status, update_plugin_action_list, get_plugin_action_list
from constants.paths import PLUGIN_CACHE_DIR

logger = logging.getLogger(__name__)


class PluginDownloadTask(BaseTask):
    """下载OEDP插件
    Attributes:
        plugin: 要下载的插件对象
    """

    def __init__(self, plugin: OEDPPlugin, **kwargs: Dict[str, Any]) -> None:
        super().__init__(task_type=Task.Type.PLUGIN_DOWNLOAD, **kwargs)
        self.plugin = plugin

    def run(self) -> str:
        """执行插件下载任务
        Returns:
            下载结果的描述信息
        Raises:
            TaskExecuteError: 当下载失败时抛出
        """
        logger.info(f"Start downloading plugin: {self.plugin.key}")
        
        # 确保插件缓存目录存在
        if not os.path.exists(PLUGIN_CACHE_DIR):
            os.makedirs(PLUGIN_CACHE_DIR)
            logger.info(f"Created plugin cache directory: {PLUGIN_CACHE_DIR}")
            
        target_project = os.path.join(PLUGIN_CACHE_DIR, self.plugin.key)
        
        # 执行下载命令
        cmd = ['oedp', 'init', self.plugin.name, '-p', target_project, '-f']
        cmd_executor = CommandExecutor(cmd, timeout=580)
        _, stderr, code = cmd_executor.run()
        
        if code != 0:
            logger.error(f"Failed to download plugin {self.plugin.key}, error: {stderr}")
            # 执行失败需清理目录
            if os.path.exists(target_project):
                try:
                    shutil.rmtree(target_project)
                    logger.info(f"Cleaned up failed download directory: {target_project}")
                except Exception as e:
                    logger.error(f"Failed to clean up directory {target_project}: {e}")
            
            # 更新插件下载状态 not yet
            if not update_plugin_status(self.plugin, Task.Status.NOT_YET):
                logger.error(f"Failed to update plugin [{self.plugin.key}] status to [{Task.Status.NOT_YET}]")
                raise TaskExecuteError(f"Failed to update plugin status")
            
            raise TaskExecuteError(stderr)
        
        logger.info(f"Successfully downloaded plugin: {self.plugin.key}")
        
        # 更新插件下载状态 success
        if not update_plugin_status(self.plugin, Task.Status.SUCCESS):
            logger.error(f"Failed to update plugin [{self.plugin.key}] status to [{Task.Status.SUCCESS}]")
            raise TaskExecuteError(f"Failed to update plugin status")
        
        action_list = get_plugin_action_list(self.plugin)
        if not update_plugin_action_list(self.plugin, action_list):
            logger.error(f"Failed to update plugin [{self.plugin.key}] action_list")
            raise TaskExecuteError(f"Failed to update plugin action_list")
        
        return f"Download plugin [{self.plugin.key}] successfully."
