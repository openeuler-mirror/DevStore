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

from tasks.base_task import BaseTask, TaskExecuteError
from tasks.models import Task
from utils.cmd_executor import CommandExecutor


class InstallMCPTask(BaseTask):

    def __init__(self, pkg_name, **kwargs):
        super().__init__(task_type=Task.Type.MCP_INSTALL, **kwargs)
        self.pkg_name = pkg_name

    def run(self):
        cmd = ['dnf', 'install', '-y', self.pkg_name]
        cmd_executor = CommandExecutor(cmd)
        _, stderr, code = cmd_executor.run()
        if code != 0:
            raise TaskExecuteError(stderr)
        return f"Install {self.pkg_name} successfully."
