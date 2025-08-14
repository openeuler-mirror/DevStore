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
# Create: 2025-08-14
# ======================================================================================================================
import logging
from typing import Any, Dict
from tasks.base_task import BaseTask, TaskExecuteError
from tasks.models import Task
from utils.cmd_executor import CommandExecutor
from artifacts.models import MCPServer
logger = logging.getLogger(__name__)

class MCPPackageTask(BaseTask):
    """执行MCP包操作任务（安装/卸载）"""

    def __init__(self, mcp_server: MCPServer, action: str, **kwargs: Dict[str, Any]) -> None:
        task_type = Task.Type.MCP_INSTALL if action == 'install' else Task.Type.MCP_UNINSTALL
        super().__init__(task_type=task_type, **kwargs)
        self.mcp_server_name = mcp_server.name
        self.package_name = mcp_server.package_name
        self.action = action
    def run(self) -> str:
        """执行MCP包操作任务"""
        logger.info(f"Start {self.action} MCP package [{self.mcp_server_name}]")
        
        try:           
            if self.action == 'install':
                return self._install_package()            
            elif self.action == 'uninstall':
                return self._uninstall_package()
            else:
                raise TaskExecuteError(f"Invalid action: {self.action}")
        except TaskExecuteError:
            raise  
        except Exception as e:
            logger.error(f"Task execution failed: {str(e)}")
            raise TaskExecuteError(f"Task execution failed: {str(e)}")

    def _install_package(self) -> str:
        """执行安装操作"""       
        cmd_executor = CommandExecutor(['dnf', 'clean', 'all'], timeout=60)
        cmd_executor.run()
        # 执行安装
        return self._execute_dnf_command(
            ['dnf', 'install', '-y', '--nogpgcheck', self.package_name],
            f"install [{self.mcp_server_name}]"
        )

    def _uninstall_package(self) -> str:
        """执行卸载操作"""
        return self._execute_dnf_command(
            ['dnf', 'remove', '-y', self.package_name],
            f"uninstall [{self.mcp_server_name}]"
        )

    def _execute_dnf_command(self, cmd: list, operation: str) -> str:
        """执行dnf命令的通用方法"""
        cmd_executor = CommandExecutor(cmd, timeout=3600)
        _, stderr, code = cmd_executor.run()
        
        if code != 0:
            error_msg = f"Failed to {operation}: {stderr}"
            logger.error(error_msg)
            raise TaskExecuteError(error_msg)
        
        success_msg = f"Successfully {operation.replace('[', '').replace(']', '')}"
        logger.info(success_msg)
        return success_msg
