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
import logging
from typing import Any, Dict

from tasks.base_task import BaseTask, TaskExecuteError
from tasks.models import Task
from utils.cmd_executor import CommandExecutor
from artifacts.models import OEDPPlugin
from artifacts.utils import set_plugin_action_status, update_plugin_action_list
from constants.paths import PLUGIN_CACHE_DIR

logger = logging.getLogger(__name__)


class PluginActionTask(BaseTask):
    """执行OEDP插件的特定部署操作
    Attributes:
        plugin: 插件对象
        action: 操作名称
    """

    def __init__(self, plugin: OEDPPlugin, action_name: str, **kwargs: Dict[str, Any]) -> None:
        super().__init__(task_type=Task.Type.PLUGIN_ACTION, **kwargs)
        self.plugin = plugin
        self.action_name = action_name

    def run(self) -> str:
        """执行插件下载任务
        Returns:
            下载结果的描述信息
        Raises:
            TaskExecuteError: 当执行失败时抛出
        """
        logger.info(f"Start running plugin [{self.plugin.name}] action [{self.action_name}]")
        
        action_list = self.plugin.action_list
        target_project = os.path.join(PLUGIN_CACHE_DIR, self.plugin.key)
        log_file = os.path.join(target_project, "run.log")
        
        # 执行部署操作
        cmd = ['oedp', 'run', self.action_name, '-p', target_project, '-lt']
        cmd_executor = CommandExecutor(cmd)
        _, stderr, code = cmd_executor.run()
        
        if code != 0:
            # 更新操作执行状态 fail
            set_plugin_action_status(action_list, self.action_name, Task.Status.FAIL)
            if not update_plugin_action_list(self.plugin, action_list):
                msg = f"Failed to update plugin [{self.plugin.name}] action [{self.action_name}] status [{Task.Status.FAIL}]"
                logger.error(msg)
                raise TaskExecuteError(msg)
            logger.error(f"Failed to run plugin [{self.plugin.name}] action [{self.action_name}], error: {stderr}")
            raise TaskExecuteError(stderr)
        
        # 更新操作执行状态 success
        set_plugin_action_status(action_list, self.action_name, Task.Status.SUCCESS)
        if not update_plugin_action_list(self.plugin, action_list):
            msg = f"Failed to update plugin [{self.plugin.name}] action [{self.action_name}] status [{Task.Status.SUCCESS}]"
            logger.error(msg)
            raise TaskExecuteError(msg)
        
        msg = f"Successfully run plugin [{self.plugin.name}] action [{self.action_name}]"
        logger.info(msg)
        return msg
